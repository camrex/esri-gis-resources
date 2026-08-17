"""Apply the lat/long Arcade expression to a feature class as an attribute rule.

Default is PREFLIGHT: reports what would happen and changes nothing.

  python apply_rule.py --fc <path>                      # preflight only, no writes
  python apply_rule.py --fc <path> --sandbox            # copy to a scratch FGDB, then run
  python apply_rule.py --fc <path> --in-place --yes     # modify the FC itself (asks first)

Steps once running: add LAT/LON fields and GlobalIDs if missing, attach the calculation
rule, backfill the existing rows with Calculate Field, then verify a random sample
against arcpy's own projectAs and confirm the rule fires on a real edit.
"""
import argparse, math, os, random, re, sys, time
import arcpy

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCRIPT = os.path.normpath(
    os.path.join(HERE, "..", "builds", "arcade_latlong_condensed.txt"))

ap = argparse.ArgumentParser()
ap.add_argument("--fc", required=True, help="target feature class path")
ap.add_argument("--rule-disabled", action="store_true",
                help="install the rule but leave it disabled")
ap.add_argument("--shape-only", action="store_true", default=True,
                help="fire only when geometry changes (default)")
ap.add_argument("--any-edit", dest="shape_only", action="store_false",
                help="fire on every attribute edit too")
ap.add_argument("--script", default=DEFAULT_SCRIPT)
ap.add_argument("--lat-field", default="LAT_CALCULATED")
ap.add_argument("--lon-field", default="LON_CALCULATED")
ap.add_argument("--rule-name", default="calc_latlon")
ap.add_argument("--sandbox", action="store_true", help="copy to a scratch FGDB and work there")
ap.add_argument("--sandbox-dir", default=os.path.join(HERE, "_scratch"))
ap.add_argument("--in-place", action="store_true", help="modify the given FC itself")
ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
ap.add_argument("--sample", type=int, default=500, help="features to verify against arcpy")
ap.add_argument("--no-backfill", action="store_true")
a = ap.parse_args()

arcpy.env.overwriteOutput = True

# --------------------------------------------------------------- preflight --
if not arcpy.Exists(a.fc):
    sys.exit("feature class not found: %s" % a.fc)
d = arcpy.Describe(a.fc)
sr = d.spatialReference
n = int(arcpy.management.GetCount(a.fc)[0])
flds = {f.name.upper(): f for f in arcpy.ListFields(a.fc)}
has_gid = any(f.type == "GlobalID" for f in flds.values())
rules = [r.name for r in getattr(d, "attributeRules", [])]
ws = d.path
wsd = arcpy.Describe(ws)
is_egdb = getattr(wsd, "workspaceFactoryProgID", "").startswith("esriDataSourcesGDB.SdeWorkspaceFactory")

src = open(a.script, encoding="utf-8").read()
codes = set()
m = re.search(r"var RN=\[(.*?)\n\];", src, re.S)
if m:                                   # run-compressed build
    for w0, cnt, v0, dw, dv in re.findall(r"\[(-?\d+),(\d+),(\d+),(\d+),(-?\d+)\]", m.group(1)):
        for i in range(int(cnt)):
            codes.add(int(w0) + i * int(dw))
else:                                   # dictionary build
    codes = {int(x) for x in re.findall(r'"(\d+)":', re.search(r"var WK=\{(.*?)\n\};", src, re.S).group(1))}

print("=" * 72)
print("PREFLIGHT  %s" % a.fc)
print("=" * 72)
print("  workspace        : %s%s" % (ws, "   [ENTERPRISE GEODATABASE]" if is_egdb else ""))
print("  geometry         : %s" % d.shapeType)
print("  features         : %d" % n)
print("  spatial reference: %s  (WKID %s, %s)" % (sr.name, sr.factoryCode, sr.linearUnitName))
print("  supported by %s : %s"
      % (os.path.basename(a.script), "YES" if sr.factoryCode in codes else "*** NO ***"))
print("  GlobalID field   : %s" % ("present" if has_gid else "MISSING - required for attribute rules"))
print("  %-16s : %s" % (a.lat_field, "present" if a.lat_field.upper() in flds else "will be added (DOUBLE)"))
print("  %-16s : %s" % (a.lon_field, "present" if a.lon_field.upper() in flds else "will be added (DOUBLE)"))
print("  existing rules   : %s" % (", ".join(rules) if rules else "none"))
if d.shapeType != "Point":
    print("  NOTE: non-point geometry -> the rule reports the geometry centroid.")
for f in (a.lat_field, a.lon_field):
    ff = flds.get(f.upper())
    if ff is not None and ff.type not in ("Double",):
        print("  *** %s is %s, not Double: single precision caps accuracy near 0.2 m" % (f, ff.type))
