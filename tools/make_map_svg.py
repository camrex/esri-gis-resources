"""Emit the inline SVG map that sits behind the landing page's heading.

Same source outlines and same Lambert Conformal Conic framing as the social card,
so the page and its link preview show the same map. Output is a fragment written
to stdout, or spliced straight into index.html between its marker comments:

    python tools/make_map_svg.py                # print the fragment
    python tools/make_map_svg.py --write        # splice it into index.html
    python tools/make_map_svg.py --write --check   # non-zero exit if that would change it

The page is a single self-contained file, so this goes in as markup rather than as
an image: it costs no request, scales without resampling, and takes its colours
from the page's own custom properties, which is what lets it follow dark mode.

Outlines are simplified hard -- this is texture behind a headline, not a reference
map. TOLERANCE is in projected metres; raise it to shrink the markup further.

Needs numpy, matplotlib, pyproj and Pillow, same as make_card_bg, which it reuses
for the source data and the projection.
"""
import argparse
import pathlib
import re
import sys

import numpy as np
from pyproj import CRS, Transformer

from make_card_bg import (
    LCC, PIN_LABEL, PIN_LONLAT, PIN_RESULT, PIN_STORED, states,
)

PAGE = (pathlib.Path(__file__).resolve().parent.parent
        / "arcade-stateplane-utm-to-latlong" / "index.html")
START = "  <!-- map:start -->"
END = "  <!-- map:end -->"

TOLERANCE = 9000.0        # metres; ~9 km of detail is invisible at this size
MIN_RING_SPAN = 60000.0   # drop islands smaller than 60 km across
VIEW_W = 1000.0           # viewBox width; height follows the projection's aspect
DECIMALS = 1


