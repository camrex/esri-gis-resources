# Esri (ArcMap/ArcGIS Pro) Standard Color Palette

All 120 named colors from Esri's ArcGIS Colors system style (the successor to the legacy ArcMap standard color set), organized in the published 12-column × 10-row grid with RGB values, hex codes, and brief narrative descriptions for each color.

The palette HTML page is also available online: [arcmap_palette.html](https://camrex.github.io/esri-gis-resources/color-palettes/arcmap-standard-palette/arcmap_palette.html)

## Files

| File | Description |
| --- | --- |
| [`arcmap_palette.html`](./arcmap_palette.html) | Interactive single-file web reference with click-to-copy, filter, PNG export, and Print (use your browser's Save as PDF to create a PDF) |
| [`ArcMap_Color_Palette.xlsx`](./ArcMap_Color_Palette.xlsx) | Excel workbook: visual 12×10 grid, sortable reference table, and notes |
| [`ArcMap_Color_Palette.png`](./ArcMap_Color_Palette.png) | Single-image 300 DPI rendering of the 12×10 grid |
| [`palette.csv`](./palette.csv) | CSV for programmatic use (`index, name, r, g, b, hex, grid_row, grid_col, description`) |

## Sources

**Primary (current):** Esri ArcGIS Colors system style, as shipped with ArcGIS Pro 3.6 (2025). Names and RGB values in this folder match the Esri-published "ArcGIS Colors" reference PDF for that release.

**Also see:** The original [Esri KB 000010027](https://support.esri.com/en-us/knowledge-base/what-are-the-rgb-color-values-for-the-standard-arcmap-c-000010027) — *"What Are the RGB Color Values for the Standard ArcMap Color Set?"* — which documents the same palette as it shipped with ArcMap. The RGB values are identical; several color names were corrected between ArcMap and ArcGIS Pro.

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
