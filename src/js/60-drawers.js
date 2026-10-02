/* ==========================================================================
   Fiókok: Párkereső kvíz, Kedvencek, Összehasonlítás, Tippek, Kirepültek
   ========================================================================== */
const drawerEl = $('#drawer');
let Q = { i: 0, answers: [] };
const drawerTitle = name => t(`drawer.${name}`);   // kviz, kedvencek, osszevet, tippek, kirepultek

function openDrawer(name) {
  if (S.drawer === name) return;
  closePanelSheet();
  if (!cardEl.hidden) closeCard();
  if (name === 'kviz' && !(S.quiz && !S.quiz.done)) Q = { i: 0, answers: [] };
  if (name === 'kviz' && S.quiz && S.quiz.done) Q = { i: QUIZ.length, answers: S.quiz.answers.slice() };
  S.drawer = name;
  if (name === 'osszevet' && S.cmp.length > 1) stat('osszevetes', { fajtak: S.cmp.map(id => BY_ID.get(id).nev0).join(' · ') });
  drawerEl.hidden = false;
  drawerEl.classList.remove('out');
  drawerEl.classList.toggle('short', name === 'kviz');
  drawerEl.setAttribute('aria-label', drawerTitle(name));
  renderDrawer();
  const needScrim = S.mobile && name !== 'kviz';
  if (needScrim) { scrimEl.hidden = false; scrimEl.classList.remove('out'); }
  else if (!scrimEl.hidden && cardEl.hidden) scrimEl.hidden = true;   // pl. Tippek → Kvíz: a kvíz alatt a felhő látsszon
  updateTabs();
  relayout();
  setTimeout(() => { const f = $('.qopt, .d-body button, [data-dclose]', drawerEl); f && f.focus({ preventScroll: true }); }, 350);
}
function closeDrawer() {
  if (!S.drawer) return;
  S.drawer = null;
  drawerEl.classList.add('out');
  if (!scrimEl.hidden && cardEl.hidden) { scrimEl.classList.add('out'); setTimeout(() => { if (cardEl.hidden) scrimEl.hidden = true; }, 300); }
  setTimeout(() => { if (!S.drawer) drawerEl.hidden = true; }, 340);
  updateTabs();
  relayout();
}
function updateTabs() {
  for (const b of $$('#tabbar button')) b.classList.toggle('on', (b.dataset.tab === 'felfedez' && !S.drawer) || b.dataset.tab === S.drawer);
}
function renderDrawer() {
  const name = S.drawer;
  if (!name) return;
  let body = '', foot = '';
  if (name === 'kviz') [body, foot] = quizView();
  else if (name === 'kedvencek') [body, foot] = favView();
  else if (name === 'osszevet') [body, foot] = cmpView();
  else if (name === 'tippek') [body, foot] = tipsView();
  else if (name === 'kirepultek') [body, foot] = flownView();
  drawerEl.innerHTML = `<div class="handle" aria-hidden="true"></div>
    <div class="d-head"><h2>${drawerTitle(name)}</h2><button class="icbtn" data-dclose aria-label="${esc(t('common.close'))}">${ic('x')}</button></div>
    <div class="d-body">${body}</div>${foot ? `<div class="d-foot">${foot}</div>` : ''}`;
  if (name === 'kviz' && Q.i >= QUIZ.length && !Q.prev && !RM()) {   // egy válasz módosítása után nincs újabb tűzijáték
    const q = drawerEl.getBoundingClientRect();
    spark(q.left + q.width / 2, q.top + 120, 40, { speed: 8, g: .15 });
  }
}
drawerEl.addEventListener('click', e => {
  if (e.target.closest('[data-dclose]')) return closeDrawer();
  const t = e.target;
  const opt = t.closest('.qopt');
  if (opt) return answer(+opt.dataset.a, opt);
  if (t.closest('[data-qback]')) { Q.i = Math.max(0, Q.i - 1); return renderDrawer(); }
  if (t.closest('[data-qrestart]')) { clearTimeout(qTimer); Q = { i: 0, answers: [] }; S.quiz = null; refresh(); return renderDrawer(); }
  if (t.closest('[data-qcloud]')) { closeDrawer(); if (S.view === 'lista') setView('felho'); return; }
  if (t.closest('[data-qshare]')) return shareQuiz();
  if (t.closest('[data-qresult]')) return quizBack();
  const qe = t.closest('[data-qedit]');
  if (qe) return quizEdit(+qe.dataset.qedit);
  if (t.closest('[data-tquiz]')) return openDrawer('kviz');
  const open = t.closest('[data-open]');
  if (open) return openCard(open.dataset.open);
  const unfav = t.closest('[data-unfav]');
  if (unfav) return toggleFav(unfav.dataset.unfav);
  const tcmp = t.closest('[data-tcmp]');
  if (tcmp) return toggleCmp(tcmp.dataset.tcmp, tcmp);
  if (t.closest('[data-favshare]')) return shareFavs();
  if (t.closest('[data-clearall]')) { clearAll(); closeDrawer(); return; }
  const set = t.closest('[data-set]');
  if (set) return setting(set.dataset.set, set);
});
/* Mobilon a fogantyú / fejléc lehúzásával zárható */
(() => {
  let y0 = null, dy = 0;
  drawerEl.addEventListener('pointerdown', e => {
    if (!S.mobile || !e.target.closest('.handle, .d-head') || e.target.closest('button')) return;
    y0 = e.clientY; dy = 0; drawerEl.setPointerCapture(e.pointerId); drawerEl.style.transition = 'none';
  });
  drawerEl.addEventListener('pointermove', e => { if (y0 == null) return; dy = Math.max(0, e.clientY - y0); drawerEl.style.transform = `translateY(${dy}px)`; });
  const end = () => { if (y0 == null) return; y0 = null; drawerEl.style.transition = ''; drawerEl.style.transform = ''; if (dy > 90) closeDrawer(); };
  drawerEl.addEventListener('pointerup', end);
  drawerEl.addEventListener('pointercancel', end);
})();

