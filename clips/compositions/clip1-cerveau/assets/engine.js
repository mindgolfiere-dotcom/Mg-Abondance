/* MG clips — hand-drawn board engine for HyperFrames compositions.
   Deterministic: every random-looking value comes from a seeded PRNG. */
window.MG = (function () {
  const NS = "http://www.w3.org/2000/svg";
  function rng(seed) {
    let a = (seed >>> 0) || 1;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  let measureSvg = null;
  function measurer() {
    if (!measureSvg) {
      measureSvg = el("svg", { width: 10, height: 10, style: "position:absolute;left:-9999px;top:-9999px" });
      document.body.appendChild(measureSvg);
    }
    return measureSvg;
  }
  function samplePath(d, step) {
    const tmp = el("path", { d }, measurer());
    const L = tmp.getTotalLength();
    const n = Math.max(2, Math.ceil(L / step));
    const pts = [];
    for (let i = 0; i <= n; i++) { const p = tmp.getPointAtLength((L * i) / n); pts.push([p.x, p.y]); }
    tmp.remove();
    return { pts, L };
  }
  function toD(pts) {
    if (pts.length < 2) return "";
    let d = `M${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      d += ` Q${x0.toFixed(1)} ${y0.toFixed(1)} ${((x0 + x1) / 2).toFixed(1)} ${((y0 + y1) / 2).toFixed(1)}`;
    }
    const l = pts[pts.length - 1];
    return d + ` L${l[0].toFixed(1)} ${l[1].toFixed(1)}`;
  }
  // One hand-drawn stroke: 1-2 jittered passes of a clean path (multi-subpath d supported). Returns the <g>.
  function stroke(parent, d, o) {
    o = o || {};
    const r = rng(o.seed || 7);
    const subs = d.split(/(?=[Mm])/).map((x) => x.trim()).filter(Boolean);
    const sampled = subs.map((sd) => samplePath(sd, o.step || 7).pts);
    const g = el("g", { class: "sk" + (o.cls ? " " + o.cls : "") }, parent);
    const passes = o.passes == null ? 2 : o.passes;
    for (let p = 0; p < passes; p++) {
      const amp = (o.amp == null ? 1.3 : o.amp) * (p ? 1.7 : 1);
      const dd = sampled.map((pts) => toD(pts.map(([x, y], i) => (i === 0 || i === pts.length - 1) ? [x, y] : [x + (r() - 0.5) * 2 * amp, y + (r() - 0.5) * 2 * amp]))).join(" ");
      el("path", { d: dd, fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round",
        stroke: o.color || null, "stroke-width": (o.width || 4) * (p ? 0.8 : 1), opacity: p ? (o.passOpacity || 0.35) : (o.opacity || 1),
        class: "stroke" }, g);
    }
    if (o.fill) { el("path", { d, fill: o.fill, opacity: o.fillOpacity || 0.18, class: "fill", stroke: "none" }, g); }
    return g;
  }
  // Hand-written text: SVG text in the hand font, revealed by a left-to-right wipe (clip rect).
  let clipN = 0;
  function text(parent, str, o) {
    o = o || {};
    const outer = el("g", { class: "txt" + (o.cls ? " " + o.cls : ""), transform: `translate(${o.x || 0},${o.y || 0})` }, parent);
    const g = el("g", { class: "inner", transform: `rotate(${o.rot || 0})` }, outer);
    outer._inner = g;
    const id = "mgclip" + (++clipN);
    const defs = el("defs", {}, g);
    const cp = el("clipPath", { id }, defs);
    const size = o.size || 44;
    const w = o.w || Math.ceil(str.length * size * 0.62) + 20;
    const rect = el("rect", { x: -10, y: -size * 1.1, width: 0, height: size * 1.6 }, cp);
    const t = el("text", { x: 0, y: 0, "font-size": size, "font-family": o.font || "var(--font-hand)", "font-weight": o.weight || 400,
      fill: o.color || "currentColor", "text-anchor": o.anchor || "start", "clip-path": `url(#${id})`, class: "hand" }, g);
    t.textContent = str;
    outer._reveal = { rect, w: w * (o.anchor === "middle" ? 2 : 1), anchor: o.anchor };
    if (o.anchor === "middle") rect.setAttribute("x", -w);
    return outer;
  }
  // Timeline helpers -----------------------------------------------------------------
  const pencil = { el: null, proxy: { p: 0 } };
  function setPencil(elm) { pencil.el = elm; }
  function pencilTo(x, y) { if (pencil.el) pencil.el.setAttribute("transform", `translate(${x.toFixed(1)},${y.toFixed(1)})`); }
  function pencilShow(tl, t, on) { if (pencil.el) tl.set(pencil.el, { opacity: on ? 1 : 0 }, t); }
  // Draw a stroke group progressively; the pencil follows the first pass.
  function draw(tl, g, t, dur, o) {
    o = o || {};
    const paths = Array.from(g.querySelectorAll("path.stroke"));
    const fills = Array.from(g.querySelectorAll("path.fill"));
    paths.forEach((p, i) => {
      const L = p.getTotalLength() * 1.02;
      p.style.strokeDasharray = `${L}`;
      p.style.strokeDashoffset = `${L}`;
      tl.to(p, { strokeDashoffset: 0, duration: dur, ease: o.ease || "power1.inOut" }, t + i * 0.04);
    });
    fills.forEach((f) => { gsap.set(f, { opacity: 0 }); tl.to(f, { opacity: o.fillOpacity || 0.18, duration: 0.3 }, t + dur); });
    if (paths[0] && pencil.el && !o.noPencil) {
      const p0 = paths[0], L0 = p0.getTotalLength();
      const proxy = { p: 0 };
      pencilShow(tl, t, true);
      const ref = g._inner || g;
      tl.to(proxy, { p: 1, duration: dur, ease: o.ease || "power1.inOut", onUpdate() { const pt = p0.getPointAtLength(proxy.p * L0); const q = ptOffset(ref, pt); pencilTo(q.x, q.y); } }, t);
      pencilShow(tl, t + dur + 0.08, false);
    }
    return t + dur;
  }
  // Convert a point inside a transformed group to board coordinates (groups use translate/scale/rotate).
  function ptOffset(g, pt) {
    const m = g.getCTM(); const root = g.ownerSVGElement.getCTM();
    if (!m || !root) return pt;
    const p = g.ownerSVGElement.createSVGPoint(); p.x = pt.x; p.y = pt.y;
    const q = p.matrixTransform(m).matrixTransform(root.inverse());
    return { x: q.x, y: q.y };
  }
  function write(tl, g, t, dur, o) {
    o = o || {};
    const rv = g._reveal;
    tl.to(rv.rect, { attr: { width: rv.w }, duration: dur, ease: "none" }, t);
    if (pencil.el && !o.noPencil) {
      const proxy = { p: 0 };
      pencilShow(tl, t, true);
      const textEl = g.querySelector("text");
      tl.to(proxy, { p: 1, duration: dur, ease: "none", onUpdate() {
        let bw = 0; try { bw = textEl.getBBox().width; } catch (e) {}
        const x0 = rv.anchor === "middle" ? -bw / 2 : 0;
        const q = ptOffset(g._inner || g, { x: x0 + bw * proxy.p, y: -4 });
        pencilTo(q.x, q.y);
      } }, t);
      pencilShow(tl, t + dur + 0.08, false);
    }
    return t + dur;
  }
  function inner(g) { return g._inner || g; }
  function pop(tl, g, t, o) {
    o = o || {};
    const n = inner(g);
    gsap.set(g, { opacity: 0 });
    gsap.set(n, { transformOrigin: o.origin || "50% 50%" });
    tl.set(g, { opacity: 1 }, t);
    tl.fromTo(n, { scale: 0 }, { scale: 1, duration: o.dur || 0.35, ease: o.ease || "back.out(2.2)" }, t);
    return t + (o.dur || 0.35);
  }
  function fade(tl, g, t, to, dur) { tl.to(g, { opacity: to, duration: dur || 0.3 }, t); return t + (dur || 0.3); }
  function wiggle(tl, g, t, dur, o) {
    o = o || {};
    const n = Math.max(2, Math.round(dur / 0.16));
    const el2 = inner(g);
    gsap.set(el2, { transformOrigin: o.origin || "50% 100%" });
    tl.to(el2, { rotation: o.deg || 4, duration: 0.16, ease: "sine.inOut", yoyo: true, repeat: n - 1 }, t);
    tl.set(el2, { rotation: 0 }, t + n * 0.16 + 0.01);
    return t + n * 0.16;
  }
  function shake(tl, g, t, o) {
    o = o || {};
    const el2 = inner(g);
    tl.to(el2, { x: o.px || 6, duration: 0.05, yoyo: true, repeat: 5, ease: "none" }, t);
    tl.set(el2, { x: 0 }, t + 0.31);
    return t + 0.3;
  }
  // Erase: an eraser sweeps while the scene fades with a ragged wipe.
  function erase(tl, sceneG, t, dur, eraserG) {
    dur = dur || 0.55;
    if (eraserG) {
      const e = inner(eraserG);
      tl.set(eraserG, { opacity: 1 }, t);
      tl.fromTo(e, { x: -40, y: 0 }, { x: 1100, duration: dur, ease: "power2.inOut" }, t);
      tl.to(e, { y: 30, duration: dur / 4, yoyo: true, repeat: 3, ease: "sine.inOut" }, t);
      tl.set(eraserG, { opacity: 0 }, t + dur + 0.02);
      tl.set(e, { x: 0, y: 0 }, t + dur + 0.03);
    }
    tl.to(sceneG, { opacity: 0, duration: dur * 0.9, ease: "power2.in" }, t + dur * 0.1);
    tl.set(sceneG, { visibility: "hidden" }, t + dur + 0.03);
    return t + dur;
  }
  // Stickman ---------------------------------------------------------------------------
  const POSES = {
    stand: { arms: [[-6, -62, -34, -14], [6, -62, 34, -14]], legs: [[0, 0, -20, 62], [0, 0, 20, 62]], mouth: "smile", head: 0 },
    point: { arms: [[-6, -62, -30, -10], [6, -62, 74, -86]], legs: [[0, 0, -20, 62], [0, 0, 20, 62]], mouth: "smile", head: 0 },
    pointLeft: { arms: [[6, -62, 30, -10], [-6, -62, -74, -86]], legs: [[0, 0, -20, 62], [0, 0, 20, 62]], mouth: "smile", head: 0 },
    think: { arms: [[-6, -62, -30, -12], [6, -62, 22, -96]], legs: [[0, 0, -16, 62], [0, 0, 22, 60]], mouth: "flat", head: -8, brows: "think" },
    cheer: { arms: [[-6, -62, -48, -124], [6, -62, 48, -124]], legs: [[0, 0, -26, 56], [0, 0, 26, 56]], mouth: "big", head: 0 },
    shrug: { arms: [[-6, -62, -46, -52], [6, -62, 46, -52]], legs: [[0, 0, -20, 62], [0, 0, 20, 62]], mouth: "flat", head: 6, brows: "up" },
    sad: { arms: [[-6, -60, -26, 4], [6, -60, 26, 4]], legs: [[0, 0, -18, 62], [0, 0, 18, 62]], mouth: "frown", head: 10, brows: "sad" },
    surprised: { arms: [[-6, -62, -40, -40], [6, -62, 40, -40]], legs: [[0, 0, -22, 62], [0, 0, 22, 62]], mouth: "o", head: 0, brows: "up" },
    sleep: { arms: [[-6, -62, -30, -30], [6, -62, 30, -30]], legs: [[0, 0, -20, 62], [0, 0, 20, 62]], mouth: "flat", head: 0, eyes: "closed", rot: 90 },
    walk: { arms: [[-6, -62, -36, -30], [6, -62, 36, -40]], legs: [[0, 0, -30, 58], [0, 0, 26, 60]], mouth: "smile", head: 0 },
    phone: { arms: [[-6, -62, -30, -12], [6, -62, 30, -110]], legs: [[0, 0, -18, 62], [0, 0, 18, 62]], mouth: "o", head: 4, brows: "up" },
    eat: { arms: [[-6, -62, -34, -20], [6, -62, 14, -100]], legs: [[0, 0, -18, 62], [0, 0, 18, 62]], mouth: "smile", head: 0 },
    scroll: { arms: [[-6, -62, -24, -34], [6, -62, 24, -34]], legs: [[0, 0, -18, 62], [0, 0, 18, 62]], mouth: "flat", head: 16, eyes: "down" },
  };
  function stickman(parent, o) {
    o = o || {};
    const P = Object.assign({}, POSES[o.pose || "stand"], o.override || {});
    const seed = o.seed || 11;
    const outer = el("g", { class: "stickman", transform: `translate(${o.x || 0},${o.y || 0})` }, parent);
    const g = el("g", { class: "inner", transform: `scale(${o.scale || 1}) rotate(${P.rot || 0})` }, outer);
    outer._inner = g;
    const w = o.width || 5;
    // body
    stroke(g, "M0 -62 L0 0", { seed: seed + 1, width: w, step: 5 });
    P.legs.forEach((l, i) => stroke(g, `M${l[0]} ${l[1]} L${l[2]} ${l[3]}`, { seed: seed + 2 + i, width: w, step: 5 }));
    P.arms.forEach((a, i) => stroke(g, `M${a[0]} ${a[1]} L${a[2]} ${a[3]}`, { seed: seed + 4 + i, width: w, step: 5 }));
    // head (circle path, slightly tilted)
    const hx = P.head || 0, hy = -96, r = 28;
    stroke(g, `M${hx} ${hy - r} A${r} ${r} 0 1 1 ${hx - 0.1} ${hy - r}`, { seed: seed + 6, width: w, step: 6, amp: 1.1 });
    // eyes
    const ey = hy - 6;
    if (P.eyes === "closed") {
      stroke(g, `M${hx - 14} ${ey} L${hx - 6} ${ey}`, { seed: seed + 7, width: w * 0.8, passes: 1 });
      stroke(g, `M${hx + 6} ${ey} L${hx + 14} ${ey}`, { seed: seed + 8, width: w * 0.8, passes: 1 });
    } else {
      const dy = P.eyes === "down" ? 4 : 0;
      el("circle", { cx: hx - 9, cy: ey + dy, r: 3.2, class: "dot" }, g);
      el("circle", { cx: hx + 9, cy: ey + dy, r: 3.2, class: "dot" }, g);
    }
    // brows
    if (P.brows === "up") { stroke(g, `M${hx - 15} ${ey - 12} L${hx - 4} ${ey - 15}`, { seed: seed + 9, width: w * 0.7, passes: 1 }); stroke(g, `M${hx + 4} ${ey - 15} L${hx + 15} ${ey - 12}`, { seed: seed + 10, width: w * 0.7, passes: 1 }); }
    if (P.brows === "sad") { stroke(g, `M${hx - 15} ${ey - 15} L${hx - 4} ${ey - 11}`, { seed: seed + 9, width: w * 0.7, passes: 1 }); stroke(g, `M${hx + 4} ${ey - 11} L${hx + 15} ${ey - 15}`, { seed: seed + 10, width: w * 0.7, passes: 1 }); }
    if (P.brows === "think") { stroke(g, `M${hx - 15} ${ey - 12} L${hx - 4} ${ey - 13}`, { seed: seed + 9, width: w * 0.7, passes: 1 }); stroke(g, `M${hx + 4} ${ey - 16} L${hx + 15} ${ey - 11}`, { seed: seed + 10, width: w * 0.7, passes: 1 }); }
    // mouth
    const my = hy + 10;
    const mouths = { smile: `M${hx - 11} ${my} Q${hx} ${my + 10} ${hx + 11} ${my}`, big: `M${hx - 13} ${my - 2} Q${hx} ${my + 16} ${hx + 13} ${my - 2}`,
      flat: `M${hx - 9} ${my + 2} L${hx + 9} ${my + 2}`, frown: `M${hx - 11} ${my + 6} Q${hx} ${my - 4} ${hx + 11} ${my + 6}`, o: `M${hx} ${my - 4} a5 6 0 1 1 -0.1 0` };
    stroke(g, mouths[P.mouth || "smile"], { seed: seed + 11, width: w * 0.8, passes: 1, step: 4 });
    return outer;
  }
  // Props: each returns a <g> at (x,y) with scale s. Local units ~ 100px wide.
  const PROPS = {
    brain(g, s) {
      stroke(g, "M-6 -52 C-30 -58 -52 -40 -46 -18 C-62 -6 -56 24 -34 28 C-28 46 4 50 12 34 C36 44 60 26 52 4 C66 -12 54 -40 32 -40 C26 -58 4 -62 -6 -52 Z", { seed: s, width: 4, step: 6 });
      stroke(g, "M-4 -50 C-10 -24 -8 4 2 34", { seed: s + 1, width: 3, passes: 1, step: 4, amp: 0.6 });
      stroke(g, "M-38 -12 C-28 -22 -16 -16 -24 -4 C-30 6 -40 2 -38 -12", { seed: s + 2, width: 2.6, passes: 1, step: 3, amp: 0.4 });
      stroke(g, "M-34 14 C-24 6 -12 12 -18 22", { seed: s + 3, width: 2.6, passes: 1, step: 3, amp: 0.4 });
      stroke(g, "M14 -32 C26 -28 26 -14 14 -12 C6 -10 6 -24 14 -32", { seed: s + 4, width: 2.6, passes: 1, step: 3, amp: 0.4 });
      stroke(g, "M20 4 C32 0 40 12 30 20 C22 26 14 14 20 4", { seed: s + 5, width: 2.6, passes: 1, step: 3, amp: 0.4 });
    },
    phone(g, s) {
      stroke(g, "M-22 -44 L22 -44 L22 44 L-22 44 Z", { seed: s, width: 4, step: 6 });
      stroke(g, "M-14 -36 L14 -36 L14 30 L-14 30 Z", { seed: s + 1, width: 2.5, passes: 1 });
      stroke(g, "M-4 38 L4 38", { seed: s + 2, width: 3, passes: 1 });
    },
    bubble(g, s, o) {
      const w = (o && o.w) || 160, h = (o && o.h) || 70;
      stroke(g, `M${-w / 2 + 12} ${-h / 2} L${w / 2 - 12} ${-h / 2} Q${w / 2} ${-h / 2} ${w / 2} ${-h / 2 + 12} L${w / 2} ${h / 2 - 12} Q${w / 2} ${h / 2} ${w / 2 - 12} ${h / 2} L${-w / 2 + 40} ${h / 2} L${-w / 2 + 20} ${h / 2 + 22} L${-w / 2 + 18} ${h / 2} L${-w / 2 + 12} ${h / 2} Q${-w / 2} ${h / 2} ${-w / 2} ${h / 2 - 12} L${-w / 2} ${-h / 2 + 12} Q${-w / 2} ${-h / 2} ${-w / 2 + 12} ${-h / 2} Z`, { seed: s, width: 4, step: 8, fill: "var(--paper-fill)", fillOpacity: 1 });
    },
    thought(g, s, o) {
      const w = (o && o.w) || 170, h = (o && o.h) || 90;
      stroke(g, `M${-w / 2} 0 C${-w / 2 - 10} ${-h / 2} ${-w / 4} ${-h / 2 - 16} ${-w / 8} ${-h / 2 + 2} C0 ${-h / 2 - 22} ${w / 4} ${-h / 2 - 14} ${w / 3} ${-h / 2 + 6} C${w / 2 + 10} ${-h / 2} ${w / 2 + 6} ${h / 3} ${w / 3} ${h / 2 - 4} C${w / 5} ${h / 2 + 14} ${-w / 6} ${h / 2 + 10} ${-w / 4} ${h / 2 - 6} C${-w / 2 - 14} ${h / 2} ${-w / 2 - 10} ${h / 4} ${-w / 2} 0 Z`, { seed: s, width: 4, step: 8, fill: "var(--paper-fill)", fillOpacity: 1 });
      el("circle", { cx: -w / 2 + 6, cy: h / 2 + 22, r: 7, class: "ring" }, g);
      el("circle", { cx: -w / 2 - 10, cy: h / 2 + 40, r: 4, class: "ring" }, g);
    },
    bulb(g, s) {
      stroke(g, "M0 -46 C-26 -46 -36 -22 -26 -4 C-18 8 -14 14 -14 24 L14 24 C14 14 18 8 26 -4 C36 -22 26 -46 0 -46 Z", { seed: s, width: 4, step: 6 });
      stroke(g, "M-12 32 L12 32 M-10 40 L10 40", { seed: s + 1, width: 3.5, passes: 1 });
      stroke(g, "M-40 -50 L-30 -42 M40 -50 L30 -42 M0 -70 L0 -58 M-50 -20 L-40 -20 M50 -20 L40 -20", { seed: s + 2, width: 3, passes: 1, cls: "accent" });
    },
    money(g, s, o) {
      stroke(g, "M-16 -44 L16 -44 L10 -30 C40 -20 46 20 30 36 C10 50 -10 50 -30 36 C-46 20 -40 -20 -10 -30 Z", { seed: s, width: 4, step: 6 });
      const t = el("text", { x: 0, y: 20, "text-anchor": "middle", "font-size": 40, "font-family": "var(--font-hand)", "font-weight": 700, class: "hand" }, g);
      t.textContent = (o && o.sym) || "€";
    },
    note(g, s, o) {
      stroke(g, "M-60 -32 L60 -32 L60 32 L-60 32 Z", { seed: s, width: 3.5, step: 8 });
      el("circle", { cx: 0, cy: 0, r: 16, class: "ring" }, g);
      const t = el("text", { x: 0, y: 8, "text-anchor": "middle", "font-size": 24, "font-family": "var(--font-hand)", "font-weight": 700, class: "hand" }, g);
      t.textContent = (o && o.sym) || "€";
    },
    calendar(g, s, o) {
      stroke(g, "M-48 -36 L48 -36 L48 44 L-48 44 Z M-48 -16 L48 -16 M-30 -46 L-30 -26 M30 -46 L30 -26", { seed: s, width: 4, step: 7 });
      const t = el("text", { x: 0, y: 24, "text-anchor": "middle", "font-size": 26, "font-family": "var(--font-hand)", "font-weight": 700, class: "hand" }, g);
      t.textContent = (o && o.label) || "20 sept.";
    },
    plate(g, s) {
      stroke(g, "M-60 0 A60 22 0 1 1 60 0 A60 22 0 1 1 -60 0 Z", { seed: s, width: 4, step: 8 });
      stroke(g, "M-26 -8 C-20 -20 10 -22 20 -10 C30 0 10 8 -8 6 C-24 4 -30 -2 -26 -8 Z", { seed: s + 1, width: 3, passes: 1 });
      stroke(g, "M-74 -30 L-74 10 M-82 -30 L-82 -10 M-66 -30 L-66 -10 M74 -30 L74 12 M70 -30 C64 -20 64 -8 74 -8", { seed: s + 2, width: 3, passes: 1 });
    },
    cup(g, s) {
      stroke(g, "M-26 -20 L-20 28 L20 28 L26 -20 Z M26 -12 C44 -12 44 14 22 16", { seed: s, width: 4, step: 6 });
      stroke(g, "M-10 -36 C-14 -46 -4 -50 -8 -58 M4 -34 C0 -44 10 -48 6 -56", { seed: s + 1, width: 2.5, passes: 1, cls: "soft" });
    },
    arrow(g, s, o) {
      const x2 = (o && o.dx) || 120, y2 = (o && o.dy) || 0, c = (o && o.curve) || 0;
      const mx = x2 / 2 - y2 * c * 0.01, my = y2 / 2 + x2 * c * 0.01;
      stroke(g, `M0 0 Q${mx} ${my} ${x2} ${y2}`, { seed: s, width: 4, step: 7 });
      const ang = Math.atan2(y2 - my, x2 - mx);
      const a1 = ang + Math.PI * 0.8, a2 = ang - Math.PI * 0.8, L = 18;
      stroke(g, `M${x2 + Math.cos(a1) * L} ${y2 + Math.sin(a1) * L} L${x2} ${y2} L${x2 + Math.cos(a2) * L} ${y2 + Math.sin(a2) * L}`, { seed: s + 1, width: 4, passes: 1 });
    },
    cross(g, s) { stroke(g, "M-26 -26 L26 26 M26 -26 L-26 26", { seed: s, width: 6, cls: "accent-red", step: 6 }); },
    check(g, s) { stroke(g, "M-28 2 L-8 22 L30 -24", { seed: s, width: 6, cls: "accent-green", step: 6 }); },
    heart(g, s) { stroke(g, "M0 24 C-40 -4 -30 -40 -2 -24 C30 -40 40 -4 0 24 Z", { seed: s, width: 4, step: 6, cls: "accent-red" }); },
    star(g, s) { stroke(g, "M0 -30 L9 -9 L31 -9 L13 4 L20 26 L0 13 L-20 26 L-13 4 L-31 -9 L-9 -9 Z", { seed: s, width: 3.5, step: 6, cls: "accent" }); },
    burst(g, s) {
      let d = "";
      for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; d += `M${Math.cos(a) * 22} ${Math.sin(a) * 22} L${Math.cos(a) * 44} ${Math.sin(a) * 44} `; }
      stroke(g, d, { seed: s, width: 3.5, passes: 1, cls: "accent" });
    },
    lamp(g, s) {
      stroke(g, "M-30 18 C-54 10 -50 -14 -22 -18 C-10 -20 6 -20 18 -14 C40 -6 42 16 18 22 L-20 24 C-26 24 -30 22 -30 18 Z", { seed: s, width: 4, step: 6 });
      stroke(g, "M-30 0 L-62 -14 L-66 -6 L-36 8", { seed: s + 1, width: 4, passes: 1, step: 5 });
      stroke(g, "M26 -6 C46 -14 50 10 30 16", { seed: s + 2, width: 3.5, passes: 1, step: 5 });
      stroke(g, "M-8 -18 C-8 -26 6 -26 6 -18 M-1 -30 L-1 -26", { seed: s + 3, width: 3, passes: 1, step: 4, amp: 0.5 });
      stroke(g, "M-62 -16 C-74 -30 -58 -38 -64 -52 C-70 -64 -54 -66 -58 -78", { seed: s + 4, width: 2.6, passes: 1, cls: "soft", step: 5 });
    },
    eye(g, s) {
      stroke(g, "M-50 0 C-30 -32 30 -32 50 0 C30 32 -30 32 -50 0 Z", { seed: s, width: 4, step: 6 });
      el("circle", { cx: 0, cy: 0, r: 14, class: "ring" }, g);
      el("circle", { cx: 0, cy: 0, r: 5, class: "dot" }, g);
    },
    box(g, s, o) {
      const w = (o && o.w) || 140, h = (o && o.h) || 90;
      stroke(g, `M${-w / 2} ${-h / 2} L${w / 2} ${-h / 2} L${w / 2} ${h / 2} L${-w / 2} ${h / 2} Z`, { seed: s, width: 4, step: 8 });
      if (o && o.label) { const t = el("text", { x: 0, y: 12, "text-anchor": "middle", "font-size": (o.size || 36), "font-family": "var(--font-hand)", "font-weight": 700, class: "hand" }, g); t.textContent = o.label; }
    },
    door(g, s) {
      stroke(g, "M-34 -70 L34 -70 L34 70 L-34 70 Z M-34 -70 L-46 -62 L-46 78 L-34 70", { seed: s, width: 4, step: 7 });
      el("circle", { cx: 20, cy: 6, r: 5, class: "dot" }, g);
    },
    clock(g, s) {
      stroke(g, "M-40 0 A40 40 0 1 1 40 0 A40 40 0 1 1 -40 0", { seed: s, width: 4, step: 6 });
      stroke(g, "M0 0 L0 -26 M0 0 L18 10", { seed: s + 1, width: 4, passes: 1 });
    },
    magnet(g, s) {
      stroke(g, "M-36 10 L-36 -20 C-36 -50 36 -50 36 -20 L36 10 M-18 10 L-18 -20 C-18 -30 18 -30 18 -20 L18 10", { seed: s, width: 5, step: 6, cls: "accent-red" });
      stroke(g, "M-36 10 L-36 30 L-18 30 L-18 10 M18 10 L18 30 L36 30 L36 10", { seed: s + 1, width: 5, passes: 1 });
    },
    zzz(g, s) { const t = el("text", { x: 0, y: 0, "font-size": 34, "font-family": "var(--font-hand)", "font-weight": 700, class: "hand soft" }, g); t.textContent = "z z Z"; },
    sparkle(g, s) { stroke(g, "M0 -16 L0 16 M-16 0 L16 0 M-10 -10 L10 10 M10 -10 L-10 10", { seed: s, width: 3, passes: 1, cls: "accent" }); },
    stairs(g, s, o) {
      const n = (o && o.n) || 6, st = (o && o.step) || 40;
      let d = "M0 0";
      for (let i = 0; i < n; i++) d += ` L${(i + 1) * st} ${-i * st} L${(i + 1) * st} ${-(i + 1) * st}`;
      stroke(g, d, { seed: s, width: 4, step: 7 });
      if (o && o.labels) o.labels.forEach((lb, i) => { const t = el("text", { x: (i + 0.5) * st + 4, y: -i * st - 10, "font-size": 26, "font-family": "var(--font-hand)", "font-weight": 700, class: "hand", "text-anchor": "middle" }, g); t.textContent = lb; });
    },
    pencil(g, s) {
      stroke(g, "M0 0 L-8 -8 L-30 -56 L-18 -62 L4 -14 Z M-30 -56 L-18 -62 L-24 -74 Z", { seed: s, width: 3, passes: 1, step: 5 });
      stroke(g, "M-6 -18 L-28 -62", { seed: s + 1, width: 2, passes: 1, cls: "soft" });
    },
    eraser(g, s) { stroke(g, "M-40 -14 L30 -14 L40 14 L-30 14 Z M-30 14 L-40 -14 M0 -14 L10 14", { seed: s, width: 4, step: 6, fill: "var(--paper-fill)", fillOpacity: 1 }); },
    igComment(g, s, o) {
      const w = (o && o.w) || 520;
      stroke(g, `M${-w / 2} -40 L${w / 2} -40 L${w / 2} 40 L${-w / 2} 40 Z`, { seed: s, width: 4, step: 10, fill: "var(--paper-fill)", fillOpacity: 1 });
      el("circle", { cx: -w / 2 + 44, cy: 0, r: 22, class: "ring" }, g);
      stroke(g, `M${w / 2 - 40} -14 L${w / 2 - 14} 0 L${w / 2 - 40} 14`, { seed: s + 1, width: 4, passes: 1, cls: "accent" });
    },
    hand(g, s) {
      stroke(g, "M-10 60 L-10 0 C-10 -10 4 -10 4 0 L4 -40 C4 -50 18 -50 18 -40 L18 -4 C18 -14 32 -14 32 -4 L32 8 C32 -2 46 -2 46 8 L46 40 C46 60 36 70 20 70 L-10 70 Z", { seed: s, width: 4, step: 7, fill: "var(--paper-fill)", fillOpacity: 1 });
    },
  };
  function prop(parent, name, o) {
    o = o || {};
    const outer = el("g", { class: "prop " + name + (o.cls ? " " + o.cls : ""), transform: `translate(${o.x || 0},${o.y || 0})` }, parent);
    const g = el("g", { class: "inner", transform: `scale(${o.scale || 1}) rotate(${o.rot || 0})` }, outer);
    outer._inner = g;
    (PROPS[name] || PROPS.box)(g, o.seed || 3, o);
    return outer;
  }
  function scene(parent, id) { const g = el("g", { class: "scene", id }, parent); return g; }
  // Captions: words appear one by one inside their group; current word highlighted.
  function captions(tl, groups, accent) {
    const r = rng(2024);
    groups.forEach((grp) => {
      const g = document.getElementById(grp.id);
      gsap.set(g, { rotation: (r() - 0.5) * 2.4, transformOrigin: "50% 50%" });
      tl.set(g, { opacity: 1 }, grp.start);
      tl.set(g, { opacity: 0 }, grp.end);
      grp.words.forEach((w, i) => {
        const span = g.children[i];
        tl.set(span, { opacity: 1 }, w.s);
        tl.fromTo(span, { scale: 0.86 }, { scale: 1.0, duration: 0.14, ease: "back.out(3)" }, w.s);
        tl.to(span, { color: accent, duration: 0.05 }, w.s);
        tl.to(span, { color: "var(--cap-color)", duration: 0.08 }, w.e);
      });
    });
  }
  return { rng, el, stroke, text, draw, write, pop, fade, wiggle, shake, erase, stickman, prop, scene, captions, setPencil, POSES, PROPS, pencilShow, inner };
})();
