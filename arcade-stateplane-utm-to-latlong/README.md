# State Plane / UTM → Latitude & Longitude, in Arcade

An ArcGIS Arcade expression that converts a feature's stored projected coordinates to
latitude and longitude — in Calculate Field, in a popup, or as an attribute rule that
keeps the values current as features are edited.

> **Not an Esri product.** This is a personal project, part of my own
> [collection of Esri-related resources](https://github.com/camrex/esri-gis-resources).
> It is not affiliated with, endorsed by, or supported by Esri, and Esri Technical Support
> does not cover it. It was checked *against* ArcGIS, not by the people who make ArcGIS —
> see [VALIDATION.md](VALIDATION.md) for exactly what was measured, and test it on your own
> data before you trust it. Esri, ArcGIS and ArcGIS Pro are trademarks of Esri.

**The problem it solves:** Arcade cannot reproject. A calculation against a feature
class stored in a projected coordinate system returns *northing and easting*, not
latitude and longitude. The numbers come back plausible and wrong, which is the
failure mode that survives review. The only way through is to inline the inverse
projection maths, which differs per projection — so this build carries the parameters
for every zone and picks the right ones from the feature's own WKID at run time.

**The claim is parity, not accuracy.** Versions of this have circulated for years, each
one written for a single State Plane zone or a single UTM zone, with its constants typed
in. The exercise here was whether *one* expression could cover all of them — pick the
right parameters from the feature's own WKID, pass geographic data straight through
untouched, work in an attribute rule — and still return what ArcGIS itself returns.
It does. Nothing here is more accurate than Calculate Geometry Attributes, and nothing
is meant to be. The point is that you give up nothing by doing it in Arcade, where a
geoprocessing tool cannot go.

**[Browse the landing page →](https://camrex.github.io/esri-gis-resources/arcade-stateplane-utm-to-latlong/)**

**One build, 1,139 EPSG codes**, in two styles:

| | Size | Use it when |
| --- | --- | --- |
| [`arcade_latlong_documented.txt`](builds/arcade_latlong_documented.txt) | 30 KB | always, unless the dialog is cramped |
| [`arcade_latlong_condensed.txt`](builds/arcade_latlong_condensed.txt) | 21 KB | pasting somewhere tight |

They are the **same program** and run at identical speed — measured over 8,000 features
at 963 µs/feature for the documented build against 966 µs for the condensed one, a
build 30% smaller. Comments and long identifiers cost nothing, because Arcade's
per-feature cost comes from rebuilding the literal data tables, not from parsing.

Coverage is every US State Plane zone across seven NAD83 realizations, plus every UTM
zone worldwide on WGS 84 and the NAD83 realizations, plus the BLM foot zones. A
US-only variant was measured and dropped: it saved 1.4 KB and about 2% of run time, and
in exchange it silently rejected any UTM data from outside the US. `scripts/us_codes.txt`
is kept as a worked example if you want to trim anyway.

## Parity

Everything below exists to answer one question — *does inlining the maths cost you
anything?* — and the answer is no. These are not accuracy claims. They are the evidence
that the expression lands on the same answer ArcGIS does.

**It returns what Calculate Geometry Attributes returns.** Asked for the source's own
geographic system, the two agree to the last digit that tool reports: it writes 8
decimal places of a degree, this writes 9, and rounded to its precision they match.
Checked across Transverse Mercator, Lambert Conformal Conic, UTM and Hotine zones, the
worst disagreement is one unit in Calculate Geometry's final digit. The difference
between the two is not accuracy — it is that Calculate Geometry is a geoprocessing tool
and cannot run in a popup, a label, or an attribute rule.

The rest is the same finding measured other ways. Worst case **0.07 mm** in the real
ArcGIS Arcade engine with the data stored in file geodatabases — which is the
geodatabase's own storage grid, since it quantises coordinates at 0.0001 m and so
displaces a point by up to 0.07 mm before the expression sees it. The disagreement
never rises above the noise floor of where the data lives.

Headless, against `arcpy`'s own projection engine over 55,811 reference points:

| | Worst difference |
| --- | --- |
| Algorithm alone | 0.012 mm |
| With the deliberate 9-decimal rounding of the output | 0.059 mm |
| In a file geodatabase, real Arcade engine | 0.071 mm |

Parity is also why zone parameters are read from `arcpy.SpatialReference` rather than
EPSG's published tables. ArcGIS and EPSG disagree on some constants, and the stored
coordinates were made with ArcGIS's — so building against EPSG's rounded values pulls
the answer up to **1.0 mm** away from the one ArcGIS would give, which is the only kind
of error that counts here. See [VALIDATION.md](VALIDATION.md).

## Quick start

**Calculate Field.** Paste a build in as an Arcade expression, set `MD` at the top to
`"LAT"`, and target a **Double** field. Repeat with `"LON"`. A Float field is single
precision and caps you near 0.2 m, which would throw away the agreement before you ever
saw it.

**Popup or label.** Set `MD = "BOTH"` for `Lat: 37.4952, Lon: -89.09`. This one is
display text, formatted by `FMT` to six decimals — about 0.1 m, rather than the nine
decimals the numeric modes return.

**Attribute rule.** Set `MD = "RULE"` and the two field names just below it, then add a
Calculation rule with the field left blank. Five things testing showed you want:

- The feature class needs a **GlobalID** field, or rule creation fails with ERROR 002710.
- **Triggering fields are an explicit list, not a switch.** Leave it empty and every
  update fires the rule — aggressively enough that a Calculate Field setting the two
  fields to null is undone by the same edit. Name the **shape field** and only geometry
  changes fire it, which is usually what you want. Inserts fire either way.
- **The list can be any fields you like, including a single ordinary attribute.** That
  gives you a deliberate recalculation handle: null the two fields, name a spare
  attribute as the triggering field, then edit that attribute — and the lat/long fills
  in. It is the quickest way to prove the rule works, and a way to re-run it over
  chosen rows without touching geometry.
- An immediate rule never touches rows that already exist. Seed those once with
  Calculate Field.
- A feature the expression cannot convert — no geometry, or an unsupported WKID —
  returns an `errorMessage`, and that **aborts the edit** rather than writing null. If
  a load inserts attributes before shapes, leave the rule disabled until the geometry
  is in. The non-RULE modes just return `FV` (null by default).

`scripts/rule_from_csv.py` packages all of that into an Export-Attribute-Rules CSV that
`ImportAttributeRules` applies to as many feature classes as you like.

## What it handles

- **Transverse Mercator** — every State Plane TM zone, and all UTM (UTM *is* TM)
- **Lambert Conformal Conic (2SP)** — the State Plane conic zones
- **Hotine Oblique Mercator** — State Plane Alaska zone 1, the only US zone that uses it
- **Geographic feature classes** pass straight through: if the data is already in
  degrees, the centroid *is* the answer, so one expression covers WGS84 and State
  Plane layers alike and you do not need to branch per feature class.
- **Any geometry type.** Points, polylines, polygons, multipoints.

### Two things to know before you trust it

**Polygons report the area centroid, which can fall outside the polygon.** Arcade's
`Centroid()` is the true centroid, not a guaranteed-inside label point, and Arcade has
no equivalent of one. On a real 47,630-parcel county layer this affected **449 parcels
(0.94%)**, and on one 27,840-vertex parcel wrapping a lake the centroid sat **4.7 km**
from the parcel. If the coordinate must land *on* the feature, an attribute rule cannot
give you that.

**NAD27 is deliberately unsupported.** NAD27 codes are on Clarke 1866 *and* need a
NADCON grid shift of up to about 100 m to reach WGS84. Inverting the projection alone
gets you the first part and not the second, so the result would look right and be up to
100 m wrong. **Carrying a grid shift was not attempted here** — that is a scope
decision rather than a claim about what Arcade can be made to do — so those WKIDs are
rejected with a message instead of being silently mishandled. The same reasoning
excludes OSGB36, Tokyo Datum and others: reproject first, or take it on as an
extension.

### Datum

An inverse projection does not change datum; it returns geodetic coordinates on the
source datum. WGS 84 / UTM sources give EPSG:4326 outright. NAD83-family sources give
NAD83 geodetic, which ArcGIS treats as EPSG:4326 through a null transformation with a
stated accuracy of 2 m — measured at exactly 0.000 m shift for NAD83, HARN and
NAD83(2011). If a downstream consumer applies an *explicit* NAD83→WGS84 transformation
instead, the same coordinate moves by up to **1.5 m**, which dwarfs everything else on
this page.

Worth knowing that **"what ArcGIS does by default" is not one thing.** On the same
NAD83 / Texas Central point asked for WGS 84, `projectAs` with no transformation named
returns the coordinate unchanged, while Calculate Geometry Attributes applies
`WGS_1984_(ITRF00)_To_NAD_1983` and lands **0.935 m** away. Calculate Geometry picks by
the data's extent, so it is not consistent even within NAD83 — for UTM 15N in Minnesota
it picked the null transformation and moved nothing. This expression matches the
untouched-datum behaviour. Say which you mean; `scripts/probe_datum.py` and
`scripts/compare_calc_geometry.py` measure both.

## Adapting it beyond the US

The maths is not US-specific — only the shipped code list is. Any EPSG code using one
of the three implemented projection methods will build, on any ellipsoid, in any linear
unit:

```powershell
# with ArcGIS Pro's Python -- build_expression.py reads its parameters from arcpy
python scripts/build_expression.py --codes 25832,25833 --out etrs89_utm.txt
python scripts/build_expression.py --codes @my_codes.txt --style documented --out mine.txt
```

Codes using a method that is not implemented are reported and refused rather than
silently mishandled, and codes whose datum needs a grid shift are excluded unless you
pass `--allow-datum-shift`. To add a projection method, write its inverse next to
`iTM` in `scripts/template_documented.py` and give it a new type number.

### Please send them back

The US scope here reflects where the author works, nothing more. If you build a code
list for your own country — ETRS89 and the national grids, GDA2020 and MGA, the SIRGAS
realizations, JGD2011, anything — **please open an issue or a pull request.** A
contributed `codes.txt` plus the validator output is enough; the build is generated, so
a code list is genuinely the whole contribution. The same goes for a projection method
this does not implement yet: Krovák, Stereographic, Cassini and the rest are all
inverses that would slot in beside `iTM` under a new type number.

Grid-shift datums are the honest open problem. NAD27, OSGB36 and their relatives need a
shift this build does not attempt, and if someone has a workable approach, that is a
conversation worth having in the issues.

## Verifying it yourself

Everything used to validate this is in [`scripts/`](scripts/), including the harness
that executes the Arcade text under Node and the arcpy reference generator. See
[scripts/README.md](scripts/README.md).

**Most of those scripts require `arcpy`,** which ships with ArcGIS Pro and cannot be
pip-installed — run them with ArcGIS Pro's Python rather than an ordinary virtual
environment. `lint.py` is the exception worth knowing about: it is pure Python and runs
anywhere, including in CI.

```powershell
python scripts/validate.py builds/arcade_latlong_condensed.txt      # vs arcpy, headless
python scripts/lint.py builds/arcade_latlong_condensed.txt          # Arcade-specific checks
python scripts/run_in_arcade.py builds/arcade_latlong_condensed.txt # the real engine
```

`lint.py` is worth running after any edit. Arcade identifiers are **case-insensitive**,
so `U` and `u` are the same variable — a hazard invisible to a JavaScript test harness,
and one that produced a real bug during development of this very file.

## Credits

**This is a culmination, not an invention.** The approach — inline the inverse
projection in Arcade, because Arcade cannot reproject — was worked out on Esri
Community over many years, by people posting zone-specific expressions, correcting each
other's constants, and porting the older GeoNet SQL versions across. What is new here is
scope: every zone in one expression, parameters chosen from the feature's own WKID, and
the whole thing checked against ArcGIS rather than trusted. The maths underneath is
theirs and Snyder's.

The threads this stands on:

- [Formula For State Plane to Lat/Lon Conversion](https://community.esri.com/t5/coordinate-reference-systems-questions/formula-for-state-plane-to-lat-lon-conversion/td-p/870543)
  — the long-running one, where the inverse Lambert and Transverse Mercator formulations
  were hashed out
- [Arcade Script For Converting From State Plane to Decimal Degrees](https://community.esri.com/t5/arcgis-arcade-questions/arcade-script-for-converting-from-state-plane-to/td-p/1580648)
  — the SQL-to-Arcade port
- [Converting Coordinates with Attribute Rules](https://community.esri.com/t5/attribute-rules-questions/converting-coordinates-with-attribute-rules/td-p/226552)
- [Attribute Rule: Latitude and Longitude](https://community.esri.com/t5/arcgis-pro-questions/attribute-rule-latitude-and-longitude/td-p/1038312)
- [Get Latitude and Longitude from geometry](https://community.esri.com/t5/attribute-rules-questions/get-latitude-and-longitude-from-geometry/td-p/1561004)
- [Arcade convert State Plane Coordinates to WGS84](https://community.esri.com/t5/arcgis-pro-questions/arcade-convert-state-plane-coordinates-to-wgs84/td-p/1334388)
- [ArcGIS Idea: Arcade projectAs Geometry Function](https://community.esri.com/t5/arcgis-pro-ideas/arcade-projectas-geometry-function/idi-p/1171382)
  — the request that would make all of this unnecessary. Vote for it.

If you are one of the people behind those posts and want to be named here — or you know
who should be — please [open an issue](https://github.com/camrex/esri-gis-resources/issues).
Named credit is owed and will be added.

Assembled and validated by **Cameron Rex** ([RMI Valuation LLC](https://rmivaluation.com)),
with **Claude** (Anthropic's AI model). The inverse-projection formulations follow
Snyder, *Map Projections — A Working Manual* (USGS Professional Paper 1395); the
rectifying-radius cross-check is against NOAA NOS NGS 5.

MIT licensed, like the rest of this repository — use it however you like. Attribution
is appreciated but not required.
