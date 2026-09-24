/* ==========================================================================
   Színpad: buborékok, fizika, nézetek, effektek
   ========================================================================== */
const stage = $('#stage'), bubblesEl = $('#bubbles'), tipEl = $('#tip');
const BASE0 = S.mobile ? 24 : 40;                // a buborék-elem kezdő natív sugara – a pillanatnyi méretet scale adja (lásd fitBase)
const DEPTH = { back: -1, mid: -.35, '': 0, front: .5, top: 1 };
const ZI = { back: 1, mid: 2, '': 3, front: 4, top: 5 };
const FX_COLORS = ['#FF6B3D', '#FFC845', '#17756E', '#A58BFF', '#7ED6B1', '#FF8FA3', '#5AB0F0'];
let SR = stage.getBoundingClientRect();
let LR = { l: 0, t: 0, r: 100, b: 100, w: 100, h: 100, cx: 50, cy: 50 };
let OBS = [];
let fill = 1;
const mouse = { tx: 0, ty: 0, px: 0, py: 0, x: 0, y: 0, in: false };
let hovered = null, focusedO = null, hoverTimer = 0;
let groupsLayout = [];
let flownShown = 0;
let FLY = null;   // a felhőjelvény helye – mérésenként egyszer számolva (ne kényszerítsünk elrendezést buborékonként)

/* ---------- Buborékok létrehozása ---------- */
const B = BREEDS.map(b => {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = 'b';
  el.tabIndex = -1;
  el.setAttribute('role', 'listitem');
  el.setAttribute('aria-label', b.nev);
  el.style.cssText = `${picStyle(b)};--s:${BASE0 * 2}px`;
  // A gyűrű, a glória és a pulzus nem DOM-elem, hanem a közös alsó vásznon rajzolódik (drawUnder) –
  // így szűréskor nem kell 124 réteget képkockánként újrarajzolni.
  el.innerHTML = `<span class="face"></span><span class="fav-b">${ic('heart-f')}</span><span class="cmp-b">${ic('compare')}</span>`;
  bubblesEl.appendChild(el);
  return {
    b, el,
    x: 0, y: 0, vx: 0, vy: 0, r: 0, rv: 0, rt: 0, hk: 1, jy: 0, jv: 0, rx: 0, ry: 0, rr: 0,
    ph: rand(0, 6.283), st: 'in', tier: '', vis: true, pend: null, op: 1, fly: null, grp: null, mx: 0, my: 0,
    opT: 1, opC: 1, ringT: 0, ringV: 0, glowV: 0, dim: false, base: BASE0, stirN: -99,
  };
});
/* A buborék-elem natív mérete a célméretéhez igazodik. A böngésző a will-change: transform rétegeket
   natív méretükben rajzolja (kicsinyítve sem kisebbet), így a natív méretnek a képernyőn látotthoz
   kell közel lennie – különben telefonon elfogy a grafikus memória. Csak ±20 %-on túli célváltozásnál
   méretezünk át (akkor a réteg újrarajzolódik); desktopon ráhagyással, hogy a hover-nagyítás is éles maradjon. */
function fitBase(o) {
  if (!o.rt || (o.st !== 'in' && o.st !== 'drop')) return;
  const want = Math.max(8, o.rt * (S.mobile ? 1.08 : 1.22));
  if (want > o.base * 1.2 || want < o.base * .8) {
    o.base = Math.round(want);
    o.el.style.setProperty('--s', `${o.base * 2}px`);
  }
}
const PULSES = [];
const underC = $('#under'), ux = underC.getContext('2d');
let underDpr = 1, underDirty = false, ringRGB = [255, 107, 61];
const hexRGB = h => { const m = /^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(h.trim()); return m ? [1, 2, 3].map(i => parseInt(m[i], 16)) : [255, 107, 61]; };
const BY_EL = new Map(B.map(o => [o.el, o]));
const OB_ID = new Map(B.map(o => [o.b.id, o]));
const markFav = () => B.forEach(o => { o.el.classList.toggle('fav', S.fav.has(o.b.id)); o.el.classList.toggle('cmp', S.cmp.includes(o.b.id)); });

/* ---------- Mérés: elrendezési téglalap + akadályok ---------- */
function sheetCover() {
  // Ami a színpadot takarja: desktopon a jobb oldali fiók, mobilon az alsó lap
  // (offset-méretekből számolva, mert a becsúszó animáció alatt a getBoundingClientRect még a kezdőállapotot adná)
  const d = $('#drawer');
  if (d && !d.hidden && !d.classList.contains('out')) return S.mobile ? { top: innerHeight - d.offsetHeight, left: innerWidth } : { top: 0, left: innerWidth - 18 - d.offsetWidth };
  const p = $('#panel');
  if (S.mobile && p.classList.contains('open')) return { top: innerHeight - p.offsetHeight, left: innerWidth };
  return null;
}
function measure() {
  SR = stage.getBoundingClientRect();
  const m = S.mobile;
  // alsó vászon (gyűrűk, glória, pulzus) a színpad méretén; legfeljebb 1,5× felbontás
  underDpr = Math.min(devicePixelRatio || 1, 1.5);
  const cw = Math.round(SR.width * underDpr), ch = Math.round(SR.height * underDpr);
  if (underC.width !== cw || underC.height !== ch) { underC.width = cw; underC.height = ch; underDirty = true; }
  ringRGB = hexRGB(getComputedStyle(document.documentElement).getPropertyValue('--primary') || '#FF6B3D');
  let l = m ? 8 : 18, t = m ? 48 : 14, r = SR.width - (m ? 8 : 18), bt = SR.height - (m ? 46 : 16);
  const cov = sheetCover();
  if (cov) {
    if (!m && cov.left < SR.right) r = Math.min(r, cov.left - SR.left - 14);
    if (m && cov.top < SR.bottom) bt = Math.min(bt, cov.top - SR.top - 8);
  }
  if (!m && (S.view === 'csoport' || S.view === 'terkep')) {
    const hud = $('#hud').getBoundingClientRect();
    t = Math.max(t, hud.bottom - SR.top + 8);
  }
  if (bt - t < 110) bt = t + 110;
  if (r - l < 160) r = l + 160;
  LR = { l, t, r, b: bt, w: r - l, h: bt - t, cx: (l + r) / 2, cy: (t + bt) / 2 };
  OBS = [];
  const add = (el, pad = 8) => {
    if (!el || el.hidden) return;
    const q = el.getBoundingClientRect();
    if (!q.width || !q.height) return;
    OBS.push({ l: q.left - SR.left - pad, t: q.top - SR.top - pad, r: q.right - SR.left + pad, b: q.bottom - SR.top + pad });
  };
  if (!m) {
    add($('#odo')); add($('.of')); add($('#modeSeg')); add($('#groupSeg'));
    $$('.achip').forEach(e => add(e, 6));
    add($('#tray'), 12);
  } else {
    add($('#mobViews'), 6); add($('#mobMode'), 6); add($('#mobClear'), 6);
  }
  FLY = m ? flyTarget() : null;
}

