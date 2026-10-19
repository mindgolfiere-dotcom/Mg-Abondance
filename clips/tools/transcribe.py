#!/usr/bin/env python3
"""Word-level transcription of a video/audio file with faster-whisper.

Usage: python3 -I clips/tools/transcribe.py <media> <out.json> [--model large-v3-turbo] [--lang fr]

Output JSON: {"media": path, "duration": s, "language": "fr", "segments": [...],
              "words": [{"w": "mot", "s": start, "e": end, "p": prob}, ...]}
Words are the ground truth for the cut list and the captions.
"""
import argparse, json, subprocess, sys, time
import numpy as np


def load_audio(path, sr=16000):
    """Decode with ffmpeg to 16 kHz mono float32 (bypasses PyAV version issues)."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True)
    return np.frombuffer(out.stdout, np.float32).copy()


def merge_tokens(words):
    """Whisper splits elisions ("c" + "'est") and emits punctuation-only tokens ("?").
    Glue those onto the previous word so captions and anchors see real words."""
    out = []
    for w in words:
        t = w["w"]
        is_punct = all(not ch.isalnum() for ch in t)
        if out and (t.startswith("'") or t.startswith("’") or is_punct):
            prev = out[-1]
            prev["w"] = prev["w"] + t
            prev["e"] = max(prev["e"], w["e"])
            prev["p"] = min(prev["p"], w["p"])
        else:
            out.append(dict(w))
    return out


def media_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    return float(out.stdout.strip() or 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("out")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--lang", default="fr")
    ap.add_argument("--prompt", default="Zak, MG Academy, MG Méditation, manifestation, subconscient, 4D, 3D, Neville Goddard, 10 000 € par mois.")
    args = ap.parse_args()

    from faster_whisper import WhisperModel
    t0 = time.time()
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    audio = load_audio(args.media)
    segments, info = model.transcribe(
        audio, language=args.lang, word_timestamps=True, beam_size=5,
        vad_filter=True, vad_parameters={"min_silence_duration_ms": 200, "speech_pad_ms": 60},
        initial_prompt=args.prompt, condition_on_previous_text=False,
    )
    words, segs = [], []
    for seg in segments:
        segs.append({"s": round(seg.start, 3), "e": round(seg.end, 3), "text": seg.text.strip()})
        for w in (seg.words or []):
            words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
    words = merge_tokens(words)
    data = {"media": args.media, "duration": media_duration(args.media), "language": info.language,
            "model": args.model, "segments": segs, "words": words}
    json.dump(data, open(args.out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(words)} words, {len(segs)} segments, {time.time()-t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
