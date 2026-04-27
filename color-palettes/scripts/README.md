# Palette Scripts

Utility scripts for maintaining ArcGIS Colors palette assets in this repository.

## verify_palette.py

Verifies the repository reference palette against a live ArcGIS Pro `.stylx` style file.

### What it does

- Loads reference values from `../arcgis-pro-standard-palette/palette.csv`.
- Reads color records from a target `.stylx` file (`ITEMS` or `DATA` schema).
- Compares reference RGB to live style RGB for each named color.
- Writes machine-readable reports:
  - `palette_verification.csv` (per-color status)
  - `palette_verification.json` (summary + mismatches + missing/unreadable)

### Default inputs and outputs

- Default style path:
  - `C:\Program Files\ArcGIS\Pro\Resources\Styles\Styles.stylx`
- Default reference CSV:
  - `../arcgis-pro-standard-palette/palette.csv`
- Default outputs:
  - `palette_verification.csv`
  - `palette_verification.json`

### Usage (verify_palette.py)

From repo root:

```powershell
python color-palettes/scripts/verify_palette.py
```

Explicit style path:

```powershell
python color-palettes/scripts/verify_palette.py "C:\Program Files\ArcGIS\Pro\Resources\Styles\Styles.stylx"
```

Custom reference and output paths:

```powershell
python color-palettes/scripts/verify_palette.py `
  --reference-csv color-palettes/arcgis-pro-standard-palette/palette.csv `
  --output-csv color-palettes/scripts/palette_verification.csv `
  --output-json color-palettes/scripts/palette_verification.json
```

### Interpreting results

`palette_verification.csv` columns:

- `name`: Palette color name
- `ref_r/ref_g/ref_b`: Repository reference RGB
- `actual_r/actual_g/actual_b`: Live style RGB
- `status`: `MATCH`, `MISMATCH`, `NOT_FOUND`, or `UNREADABLE`

`palette_verification.json` includes:

- run metadata (`generated_at_utc`, `stylx_path`, `schema`)
- summary counts (`matches`, `mismatches`, `not_found`, `multiple_records`)
- mismatch details and missing/unreadable entries

### Expected workflow after mismatches

If mismatches are found:

1. Update `../arcgis-pro-standard-palette/palette.csv`.
2. Update `../arcgis-pro-standard-palette/arcgis_pro_palette.html` embedded color data.
3. Re-run `verify_palette.py` until summary is fully matching.
4. Commit refreshed `palette_verification.csv` and `palette_verification.json`.
5. Document the change in `../arcgis-pro-standard-palette/README.md` and `../../CHANGELOG.md`.

## make_palette_pngs.py

Regenerates the two PNG renderings from `palette.csv` and `corrections.json` in the canonical folder.

- `ArcGIS_Pro_Color_Palette.png` — standard 12×10 grid with all 120 colors.
- `ArcGIS_Pro_Color_Palette_Corrections.png` — same grid, but with diagonal-split swatches for colors listed in `corrections.json`, showing original (top-left) and proposed corrected (bottom-right) values.

### Usage (make_palette_pngs.py)

From repo root:

```powershell
# Regenerate both PNGs (default)
python color-palettes/scripts/make_palette_pngs.py

# Regenerate only the standard grid
python color-palettes/scripts/make_palette_pngs.py --standard

# Regenerate only the corrections grid
python color-palettes/scripts/make_palette_pngs.py --corrections

# Read inputs and write outputs to non-default folders
python color-palettes/scripts/make_palette_pngs.py --input-dir color-palettes/arcgis-pro-standard-palette --output-dir color-palettes/arcgis-pro-standard-palette

# Show all options
python color-palettes/scripts/make_palette_pngs.py --help
```

By default the script reads from and writes to `../arcgis-pro-standard-palette` relative to `scripts/`.

### Requirements (make_palette_pngs.py)

- Python 3.8+
- `matplotlib` (install with `python -m pip install matplotlib`)

The `csv`, `json`, `colorsys`, and `argparse` modules are used from the Python standard library.

### Programmatic use

```python
from pathlib import Path
from make_palette_pngs import (
    load_palette, load_corrections,
    render_standard_grid, render_corrections_grid,
)

palette = load_palette(Path('../arcgis-pro-standard-palette/palette.csv'))
corrections = load_corrections(Path('../arcgis-pro-standard-palette/corrections.json'))

render_standard_grid(palette, Path('../arcgis-pro-standard-palette/ArcGIS_Pro_Color_Palette.png'))
render_corrections_grid(
    palette,
    corrections,
    Path('../arcgis-pro-standard-palette/ArcGIS_Pro_Color_Palette_Corrections.png'),
)
```

### Adding or changing corrections

The proposed corrections list is `../arcgis-pro-standard-palette/corrections.json`.

Each entry has:

- `name` — color name as it appears in `palette.csv`
- `corrected_rgb` — `[r, g, b]` RGB array for the proposed corrected value
- `corrected_hex` — optional; auto-computed from RGB if omitted

To add or change corrections, edit `corrections.json` and rerun:

```powershell
python color-palettes/scripts/make_palette_pngs.py --corrections
```

## make_palette_xlsx.py

Regenerates `ArcGIS_Pro_Color_Palette.xlsx` from `palette.csv` in the canonical folder.

The generated workbook preserves the current three-sheet structure:

- `Palette Grid`
- `Color Reference`
- `About`

### Usage

From repo root:

```powershell
# Regenerate workbook using default canonical paths
python color-palettes/scripts/make_palette_xlsx.py

# Verify workbook is current (non-zero exit when stale)
python color-palettes/scripts/make_palette_xlsx.py --check

# Override input and output locations
python color-palettes/scripts/make_palette_xlsx.py `
  --input-dir color-palettes/arcgis-pro-standard-palette `
  --output-file color-palettes/arcgis-pro-standard-palette/ArcGIS_Pro_Color_Palette.xlsx
```

### Requirements

- Python 3.8+
- `openpyxl` (install with `python -m pip install openpyxl`)

## create_corrected_style.py

Builds a small standalone `.stylx` containing only the proposed corrected overlays:

- `Sahara Sand (HSV-corrected)`
- `Topaz Sand (HSV-corrected)`

This script is for optional analytical overlays and does not replace canonical ArcGIS Pro palette values in this repository.