/* ---------- Kvíz ----------
   A kész kvíz bármelyik válasza módosítható az eredmény „A válaszaid” listájából (Q.edit: a módosítás előtti
   állapot). Visszatéréskor Q.prev őrzi az utolsó tényleges módosítás előtti állapotot: ebből mutatja az eredmény,
   mi változott (gazditípus, helyezések, százalékok, kiesettek). */
let qTimer = 0;
const mPct = b => Math.round(b.m * 100);
const focusIn = sel => { const f = $(sel, drawerEl); f && f.focus({ preventScroll: true }); };
function quizView() {
  if (Q.i >= QUIZ.length) return quizResult();
  const q = QUIZ[Q.i], ed = Q.edit;
  const fitting = S.quiz ? BREEDS.filter(b => b.ok && b.m >= .55).length : TOTAL;
  return [`<div class="qprog">${QUIZ.map((_, j) => `<i class="${ed || j < Q.i || (j === Q.i && Q.answers[j] != null) ? 'on' : ''}"></i>`).join('')}</div>
    <div class="qnum">${t('quiz.num', { i: Q.i + 1, n: QUIZ.length })}${ed ? t('quiz.editSuffix') : ''}</div>
    <div class="qtext">${q.q}</div>
    <div class="qopts">${q.a.map((a, j) => `<button class="qopt${Q.answers[Q.i] === j ? ' sel' : ''}" data-a="${j}" style="--i:${j}"><span class="em">${a.e}</span><span>${a.t}</span></button>`).join('')}</div>
    <div class="qnav">${ed ? `<button class="link" data-qresult>${t('quiz.toResult')}</button>`
      : `<button class="link" data-qback ${Q.i ? '' : 'style="visibility:hidden"'}>${t('quiz.back')}</button><span class="qnum">${S.quiz ? tn('quiz.fitSoFar', fitting) : t('quiz.live')}</span>`}</div>`, ''];
}
function answer(j, el) {
  if (Q.i === 0 && Q.answers[0] == null) stat('kviz-indul');   // elkezdte (az első válasszal) – a befejezési arányhoz
  Q.answers[Q.i] = j;
  $$('.qopt', drawerEl).forEach(o => o.classList.toggle('sel', o === el));
  haptic(8);
  const edit = !!Q.edit;
  S.quiz = { answers: Q.answers.slice(), crit: quizCrit(Q.answers), done: edit };
  refresh({ x: S.mobile ? LR.cx : LR.r, y: S.mobile ? LR.b : LR.cy });
  // gyors dupla koppintásnál se ugorjon át egy kérdést: az utolsó választás számít, és csak egyszer lépünk tovább
  clearTimeout(qTimer);
  qTimer = setTimeout(() => {
    if (edit) return quizBack();
    Q.i++;
    if (Q.i >= QUIZ.length) {
      S.quiz.done = true; syncHash(); setTimeout(() => maybeInstall('quiz'), 2500);
      const top = topBreeds(1)[0];
      stat('kviz-kesz', { tipus: tH(`owner.${ownerType(Q.answers)}.n`), elso: top ? top.nev0 : '–' });
    }
    renderDrawer();
  }, 420);
}
function quizEdit(qi) {
  Q.edit = { qi, was: Q.answers[qi], type: ownerType(Q.answers), top: topBreeds(5).map(b => b.id), pct: new Map(BREEDS.map(b => [b.id, mPct(b)])) };
  Q.i = qi;
  renderDrawer();
  focusIn('.qopt.sel');
}
function quizBack() {
  clearTimeout(qTimer);
  const ed = Q.edit;
  Q.edit = null;
  Q.i = QUIZ.length;
  if (ed && Q.answers[ed.qi] !== ed.was) {
    Q.prev = ed;
    stat('kviz-modositas', { kerdes: `${ed.qi + 1}. ${quizTH(ed.qi)}`, valasz: quizTH(ed.qi, Q.answers[ed.qi]) });
  }
  renderDrawer();
  if (ed) focusIn(`[data-qedit="${ed.qi}"]`);
}
function topBreeds(n) { return [...BREEDS].sort((a, b) => (b.ok - a.ok) || (b.m - a.m)).slice(0, n); }
function quizResult() {
  const tk = ownerType(Q.answers), type = OWNER_TYPES[tk];
  const top = topBreeds(5);
  const P = Q.prev, newType = !!P && P.type !== tk;
  const rows = top.map((b, i) => {
    let tag = '', dp = '';
    if (P) {
      const r0 = P.top.indexOf(b.id), d = mPct(b) - P.pct.get(b.id);
      tag = r0 < 0 ? `<span class="qd new">${t('quiz.new')}</span>` : r0 > i ? `<span class="qd up">▲ ${r0 - i}</span>` : r0 < i ? `<span class="qd down">▼ ${i - r0}</span>` : '';
      if (d) dp = `<small class="${d > 0 ? 'up' : 'down'}">${d > 0 ? '+' : '−'}${Math.abs(d)}</small>`;
    }
    return `<button class="qrow" data-open="${b.id}" style="${picStyle(b)};--i:${i}"><span class="rk">${i + 1}</span><i class="pic"></i><span><h4>${esc(b.nev)}${tag}</h4><p>${esc(b.tagline)}</p></span><span class="pc">${mPct(b)}%${dp}</span></button>`;
  }).join('');
  let chg = '';
  if (P) {
    const q = QUIZ[P.qi], a0 = q.a[P.was], a1 = q.a[Q.answers[P.qi]];   // q.q, a.t: a szótárból, lásd labels() a 20-score.js-ben
    const out = P.top.filter(id => !top.some(b => b.id === id)).map(id => esc(BY_ID.get(id).nev));
    const same = !newType && !out.length && top.every((b, i) => P.top[i] === b.id && mPct(b) === P.pct.get(b.id));
    chg = `<div class="qchg"><b>✏️ ${P.qi + 1}. ${esc(q.q)}</b><span><s>${a0.e} ${esc(a0.t)}</s> → <b>${a1.e} ${esc(a1.t)}</b></span>
      ${same ? `<small>${t('quiz.unchanged')}</small>` : out.length ? `<small>${t('quiz.dropped', { v: out.join(', ') })}</small>` : ''}</div>`;
  }
  return [`${chg}<div class="qres-type"><span class="emo">${type.e}</span><div class="qnum" style="margin-top:6px">${t('quiz.yourType')}</div><h3>${type.n}${newType ? `<span class="qnew">${t('quiz.new')}</span>` : ''}</h3>
    ${newType ? `<p class="qwas">${t('quiz.was', { v: `${OWNER_TYPES[P.type].e} ${OWNER_TYPES[P.type].n}` })}</p>` : ''}<p>${type.d}</p></div>
    <h4 class="qh">${t('quiz.top5')}</h4>
    <div class="qtop">${rows}</div>
    <h4 class="qh">${t('quiz.answers')}</h4>
    <p class="qhint">${t(S.mobile ? 'quiz.hint.mobile' : 'quiz.hint.desktop')}</p>
    <div class="qans">${QUIZ.map((q, qi) => { const a = q.a[Q.answers[qi]]; return a ? `<button class="qa${P && P.qi === qi ? ' just' : ''}" data-qedit="${qi}"><span class="qn">${qi + 1}</span><span><small>${esc(q.q)}</small><b>${a.e} ${esc(a.t)}</b></span>${ic('chev-r')}</button>` : ''; }).join('')}</div>
    <p class="c-note" style="margin-top:14px">${t('quiz.note')}</p>`,
  `<button class="btn fill" data-qcloud style="flex:1">${ic('cloud')}${t('quiz.toCloud')}</button><button class="btn round" data-qshare aria-label="${esc(t('quiz.share'))}">${ic('share')}</button><button class="btn round ghost" data-qrestart aria-label="${esc(t('quiz.restart'))}" title="${esc(t('quiz.restart'))}">↺</button>`];
}

