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
function welcomeHTML() {
  const bubbles = WL_BUBBLES.map(([id, x, y, w], i) => {
    const b = BY_ID.get(id);
    return b ? `<i class="wl-b" style="${picStyle(b)};--x:${x}%;--y:${y}%;--w:${w}%;--i:${i}"></i>` : '';
  }).join('');
  return `<div class="wl-scrim"></div>
  <section class="wl" role="dialog" aria-modal="true" aria-labelledby="wlTitle" aria-describedby="wlDesc">
    <div class="wl-art" aria-hidden="true">
      <i class="wl-glow"></i>
      <div class="wl-hero" style="background-image:url('${HERO}')"></div>
      <svg class="wl-ring" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48.6"/></svg>
      ${bubbles}
      <span class="wl-match">${ic('heart-f')}<b>100%</b> illik hozzád</span>
    </div>
    <div class="wl-text">
      <p class="wl-eyebrow">${ic('paw')}${TOTAL} kutyafajta · egy élő felhőben</p>
      <h1 id="wlTitle"><span style="--i:0">Válaszd ki a</span> <span style="--i:1"><em>neked való<svg class="wl-swash" viewBox="0 0 300 20" preserveAspectRatio="none" aria-hidden="true"><path d="M5 14C70 6 170 3 295 9"/></svg></em></span> <span style="--i:2">kutyafajtát,</span></h1>
      <p class="wl-lead">hogy mindketten azt kapjátok, amire vágytok.</p>
      <p class="wl-body" id="wlDesc">Állítsd be a szűrőket, és nézd meg, melyik fajta illik hozzád.</p>
      <div class="wl-cta"><button class="cta wl-go" data-go>Kezdjük!${ic('paw')}</button><small>${ic('sparkle')}Utána 3 gyors tipp következik</small></div>
    </div>
  </section>`;
}
function openWelcome(then) {
  if (WL.open) return;
  WL.open = true; WL.then = then;
  welcomeEl.innerHTML = welcomeHTML();
  welcomeEl.classList.remove('out');
  welcomeEl.hidden = false;
  $('#app').inert = true;
  const go = $('[data-go]', welcomeEl);
  go.addEventListener('click', closeWelcome);
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
  if (e.key === 'Tab') { e.preventDefault(); $('[data-go]', welcomeEl).focus(); }   // egyetlen gomb: a fókusz itt marad
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
  { t: () => stage, pad: -8, r: 30, h: 'Ez itt a fajtafelhő',
    p: () => `${TOTAL} kutyafajta, mind egy helyen. ${S.mobile ? 'Koppints' : 'Vidd az egeret'} egy buborékra, és megtudod, ki az.`,
    did: () => !!S.card },
  { t: () => S.mobile ? $('#dock') : $('#panel'), pad: 6, r: S.mobile ? 30 : 34, h: 'Szűrj, és figyeld!',
    p: () => modeOf() === 'rank' ? 'Kapcsolj be egy szűrőt, és nézd, ki ugrik előre!'
      : S.mobile ? 'Kapcsolj be egy szűrőt: ami nem illik hozzád, kirepül.' : 'Kapcsolj be egy szűrőt: ami nem illik hozzád, eltűnik, a többi megnő.',
    did: () => filterSig() !== CO.sig },
  { t: () => S.mobile ? $('[data-tab="kviz"]') : $('#quizBtn'), pad: 6, r: S.mobile ? 20 : 40, h: 'Nem tudod, hol kezdd?',
    p: () => 'A Párkereső kvíz 10 kérdés, kb. 1 perc – és élőben formálja a felhőt.',
    did: () => S.drawer === 'kviz' },
];
const filterSig = () => S.crit.map(c => c.label).join('|');
let CO = null;   // { i, sig, done, hold, iv, adv, rect }
const coachBlocked = () => WL.open || !cardEl.hidden || !!S.drawer || $('#panel').classList.contains('open') || !$('#mobSearch').hidden;

function coach(i = 0) {
  if (i >= COACH.length) return endCoach();
  if (!CO) CO = { iv: setInterval(coachWatch, 200) };
  clearTimeout(CO.adv);
  Object.assign(CO, { i, sig: filterSig(), done: false, adv: 0, rect: '' });
  if (coachBlocked()) { CO.hold = true; hideCoach(); return; }
  CO.hold = false;
  showCoach(i);
}
function showCoach(i) {
  const c = COACH[i];
  coachEl.innerHTML = `<i class="co-pic" style="background-image:url('${portrait('kabala-pacsi')}')" aria-hidden="true"></i>
    <span class="co-step">Tipp ${i + 1}/${COACH.length}</span><h4>${c.h}</h4><p>${c.p()}</p>
    <div class="row"><span class="dots3">${COACH.map((_, j) => `<i class="${j === i ? 'on' : j < i ? 'was' : ''}"></i>`).join('')}</span>
    <span><button class="link" data-skip>Kihagyom</button> <button class="btn fill" data-next>${i === COACH.length - 1 ? 'Kezdjük!' : 'Tovább'}</button></span></div>`;
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
function endCoach(save = true) {
  if (!CO) return;
  clearInterval(CO.iv); clearTimeout(CO.adv);
  CO = null;
  coachEl.hidden = true;
  spotEl.classList.remove('on');
  setTimeout(() => { if (!CO) spotEl.hidden = true; }, 380);
  if (save) store.set('coach', 1);
}
