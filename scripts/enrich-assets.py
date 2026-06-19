#!/usr/bin/env python3
"""
One-off enrichment pass: for every image in assets/, read it with Claude vision
(via the claude CLI in headless mode) and write a structured visual_description
back into the companion <image>.json. Idempotent — skips images whose JSON
already has visual_description.

Usage:
  python3 scripts/enrich-assets.py              # process all
  python3 scripts/enrich-assets.py --limit 1    # process one (for testing)
  python3 scripts/enrich-assets.py --force      # re-run even if already enriched
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ASSETS = Path("assets")

PROMPT_TEMPLATE = """Analyse the image at @{image_path}.

It is an Instagram post image from NOT RED, a luxury custom jewellery brand whose differentiator is symbolism.

Return ONLY a single JSON object — no markdown fences, no preamble, no explanation. Use these exact fields:

{{
  "subject": "what is in frame, one sentence",
  "composition": "framing and arrangement, one sentence",
  "palette": "comma-separated list of 2-4 dominant colours observed",
  "lighting": "quality and direction, one short phrase",
  "materials_visible": "jewellery materials shown, or 'none' if graphic/text-only",
  "human_presence": "hand/skin/face presence, or 'none'",
  "mood": "one short phrase",
  "format_signal": "one of: product detail | lifestyle | text-led campaign | carousel cover | other"
}}
"""


def has_visual_description(json_path: Path) -> bool:
    try:
        data = json.loads(json_path.read_text())
    except Exception:
        return False
    return "visual_description" in data


def call_claude_vision(image_path: Path) -> dict | None:
    prompt = PROMPT_TEMPLATE.format(image_path=image_path)
    try:
        result = subprocess.run(
            ["claude", "--print", "--permission-mode", "acceptEdits", prompt],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        print(f"  ! timeout", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(
            f"  ! claude exited {result.returncode}: {result.stderr.strip()[:300]}",
            file=sys.stderr,
        )
        return None

    text = result.stdout.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        print(f"  ! no JSON found: {text[:200]}", file=sys.stderr)
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        print(f"  ! JSON parse failed ({e}): {text[start:end+1][:200]}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="process at most N images")
    parser.add_argument("--force", action="store_true", help="re-run even if already enriched")
    args = parser.parse_args()

    images = sorted(p for p in ASSETS.glob("*.jpg") if not p.name.startswith("._"))
    print(f"Found {len(images)} images in assets/")
    if args.limit:
        images = images[: args.limit]
        print(f"Limited to first {len(images)} for this run")

    enriched, skipped, failed, no_json = 0, 0, 0, 0
    for img in images:
        json_path = img.with_suffix(".jpg.json")
        if not json_path.exists():
            no_json += 1
            continue
        if has_visual_description(json_path) and not args.force:
            skipped += 1
            continue

        print(f"+ {img.name}: enriching...", flush=True)
        desc = call_claude_vision(img)
        if desc is None:
            failed += 1
            continue

        data = json.loads(json_path.read_text())
        data["visual_description"] = desc
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        enriched += 1

    print(f"\nDone. enriched={enriched} skipped={skipped} failed={failed} no_json={no_json}")


if __name__ == "__main__":
    main()
