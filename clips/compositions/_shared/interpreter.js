/* Builds the board scenes and the single paused GSAP timeline from the resolved plan (window.PLAN). */
window.MGBuild = function build() {
    const PLAN = window.PLAN;
    const svg = document.getElementById("board-svg");
    const tl = gsap.timeline({ paused: true });
    const objs = {};
    // tools layer (pencil + eraser) sits above all scenes
    const tools = MG.el("g", { id: "tools" }, svg);
    const pencilG = MG.prop(tools, PLAN.variant === "chalk" ? "chalk" : "pencil", { seed: 101, scale: 1.0, cls: "tool" });
    gsap.set(pencilG, { opacity: 0 });
    MG.setPencil(pencilG);
    const eraserG = MG.prop(tools, "eraser", { seed: 102, scale: 1.2, cls: "tool", y: 1400 });
    gsap.set(eraserG, { opacity: 0 });
    svg.appendChild(tools); // keep tools last (on top)

    PLAN.scenes.forEach((sc) => {
      const g = MG.scene(svg, sc.id);
      svg.insertBefore(g, tools);
      gsap.set(g, { opacity: 0 });
      tl.set(g, { opacity: 1 }, sc.in);
      sc.actions.forEach((a, k) => {
        const t = a.t;
        let node = null;
        const id = a.id || `${sc.id}-${k}`;
        if (a.do === "sfx-only") return;
        if (a.do === "prop") {
          node = MG.prop(g, a.name, { x: a.x, y: a.y, scale: a.scale || 1, rot: a.rot || 0, seed: a.seed || (k * 7 + 3), w: a.w, h: a.h, label: a.label, sym: a.sym, n: a.n, step: a.step, labels: a.labels, dx: a.dx, dy: a.dy, curve: a.curve, cls: a.cls });
        } else if (a.do === "stickman") {
          node = MG.stickman(g, { x: a.x, y: a.y, scale: a.scale || 1, pose: a.pose || "stand", seed: a.seed || (k * 13 + 5) });
        } else if (a.do === "text") {
          node = MG.text(g, a.text, { x: a.x, y: a.y, size: a.size || 44, anchor: a.anchor, rot: a.rot || 0, cls: a.cls, weight: a.weight, font: a.font, w: a.w });
        } else if (a.do === "image") {
          node = MG.image(g, a.href, { x: a.x, y: a.y, w: a.w, h: a.h, rot: a.rot || 0, seed: a.seed || (k * 11 + 7), pad: a.pad, tape: a.tape, tapeRot: a.tapeRot, cls: a.cls });
        } else if (a.do === "path") {
          node = MG.stroke(g, a.d, { seed: a.seed || (k * 5 + 1), width: a.width || 4, cls: a.cls, fill: a.fill, step: a.step });
          if (a.x || a.y || a.scale) node.setAttribute("transform", `translate(${a.x || 0},${a.y || 0}) scale(${a.scale || 1})`);
        } else if (a.do === "wiggle") { MG.wiggle(tl, objs[a.target], t, a.dur || 0.6, { deg: a.deg, origin: a.origin }); return; }
        else if (a.do === "shake") { MG.shake(tl, objs[a.target], t, { px: a.px }); return; }
        else if (a.do === "fade") { MG.fade(tl, objs[a.target], t, a.to == null ? 0 : a.to, a.dur || 0.3); return; }
        else if (a.do === "move") { tl.to(MG.inner(objs[a.target]), { x: a.x || 0, y: a.y || 0, duration: a.dur || 0.6, ease: a.ease || "power2.inOut" }, t); return; }
        else if (a.do === "bounce") { const o = MG.inner(objs[a.target]); tl.to(o, { y: -(a.px || 30), duration: 0.18, ease: "power2.out", yoyo: true, repeat: 1 }, t); tl.set(o, { y: 0 }, t + 0.37); return; }
        else if (a.do === "hide") { tl.set(objs[a.target], { opacity: 0 }, t); return; }
        else if (a.do === "show") { tl.set(objs[a.target], { opacity: 1 }, t); return; }
        else if (a.do === "punch") { const o = MG.inner(objs[a.target]); gsap.set(o, { transformOrigin: "50% 50%" }); tl.to(o, { scale: `*=${a.scale || 1.15}`, duration: 0.12, ease: "power3.out", yoyo: true, repeat: 1 }, t); return; }
        if (!node) return;
        objs[id] = node;
        if (a.do === "text") {
          gsap.set(node, { opacity: 1 });
          MG.write(tl, node, t, a.write || Math.max(0.35, Math.min(1.4, (a.text || "").length * 0.045)), { noPencil: a.noPencil });
        } else if (a.draw) {
          gsap.set(node, { opacity: 0 });
          tl.set(node, { opacity: 1 }, t);
          MG.draw(tl, node, t, a.draw, { noPencil: a.noPencil, ease: a.ease });
        } else {
          MG.pop(tl, node, t, { dur: a.pop || 0.35, origin: a.origin });
        }
      });
      if (sc.exit === "erase") MG.erase(tl, g, sc.out, sc.exitDur || 0.55, eraserG);
      else if (sc.exit === "fade") { tl.to(g, { opacity: 0, duration: sc.exitDur || 0.35 }, sc.out); }
      else if (sc.exit === "drop") { tl.to(g, { y: 1200, opacity: 0, duration: sc.exitDur || 0.5, ease: "power2.in" }, sc.out); }
    });

    // face punch-ins on cuts
    const faceInner = document.getElementById("face-inner");
    gsap.set(faceInner, { transformOrigin: "50% 42%" });
    (PLAN.punches || []).forEach((p) => tl.set(faceInner, { scale: p.scale }, p.t));

    // CTA: face shrinks to a circle, captions move up, board goes full frame
    if (PLAN.cta) {
      const c = PLAN.cta;
      const wrap = document.getElementById("face-wrap");
      gsap.set(wrap, { transformOrigin: "0 0" });
      tl.to(wrap, { x: c.pipX, y: c.pipY, scale: c.pipScale, duration: 0.75, ease: "power3.inOut" }, c.at);
      tl.to(wrap, { clipPath: "circle(44% at 50% 48%)", duration: 0.6, ease: "power2.inOut" }, c.at + 0.1);
      tl.to("#tear", { opacity: 0, duration: 0.3 }, c.at);
      tl.to("#captions", { y: c.capY, duration: 0.75, ease: "power3.inOut" }, c.at);
      tl.to("#grad-bottom", { opacity: 1, duration: 0.5 }, c.at);
    }

    MG.captions(tl, PLAN.captions, "var(--cap-accent)");
    return tl;
};