/* ---------- Célméretek (13. fejezet) ---------- */
function computeTargets() {
  const active = S.crit.length > 0;
  const strict = modeOf() === 'strict';
  const list = S.view === 'lista';
  for (const o of B) {
    const b = o.b;
    o.nvis = !list && !(strict && active && !b.ok);
    let s = 1, tier = '';
    if (active) {
      if (strict) { s = .8 + .45 * b.m; tier = b.m > .97 ? 'top' : 'front'; }
      else {
        s = .55 + Math.pow(b.m, 1.25) + (b.ok ? .12 : 0);
        tier = b.ok ? 'top' : b.m >= .62 ? 'front' : b.m >= .32 ? 'mid' : 'back';
      }
    }
    o.ns = s;
    o.ntier = tier;
  }
  const vis = B.filter(o => o.nvis);
  const rho = { felho: S.mobile ? .6 : .6, csoport: S.mobile ? .34 : .33, terkep: S.mobile ? .22 : .24, lista: .5 }[S.view];
  const obsA = OBS.reduce((a, q) => a + Math.max(0, Math.min(q.r, LR.r) - Math.max(q.l, LR.l)) * Math.max(0, Math.min(q.b, LR.b) - Math.max(q.t, LR.t)), 0);
  const A = Math.max(LR.w * LR.h - obsA, 20000);
  const sum = vis.reduce((a, o) => a + o.ns * o.ns, 0) || 1;
  const r0 = clamp(Math.sqrt(rho * A / (Math.PI * sum)) * fill, S.mobile ? 14 : 16, S.mobile ? 86 : 88);
  const rMax = Math.min(LR.w, LR.h) * .3;
  for (const o of B) o.nrt = Math.min(r0 * o.ns, rMax);
  if (S.view === 'csoport') layoutGroups(vis);
  if (S.view === 'terkep') layoutMap();
}

/* ---------- Csoportosítás ---------- */
const REGIONS = [
  ['Magyar', ['Magyarország', 'Erdély']],
  ['Brit-szigetek', ['Egyesült Királyság', 'Írország']],
  ['Német nyelvterület', ['Németország', 'Svájc', 'Ausztria']],
  ['Nyugat-Európa', ['Franciaország', 'Belgium', 'Hollandia']],
  ['Dél-Európa', ['Olaszország', 'Spanyolország', 'Portugália', 'Horvátország', 'Földközi', 'Málta']],
  ['Kelet-Európa', ['Oroszország', 'Szibéria', 'Kaukázus', 'Csehország', 'Lengyelország']],
  ['Ázsia', ['Japán', 'Kína', 'Tibet', 'Közép-Ázsia', 'Afganisztán', 'Közel-Kelet']],
  ['Amerika', ['USA', 'Kanada', 'Mexikó', 'Kuba']],
  ['Afrika, Óceánia', ['Afrika', 'Zimbabwe', 'Kongó', 'Madagaszkár', 'Ausztrália']],
];
const region = s => (REGIONS.find(([, keys]) => keys.some(k => s.includes(k))) || ['Egyéb'])[0];
const GPAL = ['#FF6B3D', '#17756E', '#5B5BD6', '#E86A92', '#C7772B', '#2FA3D6', '#8A63D2', '#2E9E6A', '#E0A21B', '#6E7B8B'];
const GROUPERS = {
  // ha méretszűrő aktív, a fajta a kiválasztott méretcsoportba kerül (pl. „Óriás” szűrésnél a nagy–óriás cane corso az Óriásba)
  meret: { l: 'Méret', key: b => b.meret.find(v => S.f.meret.has(v)) || b.meret[Math.floor((b.meret.length - 1) / 2)], order: SIZES.map(s => s[0]), label: k => SIZE_L[k], color: k => ['#E86A92', '#FF8A5B', '#E0A21B', '#17756E', '#5B5BD6'][SIZE_I[k]] },
  fci: { l: 'FCI', key: b => b.fci, order: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], label: k => `${k}. ${FCI[k]}`, color: k => GPAL[(k - 1) % GPAL.length] },
  szerep: { l: 'Szerep', key: b => b.szerep[0], order: ROLES.map(r => r[0]), label: k => ROLE_L[k], color: k => ROLE_C[k] },
  szor: { l: 'Szőr', key: b => b.szor[0], order: COATS.map(c => c[0]), label: k => COAT_L[k], color: k => GPAL[COATS.findIndex(c => c[0] === k) % GPAL.length] },
  orszag: { l: 'Származás', key: b => region(b.orszag), order: REGIONS.map(r => r[0]).concat('Egyéb'), label: k => k, color: k => GPAL[Math.max(0, REGIONS.findIndex(r => r[0] === k)) % GPAL.length] },
  energia: { l: 'Energia', key: b => b.t.E <= 2 ? 'nyugis' : b.t.E === 3 ? 'mersekelt' : 'sportos', order: ['nyugis', 'mersekelt', 'sportos'], label: k => ({ nyugis: 'Nyugis', mersekelt: 'Mérsékelt', sportos: 'Sportos' })[k], color: k => ({ nyugis: '#5B5BD6', mersekelt: '#E0A21B', sportos: '#FF6B3D' })[k] },
};
function layoutGroups(vis) {
  const G = GROUPERS[S.groupBy] || GROUPERS.meret;
  const map = new Map();
  for (const o of vis) {
    const k = G.key(o.b);
    if (!map.has(k)) map.set(k, []);
    map.get(k).push(o);
  }
  const keys = G.order.filter(k => map.has(k)).concat([...map.keys()].filter(k => !G.order.includes(k)));
  // ha a csoportok túl nagyok lennének, arányosan kicsinyítünk
  let groups = keys.map(k => {
    const mem = map.get(k);
    return { key: String(k), k, label: G.label(k), color: G.color(k), n: mem.length, mem, area: mem.reduce((a, o) => a + o.nrt * o.nrt, 0) };
  });
  const need = groups.reduce((a, g) => a + Math.PI * Math.pow(Math.sqrt(g.area / .55) + 30, 2), 0);
  const scale = Math.min(1, Math.sqrt(LR.w * LR.h * .62 / need));
  if (scale < 1) for (const g of groups) { g.mem.forEach(o => { o.nrt *= scale; }); g.area *= scale * scale; }
  groups.forEach((g, i) => {
    g.R = Math.sqrt(g.area / .55) + 8;
    const prev = groupsLayout.find(p => p.key === g.key);
    const ang = i / groups.length * Math.PI * 2 - Math.PI / 2;
    g.x = prev ? prev.x : LR.cx + Math.cos(ang) * LR.w * .3;
    g.y = prev ? prev.y : LR.cy + Math.sin(ang) * LR.h * .3;
  });
  const relax = () => { for (let it = 0; it < 360; it++) {
    for (const g of groups) { g.x += (LR.cx - g.x) * .01 * Math.pow(LR.h / LR.w, 2); g.y += (LR.cy - g.y) * .01; }
    for (let i = 0; i < groups.length; i++) for (let j = i + 1; j < groups.length; j++) {
      const a = groups[i], c = groups[j];
      let dx = c.x - a.x, dy = c.y - a.y, d = Math.hypot(dx, dy) || .01;
      const min = a.R + c.R + 40;
      if (d < min) {
        const push = (min - d) / 2;
        dx /= d; dy /= d;
        a.x -= dx * push; a.y -= dy * push; c.x += dx * push; c.y += dy * push;
      }
    }
    for (const g of groups) {
      g.x = clamp(g.x, LR.l + g.R, Math.max(LR.l + g.R, LR.r - g.R));
      g.y = clamp(g.y, LR.t + g.R + 30, Math.max(LR.t + g.R + 30, LR.b - g.R));
    }
  } };
  // ha a keret miatt átfedés maradna, arányosan kicsinyítünk és újra rendezünk
  for (let tries = 0; tries < 5; tries++) {
    relax();
    let ov = 0;
    for (let i = 0; i < groups.length; i++) for (let j = i + 1; j < groups.length; j++) {
      const a = groups[i], c = groups[j];
      ov = Math.max(ov, a.R + c.R + 24 - Math.hypot(c.x - a.x, c.y - a.y));
    }
    if (ov <= 0) break;
    for (const g of groups) { g.mem.forEach(o => { o.nrt *= .88; }); g.R = (g.R - 8) * .88 + 8; }
  }
  for (const g of groups) for (const o of g.mem) o.grp = g;
  groupsLayout = groups;
}
function drawGroups() {
  const box = $('#groups');
  const on = S.view === 'csoport';
  const seen = new Set();
  if (on) for (const g of groupsLayout) {
    seen.add(g.key);
    let blob = box.querySelector(`.gblob[data-k="${CSS.escape(g.key)}"]`);
    let lab = box.querySelector(`.glabel[data-k="${CSS.escape(g.key)}"]`);
    if (!blob) {
      blob = document.createElement('div'); blob.className = 'gblob'; blob.dataset.k = g.key; box.appendChild(blob);
      lab = document.createElement('div'); lab.className = 'glabel'; lab.dataset.k = g.key; box.appendChild(lab);
      blob.style.transform = `translate(${g.x - 80}px,${g.y - 80}px) scale(.5)`;
    }
    // fix 160 px-es elem, a méretet scale adja → csak transform animálódik (nincs újrarajzolás);
    // kicsi natív méret, mert animáció közben a böngésző legalább natív méretben rajzolja a réteget
    const D = g.R * 2 + 36;
    blob.style.setProperty('--gc', g.color);
    blob.style.transform = `translate(${g.x - 80}px,${g.y - 80}px) scale(${(D / 160).toFixed(3)})`;
    lab.style.setProperty('--gc', g.color);
    lab.innerHTML = `${esc(g.label)}<b>${g.n}</b>`;
    lab.style.transform = `translate(${g.x}px,${g.y - g.R - 14}px) translate(-50%,-100%)`;
    // csak akkor kapcsoljuk be, ha a csoport a következő képkockában is létezik (gyors egymás utáni váltásnál ne ragadjon be)
    requestAnimationFrame(() => {
      if (S.view === 'csoport' && groupsLayout.some(x => x.key === g.key)) { blob.classList.add('on'); lab.classList.add('on'); }
    });
  }
  $$('.gblob, .glabel', box).forEach(e => { if (!seen.has(e.dataset.k)) e.classList.remove('on'); });
}