/* Megosztható eredménykép (vászon) */
const loadImg = src => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; });
async function shareQuiz() {
  const type = OWNER_TYPES[ownerType(S.quiz.answers)];
  stat('megosztas', { mit: 'kvíz-eredmény' });
  const top = topBreeds(3);
  const W = 1080, H = 1350, c = document.createElement('canvas');
  c.width = W; c.height = H;
  const x = c.getContext('2d');
  try { await document.fonts.ready; } catch (e) { /* nem kritikus */ }
  const dark = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() === '#14121A';
  x.fillStyle = dark ? '#14121A' : '#FBF6EE'; x.fillRect(0, 0, W, H);
  [['#FFD2B8', 140, 160, 520], ['#E2D6FF', 960, 420, 560], ['#C9EEDC', 380, 1240, 600]].forEach(([col, cx, cy, r]) => {
    const g = x.createRadialGradient(cx, cy, 0, cx, cy, r);
    g.addColorStop(0, col + (dark ? '55' : 'cc')); g.addColorStop(1, col + '00');
    x.fillStyle = g; x.fillRect(0, 0, W, H);
  });
  const ink = dark ? '#F4EFE8' : '#1E1B18', ink2 = dark ? '#B4ABA2' : '#6B625A';
  x.textAlign = 'center'; x.fillStyle = ink;
  x.font = '800 64px Fraunces, Georgia, serif'; x.fillText('Pacsi', W / 2, 110);
  x.fillStyle = ink2; x.font = '600 24px Manrope, system-ui, sans-serif'; x.fillText('by DarwinAI', W / 2, 146);
  x.fillStyle = '#FF6B3D'; x.beginPath(); x.arc(W / 2 + 62, 58, 9, 0, 6.283); x.fill();
  x.fillStyle = ink2; x.font = '600 30px Manrope, system-ui, sans-serif'; x.fillText(t('shareimg.type'), W / 2, 205);
  x.fillStyle = ink; x.font = '800 76px Fraunces, Georgia, serif'; x.fillText(`${type.e} ${type.n}`, W / 2, 295);
  x.fillStyle = ink2; x.font = '600 30px Manrope, system-ui, sans-serif'; x.fillText(t('shareimg.dogs'), W / 2, 380);
  const imgs = await Promise.all(top.map(b => loadImg(portrait(b.id)).catch(() => null)));
  const pos = [[W / 2, 610, 170], [250, 960, 130], [W - 250, 960, 130]];
  top.forEach((b, i) => {
    const [cx, cy, r] = pos[i];
    x.save(); x.shadowColor = 'rgba(90,50,20,.25)'; x.shadowBlur = 40; x.shadowOffsetY = 14;
    x.fillStyle = '#fff'; x.beginPath(); x.arc(cx, cy, r + 12, 0, 6.283); x.fill(); x.restore();
    x.save(); x.beginPath(); x.arc(cx, cy, r, 0, 6.283); x.clip();
    x.fillStyle = b.bg; x.fillRect(cx - r, cy - r, r * 2, r * 2);
    if (imgs[i]) x.drawImage(imgs[i], cx - r, cy - r, r * 2, r * 2);
    x.restore();
    x.fillStyle = '#EE5A2C'; x.beginPath(); x.arc(cx + r * .72, cy - r * .72, 44, 0, 6.283); x.fill();
    x.fillStyle = '#fff'; x.font = '800 30px Manrope, sans-serif'; x.fillText(Math.round(b.m * 100) + '%', cx + r * .72, cy - r * .72 + 11);
    x.fillStyle = ink; x.font = `700 ${i ? 36 : 46}px Fraunces, Georgia, serif`;
    x.fillText(b.nev.length > 22 ? b.nev.slice(0, 21) + '…' : b.nev, cx, cy + r + (i ? 62 : 74));
  });
  // a képet látók ide találnak el: a saját domain nagyobb és hangsúlyos, a fejlesztő alatta
  x.fillStyle = ink2; x.font = '600 28px Manrope, sans-serif'; x.fillText(t('shareimg.cta'), W / 2, H - 112);
  x.font = '800 40px Manrope, sans-serif'; x.fillStyle = '#EE5A2C'; x.fillText(SITE.url.replace(/^https?:\/\//, ''), W / 2, H - 62);
  x.font = '600 20px Manrope, sans-serif'; x.fillStyle = ink2; x.fillText('Pacsi by DarwinAI 🐾', W / 2, H - 26);
  const blob = await new Promise(r => c.toBlob(r, 'image/png'));
  if (ARTIFACT) {
    // az artifact-keret letiltja a letöltést és a Web Share-t: a képet itt mutatjuk meg, innen menthető
    const src = URL.createObjectURL(blob);
    $('.d-body', drawerEl).innerHTML = `<p style="margin:0 0 12px;color:var(--ink-2)">${t('share.artifactHint')}</p>
      <img src="${src}" alt="${esc(t('share.alt', { v: type.n }))}" style="width:100%;border-radius:20px;box-shadow:var(--shadow)">`;
    $('.d-foot', drawerEl).innerHTML = `<button class="btn fill" data-qresult style="flex:1">${t('quiz.toResult')}</button>`;
    return;
  }
  const file = new File([blob], t('share.file'), { type: 'image/png' });
  try {
    if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], title: 'Pacsi by DarwinAI', text: t('share.text', { v: type.n, url: siteUrl() }) }); return; }
  } catch (e) { if (e.name === 'AbortError') return; }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = t('share.file');
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  toast(t('toast.imgSaved'));
}

