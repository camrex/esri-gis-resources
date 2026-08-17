"""How calculation attribute rules actually behave, measured rather than assumed.

Five things that are easy to get wrong and that the documentation does not make
obvious. Everything runs in a throwaway file geodatabase.

    python probe_attribute_rules.py
"""
import json
import os
import re

# Requires ArcGIS Pro's Python -- arcpy cannot be pip-installed.
import arcpy  # pyright: ignore[reportMissingImports]

arcpy.env.overwriteOutput = True
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "_scratch")
GDB = os.path.join(WS, "rules_probe.gdb")
BUILD = os.path.join(HERE, "..", "builds", "arcade_latlong_condensed.txt")

os.makedirs(WS, exist_ok=True)
if arcpy.Exists(GDB):
    arcpy.management.Delete(GDB)
arcpy.management.CreateFileGDB(WS, "rules_probe.gdb")

SR = arcpy.SpatialReference(6348)                       # NAD83(2011) UTM 19N
RING = arcpy.Array([arcpy.Point(400000, 4880000), arcpy.Point(400500, 4880000),
                    arcpy.Point(400500, 4880500), arcpy.Point(400000, 4880500)])
RULE = re.sub(r'var\s+MD\s*=\s*"[A-Z]+"\s*;', 'var MD="RULE";',
              open(BUILD, encoding="utf-8").read(), count=1)


def make(name, editor_tracking=False):
    fc = os.path.join(GDB, name)
    arcpy.management.CreateFeatureclass(GDB, name, "POLYGON", spatial_reference=SR)
    for f in ("LAT_CALCULATED", "LON_CALCULATED"):
        arcpy.management.AddField(fc, f, "DOUBLE")
    arcpy.management.AddField(fc, "NOTE", "TEXT", field_length=40)
    arcpy.management.AddGlobalIDs(fc)
    if editor_tracking:
        for nm, tp in (("created_user", "TEXT"), ("created_date", "DATE"),
                       ("last_edited_user", "TEXT"), ("last_edited_date", "DATE")):
            arcpy.management.AddField(fc, nm, tp)
        arcpy.management.EnableEditorTracking(fc, "created_user", "created_date",
                                              "last_edited_user", "last_edited_date")
    return fc


def add_rule(fc, **over):
    kw = dict(in_table=fc, name="calc", type="CALCULATION", script_expression=RULE,
              triggering_events="INSERT;UPDATE", error_number=9001, error_message="x",
              exclude_from_client_evaluation="INCLUDE", batch="NOT_BATCH")
    kw.update(over)
    arcpy.management.AddAttributeRule(**kw)


def insert(fc, dx=0.0):
    ed = arcpy.da.Editor(GDB)
    ed.startEditing(False, False)
    ed.startOperation()
    parts = arcpy.Array([arcpy.Point(p.X + dx, p.Y + dx) for p in RING])
    with arcpy.da.InsertCursor(fc, ["SHAPE@"]) as ic:
        ic.insertRow([arcpy.Polygon(parts, SR)])
    ed.stopOperation()
    ed.stopEditing(True)


def edit_attribute(fc):
    ed = arcpy.da.Editor(GDB)
    ed.startEditing(False, False)
    ed.startOperation()
    with arcpy.da.UpdateCursor(fc, ["NOTE"]) as uc:
        for _ in uc:
            uc.updateRow(["touched"])
            break
    ed.stopOperation()
    ed.stopEditing(True)


def edit_geometry(fc, dx=250.0):
    ed = arcpy.da.Editor(GDB)
    ed.startEditing(False, False)
    ed.startOperation()
    with arcpy.da.UpdateCursor(fc, ["SHAPE@"]) as uc:
        for (g,) in uc:
            parts = arcpy.Array()
            for part in g:
                parts.add(arcpy.Array([arcpy.Point(p.X + dx, p.Y + dx) for p in part if p]))
            uc.updateRow([arcpy.Polygon(parts, SR)])
            break
    ed.stopOperation()
    ed.stopEditing(True)


def first(fc):
    return next(iter(arcpy.da.SearchCursor(fc, ["LAT_CALCULATED", "LON_CALCULATED"])))


print("1. A GlobalID field is required")
fc = os.path.join(GDB, "no_gid")
arcpy.management.CreateFeatureclass(GDB, "no_gid", "POLYGON", spatial_reference=SR)
for f in ("LAT_CALCULATED", "LON_CALCULATED"):
    arcpy.management.AddField(fc, f, "DOUBLE")
