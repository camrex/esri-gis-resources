# Changelog

<!-- markdownlint-disable MD024 -->  # noqa: E999

All notable changes to this repository will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added

- Added `color-palettes/scripts/README.md` with usage and output documentation for `verify_palette.py`, plus maintenance workflow notes.
- Added a root README verification workflow section with the one-command `verify_palette.py` run path and output report locations.
- Added `color-palettes/scripts/make_palette_xlsx.py` to regenerate `ArcGIS_Pro_Color_Palette.xlsx` from `palette.csv`, and documented it in `color-palettes/scripts/README.md`.
- Added `--check` mode to `make_palette_xlsx.py` for CI/local validation that workbook output is current without rewriting files.
- Added `color-palettes/scripts/make_palette_pngs.py` as a canonical PNG generator for `ArcGIS_Pro_Color_Palette.png` and `ArcGIS_Pro_Color_Palette_Corrections.png`.
- Consolidated script documentation into `color-palettes/scripts/README.md` and removed redundant `color-palettes/scripts/scripts_README.md`.

### Changed

- Corrected `Cretan Blue` across palette sources to match ArcGIS Pro 3.6 live style values: `RGB(0, 112, 255) / #0070FF`.
- Updated verification artifacts (`palette_verification.csv` and `palette_verification.json`) to reflect a fully matching 120/120 set.
- Promoted `arcgis_pro_palette.html` as the canonical interactive palette page, turned `arcmap_palette.html` into a redirect for GitHub Pages compatibility, and aligned copy behavior so `Copy Display` follows the active HSV/HSL/CMYK display mode.
- Renamed the exported palette assets to consistent ArcGIS Pro-oriented filenames (`ArcGIS_Pro_Color_Palette.*`).
- Renamed the canonical palette folder to `arcgis-pro-standard-palette` and retained `arcmap-standard-palette` as a legacy redirect-only path for GitHub Pages compatibility.

## [2026-04-26]

### Added

- Initial `CHANGELOG.md` for repository-level change tracking.

### Changed

- Updated ArcMap palette resources with a corrections analysis and enhanced reference assets.
- Improved family button accessibility and reused stored corrected HSV values in the interactive palette page.
- Corrected Glacier Blue values in palette sources and derived assets to match ArcGIS Pro style values: `RGB(68, 79, 137) / #444F89`.
- Updated the ArcMap palette analysis/docs to treat Glacier Blue as an Esri KB typo rather than a palette anomaly.
- Kept proposed correction overlays focused on Sahara Sand and Topaz Sand only.

## [2026-04-24]

### Added

- Added `color-palettes` resources, including the ArcMap/ArcGIS Pro standard palette reference set.

### Changed

- Updated root and palette README documentation and fixed markdown heading/lint issues.
- Added GitHub Pages links to the root and palette README files.

## [2026-04-23]

### Added

- Initial repository structure and baseline documentation.
