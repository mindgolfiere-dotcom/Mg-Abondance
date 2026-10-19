#!/usr/bin/env python3
"""Generate a HyperFrames composition (index.html + assets) for one clip.

Usage: python3 -I clips/tools/build_composition.py --project clips/compositions/clip1 --cutlist cutlist.json \
          --face face.mp4 --storyboard storyboard.json [--variant paper|chalk] [--sfx-dir clips/compositions/_shared/sfx]

storyboard.json:
{
  "variant": "paper",
  "cta": {"at": "S6:Dans", "keyword": "ABONDANCE", "auto": true},
  "scenes": [{"id": "sc1", "in": "S1:@", "out": "S2:@", "exit": "erase",
              "actions": [{"t": "S1:subconscient", "do": "prop", "name": "brain", "x": 540, "y": 1350, "scale": 2, "draw": 0.8, "sfx": "stroke"}]}]
}
Time anchors: "SEG:word" = start of the first word matching in that segment ("word#2" second match,
"word$" its end, "+0.3" offset), "SEG:@" = segment start, "SEG:$" = segment end, or a number (seconds).
Coordinates are full-frame 1080x1920 (the board is the whole frame; the face covers y<1000 until the CTA).
"""
import argparse, json, os, re, shutil, subprocess, sys, unicodedata, random

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(os.path.dirname(HERE), "compositions", "_shared")

SFX_ALIASES = {
    "paper": {"stroke": "pencil-long", "stroke-short": "pencil-short", "erase": "eraser"},
    "chalk": {"stroke": "chalk-long", "stroke-short": "chalk-line", "erase": "eraser"},
}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s)


class Anchors:
    def __init__(self, cutlist):
        self.words = cutlist["words"]
        self.segs = {s["id"]: s for s in cutlist["segments"]}
        self.duration = cutlist["duration"]

    def resolve(self, a):
        if isinstance(a, (int, float)):
            return float(a)
        m = re.match(r"^(\w+):([^+\-]+?)(\$)?(?:#(\d+))?([+-][0-9.]+)?$", a.strip())
        if not m:
            raise SystemExit(f"bad anchor: {a!r}")
        seg, word, end, nth, off = m.group(1), m.group(2), m.group(3), int(m.group(4) or 1), float(m.group(5) or 0)
        if seg not in self.segs:
            raise SystemExit(f"unknown segment in anchor {a!r}")
        S = self.segs[seg]
        if word == "@":
            return S["tl_in"] + off
        if word == "$":
            return S["tl_out"] + off
        target = norm(word)
        hits = [w for w in self.words if w["seg"] == seg and norm(w["w"]).startswith(target)]
        if len(hits) < nth:
            hits = [w for w in self.words if w["seg"] == seg and target in norm(w["w"])]
        if len(hits) < nth:
            raise SystemExit(f"anchor word not found: {a!r} (segment text: {S['text'][:120]}...)")
        w = hits[nth - 1]
        return (w["e"] if end else w["s"]) + off


def caption_groups(words, max_words=3, max_gap=0.6):
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["s"] - cur[-1]["e"] > max_gap or re.search(r"[.?!:]$", cur[-1]["w"])):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        start = g[0]["s"] - 0.04
        nxt = groups[i + 1][0]["s"] - 0.04 if i + 1 < len(groups) else g[-1]["e"] + 0.6
        end = min(nxt, g[-1]["e"] + 0.9)
        out.append({"id": f"cap{i}", "start": round(max(0, start), 3), "end": round(end, 3),
                    "words": [{"w": w["w"], "s": round(w["s"], 3), "e": round(w["e"], 3)} for w in g]})
    return out


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def audio_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
                         capture_output=True, text=True)
    return float(out.stdout.strip() or 0)