if sr.factoryCode not in codes:
    sys.exit("\nSpatial reference WKID %s is not in this build. Stopping." % sr.factoryCode)
if is_egdb:
    print("\n  Reminder: this is an enterprise geodatabase. Adding GlobalIDs and an")
    print("  attribute rule are schema changes; do them on a copy unless you mean it.")

target = a.fc
if not (a.sandbox or a.in_place):
    print("\nPreflight only - nothing changed.")
    print("Re-run with --sandbox to test on a copy, or --in-place --yes to modify this FC.")
    sys.exit(0)

# ------------------------------------------------------------------ set up --
if a.sandbox:
    os.makedirs(a.sandbox_dir, exist_ok=True)
    gdb = os.path.join(a.sandbox_dir, "apply_rule_test.gdb")
    if arcpy.Exists(gdb):
        arcpy.management.Delete(gdb)
    arcpy.management.CreateFileGDB(a.sandbox_dir, "apply_rule_test.gdb")
    print("\ncopying %d features to %s ..." % (n, gdb))
    t = time.perf_counter()
    target = os.path.join(gdb, "parcels")
    arcpy.management.CopyFeatures(a.fc, target)
    print("  copied in %.1fs" % (time.perf_counter() - t))
else:
    if not a.yes:
        sys.exit("Refusing to modify %s without --yes." % a.fc)
    print("\n*** MODIFYING THE SOURCE FEATURE CLASS ***")

d = arcpy.Describe(target)
flds = {f.name.upper(): f for f in arcpy.ListFields(target)}
for f in (a.lat_field, a.lon_field):
    if f.upper() not in flds:
        arcpy.management.AddField(target, f, "DOUBLE")
        print("  added field %s (DOUBLE)" % f)
if not any(f.type == "GlobalID" for f in arcpy.ListFields(target)):
    print("  adding GlobalIDs ...")
    arcpy.management.AddGlobalIDs(target)

def with_mode(mode):
    s, k = re.subn(r'var\s+(MD|OUT_MODE)\s*=\s*"[A-Z]+"\s*;',
                   lambda mm: 'var %s="%s";' % (mm.group(1), mode), src)
    assert k == 1
    s, k = re.subn(r'var\s+(LF|LAT_FIELD)\s*=\s*"[^"]*"\s*;',
                   lambda mm: 'var %s="%s";' % (mm.group(1), a.lat_field), s)
    s, k2 = re.subn(r'var\s+(NF|LON_FIELD)\s*=\s*"[^"]*"\s*;',
                    lambda mm: 'var %s="%s";' % (mm.group(1), a.lon_field), s)
    assert k == 1 and k2 == 1
    return s

existing = [r.name for r in arcpy.Describe(target).attributeRules]
if a.rule_name in existing:
    arcpy.management.DeleteAttributeRule(target, a.rule_name, "CALCULATION")
    print("  replaced existing rule %s" % a.rule_name)
print("  adding attribute rule %s ..." % a.rule_name)
kw = dict(in_table=target, name=a.rule_name, type="CALCULATION",
          script_expression=with_mode("RULE"),
          is_editable="EDITABLE", triggering_events="INSERT;UPDATE",
          error_number=9001, error_message="lat/long calculation failed",
          exclude_from_client_evaluation="INCLUDE", batch="NOT_BATCH")
if a.shape_only:
    # Without this the rule recalculates on EVERY attribute edit. Naming the shape
    # field limits it to geometry changes; inserts still fire.
    kw["triggering_fields"] = arcpy.Describe(target).shapeFieldName
arcpy.management.AddAttributeRule(**kw)
print("  rule accepted by the Arcade attribute-rule profile"
      + (" (geometry edits only)" if a.shape_only else ""))
if a.rule_disabled:
    arcpy.management.DisableAttributeRules(target, a.rule_name, "CALCULATION")
    print("  rule left DISABLED")

# --------------------------------------------------------------- backfill ---
# An immediate calculation rule fires only on edits, so rows that already exist are
# never touched by it. A batch rule can backfill via Evaluate Rules, but a batch rule
# accepts no triggering events and needs editor tracking, so it cannot also maintain.
# One Calculate Field pass is the simpler way to seed existing data.
if not a.no_backfill and not a.rule_disabled:
    for fld, mode in ((a.lat_field, "LAT"), (a.lon_field, "LON")):
        t = time.perf_counter()
        arcpy.management.CalculateField(target, fld, with_mode(mode), "ARCADE")
        el = time.perf_counter() - t
        print("  backfilled %-16s %7.1fs  (%.0f us/feature)" % (fld, el, el / max(n, 1) * 1e6))

