/* ==========================================================================
   Első látogatás: nyitó ablak („big picture”), utána 3 lépéses bemutató
   ========================================================================== */
const HERO = toBlobURL(window.PACSI_HERO) || 'img/nyito-pacsi.webp';
window.PACSI_HERO = null;
const welcomeEl = $('#welcome'), coachEl = $('#coach'), spotEl = $('#coachSpot');
const WL = { open: false, busy: false };
// a nyitókép előre dekódolva: az ablak beugrásakor már ott legyen (ne üres kör pattanjon be)
function preloadHero() { const im = new Image(); im.src = HERO; if (im.decode) im.decode().catch(() => {}); }

/* ---------- Nyitó ablak ---------- */
// A kép körül lebegő kis buborékok: valódi fajták a sprite-ból (x, y és méret a kép %-ában)
const WL_BUBBLES = [
  ['magyar-vizsla', -9, 4, 18], ['golden-retriever', 83, -9, 15], ['francia-bulldog', 101, 30, 19],
  ['puli', 91, 79, 14], ['border-collie', -14, 31, 12], ['beagle', 37, 97, 13], ['szamojed', 64, 101, 10],
];
// a nyitó ablak szövege külön, hogy nyelvváltáskor a kép és a körülötte lebegő buborékok megmaradjanak (lásd renderWelcomeText)
function welcomeTextHTML() {
  const swash = '<svg class="wl-swash" viewBox="0 0 300 20" preserveAspectRatio="none" aria-hidden="true"><path d="M5 14C70 6 170 3 295 9"/></svg>';
  // a főcím három része (a középső kiemelt); üres rész kimarad
  const h1 = [[t('welcome.h1a'), 0], [t('welcome.h1b'), 1, true], [t('welcome.h1c'), 2]].filter(x => x[0])
    .map(([txt, i, em]) => `<span style="--i:${i}">${em ? `<em>${txt}${swash}</em>` : txt}</span>`).join(' ');
  return `<p class="wl-eyebrow">${ic('paw')}${t('welcome.eyebrow', { n: TOTAL })}</p>
      <h1 id="wlTitle">${h1}</h1>
      <p class="wl-lead">${t('welcome.lead')}</p>
      <p class="wl-body" id="wlDesc">${t('welcome.body')}</p>
      <div class="wl-cta"><button class="cta wl-go" data-go>${t('welcome.go')}${ic('paw')}</button><small>${ic('sparkle')}${t('welcome.next')}</small></div>`;
}
function welcomeHTML() {
  const bubbles = WL_BUBBLES.map(([id, x, y, w], i) => {
    const b = BY_ID.get(id);
    return b ? `<i class="wl-b" style="${picStyle(b)};--x:${x}%;--y:${y}%;--w:${w}%;--i:${i}"></i>` : '';
  }).join('');
  return `<div class="wl-scrim"></div>
  <section class="wl" role="dialog" aria-modal="true" aria-labelledby="wlTitle" aria-describedby="wlDesc">
    <div class="wl-lang">${langPills()}</div>
    <div class="wl-art" aria-hidden="true">
      <i class="wl-glow"></i>
      <div class="wl-hero" style="background-image:url('${HERO}')"></div>
      <svg class="wl-ring" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48.6"/></svg>
      ${bubbles}
      <span class="wl-match">${ic('heart-f')}${t('welcome.match')}</span>
    </div>
    <div class="wl-text">${welcomeTextHTML()}</div>
  </section>`;
}
function bindWelcome() {
  const go = $('[data-go]', welcomeEl);
  go.addEventListener('click', closeWelcome);
  return go;
}
// nyelvváltás a nyitó ablakban: csak a szöveg és a váltó rajzolódik újra
function renderWelcomeText() {
  $('.wl-text', welcomeEl).innerHTML = welcomeTextHTML();
  $('.wl-match', welcomeEl).innerHTML = `${ic('heart-f')}${t('welcome.match')}`;
  $('.wl-lang', welcomeEl).innerHTML = langPills();
  bindWelcome();
}
function openWelcome(then) {
  if (WL.open) return;
  WL.open = true; WL.then = then;
  stat('bemutato', { lepes: 'nyitó ablak' });
  welcomeEl.innerHTML = welcomeHTML();
  welcomeEl.classList.remove('out');
  welcomeEl.hidden = false;
  $('#app').inert = true;
  const go = bindWelcome();
  $('.wl-scrim', welcomeEl).addEventListener('click', () => {   // mellékattintásra a gomb jelez: innen indulunk
    go.classList.remove('nudge'); void go.offsetWidth; go.classList.add('nudge');
  });
  setTimeout(() => WL.open && go.focus({ preventScroll: true }), 120);
  // „pacsi!”: amikor a kéz és a mancs összeér (és a gyűrű körbeért), szívecskék pattannak ki
  setTimeout(() => {
    if (!WL.open || RM()) return;
    const q = $('.wl-hero', welcomeEl).getBoundingClientRect(), x = q.left + q.width * .31, y = q.top + q.height * .29;
    spark(x, y, 9, { heart: true, size: 6, speed: 4.5, g: .05, up: 1.4, color: '#FF6B3D' });
    spark(x, y, 7, { heart: true, size: 5, speed: 4, g: .05, up: 1.2, color: '#FF8FA3' });
  }, 1500);
}
function closeWelcome() {
  if (!WL.open || WL.busy) return;
  WL.busy = true;
  stat('bemutato', { lepes: 'Kezdjük' });
  const go = $('[data-go]', welcomeEl), q = go.getBoundingClientRect();
  spark(q.left + q.width / 2, q.top + q.height / 2, 26, { speed: 6, g: .1 });
  haptic(12);
  welcomeEl.classList.add('out');
  $('#app').inert = false;
  setTimeout(() => {
    welcomeEl.hidden = true; welcomeEl.innerHTML = '';
    WL.open = WL.busy = false;
    store.set('welcome', 1);
    const then = WL.then; WL.then = null;
    then && then();
  }, RM() ? 60 : 380);
}
welcomeEl.addEventListener('keydown', e => {
  if (e.key !== 'Tab') return;   // a fókus az ablakon belül marad: a „Kezdjük!” és a nyelvváltó gombjai között körbejár
  e.preventDefault();
  const f = $$('button', welcomeEl), i = f.indexOf(document.activeElement);
  f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
});