def simplify(points, tol):
    """Ramer-Douglas-Peucker, iterative so a long ring cannot blow the stack."""
    n = len(points)
    keep = np.zeros(n, dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        seg = points[j] - points[i]
        length = np.hypot(*seg)
        rel = points[i + 1:j] - points[i]
        if length == 0:
            dist = np.hypot(rel[:, 0], rel[:, 1])
        else:
            dist = np.abs(seg[0] * rel[:, 1] - seg[1] * rel[:, 0]) / length
        k = int(np.argmax(dist))
        if dist[k] > tol:
            k += i + 1
            keep[k] = True
            stack.append((i, k))
            stack.append((k, j))
    return points[keep]


def build():
    lcc = CRS.from_proj4(
        f"+proj=lcc +lat_1={LCC['lat1']} +lat_2={LCC['lat2']} +lat_0={LCC['lat0']} "
        f"+lon_0={LCC['lon0']} +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs")
    tr = Transformer.from_crs("EPSG:4326", lcc, always_xy=True)

    rings = []
    for feat in states()["features"]:
        if feat["properties"]["name"] in ("Alaska", "Hawaii"):
            continue
        geom = feat["geometry"]
        parts = (geom["coordinates"] if geom["type"] == "MultiPolygon"
                 else [geom["coordinates"]])
        for part in parts:
            for ring in part:
                x, y = tr.transform([p[0] for p in ring], [p[1] for p in ring])
                pts = np.column_stack([np.asarray(x), np.asarray(y)])
                pts = pts[np.isfinite(pts).all(axis=1)]
                if len(pts) < 4:
                    continue
                span = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))
                if span < MIN_RING_SPAN:
                    continue
                out = simplify(pts, TOLERANCE)
                if len(out) >= 4:
                    rings.append(out)

    allpts = np.concatenate(rings)
    x0, x1 = allpts[:, 0].min(), allpts[:, 0].max()
    y0, y1 = allpts[:, 1].min(), allpts[:, 1].max()
    scale = VIEW_W / (x1 - x0)
    view_h = round((y1 - y0) * scale, 1)

    def to_view(pts):
        vx = (pts[:, 0] - x0) * scale
        vy = (y1 - pts[:, 1]) * scale        # SVG y grows downward
        return np.column_stack([vx, vy])

    def path(pts, close):
        v = to_view(pts).round(DECIMALS)
        head = f"M{v[0, 0]:g} {v[0, 1]:g}"
        body = "".join(f"L{a:g} {b:g}" for a, b in v[1:])
        return head + body + ("Z" if close else "")

    land = "".join(f'<path d="{path(r, True)}"/>' for r in rings)

    grat = []
    for lon in range(-126, -63, 6):          # 6-degree meridians, as on the card
        yy = np.linspace(24.0, 50.0, 24)
        gx, gy = tr.transform(np.full_like(yy, float(lon)), yy)
        grat.append(path(np.column_stack([gx, gy]), False))
    for lat in range(24, 53, 4):
        xx = np.linspace(-126.0, -64.0, 24)
        gx, gy = tr.transform(xx, np.full_like(xx, float(lat)))
        grat.append(path(np.column_stack([gx, gy]), False))
    grat_markup = "".join(f'<path d="{d}"/>' for d in grat)

    # The same point the social card pins, so the page and its preview agree.
    ppx, ppy = tr.transform(*PIN_LONLAT)
    px_, py_ = to_view(np.array([[ppx, ppy]]))[0].round(DECIMALS)
    pin_markup = (f'<circle class="halo" cx="{px_:g}" cy="{py_:g}" r="15"/>'
                  f'<circle class="dot" cx="{px_:g}" cy="{py_:g}" r="5.5"/>')

    # The callout, laid out in user units. Widths are estimated from the advance
    # of the monospaced face rather than measured, which is close enough because
    # the box is sized to the longest line with padding to spare.
    lab, stored, result = PIN_LABEL, PIN_STORED, PIN_RESULT
    fs_lab, fs_stored, fs_result = 18.0, 24.0, 32.0
    wid = max(len(stored) * fs_stored * 0.6, len(result) * fs_result * 0.6,
              len(lab) * fs_lab * 0.55) + 44
    hei = 36 + fs_lab + 12 + fs_stored + 12 + fs_result
    bx1 = px_ - 32
    bx0, by1 = bx1 - wid, py_ - 26
    by0 = by1 - hei
    ty = by0 + 18

    callout = (
        f'<line class="lead" x1="{bx1:g}" y1="{(by0 + hei / 2):g}" '
        f'x2="{px_ - 14:g}" y2="{(by0 + hei / 2):g}"/>'
        f'<rect class="box" x="{bx0:g}" y="{by0:g}" width="{wid:g}" height="{hei:g}" rx="10"/>'
        f'<rect class="edge" x="{bx0:g}" y="{by0 + 14:g}" width="4" height="{hei - 28:g}" rx="2"/>'
        f'<text class="lab" x="{bx0 + 22:g}" y="{ty + fs_lab * 0.8:g}">{lab}</text>'
        f'<text class="val" x="{bx0 + 22:g}" '
        f'y="{ty + fs_lab + 12 + fs_stored * 0.8:g}">{stored}</text>'
        f'<text class="res" x="{bx0 + 22:g}" '
        f'y="{ty + fs_lab + 12 + fs_stored + 12 + fs_result * 0.8:g}">{result}</text>')

    # The fade is an SVG mask over the map layers only, not a CSS mask over the
    # whole element: the callout sits in the faded half and has to stay opaque.
    # xMaxYMax anchors the crop bottom right, where the pin is -- centring it
    # vertically cropped Florida off the bottom.
    svg = (f'  <svg class="mapbg" viewBox="0 0 {VIEW_W:g} {view_h:g}" '
           f'preserveAspectRatio="xMaxYMax slice" role="img" focusable="false">\n'
           f'    <title>The lower 48, with the point this expression converts: '
           f'{stored} in EPSG 2236 becomes {result}</title>\n'
           f'    <defs><linearGradient id="mapfade" x1="0" y1="0" x2="1" y2="0">'
           f'<stop offset="0.06" stop-color="#fff" stop-opacity="0"/>'
           f'<stop offset="0.54" stop-color="#fff" stop-opacity="1"/></linearGradient>'
           f'<mask id="mapmask"><rect x="0" y="0" width="{VIEW_W:g}" '
           f'height="{view_h:g}" fill="url(#mapfade)"/></mask></defs>\n'
           f'    <g mask="url(#mapmask)">\n'
           f'      <g class="grat">{grat_markup}</g>\n'
           f'      <g class="land">{land}</g>\n'
           f'    </g>\n'
           f'    <g class="pin">{pin_markup}</g>\n'
           f'    <g class="callout">{callout}</g>\n'
           f'  </svg>')
    return svg, len(rings), view_h


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="splice into index.html")
    ap.add_argument("--check", action="store_true",
                    help="with --write, exit non-zero instead of writing a change")
    args = ap.parse_args()

    svg, n, view_h = build()
    if not args.write:
        print(svg)
        print(f"\n<!-- {n} rings, viewBox height {view_h:g}, "
              f"{len(svg) / 1024:.1f} KB -->", file=sys.stderr)
        return 0

    page = PAGE.read_text(encoding="utf-8")
    if START not in page or END not in page:
        sys.exit(f"markers {START.strip()} / {END.strip()} not found in {PAGE.name}")
    new = re.sub(f"{re.escape(START)}.*?{re.escape(END)}",
                 lambda _: f"{START}\n{svg}\n{END}", page, flags=re.S)
    if args.check:
        if new == page:
            print(f"up to date: {PAGE.name} ({n} rings, {len(svg) / 1024:.1f} KB)")
            return 0
        print(f"OUT OF DATE: {PAGE.name} -- rerun without --check")
        return 1

    PAGE.write_text(new, encoding="utf-8", newline="")
    print(f"spliced into {PAGE.name}: {n} rings, {len(svg) / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
