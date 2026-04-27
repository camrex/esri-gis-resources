# Esri GIS Resources

A personal collection of practical resources, references, and helper materials I find useful while working with Esri products.  # noqa: E999

This repository is meant to be lightweight and utility-focused: small, reusable assets that are easy to browse and use.

## Current Resources

### Color Palettes

The first resource set in this repo is a standard Esri color palette reference under [color-palettes](https://github.com/camrex/esri-gis-resources/tree/main/color-palettes).

Included assets:

- [Esri (ArcMap/ArcGIS Pro) Standard Color Palette](https://camrex.github.io/esri-gis-resources/color-palettes/arcgis-pro-standard-palette/arcgis_pro_palette.html) — interactive HTML reference with click-to-copy, filter, and PNG export
- CSV export for programmatic use
- Verification and helper scripts for comparing palette values against the live ArcGIS Pro style file
- Supporting documentation

## Verification Workflow

Before publishing palette updates, run the verification script from the repo root:

```powershell
python color-palettes/scripts/verify_palette.py
```

Then review the generated reports:

- `color-palettes/scripts/palette_verification.csv`
- `color-palettes/scripts/palette_verification.json`

Script usage and troubleshooting details are documented in [color-palettes/scripts/README.md](./color-palettes/scripts/README.md).

## Repository Structure

Current high-level structure:

```text
esri-gis-resources/
 README.md
 color-palettes/
  arcgis-pro-standard-palette/
   arcgis_pro_palette.html
   arcmap_palette.html
   palette.csv
   README.md
  arcmap-standard-palette/
   index.html
   arcmap_palette.html
  scripts/
   verify_palette.py
   create_corrected_style.py
   README.md
```

## Notes

- This project is intentionally informal and iterative.
- Additional Esri-related resources will be added over time.
- Repository change history is tracked in [CHANGELOG.md](./CHANGELOG.md).
