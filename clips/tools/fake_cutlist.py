#!/usr/bin/env python3
"""Synthetic cut list from a clipping script (for layout work before the masters arrive).

Usage: python3 -I clips/tools/fake_cutlist.py segments.json out_cutlist.json [--wps 3.2]
segments.json: [{"id": "S1", "role": "hook", "text": "..."}, ...]
Also writes a placeholder talking-head video next to the cut list (<out>_face.mp4).
"""
import json, os, re, subprocess, sys


def main():
    src, out = sys.argv[1], sys.argv[2]
    wps = float(sys.argv[sys.argv.index("--wps") + 1]) if "--wps" in sys.argv else 3.2
    segs = json.load(open(src))
    words, segments, t = [], [], 0.0
    for s in segs:
        t_in = t
        toks = s["text"].split()
        for w in toks:
            dur = max(0.1, min(0.6, 0.05 + 0.03 * len(re.sub(r"[^\w]", "", w))))
            words.append({"w": w, "s": round(t, 3), "e": round(t + dur, 3), "seg": s["id"]})
            t += dur + 0.035
            if re.search(r"[.,;:?!]$", w):
                t += 0.15
        t += 0.1
        segments.append({"id": s["id"], "role": s.get("role", ""), "tl_in": round(t_in, 3), "tl_out": round(t, 3), "text": s["text"]})
    cl = {"fps": 25, "duration": round(t, 3), "clips": [], "cuts": [{"tl": round(sg["tl_in"], 3), "tl_frame": int(sg["tl_in"] * 25), "a_last_src_f": 0, "b_first_src_f": 0, "a_clip": 0, "b_clip": 0} for sg in segments[1:]],
          "words": words, "segments": segments, "synthetic": True}
    json.dump(cl, open(out, "w"), ensure_ascii=False, indent=1)
    face = os.path.splitext(out)[0] + "_face.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=#4a3f3a:s=1080x1000:r=25:d={t:.3f}",
                    "-f", "lavfi", "-i", f"sine=frequency=220:sample_rate=48000:duration={t:.3f}",
                    "-vf", "drawbox=x=390:y=200:w=300:h=380:color=#c9a27e@1:t=fill,drawbox=x=300:y=620:w=480:h=380:color=#333333@1:t=fill",
                    "-af", "volume=0.02", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", face], check=True)
    json.dump({"fps": "25", "out_size": [1080, 1000], "crop": {"x": 0, "y": 0, "w": 1080, "h": 1000}}, open(os.path.splitext(face)[0] + ".json", "w"))
    print(f"{len(words)} words, {t:.1f}s -> {out} (+ placeholder {face})")


if __name__ == "__main__":
    main()
