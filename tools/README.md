# Tools

Repository maintenance tooling that belongs to no single resource. Nothing here is part
of a resource's verification toolchain — those live beside the resource they verify, in
[`arcade-stateplane-utm-to-latlong/scripts`](../arcade-stateplane-utm-to-latlong/scripts)
and [`color-palettes/scripts`](../color-palettes/scripts), and every one of them backs a
documented claim. These do not. They generate presentation assets.

| Script | Needs | What it does |
| --- | --- | --- |
| `make_social_card.py` | Pillow | Regenerate `arcade-stateplane-utm-to-latlong/social-card.png`, the link-preview image that page's Open Graph tags point at |

```powershell
python tools/make_social_card.py            # rewrite the PNG
python tools/make_social_card.py --check    # non-zero exit if the committed PNG is stale
```

Run them from the repository root or from this directory; paths resolve either way.

The reason a generator is committed at all: a generated file in this repository has its
generator beside it, so an asset can be reproduced or adjusted rather than being an
image nobody can regenerate.