try:
    add_rule(fc)
    print("   rule added without a GlobalID -- unexpected")
except Exception as e:
    print("   %s" % re.sub(r"\s+", " ", str(e)).strip()[:80])

def trigger_case(name, shape_only):
    """Seed a feature BEFORE the rule exists, so its fields start NULL.

    Recalculating unchanged geometry produces identical values, so comparing values
    before and after cannot tell whether the rule fired. Starting from NULL can.
    """
    fc = make(name)
    insert(fc)                                     # no rule yet -> fields are NULL
    kw = {"triggering_fields": arcpy.Describe(fc).shapeFieldName} if shape_only else {}
    add_rule(fc, **kw)
    print("   before any edit   -> %s" % ("NULL" if first(fc)[0] is None else "populated"))
    edit_attribute(fc)
    fired_on_attr = first(fc)[0] is not None
    print("   attribute-only    -> %s" % ("RECALCULATED" if fired_on_attr else "no recalc"))
    edit_geometry(fc)
    fired_on_geom = first(fc)[0] is not None
    print("   geometry edit     -> %s" % ("recalculated" if fired_on_geom else "NO RECALC"))
    insert(fc, dx=1000.0)                          # a brand-new feature
    newest = [r for r in arcpy.da.SearchCursor(fc, ["LAT_CALCULATED"])][-1]
    print("   new insert        -> %s" % ("populated" if newest[0] is not None else "NULL"))
    return fc


print("\n2. Without triggering fields, ANY attribute edit recalculates")
trigger_case("any_edit", shape_only=False)

print("\n3. triggering_fields = the shape field limits it to geometry edits")
fc = trigger_case("shape_only", shape_only=True)
print("   exported as       -> TRIGGERINGFIELDS %s"
      % json.dumps(getattr(arcpy.Describe(fc).attributeRules[0], "triggeringFields", None)))

# The list is explicit, so it does not have to be the shape field. Naming an ordinary
# attribute turns that attribute into a deliberate recalculation handle: touch it and
# the rule runs, without going anywhere near the geometry. Geometry first here, because
# once the values are populated a later edit cannot be told apart from an earlier one.
print("\n4. triggering_fields = an ordinary attribute is a recalculation handle")
fc = make("attr_trigger")
insert(fc)                                         # no rule yet -> fields are NULL
add_rule(fc, triggering_fields="NOTE")
print("   before any edit   -> %s" % ("NULL" if first(fc)[0] is None else "populated"))
edit_geometry(fc)
print("   geometry edit     -> %s"
      % ("recalculated" if first(fc)[0] is not None else "no recalc (not a trigger)"))
edit_attribute(fc)                                 # touches NOTE, the triggering field
print("   edit of NOTE      -> %s"
      % ("RECALCULATED" if first(fc)[0] is not None else "no recalc"))
print("   exported as       -> TRIGGERINGFIELDS %s"
      % json.dumps(getattr(arcpy.Describe(fc).attributeRules[0], "triggeringFields", None)))
print("   => null the two fields, make a spare attribute the trigger, edit it, and the")
print("      rule refills them -- a way to re-run over chosen rows without touching shape")

print("\n5. A batch rule can backfill, but cannot also maintain")
fc = make("batch", editor_tracking=True)
insert(fc)                                    # exists before any rule
try:
    add_rule(fc, batch="BATCH")
    print("   batch rule WITH triggering events: accepted -- unexpected")
except Exception as e:
    print("   with triggering events -> %s" % re.sub(r"\s+", " ", str(e)).strip()[:72])
add_rule(fc, batch="BATCH", triggering_events="")
print("   without triggering events -> accepted, triggers=%s"
      % arcpy.Describe(fc).attributeRules[0].triggeringEvents)
print("   rows populated on add    -> %d"
      % sum(1 for r in arcpy.da.SearchCursor(fc, ["LAT_CALCULATED"]) if r[0] is not None))
arcpy.management.EvaluateRules(GDB, "CALCULATION_RULES")
print("   rows populated after Evaluate Rules -> %d"
      % sum(1 for r in arcpy.da.SearchCursor(fc, ["LAT_CALCULATED"]) if r[0] is not None))

print("\n   (a batch rule additionally requires editor tracking -- ERROR 003324 without it)")
print("\nSo: an immediate rule maintains but never backfills; a batch rule backfills but")
print("never maintains. Seed existing rows once with Calculate Field, then keep the")
print("immediate rule for maintenance.")
