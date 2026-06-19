#!/usr/bin/env python3
"""
For each mosaic in pinterest/mosaics/, run a claude --print vision call to
extract board-level observations (palette, motifs, composition, register,
gaps). Writes per-mosaic JSON to pinterest/analysis/.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("pinterest")
MOSAICS = ROOT / "mosaics"
ANALYSIS = ROOT / "analysis"

PROMPT = """The image at @{mosaic_path} is a grid mosaic of 25 (or fewer) Pinterest pins from the "NOT RED" reference board curated for a luxury custom jewellery brand whose differentiator is symbolism.

Analyse the mosaic as a whole — treat the 25 tiles as a single visual sample of what the curator (above zero) is drawn to. You are NOT describing individual pins; you are reading the *gestalt* of this batch.

Return ONLY a single JSON object — no markdown fences, no preamble. Use these fields:

{{
  "dominant_palette": "comma-separated list of 3-6 colours that recur across the tiles",
  "secondary_palette": "comma-separated list of 2-4 colours that appear but are less dominant",
  "recurring_motifs": ["list", "of", "subjects or symbols that appear more than once — e.g. serpent, hand, eye, body, vessel, drapery, ruin, type"],
  "composition_vocabulary": "1-2 sentence description of how the pins tend to be framed and arranged — centred, edge-led, cluttered, negative-space, layered, mixed-media, etc.",
  "lighting_quality": "1 sentence on light treatment across the sample — natural / studio / chiaroscuro / flat / mixed",
  "material_textures": "comma-separated list of 3-6 textures that recur — e.g. polished metal, raw stone, velvet, parchment, brushed gold, skin, marble",
  "aesthetic_register": "1 sentence placing the sample on a register — luxury/heirloom, contemporary art-school, mystic/talisman, streetwear-adjacent, editorial-fashion, mixed",
  "mood_words": ["3-6", "single-word", "moods"],
  "notably_absent": "1 sentence on what you would *expect* on a luxury-jewellery moodboard but do NOT see here",
  "tile_count_estimate": "integer estimate of how many distinct tiles you can read"
}}
"""


def call_claude_vision(mosaic_path: Path) -> dict | None:
    prompt = PROMPT.format(mosaic_path=mosaic_path)
    try:
        result = subprocess.run(
            ["claude", "--print", "--permission-mode", "acceptEdits", prompt],
            capture_output=True,
            text=True,
            timeout=240,
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
    parser.add_argument("--limit", type=int, default=None, help="process at most N mosaics")
    parser.add_argument("--force", action="store_true", help="re-run even if analysis exists")
    args = parser.parse_args()

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    mosaics = sorted(p for p in MOSAICS.glob("mosaic-*.jpg") if not p.name.startswith("._"))
    if args.limit:
        mosaics = mosaics[: args.limit]

    print(f"analysing {len(mosaics)} mosaics")
    analysed, skipped, failed = 0, 0, 0
    for m in mosaics:
        out = ANALYSIS / f"{m.stem}.json"
        if out.exists() and not args.force:
            skipped += 1
            continue
        print(f"+ {m.name}...", flush=True)
        result = call_claude_vision(m)
        if result is None:
            failed += 1
            continue
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        analysed += 1

    print(f"\nDone. analysed={analysed} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()
