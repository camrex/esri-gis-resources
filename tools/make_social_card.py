"""Regenerate the 1200x630 link-preview image for the Arcade expression's landing page.

Writes arcade-stateplane-utm-to-latlong/social-card.png, which that page's Open Graph
tags point at. Colours and type follow the page itself: Palatino for the title, Segoe UI
for prose, Consolas for figures, and its light-theme tokens. Windows font paths, since
that is where the rest of this repository's tooling runs.

    python tools/make_social_card.py
    python tools/make_social_card.py --check    # verify the committed PNG is current

Requires Pillow, and nothing else. This produces a presentation asset rather than a
validated one, which is why it lives here instead of beside the verification scripts.
"""
import argparse
import io
import pathlib

from PIL import Image, ImageDraw, ImageFont

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "arcade-stateplane-utm-to-latlong" / "social-card.png"
# The map plate and its pinned conversion, from make_card_bg.py. Absent, the card
# still renders -- it just falls back to plain ground.
BG = pathlib.Path(__file__).resolve().parent / "card-bg.png"
W, H = 1200, 630
PAD = 76

SURFACE = "#FFFFFF"
GROUND = "#EDF0F3"
INK = "#15202A"
INK2 = "#3E4D5A"
INK3 = "#6C7C8A"
RULE = "#CFD8DF"
ACCENT = "#0B6E75"

F = "C:/Windows/Fonts/"


def font(name, size):
    return ImageFont.truetype(F + name, size)


def render():
    img = (Image.open(BG).convert("RGB") if BG.exists()
           else Image.new("RGB", (W, H), SURFACE))
    d = ImageDraw.Draw(img)

    # Accent spine on the left edge. No ground band on the right any more -- the
    # map plate occupies that side.
    d.rectangle([0, 0, 9, H], fill=ACCENT)

    y = PAD

    # Eyebrow, with manual letter-spacing.
    x, eyebrow = PAD, font("consola.ttf", 21)
    for ch in "ESRI-GIS-RESOURCES":
        d.text((x, y), ch, font=eyebrow, fill=ACCENT)
        x += d.textlength(ch, font=eyebrow) + 3.2

    # Title. Palatino has no U+2192, so the arrow is set in Segoe UI and aligned to
    # the cap-height midpoint of the serif line beside it.
    y += 58
    title = font("palab.ttf", 63)
    head = "State Plane / UTM "
    d.text((PAD, y), head, font=title, fill=INK)
    _, cap_top, _, cap_bot = d.textbbox((PAD, y), "UTM", font=title)
    d.text((PAD + d.textlength(head, font=title), (cap_top + cap_bot) / 2), "\u2192",
           font=font("segoeui.ttf", 52), fill=ACCENT, anchor="lm")
    y += 76
    d.text((PAD, y), "Latitude & Longitude, in Arcade", font=title, fill=INK)
    y += 76

    y += 18
    for line in (
        "One Arcade expression across every US State Plane and UTM zone \u2014",
        "returning what ArcGIS itself returns, where a geoprocessing tool cannot go.",
    ):
        d.text((PAD, y), line, font=font("segoeui.ttf", 27), fill=INK2)
        y += 38

    y += 28
    d.line([(PAD, y), (W - 210, y)], fill=RULE, width=1)

    y += 30
    x = PAD
    # Two facts, not three: the pinned conversion occupies the right of the card
    # now, so MIT moves to the footer line rather than crowding it.
    facts = [("1,139", "EPSG codes"), ("0.07 mm", "worst disagreement")]
    for i, (num, cap) in enumerate(facts):
        if i:
            d.line([(x - 34, y + 6), (x - 34, y + 62)], fill=RULE, width=1)
        nf, cf = font("consolab.ttf", 40), font("segoeui.ttf", 21)
        d.text((x, y), num, font=nf, fill=ACCENT)
        d.text((x, y + 50), cap.upper(), font=cf, fill=INK3)
        x += max(d.textlength(num, font=nf), d.textlength(cap.upper(), font=cf)) + 78

    d.text((PAD, H - PAD - 6), "github.com/camrex/esri-gis-resources  ·  MIT",
           font=font("consola.ttf", 20), fill=INK3)

    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the committed PNG differs from a fresh render")
    args = ap.parse_args()

    img = render()
    if args.check:
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        current = OUT.read_bytes() if OUT.exists() else b""
        if buf.getvalue() == current:
            print(f"up to date: {OUT.name}")
            return 0
        print(f"OUT OF DATE: {OUT.name} — rerun without --check")
        return 1

    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({W}x{H})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
