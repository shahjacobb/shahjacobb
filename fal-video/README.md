# SWISS × BMW M340i — "The Journey Continues"

A 45-second spec film, generated shot by shot on [fal](https://fal.ai) and cut
together locally. Unofficial concept work — not affiliated with, endorsed by, or
produced for SWISS or BMW.

## The arc

Cared for in the air → personally welcomed on arrival → completely in control on
the road. The signature moment is the **match cut at 0:18**: the red
anti-collision beacon on the aircraft belly becomes the red taillight of the
waiting M340i, same position and scale in frame, hard cut.

| Time | Beat |
|------|------|
| 0:00–0:04 | Descent through cloud into Zürich; she wakes as runway lights appear |
| 0:04–0:09 | The espresso. *"Good morning. We'll be in Zürich shortly."* |
| 0:09–0:14 | At the door, helped into the coat. *"Welcome to Zürich." / "Thank you. It was lovely."* |
| 0:14–0:18 | Jet bridge, crew framed behind her → the beacon |
| 0:18–0:23 | Match cut to the taillight; the host, the trunk, the key — the handoff |
| 0:23–0:30 | Into the ivory interior. She exhales. The track opens up |
| 0:30–0:38 | Tunnel, hands, bodywork, Lake Lucerne, one Alpine bend. A private smile |
| 0:38–0:44 | Andermatt. She pauses. The aircraft crosses faintly overhead |
| 0:44–0:45 | End card |

## Run it

```bash
pip install -r requirements.txt
export FAL_KEY=...            # never commit this
python3 generate.py           # dry run: prints the shot plan and a cost estimate
python3 generate.py --go      # actually generates
python3 assemble.py --music /path/to/new-romance.mp3
```

Output lands at `out/film.mp4`. `assemble.py` needs `ffmpeg` on PATH.

Generation is the expensive step — 19 clips at 8 s each. `generate.py` is a dry
run by default and prints an estimate before you spend anything; correct
`EST_USD_PER_CLIP` against fal's current pricing first, since the built-in
number is only a placeholder.

## Working on individual shots

Clips are cached, so re-runs only generate what's missing:

```bash
python3 generate.py --shots 06,07 --force --go   # redo just the match cut
python3 assemble.py --music ...                  # recut
```

The match cut is the shot most likely to need a few passes. Both 06 and 07 are
prompted to put the red light dead centre at about one fifth of frame height —
if the cut doesn't land, tighten that language or pin a `seed` on each shot in
`storyboard.json` and iterate.

## Structure

- `storyboard.json` — the whole film: timings, prompts, cast, audio policy
- `generate.py` — submits each shot to fal, polls, downloads to `out/shots/`
- `assemble.py` — trims to slots, hard-cuts, mixes music under dialogue, adds the card

### Notes on the storyboard

Each shot's prompt is assembled as **cast block → action → house look**. Keeping
the character descriptions as a separate prefix (rather than inlined mid-
sentence) is what holds the woman and the flight attendant consistent across
nineteen independent generations.

`tin`/`tout` are timeline positions; clips are generated at 8 s and trimmed down
to fill their slot. If the good part of a generation isn't at the head of the
clip, add `"src_in": 2.5` to that shot to pick a later window.

Shots 03 and 04 are the only ones with `"audio": "dialogue"` — they need a model
with native synced speech (veo3 by default). Everything else is generated silent
and carried by the track, which sits at low level under the cabin dialogue,
ramps up across the handoff, and opens fully at 0:23.

Verify `DIALOGUE_MODEL` / `SILENT_MODEL` in `generate.py` against
[fal.ai/models](https://fal.ai/models) before a real run — fal renames and
reversions endpoints.
