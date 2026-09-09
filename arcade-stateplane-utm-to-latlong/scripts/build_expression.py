"""Generate the Arcade projected -> lat/long expression for any set of EPSG codes.

Requires arcpy (ArcGIS Pro). Every projection parameter is read from
``arcpy.SpatialReference`` rather than typed, because ArcGIS and EPSG disagree with
each other on some published constants by up to a millimetre, and it is ArcGIS's
definition that the stored coordinates were made with.

    python build_expression.py --style documented --out ../builds/arcade_latlong_documented.txt
    python build_expression.py --style condensed  --out ../builds/arcade_latlong_condensed.txt
    python build_expression.py --codes 27700,2154 --out osgb_lambert93.txt

--codes accepts a preset (default, us), a comma-separated list, or @filename for a
file with one code per line. The presets are pinned to validated code lists, so the
published builds reproduce exactly.

ADAPTING THIS BEYOND THE US
---------------------------
Nothing here is US-specific except the code lists. Three projection methods are
implemented -- Transverse Mercator, Lambert Conformal Conic (2SP) and Hotine Oblique
Mercator -- and any code using one of them will build, on any ellipsoid, in any linear
unit. Codes using anything else are reported and refused rather than silently
mishandled. To add a method, write its inverse alongside iTM in template_condensed.py
and template_documented.py, and give it a new type number.

Datum note: an inverse projection does not change datum. Output is geodetic
coordinates on the SOURCE datum. If that datum needs a grid shift to reach WGS84
(NAD27 via NADCON, OSGB36 via OSTN15, and many others), the inverse projection supplies
only half the answer and the result will look right while being tens of metres wrong.
Carrying a grid shift was not attempted here, so such codes are excluded by default --
see --allow-datum-shift if you have handled the shift some other way.
"""
import argparse
import collections
import json
import os
import re
import sys

# Requires ArcGIS Pro's Python -- arcpy cannot be pip-installed.
import arcpy  # pyright: ignore[reportMissingImports]

from template_condensed import CONDENSED
from template_documented import DOCUMENTED

HERE = os.path.dirname(os.path.abspath(__file__))

# Projection methods this template implements, mapped to the type number used in
# the emitted zone table.
METHODS = {
    "Transverse_Mercator": 0,
    "Lambert_Conformal_Conic": 1,
    "Hotine_Oblique_Mercator_Azimuth_Natural_Origin": 2,
}

# Datums that reach WGS84 only through a grid shift, which this build does not attempt.
# Matched case-insensitively against Esri's datum name, which is usually "D_<name>".
GRID_SHIFT_DATUMS = ("North_American_1927", "NAD_1927", "NAD27", "OSGB", "Ordnance_Survey",
                     "ATS_1977", "Puerto_Rico", "Old_Hawaiian", "Guam_1963",
                     "American_Samoa", "Tokyo", "Bermuda_1957", "Qornoq")

# The two published builds are pinned to explicit, validated code lists rather than
# discovered at run time: an auto-discovered "US" set silently pulls in UTM zones on
# every datum worldwide, and the point of a published artifact is that it reproduces.
PRESETS = {
    "default": "codes.txt",     # what the published builds carry
    "us": "us_codes.txt",       # worked example of trimming to a subset
}


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--codes", default="default",
                    help="preset (default|us), comma list, or @file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lat-field", default="LAT_CALCULATED")
    ap.add_argument("--lon-field", default="LON_CALCULATED")
    ap.add_argument("--label", default=None, help="scope description for the header")
    ap.add_argument("--style", choices=("condensed", "documented"), default="condensed",
                    help="condensed is for pasting into a dialog; documented is the "
                         "one to read. They run at identical speed.")
    ap.add_argument("--allow-datum-shift", action="store_true",
                    help="keep codes whose datum needs a grid shift (NOT recommended)")
    return ap.parse_args(argv)