/* ---------- Térkép nézet: méret × energia ---------- */
function layoutMap() {
  const px = S.mobile ? 26 : 70, py = S.mobile ? 20 : 34;
  const lw = Math.log(1.5), hw = Math.log(80);
  for (const o of B) {
    const b = o.b;
    const w = (b.suly[0] + b.suly[1]) / 2;
    const fx = clamp((Math.log(w) - lw) / (hw - lw), 0, 1);
    const jit = ((b.n * 37) % 11) / 10 - .5;
    const fy = clamp((5 - (b.t.E + jit * .7)) / 4.7 + .04, 0, 1);
    o.mx = LR.l + px + fx * (LR.w - px * 1.5);
    o.my = LR.t + py + fy * (LR.h - py * 2.2);
  }
  // Sok hasonló (nagy, energikus) fajta célpontja szinte egybeesik: a rugó egy pontba húzná őket, az
  // ütközés széttolná – ettől rángatóztak kis kijelzőn. Ezért a célpontokat előre szétterítjük
  // („méhraj”), a fizikával azonos távolsággal: nyugalomban így nincs mi ellen dolgozniuk.
  const vis = B.filter(o => o.nvis), gap = S.mobile ? 4 : 6;
  for (let it = 0; it < 90; it++) {
    let moved = false;
    for (let i = 0; i < vis.length; i++) {
      const a = vis[i];
      for (let j = i + 1; j < vis.length; j++) {
        const c = vis[j], min = (a.nrt + c.nrt) * 1.09 + gap;
        let dx = c.mx - a.mx, dy = c.my - a.my;
        if (dx > min || dx < -min || dy > min || dy < -min) continue;
        const d2 = dx * dx + dy * dy;
        if (d2 >= min * min) continue;
        let d = Math.sqrt(d2);
        if (d < .01) { dx = Math.cos(i * 2.4 + j); dy = Math.sin(i * 2.4 + j); d = 1; }   // egybeeső pontok
        const push = (min - d) / 2 / d;
        a.mx -= dx * push; a.my -= dy * push;
        c.mx += dx * push; c.my += dy * push;
        moved = true;
      }
    }
    for (const o of vis) {
      const R = o.nrt * 1.09;
      o.mx = clamp(o.mx, LR.l + R, Math.max(LR.l + R, LR.r - R));
      o.my = clamp(o.my, LR.t + R, Math.max(LR.t + R, LR.b - R));
    }
    if (!moved) break;
  }
}
function drawMap() {
  const svg = $('#mapLayer');
  if (S.view !== 'terkep') { svg.classList.remove('on'); return; }
  const x0 = LR.l + (S.mobile ? 8 : 26), x1 = LR.r - 4, y0 = LR.t + 4, y1 = LR.b - (S.mobile ? 4 : 10);
  const mx = (x0 + x1) / 2, my = (y0 + y1) / 2, fs = S.mobile ? 17 : 34;
  svg.innerHTML = `
    <line class="grid" x1="${mx}" y1="${y0}" x2="${mx}" y2="${y1}"/><line class="grid" x1="${x0}" y1="${my}" x2="${x1}" y2="${my}"/>
    <path class="axis" d="M${x0} ${y0} L${x0} ${y1} L${x1} ${y1}"/>
    <path class="axis" d="M${x0 - 6} ${y0 + 10} L${x0} ${y0} L${x0 + 6} ${y0 + 10} M${x1 - 10} ${y1 - 6} L${x1} ${y1} L${x1 - 10} ${y1 + 6}"/>
    <g style="font-size:${fs}px">
      <text class="quad" x="${x0 + 18}" y="${y0 + fs + 6}">Zsebrakéták</text>
      <text class="quad" x="${x1 - 14}" y="${y0 + fs + 6}" text-anchor="end">Sportgépek</text>
      <text class="quad" x="${x0 + 18}" y="${y1 - 16}">Nyugis törpék</text>
      <text class="quad" x="${x1 - 14}" y="${y1 - 16}" text-anchor="end">Kanapé-óriások</text>
    </g>
    <text class="axl" x="${mx}" y="${y1 + 15}" text-anchor="middle">kicsi  ←  MÉRET  →  nagy</text>
    <text class="axl" transform="translate(${x0 - 9} ${my}) rotate(-90)" text-anchor="middle">nyugis  ←  ENERGIA  →  pörgős</text>`;
  svg.classList.remove('on');
  requestAnimationFrame(() => svg.classList.add('on'));
}

