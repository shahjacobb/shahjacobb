#!/usr/bin/env python3
"""
"Before Morning" — two-stage generator.

Stage 1 (refs):  text-to-image  -> one locked reference frame per shot
Stage 2 (video): image-to-video -> animate each reference frame

Continuity comes from stage 1. Approve every reference frame by eye before
running stage 2; regenerating a bad video costs far more than regenerating a
bad still.

    export FAL_KEY=...            # never commit this
    pip install fal-client
    python generate.py --stage refs
    python generate.py --stage refs --shots 03_coat --seed 12345
    python generate.py --stage video
"""

import argparse
import json
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).parent
SPEC = ROOT / "shots.json"
OUT = ROOT / "out"


def load_spec():
    with open(SPEC) as f:
        return json.load(f)


def assemble(shot, key, locks):
    """Build the full prompt: lock blocks first, then the shot body, then style
    and continuity. Locks are prepended as labelled blocks rather than spliced
    inline — a multi-sentence description dropped into the middle of a sentence
    reads as broken grammar and the model drifts."""
    blocks = [locks[name] for name in shot.get("locks", [])]
    blocks.append(shot[key])
    blocks.append(locks["photography"])
    blocks.append(locks["continuity"])
    return "\n\n".join(blocks)


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def on_queue(update):
    for log in getattr(update, "logs", None) or []:
        print("   ", log.get("message", ""), flush=True)


def run_refs(spec, shots, args, client):
    locks = spec["locks"]
    endpoint = spec["endpoints"]["reference_frame"]
    for shot in shots:
        dest = OUT / "refs" / f"{shot['id']}.jpg"
        if dest.exists() and not args.force:
            print(f"[skip] {shot['id']} — ref exists (use --force to redo)")
            continue
        prompt = assemble(shot, "reference_frame_prompt", locks)
        payload = {
            "prompt": prompt,
            "negative_prompt": locks["negative"],
            "aspect_ratio": spec["defaults"]["aspect_ratio"],
            "num_images": args.variants,
            "enable_safety_checker": True,
        }
        if args.seed is not None:
            payload["seed"] = args.seed
        print(f"[refs] {shot['id']} — {shot['title']}")
        if args.dry_run:
            print(json.dumps(payload, indent=2)[:600] + "\n")
            continue
        result = client.subscribe(endpoint, arguments=payload,
                                  with_logs=True, on_queue_update=on_queue)
        for i, img in enumerate(result["images"]):
            target = dest if i == 0 else dest.with_name(f"{shot['id']}_v{i+1}.jpg")
            print("   ->", download(img["url"], target))


def run_video(spec, shots, args, client):
    locks = spec["locks"]
    endpoint = spec["endpoints"]["image_to_video"]
    for shot in shots:
        ref = OUT / "refs" / f"{shot['id']}.jpg"
        dest = OUT / "video" / f"{shot['id']}.mp4"
        if not ref.exists() and not args.dry_run:
            print(f"[warn] {shot['id']} — no approved reference frame, skipping")
            continue
        if dest.exists() and not args.force:
            print(f"[skip] {shot['id']} — video exists (use --force to redo)")
            continue
        if args.ref_url_prefix:
            image_url = args.ref_url_prefix + ref.name
        elif args.dry_run:
            image_url = f"<uploaded at runtime: {ref}>"
        else:
            image_url = client.upload_file(str(ref))
        payload = {
            "prompt": assemble(shot, "video_prompt", locks),
            "image_url": image_url,
            "duration": shot["duration"],
            "resolution": spec["defaults"]["resolution"],
            "prompt_optimizer": False,
        }
        print(f"[video] {shot['id']} — {shot['title']} ({shot['duration']}s)")
        if args.dry_run:
            print(json.dumps(payload, indent=2)[:600] + "\n")
            continue
        result = client.subscribe(endpoint, arguments=payload,
                                  with_logs=True, on_queue_update=on_queue)
        print("   ->", download(result["video"]["url"], dest))


def main():
    p = argparse.ArgumentParser(description='"Before Morning" generator')
    p.add_argument("--stage", choices=["refs", "video", "all"], default="refs")
    p.add_argument("--shots", nargs="*", help="shot ids; default all")
    p.add_argument("--seed", type=int, help="fixed seed — reuse across shots for face consistency")
    p.add_argument("--variants", type=int, default=3, help="reference frames per shot")
    p.add_argument("--force", action="store_true", help="regenerate existing outputs")
    p.add_argument("--dry-run", action="store_true", help="print payloads, call nothing")
    p.add_argument("--ref-url-prefix", default="", help="serve refs from a URL instead of uploading")
    args = p.parse_args()

    spec = load_spec()
    shots = spec["shots"]
    if args.shots:
        wanted = set(args.shots)
        shots = [s for s in shots if s["id"] in wanted]
        unknown = wanted - {s["id"] for s in shots}
        if unknown:
            raise SystemExit(f"unknown shot id(s): {sorted(unknown)}")

    client = None
    if not args.dry_run:
        if not os.environ.get("FAL_KEY"):
            raise SystemExit("FAL_KEY is not set. export FAL_KEY=... and retry "
                             "(or use --dry-run to inspect the payloads).")
        try:
            import fal_client
        except ImportError:
            raise SystemExit("pip install fal-client")
        client = fal_client

    if args.stage in ("refs", "all"):
        run_refs(spec, shots, args, client)
    if args.stage in ("video", "all"):
        run_video(spec, shots, args, client)


if __name__ == "__main__":
    sys.exit(main())