/* ---------- Kedvencek ---------- */
function favView() {
  const ids = [...S.fav].filter(id => BY_ID.has(id));
  if (!ids.length) {
    const s = SPARES['kabala-pacsi'];
    return [`<div class="dempty"><div class="pic" style="background-image:url('${portrait(s.id)}');background-color:${s.bg}"></div><h3>${t('fav.empty.h')}</h3><p>${t('fav.empty.p')}</p></div>`, ''];
  }
  return [`<div class="favs">${ids.map((id, i) => { const b = BY_ID.get(id); const on = S.cmp.includes(id); return `<div class="favrow" style="--i:${i}">
      <button class="pic" data-open="${id}" style="${picStyle(b)}" aria-label="${esc(t('fav.open', { v: b.nev }))}"></button>
      <div><h4>${esc(b.nev)}</h4><p>${esc(b.tagline)}</p></div>
      <button class="icbtn" data-tcmp="${id}" title="${esc(t(on ? 'fav.cmpOff' : 'fav.cmpOn'))}" style="${on ? 'color:var(--teal)' : ''}">${ic('compare')}</button>
      <button class="icbtn" data-unfav="${id}" title="${esc(t('fav.remove'))}" style="color:var(--primary-fill)">${ic('heart-f')}</button></div>`; }).join('')}</div>`,
  `<button class="btn fill" data-favshare style="flex:1">${ic('share')}${t('fav.share')}</button>`];
}
async function shareFavs() {
  const names = [...S.fav].map(id => BY_ID.get(id)?.nev).filter(Boolean);
  stat('megosztas', { mit: 'kedvencek', db: names.length });
  const text = t('fav.text', { v: names.join(', ') });
  const url = siteUrl();
  if (!ARTIFACT) try { if (navigator.share && location.protocol.startsWith('http')) { await navigator.share({ title: 'Pacsi by DarwinAI', text, url }); return; } } catch (e) { if (e.name === 'AbortError') return; }
  try { await navigator.clipboard.writeText(url ? `${text}\n${url}` : text); toast(t('toast.copiedList')); } catch (e) { toast(esc(text)); }
}

