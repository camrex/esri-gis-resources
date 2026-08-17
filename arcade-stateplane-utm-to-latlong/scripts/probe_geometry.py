"""Which point does a non-point feature report, and what does Arcade allow?

Two findings live here. Arcade's X and Y exist only on Point, so reading them directly
fails on polygons -- in Calculate Field AND at rule-creation time, with the unhelpful
message "Field not found". Centroid() works on every geometry type and is identical on
points.

Centroid() is also the TRUE centroid, not a guaranteed-inside label point, so for a
concave or donut polygon it can fall outside the polygon. arcpy's .centroid silently
substitutes the label point in that case, which makes a naive comparison of the two
look like a huge error when it is nothing of the sort.
"""
import os
import re
# Requires ArcGIS Pro's Python -- arcpy cannot be pip-installed.
import arcpy  # pyright: ignore[reportMissingImports]
arcpy.env.overwriteOutput = True
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "_scratch")
GDB = os.path.join(WS, "geom.gdb")
os.makedirs(WS, exist_ok=True)
if arcpy.Exists(GDB):
    arcpy.management.Delete(GDB)
arcpy.management.CreateFileGDB(WS, "geom.gdb")
sr = arcpy.SpatialReference(6455)

def make(name, shape):
    fc = os.path.join(GDB, name)
    arcpy.management.CreateFeatureclass(GDB, name, shape, spatial_reference=sr)
    arcpy.management.AddField(fc, "V", "DOUBLE")
    arcpy.management.AddGlobalIDs(fc)
    return fc

ring = arcpy.Array([arcpy.Point(700000, 300000), arcpy.Point(800000, 300000),
                    arcpy.Point(800000, 400000), arcpy.Point(700000, 400000)])
GEOMS = {
    "POINT":      arcpy.PointGeometry(arcpy.Point(764723.8484, 302547.2518), sr),
    "POLYLINE":   arcpy.Polyline(ring, sr),
    "POLYGON":    arcpy.Polygon(ring, sr),
    "MULTIPOINT": arcpy.Multipoint(ring, sr),
}
EXPRS = {
    "gm.X (as shipped)":        'var gm=Geometry($feature); return gm.X;',
    "Centroid(gm).X":           'var gm=Geometry($feature); return Centroid(gm).X;',
    "TypeOf(gm)":               'var gm=Geometry($feature); return TypeOf(gm);',
}
print("%-11s %-22s %-9s %s" % ("shape", "expression", "status", "value / error"))
for shape, geom in GEOMS.items():
    fc = make("g_" + shape, shape)
    with arcpy.da.InsertCursor(fc, ["SHAPE@"]) as ic:
        ic.insertRow([geom])
    for label, expr in EXPRS.items():
        fld, e2 = ("V", expr)
        if label == "TypeOf(gm)":
            continue
        # (a) CalculateField
        try:
            arcpy.management.CalculateField(fc, "V", e2, "ARCADE")
            v = next(iter(arcpy.da.SearchCursor(fc, ["V"])))[0]
            calc = "OK %r" % v
        except Exception as ex:
            calc = "FAIL %s" % re.sub(r"\s+", " ", str(ex))[:70]
        # (b) attribute rule creation
        try:
            arcpy.management.AddAttributeRule(
                in_table=fc, name="r_" + label.split("(")[0].strip().replace(".", "_").replace(" ", "_"),
                type="CALCULATION", script_expression=e2, field="V",
                triggering_events="INSERT;UPDATE", error_number=9001,
                error_message="x", exclude_from_client_evaluation="INCLUDE")
            rule = "OK"
        except Exception as ex:
            m = re.search(r"Arcade error: ([^,]+), Script line: (\d+)", str(ex))
            rule = "FAIL " + (m.group(1) if m else re.sub(r"\s+", " ", str(ex))[:50])
        print("%-11s %-22s CalcField=%-28s Rule=%s" % (shape, label, calc, rule))
    print()
