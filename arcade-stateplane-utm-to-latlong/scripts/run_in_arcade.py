"""Execute a build in the REAL ArcGIS Arcade engine, not a JavaScript proxy.

Creates one scratch feature class per EPSG code, runs Calculate Field with the build
as an Arcade expression, and compares what comes back with arcpy's own inverse of the
STORED coordinates -- so geodatabase coordinate quantisation is never mistaken for
script error.

    python run_in_arcade.py ../builds/arcade_latlong_condensed.txt --grid 3
    python run_in_arcade.py ../builds/arcade_latlong_condensed.txt --codes 6455,26915,32616

This is the check the Node harness cannot make: it exercises the real parser, the real
function list, and Arcade's case-insensitive identifiers. Expect roughly one second per
code, so the full 1,139-code list takes around twenty minutes.
"""
import argparse
import collections
import os
import re
import sys
import time

# Requires ArcGIS Pro's Python -- arcpy cannot be pip-installed.
import arcpy  # pyright: ignore[reportMissingImports]

from validate import codes_for, extent_for, ground_mm, linspace  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))


def with_mode(text, mode):
    out, n = re.subn(r'var\s+MD\s*=\s*"[A-Z]+"\s*;', 'var MD="%s";' % mode, text)
    if n != 1:
        sys.exit("expected exactly one output-mode line, found %d" % n)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("build")
    ap.add_argument("--grid", type=int, default=3)
    ap.add_argument("--codes", default=None, help="comma list, instead of the whole build")
    ap.add_argument("--workspace", default=os.path.join(HERE, "_scratch"))
    a = ap.parse_args(argv)

    arcpy.env.overwriteOutput = True
    text = open(a.build, encoding="utf-8").read()
    codes = ([int(c) for c in a.codes.split(",")] if a.codes else codes_for(a.build))

    os.makedirs(a.workspace, exist_ok=True)
    gdb = os.path.join(a.workspace, "arcade_check.gdb")
    if arcpy.Exists(gdb):
        arcpy.management.Delete(gdb)
    arcpy.management.CreateFileGDB(a.workspace, "arcade_check.gdb")

    print("running %s in the real Arcade engine: %d codes, %d x %d points each"
          % (os.path.basename(a.build), len(codes), a.grid, a.grid))
    errors, per_code = [], collections.defaultdict(float)
    started = time.time()
    for i, code in enumerate(codes):
        sr = arcpy.SpatialReference(code)
        gcs = sr.GCS
        lats, lons = extent_for(sr, a.grid)
        pts = [arcpy.Point(lo, la) for la in lats for lo in lons]
        projected = arcpy.Multipoint(arcpy.Array(pts), gcs).projectAs(sr)

        name = "z%d" % code
        fc = os.path.join(gdb, name)
        arcpy.management.CreateFeatureclass(gdb, name, "POINT", spatial_reference=sr)
        arcpy.management.AddField(fc, "LAT_A", "DOUBLE")
        arcpy.management.AddField(fc, "LON_A", "DOUBLE")
        with arcpy.da.InsertCursor(fc, ["SHAPE@XY"]) as ic:
            for j in range(projected.pointCount):
                p = projected.getPart(j)
                ic.insertRow([(p.X, p.Y)])
        arcpy.management.CalculateField(fc, "LAT_A", with_mode(text, "LAT"), "ARCADE")
        arcpy.management.CalculateField(fc, "LON_A", with_mode(text, "LON"), "ARCADE")

        f = gcs.flattening
        e2 = 2 * f - f * f
        axis = gcs.semiMajorAxis or 6378137.0
        with arcpy.da.SearchCursor(fc, ["SHAPE@XY", "LAT_A", "LON_A"]) as sc:
            for (x, y), la, lo in sc:
                truth = arcpy.PointGeometry(arcpy.Point(x, y), sr).projectAs(gcs).getPart(0)
                dlon = lo - truth.X
                if dlon > 180:
                    dlon -= 360
                if dlon < -180:
                    dlon += 360
                d = ground_mm(truth.Y, la - truth.Y, dlon, e2, axis)
                errors.append(d)
                per_code[code] = max(per_code[code], d)
        if i % 25 == 0:
            print("   %4d/%d  %.0fs" % (i, len(codes), time.time() - started), flush=True)

    errors.sort()
    n = len(errors)
    print("\n=== REAL ARCADE ENGINE: %d codes, %d points ===" % (len(codes), n))
    print("median %.5f mm | p95 %.5f | p99 %.5f | worst %.5f mm"
          % (errors[n // 2], errors[int(0.95 * n)], errors[int(0.99 * n)], errors[-1]))
    print("\nworst codes:")
    for code, d in sorted(per_code.items(), key=lambda kv: -kv[1])[:10]:
        print("   %-7d %9.5f mm  %s" % (code, d, arcpy.SpatialReference(code).name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
