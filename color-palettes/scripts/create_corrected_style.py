"""
Create a small standalone .stylx file containing only the corrected
Sahara Sand and Topaz Sand colors, suitable for adding to ArcGIS Pro
alongside the bundled ArcGIS Colors style.

The corrected colors are renamed (e.g. 'Sahara Sand (HSV-corrected)') so they
don't collide with the originals when both styles are loaded.

USAGE:
    python create_corrected_style.py [output-path]

DEFAULT OUTPUT:
    ArcGIS Colors HSV-Corrected.stylx (in current directory)

APPROACH:
    Build a new .stylx from a copied Esri template and keep only two corrected
    color records. The script supports both legacy ITEMS schemas and current
    ArcGIS Pro DATA schemas.

    If you don't want to copy an Esri file as a template, you can instead build
    the SQLite schema yourself — see the SCHEMA_FALLBACK section near the
    bottom of this file for that approach.

NOTE: This script has not been tested against a live ArcGIS Pro install. Run it,
verify in Pro that the corrected colors appear correctly in the Catalog Styles
pane, and adjust if needed. The CIMColor JSON structure is the part most likely
to need adjustment if Esri changes their internal format.
"""

import sqlite3
import json
import sys
import shutil
from pathlib import Path

DEFAULT_TEMPLATE_PATH = r"C:\Program Files\ArcGIS\Pro\Resources\Styles\Styles.stylx"

# The two corrected colors to ship in our standalone style
CORRECTED_COLORS = [
    {
        "name": "Sahara Sand (HSV-corrected)",
        "rgb": (255, 212, 190),
        "tags": "Esri palette correction;Sahara Sand;HSV-aligned",
    },
    {
        "name": "Topaz Sand (HSV-corrected)",
        "rgb": (255, 233, 190),
        "tags": "Esri palette correction;Topaz Sand;HSV-aligned",
    },
]

STYLE_NAME = "ArcGIS Colors HSV-Corrected"
STYLE_SUMMARY = (
    "Two corrected pastel colors (Sahara Sand and Topaz Sand) derived from HSV/CMYK "
    "pattern analysis of the Esri ArcGIS Colors palette. Add this style to ArcGIS Pro "
    "alongside the standard ArcGIS Colors style. The corrected colors appear with the "
    "'(HSV-corrected)' suffix and do not replace the originals."
)


def make_cim_color_json(r, g, b):
    """Build a CIMRGBColor JSON content blob matching Esri's structure."""
    return json.dumps({
        "type": "CIMRGBColor",
        "values": [int(r), int(g), int(b), 100]
    }, separators=(",", ":"))


def get_tables(cur):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return {r[0] for r in cur.fetchall()}


def detect_style_schema(cur, tables):
    if "ITEMS" in tables:
        cur.execute("PRAGMA table_info(ITEMS)")
        item_cols = [r[1] for r in cur.fetchall()]
        if all(c in item_cols for c in ("NAME", "CLASS", "CONTENT")):
            return "ITEMS", item_cols

    if "DATA" in tables:
        cur.execute("PRAGMA table_info(DATA)")
        data_cols = [r[1] for r in cur.fetchall()]
        if all(c in data_cols for c in ("KEY", "CONTENT")):
            return "DATA", data_cols

    return None, []


def write_items_schema(cur, tables, item_cols):
    cur.execute("DELETE FROM ITEMS")

    for t in ("CATEGORIES", "TAGS", "GROUPS", "FAVORITES"):
        if t in tables:
            cur.execute(f"DELETE FROM {t}")

    for entry in CORRECTED_COLORS:
        r, g, b = entry["rgb"]
        content = make_cim_color_json(r, g, b)

        col_values = {}
        if "CLASS" in item_cols:
            col_values["CLASS"] = "CIMColor"
        if "CATEGORY" in item_cols:
            col_values["CATEGORY"] = "Color"
        if "NAME" in item_cols:
            col_values["NAME"] = entry["name"]
        if "TAGS" in item_cols:
            col_values["TAGS"] = entry["tags"]
        if "CONTENT" in item_cols:
            col_values["CONTENT"] = content
        if "KEY" in item_cols:
            col_values["KEY"] = f"{entry['name']}_Default_1"

        cols = ", ".join(col_values.keys())
        placeholders = ", ".join(["?"] * len(col_values))
        sql = f"INSERT INTO ITEMS ({cols}) VALUES ({placeholders})"
        cur.execute(sql, list(col_values.values()))
        print(f"  Inserted: {entry['name']} -> RGB({r}, {g}, {b})")


