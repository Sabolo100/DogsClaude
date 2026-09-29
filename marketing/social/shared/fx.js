/* Pacsi Marketing – mozgásépítőkockák a videókhoz: szavankénti felugrás, matrica-pop, kulcskockás
   kamerapálya, úszó háttérfoltok, portré-robbanás és a közös záróképernyő. Minden függvény a t időből
   (másodperc) számol, így a képkockák determinisztikusak. */
(() => {
  const { E, clamp, lerp, prog } = Comp;

  /** Szövegcsomópontok szavakra bontása (a belső elemek – pl. <span class="it"> – megmaradnak) */
  function words(el) {
    const walk = n => {
      for (const c of [...n.childNodes]) {
        if (c.nodeType === 3) {
          const parts = c.textContent.split(/(\s+)/);
          const frag = document.createDocumentFragment();
          for (const p of parts) {
            if (!p) continue;
            if (/^\s+$/.test(p)) frag.appendChild(document.createTextNode(p));
            else { const s = document.createElement('span'); s.className = 'w'; s.textContent = p; frag.appendChild(s); }
          }
          c.replaceWith(frag);
        } else if (c.nodeType === 1 && !c.classList.contains('w')) walk(c);
      }
    };
    walk(el);
    return [...el.querySelectorAll('.w')];
  }

  /** Szavankénti rugós felugrás; out: eltűnés ideje (vagy null) */
  function popWords(ws, t, t0, { stagger = .07, dur = .55, dy = 60, out = null, outDur = .3, sc = .82 } = {}) {
    ws.forEach((w, i) => {
      const p = prog(t, t0 + i * stagger, t0 + i * stagger + dur);
      const sp = E.spring(p), o = clamp(p * 3);
      let q = 1;
      if (out != null) q = 1 - prog(t, out + i * stagger * .4, out + i * stagger * .4 + outDur, E.inQ);
      w.style.opacity = (o * q).toFixed(3);
      w.style.transform = `translateY(${(1 - sp) * dy + (1 - q) * -30}px) scale(${lerp(sc, 1, sp)})`;
    });
  }

  /** Matrica/elem rugós be- és kiúsztatása */
  function pop(el, t, tIn, tOut = 1e9, { rot = 0, from = .55, dy = 0, dur = .5 } = {}) {
    const p = prog(t, tIn, tIn + dur), sp = E.spring(p, 5.6, 4.4);
    const q = 1 - prog(t, tOut, tOut + .28, E.inQ);
    const s = lerp(from, 1, sp) * lerp(.8, 1, q);
    el.style.opacity = (clamp(p * 2.5) * q).toFixed(3);
    el.style.transform = `translate(-50%,-50%) translateY(${(1 - sp) * dy}px) rotate(${rot}deg) scale(${s})`;
    el.style.visibility = p > 0 && q > 0 ? 'visible' : 'hidden';
  }

  /** Kulcskockás pálya: keys = [[t, {x,y,s,r}, easing?], …] → f(t) */
  function track(keys) {
    return t => {
      if (t <= keys[0][0]) return { ...keys[0][1] };
      for (let i = 1; i < keys.length; i++) {
        const [t1, v1, e] = keys[i], [t0, v0] = keys[i - 1];
        if (t <= t1) {
          const p = (e || E.ioC)(clamp((t - t0) / (t1 - t0)));
          const o = {};
          for (const k in v1) o[k] = lerp(v0[k] ?? v1[k], v1[k], p);
          for (const k in v0) if (!(k in o)) o[k] = v0[k];
          return o;
        }
      }
      return { ...keys[keys.length - 1][1] };
    };
  }

  /** Úszó háttérfoltok a vásznon */
  function blobs(host, cols = ['#FFD2B8', '#E2D6FF', '#C9EEDC']) {
    const el = document.createElement('div');
    el.className = 'vblobs';
    el.innerHTML = cols.map(c => `<i style="background:radial-gradient(closest-side, ${c}, rgba(255,255,255,0))"></i>`).join('');
    host.prepend(el);
    const is = [...el.children];
    const P = [[-250, -250, 1300, .11, .07], [480, 700, 1300, .08, .10], [-200, 1250, 1200, .09, .06]];
    return t => is.forEach((i, k) => {
      const [x, y, d, fx, fy] = P[k];
      i.style.transform = `translate(${x + Math.sin(t * fx * 2 + k) * 90}px, ${y + Math.cos(t * fy * 2 + k * 2) * 80}px)`;
      i.style.width = i.style.height = d + 'px';
    });
  }

  /** Portré-robbanás: buborékok a középpontból a felhő-helyükre, majd lebegés. Visszaad: update(t) */
  function burst(host, items, { cx = 540, cy = 960, t0 = 0, dur = .9, stagger = .018, float = 6 } = {}) {
    const els = items.map((it, i) => {
      const e = document.createElement('div');
      e.className = 'bub';
      e.style.cssText = `--d:${it.d}px;left:${-it.d / 2}px;top:${-it.d / 2}px;width:${it.d}px;height:${it.d}px;background-image:url('${K.img(it.id)}');z-index:${2 + (i % 5)}`;
      host.appendChild(e);
      return e;
    });
    return (t, { gather = null, gx = cx, gy = cy, gs = .2 } = {}) => els.forEach((e, i) => {
      const it = items[i];
      const p = prog(t, t0 + i * stagger, t0 + i * stagger + dur);
      const sp = E.spring(p, 4.6, 4.2);
      let x = lerp(cx, it.x, sp) + Math.sin(t * 1.3 + i) * float * clamp(p * 2);
      let y = lerp(cy, it.y, sp) + Math.cos(t * 1.1 + i * 1.7) * float * clamp(p * 2);
      let s = lerp(.2, 1, E.outBack(clamp(p * 1.1)));
      let o = clamp(p * 4);
      if (gather) {
        const g = prog(t, gather + (items.length - i) * .006, gather + .55 + (items.length - i) * .006, E.inC);
        x = lerp(x, gx, g); y = lerp(y, gy, g); s *= lerp(1, gs, g); o *= 1 - prog(t, gather + .45, gather + .75);
      }
      e.style.opacity = o.toFixed(3);
      e.style.transform = `translate(${x}px,${y}px) scale(${s}) rotate(${(1 - sp) * (i % 2 ? 40 : -40)}deg)`;
    });
  }

  /** Közös záróképernyő: integető kabala + logó (mancs-pacsival) + CTA. Visszaad: update(t) – t0-tól indul. */
  function endCard(host, { t0, line = 'Találd meg a hozzád illő kutyát!', cta = 'Próbáld ki ingyen', url = '', ask = '' } = {}) {
    const el = document.createElement('div');
    el.className = 'endcard';
    el.innerHTML = `<div class="ec-bg"></div>
      <div class="ec-ring"></div>
      <img class="ec-pup" src="${K.kv('kv_mascot_wave')}" alt="">
      <div class="ec-logo">${K.logo(150, { by: false })}</div>
      <div class="ec-by">by <b>DarwinAI</b></div>
      <div class="ec-line">${line}</div>
      <div class="ec-cta"><span class="cta">${K.ic('sparkle', 40)} ${cta}</span></div>
      <div class="ec-url">${url}</div>
      ${ask ? `<div class="ec-ask"><span class="sticker">${ask}</span></div>` : ''}`;
    host.appendChild(el);
    const ring = el.querySelector('.ec-ring'), pup = el.querySelector('.ec-pup');
    const ids = ['cavalier-king-charles-spaniel', 'magyar-vizsla', 'puli', 'golden-retriever', 'bichon-frise', 'border-collie', 'mopsz', 'szamojed'];
    const spots = [[120, 520], [960, 470], [95, 900], [985, 860], [150, 1300], [930, 1260], [330, 250], [760, 230]];
    const bs = ids.map((id, i) => { const b = document.createElement('div'); b.className = 'bub'; const d = i < 6 ? 150 : 118; b.style.cssText = `--d:${d}px;left:${-d / 2}px;top:${-d / 2}px;width:${d}px;height:${d}px;background-image:url('${K.img(id)}')`; ring.appendChild(b); return b; });
    const paw = el.querySelector('.ec-logo .i svg');
    const parts = ['.ec-logo', '.ec-by', '.ec-line', '.ec-cta', '.ec-url', '.ec-ask'].map(q => el.querySelector(q));
    return t => {
      el.style.visibility = t >= t0 ? 'visible' : 'hidden';
      if (t < t0) return;
      const a = prog(t, t0, t0 + .55, E.outC);
      el.querySelector('.ec-bg').style.clipPath = `circle(${a * 150}% at 50% 60%)`;
      const pp = prog(t, t0 + .15, t0 + .95), sp = E.spring(pp, 5, 4.2);
      const wave = Math.sin((t - t0) * 5.2) * 2.2 * clamp(pp * 2);
      pup.style.opacity = clamp(pp * 3).toFixed(3);
      pup.style.transform = `translateX(-50%) translateY(${(1 - sp) * 220}px) scale(${lerp(.7, 1, sp)}) rotate(${wave}deg)`;
      bs.forEach((b, i) => {
        const p = prog(t, t0 + .3 + i * .05, t0 + 1 + i * .05), q = E.spring(p);
        const [x, y] = spots[i];
        b.style.opacity = clamp(p * 3).toFixed(3);
        b.style.transform = `translate(${x + Math.sin(t * 1.2 + i) * 10}px, ${y + Math.cos(t + i * 1.3) * 12}px) scale(${lerp(.3, 1, q)})`;
      });
      parts.forEach((p, i) => { if (!p) return; const q = prog(t, t0 + .45 + i * .12, t0 + 1.05 + i * .12); const s2 = E.spring(q);
        p.style.opacity = clamp(q * 3).toFixed(3); p.style.transform = `translate(-50%,0) translateY(${(1 - s2) * 50}px) scale(${lerp(.8, 1, s2)})`; });
      const h5 = prog(t, t0 + 1.1, t0 + 2.0);
      const lift = Math.sin(h5 * Math.PI), tilt = Math.sin(h5 * Math.PI * 2) * 22;
      if (paw) paw.style.transform = `translateX(-50%) translateY(${-lift * 16}px) rotate(${-12 + tilt}deg) scale(${1 + lift * .35})`;
    };
  }

  window.FX = { words, popWords, pop, track, blobs, burst, endCard };
})();
