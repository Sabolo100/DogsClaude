/* ==========================================================================
   Felület: szűrőpanel, dokk, HUD, lista, üres állapot, téma, bemutató
   ========================================================================== */
const TOTAL = BREEDS.length;

/* ---------- Szegmentált vezérlő mozgó „hüvelykujjal” ---------- */
function segThumb(seg) {
  if (!seg || seg.offsetParent === null) return;
  let th = seg.querySelector('.thumb');
  if (!th) { th = document.createElement('i'); th.className = 'thumb'; seg.prepend(th); }
  const on = seg.querySelector('[aria-selected="true"],[aria-checked="true"]');
  if (!on) { th.style.width = '0px'; return; }
  th.style.width = on.offsetWidth + 'px';
  th.style.transform = `translateX(${on.offsetLeft}px)`;
}
const segAll = () => ['#views', '#modeSeg', '#groupSeg', '#mobViews'].forEach(s => segThumb($(s)));

/* ---------- Szűrőpanel ---------- */
const chip = (k, v, label, extra = '') => `<button class="chip" data-k="${k}" data-v="${v}" aria-pressed="false">${extra}<span class="ck">${ic('check')}</span>${label}<span class="n"></span></button>`;
const tog = t => `<button class="tog" data-k="t" data-v="${t.id}" aria-pressed="false" style="--tc:${t.c}"><span class="ti">${ic(t.i)}</span><span class="tl">${t.l}<small>${t.sub}</small></span><span class="n chip-n"></span><span class="sw" aria-hidden="true"></span></button>`;
const fsec = (id, title, body, more = '') => `<section class="fsec" data-sec="${id}"><h3>${title}${more}</h3>${body}</section>`;
function renderFilters() {
  const tg = g => TOGGLES.filter(t => t.g === g).map(tog).join('');
  $('#filters').innerHTML =
    fsec('meret', 'Méret', `<div class="chips sizes">${SIZES.map(([k, l], i) =>
      `<button class="chip size" data-k="meret" data-v="${k}" aria-pressed="false"><svg viewBox="0 0 64 44" style="height:${10 + i * 3}px;width:${(10 + i * 3) * 64 / 44}px" aria-hidden="true"><use href="#i-dog"/></svg>${l}<span class="ck">${ic('check')}</span><span class="n"></span></button>`).join('')}</div>`) +
    fsec('energia', 'Energia', `<div class="chips">${ENERGY.map(([k, l]) => chip('energia', k, l)).join('')}</div>`) +
    fsec('eletmod', 'Életmód', tg('eletmod')) +
    fsec('szor', 'Szőrzet', `<div class="chips">${COATS.map(([k, l]) => chip('szor', k, l)).join('')}</div>`) +
    fsec('gondozas', 'Gondozás', tg('gondozas')) +
    fsec('egeszseg', 'Egészség', tg('egeszseg')) +
    fsec('szerep', 'Szerep', `<div class="chips">${ROLES.map(([k, l]) => chip('szerep', k, l)).join('')}</div>`) +
    fsec('kulonleges', 'Különleges', `<div class="chips">${chip('t', 'magyar', 'Magyar fajta', ic('flag'))}</div>`) +
    fsec('fci', 'FCI-csoport', `<div class="chips" id="fciChips" hidden>${Object.entries(FCI).map(([k, l]) => chip('fci', k, `${k}. ${l}`)).join('')}</div>`,
      `<button class="more" id="fciMore" aria-expanded="false">Mutasd</button>`);
}
const isOn = (k, v) => k === 't' ? S.f.t.has(v) : k === 'energia' ? S.f.energia === v : S.f[k].has(k === 'fci' ? +v : v);
function mutate(f, k, v) {
  if (k === 't') f.t.has(v) ? f.t.delete(v) : f.t.add(v);
  else if (k === 'energia') f.energia = f.energia === v ? null : v;
  else { const val = k === 'fci' ? +v : v; f[k].has(val) ? f[k].delete(val) : f[k].add(val); }
}
function srcPoint(el) {
  if (!el) return null;
  const q = el.getBoundingClientRect();
  return { x: q.left + q.width / 2 - SR.left, y: q.top + q.height / 2 - SR.top };
}
function toggleFilter(k, v, el) {
  mutate(S.f, k, v);
  haptic(8);
  refresh(srcPoint(el));
}
function updateFilterUI() {
  for (const el of $$('#filters [data-k]')) {
    const { k, v } = el.dataset;
    const on = isOn(k, v);
    el.setAttribute('aria-pressed', on);
    const n = el.querySelector('.n');
    if (!n) continue;
    if (on) { n.textContent = ''; continue; }
    const c = previewCount(f => mutate(f, k, v));
    n.textContent = c;
    n.classList.toggle('zero', c === 0);
  }
  const k = filterCount() + (S.quiz ? 1 : 0);
  $('#activeCount').hidden = !k;
  $('#activeCount').innerHTML = `<span>${k} aktív</span>`;
  $('#clearBtn').hidden = !k;
}
$('#filters').addEventListener('click', e => {
  const more = e.target.closest('#fciMore');
  if (more) {
    const box = $('#fciChips'), open = box.hidden;
    box.hidden = !open; more.textContent = open ? 'Elrejt' : 'Mutasd'; more.setAttribute('aria-expanded', open);
    return;
  }
  const el = e.target.closest('[data-k]');
  if (el) toggleFilter(el.dataset.k, el.dataset.v, el);
});
function clearAll(src) {
  S.f.meret.clear(); S.f.szor.clear(); S.f.szerep.clear(); S.f.fci.clear(); S.f.t.clear(); S.f.energia = null;
  S.quiz = null;
  if (!RM()) for (const o of B) if (o.st === 'in') o.r *= .94;
  refresh(src || { x: LR.cx, y: LR.cy });
}
$('#clearBtn').addEventListener('click', e => clearAll(srcPoint(e.currentTarget)));
$('#quizBtn').addEventListener('click', () => openDrawer('kviz'));