def write_data_schema(cur, tables, data_cols):
    cur.execute("DELETE FROM DATA")
    if "STYLE_ITEM_BINARY_REFERENCES" in tables:
        cur.execute("DELETE FROM STYLE_ITEM_BINARY_REFERENCES")
    if "BINARIES" in tables:
        cur.execute("DELETE FROM BINARIES")

    for entry in CORRECTED_COLORS:
        r, g, b = entry["rgb"]
        key = f"{entry['name']}_Default_1"
        payload = (make_cim_color_json(r, g, b) + "\x00").encode("utf-8")
        size = len(payload)

        col_values = {}
        if "KEY" in data_cols:
            col_values["KEY"] = key
        if "CONTENT" in data_cols:
            col_values["CONTENT"] = payload
        if "SIZE" in data_cols:
            col_values["SIZE"] = size

        cols = ", ".join(col_values.keys())
        placeholders = ", ".join(["?"] * len(col_values))
        sql = f"INSERT INTO DATA ({cols}) VALUES ({placeholders})"
        cur.execute(sql, list(col_values.values()))
        print(f"  Inserted: {entry['name']} -> RGB({r}, {g}, {b})")


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ArcGIS Colors HSV-Corrected.stylx")
    template = Path(DEFAULT_TEMPLATE_PATH)

    if not template.exists():
        print(f"ERROR: template not found: {template}")
        print("Pass the path to a working .stylx file as the first argument,")
        print("or edit DEFAULT_TEMPLATE_PATH in this script.")
        sys.exit(1)

    if out_path.exists():
        print(f"WARNING: {out_path} already exists. Overwriting.")
        out_path.unlink()

    # Copy template, then clear it and add only our records
    shutil.copy(template, out_path)
    print(f"Copied template ({template.name}) to: {out_path}")

    conn = sqlite3.connect(str(out_path))
    cur = conn.cursor()

    # Inspect what tables exist (for safety)
    tables = get_tables(cur)
    print(f"Tables in template: {sorted(tables)}")

    schema, schema_cols = detect_style_schema(cur, tables)
    if not schema:
        print("ERROR: template is not a recognized .stylx schema (ITEMS or DATA)")
        sys.exit(1)

    print(f"Detected schema: {schema}")

    if schema == "ITEMS":
        print(f"ITEMS columns: {schema_cols}")
        write_items_schema(cur, tables, schema_cols)
    else:
        print(f"DATA columns: {schema_cols}")
        write_data_schema(cur, tables, schema_cols)

    # Update style metadata if PROPERTIES table exists (legacy schema).
    if "PROPERTIES" in tables:
        cur.execute("PRAGMA table_info(PROPERTIES)")
        prop_cols = [r[1] for r in cur.fetchall()]
        if "NAME" in prop_cols and "VALUE" in prop_cols:
            cur.execute("DELETE FROM PROPERTIES")
            cur.execute("INSERT INTO PROPERTIES (NAME, VALUE) VALUES (?, ?)",
                        ("NAME", STYLE_NAME))
            cur.execute("INSERT INTO PROPERTIES (NAME, VALUE) VALUES (?, ?)",
                        ("SUMMARY", STYLE_SUMMARY))
            cur.execute("INSERT INTO PROPERTIES (NAME, VALUE) VALUES (?, ?)",
                        ("TAGS", "Esri;ArcGIS Colors;HSV;palette;corrections"))
            print(f"Set style metadata: NAME='{STYLE_NAME}'")

    # DATA-schema styles often only have a small immutable meta table, so we skip
    # renaming there and rely on filename/display path when adding the style in Pro.

    conn.commit()
    conn.execute("VACUUM")
    conn.close()

    print(f"\nDone. Standalone style saved to:\n  {out_path}\n")
    print("To add to ArcGIS Pro:")
    print("  1. Catalog pane -> Styles -> Add -> Add Style")
    print(f"  2. Browse to: {out_path}")
    print("  3. The corrected colors appear with '(HSV-corrected)' suffix")
    print("     and do not replace the original Esri values.")


if __name__ == "__main__":
    main()


# =============================================================================
# SCHEMA_FALLBACK
# =============================================================================
# If you'd rather build the .stylx from scratch instead of copying an Esri file
# as a template, here's the minimum schema you need. This is based on observed
# .stylx files from ArcGIS Pro 3.x and may need adjustment for other versions.
#
# CREATE TABLE ITEMS (
#     ID TEXT PRIMARY KEY,
#     CLASS TEXT NOT NULL,
#     CATEGORY TEXT,
#     NAME TEXT,
#     TAGS TEXT,
#     CONTENT TEXT,
#     KEY TEXT,
#     ITEMTYPE INTEGER
# );
# CREATE TABLE PROPERTIES (
#     NAME TEXT PRIMARY KEY,
#     VALUE TEXT
# );
#
# Insert the same CIMColor records as above. The minimum viable .stylx
# probably needs at least an ITEMS table; PROPERTIES is recommended for
# clean naming in Pro's Styles pane.
