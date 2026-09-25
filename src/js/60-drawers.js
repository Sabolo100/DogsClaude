/* ==========================================================================
   Fiókok: Párkereső kvíz, Kedvencek, Összehasonlítás, Tippek, Kirepültek
   ========================================================================== */
const drawerEl = $('#drawer');
let Q = { i: 0, answers: [] };
const TITLES = { kviz: 'Párkereső kvíz', kedvencek: 'Kedvenceim', osszevet: 'Összehasonlítás', tippek: 'Gazdi-tudástár', kirepultek: 'Kirepült fajták' };

function openDrawer(name) {
  if (S.drawer === name) return;
  closePanelSheet();
  if (!cardEl.hidden) closeCard();
  if (name === 'kviz' && !(S.quiz && !S.quiz.done)) Q = { i: 0, answers: [] };
  if (name === 'kviz' && S.quiz && S.quiz.done) Q = { i: QUIZ.length, answers: S.quiz.answers.slice() };
  S.drawer = name;
  drawerEl.hidden = false;
  drawerEl.classList.remove('out');
  drawerEl.classList.toggle('short', name === 'kviz');
  drawerEl.setAttribute('aria-label', TITLES[name]);
  renderDrawer();
  const needScrim = S.mobile && name !== 'kviz';
  if (needScrim) { scrimEl.hidden = false; scrimEl.classList.remove('out'); }
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
    <div class="d-head"><h2>${TITLES[name]}</h2><button class="icbtn" data-dclose aria-label="Bezárás">${ic('x')}</button></div>
    <div class="d-body">${body}</div>${foot ? `<div class="d-foot">${foot}</div>` : ''}`;
  if (name === 'kviz' && Q.i >= QUIZ.length && !RM()) {
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
  if (t.closest('[data-qrestart]')) { Q = { i: 0, answers: [] }; S.quiz = null; refresh(); return renderDrawer(); }
  if (t.closest('[data-qcloud]')) { closeDrawer(); if (S.view === 'lista') setView('felho'); return; }
  if (t.closest('[data-qshare]')) return shareQuiz();
  if (t.closest('[data-qresult]')) return renderDrawer();
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

/* ---------- Kvíz ---------- */
function quizView() {
  if (Q.i >= QUIZ.length) return quizResult();
  const q = QUIZ[Q.i];
  const fitting = S.quiz ? BREEDS.filter(b => b.ok && b.m >= .55).length : TOTAL;
  return [`<div class="qprog">${QUIZ.map((_, j) => `<i class="${j < Q.i || (j === Q.i && Q.answers[j] != null) ? 'on' : ''}"></i>`).join('')}</div>
    <div class="qnum">${Q.i + 1}. kérdés / ${QUIZ.length}</div>
    <div class="qtext">${q.q}</div>
    <div class="qopts">${q.a.map((a, j) => `<button class="qopt${Q.answers[Q.i] === j ? ' sel' : ''}" data-a="${j}" style="--i:${j}"><span class="em">${a.e}</span><span>${a.t}</span></button>`).join('')}</div>
    <div class="qnav"><button class="link" data-qback ${Q.i ? '' : 'style="visibility:hidden"'}>← Vissza</button><span class="qnum">${S.quiz ? `${fitting} fajta illik eddig` : 'A felhő élőben reagál'}</span></div>`, ''];
}
function answer(j, el) {
  Q.answers[Q.i] = j;
  el.classList.add('sel');
  haptic(8);
  S.quiz = { answers: Q.answers.slice(), crit: quizCrit(Q.answers), done: false };
  refresh({ x: S.mobile ? LR.cx : LR.r, y: S.mobile ? LR.b : LR.cy });
  setTimeout(() => {
    Q.i++;
    if (Q.i >= QUIZ.length) { S.quiz.done = true; syncHash(); setTimeout(() => maybeInstall('quiz'), 2500); }
    renderDrawer();
  }, 420);
}
function topBreeds(n) { return [...BREEDS].sort((a, b) => (b.ok - a.ok) || (b.m - a.m)).slice(0, n); }
function quizResult() {
  const type = OWNER_TYPES[ownerType(Q.answers)];
  const top = topBreeds(5);
  return [`<div class="qres-type"><span class="emo">${type.e}</span><div class="qnum" style="margin-top:6px">A gazditípusod</div><h3>${type.n}</h3><p>${type.d}</p></div>
    <h4 style="font:700 19px var(--font-d);margin:14px 0 4px">A te top 5 fajtád</h4>
    <div class="qtop">${top.map((b, i) => `<button class="qrow" data-open="${b.id}" style="${picStyle(b)};--i:${i}"><span class="rk">${i + 1}</span><i class="pic"></i><span><h4>${esc(b.nev)}</h4><p>${esc(b.tagline)}</p></span><span class="pc">${Math.round(b.m * 100)}%</span></button>`).join('')}</div>
    <p class="c-note" style="margin-top:14px">A kvíz a válaszaidból súlyozott szempontokat képez – a felhőben is így rangsorolja a fajtákat.</p>`,
  `<button class="btn fill" data-qcloud style="flex:1">${ic('cloud')}Megnézem a felhőben</button><button class="btn round" data-qshare aria-label="Eredmény megosztása">${ic('share')}</button><button class="btn round ghost" data-qrestart aria-label="Újrakezdés" title="Újrakezdés">↺</button>`];
}

/* Megosztható eredménykép (vászon) */
const loadImg = src => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; });
async function shareQuiz() {
  const type = OWNER_TYPES[ownerType(S.quiz.answers)];
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
  x.fillStyle = ink2; x.font = '600 30px Manrope, system-ui, sans-serif'; x.fillText('A gazditípusom:', W / 2, 205);
  x.fillStyle = ink; x.font = '800 76px Fraunces, Georgia, serif'; x.fillText(`${type.e} ${type.n}`, W / 2, 295);
  x.fillStyle = ink2; x.font = '600 30px Manrope, system-ui, sans-serif'; x.fillText('…és a hozzám illő kutyák:', W / 2, 380);
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
  x.fillStyle = ink2; x.font = '600 28px Manrope, sans-serif'; x.fillText('Találd meg te is a hozzád illő kutyát – Pacsi by DarwinAI 🐾', W / 2, H - 84);
  x.font = '700 24px Manrope, sans-serif'; x.fillStyle = '#EE5A2C'; x.fillText('www.darwinai.hu', W / 2, H - 44);
  const blob = await new Promise(r => c.toBlob(r, 'image/png'));
  if (ARTIFACT) {
    // az artifact-keret letiltja a letöltést és a Web Share-t: a képet itt mutatjuk meg, innen menthető
    const src = URL.createObjectURL(blob);
    $('.d-body', drawerEl).innerHTML = `<p style="margin:0 0 12px;color:var(--ink-2)">Kattints jobb gombbal (mobilon tartsd hosszan nyomva) a képre, és mentsd el vagy oszd meg.</p>
      <img src="${src}" alt="A pacsi-kvíz eredménye: ${esc(type.n)}" style="width:100%;border-radius:20px;box-shadow:var(--shadow)">`;
    $('.d-foot', drawerEl).innerHTML = `<button class="btn fill" data-qresult style="flex:1">← Vissza az eredményhez</button>`;
    return;
  }
  const file = new File([blob], 'pacsi-eredmenyem.png', { type: 'image/png' });
  try {
    if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], title: 'Pacsi by DarwinAI', text: `${type.n} vagyok a Pacsin! 🐾 – Pacsi by DarwinAI, www.darwinai.hu` }); return; }
  } catch (e) { if (e.name === 'AbortError') return; }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'pacsi-eredmenyem.png';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  toast('Kép letöltve – oszd meg bátran! 📸');
}

/* ---------- Kedvencek ---------- */
function favView() {
  const ids = [...S.fav].filter(id => BY_ID.has(id));
  if (!ids.length) {
    const s = SPARES['kabala-pacsi'];
    return [`<div class="dempty"><div class="pic" style="background-image:url('${portrait(s.id)}');background-color:${s.bg}"></div><h3>Még nincs kedvenced</h3><p>Egy fajtakártyán a ♥ gombbal (mobilon a buborékot hosszan nyomva) jelölheted meg.</p></div>`, ''];
  }
  return [`<div class="favs">${ids.map((id, i) => { const b = BY_ID.get(id); const on = S.cmp.includes(id); return `<div class="favrow" style="--i:${i}">
      <button class="pic" data-open="${id}" style="${picStyle(b)}" aria-label="${esc(b.nev)} megnyitása"></button>
      <div><h4>${esc(b.nev)}</h4><p>${esc(b.tagline)}</p></div>
      <button class="icbtn" data-tcmp="${id}" title="${on ? 'Kivétel az összevetésből' : 'Összehasonlításba'}" style="${on ? 'color:var(--teal)' : ''}">${ic('compare')}</button>
      <button class="icbtn" data-unfav="${id}" title="Törlés a kedvencek közül" style="color:var(--primary-fill)">${ic('heart-f')}</button></div>`; }).join('')}</div>`,
  `<button class="btn fill" data-favshare style="flex:1">${ic('share')}Kedvenceim megosztása</button>`];
}
async function shareFavs() {
  const names = [...S.fav].map(id => BY_ID.get(id)?.nev).filter(Boolean);
  const text = `A kedvenc kutyafajtáim a Pacsin: ${names.join(', ')} 🐾 – Pacsi by DarwinAI, www.darwinai.hu`;
  const url = ARTIFACT ? '' : location.href.split('#')[0];
  if (!ARTIFACT) try { if (navigator.share && location.protocol.startsWith('http')) { await navigator.share({ title: 'Pacsi by DarwinAI', text, url }); return; } } catch (e) { if (e.name === 'AbortError') return; }
  try { await navigator.clipboard.writeText(url ? `${text}\n${url}` : text); toast('Lista a vágólapra másolva'); } catch (e) { toast(esc(text)); }
}

/* ---------- Összehasonlítás (radar + táblázat) ---------- */
const RADAR = [['E', 'Energia'], ['Gy', 'Gyerekbarát'], ['I', 'Tanulékony'], ['U', 'Csendes', 1], ['H', 'Kevés hullás', 1], ['A', 'Kevés ápolás', 1]];
const CMP_C = ['#FF6B3D', '#17756E', '#8A63D2'];
function cmpView() {
  const list = S.cmp.map(id => BY_ID.get(id)).filter(Boolean);
  if (list.length < 2) {
    const s = SPARES['kerdo-kutya'];
    return [`<div class="dempty"><div class="pic" style="background-image:url('${portrait(s.id)}');background-color:${s.bg}"></div><h3>Kit hasonlítsunk össze?</h3>
      <p>Tegyél legalább 2 fajtát az összevetésbe a kártyájukon az <b>Összehasonlít</b> gombbal (max. 3).${list.length ? `<br>Eddig: <b>${esc(list[0].nev)}</b>` : ''}</p></div>`, ''];
  }
  const cx = 190, cy = 170, R = 118, n = RADAR.length;
  const pt = (i, v) => { const a = -Math.PI / 2 + i / n * Math.PI * 2; return [cx + Math.cos(a) * R * v, cy + Math.sin(a) * R * v]; };
  const web = [1, 2, 3, 4, 5].map(l => `<polygon class="web" points="${RADAR.map((_, i) => pt(i, l / 5).join(',')).join(' ')}"/>`).join('');
  const spokes = RADAR.map((_, i) => `<line class="spoke" x1="${cx}" y1="${cy}" x2="${pt(i, 1)[0]}" y2="${pt(i, 1)[1]}"/>`).join('');
  const labels = RADAR.map(([, l], i) => { const [x, y] = pt(i, 1.2); return `<text class="lab" x="${x}" y="${y + 4}" text-anchor="middle">${l}</text>`; }).join('');
  const polys = list.map((b, j) => `<polygon class="poly" style="fill:${CMP_C[j]};stroke:${CMP_C[j]};animation-delay:${j * 150}ms" points="${RADAR.map(([k, , inv], i) => pt(i, (inv ? 6 - b.t[k] : b.t[k]) / 5).join(',')).join(' ')}"/>`).join('');
  const rows = [
    ['Méret', b => b.meret.map(v => SIZE_L[v]).join('–')],
    ['Súly', b => range(b.suly) + ' kg'],
    ['Marmagasság', b => b.marmagassag ? range(b.marmagassag) + ' cm' : '–'],
    ['Élettartam', b => range(b.elet) + ' év', b => b.elet[1]],
    ['Szőr', b => b.szor.map(v => COAT_L[v]).join(' / ')],
    ['Gyerekbarát', b => b.t.Gy + '/5', b => b.t.Gy],
    ['Lakásba való', b => b.t.L + '/5', b => b.t.L],
    ['Kezdőknek', b => b.t.K + '/5', b => b.t.K],
    ['Költség', b => COST[b.koltseg || 2].split(' ')[0], b => -(b.koltseg || 2)],
    ['Származás', b => b.orszag],
  ];
  const table = `<table class="ctable"><tbody>${rows.map(([l, f, score]) => {
    const best = score ? Math.max(...list.map(score)) : null;
    return `<tr><th>${l}</th>${list.map(b => `<td class="${score && score(b) === best && list.some(x => score(x) !== best) ? 'best' : ''}">${esc(f(b))}</td>`).join('')}</tr>`;
  }).join('')}</tbody></table>`;
  return [`<div class="cmp-heads">${list.map((b, j) => `<button class="cmp-h" data-open="${b.id}" style="${picStyle(b)};--cc:${CMP_C[j]};border:0;background:none;padding:0"><i class="pic"></i>${esc(b.nev)}</button>`).join('')}</div>
    <svg class="radar" viewBox="0 0 380 340">${web}${spokes}${polys}${labels}</svg>${table}`,
  list.map(b => `<button class="btn ghost" data-tcmp="${b.id}" style="flex:1;font-size:13px;padding:0 10px">${ic('x')}${esc(b.nev.split(' ')[0])}</button>`).join('')];
}

/* ---------- Tippek / Gazdi-tudástár + beállítások ---------- */
function tipsView() {
  const dark = isDark();
  return [`<div class="tips">
    <div class="tipcard"><h4>✅ Mielőtt kutyát veszel</h4><ul>
      <li>Nézd meg a kölyök szüleit és a tartási körülményeket.</li>
      <li>Kérj törzskönyvet (FCI/MEOESZ) és a szülők egészségügyi szűréseit (pl. csípő, szem, szív).</li>
      <li>A kölyök legalább 8 hetes legyen, mikrochippel és oltási könyvvel.</li>
      <li>Kerüld az „olcsó, azonnal elvihető” hirdetéseket – gyakran szaporítótól származnak.</li>
      <li>Kérj írásos adásvételi szerződést.</li></ul></div>
    <div class="tipcard"><h4>🏡 Gondolj az örökbefogadásra</h4><p>Rengeteg fajtatiszta kutya és keverék vár menhelyen vagy fajtamentő szervezetnél. Egy felnőtt kutya jellemét ráadásul már ismerni lehet.</p></div>
    <div class="tipcard"><h4>📋 Kötelezettségek Magyarországon</h4><ul>
      <li>Mikrochip és nyilvántartásba vétel.</li><li>Évenkénti veszettség elleni oltás.</li><li>Az önkormányzati ebösszeírás.</li></ul>
      <small>Tájékoztató jellegű – ellenőrizd a hatályos jogszabályokat és a helyi rendeleteket.</small></div>
    <div class="tipcard"><h4>😮‍💨 Lapos orrú fajták</h4><p>A francia bulldog, a mopsz vagy az angol bulldog cuki, de gyakoriak náluk a légzési, szem- és gerincproblémák. Ha ilyet választasz, csak egészségügyileg szűrt, nyitott orrlyukú szülőktől.</p></div>
    <div class="tipcard"><h4>💶 Mire számíts az első évben?</h4><ul>
      <li>Eledel (a mérettől függően ez a legnagyobb tétel)</li><li>Oltások, féreghajtás, parazita elleni védelem</li>
      <li>Kutyaiskola, felszerelés, fekhely</li><li>Kozmetikus a sokat ápolandó fajtáknál</li><li>Tartalék váratlan állatorvosi költségekre, vagy biztosítás</li></ul>
      <small>A fajtakártyák €–€€€ jelölése a relatív havi fenntartási költséget mutatja.</small></div>
    <div class="tipcard"><h4>⚙️ Beállítások</h4>
      <div class="setrow">Sötét téma <button class="tog" data-set="theme" aria-pressed="${dark}" style="width:auto;padding:0"><span class="sw"></span></button></div>
      <div class="setrow">Kevesebb mozgás <button class="tog" data-set="rm" aria-pressed="${S.rmUser}" style="width:auto;padding:0"><span class="sw"></span></button></div>
      <div class="setrow">Alapértelmezett mód: ${modeOf() === 'strict' ? 'Csak találatok' : 'Rangsor'} <button class="link" data-set="mode">Váltás</button></div>
      <div class="setrow">Bemutató újra <button class="link" data-set="coach">Indítás</button></div></div>
    <div class="tipcard"><h4>ℹ️ A Pacsiról</h4><p>A jellemzők a fajtákra jellemző átlagot írják le; az egyes kutyák ettől eltérhetnek. A portrék saját, mesterséges intelligenciával készült illusztrációk. Az app nem gyűjt adatot: a kedvencek csak ezen az eszközön tárolódnak.</p></div>
    <div class="tipcard credit-card"><span class="mark">D</span><div><h4 style="margin:0 0 2px">Pacsi by DarwinAI</h4><p>A Pacsit a <b>DarwinAI</b> tervezte és fejlesztette.<br><a href="https://www.darwinai.hu" target="_blank" rel="noopener">www.darwinai.hu ↗</a></p><p class="ver">Verzió: v${APP_VERSION} · build ${APP_BUILD}</p></div></div>
  </div>`, ''];
}
function setting(k, el) {
  if (k === 'theme') { toggleTheme(); el.setAttribute('aria-pressed', S.theme === 'dark'); }
  else if (k === 'rm') { S.rmUser = !S.rmUser; store.set('rm', S.rmUser); document.documentElement.classList.toggle('rm', RM()); el.setAttribute('aria-pressed', S.rmUser); }
  else if (k === 'mode') { setMode(modeOf() === 'strict' ? 'rank' : 'strict'); renderDrawer(); }
  else if (k === 'coach') { closeDrawer(); preloadHero(); setTimeout(startOnboarding, 400); }
}

/* ---------- Kirepült fajták (mobil) ---------- */
function flownView() {
  const out = BREEDS.filter(b => !b.ok);
  if (!out.length) return ['<div class="dempty"><h3>Senki sem repült ki</h3><p>Minden fajta a felhőben van.</p></div>', ''];
  return [`<p style="margin:0 0 12px;color:var(--ink-2)">Ők most kirepültek – de bármikor visszahívhatod őket egy szűrő elengedésével.</p>
    <div class="favs">${out.slice(0, 80).map((b, i) => { const why = reasons(b).find(r => r.cls !== 'y'); return `<div class="favrow" style="--i:${Math.min(i, 20)};grid-template-columns:58px 1fr">
      <button class="pic" data-open="${b.id}" style="${picStyle(b)}" aria-label="${esc(b.nev)}"></button>
      <div><h4>${esc(b.nev)}</h4><p style="color:#D9483B">✗ ${esc(why ? why.text : '')}</p></div></div>`; }).join('')}</div>`,
  `<button class="btn fill" data-clearall style="flex:1">Mindenkit vissza a felhőbe</button>`];
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