/* ---------- Mobil szűrődokk ---------- */
const DOCK = [
  { id: 'meret', l: 'Méret', i: 'ruler', sec: 'meret' },
  { id: 'gyerek', l: 'Gyerek', i: 'kid', t: 'gyerek' },
  { id: 'lakas', l: 'Lakás', i: 'home', t: 'lakas' },
  { id: 'csendes', l: 'Csendes', i: 'quiet', t: 'csendes' },
  { id: 'szor', l: 'Szőr', i: 'coat', sec: 'szor' },
  { id: 'energia', l: 'Energia', i: 'bolt', sec: 'energia' },
  { id: 'hullas', l: 'Hullás', i: 'feather', t: 'hullas' },
  { id: 'kezdo', l: 'Kezdő', i: 'sprout', t: 'kezdo' },
  { id: 'magyar', l: 'Magyar', i: 'flag', t: 'magyar' },
  { id: 'szerep', l: 'Szerep', i: 'star', sec: 'szerep' },
  { id: 'mind', l: 'Mind', i: 'sliders', sec: 'all' },
];
$('#dock').innerHTML = DOCK.map(d => `<button class="dk" data-dk="${d.id}" aria-pressed="false"><span class="o">${ic(d.i)}</span><span>${d.l}</span><b class="cb">${ic('check')}</b></button>`).join('');
$('#dock').addEventListener('click', e => {
  const el = e.target.closest('.dk');
  if (!el) return;
  const d = DOCK.find(x => x.id === el.dataset.dk);
  if (d.t) toggleFilter('t', d.t, el);
  else openPanelSheet(d.sec);
});
function updateDock() {
  for (const el of $$('.dk')) {
    const d = DOCK.find(x => x.id === el.dataset.dk);
    let n = 0;
    if (d.t) n = S.f.t.has(d.t) ? 1 : 0;
    else if (d.sec === 'energia') n = S.f.energia ? 1 : 0;
    else if (d.sec === 'all') n = filterCount() + (S.quiz ? 1 : 0);
    else n = S.f[d.sec].size;
    el.classList.toggle('on', n > 0);
    el.setAttribute('aria-pressed', n > 0);
    el.querySelector('.cb').innerHTML = d.t || n === 1 && d.sec !== 'all' ? ic('check') : n;
  }
}
function openPanelSheet(sec) {
  const p = $('#panel');
  p.classList.add('open');
  p.classList.toggle('full', sec === 'all');
  const target = sec !== 'all' && $(`.fsec[data-sec="${sec}"]`);
  $$('.fsec', p).forEach(s => { s.style.display = sec === 'all' || s === target ? '' : 'none'; });
  if (target && sec === 'fci') { $('#fciChips').hidden = false; }
  $('.panel-body', p).scrollTop = 0;
  relayout();
}
function closePanelSheet() {
  const p = $('#panel');
  if (!p.classList.contains('open')) return;
  p.classList.remove('open');
  setTimeout(() => $$('.fsec', p).forEach(s => { s.style.display = ''; }), 500);
  relayout();
}
$('#panelClose').addEventListener('click', closePanelSheet);
stage.addEventListener('pointerdown', e => { if (S.mobile && $('#panel').classList.contains('open') && !e.target.closest('.b')) closePanelSheet(); });
dragToClose($('#panel'), $('.sheet-handle', $('#panel')), closePanelSheet);

