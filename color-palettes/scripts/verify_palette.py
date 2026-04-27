"""
Verify the 120-color Esri palette against the live ArcGIS Pro 3.6 bundled style file.

For each color in our reference CSV, query the live Styles.stylx and compare RGB values.
Reports matches, mismatches, and any colors not found.

USAGE:
    python verify_palette.py [path-to-styles-stylx] [--reference-csv path]

DEFAULT PATH:
    C:\\Program Files\\ArcGIS\\Pro\\Resources\\Styles\\Styles.stylx

OUTPUT:
    - Console summary
    - CSV report (full per-color results)
    - JSON report (summary + mismatches + missing)

NOTE: The CIMColor records in Styles.stylx contain JSON like:
    {"type": "CIMRGBColor", "values": [R, G, B, alpha]}
This script reads that structure and compares against the published reference.
"""

import sqlite3
import json
import sys
import csv
import zlib
import argparse
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = r"C:\Program Files\ArcGIS\Pro\Resources\Styles\Styles.stylx"

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REFERENCE_CSV = SCRIPT_DIR.parent / "arcgis-pro-standard-palette" / "palette.csv"
DEFAULT_OUTPUT_CSV = SCRIPT_DIR / "palette_verification.csv"
DEFAULT_OUTPUT_JSON = SCRIPT_DIR / "palette_verification.json"