/* Teljes bevezetés: nyitó ablak → bemutató (első látogatáskor és a Tippek → „Bemutató újra” gombbal) */
function startOnboarding() {
  if (CO) endCoach(false);
  openWelcome(() => setTimeout(() => coach(0), 260));
}

/* ---------- Bemutató (coach mark) ----------
   Reflektorfény: a lépés célpontja kivilágítva, a többi elsötétül (a kattintás átmegy rajta), a célpont
   körül lüktető gyűrű; a buborékban a Pacsi kabala „mondja” a tippet. Ha a lépés kérését a látogató
   megteszi (buborékot nyit, szűrőt kapcsol, kvízt indít), a bemutató magától továbblép. */
const COACH = [
  { t: () => stage, pad: -8, r: 30, h: 'coach.1.h',
    p: () => t(S.mobile ? 'coach.1.p.mobile' : 'coach.1.p.desktop', { n: TOTAL }),
    did: () => !!S.card },
  { t: () => S.mobile ? $('#dock') : $('#panel'), pad: 6, r: S.mobile ? 30 : 34, h: 'coach.2.h',
    p: () => modeOf() === 'rank' ? t('coach.2.p.rank') : t(S.mobile ? 'coach.2.p.mobile' : 'coach.2.p.desktop'),
    did: () => filterSig() !== CO.sig },
  { t: () => S.mobile ? $('[data-tab="kviz"]') : $('#quizBtn'), pad: 6, r: S.mobile ? 20 : 40, h: 'coach.3.h',
    p: () => t('coach.3.p'),
    did: () => S.drawer === 'kviz' },
];
const filterSig = () => S.crit.map(c => c.label).join('|');
let CO = null;   // { i, sig, done, hold, iv, adv, rect }
const coachBlocked = () => WL.open || !cardEl.hidden || !!S.drawer || $('#panel').classList.contains('open') || !$('#mobSearch').hidden;

