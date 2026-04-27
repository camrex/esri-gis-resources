# Color conversion behavior in ArcGIS Pro

This document describes how ArcGIS Pro's Color Editor displays HSV, HSL, and CMYK values for an underlying RGB color. The findings here are based on empirical testing — entering known RGB values into the Color Editor and recording what each color space displays — rather than on official Esri documentation, which doesn't specify these conversion details.

The practical short version: **HSV and HSL use standard textbook formulas, but CMYK uses a non-normalized variant that differs from print-industry CMYK whenever the K channel is above zero.** If you copy CMYK values out of AGP's Color Editor and paste them into print-prep software, the colors will not match your intent.

## Methodology

Findings were determined by entering known RGB values into ArcGIS Pro 3.6's Color Editor and recording the displayed values for each color space. Where a candidate formula could be derived analytically, predictions were generated for several test colors and compared against AGP's displayed values. Findings were considered confirmed when predictions matched AGP's display exactly across multiple test cases spanning the relevant input ranges.

This approach can verify what AGP displays but cannot determine what AGP does internally. The findings should be read as "AGP's Color Editor displays values consistent with [this formula]" rather than as definitive statements about Esri's implementation.

Color management was disabled during testing (the AGP default).

## HSV

ArcGIS Pro's Color Editor displays HSV values consistent with the standard RGB-to-HSV formula:

```text
M = max(R, G, B) / 255
m = min(R, G, B) / 255
V = M
S = (M - m) / M   when M > 0, else 0
H = 60° × hue-from-channels   (standard piecewise H formula)
```

Display precision: 2 decimal places, with trailing zeros trimmed (e.g., 100, 25.49, 50.2).

### HSV Verification examples

| RGB | AGP HSV |
| --- | --- |
| (255, 235, 175) Topaz Sand | (45, 31.37, 100) |
| (168, 0, 0) Tuscan Red | (0, 100, 65.88) |

These match the standard formula to displayed precision.

## HSL

ArcGIS Pro's Color Editor displays HSL values consistent with the standard RGB-to-HSL formula:

```text
M = max(R, G, B) / 255
m = min(R, G, B) / 255
L = (M + m) / 2
S = (M - m) / (M + m)         when L < 0.5
S = (M - m) / (2 - M - m)     when L >= 0.5
S = 0                         when M = m
H = same as HSV
```

Display precision: 2 decimal places, trailing zeros trimmed.

### HSL Verification example

| RGB | AGP HSL |
| --- | --- |
| (255, 235, 175) Topaz Sand | (45, 100, 84.32) |

Matches the standard formula exactly.

## CMYK

ArcGIS Pro's Color Editor displays CMYK values consistent with a **non-normalized formula** with additive K extraction:

```text
K = 1 - max(R, G, B) / 255
C = (1 - R/255) - K
M = (1 - G/255) - K
Y = (1 - B/255) - K
```

All four channels expressed as percentages (× 100), 2 decimal places, trailing zeros trimmed.

**This is not the CMYK formula most other software uses.** The conventional ("normalized") CMYK formula divides each of C, M, and Y by `(1 - K)` after extraction, which scales them to fill the 0-100 range. The non-normalized formula AGP uses preserves the additive property `C + K`, `M + K`, `Y + K` = inverse RGB but produces different C/M/Y values whenever K > 0.

### CMYK Verification examples

| RGB | AGP CMYK | Conventional CMYK |
| --- | --- | --- |
| (255, 0, 0) Mars Red | (0, 100, 100, 0) | (0, 100, 100, 0) |
| (255, 235, 175) Topaz Sand | (0, 7.84, 31.37, 0) | (0, 7.84, 31.37, 0) |
| (168, 0, 0) Tuscan Red | (0, 65.88, 65.88, 34.12) | (0, 100, 100, 34.12) |
| (0, 76, 115) Steel Blue | (45.1, 15.29, 0, 54.9) | (100, 33.91, 0, 54.9) |

For colors where one of R, G, or B is at 255 (which forces K = 0), the two formulas agree. For colors where all three RGB channels are below 255 (which forces K > 0), the non-normalized values are systematically lower than conventional CMYK on the C, M, and Y channels.

### Practical implication

Copying CMYK values from AGP's Color Editor and using them in print-prep software will produce colors that do not match what was intended. The AGP Color Editor CMYK display is best understood as an alternative numeric notation for the underlying RGB value, not as a print-ready specification. For actual print work, color-managed export through a CMYK output profile (such as U.S. Web Coated SWOP v2, which AGP supports) produces values appropriate for press.

## Color profiles vs. Color Editor display

ArcGIS Pro tags color items with ICC profiles. The default profiles, observable in the bundled `Styles.stylx` file, are:

- **RGB**: sRGB IEC61966-2.1
- **CMYK**: U.S. Web Coated (SWOP) v2

These profiles affect color-managed workflows — exporting items with embedded profiles, converting between RGB and CMYK project items, displaying on calibrated devices. They do **not** affect the values shown in the Color Editor, which are computed using the mathematical formulas above regardless of the profile assignments and regardless of whether color management is enabled in the application.

In other words: AGP holds two parallel notions of "what this color is in CMYK":

1. **The Color Editor display value** — a mathematical conversion using the non-normalized formula above
2. **The color-managed CMYK value** — what the SWOP v2 profile (or any other tagged CMYK profile) would produce for color-managed conversion or output

These are different numbers. The Color Editor display is convenient for picking and adjusting; the color-managed value is what matters for production output.

## What's not covered here

### Lab

The Color Editor displays Lab values, but the conversion was not fully characterized. AGP's Lab display rounds to integer precision and uses D50 illuminant (based on partial testing), but the specific chromatic adaptation transform produces values that don't exactly match standard Bradford-adapted predictions for highly saturated reds. Whether this reflects a non-Bradford adaptation, a custom implementation, or some other factor was not determined. Anyone needing precise Lab values from AGP for cross-tool work should verify against their target tool's expected values rather than relying on AGP's display.

### Color-managed conversions

This document covers what the Color Editor *displays*. The internal Lab/XYZ pivot space used during color-managed conversion is described in [Esri's color management documentation](https://pro.arcgis.com/en/pro-app/latest/help/projects/use-color-management.htm) at a high level, but the specific transforms used during color-managed conversion were not tested.

## Reproducing these findings

Anyone with ArcGIS Pro can reproduce these findings:

1. Open any color in the Color Editor (Symbology pane → click a color → Color Properties)
2. Enter the test RGB values from the verification tables above
3. Record what AGP displays in the HSV, HSL, and CMYK fields
4. Compare against the predictions from the formulas

The findings here were tested on ArcGIS Pro 3.6 with default settings (color management disabled). Behavior may differ in earlier versions or with custom color management configurations.

## Acknowledgments

This characterization came out of a broader analysis of the Esri ArcGIS Colors palette, where verifying the exact CMYK values displayed in AGP became necessary to validate corrections derived from pattern analysis. The non-normalized CMYK formula was identified by Cameron Rex through empirical testing during that work.