def load_reference_colors(csv_path):
    """Load reference color rows from palette.csv as (name, r, g, b)."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Reference CSV not found: {csv_path}")

    reference = []
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"name", "r", "g", "b"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(
                f"Reference CSV missing required columns {sorted(required)}. "
                f"Found: {reader.fieldnames}"
            )

        for row_num, row in enumerate(reader, start=2):
            try:
                name = row["name"].strip()
                r = int(row["r"])
                g = int(row["g"])
                b = int(row["b"])
            except Exception as ex:
                raise ValueError(f"Invalid reference row {row_num}: {row}") from ex

            if not name:
                raise ValueError(f"Invalid reference row {row_num}: empty name")

            reference.append((name, r, g, b))

    if not reference:
        raise ValueError(f"Reference CSV has no data rows: {csv_path}")

    return reference

def extract_rgb(content_json):
    """Extract RGB values from a CIMColor JSON content blob.

    Returns (r, g, b) as ints, or None if the structure isn't recognized.
    """
    candidates = []

    if isinstance(content_json, (bytes, bytearray)):
        raw = bytes(content_json)
        candidates.append(raw)
        # Some entries are zlib-compressed JSON blobs.
        try:
            candidates.append(zlib.decompress(raw))
        except zlib.error:
            pass
    elif isinstance(content_json, str):
        candidates.append(content_json.encode("utf-8", errors="ignore"))

    for candidate in candidates:
        try:
            text = candidate.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue

        # DATA.CONTENT may be null-terminated JSON.
        text = text.split("\x00", 1)[0].strip()
        if not text:
            continue

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue

        # CIMRGBColor has values: [R, G, B, alpha]
        if data.get("type") == "CIMRGBColor" and "values" in data:
            vals = data["values"]
            if len(vals) >= 3:
                return (int(round(vals[0])), int(round(vals[1])), int(round(vals[2])))

    # Other color types (CIMHSVColor, CIMCMYKColor, etc.) — would need conversion
    return None


def detect_schema(cur):
    """Detect whether this style file uses ITEMS (legacy) or DATA (current)."""
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]

    if "ITEMS" in tables:
        cur.execute("PRAGMA table_info(ITEMS)")
        cols = [r[1] for r in cur.fetchall()]
        if all(c in cols for c in ("NAME", "CLASS", "CONTENT")):
            return "ITEMS", tables

    if "DATA" in tables:
        cur.execute("PRAGMA table_info(DATA)")
        cols = [r[1] for r in cur.fetchall()]
        if all(c in cols for c in ("KEY", "CONTENT")):
            return "DATA", tables

    return None, tables


def fetch_color_contents(cur, schema, color_name):
    """Fetch candidate color content blobs for a given palette color name."""
    if schema == "ITEMS":
        cur.execute(
            "SELECT CONTENT FROM ITEMS WHERE CLASS = 'CIMColor' AND NAME = ?",
            (color_name,),
        )
        return [row[0] for row in cur.fetchall()]

    if schema == "DATA":
        # ArcGIS Pro 3.6+ format uses keys like: "Mars Red_Default_1".
        default_key = f"{color_name}_Default_1"
        cur.execute("SELECT CONTENT FROM DATA WHERE KEY = ?", (default_key,))
        rows = [row[0] for row in cur.fetchall()]
        if rows:
            return rows

        # Fallback for variant suffixes without exposing LIKE wildcard issues.
        cur.execute("SELECT CONTENT FROM DATA WHERE KEY GLOB ?", (f"{color_name}_*",))
        return [row[0] for row in cur.fetchall()]

    return []


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Verify Esri palette colors against a .stylx file")
    parser.add_argument(
        "stylx_path",
        nargs="?",
        default=DEFAULT_PATH,
        help="Path to Styles.stylx (default: ArcGIS Pro bundled style)",
    )
    parser.add_argument(
        "--reference-csv",
        default=str(DEFAULT_REFERENCE_CSV),
        help="Path to reference palette CSV (default: repo palette.csv)",
    )
    parser.add_argument(
        "--output-csv",
        default=str(DEFAULT_OUTPUT_CSV),
        help="Path for per-color CSV output",
    )
    parser.add_argument(
        "--output-json",
        default=str(DEFAULT_OUTPUT_JSON),
        help="Path for JSON summary output",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    stylx_path = Path(args.stylx_path)
    reference_csv = Path(args.reference_csv)
    out_csv = Path(args.output_csv)
    out_json = Path(args.output_json)

    try:
        reference_colors = load_reference_colors(reference_csv)
    except Exception as ex:
        print(f"ERROR: {ex}")
        sys.exit(1)

    if not stylx_path.exists():
        print(f"ERROR: file not found: {stylx_path}")
        print("Pass the path to your Styles.stylx as the first argument.")
        sys.exit(1)

    print(f"Reading: {stylx_path}\n")
    print(f"Reference CSV: {reference_csv}\n")

    conn = sqlite3.connect(str(stylx_path))
    cur = conn.cursor()

    # First sanity check: see what tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Tables in file: {', '.join(tables)}\n")

    schema, _ = detect_schema(cur)
    if not schema:
        print("ERROR: could not find a supported style schema.")
        print("Expected either ITEMS(NAME, CLASS, CONTENT) or DATA(KEY, CONTENT).")
        sys.exit(1)

    print(f"Detected schema: {schema}\n")

    # For each reference color, look it up and compare
    results = []
    n_matches = 0
    n_mismatches = 0
    n_missing = 0
    n_multiple = 0

    for ref_name, ref_r, ref_g, ref_b in reference_colors:
        rows = fetch_color_contents(cur, schema, ref_name)

        if not rows:
            results.append({
                "name": ref_name, "ref": (ref_r, ref_g, ref_b),
                "actual": None, "status": "NOT_FOUND"
            })
            n_missing += 1
            continue

        # Use the first row; flag if there are multiple
        actual_rgbs = [extract_rgb(row) for row in rows]
        actual_rgbs = [a for a in actual_rgbs if a is not None]
        if not actual_rgbs:
            results.append({
                "name": ref_name, "ref": (ref_r, ref_g, ref_b),
                "actual": None, "status": "UNREADABLE"
            })
            n_missing += 1
            continue

        actual = actual_rgbs[0]
        multi = len(rows) > 1
        if multi:
            n_multiple += 1

        if actual == (ref_r, ref_g, ref_b):
            results.append({
                "name": ref_name, "ref": (ref_r, ref_g, ref_b),
                "actual": actual,
                "status": "MATCH" + (" (multiple records)" if multi else "")
            })
            n_matches += 1
        else:
            results.append({
                "name": ref_name, "ref": (ref_r, ref_g, ref_b),
                "actual": actual,
                "status": "MISMATCH" + (" (multiple records)" if multi else "")
            })
            n_mismatches += 1

    conn.close()

    # Print summary
    print("=" * 78)
    print("VERIFICATION SUMMARY")
    print("=" * 78)
    print(f"Total reference colors:  {len(reference_colors)}")
    print(f"Matches:                 {n_matches}")
    print(f"Mismatches:              {n_mismatches}")
    print(f"Not found:               {n_missing}")
    print(f"Names with multiple records (any class match): {n_multiple}")
    print()

    if n_mismatches:
        print("MISMATCHES:")
        print("-" * 78)
        for r in results:
            if r["status"].startswith("MISMATCH"):
                rr, rg, rb = r["ref"]
                ar, ag, ab = r["actual"]
                print(f"  {r['name']:<22}  reference RGB({rr:>3},{rg:>3},{rb:>3})  "
                      f"vs live RGB({ar:>3},{ag:>3},{ab:>3})  {r['status']}")
        print()

    if n_missing:
        print("NOT FOUND:")
        print("-" * 78)
        for r in results:
            if r["status"] in ("NOT_FOUND", "UNREADABLE"):
                print(f"  {r['name']:<22}  {r['status']}")
        print()

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "ref_r", "ref_g", "ref_b", "actual_r", "actual_g", "actual_b", "status"])
        for r in results:
            rr, rg, rb = r["ref"]
            if r["actual"]:
                ar, ag, ab = r["actual"]
                w.writerow([r["name"], rr, rg, rb, ar, ag, ab, r["status"]])
            else:
                w.writerow([r["name"], rr, rg, rb, "", "", "", r["status"]])

    mismatches = [r for r in results if r["status"].startswith("MISMATCH")]
    missing = [r for r in results if r["status"] in ("NOT_FOUND", "UNREADABLE")]

    report_json = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stylx_path": str(stylx_path.resolve()),
        "reference_csv": str(reference_csv.resolve()),
        "schema": schema,
        "summary": {
            "total_reference_colors": len(reference_colors),
            "matches": n_matches,
            "mismatches": n_mismatches,
            "not_found": n_missing,
            "multiple_records": n_multiple,
        },
        "mismatches": [
            {
                "name": r["name"],
                "reference": {"r": r["ref"][0], "g": r["ref"][1], "b": r["ref"][2]},
                "actual": {"r": r["actual"][0], "g": r["actual"][1], "b": r["actual"][2]},
                "status": r["status"],
            }
            for r in mismatches
        ],
        "missing_or_unreadable": [
            {
                "name": r["name"],
                "reference": {"r": r["ref"][0], "g": r["ref"][1], "b": r["ref"][2]},
                "status": r["status"],
            }
            for r in missing
        ],
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    print(f"Full CSV results:  {out_csv.resolve()}")
    print(f"JSON summary:      {out_json.resolve()}")


if __name__ == "__main__":
    main()