/* Lap lehúzással zárása (bottom sheet) */
function dragToClose(sheet, handle, onClose) {
  let y0 = null, dy = 0;
  handle.style.touchAction = 'none';
  handle.addEventListener('pointerdown', e => { y0 = e.clientY; dy = 0; handle.setPointerCapture(e.pointerId); sheet.style.transition = 'none'; });
  handle.addEventListener('pointermove', e => {
    if (y0 == null) return;
    dy = Math.max(0, e.clientY - y0);
    sheet.style.transform = `translateY(${dy}px)`;
  });
  const end = () => {
    if (y0 == null) return;
    y0 = null;
    sheet.style.transition = '';
    sheet.style.transform = '';
    if (dy > 90) onClose();
  };
  handle.addEventListener('pointerup', end);
  handle.addEventListener('pointercancel', end);
}
function relayout() {
  requestAnimationFrame(() => {
    measure(); computeTargets(); schedule(null, { instant: true }); drawGroups(); drawMap();
  });
}

/* ---------- HUD ---------- */
function setOdo(n) {
  const s = String(n), odo = $('#odo');
  while (odo.children.length < s.length) {
    const dg = document.createElement('span');
    dg.className = 'dg';
    dg.innerHTML = `<i>${[...Array(10)].map((_, d) => `<span>${d}</span>`).join('')}</i>`;
    odo.prepend(dg);
  }
  while (odo.children.length > s.length) odo.firstElementChild.remove();
  [...odo.children].forEach((dg, i) => { dg.firstElementChild.style.transform = `translateY(${-s[i] * 10}%)`; });
}
function removeCrit(key) {
  if (key === 'quiz') S.quiz = null;
  else if (key === 'energia') S.f.energia = null;
  else if (S.f[key] instanceof Set) S.f[key].clear();
  else S.f.t.delete(key);
}
function renderActiveChips() {
  const box = $('#activeChips');
  const chips = S.crit.filter(c => c.src !== 'quiz').map(c => `<span class="achip">${esc(c.label)}<button data-rm="${c.key}" aria-label="${esc(c.label)} törlése">${ic('x')}</button></span>`);
  if (S.quiz) chips.push(`<span class="achip quiz">${ic('sparkle')} Kvíz-eredmény<button data-rm="quiz" aria-label="Kvíz törlése">${ic('x')}</button></span>`);
  box.innerHTML = chips.join('');
}
$('#activeChips').addEventListener('click', e => {
  const b = e.target.closest('[data-rm]');
  if (!b) return;
  removeCrit(b.dataset.rm);
  refresh(srcPoint(b));
});
let lastCount = TOTAL, liveTimer = 0;
function updateHud() {
  const active = S.crit.length > 0;
  const count = active ? BREEDS.filter(fits).length : TOTAL;
  setOdo(count);
  $('#ofTotal').textContent = `/ ${TOTAL}`;
  $('#ofLabel').textContent = active ? 'illik hozzád' : 'vár rád';
  renderActiveChips();
  for (const b of $$('#modeSeg button')) b.setAttribute('aria-checked', b.dataset.mode === modeOf());
  const gs = $('#groupSeg');
  gs.hidden = S.view !== 'csoport';
  if (!gs.hidden) for (const b of $$('button', gs)) b.setAttribute('aria-checked', b.dataset.g === S.groupBy);
  for (const b of $$('#views button, #mobViews button')) b.setAttribute('aria-selected', b.dataset.view === S.view);
  // mobil
  const mc = $('#mobCount');
  const visCount = active && modeOf() === 'strict' ? BREEDS.filter(b => b.ok).length : count;
  mc.innerHTML = `<b>${visCount}</b> fajta`;
  if (visCount !== lastCount) { mc.classList.remove('bump'); void mc.offsetWidth; mc.classList.add('bump'); }
  // a kiértékelt állapotból számolva (a buborékok célállapota itt még a régi)
  const hidden = S.view !== 'lista' && active && modeOf() === 'strict' ? BREEDS.filter(b => !b.ok).length : 0;
  $('#flyCloud').hidden = !(S.mobile && (hidden > 0 || flownShown > 0));
  $('#mobMode').innerHTML = modeOf() === 'strict' ? `${ic('sliders')}Csak találatok` : `${ic('cloud')}Rangsor`;
  const fc = filterCount() + (S.quiz ? 1 : 0);
  $('#mobClear').hidden = !fc;
  $('#mobClear').innerHTML = `${fc} szűrő · Törlés`;
  lastCount = visCount;
  clearTimeout(liveTimer);
  liveTimer = setTimeout(() => { $('#live').textContent = active ? `${count} fajta felel meg a szűrőknek.` : `${TOTAL} fajta látható.`; }, 700);
  requestAnimationFrame(segAll);
}
function updateCloud(bumpIt) {
  const el = $('#flyCloud');
  el.querySelector('b').textContent = flownShown;
  if (bumpIt) { el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); }
}
bus.on('cloud', updateCloud);

