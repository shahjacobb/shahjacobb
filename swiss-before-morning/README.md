# "Before Morning" — SWISS × BMW M340i spec film

A 44-second cinematic spec commercial. One traveller, from a night landing at
Zürich to sunrise in Andermatt. Eight individually directed shots, one locked
character reference and one locked vehicle reference, generated two-stage so the
face and the car survive all eight.

```
04:40  ZÜRICH
06:12  ANDERMATT

Some journeys begin after arrival.

SWISS  ×  BMW M340i
THE JOURNEY CONTINUES.
```

## The arc

Cared for in the air → personally welcomed on arrival → completely in control on
the road. The signature moment is the match cut at 0:14–0:18: the aircraft's red
wingtip navigation light becomes the car's red taillight. That single cut is the
campaign — the airline hands her to the car.

## Files

| File | What it is |
|---|---|
| `shots.json` | **Source of truth.** Lock strings, all 8 shots, prompts, direction notes, end cards. |
| `00-lock-sheet.md` | Casting, wardrobe, vehicle and photography direction behind the locks. |
| `01-shot-list.md` | Generated shot list. Run `build_docs.py` after editing the JSON. |
| `02-music.md` | Score prompt, structure against picture, sound design spine. |
| `generate.py` | Two-stage fal runner. |
| `build_docs.py` | Renders `01-shot-list.md` from `shots.json`. |

## Running it

```bash
pip install fal-client
export FAL_KEY=...              # never commit this; .env is gitignored

python generate.py --stage refs --dry-run     # inspect payloads, calls nothing
python generate.py --stage refs --variants 3  # 3 reference frames per shot
# --- approve every frame by eye here ---
python generate.py --stage video
```

Useful flags: `--shots 03_coat 04_matchcut` to work a subset, `--seed 12345` to
hold a face across regenerations, `--force` to overwrite existing output.

**Approve stage 1 before you run stage 2.** The whole design of this pipeline is
that continuity is decided in the stills, where a retry is cheap. Animating an
off-model reference frame just buys an expensive off-model clip.

Endpoints are configured in `shots.json` under `endpoints` — reference frames via
Flux Pro Ultra, motion via `fal-ai/minimax/h3-max/image-to-video` (the post-trained
H3 variant). The exact argument names for the H3 Max endpoint could not be verified
from this environment (fal.ai is blocked by the network egress proxy here), so
check `duration`, `resolution` and `prompt_optimizer` against the live API page
before the first paid run — `--dry-run` prints the exact payload.

## Post

Three things are **never generated** and are always added in post:

1. All end-card typography (Helvetica Neue Light, generous tracking).
2. SWISS and BMW brand lockups, at correct trademark proportions.
3. The final grade, carrying the film cool-to-warm from sodium night to alpine gold.

Generated text is the fastest way to make a spec film look fake. Keep it out of
the frames.

## Brand status

This is an unofficial spec/concept film. It uses real SWISS and BMW marks and
cannot be published or distributed as though it were an approved campaign from
either company without their sign-off. Two practical consequences:

- Video models render real badges and liveries inconsistently shot to shot. Expect
  to clean up or replace grille badges and tail livery in post.
- An **unbranded fallback** is documented in `00-lock-sheet.md` §2 — swap one lock
  string and drop the third end card. Worth building alongside the branded cut if
  approval is uncertain.
