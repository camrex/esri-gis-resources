"""Does ArcGIS shift NAD83-family coordinates when asked for WGS 84 (4326)?

An inverse projection does not change datum: the expression returns geodetic
coordinates on the SOURCE datum, and anything consuming them as WGS 84 inherits
whatever offset ArcGIS would have applied. This measures that offset both ways --
under ArcGIS's default (a null transformation) and under an explicit one.
"""
import math, arcpy
WGS84 = arcpy.SpatialReference(4326)
PTS = [("Chicago", 41.8781, -87.6298), ("Springfield IL", 39.7817, -89.6501),
       ("Denver", 39.7392, -104.9903), ("Los Angeles", 34.0522, -118.2437),
       ("Miami", 25.7617, -80.1918), ("Honolulu", 21.3069, -157.8583)]
GCS = [("NAD83", 4269), ("NAD83(HARN)", 4152), ("NAD83(2011)", 6318)]
A = 6378137.0; f = 1/298.257222101; e2 = 2*f - f*f
def m(la1, lo1, la2, lo2):
    ph = math.radians(la1); s = math.sin(ph); w = 1-e2*s*s
    M = A*(1-e2)/w**1.5; N = A/math.sqrt(w)
    return math.hypot(math.radians(lo2-lo1)*N*math.cos(ph), math.radians(la2-la1)*M)
print("%-16s %-14s %14s   %s" % ("point", "source GCS", "shift to 4326", "transformation ArcGIS offers"))
for gname, gw in GCS:
    src = arcpy.SpatialReference(gw)
    tfs = arcpy.ListTransformations(src, WGS84)
    worst = 0.0
    for name, la, lo in PTS:
        g = arcpy.PointGeometry(arcpy.Point(lo, la), src).projectAs(WGS84).getPart(0)
        worst = max(worst, m(la, lo, g.Y, g.X))
    print("%-16s %-14s %11.4f m   %s" % ("(%d pts)" % len(PTS), gname, worst,
                                          (tfs[:2] if tfs else "none -> treated as equivalent")))


print()
print("If a downstream consumer applies an EXPLICIT NAD83->WGS84 transformation instead")
print("of the default null one, the same coordinate moves by:")
src = arcpy.SpatialReference(4269)
for tf in ("WGS_1984_(ITRF00)_To_NAD_1983", "NAD_1983_To_WGS_1984_5"):
    worst = 0.0
    for name, la, lo in PTS:
        try:
            g = arcpy.PointGeometry(arcpy.Point(lo, la), src).projectAs(WGS84, tf).getPart(0)
        except Exception:
            continue
        worst = max(worst, m(la, lo, g.Y, g.X))
    print("   %-34s up to %.3f m" % (tf, worst))