/* Nézet- és módváltók */
$('#groupSeg').innerHTML = Object.entries(GROUPERS).map(([k, g]) => `<button role="radio" data-g="${k}">${g.l}</button>`).join('');
$('#mobViews').innerHTML = [['felho', 'cloud', 'Felhő'], ['csoport', 'groups', 'Csoport'], ['terkep', 'map', 'Térkép'], ['lista', 'list', 'Lista']]
  .map(([v, i, l]) => `<button data-view="${v}" aria-label="${l}">${ic(i)}<span>${l}</span></button>`).join('');
function setView(v) {
  if (S.view === v) return;
  const wasList = S.view === 'lista';
  S.view = v;
  $('#listView').hidden = v !== 'lista';
  bubblesEl.style.visibility = v === 'lista' ? 'hidden' : '';
  stage.classList.toggle('list', v === 'lista');
  if (v === 'lista') clearUnder();
  if (wasList && !RM()) for (const o of B) { o.r = .5; }
  refresh(null, { instant: false });
  if (!RM() && v !== 'lista') for (const o of B) if (o.st === 'in') { o.vx += rand(-6, 6); o.vy += rand(-6, 6); }
}
$('#views').addEventListener('click', e => { const b = e.target.closest('[data-view]'); if (b) setView(b.dataset.view); });
$('#mobViews').addEventListener('click', e => { const b = e.target.closest('[data-view]'); if (b) setView(b.dataset.view); });
$('#groupSeg').addEventListener('click', e => { const b = e.target.closest('[data-g]'); if (b) { S.groupBy = b.dataset.g; refresh(); } });
function setMode(m) {
  S.mode = m;
  store.set('mode', m);
  refresh({ x: LR.cx, y: LR.t });
}
$('#modeSeg').addEventListener('click', e => { const b = e.target.closest('[data-mode]'); if (b) setMode(b.dataset.mode); });
$('#mobMode').addEventListener('click', () => setMode(modeOf() === 'strict' ? 'rank' : 'strict'));
$('#mobClear').addEventListener('click', e => clearAll(srcPoint(e.currentTarget)));
$('#flyCloud').addEventListener('click', () => openDrawer('kirepultek'));

