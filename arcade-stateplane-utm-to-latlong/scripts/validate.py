"""Validate a build against arcpy, headlessly, for every EPSG code it claims.

Requires arcpy and Node.js. Two stages:

  1. arcpy lays a grid of latitude/longitude points across each code's usable extent
     and forward-projects them, inside that code's OWN geographic system so no datum
     transformation contaminates the comparison.
  2. harness.js executes the build's ACTUAL Arcade text under Node with the Arcade
     built-ins mapped to JavaScript, and the returned coordinates are compared with
     the originals as a ground distance in millimetres.

    python validate.py ../builds/arcade_latlong_condensed.txt
    python validate.py ../builds/arcade_latlong_condensed.txt --grid 9 --json out.json

The Node harness is a proxy for the real engine, not a substitute for it: it cannot
see Arcade's case-insensitive identifiers, and it does not prove the attribute-rule
profile accepts the syntax. Run lint.py and run_in_arcade.py as well.
"""
import argparse
import collections
import json
import math
import os
import re
import subprocess
import sys

# Requires ArcGIS Pro's Python -- arcpy cannot be pip-installed.
import arcpy  # pyright: ignore[reportMissingImports]

HERE = os.path.dirname(os.path.abspath(__file__))
A_DEFAULT = 6378137.0


def codes_for(build_path):
    """Prefer the *_codes.json written next to the build; else parse the run table."""
    side = os.path.splitext(build_path)[0] + "_codes.json"
    if os.path.exists(side):
        return json.load(open(side))
    text = open(build_path, encoding="utf-8").read()
    m = re.search(r"var RN=\[(.*?)\n\];", text, re.S)
    if not m:
        sys.exit("cannot determine the code list for %s" % build_path)
    codes = []
    for w0, cnt, v0, dw, dv in re.findall(r"\[(-?\d+),(\d+),(-?\d+),(\d+),(-?\d+)\]", m.group(1)):
        codes += [int(w0) + i * int(dw) for i in range(int(cnt))]
    return sorted(set(codes))


def linspace(a, b, n):
    return [(a + b) / 2.0] if n == 1 else [a + (b - a) * i / (n - 1.0) for i in range(n)]


def extent_for(sr, n):
    """A grid of test latitudes/longitudes covering the code's usable area.

    Derived from the projection's own parameters, so it works for any zone anywhere,
    and deliberately reaches the edges where the series terms are largest.
    """
    cm, lat0 = sr.centralMeridian, sr.latitudeOfOrigin
    name = sr.name.upper()
    if sr.projectionName.startswith("Hotine"):
        return linspace(lat0 - 3.0, lat0 + 3.0, n), linspace(cm - 6.0, cm + 6.0, n)
    if sr.projectionName == "Lambert_Conformal_Conic":
        lo, hi = sorted([sr.standardParallel1, sr.standardParallel2])
        return linspace(lo - 2.0, hi + 2.0, n), linspace(cm - 4.0, cm + 4.0, n)
    is_utm = ("UTM" in name or "BLM" in name) and abs(sr.scaleFactor - 0.9996) < 1e-12
    if is_utm:
        south = sr.falseNorthing * sr.metersPerUnit > 1e6
        lats = linspace(-79.5, -0.5, n) if south else linspace(0.5, 84.0, n)
        return lats, linspace(cm - 3.0, cm + 3.0, n)
    return linspace(lat0 + 0.05, lat0 + 6.0, n), linspace(cm - 2.0, cm + 2.0, n)


