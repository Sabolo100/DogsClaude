/* ==========================================================================
   Nyelvek: szótár (t), fajtaszövegek, nyelvváltó (zászló), élő nyelvváltás
   --------------------------------------------------------------------------
   A szövegek a data/i18n/<nyelv>/ fájlokból jönnek (a build egy csomagba, #pacsi-i18n, ágyazza be őket).
   t('kulcs', { n: 3 })  – szöveg az aktuális nyelven; hiányzó kulcs/fordítás esetén a magyar
   tn('kulcs', n)        – többes szám (kulcs.one / kulcs.other, a nyelv PluralRules-ja szerint)
   tH('kulcs')           – mindig magyar: a statisztika nyelvfüggetlen, egységes értékeket kap
   labels(fn)            – nyelvfüggő táblázatok (címkék): induláskor és minden nyelvváltáskor lefut
   Új nyelv: lásd tools/i18n.py (fejléc) – a kódban nincs teendő.
   ========================================================================== */
const I18N = JSON.parse($('#pacsi-i18n').textContent);
const LANGS = I18N.langs;
const LANG_BY = Object.fromEntries(LANGS.map(l => [l.code, l]));
const DEF_LANG = 'hu';

/* Melyik nyelven indulunk: ?lang=xx (és megjegyezzük) › korábbi választás › magyar. A böngésző nyelvét szándékosan nem
   figyeljük: a magyar a főnyelv, a váltó (zászló) a főoldalon és a nyitó ablakban is ott van. */
function pickLang() {
  const q = new URLSearchParams(location.search).get('lang');
  if (q && LANG_BY[q]) { store.set('lang', q); return q; }
  const s = store.get('lang', null);
  return LANG_BY[s] ? s : DEF_LANG;
}
let LANG = pickLang();

const dict = l => I18N.ui[l] || {};
const PR = {};
const plural = l => PR[l] || (PR[l] = new Intl.PluralRules(LANG_BY[l] ? LANG_BY[l].locale : l));
function t(key, p, lang = LANG) {
  let s = dict(lang)[key];
  if (s == null) s = dict(DEF_LANG)[key];
  if (s == null) { console.warn('[i18n] hiányzó kulcs:', key); return key; }
  return p ? s.replace(/\{(\w+)\}/g, (m, k) => (k in p ? p[k] : m)) : s;
}
function tn(key, n, p, lang = LANG) {
  const d = dict(lang), cat = plural(lang).select(n);
  const k = [`${key}.${cat}`, `${key}.other`, key].find(x => d[x] != null);
  if (k) return t(k, { n, ...p }, lang);
  return lang === DEF_LANG ? t(key, { n, ...p }) : tn(key, n, p, DEF_LANG);
}
const tH = (key, p) => t(key, p, DEF_LANG);
const LABEL_FNS = [];
function labels(fn) { LABEL_FNS.push(fn); fn(); }
const flag = id => `<svg class="flag" aria-hidden="true"><use href="#${id}"/></svg>`;
// az aktuális nyelvű oldal címe a megosztásokhoz (a magyar a főcím, a többi ?lang=… paraméterrel)
const siteUrl = () => `${SITE.url}/${LANG === DEF_LANG ? '' : `?lang=${LANG}`}`;

/* ---------- Fajtaszövegek ----------
   A fajtaadat (DATA) magyar; a többi nyelv csak a szövegmezőket írja felül (hiányzó mezőnél marad a magyar).
   b.i0 = a magyar eredeti; b.nev0 / b.orszag0 = a magyar név és származás (statisztika, földrajzi csoportosítás). */
const BREED_TEXT = ['nev', 'orszag', 'tagline', 'leiras', 'mozgas', 'erdekesseg', 'kinekIgen', 'kinekNem', 'egeszseg'];
for (const b of BREEDS) {
  b.i0 = Object.fromEntries(BREED_TEXT.filter(f => b[f] != null).map(f => [f, b[f]]));
  b.nev0 = b.nev; b.orszag0 = b.orszag;
  // keresőnevek: bármelyik nyelven be lehet gépelni (a magyar felületen is megtalálható a „german shepherd”)
  const ovs = Object.values(I18N.breeds).map(o => o[b.id] || {});
  b.names = [b.nev, b.en, ...ovs.map(o => o.nev).filter(Boolean)];
  b.syn = [...(b.syn || []), ...ovs.flatMap(o => o.alias || [])];
}
function applyBreedText() {
  const ov = I18N.breeds[LANG] || {};
  for (const b of BREEDS) {
    const o = ov[b.id] || {};
    for (const f in b.i0) b[f] = o[f] != null ? o[f] : b.i0[f];
  }
}

/* ---------- Statikus (HTML-ben lévő) szövegek ----------
   data-i18n="kulcs" → szöveg · data-i18n-html="kulcs" → HTML · data-i18n-attr="attribútum:kulcs;…" → attribútumok */
