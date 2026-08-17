"""Background plate for the Arcade resource's social card.

Renders 1200x630: the card's own ground on the left, fading into a Lambert
Conformal Conic map of the lower 48 on the right, with a pin over Miami
carrying a real State Plane conversion -- EPSG:2236, Florida East (ftUS).

Output is a BACKGROUND ONLY. make_social_card.py imports render() from here and
composites the card's text over it, so the two stay separable: this file owns
the map, that one owns the type. The plate is generated on demand rather than
committed -- only the finished social-card.png is an artifact worth versioning.

Running this file directly writes card-bg.png beside it, which is a local
preview for working on the map alone. That file is gitignored.

    python make_card_bg.py             -> card-bg.png, a preview

The numbers on the pin are not decoration. E 922,162.27 / N 519,888.66 in
EPSG:2236 is the stored position of the point the callout reports, and
25.761680, -80.191790 is what the shipped expression returns for it -- the
condensed build answers 25.76167999, -80.191789987, which is that pair at the
six decimals the callout prints. Verify with:

    cd ../arcade-stateplane-utm-to-latlong/scripts
    echo [[2236, 922162.27, 519888.66]] > pt.json
    node harness.js ../builds/arcade_latlong_condensed.txt RULE pt.json out.json

pyproj draws the state outlines, which is cartography rather than a claim, so
it does not go through arcpy the way anything load-bearing in this repository
does. The conversion on the pin is the claim, and that one is checked against
arcpy and against the expression itself.

Needs numpy, matplotlib, pyproj and Pillow -- all pip-installable, none of them
arcpy, so the card can be rebuilt without ArcGIS Pro. Run it from this directory.
"""
import argparse
import json
import logging
import pathlib
import urllib.request

import matplotlib
import numpy as np

matplotlib.use("Agg")
# "Ignoring fixed y limits to fulfill fixed data aspect" is expected -- see the
# adjustable="datalim" note in render_map. It goes through logging rather than
# warnings, so a warnings filter does not catch it.
logging.getLogger("matplotlib.axes._base").setLevel(logging.ERROR)

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402

from pyproj import CRS, Transformer  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "card-bg.png"
CACHE = HERE / "_cache"
STATES = CACHE / "us_states.json"

# Census-derived state outlines, public domain. Cached rather than committed;
# the plate is regenerated rarely and this is the only network dependency.
STATES_URLS = [
    "https://raw.githubusercontent.com/python-visualization/folium/"
    "main/examples/data/us-states.json",
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/"
    "master/data/geojson/us-states.json",
]

W, H, SS = 1200, 630, 2                   # canvas, and supersample factor

# Tokens lifted from index.html so the plate and the type agree.
GROUND = "#EDF0F3"
SURFACE = "#FFFFFF"
ACCENT = "#0B6E75"
ACCENT_SOFT = "#4E9A9A"
INK = "#15202A"
INK3 = "#6C7C8A"
RULE = "#CFD8DF"

LCC = dict(lon0=-96.0, lat1=33.0, lat2=45.0, lat0=39.0)
MAP_SIZE = (700, 600)                     # plate size in card pixels
# The pin sits in the lower right, the one quadrant the type leaves empty: the
# title and stand run out at y~380, the facts and URL stop around x~600.
PIN_TARGET = (1016, 556)
FADE_FROM, FADE_TO = 0.50, 0.88           # left-to-right reveal, fractions of W
MAP_MAX_ALPHA = 0.46                      # ceiling, so type over it stays readable

PIN_LONLAT = (-80.191790, 25.761680)
PIN_LABEL = "FLORIDA EAST · EPSG 2236 · ftUS"
PIN_STORED = "E 922,162.27   N 519,888.66"
PIN_RESULT = "25.761680°,  -80.191790°"

F = "C:/Windows/Fonts/"


def font(name, size):
    return ImageFont.truetype(F + name, size)


