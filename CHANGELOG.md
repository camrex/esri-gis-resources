# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this repository will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added

- Documented the `arcpy` dependency explicitly: a Requirements section and a per-script **Needs** column in `arcade-stateplane-utm-to-latlong/scripts/README.md`, a note in the resource README, and a comment at each `import arcpy` recording that it comes from ArcGIS Pro's Python and cannot be pip-installed. Each of those imports now carries `# pyright: ignore[reportMissingImports]`, so editors resolving against an ordinary environment stop reporting a module that only exists inside ArcGIS Pro.
- Added an explicit "Not an Esri product" statement to the root README, the Arcade expression README, the palette README, and the Arcade landing page footer: a personal collection, not affiliated with, endorsed by or supported by Esri, with Esri trademarks acknowledged and a note to test before trusting.
- Added GitHub issue forms under `.github/ISSUE_TEMPLATE/`: a bug report that asks for the stored X/Y, the returned lat/long and the expected one; an Arcade coverage request for codes, projection methods and grid-shift datums; a credit and attribution form; a palette value correction; and a general idea/question form. `config.yml` keeps blank issues enabled and links out to Esri Community and the Arcade `projectAs` idea.
- Added `.github/PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`, stating what a contribution actually is (a code list, since the builds are generated), which checks to run, and that `builds/*.txt` are never hand-edited.
- Added `arcade-stateplane-utm-to-latlong/social-card.png`, plus Open Graph, Twitter card, canonical and favicon tags on the landing page, so a shared link renders a preview instead of a bare URL.
- Added `tools/` for repository maintenance tooling that belongs to no single resource, holding the card generator `make_social_card.py` (`--check` reports a stale PNG) and a README drawing the line: a resource's `scripts/` folder holds verification that backs a documented claim, `tools/` holds asset generation that does not.
- Added a third card to the landing page's "Get it" row linking to the resource on GitHub.
- Added `arcade-stateplane-utm-to-latlong/`: an ArcGIS Arcade expression that converts a feature's stored projected coordinates to latitude and longitude, since Arcade cannot reproject. Covers 1,139 EPSG codes — every US State Plane zone across seven NAD83 realizations, every UTM zone worldwide on WGS 84 and the NAD83 realizations, and the BLM foot zones — by inlining the inverse Transverse Mercator, Lambert Conformal Conic (2SP) and Hotine Oblique Mercator maths and selecting parameters from the feature's own WKID at run time.
- Added `arcade-stateplane-utm-to-latlong/builds/`: the shipped expression in a documented (30 KB) and a condensed (21 KB) style, bit-identical in output and within 0.3% in speed, plus the EPSG code list each was built from.
- Added `arcade-stateplane-utm-to-latlong/index.html`: landing page covering usage, accuracy, the polygon-centroid and datum caveats, and what actually costs run time.
- Added `arcade-stateplane-utm-to-latlong/VALIDATION.md`: coverage, method, error budget, zone-edge behaviour, Arcade-specific static checks, performance and datum measurements, all reproducible from `scripts/`.
- Added `arcade-stateplane-utm-to-latlong/scripts/`: the build generator (`build_expression.py`, reading every parameter from `arcpy.SpatialReference` rather than EPSG's published tables), the headless validator and Node Arcade harness, an Arcade-specific linter for case-insensitive identifier collisions, a real-engine runner, a comparison against ArcGIS Pro's own Calculate Geometry Attributes (`compare_calc_geometry.py`), capability and behaviour probes, a benchmark, and two deployment helpers (`apply_rule.py`, `rule_from_csv.py`).
- Added `color-palettes/arcgis-pro-standard-palette/sahara-topaz-analysis.md`: extended Sahara Sand / Topaz Sand analysis with a full-grid structural audit, CIEDE2000 quantification, and a near-duplicate pair survey (rows 2/8 overlap, cross-column Yogo/Oxide pair).
- Added `color-palettes/arcgis-pro-standard-palette/perceptual_distance.html`: interactive perceptual-distance (ΔE2000) explorer with nearest-neighbor map, confusability heatmap, neighbor-boundary view, and closest-pairs ranking.
- Linked the new analysis and explorer from the palette page (corrections callout and footer) and the palette README (files table and analysis section).
- Added `color-palettes/arcgis-pro-standard-palette/row-2-8-overlap.md`: companion analysis of the row 2 / row 8 overlap — two S≈50% treatments 4% apart in value, the rows 8–10 dimming cascade, the three cool-side hue bands, and naming evidence the pairing was intentional; linked from the Sahara/Topaz analysis (§4.1 and §5), the README, and the ΔE explorer's closest-pairs panel.
- Added `color-palettes/scripts/README.md` with usage and output documentation for `verify_palette.py`, plus maintenance workflow notes.
- Added a root README verification workflow section with the one-command `verify_palette.py` run path and output report locations.
- Added `color-palettes/scripts/make_palette_xlsx.py` to regenerate `ArcGIS_Pro_Color_Palette.xlsx` from `palette.csv`, and documented it in `color-palettes/scripts/README.md`.
- Added `--check` mode to `make_palette_xlsx.py` for CI/local validation that workbook output is current without rewriting files.
- Added `color-palettes/scripts/make_palette_pngs.py` as a canonical PNG generator for `ArcGIS_Pro_Color_Palette.png` and `ArcGIS_Pro_Color_Palette_Corrections.png`.
- Consolidated script documentation into `color-palettes/scripts/README.md` and removed redundant `color-palettes/scripts/scripts_README.md`.
- Added a "Descriptions" checkbox to the palette page controls (checked by default); unchecking hides the per-swatch descriptions on screen, in print, and in PNG export. With descriptions hidden, the printed grid fits on a single page.

### Fixed

- Removed a stray `# noqa: E999` lint directive from the first line of the root README, where it was rendering as visible text.
- `build_expression.py` now refuses a Hotine Oblique Mercator code whose WKT carries no `Azimuth`, `Latitude_Of_Center` or `Longitude_Of_Center` parameter, instead of raising `TypeError` on the azimuth or quietly snapping a missing centre to 0.0 and emitting constants for a zone centred off West Africa. Refusals join the existing reported-and-refused path, whose heading now reads "skipped N code(s) this template cannot build" since it no longer only covers unimplemented methods. No effect on the published builds — every shipped Hotine code carries all three.
- `apply_rule.py` no longer raises `AttributeError` when pointed at an expression carrying neither a run-compressed nor a dictionary code table. The dictionary-build branch called `.group(1)` on an unchecked `re.search`; it now exits with the same readable "cannot determine the code list" message `validate.py` gives, rather than reporting the spatial reference as unsupported or failing obscurely.
- Removed an unused `math` import from `run_in_arcade.py`, and cleared trailing whitespace left by the compound-statement cleanup across `apply_rule.py`, `bench.py`, `check_zone_edges.py` and `lint.py`.
- Printing the palette page with "Show proposed corrections" enabled no longer splits the color grid across two pages: for print only, the corrections callout moves after the grid and onto its own page (palette on page 1, corrections on page 2); the on-screen layout is unchanged.
- The two split correction swatches now print legibly: they keep enough height for the diagonal original/corrected labels, label fonts are scaled for print, and the italic HSV line (the widest, colliding line) is dropped in print since the callout carries the full HSV corrections.
- PNG export no longer bakes wide-monitor white margins into the image: the capture area is constrained to the grid's own width during rendering, so the exported PNG is tight to the grid at any window size.

### Changed

- Moved the condensed Arcade template out of `build_expression.py` into `template_condensed.py` as `CONDENSED`, mirroring `template_documented.py`. The two templates are the same program in two styles and a projection method has to be added to both, so having one in its own module and the other inlined in 480 lines of generator made the asymmetry into a trap — the generator's own instructions had to say "the template below and template_documented.py". The generator drops to 352 lines and the Arcade source sits in files that hold Arcade and nothing else. The template string is byte-identical, so the published builds are unaffected.
- Clarified analysis attribution across the palette README, both analysis documents, and the palette page credit: the follow-up structural/perceptual analysis series is directed by Cameron Rex and performed with Claude (Anthropic's AI model).
- Reworked the closest-pairs table in `perceptual_distance.html`: first column now reads name-then-swatch (right-aligned) so the paired swatches sit adjacent for direct comparison, and swatches are enlarged.
- Expanded the closest-pairs table from the top ten to all fourteen pairs below ΔE 5 (adding two row-7 Dust neighbors, the row-1 Olivine ↔ Tzavorite pair, and the tightest grayscale step); the grid overlay keeps its top-ten numbered dots.
- Enlarged the closest-pairs swatches to annotated-grid scale (68×44, same 1.55 aspect) and fused each pair into a single field with a shared edge — the patch size the CIEDE2000 model assumes and the presentation where near-threshold differences are most visible.
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
