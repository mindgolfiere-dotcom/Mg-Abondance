#!/usr/bin/env python3
"""Render the talking-head track from a master and a cut list (frame-accurate, pause-trimmed).

Usage:
  python3 -I clips/tools/render_face.py --src master.mp4 --cutlist cutlist.json --out face.mp4
      [--crop auto|x,y,w,h] [--out-size 1080x1000] [--zoom 1.25] [--headroom 0.42] [--crf 16] [--preview]

- Every sub-clip is cut on the source frame grid: input seeking half a frame before the first
  wanted frame, then exactly N frames. Sub-clips are joined with the concat filter, so no frame
  of the removed material can leak through a cut.
- Audio joints get a 6 ms fade in/out (no clicks). Nothing synthetic is inserted: the short
  pauses that remain are the speaker's own room tone.
- The crop is one fixed window (auto = OpenCV face detection on several frames, median centre),
  so the framing is stable across cuts. Punch-ins are done in the composition, not here.
Writes <out>.json next to the output: crop, fps, duration, expected frame count.
"""
import argparse, json, os, subprocess, sys
from fractions import Fraction


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True)
    j = json.loads(out.stdout)
    st = j["streams"][0]
    fps = Fraction(st["r_frame_rate"])
    return {"w": int(st["width"]), "h": int(st["height"]), "fps": fps, "duration": float(j["format"]["duration"])}


MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "face_detection_yunet_2023mar.onnx")