/* ---------- Összehasonlítás (radar + táblázat) ---------- */
const RADAR = [['E', ''], ['Gy', ''], ['I', ''], ['U', '', 1], ['H', '', 1], ['A', '', 1]];   // [mutató, felirat (labels), fordított skála?]
labels(() => RADAR.forEach(r => { r[1] = t(`radar.${r[0]}`); }));
const CMP_C = ['#FF6B3D', '#17756E', '#8A63D2'];
/* Kivétel az összevetésből (a fiók alján) – mindig a benne lévő összes fajtára, akkor is, ha már csak egy maradt.
   A gombon portré a fajta színével és a teljes név: az első szó („Rövidszőrű”, „Törpe”) nem volt egyértelmű,
   és jellemzőnek tűnt. */
const cmpOut = list => `<div class="cmp-xs" data-n="${list.length}">${list.map((b, j) =>
  `<button class="cmp-x" data-tcmp="${b.id}" style="${picStyle(b)};--cc:${CMP_C[j]}" aria-label="${esc(t('cmp.remove', { v: b.nev }))}"><i class="pic"><b class="x">${ic('x')}</b></i><span>${esc(b.nev)}</span></button>`).join('')}</div>`;
function cmpView() {
  const list = S.cmp.map(id => BY_ID.get(id)).filter(Boolean);
  if (list.length < 2) {
    const s = SPARES['kerdo-kutya'];
    return [`<div class="dempty"><div class="pic" style="background-image:url('${portrait(s.id)}');background-color:${s.bg}"></div><h3>${t('cmp.empty.h')}</h3>
      <p>${t('cmp.empty.p')}${list.length ? t('cmp.empty.sofar', { v: esc(list[0].nev) }) : ''}</p></div>`, list.length ? cmpOut(list) : ''];
  }
  const cx = 190, cy = 170, R = 118, n = RADAR.length;
  const pt = (i, v) => { const a = -Math.PI / 2 + i / n * Math.PI * 2; return [cx + Math.cos(a) * R * v, cy + Math.sin(a) * R * v]; };
  const web = [1, 2, 3, 4, 5].map(l => `<polygon class="web" points="${RADAR.map((_, i) => pt(i, l / 5).join(',')).join(' ')}"/>`).join('');
  const spokes = RADAR.map((_, i) => `<line class="spoke" x1="${cx}" y1="${cy}" x2="${pt(i, 1)[0]}" y2="${pt(i, 1)[1]}"/>`).join('');
  const labels = RADAR.map(([, l], i) => { const [x, y] = pt(i, 1.2); return `<text class="lab" x="${x}" y="${y + 4}" text-anchor="middle">${l}</text>`; }).join('');
  const polys = list.map((b, j) => `<polygon class="poly" style="fill:${CMP_C[j]};stroke:${CMP_C[j]};animation-delay:${j * 150}ms" points="${RADAR.map(([k, , inv], i) => pt(i, (inv ? 6 - b.t[k] : b.t[k]) / 5).join(',')).join(' ')}"/>`).join('');
  const rows = [
    [t('cmp.row.size'), b => b.meret.map(v => SIZE_L[v]).join('–')],
    [t('cmp.row.weight'), b => t('unit.kg', { v: range(b.suly) })],
    [t('cmp.row.height'), b => b.marmagassag ? t('unit.cm', { v: range(b.marmagassag) }) : '–'],
    [t('cmp.row.life'), b => t('unit.years', { v: range(b.elet) }), b => b.elet[1]],
    [t('cmp.row.coat'), b => b.szor.map(v => COAT_L[v]).join(' / ')],
    [t('cmp.row.kids'), b => b.t.Gy + '/5', b => b.t.Gy],
    [t('cmp.row.flat'), b => b.t.L + '/5', b => b.t.L],
    [t('cmp.row.novice'), b => b.t.K + '/5', b => b.t.K],
    [t('cmp.row.cost'), b => COST[b.koltseg || 2].split(' ')[0], b => -(b.koltseg || 2)],
    [t('cmp.row.origin'), b => b.orszag],
  ];
  const table = `<table class="ctable"><tbody>${rows.map(([l, f, score]) => {
    const best = score ? Math.max(...list.map(score)) : null;
    return `<tr><th>${l}</th>${list.map(b => `<td class="${score && score(b) === best && list.some(x => score(x) !== best) ? 'best' : ''}">${esc(f(b))}</td>`).join('')}</tr>`;
  }).join('')}</tbody></table>`;
  return [`<div class="cmp-heads">${list.map((b, j) => `<button class="cmp-h" data-open="${b.id}" style="${picStyle(b)};--cc:${CMP_C[j]};border:0;background:none;padding:0"><i class="pic"></i>${esc(b.nev)}</button>`).join('')}</div>
    <svg class="radar" viewBox="0 0 380 340">${web}${spokes}${polys}${labels}</svg>${table}`, cmpOut(list)];
}

