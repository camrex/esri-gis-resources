<!-- markdownlint-disable MD041 -->
<!-- Thanks for this. Keep it to one thing where you can, and delete any section that does not apply. -->

## What this changes

<!-- One or two lines. Link the issue if there is one. -->

## What you ran

<!-- Whichever apply — paste the summary line, not the whole output. -->

- [ ] `python scripts/validate.py <build>` — headless, against `arcpy`
- [ ] `python scripts/lint.py <build>` — required after any template change
- [ ] `python scripts/run_in_arcade.py <build>` — the real Arcade engine
- [ ] `python color-palettes/scripts/verify_palette.py` — palette values against the live style
- [ ] Not applicable (docs, landing page, tooling)

ArcGIS Pro version:

## Checks

- [ ] `builds/*.txt` were **regenerated**, not hand-edited — or are untouched
- [ ] Generated assets are current (`make_palette_xlsx.py --check`, `tools/make_social_card.py --check`)
- [ ] [CHANGELOG.md](https://github.com/camrex/esri-gis-resources/blob/main/CHANGELOG.md) updated under `[Unreleased]`
- [ ] Anyone whose work this builds on is credited
