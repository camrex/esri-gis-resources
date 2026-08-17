# Tools

Repository maintenance tooling that belongs to no single resource. Nothing here is part
of a resource's verification toolchain — those live beside the resource they verify, in
[`arcade-stateplane-utm-to-latlong/scripts`](../arcade-stateplane-utm-to-latlong/scripts)
and [`color-palettes/scripts`](../color-palettes/scripts), and every one of them backs a
documented claim. These do not. They generate presentation assets.

| Script | Needs | What it does |
| --- | --- | --- |
| `make_card_bg.py` | numpy, matplotlib, pyproj, Pillow | Render `card-bg.png`: the US map plate and the pinned conversion behind the social card |
| `make_social_card.py` | Pillow | Composite the card's type over that plate into `arcade-stateplane-utm-to-latlong/social-card.png`, the link-preview image the landing page's Open Graph tags point at |

```powershell
python tools/make_card_bg.py                # the map plate, first
python tools/make_social_card.py            # then the type over it

python tools/make_card_bg.py --check        # non-zero exit if a committed PNG is stale
python tools/make_social_card.py --check
```

Run them from the repository root or from this directory; paths resolve either way. The
card generator falls back to plain ground if `card-bg.png` is missing, so it still works
without the plotting stack.

None of this needs `arcpy` — the dependencies are all pip-installable, and the repository
`.venv` carries them.

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