/* ---------- Állapotváltás: kiértékelés → célok → hullám ---------- */
function refresh(src = null, opts = {}) {
  evaluate();
  bus.emit('pre');
  measure();
  computeTargets();
  schedule(src, opts);
  drawGroups();
  drawMap();
  bus.emit('post');
  syncHash();
}
function schedule(src, { intro = false, instant = false } = {}) {
  const t0 = now();
  const rm = RM();
  for (const o of B) {
    let delay = 0;
    if (intro) delay = 120 + o.introIdx * (B.length > 90 ? 6 : 10);
    else if (src && !rm && !instant) delay = Math.min(Math.hypot(o.x - src.x, o.y - src.y) * .5, 650) + rand(0, 40);
    o.pend = { at: t0 + delay, vis: o.nvis, rt: o.nrt, tier: o.ntier, m: o.b.m };
  }
}
function commit(o, p) {
  o.pend = null;
  const wasTier = o.tier, grew = p.rt > o.rt * 1.04;
  o.rt = p.rt;
  if (p.tier !== o.tier) {
    o.tier = p.tier;
    if (p.tier) o.el.dataset.tier = p.tier; else delete o.el.dataset.tier;
    o.el.style.zIndex = ZI[p.tier] || 3;
  }
  // a mélységi halványítás a buborék saját rétegének átlátszóságával megy (render-ben simítva) –
  // ez kompozitor-művelet, nem kell hozzá újrarajzolás
  o.opT = p.tier === 'back' ? .45 : p.tier === 'mid' ? .9 : 1;
  o.ringT = p.m == null ? 0 : p.m;
  if (p.vis && !o.vis) enter(o);
  else if (!p.vis && o.vis) leave(o);
  o.vis = p.vis;
  if (p.vis && !RM() && o.st === 'in') {
    if (p.tier === 'top' && wasTier !== 'top' && S.crit.length) { pulse(o); o.jv = -7; }
    else if (grew) o.jv = -4.5;
  }
}
function pulse(o) {
  if (PULSES.length < 40) PULSES.push({ o, t0: now() });
}
function flyTarget() {
  const el = $('#flyCloud');
  if (!el || el.hidden) return null;
  const q = el.getBoundingClientRect();
  if (!q.width) return null;
  return { tx: q.left + q.width / 2 - SR.left, ty: q.top + q.height / 2 - SR.top };
}
function leave(o) {
  if (hovered === o) setHover(null);
  if (RM()) { o.st = 'gone'; o.el.classList.add('gone'); return; }
  const tg = S.mobile && FLY;
  if (tg) {
    o.st = 'fly';
    o.fly = { t0: now(), x0: o.rx || o.x, y0: o.ry || o.y, r0: o.r, dur: rand(560, 780), rot: rand(-35, 35), ...tg };
  } else {
    o.st = 'sink';
    o.sinkT = now();
  }
}
function enter(o) {
  o.el.classList.remove('gone');
  o.op = -1;
  if (RM()) { o.st = 'in'; o.r = o.rt; o.opC = o.opT; return; }
  o.opC = S.mobile ? 1 : 0;
  if (S.mobile) {
    o.st = 'drop';
    o.x = rand(LR.l + o.rt, Math.max(LR.l + o.rt, LR.r - o.rt));
    o.y = LR.t - rand(30, 260) - o.rt;
    o.vx = rand(-1, 1); o.vy = rand(1, 4);
    o.r = o.rt * .75;
    flownShown = Math.max(0, flownShown - 1);
    bus.emit('cloud', false);
  } else {
    o.st = 'in';
    o.r = Math.max(o.r * .35, 4);
  }
}

