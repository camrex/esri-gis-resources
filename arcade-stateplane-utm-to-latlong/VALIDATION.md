# Validation report

**What this document sets out to show is parity, not accuracy.** The expression makes no
claim to be better than what ArcGIS already gives you; the question is whether inlining
the inverse projection maths — so that it can run in a popup, a label or an attribute
rule, across every zone at once rather than one hand-tailored zone at a time — costs
anything against ArcGIS's own answer. Every measurement below is a *difference from
ArcGIS*, not an error against ground truth.

Reference implementation: **`arcpy` 3.7 / ArcGIS Pro 3.7**. Every figure below is
reproducible with the scripts in [`scripts/`](scripts/).

`arcpy` is the reference rather than PROJ deliberately. The expression exists to invert
what ArcGIS stored, so ArcGIS's own definition of each zone is the one that counts —
and the two registries disagree.

## Coverage

| | |
|---|---|
| EPSG codes | 1,139 |
| State Plane | 908 |
| UTM / BLM | 231 |
| Distinct parameter sets | 254 |
| WKID lookup runs | 380 |

A US-only variant (1,081 codes, dropping the 58 UTM codes outside US territory) was
built and measured. It saved 1.4 KB and 1.9% of run time — the WKID run table is the
same 380 entries either way, so only the zone table shrinks — while silently rejecting
any UTM data from outside the US. It was dropped rather than published as a second
artifact; `scripts/us_codes.txt` keeps the list as a worked example.

Realizations: NAD83, NAD83(HARN), NAD83(CORS96), NAD83(NSRS2007), NAD83(2011),
NAD83(PA11), NAD83(MA11), and WGS 84 for the 326xx/327xx UTM zones. Linear units:
metre, US survey foot, international foot. Projection methods: Transverse Mercator,
Lambert Conformal Conic (2SP), Hotine Oblique Mercator (Alaska zone 1).

Every code the build claims resolves in `arcpy`, and every code it excludes is
**rejected** rather than mapped to a neighbouring zone — checked explicitly for all
1,139 codes in both directions.

## Method

Two independent execution paths, because neither alone is sufficient.

**Headless.** The build's actual Arcade text is loaded verbatim into Node.js with the
Arcade built-ins mapped to their JavaScript equivalents, driven by a mock `$feature`.
For each code, a grid of latitude/longitude points is laid across the zone's usable
extent, forward-projected by `arcpy` **inside that code's own geographic system** so no
datum transformation contaminates the comparison, and the returned coordinates compared
with the originals. Error is ground distance on that code's own ellipsoid, in
millimetres — not a coordinate-component difference.

**Real engine.** The same text is executed by the actual ArcGIS Arcade engine through
`CalculateField`, one scratch feature class per EPSG code, and compared with `arcpy`'s
own inverse of the **stored** coordinates so that geodatabase quantisation is never
mistaken for script error.

Run over the same 1,139 codes the two paths agree to within that quantisation — median
0.037 mm headless against 0.038 mm in the engine, worst case 0.059 mm against 0.071 mm
— which is what makes the fast headless path trustworthy for bulk work.

## Results

**55,811 headless points across 1,139 codes; 28,475 points in the real engine.**

| Statistic | Headless | Real Arcade engine |
|---|---|---|
| Median | 0.037 mm | 0.038 mm |
| 95th percentile | 0.049 mm | 0.059 mm |
| 99th percentile | 0.058 mm | 0.064 mm |
| **Worst case** | **0.059 mm** | **0.071 mm** |

Both styles — condensed and documented — return **bit-identical** values over the full
point set in all four output modes, 446,488 values compared, and match the reference
implementation they were derived from. Zero runtime errors in any pass.

### Where the difference comes from

Running the same text with successively better inputs separates the series maths from
everything layered on top of it. Only the last row is a mistake; the rest is the cost of
storing and printing a number:

| | Worst difference from ArcGIS |
|---|---|
| Algorithm alone | 0.012 mm |
| \+ the deliberate `Round(…, 9)` on output | 0.059 mm |
| \+ file geodatabase coordinate storage | 0.071 mm |
| \+ EPSG's published constants instead of ArcGIS's | 1.004 mm |

Nine decimals of a degree is about 0.11 mm, which is below the storage grid, so the
rounding costs nothing real. The last row is the one worth avoiding, and it is free to
avoid: read the parameters instead of typing them.

### Why EPSG's published values are not used

Building from EPSG's tables rather than `arcpy` leaves 191 of 1,139 codes disagreeing
with ArcGIS, each traceable to one constant:

