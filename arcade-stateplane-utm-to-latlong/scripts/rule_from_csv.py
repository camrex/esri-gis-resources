"""Package the expression as an Export-Attribute-Rules CSV, for ImportAttributeRules.

This is how ArcGIS Pro itself moves attribute rules between datasets, so a CSV is the
portable unit: it carries the expression, the target field names, the triggering
fields and the enabled state together, and it can be committed, reviewed and applied
to many feature classes without anyone pasting a 20 KB expression into a dialog.

    python rule_from_csv.py --out calc_latlong.csv --lat-field lat --lon-field long
    python rule_from_csv.py --out calc_latlong.csv --apply-to path/to/fc.gdb/parcels

Defaults reflect what testing showed you almost always want:
  * triggering fields = the shape field, so attribute-only edits do not recalculate
  * ISENABLED = False, so the rule lands inert and someone turns it on deliberately

Note that an immediate calculation rule never touches rows that already exist. Seed
those once with Calculate Field (see apply_rule.py --no-backfill / the default).
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUILD = os.path.join(HERE, "..", "builds", "arcade_latlong_condensed.txt")

COLUMNS = ["NAME", "DESCRIPTION", "TYPE", "SUBTYPE", "FIELD", "ISEDITABLE",
           "TRIGGERINSERT", "TRIGGERDELETE", "TRIGGERUPDATE", "SCRIPTEXPRESSION",
           "ERRORNUMBER", "ERRORMESSAGE", "EXCLUDECLIENTEVALUATION", "ISENABLED",
           "BATCH", "SEVERITY", "TAGS", "CATEGORY", "CHECKPARAMETERS",
           "TRIGGERINGFIELDS", "SUBTYPES"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", default=DEFAULT_BUILD)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="calc_latlong")
    ap.add_argument("--lat-field", default="LAT_CALCULATED")
    ap.add_argument("--lon-field", default="LON_CALCULATED")
    ap.add_argument("--shape-field", default="shape",
                    help="triggering field; empty string to fire on every edit")
    ap.add_argument("--enabled", action="store_true", help="load enabled (default: disabled)")
    ap.add_argument("--error-number", type=int, default=9001)
    ap.add_argument("--apply-to", default=None, help="feature class to import into (needs arcpy)")
    a = ap.parse_args(argv)

    text = open(a.build, encoding="utf-8").read()
    expr, n = re.subn(r'var\s+MD\s*=\s*"[A-Z]+"\s*;', 'var MD="RULE";', text)
    if n != 1:
        sys.exit("expected exactly one output-mode line, found %d" % n)
    expr, n_lat = re.subn(r'var\s+LF\s*=\s*"[^"]*"\s*;', 'var LF="%s";' % a.lat_field, expr)
    expr, n_lon = re.subn(r'var\s+NF\s*=\s*"[^"]*"\s*;', 'var NF="%s";' % a.lon_field, expr)
    if not (n_lat == 1 and n_lon == 1):
        sys.exit("could not set the field names in this build")

    row = {c: "" for c in COLUMNS}
    row.update(
        NAME=a.name, TYPE="CALCULATION",
        DESCRIPTION="Latitude and longitude of the feature centroid, inverted from the "
                    "stored projected coordinates.",
        ISEDITABLE="True", TRIGGERINSERT="True", TRIGGERDELETE="False", TRIGGERUPDATE="True",
        SCRIPTEXPRESSION=expr,
        ERRORNUMBER=str(a.error_number),
        ERRORMESSAGE="lat/long calculation failed",
        EXCLUDECLIENTEVALUATION="False",
        ISENABLED="True" if a.enabled else "False",
        BATCH="False",
        CHECKPARAMETERS='{"type":"PropertySet","propertySetItems":[]}',
        TRIGGERINGFIELDS=json.dumps([a.shape_field]) if a.shape_field else "",
        SUBTYPES="[]")

    with open(a.out, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerow(row)
    print("%s: %s -> %s / %s, %s, triggers on %s"
          % (os.path.basename(a.out), a.name, a.lat_field, a.lon_field,
             "ENABLED" if a.enabled else "disabled",
             a.shape_field or "any edit"))

    if a.apply_to:
        import arcpy
        arcpy.management.ImportAttributeRules(a.apply_to, a.out)
        for r in arcpy.Describe(a.apply_to).attributeRules:
            print("   applied: %s enabled=%s triggeringFields=%s"
                  % (r.name, r.isEnabled, getattr(r, "triggeringFields", None)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