/* ---------- Fizika (fix 60 Hz-es lépés) ---------- */
let stepN = 0;
function anchor(o) {
  if (S.view === 'csoport' && o.grp) return [o.grp.x, o.grp.y, .024, .024];
  if (S.view === 'terkep') return [o.mx, o.my, .03, .03];      // lágyabb rugó: nyugodtabb térkép
  // ellipszis alakú vonzás: a felhő a színpad arányát veszi fel (kx = ky · (h/w)²)
  const m = o.b.m, asp = clamp(LR.h / LR.w, .3, 1.6), a2 = asp * asp;
  if (m == null) return [LR.cx, LR.cy, .0024 * a2, .0024];
  if (o.tier === 'back') {
    // a gyenge találatok glóriát alkotnak a felhő körül (ellipszis mentén)
    const dx = (o.x - LR.cx) / LR.w, dy = (o.y - LR.cy) / LR.h, d = Math.hypot(dx, dy) || 1;
    return [LR.cx + dx / d * LR.w * .43, LR.cy + dy / d * LR.h * .43, .004, .004];
  }
  const k = .0016 + .0075 * m;
  return [LR.cx, LR.cy, k * a2, k];
}
function step() {
  stepN++;
  const act = [];
  for (const o of B) if (o.st === 'in' || o.st === 'drop') act.push(o);
  const rm = RM();
  for (const o of act) {
    const target = o.rt * o.hk;
    o.rv += (target - o.r) * (rm ? .5 : .16);
    o.rv *= rm ? .2 : .7;
    o.r += o.rv;
    if (o.r < .5) o.r = .5;
    o.jv += -o.jy * .2; o.jv *= .78; o.jy += o.jv;
    const [ax, ay, kx, ky] = anchor(o);
    o.vx += (ax - o.x) * kx;
    o.vy += (ay - o.y) * ky;
    if (o.st === 'drop') o.vy += .85;
    if (mouse.in && !S.mobile && !rm) {
      const dx = o.x - mouse.x, dy = o.y - mouse.y, d = Math.hypot(dx, dy) || 1, R = o.r + 70;
      if (d < R) { const f = (R - d) / R * .9; o.vx += dx / d * f; o.vy += dy / d * f; }
    }
    // a megkavart buborékok egy ideig lazábban csillapodnak: tovább siklanak, mint a vízen
    const damp = o.st === 'drop' ? .99 : stepN - o.stirN < 40 ? .87 : .8;
    o.vx *= damp; o.vy *= damp;
    o.x += o.vx; o.y += o.vy;
  }
  if (stir.on && !rm) stirForce(act);
  const gap = S.mobile ? 4 : 6;
  for (let it = 0; it < 2; it++) {
    for (let i = 0; i < act.length; i++) {
      const a = act[i];
      for (let j = i + 1; j < act.length; j++) {
        const c = act[j];
        const min = a.r * 1.09 + c.r * 1.09 + gap;
        const dx = c.x - a.x, dy = c.y - a.y;
        if (dx > min || dx < -min || dy > min || dy < -min) continue;
        const d2 = dx * dx + dy * dy;
        if (d2 >= min * min) continue;
        const d = Math.sqrt(d2) || .01, ov = (min - d) / d;
        const wa = c.r * c.r / (a.r * a.r + c.r * c.r), wc = 1 - wa;
        a.x -= dx * ov * wa * .5; a.y -= dy * ov * wa * .5;
        c.x += dx * ov * wc * .5; c.y += dy * ov * wc * .5;
      }
    }
  }
  for (const o of act) {
    const R = o.r * 1.09;
    for (const q of OBS) {
      if (o.x + R < q.l || o.x - R > q.r || o.y + R < q.t || o.y - R > q.b) continue;
      const nx = clamp(o.x, q.l, q.r), ny = clamp(o.y, q.t, q.b);
      let dx = o.x - nx, dy = o.y - ny, d = Math.hypot(dx, dy);
      if (d === 0) { o.y = q.b + R; o.vy = Math.abs(o.vy); continue; }
      if (d < R) { o.x += dx / d * (R - d); o.y += dy / d * (R - d); }
    }
    const minX = LR.l + R, maxX = Math.max(minX, LR.r - R);
    if (o.x < minX) { o.x = minX; o.vx *= -.3; } else if (o.x > maxX) { o.x = maxX; o.vx *= -.3; }
    const maxY = Math.max(LR.t + R, LR.b - R);
    if (o.st === 'drop') {
      if (o.y > LR.t + R) o.st = 'in';
      if (o.y > maxY) { o.y = maxY; o.vy *= -.45; o.st = 'in'; }
    } else if (o.y < LR.t + R) { o.y = LR.t + R; o.vy *= -.3; }
    else if (o.y > maxY) { o.y = maxY; o.vy *= -.3; }
  }
  // Adaptív kitöltés: ha nyugalmi állapotban is sok az átfedés, kicsit kisebb buborékok
  // (animáció közben – hullám, kirepülés, növekedés – nem mérünk, mert az átfedés ott természetes)
  const settled = () => act.every(o => !o.pend && Math.abs(o.rv) < .05 && Math.abs(o.vx) + Math.abs(o.vy) < .6) && !B.some(o => o.st === 'fly' || o.st === 'drop');
  if (stepN % 45 === 0 && S.view !== 'terkep' && settled()) {
    let ov = 0, n = 0;
    for (let i = 0; i < act.length; i++) for (let j = i + 1; j < act.length; j++) {
      const a = act[i], c = act[j], d = Math.hypot(c.x - a.x, c.y - a.y), min = (a.r + c.r) * 1.09;
      if (d < min) { ov += min - d; n++; }
    }
    const before = fill;
    if (act.length && ov / act.length > 1.6) fill = Math.max(.62, fill * .97);
    else if (ov / Math.max(act.length, 1) < .5 && fill < 1) fill = Math.min(1, fill * 1.04);
    if (fill !== before) { computeTargets(); for (const o of B) if (!o.pend) o.rt = o.nrt; }
  }
}

/* ---------- Ujjal kavarás (érintőképernyő) ----------
   Ha az ujj a felhőn húzódik, a buborékok kitérnek előle és a mozgás irányába sodródnak – mint a vízbe
   húzott kéz nyomán. A koppintás és a hosszú nyomás változatlan: a kavarás néhány pixelnyi elmozdulás
   után indul. Az ujj útját szakaszként kezeljük, így gyors húzásnál sem ugrik át buborékokat. */
const stir = { id: null, on: false, x: 0, y: 0, px: 0, py: 0, sx: 0, sy: 0, trail: 0, block: 0 };
const RIPPLES = [];
function ripple(x, y) {
  if (RIPPLES.length >= 12) RIPPLES.shift();
  RIPPLES.push({ x, y, t0: now() });
}
function stirForce(act) {
  const ax = stir.px, ay = stir.py, bx = stir.x, by = stir.y;
  stir.px = bx; stir.py = by;
  const mx = bx - ax, my = by - ay, len2 = mx * mx + my * my;
  const sp = Math.min(Math.sqrt(len2), 40);          // ujjsebesség, px / lépés
  const reach = S.mobile ? 62 : 76;                   // hatótáv a buborék szélétől
  for (const o of act) {
    const u = len2 ? clamp(((o.x - ax) * mx + (o.y - ay) * my) / len2, 0, 1) : 1;
    let dx = o.x - (ax + mx * u), dy = o.y - (ay + my * u);
    const d = Math.hypot(dx, dy) || .01, R = o.r + reach;
    if (d >= R) continue;
    const f = 1 - d / R, f2 = f * f;
    dx /= d; dy /= d;
    const push = f2 * (1.5 + sp * .13);               // kitérés az ujj elől (gyorsabb húzásnál erősebb)
    o.vx += dx * push + mx * f2 * .24;                // + sodrás az ujj irányába
    o.vy += dy * push + my * f2 * .24;
    const v = Math.hypot(o.vx, o.vy);
    if (v > 24) { o.vx *= 24 / v; o.vy *= 24 / v; }
    o.stirN = stepN;
  }
  stir.trail += sp;
  if (stir.trail > 38) { stir.trail = 0; ripple(bx, by); }
}

