/* Pacsi Marketing – videókompozíció-futtató.
   Egy videó = időfüggvény. A kompozíció a Comp.at(t, fn) eseményeket és a Comp.each(fn) képkocka-rajzolókat
   regisztrálja, a futtató pedig requestAnimationFrame-ben hívja őket. Rendereléskor (render.mjs) az idő
   virtuális, így minden képkocka pontos; böngészőben megnyitva valós időben lejátszható előnézet. */
(() => {
  const Q = new URLSearchParams(location.search);
  const RENDER = Q.has('render');
  const cues = [], each = [];
  let meta = { duration: 10, preroll: 0 }, t0 = null;

  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const E = {
    lin: p => p,
    inQ: p => p * p, outQ: p => 1 - (1 - p) * (1 - p),
    inC: p => p * p * p, outC: p => 1 - Math.pow(1 - p, 3), ioC: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
    outQuint: p => 1 - Math.pow(1 - p, 5), ioQuint: p => p < .5 ? 16 * p ** 5 : 1 - Math.pow(-2 * p + 2, 5) / 2,
    outBack: (p, s = 1.7) => 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2),
    outExpo: p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p),
    ioSine: p => -(Math.cos(Math.PI * p) - 1) / 2,
    // csillapított rugó (túllövéssel), p: 0..1 → kb. 0..1
    spring: (p, k = 5.2, d = 4.2) => p >= 1 ? 1 : 1 - Math.exp(-d * p * 1.6) * Math.cos(k * p * Math.PI * 1.15),
  };
  /** 0..1 haladás a [a,b] intervallumban, opcionális easinggel */
  const prog = (t, a, b, e = E.lin) => e(clamp((t - a) / (b - a)));
  /** tween(t, a, b, from, to, easing) */
  const tw = (t, a, b, from, to, e = E.outC) => lerp(from, to, prog(t, a, b, e));
  /** be- és kiúsztatás: 0 → 1 (tIn…tIn+dIn), 1 → 0 (tOut…tOut+dOut) */
  const inout = (t, tIn, tOut, dIn = .45, dOut = .35, eIn = E.outC, eOut = E.inQ) =>
    t < tOut ? prog(t, tIn, tIn + dIn, eIn) : 1 - prog(t, tOut, tOut + dOut, eOut);

  function loop() {
    const tick = () => {
      requestAnimationFrame(tick);
      const now = performance.now();
      if (t0 === null) t0 = now;
      const t = (now - t0) / 1000 - (meta.preroll || 0);
      for (const c of cues) if (!c.done && c.t <= t) { c.done = true; try { c.fn(t); } catch (e) { console.error(e); } }
      for (const f of each) { try { f(t); } catch (e) { console.error(e); } }
      if (!RENDER && t > meta.duration + .5 && Q.has('loop')) location.reload();
    };
    requestAnimationFrame(tick);
  }

  window.Comp = {
    RENDER, E, clamp, lerp, prog, tw, inout,
    at(t, fn) { cues.push({ t, fn, done: false }); cues.sort((a, b) => a.t - b.t); },
    each(fn) { each.push(fn); },
    /** meta: {duration, preroll}; setup: async előkészítés (képek, iframe) */
    start(m, setup) {
      meta = { ...meta, ...m };
      window.__comp = meta;
      document.documentElement.classList.toggle('rendering', RENDER);
      window.__compReady = (async () => {
        await document.fonts.ready;
        if (setup) await setup();
        await document.fonts.ready;
        loop();
        return true;
      })();
    },
  };
})();
