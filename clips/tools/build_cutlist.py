#!/usr/bin/env python3
"""Build a frame-accurate cut list from word timestamps and a selection spec.

Usage: python3 -I clips/tools/build_cutlist.py words.json spec.json cutlist.json

spec.json:
{
  "fps": 25,                 # source frame rate (ffprobe r_frame_rate)
  "max_silence": 0.25,       # hard rule: no pause longer than this survives
  "keep_silence": 0.18,      # what a long pause is shortened to (natural breath)
  "pad_in": 0.08, "pad_out": 0.12,   # room tone kept around each segment
  "segments": [
    {"id": "S1", "role": "hook", "start": "et c'est là que le subconscient", "end": "et la réalité",
     "drops": ["comme j'ai dit tout à l'heure"]},
    {"id": "S2", "role": "dev", "src_in": 512.30, "src_out": 541.02}
  ]
}
A segment is located either by anchor phrases (fuzzy-matched on the transcript) or by explicit
source seconds. "drops" are phrases removed inside the segment (treated like a long pause).

Output cutlist.json: ordered sub-clips with source in/out (seconds and frames), timeline in/out,
the kept words re-timed on the edited timeline (captions), segment boundaries, the list of
trimmed pauses, and the expected frames at every cut (used by the post-render QC).
"""
import json, os, re, subprocess, math, re, sys, unicodedata
from fractions import Fraction
from difflib import SequenceMatcher


def norm_tokens(text):
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.split()


def tokenize_words(words):
    """Return (tokens, owner) where owner[i] is the word index that produced token i."""
    toks, owner = [], []
    for i, w in enumerate(words):
        for t in norm_tokens(w["w"]):
            toks.append(t)
            owner.append(i)
    return toks, owner


def find_anchor(toks, owner, phrase, lo=0, want="start"):
    a = norm_tokens(phrase)
    n = len(a)
    if n == 0:
        raise SystemExit(f"empty anchor: {phrase!r}")
    best, best_i = -1.0, None
    joined_a = " ".join(a)
    for i in range(lo, max(lo, len(toks) - n + 1)):
        win = " ".join(toks[i:i + n])
        r = SequenceMatcher(None, joined_a, win).ratio()
        if r > best:
            best, best_i = r, i
            if r == 1.0:
                break
    if best_i is None or best < 0.6:
        raise SystemExit(f"anchor not found (best ratio {best:.2f}): {phrase!r}")
    first_word = owner[best_i]
    last_word = owner[min(best_i + n - 1, len(owner) - 1)]
    return first_word, last_word, best, best_i + n


def frames(t, fps, mode):
    f = t * fps
    return int(math.floor(f + 1e-6)) if mode == "floor" else int(math.ceil(f - 1e-6))


def load_words(path):
    W = json.load(open(path))
    words = [w for w in W["words"] if w["e"] >= w["s"] and (w["e"] - w["s"]) < 4.0]
    # Whisper splits "crois-moi" into "crois" + "-moi": glue the dash fragments back onto the previous word
    glued = []
    for w in words:
        if glued and w["w"].startswith("-") and len(w["w"]) > 1:
            glued[-1]["w"] += w["w"]
            glued[-1]["e"] = max(glued[-1]["e"], w["e"])
        else:
            glued.append(w)
    words = glued
    gpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary.json")
    if os.path.exists(gpath):
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from transcribe import apply_glossary
            words = apply_glossary(words, json.load(open(gpath)))
        except Exception as e:  # noqa: BLE001
            print(f"warning: glossary not applied ({e})")
    return words


def apply_fixes(words, fixes):
    """spec 'fixes': [["old phrase", "new phrase"], ...] applied to the segment words (first exact match,
    accent/case-insensitive). Same token count -> word by word; otherwise the first word takes the whole new text."""
    for old, new in fixes or []:
        toks, owner = tokenize_words(words)
        a = norm_tokens(old)
        for i in range(len(toks) - len(a) + 1):
            if toks[i:i + len(a)] == a:
                idx = sorted({owner[k] for k in range(i, i + len(a))})
                parts = new.split()
                if len(parts) == len(idx):
                    for j, k in enumerate(idx):
                        words[k]["w"] = parts[j]
                else:
                    # different word count: spread the new words evenly over the matched time span
                    t0, t1 = words[idx[0]]["s"], words[idx[-1]]["e"]
                    step = (t1 - t0) / len(parts)
                    repl = [{"w": pt, "s": round(t0 + j * step, 3), "e": round(t0 + (j + 1) * step, 3), "p": 1.0} for j, pt in enumerate(parts)]
                    words[idx[0]:idx[-1] + 1] = repl
                break
        else:
            print(f"  warning: fix not found: {old!r}")
    return [w for w in words if w["w"] != ""]


