#!/usr/bin/env python3
"""Cut the generated shots into the finished film.

Trims each clip to its storyboard slot, hard-cuts them together (no
dissolves - the 06/07 match cut depends on a hard cut), lays the music bed
under the dialogue and opens it up at 0:23, and appends the end card.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SHOTS = HERE / "out" / "shots"
NORM = HERE / "out" / "norm"
FINAL = HERE / "out" / "film.mp4"

W, H = 1920, 1080

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

# Music level over the timeline: held down under the cabin dialogue, ramped
# up across the arrivals handoff, wide open once she is in the car.
# Every audio input is forced to a common format before amix - otherwise the
# mix silently inherits the music file's layout and a mono track yields a mono
# master.
AFMT = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"

MUSIC_VOLUME = (
    "'if(lt(t,14),0.18,"
    "if(lt(t,23),0.18+(t-14)/9*0.72,0.9))'"
)


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)}\n\n{proc.stderr[-3000:]}")
    return proc


def find_font():
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def load_shots(path):
    board = json.loads(Path(path).read_text(encoding="utf-8"))
    for shot in board["shots"]:
        shot["seconds"] = round(shot["tout"] - shot["tin"], 3)
        shot.setdefault("src_in", 0.0)
    return board


def normalise(shot):
    """Trim to the slot and force uniform codec params so concat is safe."""
    src = SHOTS / f"{shot['id']}_{shot['slug']}.mp4"
    if not src.exists():
        sys.exit(f"missing shot {shot['id']} ({src.name}). Run generate.py first.")
    dst = NORM / f"{shot['id']}.mp4"
    run([
        "ffmpeg", "-y",
        "-ss", str(shot["src_in"]), "-i", str(src),
        "-t", str(shot["seconds"]),
        "-vf", (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1"),
        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-pix_fmt", "yuv420p", str(dst),
    ])
    return dst


def extract_dialogue(shot):
    src = SHOTS / f"{shot['id']}_{shot['slug']}.mp4"
    dst = NORM / f"{shot['id']}.wav"
    proc = subprocess.run([
        "ffmpeg", "-y", "-ss", str(shot["src_in"]), "-i", str(src),
        "-t", str(shot["seconds"]), "-vn",
        "-ac", "2", "-ar", "48000", str(dst),
    ], capture_output=True, text=True)
    if proc.returncode != 0 or not dst.exists():
        print(f"  note: shot {shot['id']} has no usable audio track", file=sys.stderr)
        return None
    return dst


def has_drawtext():
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                          capture_output=True, text=True)
    return " drawtext " in proc.stdout


def card_png(board, dst):
    """Render the end card with Pillow. Returns False if Pillow is absent.

    Preferred over drawtext because plenty of ffmpeg builds ship without the
    filter, and because it lets the second line be tracked out properly.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False

    font_path = find_font()
    img = Image.new("RGB", (W, H), (11, 11, 13))
    draw = ImageDraw.Draw(img)

    def load(size):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                pass
        return ImageFont.load_default()

    def centred(text, font, y, tracking=0):
        widths = [draw.textlength(ch, font=font) for ch in text]
        total = sum(widths) + tracking * max(0, len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            draw.text((x, y), ch, font=font, fill=(245, 245, 245))
            x += w + tracking

    centred(board["card"]["line1"], load(66), H / 2 - 86)
    centred(board["card"]["line2"], load(30), H / 2 + 26, tracking=5)
    img.save(dst)
    return True


def build_card(board):
    seconds = board["card"]["seconds"]
    dst = NORM / "99_card.mp4"
    png = NORM / "card.png"
    fade_out = max(0.0, seconds - 0.7)

    if card_png(board, png):
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(png), "-t", str(seconds),
             "-vf", (f"fps=24,setsar=1,fade=t=in:st=0.2:d=0.6,"
                     f"fade=t=out:st={fade_out}:d=0.6"),
             "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
             "-pix_fmt", "yuv420p", str(dst)])
        return dst

    font = find_font()
    if font and has_drawtext():
        line1, line2 = board["card"]["line1"], board["card"]["line2"]
        draw = (
            f"drawtext=fontfile='{font}':text='{line1}':fontcolor=white:fontsize=64:"
            f"x=(w-text_w)/2:y=(h/2)-80:alpha='min(1,max(0,(t-0.3)/0.6))',"
            f"drawtext=fontfile='{font}':text='{line2}':fontcolor=white:fontsize=34:"
            f"x=(w-text_w)/2:y=(h/2)+20:alpha='min(1,max(0,(t-0.9)/0.6))'"
        )
    else:
        print("  note: no Pillow and no drawtext filter - card will be blank.\n"
              "        pip install Pillow to get the end card.", file=sys.stderr)
        draw = "null"

    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"color=c=0x0B0B0D:s={W}x{H}:d={seconds}:r=24",
         "-vf", draw, "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-pix_fmt", "yuv420p", str(dst)])
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--storyboard", default=str(HERE / "storyboard.json"))
    ap.add_argument("--music", help="path to the 'New Romance' track")
    ap.add_argument("--out", default=str(FINAL))
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH. Install it (brew install ffmpeg).")

    board = load_shots(args.storyboard)
    NORM.mkdir(parents=True, exist_ok=True)

    print("Trimming shots to their slots...")
    parts, dialogue = [], []
    for shot in board["shots"]:
        parts.append(normalise(shot))
        print(f"  {shot['id']} {shot['slug']:<16} {shot['seconds']:.1f}s")
        if shot["audio"] == "dialogue":
            wav = extract_dialogue(shot)
            if wav:
                dialogue.append((shot["tin"], wav))

    parts.append(build_card(board))

    listing = NORM / "concat.txt"
    listing.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8"
    )
    silent = NORM / "silent.mp4"
    print("Cutting picture...")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", str(silent)])

    total = board["shots"][-1]["tout"] + board["card"]["seconds"]

    if not args.music and not dialogue:
        shutil.copy(silent, args.out)
        print(f"\nDone (no audio): {args.out}")
        return

    print("Mixing audio...")
    inputs, filters, labels = ["-i", str(silent)], [], []
    idx = 1
    if args.music:
        inputs += ["-i", args.music]
        filters.append(
            f"[{idx}:a]atrim=0:{total},asetpts=N/SR/TB,{AFMT},"
            f"volume={MUSIC_VOLUME}:eval=frame[music]"
        )
        labels.append("[music]")
        idx += 1
    for tin, wav in dialogue:
        inputs += ["-i", str(wav)]
        delay = int(tin * 1000)
        filters.append(f"[{idx}:a]{AFMT},adelay={delay}|{delay},volume=1.0[d{idx}]")
        labels.append(f"[d{idx}]")
        idx += 1

    filters.append(
        f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:"
        f"dropout_transition=0,alimiter=limit=0.95[mix]"
    )
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
         "-map", "0:v", "-map", "[mix]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
         "-shortest", args.out])

    print(f"\nDone: {args.out}  ({total:.1f}s)")
    print("Check the 0:18 match cut first - that is the shot that carries the film.")


if __name__ == "__main__":
    main()
