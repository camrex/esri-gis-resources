"""Zone-edge envelope: how does error grow with distance from the central meridian?

The Transverse Mercator series terms are largest at the zone edges, so a comfortable
interior grid flatters it. This walks a point outwards from the central meridian and
reports where the series stops being exact -- which is also the answer to "what happens
if my data is stored outside its own zone".

    python check_zone_edges.py [build.txt]
"""
import collections
import json
import math
import os
import subprocess
import sys

# Requires ArcGIS Pro's Python -- arcpy cannot be pip-installed.
import arcpy  # pyright: ignore[reportMissingImports]

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDS = {"build": (sys.argv[1] if len(sys.argv) > 1
                    else os.path.join(HERE, "..", "builds", "arcade_latlong_condensed.txt"))}

# a representative TM State Plane zone, a wide LCC zone, and a UTM zone
CASES = [
    ("Illinois East ftUS (TM)", 6455, 38.0, -88.33333333333333),
    ("New York East (TM)",      2260, 42.0, -74.5),
    ("Texas Central (LCC)",     2277, 31.5, -100.333333333333),
    ("NAD83 / UTM 15N",        26915, 40.0, -93.0),
]
OFFSETS = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 8, 10]

pts, meta = [], []
for name, w, lat, cm in CASES:
    sr = arcpy.SpatialReference(w)
    gcs = sr.GCS
    for d in OFFSETS:
        for sgn in (1, -1):
            if d == 0 and sgn < 0:
                continue
            lon = cm + sgn * d
            g = arcpy.PointGeometry(arcpy.Point(lon, lat), gcs).projectAs(sr).getPart(0)
            pts.append([w, g.X, g.Y, lat, lon])
            meta.append((name, w, d, lat, lon))
json.dump(pts, open(os.path.join(HERE, "_edge_pts.json"), "w"))

A = 6378137.0
res = {}
for label, path in BUILDS.items():
    subprocess.run(["node", os.path.join(HERE, "harness.js"), path, "RULE",
                    os.path.join(HERE, "_edge_pts.json"), os.path.join(HERE, "_edge_res.json")],
                   check=True, capture_output=True)
    res[label] = json.load(open(os.path.join(HERE, "_edge_res.json")))

print("Error (mm) vs |longitude - central meridian|, at the zone's mid-latitude\n")
by = collections.defaultdict(dict)
for i, (name, w, d, lat, lon) in enumerate(meta):
    f = arcpy.SpatialReference(w).GCS.flattening
    e2 = 2 * f - f * f
    ph = math.radians(lat)
    s = math.sin(ph)
    wv = 1 - e2 * s * s
    M = A * (1 - e2) / wv ** 1.5
    N = A / math.sqrt(wv)
    for label in BUILDS:
        r = res[label][i]
        if not isinstance(r, dict) or "result" not in r:
            by[name].setdefault(d, {})[label] = None
            continue
        a = r["result"]["attributes"]
        dl = a["LON_CALCULATED"] - lon
        if dl > 180:
            dl -= 360
        if dl < -180:
            dl += 360
        e = math.hypot(math.radians(dl) * N * math.cos(ph),
                       math.radians(a["LAT_CALCULATED"] - lat) * M) * 1000
        prev = by[name].setdefault(d, {}).get(label)
        by[name][d][label] = e if prev is None else max(prev, e)

for name, rows in by.items():
    print("  " + name)
    print("    %6s %14s" % ("d(deg)", "error mm"))
    for d in OFFSETS:
        v = rows.get(d, {})
        def fmt(x): return "  n/a (rejected)" if x is None else "%12.4f" % x
        print("    %6.1f %14s" % (d, fmt(v.get("build"))))
    print()
