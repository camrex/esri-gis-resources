# Tools

Repository maintenance tooling that belongs to no single resource. Nothing here is part
of a resource's verification toolchain — those live beside the resource they verify, in
[`arcade-stateplane-utm-to-latlong/scripts`](../arcade-stateplane-utm-to-latlong/scripts)
and [`color-palettes/scripts`](../color-palettes/scripts), and every one of them backs a
documented claim. These do not. They generate presentation assets.

| Script | What it does |
| --- | --- |
| `make_social_card.py` | Write `arcade-stateplane-utm-to-latlong/social-card.png`, the link-preview image the landing page's Open Graph tags point at |
| `make_card_bg.py` | The map plate and pinned conversion behind it. `make_social_card.py` imports `render()` from here; running it directly writes a local preview |
| `make_map_svg.py` | The inline SVG map behind the landing page's heading, spliced into `index.html` between its `map:start` / `map:end` markers |

```powershell
python tools/make_social_card.py            # the card
python tools/make_social_card.py --check    # non-zero exit if the committed PNG is stale

python tools/make_card_bg.py                # card-bg.png, a gitignored preview of the map alone

python tools/make_map_svg.py                # print the SVG fragment
python tools/make_map_svg.py --write        # splice it into index.html
python tools/make_map_svg.py --write --check
```

The page map and the card share their source outlines, their Lambert Conformal Conic
framing and the same pinned conversion — `make_map_svg.py` imports that point and its
labels from `make_card_bg.py`, so the landing page and its link preview cannot drift apart.
It goes into the page as markup rather than as an image because that page is a single
self-contained file: no request, no resampling, and its colours come from the page's own
custom properties, which is what lets it follow dark mode without a second asset.

The map is inert to the pointer, clipped by the header so it cannot widen the page, and
hidden altogether below 46rem, where the standfirst takes the full column back. It carries
a `<title>` rather than `aria-hidden`, because the callout states a real conversion rather
than decorating: the map is the frame, the numbers are the point.

Outlines are simplified hard for that one (`TOLERANCE`, in projected metres): 50 rings and
about 18 KB of markup. Raise the tolerance if that grows.

**Only the finished card is committed.** The plate is rendered on demand, so there is no
intermediate PNG to fall out of step with its generator.

Both need numpy, matplotlib, pyproj and Pillow. All four are pip-installable, none is
`arcpy`, and the repository `.venv` carries them — so the card can be rebuilt without
ArcGIS Pro. Missing them degrades rather than fails: the card still renders, on plain
ground, with a warning on stderr.

Run them from the repository root or from this directory; paths resolve either way.

## The conversion on the pin is real

The callout is not decoration. **E 922,162.27 / N 519,888.66** is a genuine stored
position in **EPSG:2236**, NAD83 / Florida East (ftUS), and **25.761680°, −80.191790°**
is what the shipped expression returns for it. The condensed build answers
`25.76167999, -80.191789987`, which is that pair at the six decimals the callout prints,
and arcpy agrees on the forward projection to 0.00 ftUS. Re-check it with:

```powershell
cd arcade-stateplane-utm-to-latlong/scripts
echo [[2236, 922162.27, 519888.66]] > pt.json
node harness.js ../builds/arcade_latlong_condensed.txt RULE pt.json out.json
```

If you change the pin, re-run that. A social card for this particular resource is the
last place to print a coordinate nobody checked.

## Notes

State outlines come from public, Census-derived GeoJSON, cached into `_cache/` on first
run rather than committed; `_cache/` is gitignored. No basemap tiles are used, so the
card carries no attribution obligation when a social network re-hosts it.

`pyproj` draws those outlines. That is cartography rather than a claim, so it does not go
through `arcpy` the way anything load-bearing in this repository does — the conversion on
the pin is the claim, and that one is checked against both arcpy and the expression.

The card is sized 1200×630 and is designed to survive the ~552px render a LinkedIn feed
uses: at that scale the title, the standfirst, the two figures and the pinned lat/long
all still read.
