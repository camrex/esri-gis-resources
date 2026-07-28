# The Row 2 / Row 8 Overlap

## Two design treatments in the Esri standard palette, four percent apart

**Companion document to the [Esri (ArcMap/ArcGIS Pro) Standard Color Palette reference](https://camrex.github.io/esri-gis-resources/color-palettes/arcgis-pro-standard-palette/arcgis_pro_palette.html).** This note grew out of the perceptual survey in [`sahara-topaz-analysis.md`](./sahara-topaz-analysis.md) (§4.1), which observed that eight of the palette's ten closest color pairs are row 2 ↔ row 8 pairings. Here that observation is taken apart: what exactly the relationship between the two rows is, where it comes from, and why some columns escape it. The [interactive ΔE explorer](https://camrex.github.io/esri-gis-resources/color-palettes/arcgis-pro-standard-palette/perceptual_distance.html) shows the resulting pairs side by side.

Analysis: Cameron Rex. Last updated: July 2026.

---

## Summary

Row 2 ("light") and row 8 ("medium") of the 120-color grid are the **same saturation treatment (S ≈ 50%) applied at two value levels only 4% apart** (V = 100 vs 96.1), built by the same construction rule. The palette's own names show the pairing is intentional — *Medium Coral Light* (row 2) sits above *Medium Coral* (row 8) — but the 4% value offset is below the threshold of distinguishability on screen, so eight of the eleven hue families collide at ΔE ≤ 4.2. Unlike the Sahara Sand / Topaz Sand anomaly — one cell breaking an otherwise strict structure — this is the opposite kind of finding: **the structure was followed perfectly, and a parameter choice makes two whole rows shadow each other.**

## 1. The generator view

Every chromatic row in the palette reduces to a (max, min) channel pair, with the middle channel interpolated by each column's hue. In those terms rows 2 and 8–10 are:

| Row | (max, min) | S% / V% | Ratio to the row above it |
| --- | --- | --- | --- |
| 2 | (255, 127) cols 2–4 · (255, 115) cols 5–12 | 50.2–54.9 / 100 | — |
| 8 | (245, 122) uniform | 50.2 / 96.1 | **× 0.961 of row 2** |
| 9 | (205, 102) | 50.2 / 80.4 | × 0.837 of row 8 |
| 10 | (137, 68) | 50.4 / 53.7 | × 0.668 of row 9 |

Row 8's endpoints are exactly row 2's first band scaled by 245/255 = 0.9608 (255 → 245; 127 × 0.9608 = 122.02 → 122). Two details show it is a re-run of the recipe rather than a channel-by-channel copy:

- **Row 8 flattens row 2's saturation split.** Row 2 uses minimum channel 127 in columns 2–4 but 115 in columns 5–12 (the two-band structure noted in `sahara-topaz-analysis.md` §5). Row 8 uses 122 everywhere.
- **The middle channels are re-derived, not scaled.** Scaling row 2's middle channels by 0.9608 would give 160 for Orange Dust and 203 for Medium Sand; the actual values are 162 and 202 — consistent with re-interpolating from row 8's own (245, 122) endpoints at the column hue.

## 2. The soft cascade, and the step that is too small

Rows 8 → 9 → 10 form a value ramp at S ≈ 50%, and row 2 is that ramp's natural V = 100 head. Measured perceptually (CIEDE2000, column 2 shown; other columns are similar):

```text
row 2  (max 255)  ─ ΔE 2.0 ─  row 8  (max 245)  ─ ΔE 9.0 ─  row 9  (max 205)  ─ ΔE 18.0 ─  row 10  (max 137)
```

The steps run roughly 2 → 9 → 18: each step doubles, and the first is tiny. Compare the saturated block's ramp (rows 3 → 6, maxes 255 → 230 → 168 → 115), whose first step is ΔE 5.4 — tight, but above threshold. The soft ramp's first step of ~2–2.7 is the entire overlap problem in one number.

Two counterfactuals put the choice in perspective:

- **An evenly placed row 8** (endpoints ≈ (225, 112), V ≈ 88) would sit at ΔE 6.0–6.9 from row 2 across the warm columns — out of the confusable band.
- **Deleting row 8 outright** leaves a clean ramp: row 2 → row 9 is ΔE 11.0, in line with the palette's typical neighbor spacing.

Whether the designer chose 245 as a tidy 255 − 10 or as "96% value," the result is a step the eye cannot use.

## 3. Why some columns escape: the three cool-hue bands

The warm columns (2–7) are hue-locked grid-wide, so their row 2/8 pairs align vertically and all six collide (ΔE 1.9–2.7). The cool columns are where the twinning breaks, because the palette's cool side uses **three distinct hue bands**, not one:

```text
cool hues (deg) at cols 8-12:    c8      c9      c10     c11     c12
rows 1, 6                       ~159    ~201    ~221    ~279    ~321
rows 2, 3, 4, 5                 ~166    ~194    ~213    ~286    ~314
rows 7, 8, 9, 10                ~158    ~211    ~230    ~278    ~331
```

Row 2 uses the middle band; row 8 uses the bottom band. The mechanism is the generator again: rows 7–10 assign lower middle-channel values on the cool side, which pushes every cool color toward its dominant primary — toward green at column 8, toward blue at columns 9–11, toward red at column 12. Where the middle channel drops a little (columns 8 and 11), the hue shifts ~7° and the pair still collides (ΔE 4.2 and 3.5); where it drops more (columns 9, 10, 12), the hue shifts ~17° — roughly one column step — with three different outcomes:

| Column | Row 2 color | Row 8 same-column | ΔE | Outcome |
| --- | --- | --- | --- | --- |
| 9 | Apatite Blue | Oxide Blue | 15.4 | escapes — no row-8 twin exists for its hue |
| 10 | Yogo Blue | Medium Azul | 12.2 | escapes its column — but lands on Oxide Blue one column left at **ΔE 1.70, the grid's closest pair** |
| 12 | Fuchsia Pink | Medium Fuchsia | 8.2 | genuinely escapes |

The grayscale column sits outside all of this: column 1 is an independent 10%-step gray ramp running down the rows, so r2c1/r8c1 are Gray 10% vs Gray 70% (ΔE 48.7).

## 4. The names say it was deliberate

| Col | Row 2 | Row 8 |
| --- | --- | --- |
| 2 | Medium Coral **Light** | **Medium** Coral |
| 3 | Cantaloupe | Orange Dust † |
| 4 | Mango | **Medium** Sand |
| 5 | Autunite Yellow | **Medium** Yellow |
| 6 | Lemongrass | **Medium** Lime |
| 7 | Light Apple | **Medium** Key Lime |
| 8 | Beryl Green | Light Vert |
| 9 | Apatite Blue | Oxide Blue |
| 10 | Yogo Blue | **Medium** Azul |
| 11 | Heliotrope | **Medium** Lilac |
| 12 | Fuchsia Pink | **Medium** Fuchsia |

Eight of the eleven chromatic row-8 names are "Medium X," and the column-2 pair makes the intent explicit: row 8 is the designed "medium" counterpart to row 2's light series. († Orange Dust is a naming stray — every other "Dust" name lives in row 7.)

## 5. Design, not error — but sub-threshold design

This is what distinguishes the overlap from the Sahara/Topaz anomaly. There, one cell breaks the palette's rules and the fix follows from the rules themselves. Here the rules were applied cleanly; the palette simply contains two soft treatments whose parameters differ by less than the eye can resolve. Eleven intentional color distinctions were designed, named, and published — and eight of them do not survive rendering.

The practical guidance for map-making follows directly: **treat rows 2 and 8 as alternates, not companions.** Used together, their 22 chromatic swatches collapse into about 13 distinguishable colors (nine pairs merge below ΔE 4.3, including the cross-column Yogo/Oxide pair). Pick whichever row's names or exact values a workflow expects, and take additional soft colors from rows 9 and 10, which are comfortably spaced.

## Appendix: reproducing the analysis

Given the 120 RGB values (Python 3 standard library only):

```python
# each chromatic row reduces to (max, min) channel endpoints
row2_warm = (255, 127)          # cols 2-4; cols 5-12 use (255, 115)
row8      = (245, 122)          # uniform

245 / 255                        # -> 0.9608
round(127 * 245 / 255)           # -> 122  (row 8 = row 2's first band, rescaled)

# hue bands: compare computed HSV hue for (row, col) across rows 1-10, cols 8-12
import colorsys
h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)   # h*360 gives the tables in section 3
```

Perceptual distances were computed with the standard CIEDE2000 formula (D65, 2° observer) on sRGB→Lab conversions, as in [`sahara-topaz-analysis.md`](./sahara-topaz-analysis.md).