/* ---------- Tippek / Gazdi-tudástár + beállítások ---------- */
function tipsView() {
  const dark = isDark(), host = SITE.url.replace(/^https?:\/\//, '');
  const card = k => `<div class="tipcard"><h4>${t(`tips.${k}.h`)}</h4>${t(`tips.${k}.body`)}</div>`;
  const newsletter = LANG_BY[LANG].newsletter   // a hírlevél magyar nyelvű: csak a magyar felületen ajánljuk
    ? `<div class="tipcard"><h4>${t('tips.newsletter.h')}</h4><p>${t('tips.newsletter.body')}</p>
      <p style="margin-top:8px"><a href="${esc(SITE.url || 'https://pacsit.hu')}/hirlevel/?utm_source=app&utm_medium=tippek" target="_blank" rel="noopener">${t('tips.newsletter.link')}</a></p></div>` : '';
  return [`<div class="tips">
    ${['responsible', 'bred', 'checklist', 'puppytest', 'adopt', 'legal', 'flat', 'cost'].map(card).join('')}
    ${newsletter}
    <div class="tipcard"><h4>${t('set.title')}</h4>
      <div class="setrow">${t('set.theme')} <button class="tog" data-set="theme" aria-pressed="${dark}" style="width:auto;padding:0"><span class="sw"></span></button></div>
      <div class="setrow">${t('set.rm')} <button class="tog" data-set="rm" aria-pressed="${S.rmUser}" style="width:auto;padding:0"><span class="sw"></span></button></div>
      <div class="setrow">${t('set.stat')} <button class="tog" data-set="stat" aria-pressed="${!store.get('nostat', false)}" style="width:auto;padding:0"><span class="sw"></span></button></div>
      <div class="setrow">${t('set.mode', { v: t(modeOf() === 'strict' ? 'mode.strict' : 'mode.rank') })} <button class="link" data-set="mode">${t('set.switch')}</button></div>
      <div class="setrow">${t('set.coach')} <button class="link" data-set="coach">${t('set.start')}</button></div>
      <div class="setrow">${t('set.lang')} ${langPills()}</div></div>
    <div class="tipcard"><h4>${t('tips.about.h')}</h4><p>${t('tips.about.p1')}</p>
      <p style="margin-top:8px">${t('tips.about.p2', { host: esc(host) })}</p></div>
    <div class="tipcard credit-card"><span class="mark">D</span><div><h4 style="margin:0 0 2px">Pacsi by DarwinAI</h4><p>${t('tips.credit')}<br><a href="https://www.darwinai.hu" target="_blank" rel="noopener">www.darwinai.hu ↗</a></p><p class="ver">${t('tips.version', { v: `v${APP_VERSION} · build ${APP_BUILD}` })}</p></div></div>
  </div>`, ''];
}
function setting(k, el) {
  if (k === 'theme') { toggleTheme(); el.setAttribute('aria-pressed', S.theme === 'dark'); }
  else if (k === 'rm') { S.rmUser = !S.rmUser; store.set('rm', S.rmUser); document.documentElement.classList.toggle('rm', RM()); el.setAttribute('aria-pressed', S.rmUser); }
  else if (k === 'stat') { const off = !store.get('nostat', false); store.set('nostat', off); el.setAttribute('aria-pressed', !off); toast(t(off ? 'toast.statOff' : 'toast.statOn')); }
  else if (k === 'mode') { setMode(modeOf() === 'strict' ? 'rank' : 'strict'); renderDrawer(); }
  else if (k === 'coach') { closeDrawer(); preloadHero(); setTimeout(startOnboarding, 400); }
}

/* ---------- Kirepült fajták (mobil) ---------- */
function flownView() {
  const out = BREEDS.filter(b => !b.ok);
  if (!out.length) return [`<div class="dempty"><h3>${t('flown.none.h')}</h3><p>${t('flown.none.p')}</p></div>`, ''];
  return [`<p style="margin:0 0 12px;color:var(--ink-2)">${t('flown.intro')}</p>
    <div class="favs">${out.slice(0, 80).map((b, i) => { const why = reasons(b).find(r => r.cls !== 'y'); return `<div class="favrow" style="--i:${Math.min(i, 20)};grid-template-columns:58px 1fr">
      <button class="pic" data-open="${b.id}" style="${picStyle(b)}" aria-label="${esc(b.nev)}"></button>
      <div><h4>${esc(b.nev)}</h4><p style="color:#D9483B">✗ ${esc(why ? why.text : '')}</p></div></div>`; }).join('')}</div>`,
  `<button class="btn fill" data-clearall style="flex:1">${t('flown.all')}</button>`];
}

/* Fülsáv (mobil) és felső gombok (desktop) */
$('#tabbar').addEventListener('click', e => {
  const b = e.target.closest('[data-tab]');
  if (!b) return;
  const t = b.dataset.tab;
  if (t === 'felfedez') { closeDrawer(); closePanelSheet(); if (!cardEl.hidden) closeCard(); return; }
  S.drawer === t ? closeDrawer() : openDrawer(t);
});
$$('[data-drawer]').forEach(b => b.addEventListener('click', () => { const t = b.dataset.drawer; S.drawer === t ? closeDrawer() : openDrawer(t); }));
