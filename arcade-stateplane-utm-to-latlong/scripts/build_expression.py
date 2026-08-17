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
mishandled. To add a method, write its inverse alongside iTM in the template below and
in template_documented.py, and give it a new type number.

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

import arcpy

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
        az = wkt_param(sr, "Azimuth") % 360.0
        row = (2, snap_angle(wkt_param(sr, "Latitude_Of_Center")),
               snap_angle(wkt_param(sr, "Longitude_Of_Center")),
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


# --------------------------------------------------------------------------- #
#  The Arcade template. Data blocks are substituted; the maths is fixed.
#  @@ELL_SELECT@@ is either a constant 0, a WKID range test, or an index unpacked
#  from the run value, depending on how many ellipsoids the chosen codes use.
# --------------------------------------------------------------------------- #
TEMPLATE = r'''@@HEADER@@
var MD="LAT";
var FMT="#.######";
var LF="@@LAT_FIELD@@";
var NF="@@LON_FIELD@@";
var FV=null;
var GW=@@GW@@;
var KS=@@KS@@;
var FE=@@FE@@;
var FN=@@FN@@;
var UT=@@UT@@;
var ZN=[
@@ZN@@
];
var RN=[
@@RN@@
];
function ecn(ax,fi){
 var fl=1.0/fi;
 var e2=2*fl-fl*fl;
 var n3=fl/(2-fl);
 return [e2,Sqrt(e2),e2/(1-e2),ax/(1+n3)*(1+Pow(n3,2)/4+Pow(n3,4)/64),
  -3*n3/2+9*Pow(n3,3)/16,15*Pow(n3,2)/16-15*Pow(n3,4)/32,-35*Pow(n3,3)/48,315*Pow(n3,4)/512,
  3*n3/2-27*Pow(n3,3)/32,21*Pow(n3,2)/16-55*Pow(n3,4)/32,151*Pow(n3,3)/96,1097*Pow(n3,4)/512,
  e2/2+5*Pow(e2,2)/24+Pow(e2,3)/12+13*Pow(e2,4)/360,
  7*Pow(e2,2)/48+29*Pow(e2,3)/240+811*Pow(e2,4)/11520,
  7*Pow(e2,3)/120+81*Pow(e2,4)/1120,4279*Pow(e2,4)/161280,ax];
}
var EL=@@EL@@;
function rd(dv){ return dv*PI/180.0; }
function dg(rv){ return rv*180.0/PI; }
function ma(ph,es){ return es[3]*(ph+es[4]*Sin(2*ph)+es[5]*Sin(4*ph)+es[6]*Sin(6*ph)+es[7]*Sin(8*ph)); }
function fpr(mu,es){ return mu+es[8]*Sin(2*mu)+es[9]*Sin(4*mu)+es[10]*Sin(6*mu)+es[11]*Sin(8*mu); }
function cpr(ch,es){ return ch+es[12]*Sin(2*ch)+es[13]*Sin(4*ch)+es[14]*Sin(6*ch)+es[15]*Sin(8*ch); }
function tfn(ph,es){ return Tan(PI/4-ph/2)/Pow((1-es[1]*Sin(ph))/(1+es[1]*Sin(ph)),es[1]/2); }
function mfn(ph,es){ return Cos(ph)/Sqrt(1-es[0]*Pow(Sin(ph),2)); }
function bad(ms){ if(MD=="RULE"){ return {"errorMessage":ms}; } return FV; }
function iTM(xx,yy,zr,es){
 var k0=zr[3];
 var mu=(yy-zr[6]+k0*ma(rd(zr[1]),es))/(k0*es[3]);
 var ph=fpr(mu,es);
 var qq=(xx-zr[5])/(k0*es[16]/Sqrt(1-es[0]*Pow(Sin(ph),2)));
 var q2=qq*qq;
 var tn=Tan(ph);
 var t2=tn*tn;
 var t4=t2*t2;
 var et=es[2]*Pow(Cos(ph),2);
 var b2=-0.5*tn*(1+et);
 var b4=-(1.0/12.0)*(5+3*t2+et*(1-9*t2)-4*et*et);
 var b6=(1.0/360.0)*(61+90*t2+45*t4+et*(46-252*t2-90*t4));
 var b3=-(1.0/6.0)*(1+2*t2+et);
 var b5=(1.0/120.0)*(5+28*t2+24*t4+et*(6+8*t2));
 var b7=-(1.0/5040.0)*(61+662*t2+1320*t4+720*t2*t4);
 var ph2=ph+b2*q2*(1+q2*(b4+b6*q2));
 var lm=rd(zr[2])+qq*(1+q2*(b3+q2*(b5+b7*q2)))/Cos(ph);
 return [dg(ph2),dg(lm)];
}
function iLC(xx,yy,zr,es){
 var s1=rd(zr[3]);
 var s2=rd(zr[4]);
 var t1=tfn(s1,es);
 var t2=tfn(s2,es);
 var nn=0;
 if(Abs(s1-s2)<0.000000000001){ nn=Sin(s1); } else { nn=(Log(mfn(s1,es))-Log(mfn(s2,es)))/(Log(t1)-Log(t2)); }
 var fk=mfn(s1,es)/(nn*Pow(t1,nn));
 var r0=es[16]*fk*Pow(tfn(rd(zr[1]),es),nn);
 var dx=xx-zr[5];
 var dy=r0-(yy-zr[6]);
 var sg=IIf(nn>0,1.0,-1.0);
 var tt=Pow(sg*Sqrt(dx*dx+dy*dy)/(es[16]*fk),1.0/nn);
 return [dg(cpr(PI/2-2*Atan(tt),es)),dg(rd(zr[2])+Atan2(sg*dx,sg*dy)/nn)];
}
function iHO(xx,yy,zr,es){
 var e2=es[0];
 var pc=rd(zr[1]);
 var kc=zr[4];
 var sn=Sin(pc);
 var bb=Sqrt(1+e2*Pow(Cos(pc),4)/(1-e2));
 var ab=es[16]*bb*kc*Sqrt(1-e2)/(1-e2*sn*sn);
 var dd=bb*Sqrt(1-e2)/(Cos(pc)*Sqrt(1-e2*sn*sn));
 var fk=dd+Sqrt(Max(dd*dd,1.0)-1)*IIf(pc>=0,1.0,-1.0);
 var hh=fk*Pow(tfn(pc,es),bb);
 var gg=(fk-1/fk)/2;
 var ga=Asin(Sin(rd(zr[3]))/dd);
 var lc=rd(zr[2])-Asin(gg*Tan(ga))/bb;
 var rg=rd(zr[7]);
 var de=xx-zr[5];
 var dn=yy-zr[6];
 var vv=de*Cos(rg)-dn*Sin(rg);
 var uu=dn*Cos(rg)+de*Sin(rg);
 var qq=Exp(-(bb*vv)/ab);
 var ss=(qq-1/qq)/2;
 var tt=(qq+1/qq)/2;
 var vs=Sin(bb*uu/ab);
 var us=(vs*Cos(ga)+ss*Sin(ga))/tt;
 var tp=Pow(hh/Sqrt((1+us)/(1-us)),1.0/bb);
 return [dg(cpr(PI/2-2*Atan(tp),es)),dg(lc-Atan2(ss*Cos(ga)-vs*Sin(ga),Cos(bb*uu/ab))/bb)];
}
var gm=Geometry($feature);
if(IsEmpty(gm)){ return bad("No geometry."); }
var ky=Text(gm.spatialReference.wkid);
var wn=Number(ky);
var ct=Centroid(gm);
var ll=[0,0];
if(Includes(GW,wn)){
 ll=[ct.Y,ct.X];
} else {
 var pk=-1;
 for(var i=0;i<Count(RN);i++){
  var rr=RN[i];
  var dd=wn-rr[0];
  if(dd>=0 && dd<=rr[3]*(rr[1]-1) && dd%rr[3]==0){ pk=rr[2]+(dd/rr[3])*rr[4]; break; }
 }
 if(pk<0){ return bad("WKID "+ky+" is not a supported coordinate system for this build."); }
 var zi=Floor(pk/@@STRIDE@@);
 var es=EL[@@ELL_SELECT@@];
 var um=UT[pk-Floor(pk/@@UNIT_MOD@@)*@@UNIT_MOD@@];
 var zc=ZN[zi];
 var zz=[zc[0],zc[1]/3600,zc[2]/3600,0,0,FE[zc[5]],FN[zc[6]],zc[7]/3600];
 if(zc[0]==0){ zz[3]=KS[zc[3]]; }
 else if(zc[0]==1){ zz[3]=zc[3]/3600; zz[4]=zc[4]/3600; }
 else { zz[3]=zc[3]; zz[4]=KS[zc[4]]; zz[7]=zc[7]; }
 var xm=ct.X*um;
 var ym=ct.Y*um;
 if(zz[0]==0){ ll=iTM(xm,ym,zz,es); } else if(zz[0]==1){ ll=iLC(xm,ym,zz,es); } else { ll=iHO(xm,ym,zz,es); }
}
var la=Round(ll[0],9);
var lr=ll[1];
if(lr>180){ lr=lr-360; }
if(lr<-180){ lr=lr+360; }
var lo=Round(lr,9);
if(IsNan(la)||IsNan(lo)||Abs(la)>90||Abs(lo)>180){ return bad("Inverse projection failed for WKID "+ky+"."); }
if(MD=="LAT"){ return la; }
if(MD=="LON"){ return lo; }
if(MD=="BOTH"){ return "Lat: "+Text(la,FMT)+", Lon: "+Text(lo,FMT); }
return {"result":{"attributes":Dictionary(LF,la,NF,lo)}};
'''


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
        print("skipped %d code(s) using unimplemented projection methods:" % len(refused))
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
    range_ok = False
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

    GW = sorted({info[c]["gcs_code"] for c in codes} | {4326})
    n_utm = sum(1 for c in codes if info[c]["is_utm"])
    label = args.label or args.codes
    header = (
        "// PROJECTED COORDINATES -> LATITUDE / LONGITUDE, for ArcGIS Arcade.\n"
        "// Build: %s -- %d EPSG codes (%d projected-zone variants, %d UTM/BLM), %d parameter sets.\n"
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

    out = TEMPLATE if args.style == "condensed" else DOCUMENTED
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
