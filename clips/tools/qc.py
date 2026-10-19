#!/usr/bin/env python3
"""Post-production quality control for a clip. Run AFTER rendering, on the actual output files.

Usage:
  python3 -I clips/tools/qc.py cuts     --src master.mp4 --cutlist cutlist.json --face face.mp4 --meta face.json --out qc_dir
  python3 -I clips/tools/qc.py flash    --video final.mp4 --out qc_dir [--region x,y,w,h]
  python3 -I clips/tools/qc.py silence  --video final.mp4 [--max 0.25] [--noise -35]
  python3 -I clips/tools/qc.py duration --video final.mp4 [--min 60] [--max 90]
  python3 -I clips/tools/qc.py loudness --video final.mp4
  python3 -I clips/tools/qc.py sheet    --video final.mp4 --cutlist cutlist.json --out qc_dir [--region x,y,w,h]
  python3 -I clips/tools/qc.py all      --src master.mp4 --cutlist cutlist.json --face face.mp4 --meta face.json --video final.mp4 --out qc_dir

Checks:
  cuts     At every cut, the last rendered frame before the cut must match the planned last source
           frame, and the first frame after the cut must match the planned first source frame of the
           next sub-clip, never the first removed frame. Compared with SSIM after applying the same
           crop/scale to the source frames.
  flash    Any single frame that differs strongly from BOTH neighbours while the neighbours match
           each other is an orphan frame (a leaked frame from another shot). Reported with timecodes.
  silence  No pause longer than --max seconds in the audio (ffmpeg silencedetect).
  duration Length within [min, max].
  loudness Integrated LUFS and true peak (EBU R128) for the delivery check.
  sheet    Contact sheet of 3 frames before / 3 frames after every cut for a human eye check.
A JSON report and a markdown summary are written to --out.
"""
import argparse, json, math, os, re, subprocess, sys
from fractions import Fraction


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True)
    j = json.loads(out.stdout)
    st = j["streams"][0]
    return {"w": int(st["width"]), "h": int(st["height"]), "fps": Fraction(st["r_frame_rate"]),
            "duration": float(j["format"]["duration"])}


def grab_frames(path, frame_indices, fps, region=None, scale=None, gray=True):
    """Decode exact frames by index: seek to a frame boundary shortly before the first wanted
    frame (accurate seek), then select by frame number relative to that point."""
    import numpy as np, cv2
    if not frame_indices:
        return {}
    idx = sorted(set(i for i in frame_indices if i >= 0))
    first = max(0, idx[0] - 30) if idx[0] > 3000 else 0   # short files: decode from 0, exact by index
    seek = first / float(fps)
    expr = "+".join(f"eq(n\\,{i - first})" for i in idx)
    vf = f"select='{expr}'"
    if region:
        x, y, w, h = region
        vf += f",crop={w}:{h}:{x}:{y}"
    if scale:
        vf += f",scale={scale[0]}:{scale[1]}:flags=lanczos"
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{seek:.6f}", "-i", path, "-vf", vf, "-vsync", "0",
           "-frames:v", str(len(idx)), "-f", "image2pipe", "-vcodec", "png", "-"]
    p = subprocess.run(cmd, capture_output=True, check=True)
    data = p.stdout
    frames, pos = [], 0
    sig = b"\x89PNG\r\n\x1a\n"
    while True:
        i = data.find(sig, pos)
        if i < 0:
            break
        j = data.find(sig, i + 8)
        chunk = data[i:j if j > 0 else len(data)]
        img = cv2.imdecode(np.frombuffer(chunk, np.uint8), cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)
        if img is not None:
            frames.append(img)
        pos = i + 8
    return dict(zip(idx, frames))


def ssim(a, b):
    from skimage.metrics import structural_similarity
    import cv2
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    return float(structural_similarity(a, b, data_range=255))