| Cause | Codes | Worst |
|---|---|---|
| False-easting overrides derived from PROJ | 28 | 1.002 mm |
| Scale factor truncated to 9 decimals (`0.999941177` vs ArcGIS's exact `0.9999411764705882`) | 134 | 0.367 mm |
| False origin in the zone row | 26 | 0.798 mm |
| Hotine azimuth, 7×10⁻⁹° off | 3 | 0.878 mm |

ArcGIS's registry is not perfectly self-consistent either: EPSG **9748/9749**
(Alabama, ftUS) carry a truncated scale factor where every sibling Alabama code carries
the exact one. Grouping zones by full parameter identity handles that without a special
case.

## Against Calculate Geometry Attributes

The absolute error matters less than a simpler question: does this return the number
ArcGIS Pro's own **Calculate Geometry Attributes** would have returned? That tool is
the familiar way to put lat/long on a feature class, and the only reason it is not the
answer here is that it is a geoprocessing tool — it cannot run in a popup, a label, or
an attribute rule.

It returns the same number. Asked for the source's own geographic system — no datum
change, which is exactly what an inverse projection performs — the two agree to the
last digit Calculate Geometry reports. That tool writes 8 decimal places of a degree;
this expression writes 9.

| Stored in | Median | Worst | Identical at 8 decimals |
|---|---|---|---|
| Illinois East ftUS (6455, TM) | 0.42 mm | 0.71 mm | 177 / 200 |
| Texas Central (32139, LCC) | 0.44 mm | 0.73 mm | 173 / 200 |
| UTM 15N (26915, TM) | 0.46 mm | 0.78 mm | 174 / 200 |
| Alaska 1 (26931, Hotine) | 0.46 mm | 0.78 mm | 178 / 200 |

That residual is Calculate Geometry's own output precision, not either one's error: one
unit in its final digit is 1.1 mm, and every disagreement is one unit or none.
Reproduce with `scripts/compare_calc_geometry.py`.

### The datum, in the same terms

Ask Calculate Geometry for **WGS 84** instead of the source's own geographic system and
ArcGIS may insert an explicit transformation. Whether it does is decided by the data's
extent, not only by its datum — the same tool, on the same datum, chooses differently:

| Source | Transformation ArcGIS chose | Shift |
|---|---|---|
| NAD83 / UTM 15N (Minnesota) | none — null transformation | 0.00 m |
| NAD83 / Texas Central | `WGS_1984_(ITRF00)_To_NAD_1983` | 1.00 m |
| NAD83(2011) / Illinois East ftUS | `WGS_1984_(ITRF08)_To_NAD_1983_2011` | 0.96 m |

That is a thousand times everything else in this document. It is a decision about which
WGS 84 you mean rather than a question of accuracy, and it lands on the geoprocessing
tool exactly as it lands on this expression — which is the point of saying so here.

## Behaviour at zone edges

The Transverse Mercator series is flat well past any real zone width, then degrades.
Lambert Conformal Conic has no longitude series and stays flat everywhere.

| Δλ from central meridian | Illinois East (TM) | UTM 15N (TM) | Texas Central (LCC) |
|---|---|---|---|
| ≤ 3.5° | 0.03 mm | 0.00 mm | 0.03 mm |
| 4° | 0.11 mm | 0.11 mm | 0.03 mm |
| 6° | 1.44 mm | 1.56 mm | 0.03 mm |
| 10° | 92 mm | 94 mm | 0.03 mm |

State Plane TM zones are about 2° wide and UTM zones 6°, so real data sits well inside.
The risk is data stored *outside* its own zone — a statewide layer forced into one
county's projection. The expression does not warn; it just gets quietly worse.

## Edge cases

| Input | Result |
|---|---|
| Null or absent geometry | `null`, or an `errorMessage` in RULE mode |
| NAD27, Web Mercator, WKID 0, any unsupported code | rejected with a message |
| Geographic feature class (4326, 4269, 6318, …) | centroid passed straight through |
| UTM zones 1N and 60S | correct across the antimeridian |
| NaN or absurd coordinates | rejected, not returned |
| Feature at x=0, y=0 | returns a real-looking coordinate — see below |

A feature at the projection origin returns a plausible coordinate, because 0,0 *is* a
real place in every projected system. Nothing in an expression can distinguish that
from a genuine point; only a zone-extent sanity check would.

## Arcade-specific static checks

Arcade is **case-insensitive** for identifiers, so `U` and `u` are the same variable —
invisible to a JavaScript harness. `lint.py` checks for it, and caught two real bugs
during development: a `U`/`u` collision in the Hotine routine that silently corrupted
the longitude, and a global colliding with a local of the same name in different case.

Both builds pass with zero findings: no case-insensitive collisions, no identifiers
shadowing an Arcade built-in, no reserved words, no multi-declarator `var`, no calls to
undefined functions, no non-ASCII characters, and only `$feature` referenced.

**There is no interior-point function to use instead of `Centroid`.** Checked by
execution in Pro 3.7: `Centroid` and `Extent` resolve, and `LabelPoint`,
`InteriorPoint`, `PointOnSurface`, `TrueCentroid`, `Center` and `CenterPoint` all fail
with *Object not found*. On a C-shaped polygon built for the purpose, Arcade's
`Centroid` lands **outside** the polygon and agrees with `arcpy`'s `.trueCentroid`,
which is also outside; `arcpy`'s `.centroid` — the label point — is inside, and has no
Arcade counterpart. So the caveat above is a property of the language, not a choice
made here.

Engine capabilities were confirmed by execution rather than assumption: `Log` is
natural log, `Max` accepts both varargs and an array, `Text(wkid)` yields `"6455"`
rather than `"6455.0"` so dictionary keys match, and `++`, `break`, `Push`, `Includes`,
`Count` and `%` all work. `Array.length` does **not** — Arcade needs `Count()`.

## Performance

Arcade rebuilds literal data tables on **every feature**, so lookup-table *entry count*
drives run time and file size does not.

| Build | Codes | Size | Calculate Field |
|---|---|---|---|
| Flat 1,139-entry dictionary | 1,139 | 31.9 KB | 1,646 µs/feature |
| Re-encoded, same entry count | 1,139 | 24.4 KB | 1,698 µs — no gain |
| **Run-compressed (published)** | 1,139 | 21.3 KB | **978 µs** |
| Run-compressed, US-only scope | 1,081 | 19.9 KB | 960 µs |
| Single zone, generated per dataset | 1 | 6.1 KB | 498 µs |

The pattern is roughly 480 µs fixed plus 1 µs per table entry, per feature. Collapsing
the WKID table into 380 arithmetic runs is what buys both the size and the speed.

Comments and long identifiers cost nothing. The two published builds differ by 30% in
size and by 0.3% in speed: **963 µs/feature documented against 966 µs condensed**, over
8,000 features in Illinois East ftUS. The same held on an earlier pair of the same
program at 32 KB and 57.5 KB — 1,686 µs against 1,688 µs.

`bench.py` reproduces the last row pair, which is the one that matters. The four
exploratory encodings above it were measured on the way to the published build and are
not kept in the repository; `build_expression.py` is what replaced them.

## Datum

Measured with `arcpy` at Chicago, Springfield, Denver, Los Angeles, Miami and Honolulu:
projecting to WGS 84 **without naming a transformation** shifts by exactly **0.000 m**
for NAD83, NAD83(HARN) and NAD83(2011). That is the null transformation, stated accuracy
2 m, so the output is EPSG:4326 under the standard definition. An inverse projection
behaves the same way, because it does not touch the datum at all.

ArcGIS still *offers* explicit transformations, and applying one moves the same
coordinate by up to **1.54 m** — four orders of magnitude above the 0.07 mm this
document otherwise spends its time on.

### "ArcGIS's default" is not one thing

This is worth stating precisely, because two ArcGIS pathways to the same destination
disagree. On a single NAD83 / Texas Central point, asked for WGS 84:

| Pathway | Transformation applied | Result |
|---|---|---|
| `projectAs(4326)`, none named | null | coordinate unchanged |
| **Calculate Geometry Attributes → WGS 84** | `WGS_1984_(ITRF00)_To_NAD_1983` | **0.935 m away** |

Calculate Geometry chooses by the data's *extent*, so it is not even consistent across
one datum: for NAD83 / UTM 15N in Minnesota it picked the null transformation and moved
the point 0.000 m, while for Texas it picked ITRF00 and moved it most of a metre.

This expression matches the first row — it returns geodetic coordinates on the source
datum, untouched. If a downstream consumer expects the second, the difference is about
a metre, and it is a decision about which WGS 84 is meant rather than a question of
accuracy. Reproduce with `scripts/probe_datum.py` and `scripts/compare_calc_geometry.py`.

## Live test

Applied as a real attribute rule to a 47,630-parcel county layer in NAD83(2011) UTM
zone 19N. All 47,630 rows verified against `arcpy` — **worst 0.068 mm**. The rule fired
correctly on insert and update, stayed inert while disabled, and blocked an edit with a
readable message when handed an unsupported spatial reference.

That test is also where the centroid behaviour showed up: 449 parcels (0.94%) have a
centroid outside the parcel, one of them by 4.7 km. `arcpy`'s `.centroid` quietly
returns the label point in that situation while Arcade returns the true centroid, so a
naive comparison of the two reports a 269 m "error" that is nothing of the sort.

---

Validation directed by **Cameron Rex** (RMI Valuation LLC) and performed with
**Claude** (Anthropic's AI model).
