"""Arcade-specific static checks that a JavaScript harness cannot catch."""
import os
import re
import sys
import collections

ARCADE_BUILTINS = """Abs Acos Angle Area AreaGeodetic Asin Atan Atan2 Attachments Average
Bearing Boolean Buffer BufferGeodetic Ceil Centroid Clip Concatenate Console Constrain
Contains Cos Count Crosses Cut Date DateAdd DateDiff DateOnly Datetime DefaultValue
Densify DensifyGeodetic Dictionary Difference Disjoint Distance DistanceGeodetic
Distinct Domain DomainCode DomainName Equals Exp Expects Extent Feature FeatureSet
FeatureSetByAssociation FeatureSetById FeatureSetByName FeatureSetByPortalItem
FeatureSetByRelationshipName Filter Find First Floor FromCharCode FromCodePoint
FromJSON Generalize Geometry GetFeatureSet GetUser GroupBy Guid HasKey HasValue Hash
Hour IIf ISOMonth ISOWeek ISOWeekday ISOYear Includes Indexof Insert Intersection
Intersects IsEmpty IsNan IsSelfIntersecting IsSimple Left Length Length3D LengthGeodetic
Log Max Mid Millisecond Min Minute Month MultiPartToSinglePart Multipoint NextSequenceValue
Now Number Offset OrderBy Overlaps PI Point Polygon Polyline Pop Portal Pow Proper Push
Random Reduce Relate Remove Replace Resize Reverse Right Round Schema Second Sequence
SetGeometry Sin Slice Sort Splice Split Sqrt Standardize Stdev Sum Symmetricdifference
Tan Text TextFormatting Time TimeZone TimeZoneOffset Timestamp ToCharCode ToCodePoint
ToHex ToLocal ToUTC Today Top Touches TrackCurrentTime TrackFieldWindow TrackGeometryWindow
TrackIndex TrackStartTime TrackWindow Trim TypeOf Union Upper Variance Week Weekday
When Within Year console decode encode lower proper trim upper""".split()
BUILTIN_LC = {b.lower() for b in ARCADE_BUILTINS}
RESERVED = {"var", "if", "else", "for", "while", "return", "function", "break",
            "continue", "true", "false", "null", "in", "new", "typeof"}

def strip(src):
    """Remove // comments and string literals so identifiers are not matched inside them."""
    out = []
    for ln in src.splitlines():
        i, q, res = 0, None, []
        while i < len(ln):
            c = ln[i]
            if q:
                if c == q:
                    q = None
                res.append(" ")
            elif c in "\"'":
                q = c
                res.append(" ")
            elif c == "/" and i + 1 < len(ln) and ln[i + 1] == "/":
                break
            else:
                res.append(c)
            i += 1
        out.append("".join(res))
    return "\n".join(out)

def check(path):
    raw = open(path, encoding="utf-8").read()
    code = strip(raw)
    print("=" * 74)
    print(os.path.basename(path), "  %d bytes, %d lines" % (len(raw), raw.count("\n") + 1))
    problems = 0

    # 1. non-ASCII anywhere
    nonascii = [(i + 1, ln) for i, ln in enumerate(raw.splitlines())
                if any(ord(ch) > 126 for ch in ln)]
    print("  non-ASCII characters: %d line(s)" % len(nonascii))
    for i, ln in nonascii[:5]:
        bad = "".join(sorted({ch for ch in ln if ord(ch) > 126}))
        print("      line %d: %r  in: %s" % (i, bad, ln.strip()[:70]))
    problems += len(nonascii)

    # 2. declared identifiers: case-insensitive collisions
    decls = collections.defaultdict(list)
    for m in re.finditer(r"\bvar\s+([A-Za-z_]\w*)", code):
        decls[m.group(1).lower()].append(m.group(1))
    for m in re.finditer(r"\bfunction\s+([A-Za-z_]\w*)\s*\(([^)]*)\)", code):
        decls[m.group(1).lower()].append(m.group(1))
        for a in m.group(2).split(","):
            a = a.strip()
            if a:
                decls[a.lower()].append(a)
    coll = {k: sorted(set(v)) for k, v in decls.items() if len(set(v)) > 1}
    print("  case-insensitive identifier collisions: %d" % len(coll))
    for k, v in list(coll.items())[:8]:
        print("      %s -> %s" % (k, v))
    problems += len(coll)

    # 3. identifiers shadowing an Arcade built-in
    shadow = sorted({v[0] for k, v in decls.items() if k in BUILTIN_LC})
    print("  identifiers shadowing an Arcade built-in: %d %s" % (len(shadow), shadow[:10]))
    problems += len(shadow)

    # 4. reserved words as identifiers
    resv = sorted({v[0] for k, v in decls.items() if k in RESERVED})
    print("  reserved words used as identifiers: %d %s" % (len(resv), resv))
    problems += len(resv)

    # 5. multi-declarator var  (comma at paren/bracket depth 0 only)
    multi = []
    for m in re.finditer(r"var\s+[A-Za-z_]\w*\s*=", code):
        i, d = m.end(), 0
        while i < len(code) and code[i] not in ";\n":
            c = code[i]
            if c in "([{":
                d += 1
            elif c in ")]}":
                d -= 1
            elif c == "," and d == 0:
                multi.append(code[m.start():i + 10].replace("\n", " "))
                break
            i += 1
    print("  multi-declarator var statements: %d %s" % (len(multi), multi[:3]))
    problems += len(multi)

    # 6. functions called that are neither built-in nor locally defined
    local = {v[0] for v in decls.values()}
    local_lc = {x.lower() for x in local}
    called = {m.group(1) for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", code)}
    unknown = sorted(c for c in called
                     if c.lower() not in BUILTIN_LC and c.lower() not in local_lc
                     and c.lower() not in RESERVED)
    print("  calls to unknown functions: %d %s" % (len(unknown), unknown))
    problems += len(unknown)

    # 7. globals referenced
    used_globals = sorted({m.group(0) for m in re.finditer(r"\$\w+", code)})
    print("  profile variables referenced: %s" % used_globals)

    # 8. ES features Arcade does not support
    for pat, label in [(r"=>", "arrow function"), (r"\blet\b", "let"), (r"\bconst\b", "const"),
                       (r"`", "template literal"),   # note: ++ IS supported (probed)
                       (r"\btry\b", "try/catch"), (r"===|!==", "strict equality"),
                       (r"\.\w+\s*=\s*[^=]", "property assignment")]:
        hits = len(re.findall(pat, code))
        if hits:
            print("  UNSUPPORTED-IN-ARCADE construct %-22s: %d" % (label, hits))
            problems += hits
    print("  --> %d issue(s)" % problems)
    return problems

total = 0
for p in sys.argv[1:]:
    total += check(p)
print("\nTOTAL ISSUES ACROSS BUILDS:", total)
