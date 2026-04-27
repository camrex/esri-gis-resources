"""
make_palette_pngs.py — generate the Esri ArcGIS Colors palette PNGs

Reads palette.csv (the canonical 120-color reference) and corrections.json
(the proposed-correction list) and writes:

    ArcGIS_Pro_Color_Palette.png             (full grid, all 120 colors)
    ArcGIS_Pro_Color_Palette_Corrections.png (full grid with diagonal-split swatches
                                              for the colors listed in corrections.json)

USAGE
-----
From the scripts/ folder:

    python make_palette_pngs.py                 # generate both PNGs
    python make_palette_pngs.py --standard      # only the full grid
    python make_palette_pngs.py --corrections   # only the corrections grid
    python make_palette_pngs.py --input-dir ../arcgis-pro-standard-palette --output-dir ../arcgis-pro-standard-palette
    python make_palette_pngs.py --help

By default the script reads from the canonical palette folder
(`../arcgis-pro-standard-palette` from `scripts/`) and writes PNGs there,
matching this layout:

    color-palettes/
    ├── arcgis-pro-standard-palette/
    │   ├── palette.csv
    │   ├── corrections.json
    │   ├── ArcGIS_Pro_Color_Palette.png             ← written here
    │   └── ArcGIS_Pro_Color_Palette_Corrections.png ← written here
    └── scripts/
        └── make_palette_pngs.py

PROGRAMMATIC USE
----------------
The render functions are also importable:

    from make_palette_pngs import render_standard_grid, render_corrections_grid

    palette = load_palette('palette.csv')
    corrections = load_corrections('corrections.json')
    render_standard_grid(palette, 'output.png')
    render_corrections_grid(palette, corrections, 'output_corrections.png')

REQUIREMENTS
------------
- Python 3.8+
- matplotlib
- (csv, json, colorsys, argparse from stdlib)
"""

from __future__ import annotations

import argparse
import colorsys
import csv
import json
import sys
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle


# ---------------------------------------------------------------------------
# Default file locations (relative to this script's folder)
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = SCRIPT_DIR.parent / "arcgis-pro-standard-palette"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "arcgis-pro-standard-palette"

PALETTE_CSV_NAME = "palette.csv"
CORRECTIONS_JSON_NAME = "corrections.json"
STANDARD_PNG_NAME = "ArcGIS_Pro_Color_Palette.png"
CORRECTIONS_PNG_NAME = "ArcGIS_Pro_Color_Palette_Corrections.png"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_palette(csv_path: Path) -> list[dict]:
    """Load the 120-color palette from palette.csv.

    Expected columns: index, name, r, g, b, hex, h_deg, s_pct, v_pct,
    grid_row, grid_col, description
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"palette CSV not found: {csv_path}")

    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"name", "r", "g", "b", "hex", "grid_row", "grid_col", "description"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"palette CSV is missing required columns: {sorted(missing)}\n"
                f"found columns: {reader.fieldnames}"
            )
        for r in reader:
            rows.append({
                "name": r["name"],
                "r": int(r["r"]),
                "g": int(r["g"]),
                "b": int(r["b"]),
                "hex": r["hex"],
                "grid_row": int(r["grid_row"]),
                "grid_col": int(r["grid_col"]),
                "description": r["description"],
            })

    if len(rows) != 120:
        raise ValueError(
            f"expected 120 colors in palette CSV, got {len(rows)}. "
            "If this is intentional, edit the script's expectations."
        )
    return rows


def load_corrections(json_path: Path) -> list[dict]:
    """Load the proposed-correction list from corrections.json.

    Each entry has: name, corrected_rgb [r, g, b], corrected_hex.
    Missing or empty file returns an empty list (no corrections to render).
    """
    if not json_path.exists():
        return []
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{json_path} must contain a JSON array")
    for entry in data:
        if "name" not in entry or "corrected_rgb" not in entry:
            raise ValueError(
                f"correction entry missing required keys (name, corrected_rgb): {entry}"
            )
        rgb = entry["corrected_rgb"]
        if not (isinstance(rgb, list) and len(rgb) == 3):
            raise ValueError(f"corrected_rgb must be [r, g, b]: {entry}")
        # Auto-fill hex if not provided
        if "corrected_hex" not in entry:
            entry["corrected_hex"] = "{:02X}{:02X}{:02X}".format(*rgb)
    return data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hex(r: int, g: int, b: int) -> str:
    return f"{r:02X}{g:02X}{b:02X}"


def _contrast_text(r: int, g: int, b: int) -> str:
    """Return 'black' or 'white' for label text on a swatch background."""
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "black" if luminance > 0.55 else "white"


def _wrap_lines(text: str, max_chars: int = 28, max_lines: int = 3) -> list[str]:
    """Wrap a description string into up to `max_lines` lines of `max_chars`."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        candidate = (current + " " + w).strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = w
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:max_lines]


