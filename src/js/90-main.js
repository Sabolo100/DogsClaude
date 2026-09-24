/* ==========================================================================
   Indítás, globális események, PWA
   ========================================================================== */
function init() {
  applyTheme();
  document.documentElement.classList.toggle('rm', RM());
  S.mode = store.get('mode', null);
  const h = decodeHash();
  if (h.quiz) S.quiz = { answers: h.quiz, crit: quizCrit(h.quiz), done: true };
  stage.classList.toggle('mobile', S.mobile);
  renderFilters();
  $('#listView').hidden = S.view !== 'lista';
  bubblesEl.style.visibility = S.view === 'lista' ? 'hidden' : '';
  stage.classList.toggle('list', S.view === 'lista');
  markFav();
  updateBadges();
  fxResize();
  $('#logo').classList.add('hi5');
  setTimeout(() => $('#logo').classList.remove('hi5'), 1200);
  intro();
  requestAnimationFrame(t => { lastT = t; frame(t); });
  setTimeout(initRoving, 1600);
  if (h.card) setTimeout(() => openCard(h.card, { push: false }), 1300);
  else if (h.kviz) { syncHash(); setTimeout(() => openDrawer('kviz'), 1300); }
  store.set('visits', store.get('visits', 0) + 1);
  if (!store.get('coach', 0) && !h.card && !h.kviz && !/[?&]nocoach/.test(location.search)) setTimeout(() => { if (!S.card && !S.drawer) coach(0); }, 2600);
  else setTimeout(() => maybeInstall(), 5000);
  if ('serviceWorker' in navigator && window.PACSI_PWA && location.protocol.startsWith('http')) {
    navigator.serviceWorker.register('sw.js').then(reg => {
      reg.addEventListener('updatefound', () => {
        const nw = reg.installing;
        nw && nw.addEventListener('statechange', () => {
          if (nw.state === 'installed' && navigator.serviceWorker.controller) toast('Új verzió érhető el', { action: 'Frissítés', onAction: () => location.reload(), ms: 6000 });
        });
      });
    }).catch(() => {});
  }
}

/* Átméretezés, forgatás, mobil/desktop váltás */
let rzTimer = 0;
new ResizeObserver(() => {
  clearTimeout(rzTimer);
  rzTimer = setTimeout(() => { fxResize(); relayout(); segAll(); }, 90);
}).observe(stage);
mqMobile.addEventListener('change', () => {
  S.mobile = mqMobile.matches;
  stage.classList.toggle('mobile', S.mobile);
  closePanelSheet();
  if (S.drawer) closeDrawer();
  if (!cardEl.hidden) closeCard();
  refresh();
});
mqRM.addEventListener('change', () => document.documentElement.classList.toggle('rm', RM()));

/* Billentyűzet */
addEventListener('keydown', e => {
  const typing = /INPUT|TEXTAREA/.test(document.activeElement && document.activeElement.tagName);
  if (e.key === 'Escape') {
    if (!cardEl.hidden) return closeCard();
    if (!$('#coach').hidden) return coach(COACH.length);
    if (S.drawer) return closeDrawer();
    if ($('#panel').classList.contains('open')) return closePanelSheet();
    if (!$('#mobSearch').hidden) return closeMobSearch();
  }
  if (typing) return;
  if (e.key === '/' && !S.mobile) { e.preventDefault(); qInput.focus(); return; }
  if (!cardEl.hidden && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) { e.preventDefault(); navCard(e.key === 'ArrowRight' ? 1 : -1); }
});

/* Vissza gomb (böngésző / Android) */
addEventListener('popstate', () => {
  const p = new URLSearchParams(location.hash.slice(1));
  const b = p.get('b');
  if (!b && !cardEl.hidden) closeCard({ fromPop: true });
  else if (b && b !== S.card && BY_ID.has(b)) openCard(b, { push: false });
});

/* Logó: pacsi + alaphelyzet */
$('#logo').addEventListener('click', e => {
  e.preventDefault();
  const l = $('#logo');
  l.classList.remove('hi5'); void l.offsetWidth; l.classList.add('hi5');
  if (!cardEl.hidden) closeCard();
  if (S.drawer) closeDrawer();
  if (S.view !== 'felho') setView('felho');
  if (S.crit.length) clearAll();
  const q = l.getBoundingClientRect();
  spark(q.right - 14, q.top + 6, 14, { speed: 4 });
});
$('#surpriseBtn').addEventListener('click', surprise);

/* Telefon megrázása = meglepetés (ahol engedély nélkül elérhető) */
if ('DeviceMotionEvent' in window && typeof DeviceMotionEvent.requestPermission !== 'function') {
  let lastShake = 0;
  addEventListener('devicemotion', e => {
    const a = e.accelerationIncludingGravity;
    if (!a) return;
    const f = Math.hypot(a.x || 0, a.y || 0, a.z || 0);
    if (f > 28 && now() - lastShake > 2500 && !S.card && !S.drawer) { lastShake = now(); surprise(); }
  });
}

init();
