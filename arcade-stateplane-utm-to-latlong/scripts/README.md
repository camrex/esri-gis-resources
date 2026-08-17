# Scripts

Everything used to build and verify the expressions. Nothing here is needed to *use* a
build — the files in [`../builds`](../builds) are self-contained — but all of it is
here so the numbers in [VALIDATION.md](../VALIDATION.md) can be reproduced or
disagreed with.

**Requirements:** ArcGIS Pro's Python (for `arcpy`) and Node.js 18+ (for the harness).
Run them from this directory.

## Building

| Script | What it does |
|---|---|
| `build_expression.py` | Generate an expression for any set of EPSG codes, reading every parameter from `arcpy.SpatialReference` |
| `template_documented.py` | The documented Arcade template `build_expression.py` fills in |
| `codes.txt` | The validated code list behind the published builds |
| `us_codes.txt` | A worked example of trimming to a subset — measured, and not worth it |

```powershell
# --label only sets the header comment, but it is what makes these two commands
# reproduce the published files byte for byte
python build_expression.py --style documented --label "US State Plane + UTM worldwide" --out ../builds/arcade_latlong_documented.txt
python build_expression.py --style condensed  --label "US State Plane + UTM worldwide" --out ../builds/arcade_latlong_condensed.txt

python build_expression.py --codes 25832,25833 --out etrs89_utm.txt
python build_expression.py --codes @my_codes.txt --lat-field lat --lon-field long --out mine.txt
```

The published builds are pinned to an explicit code list rather than discovered at run
time. Auto-discovery is a trap here: filtering "UTM zones 1–24" by zone number quietly
matches those zones on every datum on Earth, so a "US" build ends up carrying SIRGAS and
Tokyo Datum.

## Verifying

| Script | What it checks |
|---|---|
| `validate.py` | Every code in a build against `arcpy`, headless via Node. The bulk check. |
| `compare_calc_geometry.py` | The build against ArcGIS Pro's own Calculate Geometry Attributes, and what asking it for WGS 84 costs |
| `lint.py` | Arcade-specific static analysis. **Run this after any edit.** |
| `run_in_arcade.py` | The real ArcGIS Arcade engine, one scratch feature class per code |
| `probe_arcade.py` | What the engine actually supports — run it when a function's behaviour is in doubt |
| `harness.js` | Executes the Arcade text under Node with the built-ins mapped to JavaScript |
| `compare_builds.js` | Two builds against each other in all four output modes, plus the edge cases |
| `check_zone_edges.py` | How error grows with distance from the central meridian |
| `probe_geometry.py` | Geometry-type behaviour, and where a polygon centroid actually lands |
| `probe_datum.py` | What ArcGIS does to NAD83 coordinates asked for as WGS 84 |
| `probe_attribute_rules.py` | Triggering fields, insert behaviour, batch-rule constraints |
| `bench.py` | What actually costs time per feature |

```powershell
python compare_calc_geometry.py                                      # vs Pro's own tool
python compare_calc_geometry.py --wkid 32139 --n 500

python validate.py ../builds/arcade_latlong_condensed.txt            # ~1 minute
python lint.py ../builds/arcade_latlong_condensed.txt
python run_in_arcade.py ../builds/arcade_latlong_condensed.txt --codes 6455,26915,32616
python run_in_arcade.py ../builds/arcade_latlong_condensed.txt       # ~20 minutes, all codes

node compare_builds.js            # condensed vs documented; reuses the points validate.py leaves behind
node compare_builds.js --points other_points.json     # or bring your own
python check_zone_edges.py
python probe_geometry.py
python probe_datum.py
python probe_attribute_rules.py
python bench.py
```

Each of those backs a specific claim in [VALIDATION.md](../VALIDATION.md). The
investigation scripts that found the original defects are deliberately *not* here: they
only run against the superseded source files, and `build_expression.py` replaces what
they were for.

`validate.py` is fast and covers everything, but it is a JavaScript proxy: it cannot
see that **Arcade identifiers are case-insensitive**, so `U` and `u` are one variable.
That is what `lint.py` is for, and it is not hypothetical — it caught a real bug in the
Hotine routine here that the harness passed cleanly.

## Applying

| Script | What it does |
|---|---|
| `apply_rule.py` | Add the expression to a feature class as an attribute rule, and verify it |
| `rule_from_csv.py` | Package it as an Export-Attribute-Rules CSV for `ImportAttributeRules` |

```powershell
python apply_rule.py --fc path/to.gdb/parcels                       # preflight, changes nothing
python apply_rule.py --fc path/to.gdb/parcels --sandbox             # work on a copy
python apply_rule.py --fc path/to.gdb/parcels --in-place --yes --rule-disabled

python rule_from_csv.py --out calc_latlong.csv --lat-field lat --lon-field long
python rule_from_csv.py --out calc_latlong.csv --apply-to path/to.gdb/parcels
```

`apply_rule.py` defaults to a preflight that reports what it would do and writes
nothing. A CSV is the better unit for deploying to many feature classes: it carries the
expression, field names, triggering fields and enabled state together, and it is what
Pro itself uses to move rules between datasets.

### Three things attribute rules require

- A **GlobalID** field on the feature class, or creation fails with ERROR 002710.
- **Triggering fields are an explicit list.** Empty means every update fires the rule;
  naming the shape field limits it to geometry changes, which is usually what you want.
  Inserts fire either way. The list can name ordinary attributes instead — making one a
  trigger and then editing it is a clean way to force recalculation without touching
  geometry.
- A one-off **Calculate Field** pass to seed rows that already exist. An immediate rule
  only ever fires on edits. A batch rule *can* backfill through Evaluate Rules, but it
  accepts no triggering events (ERROR 002546) and needs editor tracking enabled
  (ERROR 003324), so it cannot also maintain — you need both, or one pass and one rule.