def ground_mm(lat, dlat, dlon, e2, axis):
    ph = math.radians(lat)
    s = math.sin(ph)
    w = 1 - e2 * s * s
    meridional = axis * (1 - e2) / (w ** 1.5)
    prime_vertical = axis / math.sqrt(w)
    return math.hypot(math.radians(dlon) * prime_vertical * math.cos(ph),
                      math.radians(dlat) * meridional) * 1000.0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("build")
    ap.add_argument("--grid", type=int, default=7, help="N x N points per code")
    ap.add_argument("--json", default=None, help="write per-code worst errors here")
    ap.add_argument("--node", default="node")
    a = ap.parse_args(argv)

    codes = codes_for(a.build)
    print("validating %s: %d EPSG codes, %d x %d points each"
          % (os.path.basename(a.build), len(codes), a.grid, a.grid))

    points, meta = [], []
    for code in codes:
        sr = arcpy.SpatialReference(code)
        gcs = sr.GCS
        lats, lons = extent_for(sr, a.grid)
        pts = [arcpy.Point(lo, la) for la in lats for lo in lons]
        projected = arcpy.Multipoint(arcpy.Array(pts), gcs).projectAs(sr)
        f = gcs.flattening
        e2 = 2 * f - f * f
        axis = gcs.semiMajorAxis or A_DEFAULT
        i = 0
        for la in lats:
            for lo in lons:
                p = projected.getPart(i)
                i += 1
                points.append([code, p.X, p.Y, la, lo])
                meta.append((e2, axis))
    print("   %d reference points from arcpy" % len(points))

    tmp_in = os.path.join(HERE, "_validate_points.json")
    tmp_out = os.path.join(HERE, "_validate_results.json")
    json.dump(points, open(tmp_in, "w"))
    subprocess.run([a.node, os.path.join(HERE, "harness.js"), a.build, "RULE", tmp_in, tmp_out],
                   check=True)
    results = json.load(open(tmp_out))

    errors, per_code, failures = [], collections.defaultdict(float), collections.Counter()
    for (code, x, y, lat, lon), (e2, axis), r in zip(points, meta, results):
        if not isinstance(r, dict) or "result" not in r:
            reason = r.get("errorMessage") or r.get("__throw") if isinstance(r, dict) else repr(r)
            failures[str(reason)[:90]] += 1
            per_code[code] = float("inf")
            continue
        attrs = r["result"]["attributes"]
        got_lat = attrs[list(attrs)[0]] if len(attrs) == 1 else attrs.get("LAT_CALCULATED")
        got_lon = attrs.get("LON_CALCULATED")
        if got_lat is None or got_lon is None:      # custom field names
            vals = list(attrs.values())
            got_lat, got_lon = vals[0], vals[1]
        dlon = got_lon - lon
        if dlon > 180:
            dlon -= 360
        if dlon < -180:
            dlon += 360
        d = ground_mm(lat, got_lat - lat, dlon, e2, axis)
        errors.append(d)
        per_code[code] = max(per_code[code], d)

    if failures:
        print("\n   NON-NUMERIC RESULTS:")
        for reason, count in failures.most_common(6):
            print("      %6d x %s" % (count, reason))
    if not errors:
        sys.exit("no points evaluated successfully")

    errors.sort()
    n = len(errors)
    print("\n   median %.5f mm | p95 %.5f | p99 %.5f | worst %.5f mm"
          % (errors[n // 2], errors[int(0.95 * n)], errors[int(0.99 * n)], errors[-1]))
    worst = sorted(per_code.items(), key=lambda kv: -kv[1])[:10]
    print("\n   worst codes:")
    for code, d in worst:
        print("      %-7d %9.5f mm  %s" % (code, d, arcpy.SpatialReference(code).name))
    if a.json:
        json.dump({str(k): v for k, v in per_code.items()}, open(a.json, "w"), indent=0)
        print("\n   per-code worst errors -> %s" % a.json)
    # The results file is disposable; the points file is deliberately kept, because
    # compare_builds.js reuses it to check the two builds against each other.
    os.remove(tmp_out)
    print("\n   reference points kept at %s for compare_builds.js"
          % os.path.basename(tmp_in))
    return 0 if errors[-1] < 1.0 and not failures else 1


if __name__ == "__main__":
    sys.exit(main())