/* ---------- Lista nézet ---------- */
function renderList() {
  const box = $('#listView');
  if (S.view !== 'lista') { box.innerHTML = ''; return; }
  // A lista a számláló / szűrő-pillek ALATT kezdődik (nem csak alá van tolva), így görgetéskor
  // a kártyák nem csúsznak be a fejléc mögé.
  const hudBottom = $(S.mobile ? '#mobHud' : '#hud').getBoundingClientRect().bottom;
  box.style.top = Math.max(0, Math.round(hudBottom - stage.getBoundingClientRect().top + (S.mobile ? 6 : 10))) + 'px';
  box.style.paddingTop = '8px';
  const active = S.crit.length > 0;
  const arr = [...BREEDS].sort((a, b) => active ? (b.ok - a.ok) || (b.m - a.m) : (b.nep - a.nep) || COLL.compare(a.nev, b.nev));
  box.innerHTML = arr.map((b, i) => `<button class="lcard${active && !b.ok ? ' out' : ''}" data-id="${b.id}" style="${picStyle(b)};animation-delay:${Math.min(i, 30) * 18}ms">
    ${active ? `<span class="m">${Math.round(b.m * 100)}%</span>` : ''}<i class="pic"></i><h4>${esc(b.nev)}</h4><p>${esc(b.tagline)}</p></button>`).join('');
}
$('#listView').addEventListener('click', e => { const c = e.target.closest('.lcard'); if (c) openCard(c.dataset.id); });

/* ---------- Üres állapot ---------- */
function renderEmpty() {
  const box = $('#empty');
  const show = S.view !== 'lista' && S.crit.length && modeOf() === 'strict' && !BREEDS.some(b => b.ok);
  box.hidden = !show;
  if (!show) return;
  const own = S.crit.filter(c => c.src !== 'quiz');
  const sugg = own.map(c => ({ c, n: BREEDS.filter(b => own.every(x => x === c || x.pass(b))).length }))
    .filter(s => s.n > 0).sort((a, b) => b.n - a.n).slice(0, 3);
  const kk = SPARES['kerdo-kutya'];
  box.innerHTML = `<div class="pic" style="background-image:url('${portrait(kk.id)}');background-color:${kk.bg}"></div>
    <h3>Nincs ilyen kutya… még.</h3>
    <p>${sugg.length ? 'Engedj el egy szűrőt, és visszajönnek:' : 'Próbálj kevesebb szűrőt, vagy válts Rangsor módra.'}</p>
    <div class="chips">${sugg.map(s => `<button class="chip" data-rm="${s.c.key}"><b>${esc(s.c.label)}</b> nélkül → +${s.n} fajta</button>`).join('')}
    ${sugg.length ? '' : '<button class="chip" data-mode="rank">Rangsor mód</button>'}</div>`;
}
$('#empty').addEventListener('click', e => {
  const b = e.target.closest('[data-rm],[data-mode]');
  if (!b) return;
  if (b.dataset.mode) return setMode('rank');
  removeCrit(b.dataset.rm);
  refresh(srcPoint(b));
});