/* ---------- Rajzolás ---------- */
function render(t) {
  const rm = RM();
  if (!S.mobile && !rm) { mouse.px += (mouse.tx - mouse.px) * .06; mouse.py += (mouse.ty - mouse.py) * .06; }
  for (const o of B) {
    if (o.st === 'gone') continue;
    fitBase(o);
    const R0 = o.base;
    let x = o.x, y = o.y + o.jy, s = o.r / R0, rot = 0, op = 1;
    // simított mélységi átlátszóság (keresésnél a nem találatok erősen halványak)
    o.opC += ((o.dim ? .14 : o.opT) - o.opC) * (rm ? 1 : .12);
    if (o.st === 'fly') {
      const f = o.fly, p = (t - f.t0) / f.dur;
      if (p >= 1) {
        o.st = 'gone'; o.el.classList.add('gone'); o.el.style.opacity = ''; o.op = 1;
        flownShown++; bus.emit('cloud', true);
        spark(SR.left + f.tx, SR.top + f.ty, 4, { speed: 2.2, size: 3 });
        continue;
      }
      const a = .16;
      if (p < a) { const u = p / a; s = f.r0 / R0 * (1 - .12 * Math.sin(u * Math.PI / 2)); x = f.x0; y = f.y0 + Math.sin(u * Math.PI) * 3; }
      else {
        const u = (p - a) / (1 - a), e = u * u * (1.7 - .7 * u);
        const cx = f.x0 + (f.tx - f.x0) * .15, cy = Math.min(f.y0, f.ty) - 120;
        x = (1 - e) * (1 - e) * f.x0 + 2 * (1 - e) * e * cx + e * e * f.tx;
        y = (1 - e) * (1 - e) * f.y0 + 2 * (1 - e) * e * cy + e * e * f.ty;
        s = f.r0 / R0 * (.88 - .62 * e);
        rot = f.rot * e;
        op = u > .7 ? 1 - (u - .7) / .3 : 1;
        // szikranyom – korlátozott részecskeszámmal, hogy sok kirepülőnél se lassuljon
        if (FX.length < 260 && Math.random() < .4) spark(SR.left + x + rand(-4, 4), SR.top + y + f.r0 * .6, 1, { trail: true });
      }
    } else if (o.st === 'sink') {
      const p = clamp((t - o.sinkT) / 480, 0, 1);
      s *= 1 - .6 * p; y += 22 * p; op = 1 - p;
      if (p >= 1) { o.st = 'gone'; o.el.classList.add('gone'); o.el.style.opacity = ''; o.op = 1; continue; }
    } else if (!rm) {
      x += Math.sin(t * .0008 + o.ph) * 2.2;
      y += Math.cos(t * .00093 + o.ph * 1.7) * 2.2;
      if (!S.mobile) { const d = DEPTH[o.tier] || 0; x += mouse.px * d * 12; y += mouse.py * d * 10; }
    }
    op *= o.opC;
    o.el.style.transform = `translate3d(${(x - R0).toFixed(1)}px,${(y - R0).toFixed(1)}px,0) scale(${Math.max(s, .002).toFixed(4)})${rot ? ` rotate(${rot.toFixed(1)}deg)` : ''}`;
    if (Math.abs(op - o.op) > .004) { o.el.style.opacity = op > .995 ? '' : op.toFixed(3); o.op = op; }
    o.rx = x; o.ry = y; o.rr = s * R0;
  }
  if (hovered) placeTip(hovered);
  drawUnder(t);
}

/* Lista nézetbe váltáskor a vászon azonnal üres legyen: a felhő ott megáll, és a félig
   átlátszó („kiesett”) listakártyák mögött különben átlátszana az utolsó képkocka. */
function clearUnder() {
  ux.setTransform(1, 0, 0, 1, 0, 0);
  ux.clearRect(0, 0, underC.width, underC.height);
  for (const o of B) { o.ringV = 0; o.glowV = 0; }
  PULSES.length = 0;
  RIPPLES.length = 0;
  underDirty = false;
}

/* ---------- Alsó vászon: illeszkedési gyűrű, glória, pulzus ----------
   Mind a 124 buborék díszítése egyetlen vásznon rajzolódik; a buborékrétegeket így sosem kell
   újrarajzolni, csak mozgatni (transform) és halványítani (opacity). */
function drawUnder(t) {
  const active = S.crit.length > 0 && S.view !== 'lista';
  const rm = RM();
  let work = PULSES.length > 0;
  if (!work) for (const o of B) if (o.ringV > .004 || o.glowV > .01 || (active && o.ringT > 0 && o.st !== 'gone')) { work = true; break; }
  if (!work && !underDirty) return;
  ux.setTransform(underDpr, 0, 0, underDpr, 0, 0);
  ux.clearRect(0, 0, SR.width, SR.height);
  underDirty = work;
  const [cr, cg, cb] = ringRGB;
  const col = a => `rgba(${cr},${cg},${cb},${a})`;
  ux.lineCap = 'round';
  for (const o of B) {
    const live = o.st === 'in' || o.st === 'drop' || o.st === 'sink';
    o.ringV += ((active && live ? o.ringT : 0) - o.ringV) * (rm ? 1 : .07);
    o.glowV += ((active && live && o.tier === 'top' ? 1 : 0) - o.glowV) * (rm ? 1 : .06);
    if (!live || o.rr < 2) continue;
    const a = o.op;
    if (o.glowV > .01 && a > .05) {
      const br = rm ? 0 : (1 - Math.cos(t * .0021 + o.ph)) / 2;       // 3 mp-es „lélegzés”
      // a glória kilógása kis buborékoknál arányos, nagyoknál legfeljebb ~22 px (ne folyjanak össze)
      const R = o.rr + Math.min(o.rr * .435, 22) * (1 + .3 * br);
      const g = ux.createRadialGradient(o.rx, o.ry, o.rr * .6, o.rx, o.ry, R);
      g.addColorStop(0, col(.42 * o.glowV * a * (1 - .35 * br)));
      g.addColorStop(1, col(0));
      ux.fillStyle = g;
      ux.beginPath(); ux.arc(o.rx, o.ry, R, 0, 6.2832); ux.fill();
    }
    if (o.ringV > .004 && a > .05) {
      ux.globalAlpha = a;
      ux.strokeStyle = col(1);
      const lw = Math.min(o.rr * .1, 6);                              // nagy buborékon se legyen vaskos
      ux.lineWidth = lw;
      ux.beginPath();
      ux.arc(o.rx, o.ry, o.rr * 1.1 + lw / 2 + 1, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.min(o.ringV, 1));
      ux.stroke();
      ux.globalAlpha = 1;
    }
  }
  // pulzusgyűrű: 2 × 1,25 mp, tágul és elhalványul
  for (let i = PULSES.length - 1; i >= 0; i--) {
    const p = PULSES[i], o = p.o, el = t - p.t0;
    if (el > 2500 || o.st === 'gone') { PULSES.splice(i, 1); continue; }
    const u = (el % 1250) / 1250, e = 1 - Math.pow(1 - u, 3), sc = 1 + .75 * e;
    ux.strokeStyle = col(.9 * (1 - e) * o.op);
    ux.lineWidth = o.rr * .075 * sc;
    ux.beginPath(); ux.arc(o.rx, o.ry, o.rr * 1.04 * sc, 0, 6.2832); ux.stroke();
  }
}

