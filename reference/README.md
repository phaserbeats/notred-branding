# Reference assets

Drop raw assets here. This folder is the brand-steward's intake bin.

## What to drop

- **Logo files** — vector and raster versions of the existing NOT RED logo.
- **Existing photography** — any product or campaign shots already made. Subfolder by piece if there's enough.
- **Collection photos** — photos of pieces in the current collection, ideally one folder per piece (e.g., `reference/collection/garnet-band/`).
- **Inspiration** — historical references, museum images, anything that shaped the brand's sense of itself.
- **Swatches** — palette swatches, paper samples, material references.

## What happens to these

- Image files are listed in `.gitignore` and are **not** committed to git. They live locally.
- The brand-steward agent reads this folder to extract palette, infer voice, and draft `collection/inventory.md`.
- The art-director reads this folder for visual reference when producing moodboard briefs.

## What NOT to do

- Do not drop client photos or commission references that contain personally identifying information.
- Do not commit large binaries even if you bypass `.gitignore`.
