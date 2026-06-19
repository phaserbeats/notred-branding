#!/usr/bin/env python3
"""
Build NxN mosaics of Pinterest board thumbnails for batch vision analysis.

Center-crops each pin to a square, resizes to TILE px, and tiles GRID x GRID into
one image per mosaic. Saves to pinterest/mosaics/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path("pinterest")
RAW = ROOT / "raw"
MOSAICS = ROOT / "mosaics"


def find_pins(raw_dir: Path) -> list[Path]:
    return sorted(
        p
        for p in raw_dir.rglob("pinterest_*.jpg")
        if not p.name.startswith("._")
    )


def square_crop_resize(img: Image.Image, size: int) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)


def build_mosaic(pins: list[Path], grid: int, tile: int) -> tuple[Image.Image, list[Path]]:
    """Build one mosaic from the next grid*grid pins. Returns (image, pins_used)."""
    canvas = Image.new("RGB", (grid * tile, grid * tile), (32, 32, 32))
    used: list[Path] = []
    for i, pin in enumerate(pins[: grid * grid]):
        try:
            with Image.open(pin) as src:
                src = src.convert("RGB")
                thumb = square_crop_resize(src, tile)
        except Exception as e:
            print(f"  ! skipping {pin.name}: {e}")
            continue
        row, col = divmod(i, grid)
        canvas.paste(thumb, (col * tile, row * tile))
        used.append(pin)
    return canvas, used


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", type=int, default=5, help="grid side length (default: 5 = 25 pins per mosaic)")
    parser.add_argument("--tile", type=int, default=256, help="tile size in pixels (default: 256)")
    args = parser.parse_args()

    pins = find_pins(RAW)
    if not pins:
        print(f"no pins found under {RAW}/")
        return

    MOSAICS.mkdir(parents=True, exist_ok=True)
    per = args.grid * args.grid
    print(f"found {len(pins)} pins; building mosaics of {per} ({args.grid}x{args.grid} @ {args.tile}px)")

    mosaic_idx = 0
    manifest_rows = ["mosaic,pin_index,pin_filename"]
    remaining = pins[:]
    while remaining:
        chunk = remaining[:per]
        remaining = remaining[per:]
        mosaic, used = build_mosaic(chunk, args.grid, args.tile)
        out = MOSAICS / f"mosaic-{mosaic_idx:02d}.jpg"
        mosaic.save(out, "JPEG", quality=88)
        for i, p in enumerate(used):
            manifest_rows.append(f"{out.name},{i},{p.name}")
        print(f"  wrote {out.name} ({len(used)} pins)")
        mosaic_idx += 1

    (MOSAICS / "manifest.csv").write_text("\n".join(manifest_rows) + "\n")
    print(f"done. {mosaic_idx} mosaics in {MOSAICS}/ + manifest.csv")


if __name__ == "__main__":
    main()