def _setup_axes(rows_n: int, cols_n: int):
    """Create a figure and axes set up for the 12-col × 10-row grid."""
    fig, ax = plt.subplots(figsize=(22, 14), dpi=300)
    ax.set_xlim(0, cols_n)
    ax.set_ylim(0, rows_n)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


# ---------------------------------------------------------------------------
# Standard cell renderer
# ---------------------------------------------------------------------------

def _draw_standard_cell(ax, x: float, y: float, color: dict, cell_w: float = 1.0,
                        cell_h: float = 1.0) -> None:
    """Draw a single (non-split) palette cell at (x, y)."""
    r, g, b = color["r"], color["g"], color["b"]
    txt_color = _contrast_text(r, g, b)

    h_deg, s_pct, v_pct = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h_deg *= 360
    s_pct *= 100
    v_pct *= 100

    ax.add_patch(Rectangle((x, y), cell_w, cell_h,
                            facecolor=(r / 255, g / 255, b / 255),
                            edgecolor="#666666", linewidth=0.6))

    ax.text(x + 0.5, y + 0.14, color["name"], ha="center", va="center",
            fontsize=8.5, fontweight="bold", color=txt_color)
    ax.text(x + 0.5, y + 0.29, f"{r}, {g}, {b}", ha="center", va="center",
            fontsize=6.8, color=txt_color)
    ax.text(x + 0.5, y + 0.41, f"#{_hex(r, g, b)}", ha="center", va="center",
            fontsize=6.8, color=txt_color, family="monospace")
    ax.text(x + 0.5, y + 0.53, f"H{h_deg:.0f}° S{s_pct:.0f}% V{v_pct:.0f}%",
            ha="center", va="center", fontsize=6.2, color=txt_color,
            family="monospace", alpha=0.85)

    for i, line in enumerate(_wrap_lines(color["description"])):
        ax.text(x + 0.5, y + 0.71 + i * 0.11, line, ha="center", va="center",
                fontsize=5.8, style="italic", color=txt_color)


# ---------------------------------------------------------------------------
# Split cell renderer (for corrections)
# ---------------------------------------------------------------------------

def _draw_split_cell(ax, x: float, y: float, color: dict, corrected_rgb: tuple[int, int, int],
                     cell_w: float = 1.0, cell_h: float = 1.0) -> None:
    """Draw a diagonal-split cell showing original (top-left) and corrected (bottom-right)."""
    r, g, b = color["r"], color["g"], color["b"]
    cR, cG, cB = corrected_rgb

    # Top-left triangle = ORIGINAL
    ax.add_patch(Polygon([(x, y), (x + cell_w, y), (x, y + cell_h)],
                          facecolor=(r / 255, g / 255, b / 255), edgecolor="none"))
    # Bottom-right triangle = CORRECTED
    ax.add_patch(Polygon([(x + cell_w, y), (x + cell_w, y + cell_h), (x, y + cell_h)],
                          facecolor=(cR / 255, cG / 255, cB / 255), edgecolor="none"))

    # Cell border + diagonal divider
    ax.add_patch(Rectangle((x, y), cell_w, cell_h, facecolor="none",
                            edgecolor="#666666", linewidth=0.6))
    ax.plot([x, x + cell_w], [y + cell_h, y], color="white", linewidth=1.0, alpha=0.85)

    # Red dashed marker outline (visual signal that this swatch has a correction)
    ax.add_patch(Rectangle((x + 0.012, y + 0.012),
                            cell_w - 0.024, cell_h - 0.024,
                            facecolor="none", edgecolor="#FF3030",
                            linewidth=1.2, linestyle="--", alpha=0.85))

    # ORIGINAL labels
    orig_text = _contrast_text(r, g, b)
    h_o, s_o, v_o = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    ax.text(x + 0.04, y + 0.10, color["name"], ha="left", va="center",
            fontsize=8.5, fontweight="bold", color=orig_text)
    ax.text(x + 0.04, y + 0.22, "ORIGINAL", ha="left", va="center",
            fontsize=5.5, fontweight="bold", color=orig_text,
            family="monospace", alpha=0.8)
    ax.text(x + 0.04, y + 0.31, f"{r},{g},{b}", ha="left", va="center",
            fontsize=6.5, color=orig_text, family="monospace")
    ax.text(x + 0.04, y + 0.39, f"#{_hex(r, g, b)}", ha="left", va="center",
            fontsize=6.5, color=orig_text, family="monospace")
    ax.text(x + 0.04, y + 0.47,
            f"H{h_o*360:.0f}° S{s_o*100:.0f}% V{v_o*100:.0f}%",
            ha="left", va="center", fontsize=5.8, style="italic",
            color=orig_text, alpha=0.9)

    # CORRECTED labels
    cor_text = _contrast_text(cR, cG, cB)
    h_c, s_c, v_c = colorsys.rgb_to_hsv(cR / 255, cG / 255, cB / 255)
    ax.text(x + cell_w - 0.04, y + 0.62, "CORRECTED", ha="right", va="center",
            fontsize=5.5, fontweight="bold", color=cor_text,
            family="monospace", alpha=0.85)
    ax.text(x + cell_w - 0.04, y + 0.72, f"{cR},{cG},{cB}",
            ha="right", va="center", fontsize=6.5, color=cor_text, family="monospace")
    ax.text(x + cell_w - 0.04, y + 0.82, f"#{_hex(cR, cG, cB)}",
            ha="right", va="center", fontsize=6.5, color=cor_text, family="monospace")
    ax.text(x + cell_w - 0.04, y + 0.92,
            f"H{h_c*360:.0f}° S{s_c*100:.0f}% V{v_c*100:.0f}%",
            ha="right", va="center", fontsize=5.8, style="italic",
            color=cor_text, alpha=0.9)


