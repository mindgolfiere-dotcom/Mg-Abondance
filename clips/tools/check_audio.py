#!/usr/bin/env python3
"""Fast pre-render check of a cut list: concatenates only the audio of every sub-clip (same cuts, same fades,
same loudness target as render_face.py) and runs the QC silence gate on it.
Usage: python3 -I clips/tools/check_audio.py cutlist.json [--max 0.25] [--noise -35] [--lufs -16]"""
import argparse, json, os, re, subprocess, tempfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlist"); ap.add_argument("--max", type=float, default=0.25)
    ap.add_argument("--noise", type=float, default=-35.0); ap.add_argument("--lufs", type=float, default=-16.0)
    a = ap.parse_args()
    cl = json.load(open(a.cutlist)); fps = float(cl["fps"]); half = 0.5 / fps
    cmd, fc, labels = ["ffmpeg", "-y", "-v", "error"], [], []
    for k, c in enumerate(cl["clips"]):
        n = c["src_out_f"] - c["src_in_f"]; dur = n / fps
        cmd += ["-ss", f"{max(0.0, c['src_in_f'] / fps - half):.6f}", "-t", f"{dur:.6f}", "-i", c["file"]]
        fc.append(f"[{k}:a]asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.006,afade=t=out:st={max(0, dur - 0.006):.4f}:d=0.006[a{k}]")
        labels.append(f"[a{k}]")
    fc.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[ac]")
    tmp = os.path.join(tempfile.mkdtemp(), "audio.wav")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[ac]", "-ar", "48000", "-ac", "2", tmp]
    subprocess.run(cmd, check=True)
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"I:\s*(-?[0-9.]+) LUFS", out[out.rfind("Summary:"):]); I = float(m.group(1)) if m else -23.0
    gain = a.lufs - I
    det = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-af", f"volume={gain:.2f}dB,silencedetect=n={a.noise}dB:d={a.max}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    pauses = [(float(s), float(d)) for s, d in re.findall(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)", det)]
    for e, d in pauses:
        print(f"  pause at {e - d:.3f}s for {d:.3f}s")
    print(f"{len(cl['clips'])} sub-clips, {cl['duration']:.2f}s, {I:.1f} LUFS (gain {gain:+.1f} dB) -> {len(pauses)} pause(s) > {a.max}s -> {'PASS' if not pauses else 'FAIL'}")
    return 0 if not pauses else 1


if __name__ == "__main__":
    raise SystemExit(main())
