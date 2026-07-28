# The Sahara Sand / Topaz Sand Anomaly

## A structural analysis of two colors in the Esri standard palette that don't fit the pattern

**Companion document to the [Esri (ArcMap/ArcGIS Pro) Standard Color Palette reference](https://camrex.github.io/esri-gis-resources/color-palettes/arcgis-pro-standard-palette/arcgis_pro_palette.html).** This document extends the analysis summarized in the [folder README](./README.md#hsv-analysis--proposed-corrections) and in the palette page's "Show proposed corrections" panel, adding a full-grid structural audit, perceptual (CIEDE2000) quantification, and a survey of near-duplicate pairs. An [interactive ΔE explorer](https://camrex.github.io/esri-gis-resources/color-palettes/arcgis-pro-standard-palette/perceptual_distance.html) accompanies it.

Original Sahara Sand / Topaz Sand observation, initial HSV analysis, and proposed corrections: **Michael Ray Wilson, MS, CFM**. Follow-up structural analysis of all 120 colors, verification against the live ArcGIS Pro style file, and this perceptual extension: directed by Cameron Rex and performed with Claude (Anthropic's AI model). Last updated: July 2026.

---

## Summary

The 120-color Esri standard palette (ArcMap and ArcGIS Pro) is built on a strict internal grid: each **row** is locked to a single saturation/value combination, and each **warm-side column** is locked to a single hue in 20° steps (0°, 20°, 40°, 60°, 80°, 100°). Analysis of all 120 colors shows this structure holds everywhere within small rounding tolerances (≤ ~3°) — **except at two cells in row 1**:

| Color | Position | Actual | Expected by structure | Deviation |
| --- | --- | --- | --- | --- |
| Sahara Sand | row 1, hue col 20° | H 41.5° · RGB(255, 235, 190) `#FFEBBE` | H 20° · RGB(255, 212, 190) `#FFD4BE` | **+21.5° hue** |
| Topaz Sand | row 1, hue col 40° | H 45° / S 31.4% · RGB(255, 235, 175) `#FFEBAF` | H 40° / S 25.5% · RGB(255, 233, 190) `#FFE9BE` | +5° hue, **+5.9% saturation** (only saturation break in the row) |

The result: two adjacent palette entries that sit at nearly the same hue and are **nearly indistinguishable in practice (CIEDE2000 ΔE = 3.6)**, in a palette whose whole design otherwise guarantees distinct, evenly spaced hues. Three independent derivations — HSV row-structure matching, CMYK magenta-progression matching, and direct RGB channel interpolation — all converge on the same corrected values.

Whether this is a decades-old design slip or an intentional choice, only the original palette designer could say. What the structure tells us is exactly what the two colors would be if they followed the pattern.

---

## 1. Data

RGB values for all 120 colors were taken from the palette reference page, which sources them from the ArcGIS Pro 3.6.2 system style file (`Styles.stylx`). Esri Knowledge Base article 000010027 ("What Are the RGB Color Values for the Standard ArcMap Color Set?") provides the same values for the colors discussed here (the two known KB discrepancies, Glacier Blue and Cretan Blue, are unrelated to this analysis).

The palette is presented as a 12×10 grid: column 1 is a grayscale ramp; columns 2–12 are eleven hue families; rows 1–10 are ten lightness/saturation treatments of each family.

## 2. The palette's hidden structure

### 2.1 Rows are locked to saturation/value

Computing HSV for all 120 colors shows that within each row, every chromatic swatch shares a single saturation/value pair (rounding to 8-bit RGB causes sub-0.5% wobble):

| Row | S% | V% | Character |
| --- | --- | --- | --- |
| 1 | 25.5 | 100 | pale pastels |
| 2 | 50.2 / 54.9 † | 100 | light mediums |
| 3 | 100 | 100 | full saturation |
| 4 | 100 | 90.2 | strong |
| 5 | 100 | 65.9 | deep |
| 6 | 100 | 45.1 | dark |
| 7 | 26.5 | 84.3 | dusty muted |
| 8 | 50.2 | 96.1 | bright soft |
| 9 | 50.2 | 80.4 | medium soft |
| 10 | 50.4 | 53.7 | dark soft |

† Row 2 splits into two saturation sub-bands (columns 2–4 at 50.2%, columns 5–12 at 54.9%) — a mild irregularity discussed in §5, qualitatively different from the row-1 anomaly.

**The single exception to row locking anywhere in the grid: Topaz Sand**, at S 31.4% in a row where all ten other chromatic swatches sit at 25.5%.

### 2.2 Warm-side columns are locked to 20° hue steps

On the warm side of the grid (columns 2–7), each column is locked to one hue — 0°, 20°, 40°, 60°, 80°, 100° — across all ten rows. Computed hue by row for those columns:

```text
        0°-col   20°-col  40°-col  60°-col  80°-col  100°-col
row 1     0.0     41.5 ←    45.0 ←   60.0     80.3     100.6
row 2     0.0     18.8      39.4     60.0     79.7      99.4
row 3     0.0     20.0      40.0     60.0     80.0     100.0
row 4     0.0     19.8      39.7     60.0     80.3     100.2
row 5     0.0     20.0      40.0     60.0     80.0     100.0
row 6     0.0     19.8      39.7     60.0     80.3     100.2
row 7     0.0     18.9      37.9     60.0     76.8      96.8
row 8     0.0     19.5      39.0     60.0     79.5      99.0
row 9     0.0     20.4      39.6     60.0     79.8      99.6
row 10    0.0     19.1      38.3     60.0     80.0      99.1
```

Fifty-eight of the sixty warm-side swatches land within ~3° of their column's target — the scatter is pure 8-bit rounding. The two arrows are Sahara Sand (41.5° in the 20° column — **a 21.5° miss, an order of magnitude beyond rounding**) and Topaz Sand (45° in the 40° column, compounded by the saturation break).

Cool-side columns (8–12) follow a looser scheme — hues shift in coordinated row-bands rather than locking to a single value — so the strict 20°-step rule is specifically a warm-side property. The anomaly sits squarely on the strict side of the grid.

### 2.3 The anomaly, visible in raw RGB

No color theory is needed to see the break. In row 1's warm span, blue holds constant at 190 while green steps evenly toward yellow:

```text
                       R    G    B
Rose Quartz   (0°)    255  190  190
Sahara Sand           255  235  190   ← G should step to ~212, jumps to 235
Topaz Sand            255  235  175   ← same G as Sahara; only broken B in the row
Yucca Yellow  (60°)   255  255  190
Olivine Yellow(80°)   233  255  190
```

Row 2, the control, behaves exactly as the structure predicts:

```text
Medium Coral Light    255  127  127
Cantaloupe            255  167  127
Mango                 255  211  127
Autunite Yellow       255  255  115
Lemongrass            209  255  115
```

## 3. Three independent derivations of the corrected values

The corrected values below were originally proposed by Michael Ray Wilson; the three derivations confirm them independently from the palette's structure.

**Path A — HSV row-structure matching.** Hold row 1's locked S/V (25.5%, 100%) and assign each swatch its column hue. HSV(20°, 25.5%, 100%) → RGB(255, 212, 190). HSV(40°, 25.5%, 100%) → RGB(255, 233, 190).

**Path B — CMYK magenta progression.** Row 1's warm span in CMYK (K=0, C=0, Y=25.5% throughout) implies magenta falling linearly from 25.5% at 0° to 0% at 60°: the 20° and 40° slots take M=17.0% and M=8.5%. Converting those pattern-derived CMYK values back to RGB gives (255, 212, 190) and (255, 233, 190). (The original verification also ran these CMYK inputs through ArcGIS Pro's own CMYK→RGB conversion in-app, with the same result.)

**Path C — direct RGB interpolation.** With R=255 and B=190 fixed across the span, G must step evenly from 190 to 255 in thirds: 190 → 211.7 → 233.3 → 255. Rounding gives G=212 and G=233.

All three paths converge:

| Color | Corrected value | Aligns with |
| --- | --- | --- |
| Sahara Sand | **RGB(255, 212, 190) `#FFD4BE`** | 20° column (Fire Red's family) |
| Topaz Sand | **RGB(255, 233, 190) `#FFE9BE`** | 40° column (Electron Gold's family) |

## 4. Perceptual effect

CIEDE2000 color differences quantify what the eye reports:

| Pair | ΔE2000 | Interpretation |
| --- | --- | --- |
| Sahara vs Topaz — **as published** | **3.6** | at the threshold of distinguishability; effectively duplicates as map fills |
| Sahara vs Topaz — corrected | 12.9 | clearly distinct |
| Corrected Sahara vs Rose Quartz (left neighbor) | 11.6 | normal neighbor spacing |
| Corrected Topaz vs Yucca Yellow (right neighbor) | 9.7 | normal neighbor spacing |

The correction doesn't just satisfy the grid's arithmetic — it restores the even perceptual spacing the rest of row 1 already has.

### 4.1 The pair in grid-wide context

Computing ΔE2000 for all 7,140 pairs among the 120 colors puts the anomaly in perspective. The median nearest-neighbor distance across the palette is 7.6. Sahara–Topaz, at 3.6, sits at less than half of that — but it is not the closest pair in the grid. Eight of the nine closer pairs are **row 2 ↔ row 8 pairings** (e.g., Medium Coral Light vs Medium Coral at ΔE 2.0, Cantaloupe vs Orange Dust at 1.9, Yogo Blue vs Oxide Blue at 1.7): row 8 is very nearly row 2 dimmed by ~4%, so those two design treatments systematically shadow each other across all eleven hue families.

One detail of the row 2/8 overlap deserves its own note: the grid-wide closest pair, Yogo Blue ↔ Oxide Blue, is the only one of these pairings that is **not in the same column**. On the warm side the hue-locked columns make the row 2/8 twins align vertically; on the cool side, the hue re-banding between the upper and lower row groups (§2.2) shifts the blue columns by ~17° — roughly one column step — so Yogo Blue's true twin (213.0° vs 210.7°, ΔE 1.70) sits one column to the *left* in row 8, while its same-column partner drifted to 230.2° (ΔE 12.2). The palette's single closest pair is thus the interaction of two independent structural quirks: the duplicated row treatment and the cool-side band shift. The same shift leaves Apatite Blue (row 2, col 9) with no row-8 twin at all — its hue doesn't exist in row 8's band (same-column ΔE 15.4). The rows 2/8 overlap is analyzed in depth — the generator arithmetic, the dimming cascade behind rows 8–10, the cool-side band mechanism, and the naming evidence of intent — in a companion note: [`row-2-8-overlap.md`](./row-2-8-overlap.md).

What distinguishes Sahara–Topaz is *why* it is close. The row 2/row 8 overlap is a property of two whole rows — two treatments designed (intentionally or not) nearly on top of each other, uniformly, with each color still occupying its correct hue column. Sahara–Topaz is the **only near-duplicate pair within a single row**: two swatches that the grid assigns to *different hue families*, landing on essentially the same hue because one of them broke the structure. Every other adjacent-in-row pair in the entire palette sits at ΔE 4.6 or above; row 1's other adjacent pairs average ~11. Measured across all 218 adjacent boundaries in the grid — 110 horizontal and 108 vertical, median ΔE 13.6 — the Sahara ↔ Topaz boundary is the single tightest.

## 5. Secondary observations

For completeness, the full-grid audit surfaced two milder irregularities, noted here because they are qualitatively different from the Sahara/Topaz break:

The **row 2 saturation split**: columns 2–4 sit at S 50.2% (blue channel 127) while columns 5–12 sit at 54.9% (blue channel 115). This is a consistent two-band structure rather than a one-off outlier, and it produces no near-duplicate colors. Notably, row 8 — otherwise a near-copy of row 2's treatment — does not inherit the split: it uses a uniform minimum channel of 122 across all eleven families (see [`row-2-8-overlap.md`](./row-2-8-overlap.md)).

The **row 7 "Dust" drift**: the dusty row's warm hues run 2–3° flat of their column targets (e.g., Tecate Dust at 37.9°). This is uniform, small, and consistent with rounding at low saturation — again, nothing like a 21.5° miss.

That the rest of the palette holds its structure this tightly is precisely what makes the two row-1 cells stand out.

## 6. Slip or intentional?

The structure alone can't answer that — only the original palette designer could. What can be said: the palette's design rules are otherwise followed to within rounding error across 118 of 120 colors; the two exceptions happen to be adjacent, happen to land on nearly the same hue, and happen to produce the palette's only near-duplicate pair within a row (§4.1). The corrected values follow from the palette's own logic by three independent routes.

## Appendix: reproducing the analysis

The core computation, given the 120 RGB values (Python 3 standard library only):

```python
import colorsys

# hue/sat/val for any swatch
h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)   # h*360, s*100, v*100

# Path A: corrected values from row structure
sahara = colorsys.hsv_to_rgb(20/360, 65/255, 1.0)     # -> (255, 212, 190)
topaz  = colorsys.hsv_to_rgb(40/360, 65/255, 1.0)     # -> (255, 233, 190)
```

Perceptual distances were computed with the standard CIEDE2000 formula (D65, 2° observer) on sRGB→Lab conversions.
