"""The documented Arcade template, used by build_expression.py --style documented.

Same program as the condensed template, same substitutions. Comments and long
identifiers are free at run time -- the documented build measures 963 us/feature
against 966 us for the condensed one -- so this is the version to read, and the
condensed one exists only for pasting into a small dialog.

Arcade identifiers are CASE-INSENSITIVE. `U` and `u` are the same variable. Every
name below is deliberately distinct case-insensitively; run lint.py after editing.
"""

DOCUMENTED = r'''@@HEADER@@

// ---------------------------------------------------------------------------
//  OUTPUT MODE -- the one line to change.
// ---------------------------------------------------------------------------
var MD = "LAT";                       // "LAT" | "LON" | "BOTH" | "RULE"

// Number format for "BOTH". Each # is an optional decimal, so trailing zeros drop.
var FMT = "#.######";

// Field names written by "RULE" mode.
var LF = "@@LAT_FIELD@@";
var NF = "@@LON_FIELD@@";

// What the non-RULE modes return when a feature cannot be converted. RULE mode has a
// diagnostic channel (an errorMessage dictionary, which aborts the edit); the others
// do not, so they return null. Set this to something like -999 to symbolise on it.
var FV = null;

function bad(message) {
  if (MD == "RULE") { return {"errorMessage": message}; }
  return FV;
}

// ---------------------------------------------------------------------------
//  1. GEOGRAPHIC SYSTEMS -- nothing to invert
//
//  A feature class stored in one of these already holds degrees, so latitude and
//  longitude are the centroid straight through. These are the geographic systems
//  underlying the projected codes below, plus WGS 84.
// ---------------------------------------------------------------------------
var GW = @@GW@@;

// ---------------------------------------------------------------------------
//  2. SHARED VALUE TABLES
//
//  Scale factors and false origins repeat across zones, so each distinct value is
//  written once and referenced by index. False origins are ALWAYS IN METRES,
//  whatever the zone's display units -- x and y are converted before use.
// ---------------------------------------------------------------------------
var KS = @@KS@@;                      // scale factors
var FE = @@FE@@;                      // false eastings, metres
var FN = @@FN@@;                      // false northings, metres
var UT = @@UT@@;                      // metres per linear unit

// ---------------------------------------------------------------------------
//  3. ZONE TABLE -- @@N_ROWS@@ distinct parameter sets
//
//  [ type, latOrigin, lonOrigin, p1, p2, feIndex, fnIndex, rectifiedGridAngle ]
//
//    type 0 = Transverse Mercator          p1 = index into KS
//    type 1 = Lambert Conformal Conic 2SP  p1, p2 = standard parallels
//    type 2 = Hotine Oblique Mercator      p1 = azimuth in DEGREES, p2 = index into KS
//
//  ANGLES ARE ARCSECONDS, not degrees. Every angle in every US zone is an exact
//  arcsecond, so integers are both shorter and exact where a decimal degree would
//  round; divide by 3600 to use them. The Hotine azimuth and rectified grid angle
//  stay in degrees.
//
//  Positive north and positive EAST.
// ---------------------------------------------------------------------------
var ZN = [
@@ZN@@
];

// ---------------------------------------------------------------------------
//  4. WKID LOOKUP -- @@N_CODES@@ codes in @@N_RUNS@@ arithmetic runs
//
//  [ firstWkid, count, firstValue, wkidStep, valueStep ]
//
//  Datum realizations occupy contiguous WKID ranges that step through the zones in
//  the same order, so the table collapses into runs. A run matches when:
//
//      offset = wkid - firstWkid,  0 <= offset <= wkidStep * (count - 1),
//      offset MOD wkidStep == 0
//
//  and then value = firstValue + (offset / wkidStep) * valueStep,
//  where value = zoneRow * @@STRIDE@@ + (ellipsoid and unit indexes).
//
//  Runs are why this is both smaller and faster than a flat dictionary: Arcade
//  rebuilds literal tables on every feature, so ENTRY COUNT -- not file size --
//  is what costs time. Comments cost nothing.
// ---------------------------------------------------------------------------
var RN = [
@@RN@@
];

// ---------------------------------------------------------------------------
//  5. ELLIPSOID CONSTANTS, derived rather than tabulated
//
//  Everything comes from the semi-major axis and the third flattening n = f/(2-f),
//  so no per-zone constant is looked up or maintained. The returned array is:
//
//    [0]  e2    first eccentricity squared      [1]  e    first eccentricity
//    [2]  ep2   second eccentricity squared     [3]  rectifying radius
//    [4..7]   meridional arc series             [8..11]  footpoint series
//    [12..15] conformal-to-geodetic series      [16] semi-major axis
//
//  Cross-check: the rectifying radius for GRS80 comes out 6367449.145771 m against
//  the published 6367449.14577 m (NOAA NOS NGS 5).
// ---------------------------------------------------------------------------
function ecn(ax, fi) {
  var fl = 1.0 / fi;
  var e2 = 2 * fl - fl * fl;
  var n3 = fl / (2 - fl);             // third flattening
  return [e2, Sqrt(e2), e2 / (1 - e2),
    ax / (1 + n3) * (1 + Pow(n3, 2) / 4 + Pow(n3, 4) / 64),
    -3 * n3 / 2 + 9 * Pow(n3, 3) / 16,
    15 * Pow(n3, 2) / 16 - 15 * Pow(n3, 4) / 32,
    -35 * Pow(n3, 3) / 48,
    315 * Pow(n3, 4) / 512,
    3 * n3 / 2 - 27 * Pow(n3, 3) / 32,
    21 * Pow(n3, 2) / 16 - 55 * Pow(n3, 4) / 32,
    151 * Pow(n3, 3) / 96,
    1097 * Pow(n3, 4) / 512,
    e2 / 2 + 5 * Pow(e2, 2) / 24 + Pow(e2, 3) / 12 + 13 * Pow(e2, 4) / 360,
    7 * Pow(e2, 2) / 48 + 29 * Pow(e2, 3) / 240 + 811 * Pow(e2, 4) / 11520,
    7 * Pow(e2, 3) / 120 + 81 * Pow(e2, 4) / 1120,
    4279 * Pow(e2, 4) / 161280,
    ax];
}

var EL = @@EL@@;

// ---------------------------------------------------------------------------
//  6. SMALL HELPERS
// ---------------------------------------------------------------------------
function rd(degrees) { return degrees * PI / 180.0; }
function dg(radians) { return radians * 180.0 / PI; }

// Meridional arc: distance along the meridian from the equator to latitude phi.
function ma(phi, es) {
  return es[3] * (phi + es[4] * Sin(2 * phi) + es[5] * Sin(4 * phi)
                      + es[6] * Sin(6 * phi) + es[7] * Sin(8 * phi));
}

// Footpoint latitude: the inverse of ma, given rectifying latitude mu.
function fpr(mu, es) {
  return mu + es[8] * Sin(2 * mu) + es[9] * Sin(4 * mu)
            + es[10] * Sin(6 * mu) + es[11] * Sin(8 * mu);
}

// Conformal latitude -> geodetic latitude, as a series. The iterative form reaches
// ~0.000 mm rather than this series' ~0.01 mm, but a series has no loop, and the
// residual sits far below a geodatabase's own coordinate grid.
function cpr(chi, es) {
  return chi + es[12] * Sin(2 * chi) + es[13] * Sin(4 * chi)
             + es[14] * Sin(6 * chi) + es[15] * Sin(8 * chi);
}

// Snyder's t and m, used by the conic and oblique projections.
function tfn(phi, es) {
  return Tan(PI / 4 - phi / 2)
       / Pow((1 - es[1] * Sin(phi)) / (1 + es[1] * Sin(phi)), es[1] / 2);
}
function mfn(phi, es) {
  return Cos(phi) / Sqrt(1 - es[0] * Pow(Sin(phi), 2));
}

// ---------------------------------------------------------------------------
//  7. INVERSE TRANSVERSE MERCATOR  (State Plane TM zones, and all UTM)
//
//  zr = [type, latOrigin(deg), lonOrigin(deg), k0, unused, fe(m), fn(m), unused]
//
//  The series is flat to about 3.5 degrees from the central meridian and degrades
//  beyond: roughly 0.1 mm at 4 degrees, 1.4 mm at 6, 92 mm at 10. State Plane TM
//  zones are about 2 degrees wide and UTM zones 6, so real data sits well inside.
//  Data stored OUTSIDE its own zone is where this quietly loses accuracy.
// ---------------------------------------------------------------------------
function iTM(xx, yy, zr, es) {
  var k0 = zr[3];
  var mu = (yy - zr[6] + k0 * ma(rd(zr[1]), es)) / (k0 * es[3]);
  var ph = fpr(mu, es);

  // qq is easting scaled by the radius of curvature in the prime vertical
  var qq = (xx - zr[5]) / (k0 * es[16] / Sqrt(1 - es[0] * Pow(Sin(ph), 2)));
  var q2 = qq * qq;
  var tn = Tan(ph);
  var t2 = tn * tn;
  var t4 = t2 * t2;
  var et = es[2] * Pow(Cos(ph), 2);

  var b2 = -0.5 * tn * (1 + et);                                        // latitude
  var b4 = -(1.0 / 12.0) * (5 + 3 * t2 + et * (1 - 9 * t2) - 4 * et * et);
  var b6 = (1.0 / 360.0) * (61 + 90 * t2 + 45 * t4 + et * (46 - 252 * t2 - 90 * t4));
  var b3 = -(1.0 / 6.0) * (1 + 2 * t2 + et);                            // longitude
  var b5 = (1.0 / 120.0) * (5 + 28 * t2 + 24 * t4 + et * (6 + 8 * t2));
  var b7 = -(1.0 / 5040.0) * (61 + 662 * t2 + 1320 * t4 + 720 * t2 * t4);

  var ph2 = ph + b2 * q2 * (1 + q2 * (b4 + b6 * q2));
  var lm = rd(zr[2]) + qq * (1 + q2 * (b3 + q2 * (b5 + b7 * q2))) / Cos(ph);
  return [dg(ph2), dg(lm)];
}

// ---------------------------------------------------------------------------
//  8. INVERSE LAMBERT CONFORMAL CONIC (2SP)
//
//  zr = [type, latOrigin(deg), lonOrigin(deg), sp1(deg), sp2(deg), fe(m), fn(m), -]
//
//  Exact in longitude -- no series -- so unlike TM the error does not grow with
//  distance from the central meridian.
//
//  Atan2 is used rather than Atan(dx/dy): the plain form returns the wrong quadrant
//  and produced errors over 1,000 km in Texas Central during testing. The sign of
//  the cone constant is carried through both the radius and the angle.
//
//  Log appears only as a ratio of logs inside nn, so its base cancels.
// ---------------------------------------------------------------------------
function iLC(xx, yy, zr, es) {
  var s1 = rd(zr[3]);
  var s2 = rd(zr[4]);
  var t1 = tfn(s1, es);
  var t2 = tfn(s2, es);

  var nn = 0;                         // cone constant
  if (Abs(s1 - s2) < 0.000000000001) {
    nn = Sin(s1);                     // tangent case: the parallels coincide
  } else {
    nn = (Log(mfn(s1, es)) - Log(mfn(s2, es))) / (Log(t1) - Log(t2));
  }
  var fk = mfn(s1, es) / (nn * Pow(t1, nn));
  var r0 = es[16] * fk * Pow(tfn(rd(zr[1]), es), nn);

  var dx = xx - zr[5];
  var dy = r0 - (yy - zr[6]);
  var sg = IIf(nn > 0, 1.0, -1.0);
  var tt = Pow(sg * Sqrt(dx * dx + dy * dy) / (es[16] * fk), 1.0 / nn);

  return [dg(cpr(PI / 2 - 2 * Atan(tt), es)),
          dg(rd(zr[2]) + Atan2(sg * dx, sg * dy) / nn)];
}

// ---------------------------------------------------------------------------
//  9. INVERSE HOTINE OBLIQUE MERCATOR
//
//  zr = [type, latCenter(deg), lonCenter(deg), azimuth(deg), k0, fe(m), fn(m),
//        rectifiedGridAngle(deg)]
//
//  Esri's "Azimuth Natural Origin" variant. In US State Plane this is Alaska zone 1
//  and nothing else.
// ---------------------------------------------------------------------------
function iHO(xx, yy, zr, es) {
  var e2 = es[0];
  var pc = rd(zr[1]);
  var kc = zr[4];
  var sn = Sin(pc);

  var bb = Sqrt(1 + e2 * Pow(Cos(pc), 4) / (1 - e2));
  var ab = es[16] * bb * kc * Sqrt(1 - e2) / (1 - e2 * sn * sn);
  var dd = bb * Sqrt(1 - e2) / (Cos(pc) * Sqrt(1 - e2 * sn * sn));
  var fk = dd + Sqrt(Max(dd * dd, 1.0) - 1) * IIf(pc >= 0, 1.0, -1.0);
  var hh = fk * Pow(tfn(pc, es), bb);
  var gg = (fk - 1 / fk) / 2;
  var ga = Asin(Sin(rd(zr[3])) / dd);
  var lc = rd(zr[2]) - Asin(gg * Tan(ga)) / bb;
  var rg = rd(zr[7]);

  var de = xx - zr[5];
  var dn = yy - zr[6];
  var vv = de * Cos(rg) - dn * Sin(rg);
  var uu = dn * Cos(rg) + de * Sin(rg);

  var qq = Exp(-(bb * vv) / ab);
  var ss = (qq - 1 / qq) / 2;         // sinh
  var tt = (qq + 1 / qq) / 2;         // cosh
  var vs = Sin(bb * uu / ab);
  var us = (vs * Cos(ga) + ss * Sin(ga)) / tt;
  var tp = Pow(hh / Sqrt((1 + us) / (1 - us)), 1.0 / bb);

  return [dg(cpr(PI / 2 - 2 * Atan(tp), es)),
          dg(lc - Atan2(ss * Cos(ga) - vs * Sin(ga), Cos(bb * uu / ab)) / bb)];
}

// ---------------------------------------------------------------------------
//  10. MAIN
// ---------------------------------------------------------------------------
var gm = Geometry($feature);
if (IsEmpty(gm)) { return bad("No geometry."); }

var ky = Text(gm.spatialReference.wkid);
var wn = Number(ky);

// Any geometry type. A non-point feature reports its centroid, which for a concave
// or donut polygon can fall OUTSIDE the polygon -- Arcade has no guaranteed-inside
// point. On a real 47,630-parcel county layer this affected 0.94% of parcels, one
// of them by 4.7 km.
var ct = Centroid(gm);

var ll = [0, 0];

if (Includes(GW, wn)) {
  ll = [ct.Y, ct.X];                  // already degrees
} else {
  var pk = -1;
  for (var i = 0; i < Count(RN); i++) {
    var rr = RN[i];
    var dd = wn - rr[0];
    if (dd >= 0 && dd <= rr[3] * (rr[1] - 1) && dd % rr[3] == 0) {
      pk = rr[2] + (dd / rr[3]) * rr[4];
      break;
    }
  }
  if (pk < 0) {
    return bad("WKID " + ky + " is not a supported coordinate system for this build.");
  }

  var zi = Floor(pk / @@STRIDE@@);
  var es = EL[@@ELL_SELECT@@];
  var um = UT[pk - Floor(pk / @@UNIT_MOD@@) * @@UNIT_MOD@@];

  // expand the stored row: arcseconds -> degrees, indexes -> values
  var zc = ZN[zi];
  var zz = [zc[0], zc[1] / 3600, zc[2] / 3600, 0, 0, FE[zc[5]], FN[zc[6]], zc[7] / 3600];
  if (zc[0] == 0) {
    zz[3] = KS[zc[3]];
  } else if (zc[0] == 1) {
    zz[3] = zc[3] / 3600;
    zz[4] = zc[4] / 3600;
  } else {
    zz[3] = zc[3];                    // Hotine azimuth stays in degrees
    zz[4] = KS[zc[4]];
    zz[7] = zc[7];
  }

  var xm = ct.X * um;
  var ym = ct.Y * um;

  if (zz[0] == 0) { ll = iTM(xm, ym, zz, es); }
  else if (zz[0] == 1) { ll = iLC(xm, ym, zz, es); }
  else { ll = iHO(xm, ym, zz, es); }
}

// Nine decimals of a degree is about 0.11 mm -- below a geodatabase's own coordinate
// grid, so nothing real is lost here.
var la = Round(ll[0], 9);

// UTM zones 1 and 60, and State Plane Alaska 10, solve to longitudes outside +/-180
// and must be wrapped before any range check.
var lr = ll[1];
if (lr > 180) { lr = lr - 360; }
if (lr < -180) { lr = lr + 360; }
var lo = Round(lr, 9);

if (IsNan(la) || IsNan(lo) || Abs(la) > 90 || Abs(lo) > 180) {
  return bad("Inverse projection failed for WKID " + ky + ".");
}

if (MD == "LAT") { return la; }
if (MD == "LON") { return lo; }
if (MD == "BOTH") { return "Lat: " + Text(la, FMT) + ", Lon: " + Text(lo, FMT); }
return {"result": {"attributes": Dictionary(LF, la, NF, lo)}};
'''
