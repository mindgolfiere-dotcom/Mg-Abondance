#!/usr/bin/env python3
"""Locate each scripted segment in the master transcript and extract a lossless, all-intra,
constant-frame-rate mezzanine for it (PCM audio, timestamps from zero). Downstream tools then
work by exact frame index on these short files, which removes every seek ambiguity.

Usage: python3 -I clips/tools/locate_segments.py --src master.mp4 --words master_words.json \
          --spec spec.json --out-dir seg_dir [--margin 1.5] [--transcribe]

Writes seg_dir/segments.json: [{id, file, master_in, master_out, words}] and, with --transcribe,
runs transcribe.py on each mezzanine so the words are aligned to the mezzanine itself.
"""
import argparse, json, os, subprocess, sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_cutlist import tokenize_words, find_anchor, norm_tokens  # noqa: E402


def probe_fps(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return Fraction(out.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--margin", type=float, default=1.5)
    ap.add_argument("--transcribe", action="store_true")
    ap.add_argument("--model", default="large-v3-turbo")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    W = json.load(open(a.words))
    words = W["words"]
    spec = json.load(open(a.spec))
    fps = probe_fps(a.src)
    toks, owner = tokenize_words(words)
    segs, cursor = [], 0
    for seg in spec["segments"]:
        sid = seg["id"]
        if "src_in" in seg:
            t_in, t_out = float(seg["src_in"]), float(seg["src_out"])
        else:
            i0, _, r0, after = find_anchor(toks, owner, seg["start"], cursor)
            _, i1, r1, after_end = find_anchor(toks, owner, seg["end"], after - len(norm_tokens(seg["start"])))
            cursor = 0 if seg.get("rewind") else after_end
            t_in, t_out = words[i0]["s"], words[i1]["e"]
            print(f"{sid}: {t_in:.2f}s -> {t_out:.2f}s on master (anchor matches {r0:.2f}/{r1:.2f}) "
                  f"| {' '.join(w['w'] for w in words[i0:i0+6])} ... {' '.join(w['w'] for w in words[max(i0, i1-5):i1+1])}")
        m_in = max(0.0, t_in - a.margin)
        m_out = t_out + a.margin
        # snap the start to the frame grid so the mezzanine frame 0 is a real master frame
        f_in = int(m_in * fps)
        m_in = f_in / float(fps)
        out = os.path.join(a.out_dir, f"{sid}.mov")
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{m_in:.6f}", "-i", a.src, "-t", f"{m_out - m_in:.6f}",
               "-vf", "setpts=PTS-STARTPTS", "-af", "asetpts=PTS-STARTPTS,aresample=48000",
               "-r", str(fps), "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-g", "1",
               "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-video_track_timescale", "90000", out]
        subprocess.run(cmd, check=True)
        entry = {"id": sid, "file": out, "master_in": round(m_in, 4), "master_out": round(m_out, 4), "fps": str(fps)}
        if a.transcribe:
            wpath = os.path.join(a.out_dir, f"{sid}_words.json")
            subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcribe.py"),
                            out, wpath, "--model", a.model], check=True)
            entry["words"] = wpath
        segs.append(entry)
        print(f"  mezzanine {out} ({m_out - m_in:.2f}s)")
    json.dump({"src": a.src, "fps": str(fps), "segments": segs}, open(os.path.join(a.out_dir, "segments.json"), "w"), indent=1)
    print(f"{len(segs)} segment(s) -> {os.path.join(a.out_dir, 'segments.json')}")


if __name__ == "__main__":
    main()
