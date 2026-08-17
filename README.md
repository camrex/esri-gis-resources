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

### Arcade: State Plane / UTM to Latitude & Longitude

An ArcGIS Arcade expression that converts stored projected coordinates to latitude and
longitude, under [arcade-stateplane-utm-to-latlong](https://github.com/camrex/esri-gis-resources/tree/main/arcade-stateplane-utm-to-latlong).
Arcade cannot reproject, so a calculation against a projected feature class returns
northing and easting rather than lat/long — plausible and wrong. This inlines the
inverse projection maths for every zone and picks the right parameters from the
feature's own WKID. Per-zone versions have circulated for years; this combines them
all, plus pass-through for data already stored in degrees, in a single script.

Included assets:

- [Landing page](https://camrex.github.io/esri-gis-resources/arcade-stateplane-utm-to-latlong/) — what it does, how to use it, and what to watch for
- A ready-to-use build covering 1,139 EPSG codes, in a condensed and a fully
  documented form (identical behaviour, identical speed)
- Works in Calculate Field, popups and labels, or as an attribute rule
- Handles Transverse Mercator, Lambert Conformal Conic and Hotine Oblique Mercator,
  any geometry type, and passes geographic feature classes straight through
- Parity with ArcGIS Pro's own Calculate Geometry Attributes — agreement to the last
  digit that tool reports, verified across all 1,139 codes. The claim is parity, not
  better accuracy; the novelty is that one expression covers every zone and runs where
  a geoprocessing tool cannot
- The full build and verification toolchain, so the numbers can be reproduced, and so
  the expression can be regenerated for projections outside the US

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
 arcade-stateplane-utm-to-latlong/
  index.html
  README.md
  VALIDATION.md
  builds/
   arcade_latlong_documented.txt
   arcade_latlong_condensed.txt
  scripts/
   build_expression.py
   validate.py
   lint.py
   run_in_arcade.py
   apply_rule.py
   README.md
```

## Notes

- This project is intentionally informal and iterative.
- Additional Esri-related resources will be added over time.
- Repository change history is tracked in [CHANGELOG.md](./CHANGELOG.md).