def states():
    if not STATES.exists():
        CACHE.mkdir(exist_ok=True)
        last = None
        for url in STATES_URLS:
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    STATES.write_text(json.dumps(json.load(r)), encoding="utf-8")
                break
            except Exception as e:                        # try the next mirror
                last = e
        else:
            raise SystemExit(
                f"could not fetch state outlines ({last}) -- download either URL in "
                f"STATES_URLS by hand and save it as {STATES}")
    return json.loads(STATES.read_text(encoding="utf-8"))


def render_map():
    """Draw the lower 48 into a transparent plate.

    Returns the image and the pin's position as a fraction of it, taken from
    the data transform rather than from the axes box, so it cannot drift.
    """
    gj = states()
    lcc = CRS.from_proj4(
        f"+proj=lcc +lat_1={LCC['lat1']} +lat_2={LCC['lat2']} +lat_0={LCC['lat0']} "
        f"+lon_0={LCC['lon0']} +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs")
    tr = Transformer.from_crs("EPSG:4326", lcc, always_xy=True)

    polys, xs, ys = [], [], []
    for feat in gj["features"]:
        if feat["properties"]["name"] in ("Alaska", "Hawaii"):
            continue
        geom = feat["geometry"]
        parts = (geom["coordinates"] if geom["type"] == "MultiPolygon"
                 else [geom["coordinates"]])
        for part in parts:
            for ring in part:
                x, y = tr.transform([p[0] for p in ring], [p[1] for p in ring])
                x, y = np.asarray(x), np.asarray(y)
                ok = np.isfinite(x) & np.isfinite(y)
                if ok.sum() < 4:
                    continue
                polys.append((x[ok], y[ok]))
                xs.append(x[ok])
                ys.append(y[ok])

    xs, ys = np.concatenate(xs), np.concatenate(ys)
    bw, bh = MAP_SIZE[0] * SS, MAP_SIZE[1] * SS
    fig = plt.figure(figsize=(bw / 100, bh / 100), dpi=100)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.set_axis_off()
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

    # Graticule first, so it reads as underlay. 6-degree meridians echo the UTM
    # zone width the expression covers.
    for lon in range(-125, -60, 6):
        yy = np.linspace(22, 51, 60)
        px, py = tr.transform(np.full_like(yy, lon), yy)
        ax.plot(px, py, lw=0.7 * SS, color=ACCENT_SOFT, alpha=0.35, zorder=1)
    for lat in range(24, 52, 4):
        xx = np.linspace(-126, -64, 60)
        px, py = tr.transform(xx, np.full_like(xx, lat))
        ax.plot(px, py, lw=0.7 * SS, color=ACCENT_SOFT, alpha=0.35, zorder=1)

    for x, y in polys:
        ax.add_patch(PathPatch(MplPath(np.column_stack([x, y])),
                               facecolor=ACCENT, alpha=0.11, edgecolor="none", zorder=2))
        ax.plot(x, y, lw=1.05 * SS, color=ACCENT, alpha=0.8,
                solid_joinstyle="round", zorder=3)

    pad = (xs.max() - xs.min()) * 0.015
    ax.set_xlim(xs.min() - pad, xs.max() + pad)
    ax.set_ylim(ys.min() - pad, ys.max() + pad)
    # 'datalim' widens the data window instead of shrinking and re-centring the
    # axes inside the figure, which would move the pin off its mark.
    ax.set_aspect("equal", adjustable="datalim")

    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba()).copy()  # pyright: ignore[reportAttributeAccessIssue]
    px, py = tr.transform(*PIN_LONLAT)
    dx, dy = ax.transData.transform((px, py))
    ih, iw = buf.shape[0], buf.shape[1]
    plt.close(fig)
    return Image.fromarray(buf, "RGBA"), (dx / iw, 1.0 - dy / ih)


