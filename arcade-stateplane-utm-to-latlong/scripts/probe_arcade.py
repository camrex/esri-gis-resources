"""Probe what the REAL Arcade engine accepts, via arcpy CalculateField (ARCADE)."""
import os
# Requires ArcGIS Pro's Python -- arcpy cannot be pip-installed.
import arcpy  # pyright: ignore[reportMissingImports]

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "_scratch")
GDB = os.path.join(WS, "probe.gdb")
os.makedirs(WS, exist_ok=True)
if arcpy.Exists(GDB):
    arcpy.management.Delete(GDB)
arcpy.management.CreateFileGDB(WS, "probe.gdb")
sr = arcpy.SpatialReference(6455)          # Illinois East ftUS
fc = os.path.join(GDB, "pts")
arcpy.management.CreateFeatureclass(GDB, "pts", "POINT", spatial_reference=sr)
arcpy.management.AddField(fc, "V", "DOUBLE")
arcpy.management.AddField(fc, "S", "TEXT", field_length=120)
with arcpy.da.InsertCursor(fc, ["SHAPE@XY"]) as ic:
    ic.insertRow([(764723.8484, 302547.2518)])

CHECKS = [
    ("Sqrt",        'return Sqrt(2);'),
    ("Pow",         'return Pow(2,10);'),
    ("Exp",         'return Exp(1);'),
    ("Log natural", 'return Log(Exp(1));'),
    ("Log(100)",    'return Log(100);'),
    ("Atan2",       'return Atan2(1,-1);'),
    ("Asin",        'return Asin(0.5);'),
    ("Abs/Floor",   'return Abs(-3)+Floor(3.7);'),
    ("Round 2-arg", 'return Round(1.23456789012,9);'),
    ("Max varargs", 'return Max(3,7);'),
    ("Max array",   'return Max([3,7]);'),
    ("Includes",    'return IIf(Includes([1,2,3],2),1,0);'),
    ("Count(array)",'return Count([[1,2],[3,4]]);'),
    ("array .length",'var a=[1,2,3]; return a.length;'),
    ("Push in loop",'var a=[]; for(var i=0;i<5;i++){Push(a,i);} return a[4];'),
    ("modulo %",    'return 7 % 3;'),
    ("break",       'var t=0; for(var i=0;i<9;i++){ if(i==3){break;} t=t+i; } return t;'),
    ("Centroid",    'return Centroid(Geometry($feature)).X;'),
    ("Min varargs", 'return Min(3,7);'),
    ("IIf",         'return IIf(1>0,1,2);'),
    ("IsNan",       'return IIf(IsNan(Sqrt(-1)),1,0);'),
    ("PI",          'return PI;'),
    ("geom X",      'return Geometry($feature).X;'),
    ("geom wkid",   'return Geometry($feature).spatialReference.wkid;'),
    ("IsEmpty geom",'return IIf(IsEmpty(Geometry($feature)),1,0);'),
    ("multi-decl var", 'var a=1, b=2; return a+b;'),
    ("case-insens",  'var Foo=5; return foo;'),
    ("dict+haskey", 'var d=Dictionary("a",1); return IIf(HasKey(d,"a"),d["a"],0);'),
    ("dict num key",'var d={"6455":7}; return d["6455"];'),
]
print("%-16s %-8s %s" % ("feature", "status", "value / error"))
for name, expr in CHECKS:
    try:
        arcpy.management.CalculateField(fc, "V", expr, "ARCADE")
        v = next(iter(arcpy.da.SearchCursor(fc, ["V"])))[0]
        print("%-16s %-8s %r" % (name, "OK", v))
    except Exception as e:
        msg = str(e).replace("\n", " ")[:110]
        print("%-16s %-8s %s" % (name, "FAIL", msg))

STR = [("Text fmt", 'return Text(1.5,"#.######");'), ("Text int", 'return Text(6455);')]
for name, expr in STR:
    try:
        arcpy.management.CalculateField(fc, "S", expr, "ARCADE")
        v = next(iter(arcpy.da.SearchCursor(fc, ["S"])))[0]
        print("%-16s %-8s %r" % (name, "OK", v))
    except Exception as e:
        print("%-16s %-8s %s" % (name, "FAIL", str(e).replace("\n", " ")[:110]))
