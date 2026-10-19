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
from difflib import SequenceMatcher


def find_all_anchor(toks, owner, phrase, min_ratio=0.72):
    """Every position where the phrase matches (fuzzy), as (first_word_idx, ratio, tok_pos)."""
    a = norm_tokens(phrase)
    n = len(a)
    joined = " ".join(a)
    hits = []
    for i in range(0, max(0, len(toks) - n + 1)):
        r = SequenceMatcher(None, joined, " ".join(toks[i:i + n])).ratio()
        if r >= min_ratio:
            hits.append((owner[i], r, i))
    # collapse neighbouring positions into one hit (keep the best)
    out = []
    for h in hits:
        if out and h[2] - out[-1][2] <= n:
            if h[1] > out[-1][1]:
                out[-1] = h
        else:
            out.append(h)
    return out


def best_take(words, toks, owner, seg):
    """Rushes contain retakes: pick the occurrence whose text is closest to the expected wording
    (the cut used in the published video); ties go to the latest take."""
    starts = find_all_anchor(toks, owner, seg["start"])
    if not starts:
        raise SystemExit(f"{seg['id']}: start anchor not found: {seg['start']!r}")
    expected = " ".join(norm_tokens(seg.get("expected", "")))
    cands = []
    for i0, r0, tpos in starts:
        try:
            _, i1, r1, _ = find_anchor(toks, owner, seg["end"], tpos)
        except SystemExit:
            continue
        if i1 < i0 or words[i1]["e"] - words[i0]["s"] > 4 * max(5.0, len(expected.split()) * 0.4 + 5):
            continue
        text = " ".join(norm_tokens(" ".join(w["w"] for w in words[i0:i1 + 1])))
        score = SequenceMatcher(None, expected, text).ratio() if expected else (r0 + r1) / 2
        cands.append((score, i0, i1, r0, r1))
    if not cands:
        raise SystemExit(f"{seg['id']}: no window found between {seg['start']!r} and {seg['end']!r}")
    cands.sort(key=lambda c: (round(c[0], 2), c[1]))   # best score, then latest take
    best = cands[-1]
    print(f"{seg['id']}: {len(cands)} take(s) " + ", ".join(f"[{words[c[1]]['s']:.0f}s score {c[0]:.2f}]" for c in cands) + f" -> chosen {words[best[1]]['s']:.1f}s")
    return best[1], best[2], best[3], best[4]



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
    ap.add_argument("--takes", action="store_true", help="rush mode: choose the best take per segment using 'expected' text")
    ap.add_argument("--fps", default="", help="output frame rate of the mezzanines (default: the source's), e.g. 30 for a 60 fps rush")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    W = json.load(open(a.words))
    words = W["words"]
    spec = json.load(open(a.spec))
    src_fps = probe_fps(a.src)
    fps = Fraction(a.fps) if a.fps else src_fps
    toks, owner = tokenize_words(words)
    segs, cursor = [], 0
    for seg in spec["segments"]:
        sid = seg["id"]
        if "src_in" in seg:
            t_in, t_out = float(seg["src_in"]), float(seg["src_out"])
        elif seg.get("expected") or a.takes:
            i0, i1, r0, r1 = best_take(words, toks, owner, seg)
            t_in, t_out = words[i0]["s"], words[i1]["e"]
        else:
            i0, _, r0, after = find_anchor(toks, owner, seg["start"], cursor)
            _, i1, r1, after_end = find_anchor(toks, owner, seg["end"], after - len(norm_tokens(seg["start"])))
            cursor = 0 if seg.get("rewind") else after_end
            t_in, t_out = words[i0]["s"], words[i1]["e"]
            print(f"{sid}: {t_in:.2f}s -> {t_out:.2f}s on master (anchor matches {r0:.2f}/{r1:.2f}) "
                  f"| {' '.join(w['w'] for w in words[i0:i0+6])} ... {' '.join(w['w'] for w in words[max(i0, i1-5):i1+1])}")
        m_in = max(0.0, t_in - a.margin)
        m_out = t_out + a.margin
        # snap the start to the source frame grid so the mezzanine frame 0 is a real master frame
        f_in = int(m_in * src_fps)
        m_in = f_in / float(src_fps)
        out = os.path.join(a.out_dir, f"{sid}.mov")
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{m_in:.6f}", "-i", a.src, "-t", f"{m_out - m_in:.6f}",
               "-vf", "setpts=PTS-STARTPTS", "-af", "asetpts=PTS-STARTPTS,aresample=48000",
               "-r", str(fps), "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-g", "1",
               "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-video_track_timescale", "90000", out]
        subprocess.run(cmd, check=True)
        entry = {"id": sid, "file": out, "master_in": round(m_in, 4), "master_out": round(m_out, 4), "fps": str(fps)}
        if a.transcribe:
            wpath = os.path.join(a.out_dir, f"{sid}_words.json")
            tools = os.path.dirname(os.path.abspath(__file__))
            cmd_t = [sys.executable, "-I", os.path.join(tools, "transcribe.py"), out, wpath, "--model", a.model]
            if os.path.exists(os.path.join(tools, "glossary.json")):
                cmd_t += ["--glossary", os.path.join(tools, "glossary.json")]
            subprocess.run(cmd_t, check=True)
            entry["words"] = wpath
        segs.append(entry)
        print(f"  mezzanine {out} ({m_out - m_in:.2f}s)")
    json.dump({"src": a.src, "fps": str(fps), "segments": segs}, open(os.path.join(a.out_dir, "segments.json"), "w"), indent=1)
    print(f"{len(segs)} segment(s) -> {os.path.join(a.out_dir, 'segments.json')}")


if __name__ == "__main__":
    main()
