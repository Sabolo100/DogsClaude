/* ==========================================================================
   Fajtakártya: morph a buborékból, lapozás, kedvenc, összehasonlítás
   ========================================================================== */
const cardEl = $('#card'), scrimEl = $('#scrim');
const STATS = [['E', 'Energia', 'bolt'], ['Gy', 'Gyerekbarát', 'kid'], ['I', 'Idomíthatóság', 'cap'], ['U', 'Ugatás', 'quiet'], ['H', 'Szőrhullás', 'feather'], ['A', 'Ápolásigény', 'comb'], ['L', 'Lakásba való', 'home'], ['O', 'Őrzőösztön', 'shield']];
const COST = ['', '€ – alacsony', '€€ – közepes', '€€€ – magas'];
let cardOrder = [], cardBusy = false;

function orderList() {
  const vis = B.filter(o => o.vis || S.view === 'lista').map(o => o.b);
  const active = S.crit.length > 0;
  return vis.sort((a, b) => active ? (b.m - a.m) || COLL.compare(a.nev, b.nev) : COLL.compare(a.nev, b.nev)).map(b => b.id);
}
const dots = (v, d0 = 0) => `<span class="dots" aria-label="${v} az 5-ből">${[1, 2, 3, 4, 5].map(i => `<i class="${i <= v ? 'on' : ''}" style="--d:${d0 + i * 45}ms"></i>`).join('')}</span>`;