def check_cuts(src, cutlist, face, meta, out_dir):
    cl = json.load(open(cutlist))
    m = json.load(open(meta))
    crop = m["crop"]
    ow, oh = m["out_size"]
    finfo = probe(face)
    region = (crop["x"], crop["y"], crop["w"], crop["h"])
    small = (ow // 4, oh // 4)
    clips = {c["i"]: c for c in cl["clips"]}
    # group wanted source frames by source file
    wanted = {}
    for c in cl["cuts"]:
        fa = clips[c["a_clip"]].get("file") or src
        fb = clips[c["b_clip"]].get("file") or src
        wanted.setdefault(fa, set()).update([c["a_last_src_f"], c["a_last_src_f"] + 1])
        wanted.setdefault(fb, set()).add(c["b_first_src_f"])
    S = {}
    for f, idx in wanted.items():
        S[f] = grab_frames(f, sorted(idx), probe(f)["fps"], region=region, scale=small)
    face_idx = []
    for c in cl["cuts"]:
        face_idx += [c["tl_frame"] - 1, c["tl_frame"]]
    F = grab_frames(face, face_idx, finfo["fps"], scale=small)
    results, fails = [], 0
    for c in cl["cuts"]:
        fa = clips[c["a_clip"]].get("file") or src
        fb = clips[c["b_clip"]].get("file") or src
        a_last, leaked = S[fa].get(c["a_last_src_f"]), S[fa].get(c["a_last_src_f"] + 1)
        b_first = S[fb].get(c["b_first_src_f"])
        f_before, f_after = F.get(c["tl_frame"] - 1), F.get(c["tl_frame"])
        if any(v is None for v in (a_last, b_first, f_before, f_after)):
            results.append({"cut": c["tl"], "status": "ERROR", "reason": "frame extraction failed"})
            fails += 1
            continue
        s_before = ssim(f_before, a_last)
        s_after = ssim(f_after, b_first)
        s_leak = ssim(f_after, leaked) if leaked is not None else 0.0
        ok = s_before > 0.9 and s_after > 0.9 and s_after >= s_leak
        if not ok:
            fails += 1
        results.append({"cut": c["tl"], "tl_frame": c["tl_frame"], "ssim_before": round(s_before, 3),
                        "ssim_after": round(s_after, 3), "ssim_after_vs_removed": round(s_leak, 3),
                        "status": "PASS" if ok else "FAIL"})
    rep = {"check": "cuts", "n_cuts": len(cl["cuts"]), "fails": fails, "results": results,
           "status": "PASS" if fails == 0 else "FAIL"}
    print(f"cuts: {len(cl['cuts'])} checked, {fails} failed -> {rep['status']}")
    return rep


def check_flash(video, out_dir, region=None):
    import numpy as np
    info = probe(video)
    vf = []
    if region:
        x, y, w, h = region
        vf.append(f"crop={w}:{h}:{x}:{y}")
    vf.append("scale=64:-2:flags=area,format=gray")
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True, check=True)
    # derive frame size from the first bytes: width 64, height from region aspect
    w = 64
    h = len(p.stdout) // (w * max(1, round(info["duration"] * float(info["fps"]))))
    # robust: recompute height from aspect
    aspect = (region[3] / region[2]) if region else (info["h"] / info["w"])
    h = int(round(64 * aspect / 2) * 2)
    n = len(p.stdout) // (w * h)
    frames = np.frombuffer(p.stdout[: n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)
    d = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))  # d[i] = |F[i+1]-F[i]|
    med = float(np.median(d)) if len(d) else 0.0
    thr = max(6.0, 6.0 * med)
    flashes = []
    for i in range(1, n - 1):
        d_in, d_out = d[i - 1], d[i]
        if d_in > thr and d_out > thr:
            d_skip = float(np.abs(frames[i + 1] - frames[i - 1]).mean())
            if d_skip < max(3.0, 0.4 * min(d_in, d_out)):
                flashes.append({"frame": i, "t": round(i / float(info["fps"]), 3), "d_in": round(float(d_in), 1),
                                "d_out": round(float(d_out), 1), "neighbours": round(d_skip, 1)})
    rep = {"check": "flash", "frames": n, "median_diff": round(med, 2), "threshold": round(thr, 2),
           "flash_frames": flashes, "status": "PASS" if not flashes else "FAIL"}
    print(f"flash: {n} frames, {len(flashes)} orphan frame(s) -> {rep['status']}")
    return rep