# --------------------------------------------------------------- verify -----
sr = arcpy.Describe(target).spatialReference
gcs = sr.GCS
f = gcs.flattening
e2 = 2 * f - f * f
A = 6378137.0
def dist_mm(la1, lo1, la2, lo2):
    ph = math.radians(la1); s = math.sin(ph); w = 1 - e2 * s * s
    M = A * (1 - e2) / w ** 1.5; N = A / math.sqrt(w)
    dl = lo2 - lo1
    if dl > 180: dl -= 360
    if dl < -180: dl += 360
    return math.hypot(math.radians(dl) * N * math.cos(ph), math.radians(la2 - la1) * M) * 1000.0

oids = [r[0] for r in arcpy.da.SearchCursor(target, ["OID@"])]
random.seed(11)
pick = set(random.sample(oids, min(a.sample, len(oids))))
worst, nulls, checked, worst_oid = 0.0, 0, 0, None
oid_fld = arcpy.Describe(target).OIDFieldName
with arcpy.da.SearchCursor(target, ["OID@", "SHAPE@", a.lat_field, a.lon_field]) as sc:
    for oid, geom, la, lo in sc:
        if oid not in pick: continue
        if la is None or lo is None:
            nulls += 1; continue
        if geom is None: continue
        c = geom.centroid
        g = arcpy.PointGeometry(arcpy.Point(c.X, c.Y), sr).projectAs(gcs).getPart(0)
        dd = dist_mm(g.Y, g.X, la, lo)
        checked += 1
        if dd > worst: worst, worst_oid = dd, oid

print("\nverification against arcpy projectAs, %d sampled features:" % len(pick))
print("  checked %d, null lat/long %d, worst error %.4f mm (OID %s)" % (checked, nulls, worst, worst_oid))
tot_null = sum(1 for r in arcpy.da.SearchCursor(target, [a.lat_field]) if r[0] is None)
print("  rows still null across the whole FC: %d of %d" % (tot_null, n))

# ------------------------------------------------- does the rule fire? ------
print("\nedit test: nudging one feature to confirm the rule recalculates")
test_oid = sorted(pick)[0]
gdbws = arcpy.Describe(target).path
where = "%s = %d" % (oid_fld, test_oid)
original = None
with arcpy.da.SearchCursor(target, ["SHAPE@", a.lat_field, a.lon_field], where) as sc:
    g0, la0, lo0 = next(iter(sc))
    original, before = g0, (la0, lo0)

def shift(geom, dx):
    """Move a geometry by dx on both axes, whatever its type."""
    if geom.type == "point":
        p = geom.getPart(0)
        return arcpy.PointGeometry(arcpy.Point(p.X + dx, p.Y + dx), sr)
    if geom.type == "multipoint":
        moved = [arcpy.Point(geom.getPart(i).X + dx, geom.getPart(i).Y + dx)
                 for i in range(geom.pointCount)]
        return arcpy.Multipoint(arcpy.Array(moved), sr)
    parts = arcpy.Array()
    for part in geom:
        parts.add(arcpy.Array([arcpy.Point(p.X + dx, p.Y + dx) for p in part if p]))
    return arcpy.Polygon(parts, sr) if geom.type == "polygon" else arcpy.Polyline(parts, sr)

ed = arcpy.da.Editor(gdbws)
ed.startEditing(False, False); ed.startOperation()
with arcpy.da.UpdateCursor(target, ["SHAPE@"], where) as uc:
    for row in uc:
        uc.updateRow([shift(original, 30.0)]); break
ed.stopOperation(); ed.stopEditing(True)
with arcpy.da.SearchCursor(target, [a.lat_field, a.lon_field], where) as sc:
    after = next(iter(sc))

# put the geometry back; the rule recalculates the original values with it
ed.startEditing(False, False); ed.startOperation()
with arcpy.da.UpdateCursor(target, ["SHAPE@"], where) as uc:
    for row in uc:
        uc.updateRow([original]); break
ed.stopOperation(); ed.stopEditing(True)
with arcpy.da.SearchCursor(target, [a.lat_field, a.lon_field], where) as sc:
    restored = next(iter(sc))

print("  OID %d before move : %s" % (test_oid, before))
print("  after +30 m shift  : %s" % (after,))
print("  after restore      : %s" % (restored,))
print("  rule fired on UPDATE : %s" % ("YES" if after != before else "NO - check triggers"))
print("  geometry restored    : %s" % ("YES" if restored == before else "CHECK - values differ"))
print("\ntarget: %s" % target)