def detect_face_crop(src, info, cutlist, out_w, out_h, zoom, headroom, debug_png=None):
    """Fixed crop window centred on the median face position (OpenCV YuNet detector)."""
    import cv2, numpy as np
    det = None
    if os.path.exists(MODEL):
        det = cv2.FaceDetectorYN_create(MODEL, "", (320, 320), 0.6, 0.3, 5000)
    times = [c["src_in"] + 0.3 for c in cutlist["clips"][:12:2]] or [1.0]
    centers, heights, img = [], [], None
    for t in times:
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-f", "image2pipe",
                            "-vcodec", "png", "-"], capture_output=True)
        img = cv2.imdecode(np.frombuffer(p.stdout, np.uint8), cv2.IMREAD_COLOR)
        if img is None or det is None:
            continue
        h, w = img.shape[:2]
        scale = min(1.0, 640.0 / w)
        small = cv2.resize(img, (int(w * scale), int(h * scale))) if scale < 1.0 else img
        det.setInputSize((small.shape[1], small.shape[0]))
        _, faces = det.detect(small)
        if faces is None or len(faces) == 0:
            continue
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])[:4] / scale
        centers.append((x + fw / 2, y + fh / 2))
        heights.append(fh)
    if not centers:
        print("warning: no face detected, centring the crop")
        cx, cy, fh = info["w"] / 2, info["h"] * 0.45, info["h"] / 4
    else:
        cx = float(np.median([c[0] for c in centers]))
        cy = float(np.median([c[1] for c in centers]))
        fh = float(np.median(heights))
        print(f"face: {len(centers)} detections, centre ({cx:.0f},{cy:.0f}), height {fh:.0f}px")
    crop_h = min(info["h"], round((out_h / zoom) * (info["h"] / 1080)))
    crop_w = min(info["w"], round(crop_h * out_w / out_h))
    crop_h = round(crop_w * out_h / out_w)
    x = int(round(cx - crop_w / 2))
    y = int(round(cy - crop_h * headroom))
    x = max(0, min(info["w"] - crop_w, x))
    y = max(0, min(info["h"] - crop_h, y))
    crop = (x, y, crop_w, crop_h)
    if debug_png and img is not None:
        img2 = img.copy()
        cv2.rectangle(img2, (x, y), (x + crop_w, y + crop_h), (0, 0, 255), 3)
        if centers:
            cv2.circle(img2, (int(cx), int(cy)), 6, (0, 255, 0), -1)
        cv2.imwrite(debug_png, img2)
    return crop, {"face_centre": [cx, cy], "face_height": fh, "detections": len(centers)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None, help="master (only needed when the cut list has no per-clip files)")
    ap.add_argument("--cutlist", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--crop", default="auto")
    ap.add_argument("--out-size", default="1080x1000")
    ap.add_argument("--zoom", type=float, default=1.25, help="face scale relative to a 1:1 crop of a 1080p frame")
    ap.add_argument("--headroom", type=float, default=0.42, help="face centre position as a fraction of crop height")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    cl = json.load(open(args.cutlist))
    first_file = cl["clips"][0].get("file") or args.src
    info = probe(first_file)
    fps = info["fps"]
    if abs(float(fps) - cl["fps"]) > 0.01:
        print(f"WARNING: cutlist fps {cl['fps']} != source fps {float(fps):.3f}; cut frames were rounded on the wrong grid")
    out_w, out_h = map(int, args.out_size.lower().split("x"))
    if args.crop == "auto":
        crop, face = detect_face_crop(first_file, info, cl, out_w, out_h, args.zoom, args.headroom,
                                      debug_png=os.path.splitext(args.out)[0] + "_crop.png")
    else:
        crop, face = tuple(int(v) for v in args.crop.split(",")), None
    x, y, w, h = crop
    print(f"crop {w}x{h} at ({x},{y}) from {info['w']}x{info['h']} @ {float(fps):.3f} fps -> {out_w}x{out_h}")

    cmd = ["ffmpeg", "-y", "-v", "error", "-stats"]
    fc, vlabels, alabels = [], [], []
    half = 0.5 / float(fps)
    total_frames = 0
    for k, c in enumerate(cl["clips"]):
        n = c["src_out_f"] - c["src_in_f"]
        total_frames += n
        seek = max(0.0, c["src_in_f"] / float(fps) - half)
        dur = n / float(fps)
        cmd += ["-ss", f"{seek:.6f}", "-t", f"{dur:.6f}", "-i", c.get("file") or args.src]
        fade_out_st = max(0.0, dur - 0.006)
        fc.append(f"[{k}:v]setpts=PTS-STARTPTS[v{k}]")
        fc.append(f"[{k}:a]asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.006,afade=t=out:st={fade_out_st:.4f}:d=0.006[a{k}]")
        vlabels.append(f"[v{k}]")
        alabels.append(f"[a{k}]")
    n = len(cl["clips"])
    concat_in = "".join(f"{v}{a}" for v, a in zip(vlabels, alabels))
    fc.append(f"{concat_in}concat=n={n}:v=1:a=1[vc][ac]")
    if args.preview:
        pw, ph = out_w // 2, out_h // 2
        fc.append(f"[vc]crop={w}:{h}:{x}:{y},scale={pw}:{ph}:flags=bicubic,setsar=1,format=yuv420p[vo]")
    else:
        fc.append(f"[vc]crop={w}:{h}:{x}:{y},scale={out_w}:{out_h}:flags=lanczos,setsar=1,format=yuv420p[vo]")
    fc.append("[ac]aresample=48000[ao]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vo]", "-map", "[ao]",
            "-r", str(fps), "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "veryfast" if args.preview else "slow",
            "-crf", str(28 if args.preview else args.crf), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", args.out]
    print(f"{n} sub-clips, {total_frames} frames expected ({total_frames / float(fps):.2f}s)")
    subprocess.run(cmd, check=True)
    got = probe(args.out)
    nb = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                         "stream=nb_read_frames", "-of", "default=nw=1:nk=1", args.out], capture_output=True, text=True).stdout.strip()
    meta = {"src": args.src, "cutlist": args.cutlist, "crop": {"x": x, "y": y, "w": w, "h": h}, "face": face,
            "fps": str(fps), "out_size": [out_w, out_h], "expected_frames": total_frames, "rendered_frames": int(nb or 0),
            "duration": got["duration"], "zoom": args.zoom, "headroom": args.headroom}
    json.dump(meta, open(os.path.splitext(args.out)[0] + ".json", "w"), indent=1)
    ok = int(nb or 0) == total_frames
    print(f"rendered {nb} frames ({got['duration']:.2f}s) -> {args.out} | frame count {'OK' if ok else 'MISMATCH'}")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
