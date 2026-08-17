"""Compare the Arcade expression with ArcGIS Pro's own Calculate Geometry Attributes.

This is the comparison most people actually care about: Calculate Geometry Attributes
is the familiar way to get lat/long onto a feature class, and the only reason it is not
the answer is that it is a geoprocessing tool -- it cannot run in a popup, a label, or
an attribute rule. So the question is whether the expression gives the same number.

It does, to the last digit Calculate Geometry reports. That tool writes 8 decimal
places of a degree; the expression writes 9. Rounded to the tool's own precision the
two agree, give or take one unit in that final digit.

    python compare_calc_geometry.py                     # scratch points in 6455
    python compare_calc_geometry.py --wkid 32139 --n 500
    python compare_calc_geometry.py --fc path/to.gdb/parcels

The second comparison is the one to pay attention to. Ask Calculate Geometry for WGS84
output instead of the source's own geographic system and it applies an explicit datum
transformation, moving the point by the better part of a metre -- three orders of
magnitude more than anything the projection maths does. That is a datum decision, not
an accuracy one, and it applies to the tool exactly as it applies to this expression.
"""
import argparse
import math
import os
import random
import re
import sys

# Requires ArcGIS Pro's Python -- arcpy cannot be pip-installed.
import arcpy  # pyright: ignore[reportMissingImports]

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUILD = os.path.normpath(
    os.path.join(HERE, "..", "builds", "arcade_latlong_condensed.txt"))


def ground_mm(lat, dlat, dlon, e2, axis):
    ph = math.radians(lat)
    s = math.sin(ph)
    w = 1 - e2 * s * s
    return math.hypot(math.radians(dlon) * (axis / math.sqrt(w)) * math.cos(ph),
                      math.radians(dlat) * (axis * (1 - e2) / w ** 1.5)) * 1000.0


def with_mode(text, mode):
    out, n = re.subn(r'var\s+MD\s*=\s*"[A-Z]+"\s*;', 'var MD="%s";' % mode, text)
    if n != 1:
        sys.exit("expected exactly one output-mode line, found %d" % n)
    return out


def scratch_points(workspace, wkid, n):
    """A field of random points inside the zone, in a throwaway file geodatabase."""
    os.makedirs(workspace, exist_ok=True)
    gdb = os.path.join(workspace, "calc_geom.gdb")
    if arcpy.Exists(gdb):
        arcpy.management.Delete(gdb)
    arcpy.management.CreateFileGDB(workspace, "calc_geom.gdb")
    sr = arcpy.SpatialReference(wkid)
    fc = os.path.join(gdb, "pts")
    arcpy.management.CreateFeatureclass(gdb, "pts", "POINT", spatial_reference=sr)

    # Work in geographic space so the points land inside the zone whatever it is, then
    # let arcpy project them in.
    gcs = sr.GCS
    lat0 = sr.latitudeOfOrigin or sr.standardParallel1 or 0.0
    cm = sr.centralMeridian
    random.seed(5)
    pts = [arcpy.Point(cm + (random.random() - 0.5) * 2.0, lat0 + 0.2 + random.random() * 2.0)
           for _ in range(n)]
    projected = arcpy.Multipoint(arcpy.Array(pts), gcs).projectAs(sr)
    with arcpy.da.InsertCursor(fc, ["SHAPE@XY"]) as ic:
        for i in range(projected.pointCount):
            p = projected.getPart(i)
            ic.insertRow([(p.X, p.Y)])
    return fc


def report(fc, arcade_fields, tool_fields, gcs, label):
    f = gcs.flattening
    e2 = 2 * f - f * f
    axis = gcs.semiMajorAxis or 6378137.0
    d, same, tot = [], 0, 0
    with arcpy.da.SearchCursor(fc, list(arcade_fields) + list(tool_fields)) as sc:
        for la, lo, tla, tlo in sc:
            if None in (la, lo, tla, tlo):
                continue
            tot += 1
            d.append(ground_mm(la, la - tla, lo - tlo, e2, axis))
            if round(la, 8) == round(tla, 8) and round(lo, 8) == round(tlo, 8):
                same += 1
    d.sort()
    n = len(d)
    print("\n  %s" % label)
    print("     median %.4f mm | p95 %.4f mm | worst %.4f mm"
          % (d[n // 2], d[int(0.95 * n)], d[-1]))
    print("     identical at Calculate Geometry's 8 decimals: %d of %d" % (same, tot))
    return d[-1]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", default=DEFAULT_BUILD)
    ap.add_argument("--fc", default=None, help="existing feature class; else scratch points")
    ap.add_argument("--wkid", type=int, default=6455, help="zone for the scratch points")
    ap.add_argument("--n", type=int, default=200, help="scratch point count")
    ap.add_argument("--workspace", default=os.path.join(HERE, "_scratch"))
    a = ap.parse_args(argv)

    arcpy.env.overwriteOutput = True
    fc = a.fc or scratch_points(a.workspace, a.wkid, a.n)
    sr = arcpy.Describe(fc).spatialReference
    gcs = sr.GCS
    print("comparing against Calculate Geometry Attributes")
    print("   feature class : %s" % fc)
    print("   stored in     : %s (WKID %s)" % (sr.name, sr.factoryCode))
    print("   its own GCS   : %s (WKID %s)" % (gcs.name, gcs.factoryCode))

    have = {fld.name.upper() for fld in arcpy.ListFields(fc)}
    for name in ("AR_LAT", "AR_LON", "CG_LAT", "CG_LON", "CG84_LAT", "CG84_LON"):
        if name not in have:
            arcpy.management.AddField(fc, name, "DOUBLE")

    text = open(a.build, encoding="utf-8").read()
    arcpy.management.CalculateField(fc, "AR_LAT", with_mode(text, "LAT"), "ARCADE")
    arcpy.management.CalculateField(fc, "AR_LON", with_mode(text, "LON"), "ARCADE")

    # Calculate Geometry into the source's OWN geographic system: no datum change,
    # the same thing an inverse projection does.
    arcpy.management.CalculateGeometryAttributes(
        fc, [["CG_LON", "POINT_X"], ["CG_LAT", "POINT_Y"]],
        coordinate_system=gcs, coordinate_format="DD")
    worst = report(fc, ("AR_LAT", "AR_LON"), ("CG_LAT", "CG_LON"), gcs,
                   "vs Calculate Geometry into the source's own GCS")

    # Calculate Geometry into WGS84: ArcGIS applies an explicit transformation.
    arcpy.management.CalculateGeometryAttributes(
        fc, [["CG84_LON", "POINT_X"], ["CG84_LAT", "POINT_Y"]],
        coordinate_system=arcpy.SpatialReference(4326), coordinate_format="DD")
    shifted = report(fc, ("AR_LAT", "AR_LON"), ("CG84_LAT", "CG84_LON"), gcs,
                     "vs Calculate Geometry asked for WGS 84")

    print("\n  The first is the like-for-like comparison, and the residual there is")
    print("  Calculate Geometry's own 8-decimal output, not either one's error.")
    print("  The second is %.0fx larger and is a datum decision, not an accuracy one:"
          % (shifted / max(worst, 1e-9)))
    print("  ArcGIS applied an explicit transformation on the way to WGS 84.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