def audio_envelope(path, hop=0.02):
    """20 ms RMS envelope (dBFS) of the file's audio, plus a speech threshold derived from its own levels."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n = int(16000 * hop)
    nf = max(1, len(x) // n)
    fr = x[:nf * n].reshape(nf, n)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)
    floor, loud = float(np.percentile(db, 15)), float(np.percentile(db, 90))
    thr = max(floor + 10.0, loud - 24.0)
    return db, hop, thr


def integrated_loudness(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = out[out.rfind("Summary:"):]
    m = re.search(r"I:\s*(-?[0-9.]+) LUFS", tail)
    return float(m.group(1)) if m else -23.0


def silence_map(path, target_lufs=-16.0, qc_noise_db=-35.0, hop=0.005, margin_db=4.0):
    """Where the speech track will read as silent to the post-render QC: per 5 ms frame, the peak amplitude in dBFS
    is compared with the QC noise gate brought back to the mezzanine's own level (the face track is normalised to
    target_lufs later). Returns (silent_bool_array, hop)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    x = np.abs(np.frombuffer(raw, dtype=np.float32))      # interleaved L/R: the peak over both channels per frame
    n = int(16000 * hop) * 2
    nf = max(1, len(x) // n)
    peak = x[:nf * n].reshape(nf, n).max(axis=1)
    gain = target_lufs - integrated_loudness(path)
    thr_db = qc_noise_db - gain + margin_db
    silent = 20 * np.log10(peak + 1e-9) < thr_db
    return silent, hop


def split_on_silence(src_in, src_out, silent, hop, max_sil, keep, edge=0.03):
    """Cut every silent stretch longer than max_sil inside [src_in, src_out] down to keep seconds.
    Returns the list of kept (in, out) intervals, in order."""
    i0, i1 = int(src_in / hop), int(src_out / hop)
    if i1 <= i0 + 1 or i1 > len(silent):
        return [(src_in, src_out)]
    seg = silent[i0:i1]
    stretches, j = [], 0
    while j < len(seg):
        if seg[j]:
            k = j
            while k < len(seg) and seg[k]:
                k += 1
            a, b = src_in + j * hop, src_in + k * hop
            if b - a >= 0.02:
                stretches.append((a, b))
            j = k
        else:
            j += 1
    out, cur_in = [], src_in
    for a, b in stretches:
        # a boundary pause is shared with the neighbouring sub-clip, so each side keeps half of `keep`,
        # whatever the length of the silence touching the edge
        if a <= src_in + 0.12:            # leading silence: keep only its tail
            cur_in = max(cur_in, b - keep / 2)
            continue
        if b >= src_out - 0.15:           # trailing silence: keep only its head
            src_out = min(src_out, a + keep / 2)
            continue
        if b - a <= max_sil - 0.03:       # 30 ms of headroom under the rule: the final mix is gated a little differently
            continue
        out.append((cur_in, a + keep / 2))
        cur_in = b - keep / 2
    if src_out - cur_in > 0.02:
        out.append((cur_in, src_out))
    return out or [(src_in, src_out)]


def snap_to_speech(words, env, max_sil, bridge=0.08):
    """Whisper sometimes leaves untranscribed speech (a stutter, a dropped 'par') inside what looks like a pause.
    For every gap wider than max_sil, extend the neighbouring words over the voiced audio that touches them so a
    cut never lands in the middle of speech. Returns the number of adjusted boundaries."""
    import numpy as np
    db, hop, thr = env
    nb = int(round(bridge / hop))
    adjusted = 0
    def voiced(i):
        return 0 <= i < len(db) and db[i] > thr
    for a, b in zip(words, words[1:]):
        if b["s"] - a["e"] <= max_sil:
            continue
        # trailing speech glued to the end of a
        i = int(a["e"] / hop)
        last_v, run = None, 0
        j = i
        while j < len(db) and (j * hop) < b["s"]:
            if voiced(j):
                last_v, run = j, 0
            else:
                run += 1
                if run > nb:
                    break
            j += 1
        new_e = a["e"] if last_v is None else max(a["e"], (last_v + 1) * hop)
        # leading speech glued to the start of b
        i = int(b["s"] / hop) - 1
        first_v, run = None, 0
        j = i
        while j >= 0 and ((j + 1) * hop) > new_e:
            if voiced(j):
                first_v, run = j, 0
            else:
                run += 1
                if run > nb:
                    break
            j -= 1
        new_s = b["s"] if first_v is None else min(b["s"], first_v * hop)
        if new_e > a["e"] + 0.03 or new_s < b["s"] - 0.03:
            adjusted += 1
            print(f"  speech in gap after {a['w']!r} ({a['e']:.2f}s): end -> {new_e:.2f}s | before {b['w']!r} ({b['s']:.2f}s): start -> {new_s:.2f}s")
            a["e"], b["s"] = round(new_e, 3), round(new_s, 3)
    return adjusted


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    first, spec_path, out_path = sys.argv[1:4]
    spec = json.load(open(spec_path))
    first_json = json.load(open(first))
    per_segment = "segments" in first_json and "words" not in first_json
    if per_segment:
        seg_files = {s["id"]: s for s in first_json["segments"]}
        fps = float(Fraction(first_json["fps"]))
        words_path = first
        words = None
    else:
        seg_files = None
        words = load_words(first)
        words_path = first
        fps = float(spec.get("fps", 25))
    max_sil = float(spec.get("max_silence", 0.25))
    keep = float(spec.get("keep_silence", 0.18))
    pad_in = float(spec.get("pad_in", 0.08))
    pad_out = float(spec.get("pad_out", 0.12))
    toks, owner = tokenize_words(words) if words else ([], [])

    clips, out_words, segments, trimmed = [], [], [], []
    tl = 0.0
    cursor_tok = 0
    for seg in spec["segments"]:
        sid = seg["id"]
        seg_file = None
        if per_segment:
            sf = seg_files[sid]
            seg_file = sf["file"]
            words = load_words(sf["words"])
            if seg.get("fixes"):
                words = apply_fixes(words, seg["fixes"])
            try:
                snap_to_speech(words, audio_envelope(seg_file), max_sil)
            except Exception as e:  # noqa: BLE001
                print(f"  warning: speech snapping skipped for {sid} ({e})")
            toks, owner = tokenize_words(words)
            cursor_tok = 0
            if "src_in" in seg:   # explicit master times -> relative to the mezzanine
                seg = dict(seg, src_in=seg["src_in"] - sf["master_in"], src_out=seg["src_out"] - sf["master_in"])
        if "src_in" in seg:
            i0 = next(i for i, w in enumerate(words) if w["s"] >= seg["src_in"] - 0.05)
            i1 = max(i for i, w in enumerate(words) if w["e"] <= seg["src_out"] + 0.05)
        else:
            i0, _, r0, after = find_anchor(toks, owner, seg["start"], cursor_tok, "start")
            _, i1, r1, after_end = find_anchor(toks, owner, seg["end"], after - len(norm_tokens(seg["start"])), "end")
            cursor_tok = 0 if seg.get("rewind") else after_end
            print(f"{sid}: start match {r0:.2f} at word {i0} ({words[i0]['s']:.2f}s), end match {r1:.2f} at word {i1} ({words[i1]['e']:.2f}s)")
        seg_words = words[i0:i1 + 1]
        # drops: remove phrases inside the segment
        dropped = set()
        for entry in seg.get("drops", []):
            phrase, nth = (entry, 1) if isinstance(entry, str) else (entry["phrase"], int(entry.get("nth", 1)))
            st, so = tokenize_words(seg_words)
            lo, found, seen = 0, None, 0
            while True:
                try:
                    d0, d1, r, after = find_anchor(st, so, phrase, lo)
                except SystemExit:
                    break
                if any(k not in dropped for k in range(d0, d1 + 1)):
                    seen += 1
                    if seen >= nth:
                        found = (d0, d1, r)
                        break
                lo = after - len(norm_tokens(phrase)) + 1   # already dropped or not the wanted occurrence: look further
            if not found:
                print(f"  warning: drop not found in {sid}: {phrase!r}")
                continue
            d0, d1, r = found
            for k in range(d0, d1 + 1):
                dropped.add(k)
            print(f"  drop {phrase!r} -> words {d0}-{d1} (match {r:.2f})")
        kept = [(k, w) for k, w in enumerate(seg_words) if k not in dropped]
        if not kept:
            raise SystemExit(f"segment {sid} has no words left")
        # split into runs separated by pauses > max_sil or by dropped words
        runs, cur = [], [kept[0]]
        for prev, nxt in zip(kept, kept[1:]):
            gap = nxt[1]["s"] - prev[1]["e"]
            contiguous = nxt[0] == prev[0] + 1
            if gap > max_sil or not contiguous:
                runs.append(cur)
                cur = [nxt]
                trimmed.append({"seg": sid, "at_src": round(prev[1]["e"], 3), "gap": round(gap, 3),
                                "kept": keep if gap > max_sil else None, "reason": "pause" if contiguous else "drop"})
            else:
                cur.append(nxt)
        runs.append(cur)
        seg_tl_in = tl
        seg_text = []
        silent = None
        if seg_file:
            try:
                silent, shop = silence_map(seg_file)
            except Exception as e:  # noqa: BLE001
                print(f"  warning: silence map skipped for {sid} ({e})")
        for ri, run in enumerate(runs):
            first_w, last_w = run[0][1], run[-1][1]
            src_in = first_w["s"] - (pad_in if ri == 0 else keep / 2)
            src_out = last_w["e"] + (pad_out if ri == len(runs) - 1 else keep / 2)
            # never bleed into the neighbouring (dropped or out-of-segment) word
            gi0, gi1 = i0 + run[0][0], i0 + run[-1][0]
            if gi0 > 0 and words[gi0 - 1]["e"] < first_w["s"]:
                src_in = max(src_in, words[gi0 - 1]["e"] + 0.01)
            if gi1 + 1 < len(words) and words[gi1 + 1]["s"] > last_w["e"]:
                src_out = min(src_out, words[gi1 + 1]["s"] - 0.01)
            src_in = max(0.0, src_in)
            # the audio has the last word: every silent stretch > max_sil inside the run is shortened to keep
            parts = split_on_silence(src_in, src_out, silent, shop, max_sil, keep) if silent is not None else [(src_in, src_out)]
            for pi, (a_in, a_out) in enumerate(parts):
                if pi > 0:
                    trimmed.append({"seg": sid, "at_src": round(a_in, 3), "gap": round(a_in - parts[pi - 1][1] + keep, 3),
                                    "kept": keep, "reason": "silence"})
            run_words = list(run)
            for pi, (a_in, a_out) in enumerate(parts):
                fin, fout = frames(a_in, fps, "floor"), frames(a_out, fps, "ceil")
                if fout <= fin:
                    fout = fin + 1
                a_in, a_out = fin / fps, fout / fps
                dur = a_out - a_in
                # words whose start falls in this part (the last part takes what is left)
                mine = [rw for rw in run_words if rw[1]["s"] < a_out] if pi < len(parts) - 1 else run_words
                run_words = [rw for rw in run_words if rw not in mine]
                clips.append({"i": len(clips), "seg": sid, "file": seg_file, "src_in": round(a_in, 4), "src_out": round(a_out, 4),
                              "src_in_f": fin, "src_out_f": fout, "dur": round(dur, 4),
                              "tl_in": round(tl, 4), "tl_out": round(tl + dur, 4),
                              "text": " ".join(w["w"] for _, w in mine)})
                for _, w in mine:
                    ws = max(a_in, min(w["s"], a_out)) - a_in + tl
                    we = max(a_in, min(w["e"], a_out)) - a_in + tl
                    out_words.append({"w": w["w"], "s": round(ws, 3), "e": round(max(we, ws + 0.05), 3), "seg": sid, "src_s": w["s"]})
                    seg_text.append(w["w"])
                tl += dur
        segments.append({"id": sid, "role": seg.get("role", ""), "tl_in": round(seg_tl_in, 3), "tl_out": round(tl, 3),
                         "text": " ".join(seg_text)})

    cuts = []
    for a, b in zip(clips, clips[1:]):
        cuts.append({"tl": b["tl_in"], "tl_frame": round(b["tl_in"] * fps), "a_last_src_f": a["src_out_f"] - 1,
                     "b_first_src_f": b["src_in_f"], "a_clip": a["i"], "b_clip": b["i"]})
    total = tl
    out = {"source_words": words_path, "fps": fps, "rules": {"max_silence": max_sil, "keep_silence": keep,
           "pad_in": pad_in, "pad_out": pad_out}, "duration": round(total, 3), "clips": clips, "cuts": cuts,
           "words": out_words, "segments": segments, "trimmed_pauses": trimmed,
           "stats": {"n_clips": len(clips), "n_cuts": len(cuts), "n_words": len(out_words),
                     "pauses_trimmed": sum(1 for t in trimmed if t["reason"] in ("pause", "silence")),
                     "seconds_removed_by_pauses": round(sum(t["gap"] - keep for t in trimmed if t["reason"] in ("pause", "silence")), 2)}}
    json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f"timeline {total:.2f}s | {len(clips)} sub-clips | {len(cuts)} cuts | {out['stats']['pauses_trimmed']} pauses trimmed "
          f"({out['stats']['seconds_removed_by_pauses']}s removed) -> {out_path}")
    if not (60 <= total <= 90):
        print(f"WARNING: duration {total:.1f}s is outside the 60-90 s window")


if __name__ == "__main__":
    main()