function coach(i = 0) {
  if (i >= COACH.length) return endCoach(true, 'vége');
  if (!CO) CO = { iv: setInterval(coachWatch, 200) };
  clearTimeout(CO.adv);
  Object.assign(CO, { i, sig: filterSig(), done: false, adv: 0, rect: '' });
  if (CO.statI !== i) { CO.statI = i; stat('bemutato', { lepes: `tipp ${i + 1}` }); }   // újramegjelenítéskor nem számol újra
  if (coachBlocked()) { CO.hold = true; hideCoach(); return; }
  CO.hold = false;
  showCoach(i);
}
function showCoach(i) {
  const c = COACH[i];
  coachEl.innerHTML = `<i class="co-pic" style="background-image:url('${portrait('kabala-pacsi')}')" aria-hidden="true"></i>
    <span class="co-step">${t('coach.step', { i: i + 1, n: COACH.length })}</span><h4>${t(c.h)}</h4><p>${c.p()}</p>
    <div class="row"><span class="dots3">${COACH.map((_, j) => `<i class="${j === i ? 'on' : j < i ? 'was' : ''}"></i>`).join('')}</span>
    <span><button class="link" data-skip>${t('coach.skip')}</button> <button class="btn fill" data-next>${i === COACH.length - 1 ? t('welcome.go') : t('coach.next')}</button></span></div>`;
  coachEl.hidden = false;
  coachEl.style.animation = 'none'; void coachEl.offsetWidth; coachEl.style.animation = '';   // minden lépés újra „beugrik”
  $('[data-next]', coachEl).onclick = () => coach(i + 1);
  $('[data-skip]', coachEl).onclick = () => endCoach();
  const first = spotEl.hidden || !spotEl.classList.contains('on');
  if (first) spotEl.style.transition = 'none';
  spotEl.hidden = false;
  placeCoach(i);
  if (first) { void spotEl.offsetWidth; spotEl.style.transition = ''; }
  spotEl.classList.add('on');
  haptic(10);
}
function placeCoach(i) {
  const c = COACH[i], q = c.t().getBoundingClientRect();
  CO.rect = `${q.left},${q.top},${q.width},${q.height}`;
  // reflektor: a célpont (+ margó), a képernyőn belül tartva, hogy a gyűrű mindig látsszon
  const sx = clamp(q.left - c.pad, 5, innerWidth - 5), sy = clamp(q.top - c.pad, 5, innerHeight - 5);
  const sw = clamp(q.right + c.pad, 5, innerWidth - 5) - sx, sh = clamp(q.bottom + c.pad, 5, innerHeight - 5) - sy;
  const r = Math.min(c.r, sw / 2, sh / 2);
  Object.assign(spotEl.style, { left: sx + 'px', top: sy + 'px', width: sw + 'px', height: sh + 'px', borderRadius: r + 'px' });
  spotEl.style.setProperty('--sx', ((sw + 26) / sw).toFixed(4));   // a lüktetés mindkét irányban ~13 px-t tágul
  spotEl.style.setProperty('--sy', ((sh + 26) / sh).toFixed(4));
  // a tippbuborék: asztalon a célpont mellett/alatt, mobilon a célpont fölött
  const box = coachEl, w = box.offsetWidth, h = box.offsetHeight;
  box.classList.remove('up', 'left');
  let x, y;
  if (i === 0) { x = q.left + q.width / 2 - w / 2; y = q.top + q.height * (S.mobile ? .5 : .56); box.style.setProperty('--ax', w / 2 - 10 + 'px'); }
  else if (!S.mobile) {
    x = sx + sw + 22;
    y = i === 1 ? q.top + 62 : q.top + q.height / 2 - h / 2;
    box.classList.add('left');
    box.style.setProperty('--ay', (i === 1 ? 64 : h / 2 - 10) + 'px');
  } else {
    x = 16; y = sy - h - 18;
    box.classList.add('up');
    box.style.setProperty('--ax', clamp(q.left + q.width / 2 - 16 - 10, 22, w - 34) + 'px');
  }
  box.style.left = clamp(x, 12, innerWidth - w - 12) + 'px';
  box.style.top = clamp(y, 12, innerHeight - h - 12) + 'px';
}
function hideCoach() {
  coachEl.hidden = true;
  spotEl.classList.remove('on');
  spotEl.hidden = true;
}
function coachWatch() {
  if (!CO) return;
  const c = COACH[CO.i];
  if (!CO.done && c.did()) CO.done = true;
  const bl = coachBlocked();
  if (bl) { if (!CO.hold) { CO.hold = true; hideCoach(); } return; }
  if (CO.hold) {                       // bezárult a kártya/lap/fiók: jöhet a következő (vagy ugyanez a) lépés
    CO.hold = false;
    return coach(CO.done ? CO.i + 1 : CO.i);
  }
  if (CO.done && !CO.adv) CO.adv = setTimeout(() => CO && coach(CO.i + 1), 1500);   // hadd lássa a hatást
  const q = c.t().getBoundingClientRect();
  if (`${q.left},${q.top},${q.width},${q.height}` !== CO.rect) placeCoach(CO.i);   // átméretezés, elforgatás
}
function endCoach(save = true, how = 'kihagyva') {
  if (!CO) return;
  clearInterval(CO.iv); clearTimeout(CO.adv);
  if (save) stat('bemutato', { lepes: how === 'vége' ? 'vége' : `kihagyva (tipp ${CO.i + 1})` });
  CO = null;
  coachEl.hidden = true;
  spotEl.classList.remove('on');
  setTimeout(() => { if (!CO) spotEl.hidden = true; }, 380);
  if (save) store.set('coach', 1);
}