function applyStatic(root = document) {
  for (const el of $$('[data-i18n]', root)) el.textContent = t(el.dataset.i18n);
  for (const el of $$('[data-i18n-html]', root)) el.innerHTML = t(el.dataset.i18nHtml);
  for (const el of $$('[data-i18n-attr]', root)) {
    for (const pair of el.dataset.i18nAttr.split(';')) {
      const [a, k] = pair.split(':');
      el.setAttribute(a.trim(), t(k.trim()));
    }
  }
}
function applyLangBase() {
  const l = LANG_BY[LANG];
  document.documentElement.lang = l.locale;
  COLL = new Intl.Collator(l.locale);
  applyBreedText();
  LABEL_FNS.forEach(f => f());
  applyStatic();
  document.title = t('meta.title');
  const set = (sel, v) => { const m = $(sel); if (m) m.setAttribute('content', v); };
  set('meta[name="description"]', t('meta.desc'));
  set('meta[property="og:title"]', t('meta.ogTitle'));
  set('meta[property="og:description"]', t('meta.ogDesc'));
}

/* ---------- Nyelvváltó: zászló gomb a főoldalon + lenyíló menü; a nyitó ablakban és a Tippekben kis zászló-gombok ---------- */
const langPills = () => `<span class="lang-pills" role="group" aria-label="${esc(t('lang.label'))}">${LANGS.map(l =>
  `<button class="lang-pill" data-lang="${l.code}" aria-pressed="${l.code === LANG}">${flag(l.flag)}<span>${esc(l.name)}</span></button>`).join('')}</span>`;
function renderLangUI() {
  const cur = LANG_BY[LANG], btn = $('#langBtn');
  btn.innerHTML = flag(cur.flag);
  btn.setAttribute('aria-label', `${t('lang.label')}: ${cur.name}`);
  btn.title = t('lang.label');
  $('#langMenu').innerHTML = LANGS.map(l =>
    `<button role="menuitemradio" aria-checked="${l.code === LANG}" data-lang="${l.code}">${flag(l.flag)}<span>${esc(l.name)}</span><i class="lm-ck">${ic('check')}</i></button>`).join('');
  $$('.lang-pill').forEach(p => p.setAttribute('aria-pressed', p.dataset.lang === LANG));
}
function openLangMenu(open = $('#langMenu').hidden) {
  const m = $('#langMenu'), b = $('#langBtn');
  m.hidden = !open;
  b.setAttribute('aria-expanded', open);
  if (!open) return;
  const q = b.getBoundingClientRect();
  m.style.top = q.bottom + 8 + 'px';
  m.style.right = Math.max(8, innerWidth - q.right - 4) + 'px';
  const cur = $('[aria-checked="true"]', m);
  cur && cur.focus({ preventScroll: true });
}
$('#langBtn').addEventListener('click', () => openLangMenu());
addEventListener('pointerdown', e => { if (!$('#langMenu').hidden && !e.target.closest('#langMenu, #langBtn')) openLangMenu(false); });
$('#langMenu').addEventListener('keydown', e => {
  const items = $$('button', $('#langMenu')), i = items.indexOf(document.activeElement);
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); items[(i + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length].focus(); }
  else if (e.key === 'Escape') { e.stopPropagation(); openLangMenu(false); $('#langBtn').focus(); }
  else if (e.key === 'Tab') openLangMenu(false);
});
document.addEventListener('click', e => {
  const b = e.target.closest('[data-lang]');
  if (!b) return;
  const wasMenu = !!b.closest('#langMenu');
  setLang(b.dataset.lang);
  if (wasMenu) { openLangMenu(false); $('#langBtn').focus({ preventScroll: true }); }
});

/* Nyelvváltás menet közben (újratöltés nélkül): táblák, fajtaszövegek, statikus szövegek, majd a látható részek újrarajzolása */
function setLang(l) {
  if (!LANG_BY[l] || l === LANG) return;
  LANG = l;
  store.set('lang', l);
  stat('nyelv', { nyelv: l });
  applyLangBase();
  relang();
}
function relang() {
  setHover(null);
  B.forEach(o => o.el.setAttribute('aria-label', o.b.nev));
  if (S.quiz) S.quiz.crit = quizCrit(S.quiz.answers);       // a kvíz-szempontok címkéi az új nyelven
  closePanelSheet();
  const fci = $('#fciChips'), fciOpen = fci && !fci.hidden;
  renderFilters();
  if (fciOpen) { $('#fciChips').hidden = false; $('#fciMore').textContent = t('filters.hide'); $('#fciMore').setAttribute('aria-expanded', true); }
  renderDock(); renderGroupSeg(); renderMobViews();
  renderLangUI();
  refresh(null, { instant: true });                          // kiértékelés → szám-, szűrő- és lista-feliratok, csoportcímkék, térkép
  if (S.card) { cardEl.innerHTML = cardHTML(BY_ID.get(S.card)); animateCardIn(); }
  if (S.drawer) { drawerEl.setAttribute('aria-label', drawerTitle(S.drawer)); renderDrawer(); }
  if (WL.open) renderWelcomeText();
  if (CO && !coachEl.hidden) showCoach(CO.i);
  const mi = $('#mobSearch input');
  if (mi) { mi.placeholder = t('search.ph'); mi.setAttribute('aria-label', t('search.aria')); $('#mobSearch button').setAttribute('aria-label', t('common.close')); }
  $('#live').textContent = '';
}

applyLangBase();