function cardHTML(b) {
  const active = S.crit.length > 0;
  const pct = active ? Math.round(b.m * 100) : null;
  const size = b.meret.map(v => SIZE_L[v]).join('–');
  const rs = active ? reasons(b) : [];
  const warns = [];
  if (b.brachy) warns.push(`<span class="ichip warn">${ic('warn')}Lapos orrú – légzési kockázat</span>`);
  if (b.korl) warns.push(`<span class="ichip warn">${ic('warn')}Egyes országokban engedélyköteles</span>`);
  if (b.vonyit) warns.push(`<span class="ichip">${ic('quiet')}Ritkán ugat, de vonyít</span>`);
  const fav = S.fav.has(b.id), cmp = S.cmp.includes(b.id);
  let i = 0;
  const rv = () => `rv" style="--i:${i++}`;
  return `
  <div class="handle" aria-hidden="true"></div>
  <button class="close" data-act="close" aria-label="Bezárás">${ic('x')}</button>
  <div class="card-scroll">
    <div class="c-head">
      <div class="c-pic" id="cPic" style="--bgc:${b.bg};background-image:url('${portrait(b.id)}')"></div>
      <div class="c-title">
        <h2 id="cardTitle" class="${rv()}">${esc(b.nev)}</h2>
        <div class="c-sub ${rv()}">${esc(b.en)} · FCI ${b.fci}. csoport · ${b.hu ? ic('flag') : ''}${esc(b.orszag)}</div>
        <p class="c-tag ${rv()}">${esc(b.tagline)}</p>
        ${active ? `<div class="c-match ${rv()}"><div class="mring"><svg viewBox="0 0 80 80"><circle class="bgc" cx="40" cy="40" r="34"/><circle class="fg" cx="40" cy="40" r="34" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100" data-pct="${pct}"/></svg><b data-count="${pct}">0%</b></div><small>${b.ok ? 'Minden szempontodnak megfelel' : 'ennyire illik<br>a szempontjaidhoz'}</small></div>` : ''}
      </div>
    </div>
    <div class="c-chips ${rv()}">
      <span class="ichip">${ic('ruler')}${size}</span>
      <span class="ichip">⚖︎ ${range(b.suly)} kg</span>
      ${b.marmagassag ? `<span class="ichip">↕ ${range(b.marmagassag)} cm</span>` : ''}
      <span class="ichip">${ic('pulse')}${range(b.elet)} év</span>
      <span class="ichip">${ic('coat')}${b.szor.map(v => COAT_L[v]).join(' / ')}</span>
      ${warns.join('')}
    </div>
    <div class="c-grid">
      <div class="stats ${rv()}">${STATS.map(([k, l, icn], j) => `<div class="stat">${ic(icn)}<span>${l}</span>${dots(b.t[k], j * 60)}</div>`).join('')}</div>
      <div class="why ${rv()}"><h4>${active ? 'Miért illik hozzád?' : 'Röviden'}</h4>
        ${active ? `<ul>${rs.slice(0, 6).map(r => `<li class="${r.cls}">${ic(r.cls === 'y' ? 'check' : r.cls === 'h' ? 'warn' : 'x')}${esc(r.text)}</li>`).join('')}</ul>`
          : `<ul>${(b.kinekIgen || []).map(t => `<li class="y">${ic('check')}${esc(t)}</li>`).join('')}</ul>`}
        ${b.mozgas ? `<p class="c-note" style="font-size:13px;margin-top:10px">${ic('bolt')} <b>Mozgás:</b> ${esc(b.mozgas)}</p>` : ''}
      </div>
    </div>
    <div class="c-actions ${rv()}">
      <button class="btn fill ${fav ? 'on' : ''}" data-act="fav">${ic(fav ? 'heart-f' : 'heart')}<span>${fav ? 'Kedvenc' : 'Kedvencekhez'}</span></button>
      <button class="btn ${cmp ? 'on' : ''}" data-act="cmp">${ic('compare')}<span>${cmp ? 'Összevetésben' : 'Összehasonlít'}</span></button>
      <button class="btn round" data-act="share" aria-label="Megosztás">${ic('share')}</button>
    </div>
    ${b.leiras ? `<p class="c-desc ${rv()}">${esc(b.leiras)}</p>` : ''}
    <div class="c-cols ${rv()}">
      ${b.kinekIgen ? `<div class="c-sec"><h4>Kinek ajánlott?</h4><ul>${b.kinekIgen.map(t => `<li>${esc(t)}</li>`).join('')}</ul></div>` : ''}
      ${b.kinekNem ? `<div class="c-sec no"><h4>Kinek nem?</h4><ul>${b.kinekNem.map(t => `<li>${esc(t)}</li>`).join('')}</ul></div>` : ''}
      ${b.egeszseg ? `<div class="c-sec"><h4>Egészség – figyelj rá</h4><ul>${b.egeszseg.map(t => `<li>${esc(t)}</li>`).join('')}</ul></div>` : ''}
      ${b.koltseg ? `<div class="c-sec"><h4>Fenntartás</h4><ul><li>${COST[b.koltseg]} havi költség</li><li>Ápolásigény: ${['', 'minimális', 'kevés', 'közepes', 'jelentős', 'nagy'][b.t.A]}</li></ul></div>` : ''}
    </div>
    ${b.erdekesseg ? `<div class="c-fun ${rv()}"><b>Tudtad?</b> ${esc(b.erdekesseg)}</div>` : ''}
    ${b.hasonlo && b.hasonlo.length ? `<div class="${rv()}"><h4 style="font:700 18px var(--font-d);margin:6px 0 10px">Hasonló fajták</h4><div class="c-sim">${b.hasonlo.map(id => { const s = BY_ID.get(id); return s ? `<button class="sim" data-sim="${id}"><i style="${picStyle(s)}"></i>${esc(s.nev)}</button>` : ''; }).join('')}</div></div>` : ''}
    <p class="c-note">A jellemzők a fajtára jellemző átlagot mutatják – az egyedi kutya ettől eltérhet. Nem helyettesíti az állatorvosi vagy tenyésztői tanácsot.</p>
  </div>`;
}

function animateCardIn() {
  const ring = $('.mring .fg', cardEl), cnt = $('.mring b', cardEl);
  if (ring) requestAnimationFrame(() => { ring.style.strokeDashoffset = 100 - ring.dataset.pct; });
  if (cnt) {
    const target = +cnt.dataset.count, t0 = now() + 250;
    const tick = t => { const p = clamp((t - t0) / 1000, 0, 1), e = 1 - Math.pow(1 - p, 3); cnt.textContent = Math.round(target * e) + '%'; if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  }
}

function openCard(id, { push = true, dir = 0 } = {}) {
  const b = BY_ID.get(id);
  if (!b) return;
  setHover(null);
  const already = !cardEl.hidden;
  S.card = id;
  cardOrder = orderList();
  if (!cardOrder.includes(id)) cardOrder.unshift(id);
  cardEl.innerHTML = cardHTML(b);
  cardEl.style.setProperty('--bgc', b.bg);
  if (already) {
    cardEl.classList.remove('swap', 'left');
    void cardEl.offsetWidth;
    cardEl.classList.add('swap');
    if (dir < 0) cardEl.classList.add('left');
    animateCardIn();
  } else {
    scrimEl.hidden = false; scrimEl.classList.remove('out');
    cardEl.hidden = false;
    $('#cardPrev').hidden = $('#cardNext').hidden = S.mobile;
    morphIn(OB_ID.get(id));
    animateCardIn();
    lastFocus = document.activeElement;
    setTimeout(() => { const c = $('.close', cardEl); c && c.focus({ preventScroll: true }); }, 60);
  }
  if (push && !already) syncHash(true); else syncHash();
}
let lastFocus = null;

/* Buborék → kártya: FLIP a portrén + kör alakú kinyílás */
function morphIn(o) {
  cardEl.style.clipPath = '';
  cardEl.style.transition = '';
  if (RM() || !o || o.st === 'gone' || S.view === 'lista') {
    const base = S.mobile ? '' : 'translate(-50%,-50%) ';
    cardEl.animate([{ opacity: 0, transform: base + 'translateY(40px)' }, { opacity: 1, transform: base || 'none' }], { duration: 320, easing: 'cubic-bezier(.22,1,.36,1)' });
    return;
  }
  const cq = cardEl.getBoundingClientRect();
  const bx = SR.left + o.rx - cq.left, by = SR.top + o.ry - cq.top, br = o.r;
  const far = Math.hypot(Math.max(bx, cq.width - bx), Math.max(by, cq.height - by));
  cardEl.animate([{ clipPath: `circle(${br}px at ${bx}px ${by}px)` }, { clipPath: `circle(${far}px at ${bx}px ${by}px)` }],
    { duration: 560, easing: 'cubic-bezier(.3,.9,.25,1)' });
  const pic = $('#cPic', cardEl), pq = pic.getBoundingClientRect();
  const s = (br * 2) / pq.width;
  const dx = SR.left + o.rx - (pq.left + pq.width / 2), dy = SR.top + o.ry - (pq.top + pq.height / 2);
  pic.animate([{ transform: `translate(${dx}px,${dy}px) scale(${s})` }, { transform: 'none' }], { duration: 620, easing: 'cubic-bezier(.3,1.25,.4,1)' });
  o.el.style.visibility = 'hidden';
  setTimeout(() => { o.el.style.visibility = ''; }, 400);
}
function closeCard({ fromPop = false } = {}) {
  if (cardEl.hidden || cardBusy) return;
  cardBusy = true;
  const o = OB_ID.get(S.card);
  S.card = null;
  const done = () => {
    cardEl.hidden = true; scrimEl.hidden = true; cardBusy = false;
    $('#cardPrev').hidden = $('#cardNext').hidden = true;
    if (o && o.st === 'in' && !RM()) { o.r *= .7; o.jv = -5; }
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  };
  scrimEl.classList.add('out');
  if (RM() || !o || o.st === 'gone' || S.view === 'lista') {
    cardEl.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 200 }).onfinish = done;
  } else {
    const cq = cardEl.getBoundingClientRect();
    const bx = SR.left + o.rx - cq.left, by = SR.top + o.ry - cq.top;
    const far = Math.hypot(Math.max(bx, cq.width - bx), Math.max(by, cq.height - by));
    cardEl.animate([{ clipPath: `circle(${far}px at ${bx}px ${by}px)` }, { clipPath: `circle(${Math.max(o.r, 8)}px at ${bx}px ${by}px)`, opacity: .6 }],
      { duration: 380, easing: 'cubic-bezier(.55,0,.8,.4)' }).onfinish = done;
  }
  if (!fromPop) syncHash();
}
function navCard(d) {
  if (!S.card) return;
  const i = cardOrder.indexOf(S.card);
  const next = cardOrder[(i + d + cardOrder.length) % cardOrder.length];
  if (next) openCard(next, { push: false, dir: d });
}

cardEl.addEventListener('click', e => {
  const a = e.target.closest('[data-act]');
  const sim = e.target.closest('[data-sim]');
  if (sim) return openCard(sim.dataset.sim, { push: false, dir: 1 });
  if (!a) return;
  const id = S.card;
  if (a.dataset.act === 'close') closeCard();
  else if (a.dataset.act === 'fav') toggleFav(id, a);
  else if (a.dataset.act === 'cmp') toggleCmp(id, a);
  else if (a.dataset.act === 'share') shareBreed(id);
});
scrimEl.addEventListener('click', () => { if (!cardEl.hidden) closeCard(); else if (S.drawer) closeDrawer(); });
$('#cardPrev').addEventListener('click', () => navCard(-1));
$('#cardNext').addEventListener('click', () => navCard(1));

/* Mobil: lehúzás = bezárás, oldalra húzás = lapozás */
(() => {
  let x0 = null, y0 = 0, dx = 0, dy = 0, axis = null, scroller = null;
  cardEl.addEventListener('pointerdown', e => {
    if (!S.mobile || e.target.closest('button')) return;
    scroller = $('.card-scroll', cardEl);
    x0 = e.clientX; y0 = e.clientY; dx = dy = 0; axis = null;
  });
  cardEl.addEventListener('pointermove', e => {
    if (x0 == null) return;
    dx = e.clientX - x0; dy = e.clientY - y0;
    if (!axis && Math.hypot(dx, dy) > 12) axis = Math.abs(dx) > Math.abs(dy) * 1.3 ? 'x' : 'y';
    if (axis === 'y' && dy > 0 && scroller.scrollTop <= 0) { cardEl.style.transform = `translateY(${dy}px)`; }
    else if (axis === 'x') { $('.card-scroll', cardEl).style.transform = `translateX(${dx * .6}px)`; }
  });
  const end = () => {
    if (x0 == null) return;
    x0 = null;
    const sc = $('.card-scroll', cardEl);
    if (axis === 'y' && dy > 110 && scroller.scrollTop <= 0) { cardEl.style.transform = ''; closeCard(); }
    else if (axis === 'x' && Math.abs(dx) > 70) { sc.style.transform = ''; navCard(dx < 0 ? 1 : -1); }
    else {
      cardEl.animate([{ transform: cardEl.style.transform || 'none' }, { transform: 'none' }], { duration: 250, easing: 'ease-out' });
      cardEl.style.transform = ''; if (sc) sc.style.transform = '';
    }
  };
  cardEl.addEventListener('pointerup', end);
  cardEl.addEventListener('pointercancel', end);
})();

/* ---------- Kedvenc / összevetés ---------- */
function burstAt(el, heart) {
  if (!el) return;
  const q = el.getBoundingClientRect();
  spark(q.left + q.width / 2, q.top + q.height / 2, heart ? 12 : 8, { speed: 5, heart, color: heart ? undefined : '#17756E', g: .1 });
}
function toggleFav(id, srcEl) {
  const on = !S.fav.has(id);
  on ? S.fav.add(id) : S.fav.delete(id);
  store.set('fav', [...S.fav]);
  markFav();
  updateBadges(on ? 'fav' : null);
  if (on) { burstAt(srcEl, true); haptic([8, 30, 8]); }
  const b = BY_ID.get(id);
  if (S.card === id) {
    const btn = $('[data-act="fav"]', cardEl);
    if (btn) { btn.classList.toggle('on', on); btn.innerHTML = `${ic(on ? 'heart-f' : 'heart')}<span>${on ? 'Kedvenc' : 'Kedvencekhez'}</span>`; }
  } else toast(on ? `♥ ${esc(b.nev)} a kedvencek közé került` : `${esc(b.nev)} kikerült a kedvencek közül`);
  if (S.drawer === 'kedvencek') renderDrawer();
}
function toggleCmp(id, srcEl) {
  const i = S.cmp.indexOf(id);
  if (i >= 0) S.cmp.splice(i, 1);
  else {
    if (S.cmp.length >= 3) { toast('Egyszerre 3 fajtát hasonlíthatsz össze – vegyél ki egyet.'); return; }
    S.cmp.push(id);
    flyToTray(id, srcEl);
  }
  store.set('cmp', S.cmp);
  markFav();
  updateBadges(i < 0 ? 'cmp' : null);
  renderTray();
  if (S.card === id) {
    const btn = $('[data-act="cmp"]', cardEl), on = S.cmp.includes(id);
    if (btn) { btn.classList.toggle('on', on); btn.innerHTML = `${ic('compare')}<span>${on ? 'Összevetésben' : 'Összehasonlít'}</span>`; }
  }
  if (S.drawer === 'osszevet') renderDrawer();
}
function flyToTray(id, srcEl) {
  if (RM() || !srcEl) return;
  const target = S.mobile ? $('[data-tab="osszevet"]') : ($('#tray').hidden ? $('[data-drawer="osszevet"]') : $('#tray'));
  if (!target) return;
  const a = srcEl.getBoundingClientRect(), z = target.getBoundingClientRect();
  const el = document.createElement('i');
  el.className = 'flyclone';
  el.style.cssText = picStyle(BY_ID.get(id)) + `;left:${a.left + a.width / 2 - 28}px;top:${a.top + a.height / 2 - 28}px;width:56px;height:56px`;
  document.body.appendChild(el);
  const dx = z.left + z.width / 2 - (a.left + a.width / 2), dy = z.top + z.height / 2 - (a.top + a.height / 2);
  el.animate([
    { transform: 'translate(0,0) scale(1)' },
    { transform: `translate(${dx * .5}px,${dy * .5 - 120}px) scale(1.15)`, offset: .45 },
    { transform: `translate(${dx}px,${dy}px) scale(.4)`, opacity: .6 },
  ], { duration: 700, easing: 'cubic-bezier(.45,0,.3,1)' }).onfinish = () => {
    el.remove();
    const t = $('#tray');
    if (!t.hidden) { t.classList.remove('shake'); void t.offsetWidth; t.classList.add('shake'); }
  };
}

/* ---------- Megosztás ---------- */
async function shareBreed(id) {
  const b = BY_ID.get(id);
  const url = ARTIFACT ? '' : location.href.split('#')[0] + '#b=' + id;
  const text = `${b.nev} – ${b.tagline}`;
  if (ARTIFACT) {
    try { await navigator.clipboard.writeText(`${text} 🐾 (Pacsi by DarwinAI · www.darwinai.hu)`); toast('A fajta leírása a vágólapra került 📋'); }
    catch (e) { toast(esc(text)); }
    return;
  }
  try {
    if (navigator.share && location.protocol.startsWith('http')) { await navigator.share({ title: 'Pacsi by DarwinAI', text, url }); return; }
  } catch (e) { if (e.name === 'AbortError') return; }
  try { await navigator.clipboard.writeText(`${text}\n${url}`); toast('Link a vágólapra másolva 🔗'); }
  catch (e) { toast('A megosztás itt nem érhető el'); }
}
