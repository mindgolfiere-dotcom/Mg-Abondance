#!/usr/bin/env python3
"""Convert a Shade transcription (utterances with ms word timestamps) to the pipeline's words.json.

Usage: python3 -I clips/tools/shade_words.py shade_utterances.json out_words.json [--media path_or_url]
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcribe import merge_tokens, apply_glossary  # noqa: E402


def main():
    src, out = sys.argv[1], sys.argv[2]
    media = sys.argv[sys.argv.index("--media") + 1] if "--media" in sys.argv else ""
    d = json.load(open(src))
    words = []
    for u in d.get("base_utterances", []):
        for w in u.get("words", []):
            words.append({"w": w["text"].strip(), "s": round(w["start"] / 1000.0, 3), "e": round(w["end"] / 1000.0, 3), "p": 1.0})
    words = [w for w in words if w["w"]]
    gpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary.json")
    glossary = json.load(open(gpath)) if os.path.exists(gpath) else {"replace": {}}
    words = apply_glossary(merge_tokens(words), glossary)
    dur = max((w["e"] for w in words), default=0)
    json.dump({"media": media, "duration": dur, "language": "fr", "model": "shade", "segments": [], "words": words}, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(words)} words, {dur:.0f}s -> {out}")


if __name__ == "__main__":
    main()
