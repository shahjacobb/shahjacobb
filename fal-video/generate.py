#!/usr/bin/env python3
"""Generate the SWISS x BMW M340i spec film shot by shot on fal.

Each storyboard beat is generated as its own clip, then trimmed to its
timeline slot by assemble.py. Nothing here writes a key to disk: the
credential is read from the FAL_KEY environment variable only.
"""
import argparse
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import fal_client
except ImportError:
    sys.exit("fal-client not installed. Run: pip install -r requirements.txt")

HERE = Path(__file__).parent
OUT = HERE / "out" / "shots"

# Verify against https://fal.ai/models before a real run - fal renames and
# reversions endpoints, and the dialogue beats (03, 04) need a model with
# native synced speech. veo3 is the safe default for those.
DIALOGUE_MODEL = "fal-ai/veo3"
SILENT_MODEL = "fal-ai/veo3"

# Generated length per clip. Shots are trimmed down to their timeline slot
# later, so this only needs to be >= the longest slot.
GEN_SECONDS = 8

# Rough per-clip cost used for the estimate only. Check fal's pricing page;
# this is deliberately a guess you should correct before spending.
EST_USD_PER_CLIP = 3.20

NEGATIVE = (
    "subtitles, captions, burned-in text, watermark, logo overlay, distorted hands, "
    "extra fingers, morphing faces, warped car badges, cartoonish, oversaturated, "
    "exaggerated grinning, stock-footage look"
)


def load_storyboard(path):
    """Build each prompt as: cast descriptions, then action, then house look.

    Keeping the cast block separate from the action sentence is what holds
    the woman and the flight attendant consistent across nineteen separate
    generations - inlining the descriptions mid-sentence reads as garble.
    """
    board = json.loads(Path(path).read_text(encoding="utf-8"))
    tokens = board.get("tokens", {})
    look = tokens.get("LOOK", "")
    for shot in board["shots"]:
        blocks = [tokens[name] for name in shot.get("cast", []) if name in tokens]
        blocks.append(shot["prompt"])
        if look:
            blocks.append(look)
        shot["resolved_prompt"] = "\n\n".join(blocks)
        shot["seconds"] = round(shot["tout"] - shot["tin"], 3)
    return board


def dest_for(shot):
    return OUT / f"{shot['id']}_{shot['slug']}.mp4"


def find_video_url(result):
    """fal result shapes vary by model; pull the first mp4-ish url out."""
    if isinstance(result, dict):
        for key in ("video", "videos", "output", "url"):
            if key in result:
                found = find_video_url(result[key])
                if found:
                    return found
        for value in result.values():
            found = find_video_url(value)
            if found:
                return found
    elif isinstance(result, list):
        for item in result:
            found = find_video_url(item)
            if found:
                return found
    elif isinstance(result, str) and result.startswith("http"):
        return result
    return None


def generate(shot, aspect, verbose):
    model = DIALOGUE_MODEL if shot["audio"] == "dialogue" else SILENT_MODEL
    arguments = {
        "prompt": shot["resolved_prompt"],
        "duration": f"{GEN_SECONDS}s",
        "aspect_ratio": aspect,
        "generate_audio": shot["audio"] == "dialogue",
        "negative_prompt": NEGATIVE,
    }
    if shot.get("seed") is not None:
        arguments["seed"] = shot["seed"]

    def on_update(update):
        if verbose and getattr(update, "logs", None):
            for entry in update.logs:
                print(f"  [{shot['id']}] {entry.get('message','')}", flush=True)

    result = fal_client.subscribe(
        model, arguments=arguments, with_logs=verbose, on_queue_update=on_update
    )
    url = find_video_url(result)
    if not url:
        raise RuntimeError(f"no video url in result for {shot['id']}: {result!r}")

    dest = dest_for(shot)
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    (dest.with_suffix(".json")).write_text(
        json.dumps({"shot": shot["id"], "model": model, "url": url,
                    "arguments": arguments}, indent=2),
        encoding="utf-8",
    )
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--storyboard", default=str(HERE / "storyboard.json"))
    ap.add_argument("--shots", help="comma-separated shot ids, e.g. 06,07")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--force", action="store_true",
                    help="regenerate shots that already have a file")
    ap.add_argument("--go", action="store_true",
                    help="actually spend credits; without it this is a dry run")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    board = load_storyboard(args.storyboard)
    shots = board["shots"]
    if args.shots:
        wanted = {s.strip() for s in args.shots.split(",")}
        shots = [s for s in shots if s["id"] in wanted]
        missing = wanted - {s["id"] for s in shots}
        if missing:
            sys.exit(f"unknown shot ids: {', '.join(sorted(missing))}")
    if not args.force:
        shots = [s for s in shots if not dest_for(s).exists()]

    if not shots:
        print("Nothing to generate. Use --force to redo existing shots.")
        return

    print(f"{len(shots)} shot(s) to generate, {GEN_SECONDS}s each")
    for shot in shots:
        mark = "SPEECH" if shot["audio"] == "dialogue" else "silent"
        print(f"  {shot['id']} {shot['slug']:<16} "
              f"{shot['tin']:>5.1f}-{shot['tout']:<5.1f} ({shot['seconds']:.1f}s)  {mark}")
    print(f"\nRough estimate: ~${len(shots) * EST_USD_PER_CLIP:.2f} "
          f"(verify EST_USD_PER_CLIP against fal's pricing)")

    if not args.go:
        print("\nDry run. Re-run with --go to generate.")
        return

    if not os.environ.get("FAL_KEY"):
        sys.exit("FAL_KEY is not set. export FAL_KEY=... and retry.")

    OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(generate, s, args.aspect, args.verbose): s for s in shots}
        for future in as_completed(futures):
            shot = futures[future]
            try:
                path = future.result()
                print(f"OK   {shot['id']} {shot['slug']} -> {path.name}", flush=True)
            except Exception as exc:
                failures.append(shot["id"])
                print(f"FAIL {shot['id']} {shot['slug']}: {exc}", file=sys.stderr, flush=True)

    if failures:
        sys.exit(f"\n{len(failures)} shot(s) failed: {', '.join(sorted(failures))}\n"
                 f"Retry just those with --shots {','.join(sorted(failures))}")
    print(f"\nAll shots in {OUT}. Next: python3 assemble.py")


if __name__ == "__main__":
    main()
