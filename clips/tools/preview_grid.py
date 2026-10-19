#!/usr/bin/env python3
"""Contact sheet of a rendered clip for a visual review: one frame every N seconds, tiled.
Usage: python3 -I clips/tools/preview_grid.py video.mp4 out.png [--every 3] [--cols 6] [--width 270] [--times t1,t2,...]"""
import argparse, subprocess, os, tempfile
from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--every", type=float, default=3.0); ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--width", type=int, default=270); ap.add_argument("--times", default="")
    a = ap.parse_args()
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", a.video],
                               capture_output=True, text=True).stdout.strip())
    times = [float(t) for t in a.times.split(",") if t] if a.times else [round(t * a.every, 3) for t in range(int(dur / a.every) + 1)]
    tmp = tempfile.mkdtemp()
    frames = []
    for i, t in enumerate(times):
        f = os.path.join(tmp, f"f{i:03d}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", a.video, "-frames:v", "1", f], check=True)
        if os.path.exists(f):
            frames.append((t, f))
    if not frames:
        raise SystemExit("no frames")
    im0 = Image.open(frames[0][1]); w = a.width; h = round(im0.height * w / im0.width)
    cols = a.cols; rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + 18)), (30, 30, 30)); d = ImageDraw.Draw(sheet)
    for k, (t, f) in enumerate(frames):
        im = Image.open(f).resize((w, h)); x, y = (k % cols) * w, (k // cols) * (h + 18)
        sheet.paste(im, (x, y + 18)); d.text((x + 4, y + 2), f"{t:.1f}s", fill=(255, 255, 255))
    sheet.save(a.out); print(f"{len(frames)} frames -> {a.out} ({sheet.size[0]}x{sheet.size[1]})")


if __name__ == "__main__":
    main()
