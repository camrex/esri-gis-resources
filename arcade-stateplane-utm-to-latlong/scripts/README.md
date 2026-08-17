# Scripts

Everything used to build and verify the expressions. Nothing here is needed to *use* a
build — the files in [`../builds`](../builds) are self-contained — but all of it is
here so the numbers in [VALIDATION.md](../VALIDATION.md) can be reproduced or
disagreed with.

## Requirements

**Most of these scripts require `arcpy`, which means running them with ArcGIS Pro's
Python.** `arcpy` ships with ArcGIS Pro and cannot be installed with `pip`, so an ordinary
virtual environment will not do — use Pro's interpreter, typically
`C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`, or a cloned Pro
environment. The **Needs** column in each table below says which scripts those are.

Beyond `arcpy`, **Node.js 18+**: `harness.js` and `compare_builds.js` are Node programs,
and `validate.py` and `check_zone_edges.py` shell out to `harness.js`.

Four of them need no ArcGIS at all: `lint.py` is pure Python, `template_documented.py` and
`template_condensed.py` are template modules holding Arcade source and nothing else, and
`rule_from_csv.py` writes its CSV without ArcGIS and imports `arcpy` only if you pass
`--apply-to`.

Both templates are the same program in two styles, and a change to the maths belongs in
both — `build_expression.py` asserts that every `@@PLACEHOLDER@@` was substituted, so a
template that drifts out of step fails the build rather than shipping.

Every `arcpy` import carries a `# pyright: ignore[reportMissingImports]`, because an editor
resolving against anything other than Pro's Python cannot see a module that only exists
inside ArcGIS Pro. The comment is a note about where the dependency comes from, not a
suppressed mistake.

Run them from this directory.

## Building

| Script | Needs | What it does |
| --- | --- | --- |
| `build_expression.py` | **arcpy** | Generate an expression for any set of EPSG codes, reading every parameter from `arcpy.SpatialReference` |
| `template_documented.py` | — | The documented Arcade template, filled in for `--style documented`. The one to read, and to edit first |
| `template_condensed.py` | — | The same program stripped of commentary, filled in for `--style condensed` |
| `codes.txt` | — | The validated code list behind the published builds |
| `us_codes.txt` | — | A worked example of trimming to a subset — measured, and not worth it |

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

| Script | Needs | What it checks |
| --- | --- | --- |
| `validate.py` | **arcpy** + Node | Every code in a build against `arcpy`, headless via Node. The bulk check. |
| `compare_calc_geometry.py` | **arcpy** | The build against ArcGIS Pro's own Calculate Geometry Attributes, and what asking it for WGS 84 costs |
| `lint.py` | — | Arcade-specific static analysis. **Run this after any edit.** |
| `run_in_arcade.py` | **arcpy** | The real ArcGIS Arcade engine, one scratch feature class per code |
| `probe_arcade.py` | **arcpy** | What the engine actually supports — run it when a function's behaviour is in doubt |
| `harness.js` | Node | Executes the Arcade text under Node with the built-ins mapped to JavaScript |
| `compare_builds.js` | Node | Two builds against each other in all four output modes, plus the edge cases |
| `check_zone_edges.py` | **arcpy** + Node | How error grows with distance from the central meridian |
| `probe_geometry.py` | **arcpy** | Geometry-type behaviour, and where a polygon centroid actually lands |
| `probe_datum.py` | **arcpy** | What ArcGIS does to NAD83 coordinates asked for as WGS 84 |
| `probe_attribute_rules.py` | **arcpy** | Triggering fields, insert behaviour, batch-rule constraints |
| `bench.py` | **arcpy** | What actually costs time per feature |

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

| Script | Needs | What it does |
| --- | --- | --- |
| `apply_rule.py` | **arcpy** | Add the expression to a feature class as an attribute rule, and verify it |
| `rule_from_csv.py` | **arcpy** only for `--apply-to` | Package it as an Export-Attribute-Rules CSV for `ImportAttributeRules` |

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
