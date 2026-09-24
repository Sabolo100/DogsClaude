/* ==========================================================================
   Alapok: segédfüggvények, adatok, állapot, tárolás, URL-állapot
   ========================================================================== */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const now = () => performance.now();
const rand = (a = 0, b = 1) => a + Math.random() * (b - a);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const ic = (id, cls = 'ic') => `<svg class="${cls}" aria-hidden="true"><use href="#i-${id}"/></svg>`;
const num = n => String(n).replace('.', ',');
const range = a => a[0] === a[1] ? num(a[0]) : `${num(a[0])}–${num(a[1])}`;
const haptic = ms => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) { /* nem támogatott */ } };

const DATA = JSON.parse($('#pacsi-data').textContent);
const BREEDS = DATA.breeds;
const SPARES = Object.fromEntries(DATA.spares.map(s => [s.id, s]));
const BY_ID = new Map(BREEDS.map(b => [b.id, b]));
const IMG = window.PACSI_IMG || {};
const ARTIFACT = !!window.PACSI_ARTIFACT;   // claude.ai artifact-néző: nincs hash-állapot, letöltés, Web Share
const COLL = new Intl.Collator('hu');

/* A beágyazott (base64) képeket rövid blob:-hivatkozássá alakítjuk. Egy 1,6 MB-os data URI
   egy CSS-változóban minden buborék minden stílus-újraszámolásakor újra feldolgozódna –
   ez okozta a több másodperces akadásokat az egyfájlos verzióban. */
function toBlobURL(uri) {
  if (!uri || !uri.startsWith('data:')) return uri;
  try {
    const comma = uri.indexOf(',');
    const mime = uri.slice(5, comma).split(';')[0];
    const bin = atob(uri.slice(comma + 1));
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return URL.createObjectURL(new Blob([bytes], { type: mime }));
  } catch (e) { return uri; }
}
const SPRITE = toBlobURL(window.PACSI_SPRITE) || 'img/sprite-thumbs.webp';
window.PACSI_SPRITE = null;
const SP_ROWS = DATA.spriteRows || 8;
document.documentElement.style.setProperty('--sprite', `url("${SPRITE}")`);
document.documentElement.style.setProperty('--sp-size', `800% ${SP_ROWS * 100}%`);

const PORTRAIT_URL = {};
const portrait = id => IMG[id] ? (PORTRAIT_URL[id] || (PORTRAIT_URL[id] = toBlobURL(IMG[id]))) : `img/portrek/${id}.webp`;
const spritePos = b => `${(b.sprite % 8) / 7 * 100}% ${Math.floor(b.sprite / 8) / (SP_ROWS - 1) * 100}%`;
const picStyle = b => `--bgc:${b.bg};--pos:${spritePos(b)}`;

const mqRM = matchMedia('(prefers-reduced-motion: reduce)');
const mqMobile = matchMedia('(max-width: 899px)');
const mqDark = matchMedia('(prefers-color-scheme: dark)');

const store = {
  get(k, d) { try { const v = localStorage.getItem('pacsi:' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('pacsi:' + k, JSON.stringify(v)); } catch (e) { /* privát mód */ } },
};

/* Központi állapot */
const S = {
  f: { meret: new Set(), szor: new Set(), szerep: new Set(), fci: new Set(), energia: null, t: new Set() },
  quiz: null,                 // { answers:[], crit:[] }
  mode: null,                 // 'rank' | 'strict' | null (= alapértelmezés: Csak találatok)
  view: 'felho', groupBy: 'meret', q: '',
  fav: new Set(store.get('fav', [])),
  cmp: store.get('cmp', []).filter(id => BY_ID.has(id)),
  card: null, drawer: null,
  theme: store.get('theme', 'auto'),
  rmUser: store.get('rm', false),
  mobile: mqMobile.matches,
  crit: [],
};
S.fav.forEach(id => { if (!BY_ID.has(id)) S.fav.delete(id); });
// alapértelmezés mindkét platformon: Csak találatok (a Rangsor egy kattintással bekapcsolható)
const modeOf = () => S.mode || 'strict';
const RM = () => mqRM.matches || S.rmUser;

/* Egyszerű eseménybusz */
const bus = {
  h: {},
  on(e, f) { (this.h[e] = this.h[e] || []).push(f); },
  emit(e, a) { (this.h[e] || []).forEach(f => f(a)); },
};

/* ---------- URL-állapot (hash) – szerver nélkül is megosztható ---------- */
function encodeHash() {
  const f = S.f, parts = [];
  for (const k of ['meret', 'szor', 'szerep', 'fci']) if (f[k].size) parts.push(`${k}:${[...f[k]].join('.')}`);
  if (f.energia) parts.push(`energia:${f.energia}`);
  f.t.forEach(t => parts.push(t));
  const p = new URLSearchParams();
  if (parts.length) p.set('f', parts.join(';'));
  if (S.quiz && S.quiz.done) p.set('k', S.quiz.answers.join('.'));
  if (S.mode) p.set('m', S.mode === 'strict' ? 's' : 'r');
  if (S.view !== 'felho') p.set('v', S.view === 'csoport' ? `csoport.${S.groupBy}` : S.view);
  if (S.card) p.set('b', S.card);
  const s = p.toString().replace(/%3A/g, ':').replace(/%3B/g, ';');
  return s ? '#' + s : '';
}
function decodeHash() {
  const h = location.hash.slice(1);
  if (!h) return {};
  const p = new URLSearchParams(h);
  const out = {};
  if (p.get('f')) {
    for (const part of p.get('f').split(';')) {
      const [k, v] = part.split(':');
      if (v != null) {
        if (k === 'energia') S.f.energia = v;
        else if (S.f[k] instanceof Set) v.split('.').forEach(x => S.f[k].add(k === 'fci' ? +x : x));
      } else if (TBY[k]) S.f.t.add(k);
    }
  }
  if (p.get('k')) out.quiz = p.get('k').split('.').map(Number);
  if (p.get('m')) S.mode = p.get('m') === 's' ? 'strict' : 'rank';
  if (p.get('v')) {
    const [v, g] = p.get('v').split('.');
    if (['felho', 'csoport', 'terkep', 'lista'].includes(v)) S.view = v;
    if (g) S.groupBy = g;
  }
  if (p.get('b') && BY_ID.has(p.get('b'))) out.card = p.get('b');
  if (p.has('kviz')) out.kviz = true;   // PWA-gyorsparancs: „Párkereső kvíz”
  return out;
}
let hashTimer = 0;
function syncHash(push = false) {
  if (ARTIFACT) return;
  clearTimeout(hashTimer);
  const go = () => {
    const h = encodeHash();
    const url = location.pathname + location.search + h;
    if (url === location.pathname + location.search + location.hash) return;
    try { (push ? history.pushState : history.replaceState).call(history, null, '', url || location.pathname); } catch (e) { /* file:// korlát */ }
  };
  push ? go() : (hashTimer = setTimeout(go, 250));
}
