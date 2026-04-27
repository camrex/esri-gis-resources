# Esri (ArcMap/ArcGIS Pro) Standard Color Palette

All 120 named colors from Esri's ArcGIS Colors system style (the successor to the legacy ArcMap standard color set), organized in the published 12-column × 10-row grid with RGB values, hex codes, and brief narrative descriptions for each color.

## Files

The palette HTML page is also available online: [arcgis_pro_palette.html](https://camrex.github.io/esri-gis-resources/color-palettes/arcgis-pro-standard-palette/arcgis_pro_palette.html)

| File | Description |
| --- | --- |
| [`arcgis_pro_palette.html`](./arcgis_pro_palette.html) | Interactive single-file web reference with click-to-copy, filter, PNG export, Print, and a toggle to show proposed corrections (see Analysis section below) |
| [`arcmap_palette.html`](./arcmap_palette.html) | Legacy compatibility URL that redirects to `arcgis_pro_palette.html` |
| [`ArcGIS_Pro_Color_Palette.xlsx`](./ArcGIS_Pro_Color_Palette.xlsx) | Excel workbook: visual 12×10 grid, sortable reference table with HSV columns, and notes |
| [`ArcGIS_Pro_Color_Palette.png`](./ArcGIS_Pro_Color_Palette.png) | Single-image 300 DPI rendering of the 12×10 grid |
| [`ArcGIS_Pro_Color_Palette_Corrections.png`](./ArcGIS_Pro_Color_Palette_Corrections.png) | 300 DPI grid with Sahara Sand and Topaz Sand rendered as diagonal split swatches showing original (top-left) and proposed corrected (bottom-right) values |
| [`palette.csv`](./palette.csv) | CSV for programmatic use (`index, name, r, g, b, hex, h_deg, s_pct, v_pct, grid_row, grid_col, description`) |
| [`arcgis-pro-color-conversion.md`](./arcgis-pro-color-conversion.md) | Technical reference for how ArcGIS Pro's Color Editor converts between RGB, HSV, HSL, and CMYK color spaces |

Verification scripts and generated verification reports are documented in [`../scripts/README.md`](../scripts/README.md).

## Sources

**Primary (current):** Esri ArcGIS Colors system style, as shipped with ArcGIS Pro 3.6 (2025). Names and RGB values in this folder match the Esri-published "ArcGIS Colors" reference PDF for that release.

On 2026-04-27, this repo's `Cretan Blue` value was corrected from `RGB(0, 130, 255) #0082FF` to the live ArcGIS Pro 3.6 style value `RGB(0, 112, 255) #0070FF`, based on verification output from `scripts/palette_verification.csv`.

**Also see:** The original [Esri KB 000010027](https://support.esri.com/en-us/knowledge-base/what-are-the-rgb-color-values-for-the-standard-arcmap-c-000010027) — *"What Are the RGB Color Values for the Standard ArcMap Color Set?"* — which documents the same palette as it shipped with ArcMap. Its Glacier Blue entry contains a typo (`RGB(38, 79, 137) #264F89`); the ArcGIS Pro style file and the values in this folder use the correct `RGB(68, 79, 137) #444F89`. Several color names were also corrected between ArcMap and ArcGIS Pro.

The narrative descriptions, grid layout reproduction, and file formatting in this folder are my original work.

### Naming note

Esri corrected several color-name typos between the original ArcMap palette and the current ArcGIS Pro ArcGIS Colors style:

| ArcMap (legacy) | ArcGIS Pro (current) |
| --- | --- |
| Fushia Pink | **Fuchsia Pink** |
| Medium Fushia | **Medium Fuchsia** |
| Cretean Blue | **Cretan Blue** |
| Chrysophase | **Chrysoprase** |
| Citroen Yellow | **Citron Yellow** |

This folder uses the current ArcGIS Pro names. If you're working with legacy ArcMap style files or older documentation, be aware you may encounter the earlier spellings.

## Structure of the palette

The palette is arranged as a 12-column, 10-row grid (120 colors total). The leftmost column is the grayscale ramp (Arctic White → Black), and each row cycles through the same 11 hues at progressively different lightness, saturation, and muting levels:

| Row | Theme |
| --- | --- |
| 1 | Very pale pastels (near-white wash of each hue) |
| 2 | Gray 10% + light brights |
| 3 | Gray 20% + pure saturated primaries |
| 4 | Gray 30% + deep saturated |
| 5 | Gray 40% + earthy mediums |
| 6 | Gray 50% + deep earth tones |
| 7 | Gray 60% + dusty pastels (muted lights) |
| 8 | Gray 70% + medium muted |
| 9 | Gray 80% + deeper muted |
| 10 | Black + darkest deep tones |

Understanding this structure makes the palette far more useful — picking "the row 4 equivalent of the blue in row 2" is a meaningful cartographic choice.

## HSV analysis & proposed corrections

After this reference was first published, **Michael Ray Wilson, MS, CFM** observed in a LinkedIn comment that Sahara Sand and Topaz Sand are virtually indistinguishable on screen, and that Sahara Sand isn't "red enough" for its position in the palette. His HSV analysis confirmed the observation. Following up on his work, I ran a full HSV analysis of all 120 colors to see if any other anomalies were hiding in the grid.

### The palette's underlying design rules

Viewing the palette in HSV space rather than RGB reveals an elegant underlying structure:

**Columns are locked to specific hues.** Row 3 is the "anchor row" of pure saturated primaries (V=100%, S=100%). The hue at each column is defined by its row 3 entry:

| Col | Anchor (Row 3) | Target Hue |
| --- | --- | --- |
| 2 | Mars Red | 0° |
| 3 | Fire Red | 20° |
| 4 | Electron Gold | 40° |
| 5 | Solar Yellow | 60° |
| 6 | Peridot Green | 80° |
| 7 | Medium Apple | 100° |
| 8 | Tourmaline Green | 160° |
| 9 | Big Sky Blue | 200° |
| 10 | Cretan Blue | 214° |
| 11 | Amethyst | 280° |
| 12 | Ginger Pink | 320° |

The warm side (cols 2–7) is rigidly spaced at 20° per column. The cool side is looser, with a notable 60° gap between col 7 and col 8 — Esri skips the teal range entirely.

**Rows are locked to specific saturation/value combinations.** Row 1 sits at S≈25%, V=100% (pale pastels). Row 3 at S=100%, V=100% (pure saturated). Row 6 at S=100%, V≈45% (deep earth). Row 10 at S≈50%, V≈54% (darkest deep). Each row's chromatic colors all share the same approximate (S, V) coordinates.

A small systematic drift in the cool columns (cols 9–12) between saturated and muted rows appears to be intentional Bezold-Brücke compensation — perceived hue drifts as colors desaturate, and Esri's values appear to correct for it.

### Two anomalies that don't fit the rules

Two swatches deviate from these rules in ways that look more like errors than design choices:

| Color | Original | Proposed Correction | Issue |
| --- | --- | --- | --- |
| **Sahara Sand** (Row 1, Col 3) | RGB(255, 235, 190) #FFEBBE — H 42° S 25% V 100% | RGB(255, 212, 190) **#FFD4BE** — H 20° S 25% V 100% | Hue 21.7° off from the column's expected 20° |
| **Topaz Sand** (Row 1, Col 4) | RGB(255, 235, 175) #FFEBAF — H 45° S 31% V 100% | RGB(255, 233, 190) **#FFE9BE** — H 40° S 25% V 100% | Hue 5.4° off from column expected 40°, and only saturation outlier in row 1 |

**On Sahara and Topaz Sand:** these two share identical R and G values (255, 235) and differ only by 15 points in the blue channel — they're effectively the same hue at slightly different saturations rather than two distinct hues, which is why they're hard to tell apart on screen. The corrected values shift Sahara to the 20° hue position (aligned with Fire Red's column) and Topaz to the 40° position (aligned with Electron Gold's column), giving each its own distinct hue identity in the column structure. The corrected RGB values converge from three independent methods: HSV row-saturation matching, CMYK row-M-progression matching, and ArcGIS Pro's own CMYK→RGB conversion when given pattern-derived CMYK inputs. All three approaches produce identical RGBs.

**On Glacier Blue:** an earlier draft of this analysis treated Esri KB 000010027's `RGB(38, 79, 137) #264F89` entry as a palette anomaly — at S=72% it would have been the only color in row 10 above ~50% saturation. After checking the live ArcGIS Pro style file, Glacier Blue is actually `RGB(68, 79, 137) #444F89` (S=50%), which aligns cleanly with row 10's pattern. The inconsistency was in the Esri documentation, not in ArcGIS Pro.

### What this means

Aside from the Glacier Blue typo in KB 000010027, these RGB values are preserved between ArcMap and ArcGIS Pro 3.6, so Esri appears to be treating them as canonical for backward compatibility. The corrections in this section are analytical observations about Sahara Sand and Topaz Sand, not advocacy for changing the published palette.

The interactive HTML reference includes a **"Show proposed corrections"** toggle that displays the two row-1 swatches as diagonal splits with both original and corrected values visible. The static [`ArcGIS_Pro_Color_Palette_Corrections.png`](./ArcGIS_Pro_Color_Palette_Corrections.png) shows the same view as a single image. All other deliverables in this folder use the ArcGIS Pro style values throughout.

### Credits

- **Michael Ray Wilson, MS, CFM** — original observation that Sahara Sand and Topaz Sand sit on essentially the same hue; HSV analysis demonstrating Sahara Sand's hue shift toward yellow; proposed corrections for Sahara and Topaz.
- Glacier Blue documentation discrepancy in KB 000010027 identified during follow-up HSV analysis of all 120 colors and verification against the live ArcGIS Pro style file.

## About the descriptions

Each color has a brief (5–10 word) description that combines three angles:

- **Functional:** lightness (pale / medium / deep / very dark), warmth (warm / cool / balanced), and saturation (pure / muted / earthy)
- **Evocative:** a familiar real-world anchor ("mango flesh," "old denim," "glacier ice")
- **Cartographic:** a typical mapping use ("water bodies," "residential fills," "boundary lines")

Examples:

- *Mars Red* — "Pure saturated red; alerts, hazards"
- *Raw Umber* — "Earthy warm caramel; soil, geology"
- *Peacock Green* — "Very dark cool teal; deep ocean water"
- *Blue Gray Dust* — "Muted cool dusty blue; distant mountains"

### Why descriptions written this way

These descriptions were originally requested to help someone with color vision deficiency navigate the palette. Lightness, warmth (relative amounts of red vs blue), and saturation (vivid vs muted) are perceivable across essentially all types of color vision — hue alone is not. Leading with those three properties, then anchoring with a concrete object reference, makes the descriptions functionally useful regardless of whether the reader has typical color vision or any form of CVD.

The cartographic hint at the end is meant as a starting suggestion, not a rule. The palette isn't organized by intended use, but many colors have obvious visual affordances (deep blues read as deep water, earthy tans read as dry land, bright saturated reds read as alerts).

## Usage

Feel free to use this reference however you like — for personal projects, client work, cartographic standards documentation, training material, whatever. No attribution required for the descriptions, though it's always appreciated. For the palette values themselves, credit goes to Esri.

If you build something interesting with this — a web-based palette picker, a GIS plugin, a Python package — I'd love to hear about it. Open an issue or drop a link.