# ---------------------------------------------------------------------------
# Public render functions
# ---------------------------------------------------------------------------

def render_standard_grid(palette: Iterable[dict], output_path: Path) -> None:
    """Render the full 12×10 grid as a PNG."""
    fig, ax = _setup_axes(rows_n=10, cols_n=12)
    for color in palette:
        x = (color["grid_col"] - 1) * 1.0
        y = (color["grid_row"] - 1) * 1.0
        _draw_standard_cell(ax, x, y, color)
    plt.title("Esri (ArcMap/ArcGIS Pro) Standard Color Palette",
              fontsize=14, fontweight="bold", pad=18)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def render_corrections_grid(palette: Iterable[dict], corrections: list[dict],
                             output_path: Path) -> None:
    """Render the 12×10 grid with diagonal-split swatches for any corrected colors."""
    palette_list = list(palette)
    correction_map = {c["name"]: tuple(c["corrected_rgb"]) for c in corrections}

    fig, ax = _setup_axes(rows_n=10, cols_n=12)
    for color in palette_list:
        x = (color["grid_col"] - 1) * 1.0
        y = (color["grid_row"] - 1) * 1.0
        if color["name"] in correction_map:
            _draw_split_cell(ax, x, y, color, correction_map[color["name"]])
        else:
            _draw_standard_cell(ax, x, y, color)

    # Build subtitle from correction names (handles 1, 2, or many)
    correction_names = [c["name"] for c in corrections]
    if len(correction_names) == 0:
        subtitle = "(no corrections defined in corrections.json)"
    elif len(correction_names) == 1:
        subtitle = f"{correction_names[0]} shown split: original (top-left) / corrected (bottom-right)"
    elif len(correction_names) == 2:
        subtitle = (f"{correction_names[0]} and {correction_names[1]} shown split: "
                     "original (top-left) / corrected (bottom-right)")
    else:
        joined = ", ".join(correction_names[:-1]) + f", and {correction_names[-1]}"
        subtitle = f"{joined} shown split: original (top-left) / corrected (bottom-right)"

    plt.title("Esri (ArcMap/ArcGIS Pro) Standard Color Palette — with proposed corrections\n"
              + subtitle,
              fontsize=14, fontweight="bold", pad=18)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="make_palette_pngs.py",
        description=__doc__.split("USAGE")[0].strip() if __doc__ else None,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--standard", action="store_true",
                        help=f"Generate only {STANDARD_PNG_NAME}")
    parser.add_argument("--corrections", action="store_true",
                        help=f"Generate only {CORRECTIONS_PNG_NAME}")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR,
                        help="Folder containing palette.csv and corrections.json "
                             f"(default: {DEFAULT_INPUT_DIR})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help=f"Folder to write PNGs into (default: {DEFAULT_OUTPUT_DIR})")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # If neither flag is set, generate both
    do_standard = args.standard or not args.corrections
    do_corrections = args.corrections or not args.standard

    palette_path = args.input_dir / PALETTE_CSV_NAME
    corrections_path = args.input_dir / CORRECTIONS_JSON_NAME

    try:
        palette = load_palette(palette_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if do_standard:
        out = args.output_dir / STANDARD_PNG_NAME
        print(f"Rendering standard grid → {out}")
        render_standard_grid(palette, out)

    if do_corrections:
        try:
            corrections = load_corrections(corrections_path)
        except (FileNotFoundError, ValueError) as e:
            print(f"ERROR loading corrections: {e}", file=sys.stderr)
            return 1
        if not corrections:
            print(f"WARNING: no corrections found in {corrections_path}, "
                  f"skipping {CORRECTIONS_PNG_NAME}", file=sys.stderr)
        else:
            out = args.output_dir / CORRECTIONS_PNG_NAME
            print(f"Rendering corrections grid → {out}")
            render_corrections_grid(palette, corrections, out)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