def check_silence(video, max_s=0.25, noise=-35):
    p = subprocess.run(["ffmpeg", "-v", "info", "-i", video, "-af", f"silencedetect=noise={noise}dB:d={max_s}", "-f", "null", "-"],
                       capture_output=True, text=True)
    log = p.stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    durs = [float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", log)]
    sil = [{"start": round(s, 3), "duration": round(d, 3)} for s, d in zip(starts, durs)]
    info = probe(video)
    # ignore a trailing silence shorter than 0.6 s at the very end (tail of the render)
    sil = [s for s in sil if not (s["start"] + s["duration"] >= info["duration"] - 0.05 and s["duration"] < 0.6)]
    rep = {"check": "silence", "max_allowed": max_s, "noise_floor_db": noise, "pauses": sil,
           "status": "PASS" if not sil else "FAIL"}
    print(f"silence: {len(sil)} pause(s) > {max_s}s -> {rep['status']}")
    return rep


def check_duration(video, lo=60, hi=90):
    d = probe(video)["duration"]
    rep = {"check": "duration", "seconds": round(d, 2), "min": lo, "max": hi, "status": "PASS" if lo <= d <= hi else "FAIL"}
    print(f"duration: {d:.2f}s -> {rep['status']}")
    return rep


def check_loudness(video):
    p = subprocess.run(["ffmpeg", "-v", "info", "-i", video, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    log = p.stderr
    I = re.findall(r"I:\s+(-?[0-9.]+) LUFS", log)
    tp = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", log)
    lra = re.findall(r"LRA:\s+(-?[0-9.]+) LU", log)
    rep = {"check": "loudness", "integrated_lufs": float(I[-1]) if I else None, "true_peak_dbtp": float(tp[-1]) if tp else None,
           "lra": float(lra[-1]) if lra else None}
    rep["status"] = "PASS" if rep["integrated_lufs"] is not None and -18 <= rep["integrated_lufs"] <= -12 and (rep["true_peak_dbtp"] or 0) <= -1.0 else "WARN"
    print(f"loudness: {rep['integrated_lufs']} LUFS, peak {rep['true_peak_dbtp']} dBTP -> {rep['status']}")
    return rep


def make_sheet(video, cutlist, out_dir, region=None):
    import numpy as np, cv2
    cl = json.load(open(cutlist))
    info = probe(video)
    idx = []
    for c in cl["cuts"]:
        idx += [c["tl_frame"] + k for k in range(-3, 3)]
    idx = [i for i in idx if 0 <= i]
    small = (180, int(180 * ((region[3] / region[2]) if region else info["h"] / info["w"])))
    F = grab_frames(video, idx, info["fps"], region=region, scale=small, gray=False)
    rows = []
    for c in cl["cuts"]:
        tiles = []
        for k in range(-3, 3):
            f = F.get(c["tl_frame"] + k)
            if f is None:
                f = np.zeros((small[1], small[0], 3), np.uint8)
            f = f.copy()
            color = (0, 0, 255) if k == 0 else (255, 255, 255)
            cv2.putText(f, f"{'+' if k >= 0 else ''}{k}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            if k == 0:
                cv2.rectangle(f, (0, 0), (small[0] - 1, small[1] - 1), (0, 0, 255), 3)
            tiles.append(f)
        row = np.concatenate(tiles, axis=1)
        cv2.putText(row, f"cut @ {c['tl']:.3f}s", (6, small[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        rows.append(row)
    if rows:
        sheet = np.concatenate(rows, axis=0)
        path = os.path.join(out_dir, "cuts_sheet.png")
        cv2.imwrite(path, sheet)
        print(f"sheet: {len(rows)} cuts -> {path}")
        return {"check": "sheet", "path": path, "status": "INFO"}
    return {"check": "sheet", "status": "INFO", "path": None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cuts", "flash", "silence", "duration", "loudness", "sheet", "all"])
    ap.add_argument("--src"); ap.add_argument("--cutlist"); ap.add_argument("--face"); ap.add_argument("--meta")
    ap.add_argument("--video"); ap.add_argument("--out", default="qc")
    ap.add_argument("--region", help="x,y,w,h of the talking-head area inside the final frame")
    ap.add_argument("--max", type=float, default=0.25); ap.add_argument("--noise", type=float, default=-35)
    ap.add_argument("--min-dur", type=float, default=60); ap.add_argument("--max-dur", type=float, default=90)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    region = tuple(int(v) for v in a.region.split(",")) if a.region else None
    reps = []
    if a.cmd in ("cuts", "all") and a.face:
        reps.append(check_cuts(a.src, a.cutlist, a.face, a.meta, a.out))
    if a.cmd in ("flash", "all"):
        reps.append(check_flash(a.video or a.face, a.out, region))
    if a.cmd in ("silence", "all"):
        reps.append(check_silence(a.video or a.face, a.max, a.noise))
    if a.cmd in ("duration", "all"):
        reps.append(check_duration(a.video or a.face, a.min_dur, a.max_dur))
    if a.cmd in ("loudness", "all"):
        reps.append(check_loudness(a.video or a.face))
    if a.cmd in ("sheet", "all") and a.cutlist:
        reps.append(make_sheet(a.video or a.face, a.cutlist, a.out, region))
    overall = "FAIL" if any(r["status"] == "FAIL" for r in reps) else "PASS"
    report = {"status": overall, "checks": reps}
    json.dump(report, open(os.path.join(a.out, "qc_report.json"), "w"), indent=1, ensure_ascii=False)
    with open(os.path.join(a.out, "qc_report.md"), "w") as f:
        f.write(f"# QC report: {overall}\n\n")
        for r in reps:
            f.write(f"- **{r['check']}**: {r['status']}" + (f" ({r.get('fails', 0)} failed cuts)" if r['check'] == 'cuts' else "") + "\n")
            if r["check"] == "silence" and r["pauses"]:
                for s in r["pauses"]:
                    f.write(f"  - pause at {s['start']}s for {s['duration']}s\n")
            if r["check"] == "flash" and r["flash_frames"]:
                for s in r["flash_frames"]:
                    f.write(f"  - orphan frame {s['frame']} at {s['t']}s\n")
            if r["check"] == "cuts":
                for s in r["results"]:
                    if s["status"] != "PASS":
                        f.write(f"  - cut at {s['cut']}s: {s}\n")
    print(f"QC {overall} -> {a.out}/qc_report.md")
    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()
