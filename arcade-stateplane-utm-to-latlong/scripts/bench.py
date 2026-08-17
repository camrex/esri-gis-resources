"""What actually costs time in an Arcade expression?

Times Calculate Field and attribute-rule inserts in the real engine. The finding worth
knowing: Arcade rebuilds the literal data tables on EVERY feature, so lookup-table
entry count drives run time and file size does not. Comments are free.

    python bench.py                       # the shipped builds
    python bench.py a.txt b.txt ...       # any builds
"""
import os, random, re, sys, time
import arcpy
arcpy.env.overwriteOutput = True
HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "_scratch"); GDB = os.path.join(WS, "bench.gdb")
os.makedirs(WS, exist_ok=True)
if arcpy.Exists(GDB): arcpy.management.Delete(GDB)
arcpy.management.CreateFileGDB(WS, "bench.gdb")
sr = arcpy.SpatialReference(6455)

N = 8000
random.seed(3)
pts = [(700000 + random.random() * 200000, 200000 + random.random() * 300000) for _ in range(N)]
fc = os.path.join(GDB, "bench")
arcpy.management.CreateFeatureclass(GDB, "bench", "POINT", spatial_reference=sr)
arcpy.management.AddField(fc, "LAT_CALCULATED", "DOUBLE")
arcpy.management.AddField(fc, "LON_CALCULATED", "DOUBLE")
with arcpy.da.InsertCursor(fc, ["SHAPE@XY"]) as ic:
    for p in pts: ic.insertRow([p])

BUILDS = ([(os.path.basename(p), p) for p in sys.argv[1:]] or
          [("condensed", os.path.join(HERE, "..", "builds", "arcade_latlong_condensed.txt")),
           ("documented", os.path.join(HERE, "..", "builds", "arcade_latlong_documented.txt"))])
def mode(path, m):
    s = open(path, encoding="utf-8").read()
    out, n = re.subn(r'var\s+MD\s*=\s*"[A-Z]+"\s*;', 'var MD="%s";' % m, s)
    assert n == 1
    return out

print("Calculate Field over %d features, Illinois East ftUS\n" % N)
print("%-24s %10s %10s %14s" % ("build", "run 1", "run 2", "per feature"))
for label, path in BUILDS:
    expr = mode(path, "LAT")
    ts = []
    for _ in range(2):
        t = time.perf_counter()
        arcpy.management.CalculateField(fc, "LAT_CALCULATED", expr, "ARCADE")
        ts.append(time.perf_counter() - t)
    print("%-24s %9.2fs %9.2fs %11.1f us" % (label, ts[0], ts[1], min(ts) / N * 1e6))

print("\nAttribute-rule inserts, 1500 features")
print("%-24s %10s %14s" % ("build", "elapsed", "per feature"))
for label, path in BUILDS:
    name = "r" + re.sub(r"\W", "", label)[:12]
    rfc = os.path.join(GDB, name)
    arcpy.management.CreateFeatureclass(GDB, name, "POINT", spatial_reference=sr)
    arcpy.management.AddField(rfc, "LAT_CALCULATED", "DOUBLE")
    arcpy.management.AddField(rfc, "LON_CALCULATED", "DOUBLE")
    arcpy.management.AddGlobalIDs(rfc)
    arcpy.management.AddAttributeRule(
        in_table=rfc, name="calc", type="CALCULATION", script_expression=mode(path, "RULE"),
        triggering_events="INSERT;UPDATE", error_number=9001, error_message="x",
        exclude_from_client_evaluation="INCLUDE")
    ed = arcpy.da.Editor(GDB)
    ed.startEditing(False, False); ed.startOperation()
    t = time.perf_counter()
    with arcpy.da.InsertCursor(rfc, ["SHAPE@XY"]) as ic:
        for p in pts[:1500]: ic.insertRow([p])
    el = time.perf_counter() - t
    ed.stopOperation(); ed.stopEditing(True)
    got = sum(1 for r in arcpy.da.SearchCursor(rfc, ["LAT_CALCULATED"]) if r[0] is not None)
    print("%-24s %9.2fs %11.1f us   (%d/1500 populated)" % (label, el, el / 1500 * 1e6, got))