/* ---------- Tooltip (név + egyezés) ---------- */
function setHover(o) {
  clearTimeout(hoverTimer);
  if (hovered === o) return;
  if (hovered) hovered.hk = 1;
  hovered = o;
  if (!o) { tipEl.classList.remove('on'); return; }
  o.hk = S.mobile ? 1 : 1.18;
  const b = o.b, k = filterCount();
  let badge = '';
  if (S.crit.length) {
    badge = k && !S.quiz
      ? `<span class="m ${b.np === k ? '' : 'part'}">${b.np}/${k}</span>`
      : `<span class="m ${b.ok ? '' : 'part'}">${Math.round(b.m * 100)}%</span>`;
  }
  tipEl.innerHTML = `<span class="tip-in">${b.hu ? ic('flag', 'ic hu') : ''}${esc(b.nev)}${badge}</span>`;
  placeTip(o);
  requestAnimationFrame(() => tipEl.classList.add('on'));
}
function placeTip(o) {
  // transformmal pozicionálunk (nem left/top), így képkockánként nincs elrendezés-számolás
  const R = o.r * 1.1;
  let y = o.ry + R + 10;
  if (y + 44 > SR.height) y = o.ry - R - 52;
  tipEl.style.transform = `translate3d(${clamp(o.rx, 90, SR.width - 90).toFixed(1)}px,${y.toFixed(1)}px,0)`;
}

/* ---------- Részecskék (vászon) ---------- */
const fxc = $('#fx'), fxx = fxc.getContext('2d');
let FX = [], fxDpr = 1;
function fxResize() {
  // a részecskék apró pöttyök: 1× felbontás bőven elég, és negyedannyi pixelt kell törölni képkockánként
  fxDpr = 1;
  fxc.width = innerWidth * fxDpr; fxc.height = innerHeight * fxDpr;
  fxx.setTransform(fxDpr, 0, 0, fxDpr, 0, 0);
}
function spark(x, y, n, o = {}) {
  if (RM()) return;
  n = Math.min(n, 420 - FX.length);
  for (let i = 0; i < n; i++) {
    const a = o.trail ? rand(Math.PI * .3, Math.PI * .7) : rand(0, Math.PI * 2);
    const sp = o.trail ? rand(.3, 1.2) : rand(1, o.speed || 4);
    FX.push({
      x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - (o.up || 0), g: o.g ?? (o.trail ? .02 : .12),
      life: 0, max: o.trail ? rand(26, 44) : rand(34, 60), size: o.size ? rand(o.size * .6, o.size) : rand(2, 4.5),
      c: o.color || FX_COLORS[Math.floor(Math.random() * FX_COLORS.length)], heart: !!o.heart,
    });
  }
}
function drawHeart(x, y, s) {
  fxx.beginPath();
  fxx.moveTo(x, y + s * .35);
  fxx.bezierCurveTo(x - s, y - s * .45, x - s * .45, y - s * 1.1, x, y - s * .45);
  fxx.bezierCurveTo(x + s * .45, y - s * 1.1, x + s, y - s * .45, x, y + s * .35);
  fxx.fill();
}
function fxStep() {
  if (!FX.length && !RIPPLES.length) { if (fxc.dataset.dirty) { fxx.clearRect(0, 0, innerWidth, innerHeight); delete fxc.dataset.dirty; } return; }
  fxc.dataset.dirty = 1;
  fxx.clearRect(0, 0, innerWidth, innerHeight);
  // kavarás hullámai: az ujj nyomán táguló, halványuló körök – a buborékok fölött, hogy a sűrű felhőben is látsszanak
  const tn = now(), [cr, cg, cb] = ringRGB;
  for (let i = RIPPLES.length - 1; i >= 0; i--) {
    const q = RIPPLES[i], u = (tn - q.t0) / 900;
    if (u >= 1) { RIPPLES.splice(i, 1); continue; }
    const e = 1 - Math.pow(1 - Math.max(u, 0), 3);
    fxx.strokeStyle = `rgba(${cr},${cg},${cb},${(.62 * (1 - u)).toFixed(3)})`;
    fxx.lineWidth = 3.6 * (1 - u) + 1;
    fxx.beginPath(); fxx.arc(SR.left + q.x, SR.top + q.y, 12 + 70 * e, 0, 6.2832); fxx.stroke();
  }
  FX = FX.filter(p => {
    p.life++;
    p.vy += p.g; p.vx *= .985; p.x += p.vx; p.y += p.vy;
    const a = 1 - p.life / p.max;
    if (a <= 0) return false;
    fxx.globalAlpha = a;
    fxx.fillStyle = p.c;
    if (p.heart) drawHeart(p.x, p.y, p.size * 2.2);
    else { fxx.beginPath(); fxx.arc(p.x, p.y, p.size * (.5 + a * .5), 0, 6.283); fxx.fill(); }
    return true;
  });
  fxx.globalAlpha = 1;
}

/* ---------- Kereső-reflektor ---------- */
function applySearch(q) {
  S.q = q;
  const nq = norm(q.trim());
  const hits = [];
  for (const o of B) {
    const b = o.b;
    const hit = !!nq && (norm(b.nev).includes(nq) || norm(b.en).includes(nq) || (b.syn || []).some(s => norm(s).includes(nq)));
    if (o.dim !== (!!nq && !hit)) { o.dim = !!nq && !hit; o.el.classList.toggle('dim', o.dim); }
    if (o.el.classList.contains('spot') !== hit) o.el.classList.toggle('spot', hit);
    if (hit && o.vis) hits.push(o);
  }
  if (hits.length === 1 && !RM()) { hits[0].jv = -6; }
  return hits;
}

/* ---------- Meglepetés ---------- */
function surprise() {
  const pool = B.filter(o => o.vis && o.st === 'in' && (o.b.m == null || o.b.m >= .6));
  if (!pool.length) return;
  const pick = pool[Math.floor(Math.random() * pool.length)];
  if (!RM()) for (const o of B) if (o.st === 'in') { o.vx += rand(-10, 10); o.vy += rand(-10, 10); }
  haptic(20);
  setTimeout(() => { pulse(pick); pick.jv = -9; }, 380);
  setTimeout(() => openCard(pick.b.id), 950);
}

/* ---------- Intró: spirálban „kipattanó” felhő ---------- */
function intro() {
  measure();
  const ga = Math.PI * (3 - Math.sqrt(5));
  const order = [...B].sort((a, c) => (c.b.nep - a.b.nep) || a.b.n - c.b.n);
  order.forEach((o, i) => {
    o.introIdx = i;
    const rr = Math.sqrt(i) * 5;
    o.x = LR.cx + Math.cos(i * ga) * rr * (LR.w / LR.h > 1 ? 1.4 : 1);
    o.y = LR.cy + Math.sin(i * ga) * rr;
    o.r = .5; o.rt = 0;
  });
  refresh(null, { intro: true });
  if (!RM()) setTimeout(() => spark(SR.left + LR.cx, SR.top + LR.cy, 36, { speed: 7, g: .08 }), 250);
}