def prepare_images(scenes, assets, proj):
    """Copy every image action's source into assets/img and set href (+ height from the file's aspect)."""
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        Image = None
    os.makedirs(os.path.join(assets, "img"), exist_ok=True)
    for sc in scenes:
        for act in sc["actions"]:
            if act.get("do") != "image":
                continue
            src = act["src"]
            cands = [src, os.path.join(SHARED, "img", src), os.path.join(proj, src)]
            path = next((c for c in cands if os.path.exists(c)), None)
            if not path:
                raise SystemExit(f"image not found: {src!r}")
            base = os.path.basename(path)
            shutil.copy(path, os.path.join(assets, "img", base))
            act["href"] = f"assets/img/{base}"
            if Image is not None and not act.get("h"):
                iw, ih = Image.open(path).size
                act["h"] = round(act.get("w", 400) * ih / iw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--cutlist", required=True)
    ap.add_argument("--face", required=True)
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--variant", default=None)
    ap.add_argument("--sfx-dir", default=os.path.join(SHARED, "sfx"))
    ap.add_argument("--title", default="MG clip")
    ap.add_argument("--fps", type=int, default=None)
    ap.add_argument("--tail", type=float, default=1.5, help="seconds of CTA board held after the last word (face fades out)")
    a = ap.parse_args()

    cl = json.load(open(a.cutlist))
    sb = json.load(open(a.storyboard))
    variant = a.variant or sb.get("variant", "paper")
    an = Anchors(cl)
    proj = a.project
    assets = os.path.join(proj, "assets")
    os.makedirs(os.path.join(assets, "fonts"), exist_ok=True)
    os.makedirs(os.path.join(assets, "sfx"), exist_ok=True)
    for f in ("engine.js", "interpreter.js"):
        shutil.copy(os.path.join(SHARED, f), os.path.join(assets, f))
    for f in os.listdir(os.path.join(SHARED, "fonts")):
        shutil.copy(os.path.join(SHARED, "fonts", f), os.path.join(assets, "fonts", f))
    shutil.copy(a.face, os.path.join(assets, "face.mp4"))
    face_dur = audio_duration(os.path.join(assets, "face.mp4"))
    tail = float(a.tail)
    total = round(face_dur + tail, 3)

    # scenes with resolved times
    scenes = []
    for i, sc in enumerate(sb["scenes"]):
        t_in = an.resolve(sc["in"])
        t_out = an.resolve(sc["out"]) if sc.get("out") else (an.resolve(sb["scenes"][i + 1]["in"]) if i + 1 < len(sb["scenes"]) else total)
        acts = []
        for act in sc["actions"]:
            act = dict(act)
            act["t"] = round(an.resolve(act["t"]), 3)
            if act.get("x") is not None and act["do"] in ("prop", "stickman", "text") and sc["id"] != "cta":
                in_cta = sb.get("cta") and act["t"] >= an.resolve(sb["cta"]["at"])
                ymin = 270 if in_cta else 1040
                if not (108 <= act["x"] <= 860 and ymin <= act["y"] <= 1500):
                    print(f"safe-zone warning: {sc['id']} {act['do']} {act.get('name', act.get('text', ''))!r} at ({act['x']},{act['y']}) is outside x 108-860 / y {ymin}-1500")
            if act["t"] > total - 0.05:
                print(f"warning: action at {act['t']}s is past the end ({total}s), dropped: {act.get('do')} {act.get('name', act.get('text', ''))}")
                continue
            acts.append(act)
        scenes.append({"id": sc["id"], "in": round(t_in, 3), "out": round(t_out, 3), "exit": sc.get("exit", "erase"),
                       "exitDur": sc.get("exitDur"), "actions": acts})

    # CTA
    cta = None
    if sb.get("cta"):
        c = sb["cta"]
        cta = {"at": round(an.resolve(c["at"]), 3), "pipScale": c.get("pipScale", 0.24), "pipX": c.get("pipX", 120),
               "pipY": c.get("pipY", 300), "capY": c.get("capY", -330), "keyword": c.get("keyword", "ABONDANCE")}
        if c.get("auto", True):
            kw = cta["keyword"]
            t0 = cta["at"]
            auto = {"id": "cta", "in": round(t0, 3), "out": total, "exit": "none", "actions": [
                {"t": round(t0 + 0.55, 3), "do": "text", "text": c.get("line1", "Commente"), "x": 540, "y": 1010, "size": 96, "anchor": "middle", "weight": 700, "sfx": "stroke-short"},
                {"t": round(t0 + 1.0, 3), "do": "prop", "name": "igComment", "id": "igbox", "x": 540, "y": 1150, "scale": 1.5, "w": 560, "draw": 0.55, "sfx": "stroke-short"},
                {"t": round(t0 + 1.55, 3), "do": "text", "text": kw, "id": "kw", "x": 540, "y": 1172, "size": 64, "anchor": "middle", "weight": 700, "cls": "accent", "write": 0.9, "sfx": "typing"},
                {"t": round(t0 + 2.5, 3), "do": "prop", "name": "arrow", "x": 540, "y": 1250, "dx": 0, "dy": 110, "curve": 40, "draw": 0.35, "sfx": "stroke-short"},
                {"t": round(t0 + 2.9, 3), "do": "prop", "name": "bubble", "id": "dm", "x": 540, "y": 1440, "w": 700, "h": 150, "scale": 1, "pop": 0.4, "sfx": "pop"},
                {"t": round(t0 + 3.15, 3), "do": "text", "text": c.get("line2", "je t'envoie l'accès en DM"), "x": 540, "y": 1455, "size": 50, "anchor": "middle", "weight": 700, "write": 0.8, "sfx": "stroke-short"},
                {"t": round(t0 + 4.0, 3), "do": "prop", "name": "check", "x": 850, "y": 1440, "scale": 1.1, "pop": 0.3, "sfx": "ding"},
                {"t": round(t0 + 4.3, 3), "do": "punch", "target": "kw", "scale": 1.12},
                {"t": round(t0 + 4.3, 3), "do": "prop", "name": "sparkle", "x": 300, "y": 1120, "scale": 1.2, "pop": 0.25, "sfx": "magic"},
                {"t": round(t0 + 4.45, 3), "do": "prop", "name": "sparkle", "x": 790, "y": 1110, "scale": 0.9, "pop": 0.25},
            ] + [dict(x, t=round(an.resolve(x["t"]), 3)) for x in c.get("extra", [])]}
            if tail >= 0.8:   # the board holds after the last word: one last nudge on the keyword, never silent
                auto["actions"] += [
                    {"t": round(face_dur + 0.15, 3), "do": "punch", "target": "kw", "scale": 1.12},
                    {"t": round(face_dur + 0.15, 3), "do": "prop", "name": "sparkle", "x": 360, "y": 1105, "scale": 1.0, "pop": 0.25, "sfx": "magic"},
                    {"t": round(face_dur + 0.55, 3), "do": "prop", "name": "sparkle", "x": 760, "y": 1215, "scale": 0.8, "pop": 0.25, "sfx": "ding"},
                ]
            scenes.append(auto)
        cta["faceOut"] = round(face_dur, 3)

    # punch-ins at cuts (seeded pattern, never two in a row at the same scale)
    rnd = random.Random(42)
    punches, scale = [], 1.0
    for k, cut in enumerate(cl["cuts"]):
        if rnd.random() < 0.55:
            scale = 1.0 if scale > 1.0 else rnd.choice([1.06, 1.08, 1.1])
            punches.append({"t": cut["tl"], "scale": scale})

    # SFX elements
    aliases = SFX_ALIASES[variant]
    sfx_tags, missing = [], set()
    srnd = random.Random(7)
    k = 0
    lanes = []   # per Studio track: time until which it is busy (sfx sorted by start below)
    for sc in scenes:
        if sc.get("exit") == "erase" and sc["out"] < total - 0.3:
            sc["actions"] = sc["actions"] + [{"t": round(sc["out"], 3), "do": "sfx-only", "sfx": "erase", "draw": sc.get("exitDur") or 0.55, "gain": 0.5}]
    all_acts = sorted((act for sc in scenes for act in sc["actions"] if act.get("sfx")), key=lambda x: x["t"])
    for sc in [{"actions": all_acts}]:
        for act in sc["actions"]:
            name = act.get("sfx")
            if not name:
                continue
            fname = aliases.get(name, name)
            src = os.path.join(a.sfx_dir, fname + ".wav")
            if not os.path.exists(src):
                missing.add(fname)
                continue
            dst = os.path.join(assets, "sfx", fname + ".wav")
            if not os.path.exists(dst):
                shutil.copy(src, dst)
            full = audio_duration(dst)
            if act["do"] == "text":
                dur = act.get("write") or max(0.35, min(1.4, len(act.get("text", "")) * 0.045))
            else:
                dur = act.get("draw") or (0.35 if name in ("pop", "ding", "stroke-short") else min(full, 1.2 if name != "vibrate" else 0.9))
            dur = min(dur + 0.15, full, max(0.1, total - act["t"] - 0.02))
            gain = act.get("gain", 0.55 if name in ("stroke", "stroke-short", "typing") else 0.7)
            media_start = 0.0
            if full > dur + 1.0 and name in ("stroke", "typing", "erase"):
                media_start = round(srnd.uniform(0.2, full - dur - 0.5), 2)   # different bit of the recording each time
            fade = min(0.12, dur / 3)
            auto = {"version": 1, "lanes": [{"target": "volume", "points": [{"t": 0, "v": 0}, {"t": 0.03, "v": 1}, {"t": round(dur - fade, 3), "v": 1}, {"t": round(dur, 3), "v": 0}]}]}
            lane = next((i for i, busy in enumerate(lanes) if busy <= act["t"]), None)
            if lane is None:
                lanes.append(0.0)
                lane = len(lanes) - 1
            lanes[lane] = act["t"] + dur + 0.02
            sfx_tags.append(f'<audio id="sfx{k}" src="assets/sfx/{fname}.wav" data-start="{act["t"]:.3f}" data-duration="{dur:.3f}" '
                            f'data-media-start="{media_start}" data-track-index="{20 + lane}" data-volume="{gain}" '
                            f"data-automation='{json.dumps(auto)}'></audio>")
            k += 1
    if missing:
        print(f"warning: missing sfx files (skipped): {sorted(missing)}")

    caps = caption_groups(cl["words"])
    cap_html = []
    for g in caps:
        spans = "".join(f'<span>{w["w"]}</span>' for w in g["words"])
        cap_html.append(f'<div class="cap" id="{g["id"]}">{spans}</div>')
    with open(os.path.join(proj, "captions.srt"), "w") as f:
        for i, g in enumerate(caps, 1):
            f.write(f"{i}\n{srt_time(g['start'])} --> {srt_time(g['end'])}\n{' '.join(w['w'] for w in g['words'])}\n\n")

    prepare_images(scenes, assets, proj)
    plan = {"variant": variant, "scenes": scenes, "cta": cta, "punches": punches, "captions": caps, "duration": total}
    json.dump(plan, open(os.path.join(proj, "plan.json"), "w"), ensure_ascii=False, indent=1)

    themes = {
        "paper": {"--ink": "#2b2a28", "--paper": "#f6f1e6", "--paper-fill": "#f6f1e6", "--accent": "#1f4fbf", "--accent-red": "#d2342c",
                  "--accent-green": "#2f8f4e", "--cap-color": "#1c1b1a", "--cap-accent": "#d2342c", "--cap-bg": "rgba(255,252,245,0.92)",
                  "--grad": "rgba(22,17,12,0.58)", "--tex-op": "0.14", "--stroke-op": "0.92", "--font-hand": "Kalam", "--font-cap": "Patrick Hand"},
        "chalk": {"--ink": "#f4f1e8", "--paper": "#1c2320", "--paper-fill": "#1c2320", "--accent": "#ffd166", "--accent-red": "#ff7b72",
                  "--accent-green": "#8be3a1", "--cap-color": "#ffffff", "--cap-accent": "#ffd166", "--cap-bg": "rgba(0,0,0,0.0)",
                  "--grad": "rgba(0,0,0,0.7)", "--tex-op": "0.22", "--stroke-op": "0.9", "--font-hand": "Kalam", "--font-cap": "Patrick Hand"},
    }[variant]
    root_vars = "\n".join(f"      {k}: {v};" for k, v in themes.items())
    from fractions import Fraction
    meta_path = os.path.splitext(a.face)[0] + ".json"
    fps = a.fps or (int(round(float(Fraction(json.load(open(meta_path))["fps"])))) if os.path.exists(meta_path) else 25)
    cap_shadow = "0 2px 0 rgba(0,0,0,0.55), 0 0 18px rgba(0,0,0,0.6)" if variant == "chalk" else "none"
    trnd = random.Random(2026)
    pts, x = [], 0
    while x < 1080:
        pts.append((x, 18 + trnd.uniform(-12, 16)))
        x += trnd.uniform(14, 48)
    pts.append((1080, 24))
    tear_line = " ".join(f"L{px:.0f} {py:.0f}" for px, py in pts)
    tear = ("" if variant == "chalk" else
            f'<svg id="tear" data-layout-allow-occlusion viewBox="0 0 1080 60" preserveAspectRatio="none"><path d="M0 0 L0 {pts[0][1]:.0f} {tear_line} L1080 0 Z" fill="var(--paper)"/><path d="M0 {pts[0][1]:.0f} {tear_line}" fill="none" stroke="rgba(0,0,0,0.16)" stroke-width="2"/><path d="M0 {pts[0][1]+5:.0f} {" ".join(f"L{px:.0f} {py+5:.0f}" for px, py in pts)}" fill="none" stroke="rgba(0,0,0,0.05)" stroke-width="6"/></svg>')
    face_shade = ('<div id="face-shade"></div>' if variant == "chalk" else "")
    html = f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>{a.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script src="assets/engine.js"></script>
    <style>
      @font-face {{ font-family: "Kalam"; src: url("assets/fonts/Kalam-700.woff2") format("woff2"); font-weight: 700; }}
      @font-face {{ font-family: "Kalam"; src: url("assets/fonts/Kalam-400.woff2") format("woff2"); font-weight: 400; }}
      @font-face {{ font-family: "Patrick Hand"; src: url("assets/fonts/Patrick-Hand-400.woff2") format("woff2"); font-weight: 400; }}
      :root {{
{root_vars}
      }}
      * {{ box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--paper); }}
      #board {{ position: absolute; inset: 0; background: var(--paper); }}
      #board svg {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; color: var(--ink); overflow: visible; }}
      #board .stroke {{ stroke: currentColor; opacity: var(--stroke-op); }}
      #board .sk .stroke + .stroke {{ opacity: 0.32; }}
      #board .dot {{ fill: currentColor; }}
      #board .ring {{ fill: none; stroke: currentColor; stroke-width: 3; }}
      #board .hand {{ fill: currentColor; }}
      #board .accent .stroke, #board .accent .hand, #board .accent.hand, #board .txt.accent text {{ color: var(--accent); fill: var(--accent); stroke: var(--accent); }}
      #board .txt.accent text {{ stroke: none; }}
      #board .accent-red .stroke {{ stroke: var(--accent-red); }}
      #board .accent-green .stroke {{ stroke: var(--accent-green); }}
      #board .soft .stroke, #board .soft.hand {{ opacity: 0.45; }}
      #board .tool .stroke {{ stroke: var(--ink); opacity: 1; }}
      #board .tool .fill {{ opacity: 1; }}
      #tex {{ position: absolute; inset: 0; opacity: var(--tex-op); pointer-events: none; }}
      #face-wrap {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1000px; overflow: hidden; clip-path: circle(120% at 50% 48%); }}
      #face-inner {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1000px; }}
      #face {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1000px; object-fit: cover; }}
      #face-shade {{ position: absolute; left: 0; top: 760px; width: 1080px; height: 240px; background: linear-gradient(to bottom, rgba(28,35,32,0) 0%, rgba(28,35,32,0.85) 70%, var(--paper) 100%); }}
      #tear {{ position: absolute; left: 0; top: 976px; width: 1080px; height: 60px; }}
      #grad-right {{ position: absolute; right: 0; top: 1040px; width: 210px; height: 880px; background: linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,0.06) 35%, var(--grad) 100%); -webkit-mask-image: linear-gradient(to bottom, transparent 0%, #000 22%, #000 100%); mask-image: linear-gradient(to bottom, transparent 0%, #000 22%, #000 100%); pointer-events: none; }}
      #grad-bottom {{ position: absolute; left: 0; top: 1560px; width: 1080px; height: 360px; background: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.05) 30%, var(--grad) 100%); pointer-events: none; }}
      #captions {{ position: absolute; left: 110px; width: 860px; top: 905px; height: 160px; }}
      .cap {{ position: absolute; left: 0; right: 0; top: 0; opacity: 0; text-align: center; font-family: var(--font-cap), sans-serif; font-size: 66px; line-height: 1.05; color: var(--cap-color); text-shadow: {cap_shadow}; }}
      .cap span {{ display: inline-block; opacity: 0; margin: 0 6px; padding: 2px 12px; background: var(--cap-bg); border-radius: 12px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{total}" data-fps="{fps}">
      <div id="board">
        <svg id="tex" viewBox="0 0 1080 1920" preserveAspectRatio="none"><filter id="paperf"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="7" /><feColorMatrix type="saturate" values="0" /></filter><rect width="1080" height="1920" filter="url(#paperf)" /></svg>
        <svg id="board-svg" viewBox="0 0 1080 1920"></svg>
      </div>
      <div id="face-wrap">
        <div id="face-inner" data-layout-allow-overflow>
          <video id="face" class="clip" src="assets/face.mp4" playsinline data-has-audio="true" data-start="0" data-duration="{face_dur:.3f}" data-track-index="0" data-volume="1"></video>
          {face_shade}
        </div>
      </div>
      {tear}
      <div id="grad-right" data-layout-allow-occlusion></div>
      <div id="grad-bottom" data-layout-allow-occlusion></div>
      <div id="captions">
        {chr(10).join(cap_html)}
      </div>
      {chr(10).join(sfx_tags)}
    </div>
    <script>window.PLAN = {json.dumps(plan, ensure_ascii=False)};</script>
    <script src="assets/interpreter.js"></script>
    <script>
      document.fonts.ready.then(() => {{
        const tl = window.MGBuild();
        window.__timelines["main"] = tl;
        if (window.__hfForceTimelineRebind) window.__hfForceTimelineRebind();
      }});
    </script>
  </body>
</html>
"""
    with open(os.path.join(proj, "index.html"), "w") as f:
        f.write(html)
    print(f"index.html written: {len(scenes)} scenes, {len(caps)} caption groups, {len(sfx_tags)} sfx, {len(punches)} punch-ins, duration {total}s, fps {fps}")


if __name__ == "__main__":
    main()