def read_code_file(path):
    codes = []
    for line in open(path, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if line:
            codes.append(int(line))
    return sorted(set(codes))


def select_codes(spec):
    if spec in PRESETS:
        return read_code_file(os.path.join(HERE, PRESETS[spec]))
    if spec.startswith("@"):
        return read_code_file(spec[1:])
    return sorted({int(x) for x in spec.split(",") if x.strip()})


def wkt_param(sr, name):
    m = re.search(r'PARAMETER\["%s",(-?[\d.eE+]+)' % name, sr.exportToString())
    return float(m.group(1)) if m else None


def required_param(sr, code, name):
    """A WKT parameter with no safe default: if it is absent, refuse the code.

    snap_angle turns a missing angle into 0.0, which is right for a parameter ArcGIS
    omits because it is zero, and wrong for one that is simply not written under the
    name looked for here -- a Hotine zone would then be built around latitude 0,
    longitude 0, on an azimuth of 0, and every constant after it would be plausible
    and wrong. Refusing joins the same path as an unimplemented projection method.
    """
    v = wkt_param(sr, name)
    if v is None:
        raise ValueError('%s uses %s, whose WKT here carries no PARAMETER["%s"]'
                         % (code, sr.projectionName, name))
    return v


def snap_angle(deg):
    """Collapse float-representation noise so two definitions of the same zone dedupe.

    ArcGIS writes the same parameter as 34.33333333333334 in one realization and
    34.333333333333336 in another. Angles are emitted in arcseconds anyway, so snap
    to a whole arcsecond when within 1e-7 of one; the difference is 1e-11 degrees,
    about a nanometre on the ground.
    """
    if deg is None:
        return 0.0
    a = deg * 3600.0
    return round(a) / 3600.0 if abs(a - round(a)) < 1e-7 else deg


def snap_length(m):
    return round(m, 9) if m is not None else 0.0


def describe(code):
    """Everything the template needs about one EPSG code, in metres and degrees."""
    sr = arcpy.SpatialReference(code)
    if sr.type != "Projected":
        raise ValueError("%s is not a projected coordinate system" % code)
    if sr.projectionName not in METHODS:
        raise ValueError("%s uses %s, which this template does not implement"
                         % (code, sr.projectionName))
    gcs = sr.GCS
    mpu = sr.metersPerUnit
    fe = snap_length(sr.falseEasting * mpu)
    fn = snap_length(sr.falseNorthing * mpu)
    kind = METHODS[sr.projectionName]
    if kind == 0:
        row = (0, snap_angle(sr.latitudeOfOrigin), snap_angle(sr.centralMeridian),
               sr.scaleFactor, 0.0, fe, fn, 0.0)
    elif kind == 1:
        row = (1, snap_angle(sr.latitudeOfOrigin), snap_angle(sr.centralMeridian),
               snap_angle(sr.standardParallel1), snap_angle(sr.standardParallel2), fe, fn, 0.0)
    else:
        az = required_param(sr, code, "Azimuth") % 360.0
        row = (2, snap_angle(required_param(sr, code, "Latitude_Of_Center")),
               snap_angle(required_param(sr, code, "Longitude_Of_Center")),
               az, sr.scaleFactor, fe, fn, az)
    f = gcs.flattening
    return dict(row=row, mpu=mpu, axis=gcs.semiMajorAxis, inv_flat=(1.0 / f) if f else 0.0,
                gcs_code=gcs.factoryCode, gcs_name=gcs.name, name=sr.name,
                datum=gcs.datumName, is_utm=("UTM" in sr.name.upper() or "BLM" in sr.name.upper()))


def shortest(v):
    """Shortest decimal literal that round-trips to the same double."""
    if v == int(v):
        return str(int(v))
    for digits in range(6, 18):
        t = "%.*g" % (digits, v)
        if float(t) == float(v):
            return t
    return repr(float(v))


def arcseconds(deg):
    """Angles are stored in arcseconds: every US zone is a whole arcsecond, which is
    both shorter and exact. Non-integral angles simply stay fractional."""
    a = deg * 3600.0
    return int(round(a)) if abs(a - round(a)) < 1e-7 else a


def wrap(items, width=100):
    out, line = [], ""
    for it in items:
        if line and len(line) + len(it) + 1 > width:
            out.append(line)
            line = it
        else:
            line = it if not line else line + "," + it
    if line:
        out.append(line)
    return ",\n".join(out)


def compress_runs(pairs):
    """[(wkid, value)] sorted -> [(firstWkid, count, firstValue, wkidStep, valueStep)]."""
    runs, i = [], 0
    while i < len(pairs):
        w0, v0 = pairs[i]
        n, dw, dv = 1, 1, 0
        if i + 1 < len(pairs):
            dw2, dv2 = pairs[i + 1][0] - w0, pairs[i + 1][1] - v0
            m = 1
            while i + m < len(pairs) and pairs[i + m] == (w0 + m * dw2, v0 + m * dv2):
                m += 1
            if m > 1:
                n, dw, dv = m, dw2, dv2
        runs.append((w0, n, v0, dw, dv))
        i += n
    return runs


def build(args):
    codes = select_codes(args.codes)
    if not codes:
        sys.exit("no codes selected for %r" % args.codes)

    info, refused = {}, []
    for c in codes:
        try:
            info[c] = describe(c)
        except ValueError as e:
            refused.append(str(e))
    if refused:
        print("skipped %d code(s) this template cannot build:" % len(refused))
        for r in refused[:8]:
            print("   " + r)

    if not args.allow_datum_shift:
        blocked = [c for c, d in info.items()
                   if any(g.lower() in (d["datum"] or "").lower() for g in GRID_SHIFT_DATUMS)]
        for c in blocked:
            del info[c]
        if blocked:
            print("excluded %d code(s) whose datum needs a grid shift this build does "
                  "not attempt (pass --allow-datum-shift to override)" % len(blocked))
    codes = sorted(info)

    # distinct parameter rows, and the value tables they index into
    rows = list(collections.OrderedDict.fromkeys(info[c]["row"] for c in codes))
    KS = sorted({r[3] for r in rows if r[0] == 0} | {r[4] for r in rows if r[0] == 2})
    FE = sorted({r[5] for r in rows})
    FN = sorted({r[6] for r in rows})
    UT = sorted({info[c]["mpu"] for c in codes})
    ELL = sorted({(info[c]["axis"], info[c]["inv_flat"]) for c in codes})
    row_index = {r: i for i, r in enumerate(rows)}

    # How to recover the ellipsoid index. One ellipsoid needs no test at all; the
    # WGS84-UTM range test keeps the common US case small; otherwise pack it in.
    wgs = [i for i, e in enumerate(ELL) if abs(e[1] - 298.257223563) < 1e-6]
    range_ok, wi = False, 0          # wi is only read when range_ok, but bind it anyway
    if len(ELL) == 2 and wgs:
        wi = wgs[0]
        range_ok = all((32601 <= c <= 32760) == (ELL.index((info[c]["axis"], info[c]["inv_flat"])) == wi)
                       for c in codes)
    if len(ELL) == 1:
        stride, unit_mod, ell_sel = len(UT), len(UT), "0"
    elif range_ok:
        stride, unit_mod = len(UT), len(UT)
        ell_sel = "IIf(wn>=32601&&wn<=32760,%d,%d)" % (wi, 1 - wi)
    else:
        stride, unit_mod = len(UT) * len(ELL), len(UT)
        ell_sel = "Floor(pk/%d)-Floor(pk/%d)*%d" % (unit_mod, stride, len(ELL))

    value = {}
    for c in codes:
        d = info[c]
        ui = UT.index(d["mpu"])
        ei = ELL.index((d["axis"], d["inv_flat"]))
        zi = row_index[d["row"]]
        value[c] = zi * stride + (ei * unit_mod if not (len(ELL) == 1 or range_ok) else 0) + ui
    runs = compress_runs([(c, value[c]) for c in codes])

    def enc(r):
        o = [r[0], arcseconds(r[1]), arcseconds(r[2]), 0, 0, FE.index(r[5]), FN.index(r[6]), 0]
        if r[0] == 0:
            o[3] = KS.index(r[3])
        elif r[0] == 1:
            o[3], o[4] = arcseconds(r[3]), arcseconds(r[4])
        else:
            o[3], o[4], o[7] = shortest(r[3]), KS.index(r[4]), shortest(r[7])
        return o

    # Geographic systems pass straight through: the data is already in degrees,
    # so the centroid IS the answer. Most are picked up from the projected
    # codes' own GCS, but three have to be named. 4326 need not be any code's
    # GCS. 4267 never is, because the NAD 27 *projected* zones are refused --
    # but refusing NAD 27 *geographic* would be a different claim: inverting a
    # projection is what the grid shift is missing from, and there is no
    # projection to invert here. 4979 is a 3D variant no projected code
    # declares. All three return degrees on their own datum, which is what this
    # expression does everywhere else.
    GW = sorted({info[c]["gcs_code"] for c in codes} | {4326, 4267, 4979})
    n_utm = sum(1 for c in codes if info[c]["is_utm"])
    label = args.label or args.codes
    header = (
        "// PROJECTED COORDINATES -> LATITUDE / LONGITUDE, for ArcGIS Arcade.\n"
        "// Build: %s -- %d coordinate system codes (%d projected-zone variants, %d UTM/BLM), "
        "%d parameter sets.\n"
        "// Generated by build_expression.py from arcpy.SpatialReference. Do not hand-edit.\n"
        "//\n"
        "// USE: set MD below.\n"
        '//   "LAT"  latitude as a number   -> Calculate Field into a DOUBLE field\n'
        '//   "LON"  longitude as a number  -> Calculate Field into a DOUBLE field\n'
        '//   "BOTH" "Lat: 37.4952, Lon: -89.09" -> popups, labels, or a TEXT field\n'
        '//   "RULE" attribute-rule dictionary writing both fields at once\n'
        "// Float fields cap accuracy near 0.2 m; use Double. Attribute rules also need\n"
        "// the feature class to have a GlobalID field.\n"
        "//\n"
        "// Any geometry type. Non-point features report the geometry centroid, which for a\n"
        "// concave or donut polygon can fall outside the polygon; Arcade has no\n"
        "// guaranteed-inside point.\n"
        "//\n"
        "// DATUM: an inverse projection does not change datum. Output is geodetic on the\n"
        "// source datum. Feature classes already stored geographic pass straight through.\n"
        "//\n"
        "// Ellipsoids in this build: %s\n"
        % (label, len(codes), len(codes) - n_utm, n_utm, len(rows),
           "; ".join("a=%s 1/f=%s" % (shortest(a), shortest(f)) for a, f in ELL)))

    out = CONDENSED if args.style == "condensed" else DOCUMENTED
    subs = {
        "HEADER": header.rstrip("\n"),
        "LAT_FIELD": args.lat_field,
        "LON_FIELD": args.lon_field,
        "GW": "[" + ",".join(str(c) for c in GW) + "]",
        "KS": "[" + ",".join(shortest(v) for v in KS) + "]",
        "FE": "[" + ",".join(shortest(v) for v in FE) + "]",
        "FN": "[" + ",".join(shortest(v) for v in FN) + "]",
        "UT": "[" + ",".join(shortest(v) for v in UT) + "]",
        "EL": "[" + ",".join("ecn(%s,%s)" % (shortest(a), shortest(f)) for a, f in ELL) + "]",
        "ZN": wrap(["[" + ",".join(str(x) for x in enc(r)) + "]" for r in rows]),
        "RN": wrap(["[%d,%d,%d,%d,%d]" % r for r in runs]),
        "STRIDE": str(stride),
        "UNIT_MOD": str(unit_mod),
        "ELL_SELECT": ell_sel,
        "N_ROWS": str(len(rows)),
        "N_RUNS": str(len(runs)),
        "N_CODES": str(len(codes)),
    }
    for k, v in subs.items():
        out = out.replace("@@%s@@" % k, v)
    assert "@@" not in out, out[out.index("@@"):out.index("@@") + 40]

    open(args.out, "w", encoding="utf-8").write(out)
    print("%s: %d codes, %d parameter sets, %d runs, %d ellipsoid(s), %d byte(s)"
          % (os.path.basename(args.out), len(codes), len(rows), len(runs), len(ELL), len(out)))
    json.dump(codes, open(os.path.splitext(args.out)[0] + "_codes.json", "w"))
    return out


if __name__ == "__main__":
    build(parse_args())