/* ---------- Fő ciklus ---------- */
let lastT = now(), acc = 0;
let paused = false;
const bgEl = $('.bg');
function frame(t) {
  requestAnimationFrame(frame);
  const dt = Math.min(t - lastT, 100);
  lastT = t;
  // Ha a fajtakártya (vagy mobilon egy takaró lap) nyitva van, a felhő megáll: nem fut a fizika,
  // nem mozognak a rétegek, így a háttér-elmosásnak sem kell képkockánként újraszámolnia.
  const p = !cardEl.hidden || (S.mobile && !scrimEl.hidden) || S.view === 'lista';
  if (p !== paused) { paused = p; bgEl.classList.toggle('paused', p); }   // csak a háttér: ne az egész dokumentum stílusa számolódjon újra
  if (!paused) {
    acc += dt;
    for (const o of B) if (o.pend && t >= o.pend.at) commit(o, o.pend);
    // legfeljebb 3 lépés képkockánként: lassú gépen inkább lassul a mozgás, mint hogy
    // a felgyűlt lépések miatt még lassabb legyen a következő képkocka
    let n = 0;
    while (acc >= 16.67 && n < 3) { step(); acc -= 16.67; n++; }
    if (n === 3) acc = 0;
    render(t);
  } else {
    for (const o of B) if (o.pend && t >= o.pend.at) commit(o, o.pend);
  }
  fxStep();
}

/* ---------- Mutató, billentyűzet ---------- */
bubblesEl.addEventListener('pointerover', e => {
  if (e.pointerType !== 'mouse') return;
  const o = BY_EL.get(e.target.closest('.b'));
  if (!o) return;
  clearTimeout(hoverTimer);
  hoverTimer = setTimeout(() => setHover(o), 55);
});
bubblesEl.addEventListener('pointerout', e => {
  const from = e.target.closest('.b');
  if (from && !from.contains(e.relatedTarget)) { clearTimeout(hoverTimer); if (hovered && hovered.el === from) setHover(null); }
});
let lpTimer = 0, lpFired = false, pressed = null;
// érintésre a buborék kicsit „benyomódik”, elengedéskor visszarugózik
const unpress = () => { if (pressed) { pressed.hk = 1; pressed = null; } };
bubblesEl.addEventListener('pointerdown', e => {
  const o = BY_EL.get(e.target.closest('.b'));
  lpFired = false;
  if (!o || e.pointerType === 'mouse') return;
  if (!RM()) { pressed = o; o.hk = .9; }
  lpTimer = setTimeout(() => { lpFired = true; haptic([10, 30, 10]); toggleFav(o.b.id, o.el); }, 520);
});
['pointerup', 'pointercancel', 'pointerleave'].forEach(ev => bubblesEl.addEventListener(ev, () => { clearTimeout(lpTimer); unpress(); }));
bubblesEl.addEventListener('click', e => {
  const o = BY_EL.get(e.target.closest('.b'));
  if (now() < stir.block) return;               // kavarás után felengedett ujj ne nyisson kártyát
  if (!o || lpFired) { lpFired = false; return; }
  if (focusedO && focusedO !== o) focusedO.el.tabIndex = -1;
  focusedO = o; o.el.tabIndex = 0;
  openCard(o.b.id);
});
bubblesEl.addEventListener('keydown', e => {
  const o = BY_EL.get(e.target.closest('.b'));
  if (!o) return;
  const dirs = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
  if (dirs[e.key]) {
    e.preventDefault();
    const [dx, dy] = dirs[e.key];
    let best = null, bs = 1e9;
    for (const q of B) {
      if (q === o || !q.vis || q.st === 'gone') continue;
      const vx = q.x - o.x, vy = q.y - o.y, along = vx * dx + vy * dy;
      if (along <= 0) continue;
      const sc = along + Math.abs(vx * dy - vy * dx) * 2.2;
      if (sc < bs) { bs = sc; best = q; }
    }
    if (best) focusBubble(best);
  } else if (e.key === 'f' || e.key === 'F') toggleFav(o.b.id, o.el);
  else if (e.key === 'c' || e.key === 'C') toggleCmp(o.b.id, o.el);
});
bubblesEl.addEventListener('focusin', e => { const o = BY_EL.get(e.target.closest('.b')); if (o) setHover(o); });
bubblesEl.addEventListener('focusout', () => { if (hovered && document.activeElement !== hovered.el) setHover(null); });
function focusBubble(o) {
  if (focusedO) focusedO.el.tabIndex = -1;
  focusedO = o;
  o.el.tabIndex = 0;
  o.el.focus({ preventScroll: true });
}
function initRoving() {
  const vis = B.filter(o => o.vis);
  if (!vis.length) return;
  const c = vis.reduce((a, o) => Math.hypot(o.x - LR.cx, o.y - LR.cy) < Math.hypot(a.x - LR.cx, a.y - LR.cy) ? o : a);
  if (focusedO) focusedO.el.tabIndex = -1;
  focusedO = c; c.el.tabIndex = 0;
}
stage.addEventListener('pointermove', e => {
  if (e.pointerType !== 'mouse') return;
  mouse.x = e.clientX - SR.left; mouse.y = e.clientY - SR.top; mouse.in = true;
  mouse.tx = clamp((mouse.x - SR.width / 2) / (SR.width / 2), -1, 1);
  mouse.ty = clamp((mouse.y - SR.height / 2) / (SR.height / 2), -1, 1);
});
stage.addEventListener('pointerleave', () => { mouse.in = false; mouse.tx = mouse.ty = 0; });

/* Kavarás: ujj vagy toll a felhőn (a HUD-gombokon, a listán és a felhőjelvényen nem) – lásd stirForce */
stage.addEventListener('pointerdown', e => {
  if (e.pointerType === 'mouse' || stir.id !== null || paused || RM() || S.view === 'lista') return;
  if (e.target !== stage && !e.target.closest('.b, .bubbles')) return;
  const x = e.clientX - SR.left, y = e.clientY - SR.top;
  Object.assign(stir, { id: e.pointerId, on: false, x, y, px: x, py: y, sx: x, sy: y, trail: 0 });
});
stage.addEventListener('pointermove', e => {
  if (e.pointerId !== stir.id) return;
  stir.x = e.clientX - SR.left; stir.y = e.clientY - SR.top;
  if (!stir.on && Math.hypot(stir.x - stir.sx, stir.y - stir.sy) > 9) {
    stir.on = true;
    clearTimeout(lpTimer);                        // kavarás közben nincs hosszú nyomásos kedvencelés
    unpress();
    if (hovered) setHover(null);                  // pl. kártyazárás után a fókusz miatt kint maradt név
    ripple(stir.sx, stir.sy);
  }
});
const endStir = e => {
  if (e.pointerId !== stir.id) return;
  if (stir.on) stir.block = now() + 400;
  stir.id = null; stir.on = false;
};
stage.addEventListener('pointerup', endStir);
stage.addEventListener('pointercancel', endStir);
