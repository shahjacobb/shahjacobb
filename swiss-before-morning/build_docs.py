#!/usr/bin/env python3
"""Render 01-shot-list.md from shots.json so prose and prompts cannot drift.

    python build_docs.py
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("gen", ROOT / "generate.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

d = gen.load_spec()
locks = d["locks"]
runtime = sum(s["duration"] for s in d["shots"])

out = [
    f'# SHOT LIST — "{d["title"]}" · {runtime}s · {d["campaign"]}',
    "",
    "> Generated from `shots.json` by `build_docs.py`. Edit the JSON, not this file.",
    "",
    "Eight individually directed shots. Each is generated as a **locked reference frame**",
    "first (text-to-image), then animated (image-to-video). Never generate a shot from a",
    "text prompt alone — that is where the face drifts.",
    "",
    "Each prompt below shows only the `SHOT —` body. `generate.py` prepends the SUBJECT,",
    "VEHICLE and AIRCRAFT lock blocks this shot needs and appends STYLE and CONTINUITY,",
    "so the wording of the woman and the car is byte-identical across all eight shots.",
    "",
    "The arc: **cared for in the air → personally welcomed on arrival → completely in",
    "control on the road.**",
    "",
    "---",
    "",
]

for i, s in enumerate(d["shots"], 1):
    out += [
        f'## SHOT {i:02d} — {s["title"].upper()} · {s["timecode"]} · {s["duration"]}s',
        "",
        f'> **Beat:** {s["beat"]}',
        "",
        f'**Locks:** `{"`, `".join(s["locks"])}`',
        "",
        f'**Camera:** {s["camera"]}',
        "",
        "**Reference frame (t2i):**",
        "",
        f'> {s["reference_frame_prompt"]}',
        "",
        "**Motion (i2v):**",
        "",
        f'> {s["video_prompt"]}',
        "",
    ]
    if "dialogue" in s:
        out += [f'**Dialogue:** {s["dialogue"]}', ""]
    out += [f'**Sound:** {s["sound"]}', ""]
    if "note" in s:
        out += [f'**Note:** {s["note"]}', ""]
    out += ["---", ""]

out += [
    "## END CARDS",
    "",
    "Held 2s each over black after the final frame. Helvetica Neue Light, generous",
    "letter-spacing, left-aligned at optical centre. Added in post — **never generated**.",
    "",
]
for card in d["end_cards"]:
    out += ["```", card, "```", ""]
out += [
    "Brand lockups applied in post at correct trademark proportions.",
    "",
    "## NEGATIVE PROMPT (all shots)",
    "",
    "```",
    locks["negative"],
    "```",
    "",
]

(ROOT / "01-shot-list.md").write_text("\n".join(out))
print(f"wrote 01-shot-list.md — {len(d['shots'])} shots, {runtime}s")