/* ---------- Összehasonlító tálca és jelvények ---------- */
function renderTray() {
  const t = $('#tray');
  const was = !t.hidden;
  t.hidden = !S.cmp.length || S.mobile;
  if (t.hidden) return;
  t.innerHTML = S.cmp.map(id => { const b = BY_ID.get(id); return `<button class="mini" data-id="${id}" style="${picStyle(b)}" title="${esc(b.nev)}"><span class="x" data-x="${id}">${ic('x')}</span></button>`; }).join('') +
    `<button class="btn fill" id="trayGo">${ic('compare')}Összehasonlítás (${S.cmp.length})</button>`;
  if (!was) relayout();
}
$('#tray').addEventListener('click', e => {
  const x = e.target.closest('[data-x]');
  if (x) { e.stopPropagation(); toggleCmp(x.dataset.x); return; }
  const m = e.target.closest('.mini');
  if (m) return openCard(m.dataset.id);
  if (e.target.closest('#trayGo')) openDrawer('osszevet');
});
function updateBadges(bumpKey) {
  for (const el of $$('[data-badge]')) {
    const n = el.dataset.badge === 'fav' ? S.fav.size : S.cmp.length;
    el.hidden = !n;
    el.textContent = n;
    if (bumpKey === el.dataset.badge) { el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); }
  }
}

/* ---------- Toast ---------- */
let toastTimer = 0;
function toast(msg, { action, onAction, ms = 2600 } = {}) {
  const t = $('#toast');
  t.innerHTML = `<span>${msg}</span>${action ? `<button>${action}</button>` : ''}`;
  if (action) t.querySelector('button').onclick = () => { t.classList.remove('on'); onAction && onAction(); };
  t.classList.add('on');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('on'), action ? ms * 2 : ms);
}