def draw_pin(canvas, xy):
    """Teardrop pin, and the callout carrying the conversion."""
    s = SS
    x, y = xy
    d = ImageDraw.Draw(canvas, "RGBA")

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([x - 12 * s, y - 4 * s, x + 12 * s, y + 4 * s],
                                   fill=(21, 32, 42, 55))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(4 * s)))

    r = 12 * s
    cy = y - 28 * s
    d.ellipse([x - r, cy - r, x + r, cy + r], fill=ACCENT)
    d.polygon([(x - r * 0.72, cy + r * 0.70), (x + r * 0.72, cy + r * 0.70), (x, y)],
              fill=ACCENT)
    d.ellipse([x - r * 0.36, cy - r * 0.36, x + r * 0.36, cy + r * 0.36],
              fill=(255, 255, 255, 255))

    # Sized for the ~552px render LinkedIn uses in a feed, where the whole card
    # is at 46%: the result line is the payoff and has to survive that, the two
    # above it are supporting detail that only has to survive a click.
    lines = [(PIN_LABEL, font("seguisb.ttf", 13 * s), INK3),
             (PIN_STORED, font("consola.ttf", 16 * s), INK),
             (PIN_RESULT, font("consolab.ttf", 22 * s), ACCENT)]
    padx, pady, gap = 17 * s, 13 * s, 8 * s
    wid = max(d.textlength(t, font=f) for t, f, _ in lines) + padx * 2
    hei = sum(f.size + gap for _, f, _ in lines) - gap + pady * 2

    bx1 = x - 20 * s
    bx0, by0 = bx1 - wid, y - 32 * s - hei
    by1 = by0 + hei

    card = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([bx0, by0 + 3 * s, bx1, by1 + 3 * s],
                                           radius=8 * s, fill=(21, 32, 42, 40))
    canvas.alpha_composite(card.filter(ImageFilter.GaussianBlur(6 * s)))
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=8 * s,
                        fill=(255, 255, 255, 247), outline=RULE, width=1 * s)
    d.rounded_rectangle([bx0, by0 + 10 * s, bx0 + 3 * s, by1 - 10 * s],
                        radius=2 * s, fill=ACCENT)

    ty = by0 + pady
    for text, f, colour in lines:
        d.text((bx0 + padx, ty), text, font=f, fill=colour)
        ty += f.size + gap

    d.line([bx1, by0 + hei / 2, x - 18 * s, by0 + hei / 2], fill=RULE, width=1 * s)


def render():
    # Pass 1 locates the pin inside the plate; pass 2 positions the plate so the
    # pin lands on PIN_TARGET.
    _, (fx, fy) = render_map()
    mw, mh = MAP_SIZE
    left = int(round(PIN_TARGET[0] - fx * mw))
    top = int(round(PIN_TARGET[1] - fy * mh))

    map_img, (fx, fy) = render_map()
    canvas = Image.new("RGBA", (W * SS, H * SS), (255, 255, 255, 255))
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    layer.paste(map_img, (left * SS, top * SS), map_img)

    gx = np.linspace(0, 1, W * SS)
    u = np.clip((gx - FADE_FROM) / (FADE_TO - FADE_FROM), 0, 1)
    mask = np.tile(u * u * (3 - 2 * u), (H * SS, 1)) * MAP_MAX_ALPHA

    alpha = np.asarray(layer)[:, :, 3].astype(np.float32) / 255.0
    layer.putalpha(Image.fromarray((alpha * mask * 255).astype(np.uint8), "L"))
    canvas = Image.alpha_composite(canvas, layer)

    draw_pin(canvas, ((left + fx * mw) * SS, (top + fy * mh) * SS))
    return canvas.resize((W, H), Image.Resampling.LANCZOS).convert("RGB")


def main():
    # No --check here: the plate is not a committed artifact, so there is nothing
    # to be stale against. make_social_card.py --check covers the finished card.
    argparse.ArgumentParser(description=__doc__).parse_args()
    render().save(OUT, optimize=True)
    print(f"wrote {OUT} ({W}x{H})  pin at {PIN_TARGET}  [preview, gitignored]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