/* ---------- Téma (világos / sötét) körkörös felfedéssel ---------- */
// 'auto' módban a gyökérelem data-theme bélyegéhez nem nyúlunk (azt a befogadó felület is beállíthatja)
const isDark = () => { const t = document.documentElement.dataset.theme; return t ? t === 'dark' : mqDark.matches; };
function applyTheme() {
  const r = document.documentElement;
  if (S.theme !== 'auto') r.dataset.theme = S.theme;
  const dark = isDark();
  $('#themeBtn use').setAttribute('href', dark ? '#i-sun' : '#i-moon');
  $$('meta[name="theme-color"]').forEach(m => m.setAttribute('content', dark ? '#14121A' : '#FBF6EE'));
}
function toggleTheme(e) {
  S.theme = isDark() ? 'light' : 'dark';
  store.set('theme', S.theme);
  if (!document.startViewTransition || RM()) return applyTheme();
  const x = e && e.clientX ? e.clientX : innerWidth - 40, y = e && e.clientY ? e.clientY : 40;
  const rad = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
  const vt = document.startViewTransition(applyTheme);
  vt.ready.then(() => document.documentElement.animate(
    { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${rad}px at ${x}px ${y}px)`] },
    { duration: 650, easing: 'cubic-bezier(.22,1,.36,1)', pseudoElement: '::view-transition-new(root)' })).catch(() => {});
}
$('#themeBtn').addEventListener('click', toggleTheme);
mqDark.addEventListener('change', applyTheme);

/* ---------- Mobil kereső ---------- */
function openMobSearch() {
  const box = $('#mobSearch');
  box.hidden = false;
  box.innerHTML = `${ic('search')}<input type="search" placeholder="Keress fajtát… pl. vizsla" aria-label="Fajta keresése" value="${esc(S.q)}"><button class="icbtn" aria-label="Bezárás">${ic('x')}</button>`;
  const inp = $('input', box);
  inp.focus();
  inp.addEventListener('input', () => applySearch(inp.value));
  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') { const h = applySearch(inp.value); if (h[0]) { inp.blur(); openCard(h[0].b.id); } }
    if (e.key === 'Escape') closeMobSearch();
  });
  $('button', box).addEventListener('click', closeMobSearch);
}
function closeMobSearch() { $('#mobSearch').hidden = true; applySearch(''); }
$('#mobSearchBtn').addEventListener('click', openMobSearch);
const qInput = $('#q');
qInput.addEventListener('input', () => applySearch(qInput.value));
qInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') { const h = applySearch(qInput.value); if (h[0]) openCard(h[0].b.id); }
  if (e.key === 'Escape') { qInput.value = ''; applySearch(''); qInput.blur(); }
});

/* ---------- Bemutató (coach mark) ---------- */
const COACH = [
  { t: () => stage, h: 'Szia, itt a Pacsi! 🐾', p: () => `Ez itt ${TOTAL} kutyafajta egy felhőben. ${S.mobile ? 'Koppints' : 'Vidd az egeret'} egy buborékra, és megtudod, ki az.` },
  { t: () => S.mobile ? $('#dock') : $('#panel'), h: 'Szűrj, és figyeld!', p: () => S.mobile ? 'Kapcsolj be egy szűrőt: ami nem illik hozzád, kirepül.' : 'Kapcsolj be egy szűrőt, és nézd, ki ugrik előre!' },
  { t: () => S.mobile ? $('[data-tab="kviz"]') : $('#quizBtn'), h: 'Nem tudod, hol kezdd?', p: () => 'A Párkereső kvíz 10 kérdés, kb. 1 perc – és élőben formálja a felhőt.' },
];
function coach(i = 0) {
  const box = $('#coach');
  if (i >= COACH.length) { box.hidden = true; store.set('coach', 1); return; }
  const c = COACH[i], tg = c.t();
  box.hidden = false;
  box.className = 'coach';
  box.innerHTML = `<h4>${c.h}</h4><p>${c.p()}</p><div class="row"><span class="dots3">${COACH.map((_, j) => `<i class="${j === i ? 'on' : ''}"></i>`).join('')}</span>
    <span><button class="link" data-skip>Kihagyom</button> <button class="btn fill" data-next style="height:38px;padding:0 16px">${i === COACH.length - 1 ? 'Kezdjük!' : 'Tovább'}</button></span></div>`;
  const q = tg.getBoundingClientRect(), w = box.offsetWidth, h = box.offsetHeight;
  let x, y;
  if (i === 0) { x = q.left + q.width / 2 - w / 2; y = q.top + q.height / 2 + 60; box.style.setProperty('--ax', w / 2 - 8 + 'px'); }
  else if (!S.mobile && i === 1) { x = q.right + 16; y = q.top + 120; box.classList.add('left'); box.style.setProperty('--ay', '30px'); }
  else if (!S.mobile && i === 2) { x = q.right + 16; y = q.top + q.height / 2 - h / 2; box.classList.add('left'); box.style.setProperty('--ay', h / 2 - 8 + 'px'); }
  else { x = 16; y = q.top - h - 14; box.classList.add('up'); box.style.setProperty('--ax', clamp(q.left + q.width / 2 - 16 - 8, 20, w - 30) + 'px'); }
  box.style.left = clamp(x, 12, innerWidth - w - 12) + 'px';
  box.style.top = clamp(y, 12, innerHeight - h - 12) + 'px';
  $('[data-next]', box).onclick = () => coach(i + 1);
  $('[data-skip]', box).onclick = () => coach(COACH.length);
}

/* ---------- Telepítési ajánlat (PWA) ---------- */
let installEvt = null;
addEventListener('beforeinstallprompt', e => { e.preventDefault(); installEvt = e; });
const standalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone;
function maybeInstall(reason) {
  if (ARTIFACT || standalone() || store.get('installAsked', 0) > 1) return;
  const visits = store.get('visits', 0);
  if (reason !== 'quiz' && visits < 2) return;
  if (installEvt) {
    toast('Tedd ki a kezdőképernyőre – offline is működik!', { action: 'Telepítés', onAction: () => installEvt.prompt(), ms: 5000 });
    store.set('installAsked', store.get('installAsked', 0) + 1);
  } else if (/iPhone|iPad|iPod/.test(navigator.userAgent) && location.protocol.startsWith('http')) {
    toast('Tipp: Megosztás → „Főképernyőhöz adás” – és a Pacsi appként fut.', { ms: 6000 });
    store.set('installAsked', store.get('installAsked', 0) + 1);
  }
}

/* ---------- Állapotfrissítés bekötése ---------- */
bus.on('pre', () => { updateHud(); updateFilterUI(); updateDock(); });
bus.on('post', () => { renderList(); renderEmpty(); renderTray(); stage.classList.toggle('filtered', S.crit.length > 0); });
