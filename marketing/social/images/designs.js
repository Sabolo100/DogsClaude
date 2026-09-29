/* Pacsi Marketing – képdesignok. Mindegyik függvény egy HTML-t ad vissza a (w×h) vászonra.
   A képeken lévő feliratok végleges, kiposztolható szövegek; a posztszövegek a content.json-ban vannak.
   Fajtaadatok (név, tagline, jellemzők) a data/fajtak.json-ból jönnek – egy forrás az appal. */
const HU9 = ['puli', 'pumi', 'mudi', 'komondor', 'kuvasz', 'erdelyi-kopo', 'magyar-vizsla', 'drotszoru-magyar-vizsla', 'magyar-agar'];
const SHORT = { 'magyar-vizsla': 'Rövidszőrű vizsla', 'drotszoru-magyar-vizsla': 'Drótszőrű vizsla', 'cavalier-king-charles-spaniel': 'Cavalier', 'angol-agar': 'Angol agár', 'pomeraniai-torpespicc': 'Törpespicc' };
const sname = id => SHORT[id] || K.name(id);
const CLOUD = ['cavalier-king-charles-spaniel', 'magyar-vizsla', 'golden-retriever', 'puli', 'bichon-frise', 'border-collie', 'mopsz', 'havanese', 'beagle',
  'shiba-inu', 'szamojed', 'tacsko', 'whippet', 'francia-bulldog', 'labrador-retriever', 'mudi', 'bernathegyi', 'uszkar', 'jack-russell-terrier', 'boston-terrier',
  'komondor', 'sziberiai-husky', 'dalmata', 'pomeraniai-torpespicc', 'yorkshire-terrier', 'basenji', 'angol-agar', 'shih-tzu', 'coton-de-tulear', 'lagotto-romagnolo',
  'welsh-corgi-pembroke', 'berni-pasztorkutya', 'kuvasz', 'papillon', 'nemet-juhaszkutya', 'akita-inu', 'chihuahua', 'pumi', 'dobermann', 'uj-fundlandi', 'maltai-selyemkutya', 'weimari-vizsla'];

/** Robbanásszerű „pacsi-csillanás”: sugarak egy pont körül (a0..a1 fokban) */
const burst = (cx, cy, { r0 = 70, r1 = 120, n = 9, a0 = -160, a1 = -20, wd = 9, cols = ['#FF6B3D', '#FFC845', '#E86A92', '#17756E', '#5B5BD6'] } = {}) => {
  let l = '';
  for (let i = 0; i < n; i++) {
    const a = (a0 + (a1 - a0) * i / (n - 1)) * Math.PI / 180, rr = r1 - (i % 2) * (r1 - r0) * .35;
    l += `<line x1="${cx + Math.cos(a) * r0}" y1="${cy + Math.sin(a) * r0}" x2="${cx + Math.cos(a) * rr}" y2="${cy + Math.sin(a) * rr}" stroke="${cols[i % cols.length]}" stroke-width="${wd}" stroke-linecap="round"/>`;
  }
  return `<svg class="abs" style="left:0;top:0;overflow:visible;z-index:3" width="1" height="1">${l}</svg>`;
};
/** illeszkedési pontszám (az app képletével) a megadott kapcsoló-szűrőkre */
const SC = [0, 0, .15, .5, .85, 1];
const TS = { gyerek: b => SC[b.t.Gy], lakas: b => SC[b.t.L], csendes: b => SC[6 - b.t.U], kezdo: b => SC[b.t.K], hullas: b => SC[6 - b.t.H] };
const match = (id, fs) => Math.round(fs.reduce((s, f) => s + TS[f](K.by[id]), 0) / fs.length * 100);

const TYPES = [
  { e: '🛋️', n: 'Kanapé-kapitány', d: 'Nyugis esték, rövid séták, sok bújás.', c: '#FFD9C2', ids: ['mopsz', 'shih-tzu'] },
  { e: '🏃', n: 'Aktív kalandor', d: 'Futás, túra, bicikli – bírja a tempót.', c: '#CDEFE0', ids: ['magyar-vizsla', 'border-collie'] },
  { e: '👨‍👩‍👧', n: 'Családi karmester', d: 'Gyerekzsivaj, türelmes családtag.', c: '#FFE6A0', ids: ['golden-retriever', 'labrador-retriever'] },
  { e: '🏙️', n: 'Városi flâneur', d: 'Kávézóterasz, parki séta, lift.', c: '#E2D6FF', ids: ['whippet', 'francia-bulldog'] },
  { e: '🛡️', n: 'Tanyasi őrangyal', d: 'Van udvar, kell egy hűséges őrző.', c: '#BFDDF7', ids: ['komondor', 'kuvasz'] },
  { e: '🎓', n: 'Kutyasuttogó', d: 'Tapasztalt vagy, kihívásra vágysz.', c: '#FFC8D6', ids: ['malinois', 'nemet-juhaszkutya'] },
];

/** Fajtakártya-sor: jellemzőmérő címkével */
const traitRow = (label, v, { w = 440, fs = 28, d = 22 } = {}) => `<div class="row" style="justify-content:space-between;width:${w}px;font:700 ${fs}px/1 var(--font-u);color:var(--ink)"><span>${label}</span>${K.meter(v, { d, g: 8 })}</div>`;

const DESIGNS = {
  /* ---------- A1 · Bemutatkozás: pacsi a kabalával ---------- */
  launch({ w, h }) {
    const top = h - w;
    const cx = 447 * w / 1080, cy = top + 465 * w / 1080;
    return `<div class="bgl" style="background:#FDF8EA"></div>
      <img class="kv" src="${K.kv('kv_pacsi_highfive')}" style="left:0;top:${top}px;width:${w}px;height:${w}px">
      ${[[-87, -135, 9, '#FF6B3D'], [-37, -157, 7, '#FFC845'], [21, -145, 10, '#E86A92'], [73, -129, 7, '#17756E'], [98, -95, 9, '#5B5BD6'], [-117, -95, 7, '#2FA3D6']].map(([dx, dy, r, c]) => `<i class="dot" style="left:${cx + dx - r}px;top:${cy + dy - r}px;width:${r * 2}px;height:${r * 2}px;background:${c};z-index:3"></i>`).join('')}
      <div class="abs" style="left:72px;top:84px;right:60px">
        <div class="kicker">Új · ingyenes · 124 kutyafajta</div>
        <div class="hd" style="font-size:106px;margin-top:26px">Adj egy pacsit<br>a hozzád illő<br><span class="it">kutyának!</span></div>
        <div class="body-l" style="margin-top:30px;max-width:640px">Szűrj, töltsd ki a kvízt, és figyeld, melyik fajta marad a felhőben.</div>
      </div>
      <div class="abs" style="left:72px;bottom:74px">${K.logo(66)}<div class="url" style="margin-top:20px">Próbáld ki ingyen – link a bióban</div></div>`;
  },

  /* ---------- A3 · Négyzetes hirdetés: szűrők + telefon ---------- */
  launch_sq({ w, h }) {
    return `${K.blobs(w, h, 0)}
      <div class="abs" style="left:64px;top:60px">${K.logo(46)}</div>
      <div class="abs" style="left:64px;top:150px;width:540px">
        <div class="hd" style="font-size:94px">Melyik kutya illik <span class="it">hozzád?</span></div>
      </div>
      ${K.phone(K.screen('m_filtered'), { x: 618, y: 170, sw: 360, rot: 7 })}
      <div class="abs" style="left:70px;top:420px;display:flex;flex-direction:column;gap:24px;align-items:flex-start">
        <span style="transform:rotate(-3deg)">${K.chip('home', 'Lakásba való')}</span>
        <span style="transform:rotate(2deg);margin-left:36px">${K.chip('kid', 'Gyerekbarát')}</span>
        <span style="transform:rotate(-2deg);margin-left:8px">${K.chip('quiet', 'Csendes')}</span>
      </div>
      <div class="abs" style="left:72px;top:690px">
        <div class="row" style="align-items:baseline;gap:18px"><span class="hd" style="font-size:118px;letter-spacing:-.04em">124</span><span style="font:800 64px/1 var(--font-u);color:var(--primary-fill)">→</span><span class="hd it" style="font-size:118px">10</span></div>
        <div class="label" style="margin-top:6px;letter-spacing:.08em">fajta illik hozzád</div>
      </div>
      <div class="abs" style="left:64px;bottom:62px"><span class="cta" style="font-size:36px;padding:22px 40px">Próbáld ki ingyen</span></div>`;
  },

  /* ---------- B1 · Előtte–utána: 124 → 10 ---------- */
  before_after({ w, h }) {
    const sw = 392;
    return `${K.blobs(w, h, 1)}
      <div class="abs" style="right:64px;top:66px">${K.logo(44)}</div>
      <div class="abs" style="left:64px;right:64px;top:74px">
        <div class="kicker">3 koppintás</div>
        <div class="hd" style="font-size:100px;margin-top:22px">124 kutyából<br><span class="it">10, ami illik hozzád</span></div>
      </div>
      <div class="abs" style="left:78px;top:418px"><span class="tag">Előtte: 124 fajta</span></div>
      <div class="abs" style="right:70px;top:418px"><span class="tag hot">Utána: 10 fajta</span></div>
      ${K.phone(K.screen('m_cloud'), { x: 40, y: 506, sw, rot: -5, z: 2 })}
      ${K.phone(K.screen('m_filtered'), { x: 600, y: 471, sw, rot: 5, z: 3 })}
      <div class="abs" style="left:318px;top:726px;z-index:6;display:flex;flex-direction:column;gap:22px;align-items:center">
        <span style="transform:rotate(-4deg)">${K.chip('home', 'Lakás', { size: 1.05 })}</span>
        <span style="transform:rotate(3deg)">${K.chip('kid', 'Gyerek', { size: 1.05 })}</span>
        <span style="transform:rotate(-2deg)">${K.chip('quiet', 'Csendes', { size: 1.05 })}</span>
      </div>`;
  },

  /* ---------- C1 · A 9 magyar kutyafajta ---------- */
  hu9({ w, h }) {
    const d = 180, gx = 316, gy = 262, x0 = w / 2 - gx, y0 = 440;
    const cells = HU9.map((id, i) => {
      const x = x0 + (i % 3) * gx, y = y0 + Math.floor(i / 3) * gy;
      return K.bub(id, x, y, d, { z: 2 }) + `<div class="abs bname" style="left:${x - 150}px;width:300px;top:${y + d / 2 + 18}px">${K.esc(sname(id))}</div>`;
    }).join('');
    return `${K.blobs(w, h, 2)}
      <div class="abs" style="left:64px;right:64px;top:66px;text-align:center">
        <div class="row" style="justify-content:center;gap:16px"><span class="tricolor"><i></i><i></i><i></i></span><span class="kicker">Magyar büszkeségek</span><span class="tricolor"><i></i><i></i><i></i></span></div>
        <div class="hd" style="font-size:80px;margin-top:22px">Ismered mind<br>a <span class="it">9 magyar</span> kutyafajtát?</div>
      </div>
      ${cells}
      <div class="abs" style="left:0;right:0;bottom:58px;text-align:center">
        <div class="body-m" style="color:var(--ink)">Kapcsold be a <b style="color:var(--primary-fill)">Magyar</b> szűrőt a Pacsiban!</div>
        <div style="margin-top:16px">${K.logo(46)}</div>
      </div>`;
  },

  /* ---------- B2 · Párkereső kvíz: 6 gazditípus ---------- */
  feat_quiz({ w, h }) {
    const cw = 452, ch = 238, gx = 24, gy = 24, x0 = (w - 2 * cw - gx) / 2, y0 = 452;
    const cards = TYPES.map((t, i) => {
      const x = x0 + (i % 2) * (cw + gx), y = y0 + Math.floor(i / 2) * (ch + gy);
      return `<div class="card-w" style="left:${x}px;top:${y}px;width:${cw}px;height:${ch}px;border-radius:34px;overflow:hidden">
        <div class="abs" style="left:0;top:0;right:0;height:10px;background:${t.c}"></div>
        <div class="abs" style="left:28px;top:36px;font-size:66px;line-height:1">${t.e}</div>
        <div class="abs" style="left:28px;top:124px;right:24px">
          <div class="hd" style="font-size:40px;letter-spacing:-.02em">${t.n}</div>
          <div style="font:600 23px/1.3 var(--font-u);color:var(--ink-2);margin-top:8px">${t.d}</div></div>
        ${K.bub(t.ids[0], cw - 118, 74, 82, { z: 3 })}${K.bub(t.ids[1], cw - 50, 88, 66, { z: 2 })}
      </div>`;
    }).join('');
    return `${K.blobs(w, h, 0)}
      <div class="abs" style="left:64px;right:64px;top:70px">
        <div class="row" style="justify-content:space-between"><div class="kicker">Párkereső kvíz</div>${K.logo(40)}</div>
        <div class="hd" style="font-size:108px;margin-top:22px">Milyen <span class="it">gazdi</span> vagy?</div>
        <div class="body-m" style="margin-top:22px">10 kérdés, 1 perc – és kiderül, melyik fajták illenek hozzád.</div>
      </div>
      ${cards}
      <div class="abs" style="left:0;right:0;bottom:56px;text-align:center"><span class="tag ink" style="font-size:32px;padding:18px 30px">Te melyik vagy? Írd meg kommentben! 👇</span></div>`;
  },

  /* ---------- B3 · Összehasonlítás: radar ---------- */
  feat_compare({ w, h }) {
    const ids = ['magyar-vizsla', 'golden-retriever', 'border-collie'], cols = ['#EE5A2C', '#17756E', '#5B5BD6'];
    const ax = [['Energia', b => b.t.E], ['Gyerekbarát', b => b.t.Gy], ['Tanulékony', b => b.t.I], ['Csendes', b => 6 - b.t.U], ['Kevés hullás', b => 6 - b.t.H], ['Kevés ápolás', b => 6 - b.t.A]];
    const R = 218, cx = w / 2, cy = 872;
    const pt = (i, v) => { const a = -Math.PI / 2 + i * Math.PI * 2 / ax.length; return [cx + Math.cos(a) * R * v / 5, cy + Math.sin(a) * R * v / 5]; };
    let grid = '';
    for (let k = 1; k <= 5; k++) grid += `<polygon points="${ax.map((_, i) => pt(i, k).join(',')).join(' ')}" fill="${k === 5 ? 'rgba(255,255,255,.7)' : 'none'}" stroke="rgba(30,27,24,.10)" stroke-width="2"/>`;
    grid += ax.map((_, i) => `<line x1="${cx}" y1="${cy}" x2="${pt(i, 5)[0]}" y2="${pt(i, 5)[1]}" stroke="rgba(30,27,24,.10)" stroke-width="2"/>`).join('');
    const polys = ids.map((id, j) => `<polygon points="${ax.map((a, i) => pt(i, a[1](K.by[id])).join(',')).join(' ')}" fill="${cols[j]}" fill-opacity=".13" stroke="${cols[j]}" stroke-width="5" stroke-linejoin="round"/>`).join('');
    const labels = ax.map((a, i) => { const [x, y] = pt(i, 6.15); return `<div class="abs" style="left:${x - 120}px;top:${y - 18}px;width:240px;text-align:center;font:800 26px/1.1 var(--font-u);color:var(--ink-2)">${a[0]}</div>`; }).join('');
    const heads = ids.map((id, j) => {
      const x = w / 2 + (j - 1) * 300;
      return K.bub(id, x, 396, 150, { z: 3, style: `box-shadow:0 0 0 7px #fff,0 0 0 13px ${cols[j]},0 14px 30px rgba(90,50,20,.2)` }) +
        `<div class="abs bname" style="left:${x - 140}px;width:280px;top:494px;color:${cols[j]}">${K.esc(sname(id))}</div>`;
    }).join('');
    return `${K.blobs(w, h, 1)}
      <div class="abs" style="left:64px;right:64px;top:70px;text-align:center">
        <div class="kicker">Összehasonlítás</div>
        <div class="hd" style="font-size:78px;margin-top:20px">Vizsla, golden vagy <span class="it">border collie?</span></div>
      </div>
      ${heads}
      <svg class="abs" style="left:0;top:0" width="${w}" height="${h}">${grid}${polys}</svg>
      ${labels}
      <div class="abs" style="left:90px;right:90px;bottom:104px;text-align:center" ><div class="body-m" style="font-size:28px">Tedd egymás mellé a jelöltjeidet – a Pacsi megmutatja, miben különböznek.</div></div>
      <div class="abs" style="left:0;right:0;bottom:38px;text-align:center">${K.logo(40)}</div>`;
  },

  /* ---------- B4 · Fajtakártya magyarázó feliratokkal ---------- */
  feat_card({ w, h }) {
    const sw = 470, s = sw / 390, px = w - 64 - K.phoneSize(sw).w + 20, py = 330;
    const P = (x, y) => [px + (14 + x) * s, py + (14 + y) * s];
    // [címke teteje, felirat, célpont a képernyőképen (390×844-es koordináták)]
    const call = [
      [686, 'Jellemzés egy mondatban', 44, 393],
      [812, 'Mennyire illik hozzád', 50, 467],
      [938, 'Méret, súly, élettartam', 50, 541],
      [1064, '9 jellemző, 1-től 5-ig', 26, 628],
    ];
    const lines = call.map(([y, , ax, ay]) => {
      const [x2, y2] = P(ax, ay), x1 = 440, y1 = y + 34;
      return `<path d="M ${x1} ${y1} C ${x1 + 60} ${y1}, ${x2 - 70} ${y2}, ${x2 - 14} ${y2}" fill="none" stroke="#EE5A2C" stroke-width="4" stroke-dasharray="2 11" stroke-linecap="round"/><circle cx="${x2}" cy="${y2}" r="11" fill="#EE5A2C" stroke="#fff" stroke-width="5"/>`;
    }).join('');
    const labels = call.map(([y, t], i) => `<div class="abs" style="left:64px;top:${y}px;width:376px;display:flex;justify-content:flex-end"><span class="tag" style="font-size:26px;padding:16px 22px"><b style="color:var(--primary-fill);margin-right:2px">${i + 1}</b> ${t}</span></div>`).join('');
    return `${K.blobs(w, h, 2)}
      <div class="abs" style="left:64px;right:64px;top:70px">
        <div class="row" style="justify-content:space-between"><div class="kicker">Fajtakártya</div>${K.logo(40)}</div>
        <div class="hd" style="font-size:88px;margin-top:22px">Minden, ami számít – <span class="it">egy kártyán</span></div>
      </div>
      ${K.phone(K.screen('m_card_agar'), { x: px, y: py, sw, z: 2 })}
      <svg class="abs" style="left:0;top:0;z-index:4;overflow:visible" width="${w}" height="${h}">${lines}</svg>
      ${labels}
      <div class="abs" style="left:64px;top:356px;width:420px"><div class="body-m" style="font-size:29px">Portré, illeszkedés, jellemzők – plusz egészség, költségek, kinek ajánlott és érdekességek mind a 124 fajtáról.</div></div>`;
  },

  /* ---------- C2 · Térkép: 4 kutyatípus ---------- */
  map4({ w, h }) {
    const L = 170, T = 400, S = 740, half = S / 2;
    const Q = [
      { n: 1, t: 'Zsebrakéták', s: 'kicsi, de pörgős', ids: ['jack-russell-terrier', 'pumi', 'papillon'], x: L, y: T },
      { n: 2, t: 'Sportgépek', s: 'nagy és fáradhatatlan', ids: ['magyar-vizsla', 'dalmata', 'malinois'], x: L + half, y: T },
      { n: 3, t: 'Nyugis törpék', s: 'kicsi és kényelmes', ids: ['shih-tzu', 'mopsz', 'pekingi-palotakutya'], x: L, y: T + half },
      { n: 4, t: 'Kanapé-óriások', s: 'nagy, de nyugodt', ids: ['bernathegyi', 'uj-fundlandi', 'komondor'], x: L + half, y: T + half },
    ];
    const bg = ['rgba(255,210,184,.55)', 'rgba(201,238,220,.6)', 'rgba(226,214,255,.6)', 'rgba(255,230,160,.55)'];
    const quads = Q.map((q, i) => `<div class="abs" style="left:${q.x + 8}px;top:${q.y + 8}px;width:${half - 16}px;height:${half - 16}px;border-radius:34px;background:${bg[i]}"></div>
      <div class="abs" style="left:${q.x + 34}px;top:${q.y + 30}px;width:${half - 60}px">
        <div class="row" style="gap:14px"><span style="display:grid;place-items:center;width:52px;height:52px;border-radius:50%;background:var(--ink);color:#fff;font:800 30px/1 var(--font-d)">${q.n}</span><span class="hd" style="font-size:34px;letter-spacing:-.02em;white-space:nowrap">${q.t}</span></div>
        <div style="font:700 23px/1.2 var(--font-u);color:var(--ink-2);margin:8px 0 0 66px">${q.s}</div></div>
      ${K.bub(q.ids[0], q.x + half * .32, q.y + half * .68, 140, { z: 3 })}${K.bub(q.ids[1], q.x + half * .70, q.y + half * .62, 110, { z: 2 })}${K.bub(q.ids[2], q.x + half * .66, q.y + half * .86, 78, { z: 4 })}`).join('');
    return `${K.blobs(w, h, 0)}
      <div class="abs" style="left:64px;right:64px;top:66px">
        <div class="row" style="justify-content:space-between"><div class="kicker">Térkép nézet</div>${K.logo(40)}</div>
        <div class="hd" style="font-size:92px;margin-top:22px">Zsebrakéta vagy <span class="it">kanapé-óriás?</span></div>
      </div>
      ${quads}
      <svg class="abs" style="left:0;top:0;overflow:visible" width="${w}" height="${h}">
        <defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="#6B625A"/></marker></defs>
        <line x1="${L - 36}" y1="${T + S}" x2="${L - 36}" y2="${T - 10}" stroke="#6B625A" stroke-width="4" marker-end="url(#ah)"/>
        <line x1="${L - 10}" y1="${T + S + 34}" x2="${L + S + 10}" y2="${T + S + 34}" stroke="#6B625A" stroke-width="4" marker-end="url(#ah)"/></svg>
      <div class="abs label" style="left:${L - 58}px;top:${T + S / 2}px;transform:translate(-50%,-50%) rotate(-90deg);white-space:nowrap;font-size:22px">nyugis ← Energia → pörgős</div>
      <div class="abs label" style="left:${L}px;width:${S}px;top:${T + S + 52}px;text-align:center;font-size:22px">kicsi ← Méret → nagy</div>
      <div class="abs" style="left:0;right:0;bottom:40px;text-align:center"><span class="tag ink" style="font-size:30px;padding:16px 28px">Te melyiket választanád? 1, 2, 3 vagy 4? 👇</span></div>`;
  },

  /* ---------- C3 · Karusszel: 5 csendes, lakásba való kutya (p = 1…7) ---------- */
  car_lakas({ w, h, p }) {
    const ids = ['cavalier-king-charles-spaniel', 'coton-de-tulear', 'whippet', 'basenji', 'angol-agar'];
    const n = +p || 1, tot = 7;
    const pager = `<div class="abs" style="right:56px;top:62px;font:800 24px/1 var(--font-u);color:var(--ink-2);letter-spacing:.06em">${n}/${tot}</div>`;
    const swipe = `<div class="abs" style="right:56px;bottom:56px;font:800 28px/1 var(--font-u);color:var(--primary-fill)">Lapozz →</div>`;
    if (n === 1) {
      const arc = ids.map((id, i) => { const x = 150 + i * 195, y = 1010 + (i % 2 ? 60 : 0); return K.bub(id, x, y, 168, { z: 2 + i }) +
        `<div class="abs" style="left:${x - 22}px;top:${y + 64}px;z-index:9;display:grid;place-items:center;width:44px;height:44px;border-radius:50%;background:var(--ink);color:#fff;font:800 24px/1 var(--font-d)">${i + 1}</div>`; }).join('');
      return `${K.blobs(w, h, 1)}${pager}
        <div class="abs" style="left:64px;top:62px">${K.logo(44)}</div>
        <div class="abs" style="left:64px;right:64px;top:196px">
          <div class="row" style="gap:14px">${K.chip('home', 'Lakásba való', { size: .9 })}${K.chip('quiet', 'Csendes', { size: .9 })}</div>
          <div class="hd" style="font-size:112px;margin-top:40px">5 kutya, amiért a <span class="it">szomszéd</span> is hálás lesz</div>
          <div class="body-l" style="margin-top:30px">Kis lakás, vékony falak? Ők ritkán ugatnak. <b style="color:var(--ink)">Az utolsó meglep!</b></div>
        </div>${arc}${swipe}`;
    }
    if (n === tot) {
      return `${K.blobs(w, h, 2)}${pager}
        <div class="abs" style="left:64px;right:64px;top:100px">
          <div class="hd" style="font-size:100px">Találd meg a te <span class="it">csendes lakótársadat</span></div>
          <div class="body-l" style="margin-top:28px;max-width:520px">Kapcsold be a Lakás és a Csendes szűrőt – 124 fajtából ez a 16 marad.</div>
        </div>
        ${K.phone(K.screen('m_lakas_csendes'), { x: 600, y: 470, sw: 400, rot: 6 })}
        <div class="abs" style="left:64px;top:640px;display:flex;flex-direction:column;gap:22px;align-items:flex-start">
          <span style="transform:rotate(-3deg)">${K.chip('home', 'Lakás')}</span><span style="transform:rotate(2deg);margin-left:30px">${K.chip('quiet', 'Csendes')}</span></div>
        <div class="abs" style="left:64px;bottom:70px">${K.logo(58)}<div class="url" style="margin-top:18px">Ingyenes · link a bióban</div></div>`;
    }
    const id = ids[n - 2], b = K.by[id];
    const notes = {
      'cavalier-king-charles-spaniel': ['Kezdőknek és gyerekes családoknak is jó választás.', 'Szívszűrt szülőktől válaszd!'],
      'coton-de-tulear': ['Alig hullat szőrt – allergiásoknak barátságosabb.', 'A bundáját rendszeresen fésülni kell.'],
      'whippet': ['Otthon nyugodt, bújós kanapészobor.', 'Futni is szeret – biztonságos, bekerített helyen.'],
      'basenji': ['Alig hullat, és úgy mosakszik, mint egy macska.', 'Nem kezdőknek: önfejű, sok mozgást igényel.'],
      'angol-agar': ['Meglepő, de igazi lakótárs: csendes és nyugodt.', 'Sprintelni biztonságos, bekerített helyen engedd.'],
    }[id];
    return `${K.blobs(w, h, n % 3)}${pager}
      <div class="abs" style="left:64px;top:62px">${K.logo(40)}</div>
      ${K.bub(id, w / 2, 470, 470, { ring: 100, z: 2 })}
      <div class="abs" style="left:${w / 2 + 150}px;top:250px;z-index:4;display:grid;place-items:center;width:104px;height:104px;border-radius:50%;background:var(--ink);color:#fff;font:800 58px/1 var(--font-d)">${n - 1}</div>
      <div class="abs" style="left:64px;right:64px;top:760px;text-align:center">
        <div class="hd" style="font-size:${b.nev.length > 22 ? 64 : 80}px">${K.esc(b.nev)}</div>
        <div class="bsub" style="font-size:36px;margin-top:14px">${K.esc(b.tagline)}</div>
      </div>
      <div class="abs" style="left:110px;top:${b.tagline.length > 46 ? 1000 : 960}px;display:grid;grid-template-columns:1fr 1fr;gap:18px 60px">
        ${traitRow('Lakásba való', b.t.L, { w: 400 })}${traitRow('Csendes', 6 - b.t.U, { w: 400 })}${traitRow('Energia', b.t.E, { w: 400 })}${traitRow('Gyerekbarát', b.t.Gy, { w: 400 })}
      </div>
      <div class="abs" style="left:110px;right:110px;top:1128px;font:700 27px/1.45 var(--font-u);color:var(--ink)">
        <div>✓ ${notes[0]}</div><div style="color:var(--ink-2)">⚠ ${notes[1]}</div></div>
      ${swipe}`;
  },

  /* ---------- C4 · „Tudtad?” tényposztok (p = basenji | agar | border) ---------- */
  tudtad({ w, h, p }) {
    const F = {
      basenji: { id: 'basenji', hd: 'Ez a kutya nem ugat. <span class="it">Jódlizik.</span>', tx: 'A basenji az „ugatás nélküli kutya”: ugatás helyett jellegzetes, jódlizó hangot ad – és úgy mosakszik, mint egy macska.' },
      agar: { id: 'angol-agar', hd: '70 km/h sprintben. Otthon: <span class="it">kanapészobor.</span>', tx: 'Az angol agár a leggyorsabb kutyafajta, mégis csendes, nyugodt lakótárs, aki a legszívesebben heverészik.' },
      border: { id: 'border-collie', hd: 'Több mint <span class="it">1000 játékát</span> ismerte név szerint', tx: 'Chaser, egy amerikai border collie képességeit tudományos cikk is leírta. A border collie a kutyavilág zsenije – munka nélkül unatkozik.' },
    }[p || 'basenji'];
    return `${K.blobs(w, h, 1)}
      <div class="abs" style="left:64px;top:64px;right:64px"><div class="row" style="justify-content:space-between"><span class="hd" style="font-size:64px;color:var(--primary-fill);font-style:italic">Tudtad?</span>${K.logo(40)}</div></div>
      ${K.bub(F.id, w / 2, 520, 560, { z: 2 })}
      ${K.dots(14, { x0: 120, y0: 200, w: 840, h: 640, seed: p === 'agar' ? 5 : p === 'border' ? 9 : 2, rmin: 6, rmax: 13 })}
      <div class="card-w" style="left:64px;right:64px;top:830px;padding:44px 50px 40px;z-index:3">
        <div class="hd" style="font-size:66px">${F.hd}</div>
        <div class="body-m" style="margin-top:20px;font-size:29px">${F.tx}</div>
        <div class="row" style="gap:12px;margin-top:24px"><span class="tag" style="background:var(--bg);box-shadow:none;font-size:25px">${K.ic('dog', 26)} ${K.esc(K.name(F.id))}</span></div>
      </div>`;
  },

  /* ---------- C5 · A hét fajtája (p = fajta-id) ---------- */
  het({ w, h, p }) {
    const id = p || 'magyar-vizsla', b = K.by[id];
    const SZ = { toy: 'Toy', kicsi: 'Kicsi', kozepes: 'Közepes', nagy: 'Nagy', orias: 'Óriás' };
    const CO = { rovid: 'Rövid szőr', kozepes: 'Közepes szőr', hosszu: 'Hosszú szőr', drot: 'Drótszőr', gondor: 'Göndör', zsinoros: 'Zsinóros', szortelen: 'Szőrtelen' };
    const rng = a => a[0] === a[a.length - 1] ? `${a[0]}` : `${a[0]}–${a[a.length - 1]}`;
    const chips = [b.meret.map(m => SZ[m]).join('–'), `${rng(b.suly)} kg`, `${rng(b.elet)} év`, CO[b.szor[0]]].map(t => `<span class="tag" style="font-size:26px;padding:12px 20px">${String(t).replace('.', ',')}</span>`).join('');
    const tr = [['Energia', b.t.E], ['Gyerekbarát', b.t.Gy], ['Tanulékony', b.t.I], ['Lakásba való', b.t.L], ['Csendes', 6 - b.t.U], ['Kezdőknek', b.t.K]];
    return `${K.blobs(w, h, 2)}
      <div class="abs" style="left:64px;right:64px;top:64px"><div class="row" style="justify-content:space-between"><div class="kicker">A hét fajtája</div>${K.logo(40)}</div></div>
      ${K.bub(id, 300, 380, 380, { ring: 100, z: 2 })}
      <div class="abs" style="left:540px;right:64px;top:210px">
        ${b.hu ? '<div class="row" style="gap:10px;margin-bottom:14px"><span class="tricolor"><i></i><i></i><i></i></span><span class="label" style="font-size:20px">Magyar fajta</span></div>' : ''}
        <div class="hd" style="font-size:${b.nev.length > 18 ? 60 : 78}px">${K.esc(b.nev)}</div>
        <div class="bsub" style="text-align:left;font-size:32px;margin-top:16px">${K.esc(b.tagline)}</div>
      </div>
      <div class="abs" style="left:64px;right:64px;top:622px;display:flex;flex-wrap:wrap;gap:14px">${chips}</div>
      <div class="abs" style="left:80px;top:734px;display:grid;grid-template-columns:1fr 1fr;gap:20px 70px">${tr.map(([l, v]) => traitRow(l, v, { w: 420 })).join('')}</div>
      <div class="card-w" style="left:64px;right:64px;top:990px;padding:26px 40px;border-radius:30px">
        <div class="kicker" style="font-size:22px">Érdekesség</div>
        <div style="font:600 26px/1.38 var(--font-u);color:var(--ink);margin-top:10px">${K.esc(b.erdekesseg)}</div></div>
      <div class="abs" style="left:80px;right:80px;top:1188px;display:grid;grid-template-columns:1fr 1fr;gap:40px;font:700 24px/1.35 var(--font-u)">
        <div><span style="color:var(--ok)">✓ Kinek ajánlott?</span><br><span style="color:var(--ink)">${K.esc(b.kinekIgen[0])}</span></div>
        <div><span style="color:#C8431C">⚠ Kinek nem?</span><br><span style="color:var(--ink)">${K.esc(b.kinekNem[0])}</span></div></div>
      <div class="abs" style="left:64px;right:64px;bottom:34px;text-align:center;font:700 22px/1 var(--font-u);color:var(--ink-2)">A teljes fajtakártya a Pacsiban – link a bióban</div>`;
  },

  /* ---------- D1 · Story: bemutatkozik a kabala ---------- */
  story_hello({ w, h }) {
    const iw = 1060, ih = iw * 2048 / 1536;
    return `<div class="bgl" style="background:#FEF9EC"></div>
      <img class="kv" src="${K.kv('kv_mascot_wave')}" style="left:${w - iw + 170}px;top:${h - ih + 60}px;width:${iw}px;height:${ih}px">
      <div class="abs" style="left:72px;top:150px">${K.logo(44)}</div>
      <div class="abs" style="left:72px;right:72px;top:250px">
        <div class="hd" style="font-size:118px">Szia! Én vagyok <span class="it">a Pacsi.</span></div>
        <div class="body-l" style="margin-top:28px;font-size:40px;max-width:760px">Segítek megtalálni a hozzád illő kutyát – 124 fajta közül.</div>
      </div>
      <div class="abs" style="left:72px;top:1120px"><span class="tag hot" style="font-size:32px;padding:16px 26px">Koppints a linkre! ↓</span></div>`;
  },

  /* ---------- D2 · Story: kvíz-teaser (hely a szavazás-matricának) ---------- */
  story_quiz({ w, h }) {
    const ring = TYPES.map((t, i) => { const a = -Math.PI / 2 + i * Math.PI / 3; const x = w / 2 + Math.cos(a) * 330, y = 940 + Math.sin(a) * 330;
      return `<div class="abs" style="left:${x - 95}px;top:${y - 95}px;width:190px;height:190px;border-radius:50%;background:#fff;box-shadow:var(--shadow);display:grid;place-items:center;font-size:88px">${t.e}</div>
        <div class="abs bname" style="left:${x - 120}px;width:240px;top:${y + 104}px;font-size:26px">${t.n}</div>`; }).join('');
    return `${K.blobs(w, h, 0)}
      <div class="abs" style="left:72px;top:150px">${K.logo(44)}</div>
      <div class="abs" style="left:72px;right:72px;top:250px;text-align:center">
        <div class="hd" style="font-size:112px">Milyen <span class="it">gazdi</span> vagy?</div>
        <div class="body-l" style="margin-top:24px;font-size:38px">Tippelj, aztán töltsd ki a kvízt!</div></div>
      ${ring}
      ${K.bub('kabala-pacsi', w / 2, 940, 250, { z: 3 })}
      <div class="abs" style="left:72px;right:72px;top:1480px;text-align:center;font:700 30px/1.35 var(--font-u);color:var(--ink-2)">10 kérdés · 1 perc · a végén a te top 5 fajtád</div>`;
  },

  /* ---------- E1 · Profilkép ---------- */
  avatar({ w, h }) {
    const d = w * .8;
    return `<div class="bgl" style="background:radial-gradient(circle at 30% 25%, #FF8A5C, #EE5A2C 70%)"></div>
      <div class="abs" style="left:${(w - d) / 2 - 18}px;top:${(h - d) / 2 - 18}px;width:${d + 36}px;height:${d + 36}px;border-radius:50%;background:#FFFDF9;box-shadow:0 20px 50px rgba(120,40,10,.35)"></div>
      <div class="abs" style="left:${(w - d) / 2}px;top:${(h - d) / 2}px;width:${d}px;height:${d}px;border-radius:50%;overflow:hidden;background:#FEF9EC">
        <img src="${K.kv('kv_mascot_wave')}" style="position:absolute;width:${d * 1536 / 1100}px;left:${-d * 225 / 1100}px;top:${-d * 290 / 1100}px"></div>`;
  },

  /* ---------- E2 · Facebook-borító ---------- */
  fb_cover({ w, h }) {
    const iw = 1480, ih = iw / 3;
    return `<div class="bgl" style="background:#FEF9EC"></div>
      <img class="kv" src="${K.kv('kv_lineup')}" style="left:${(w - iw) / 2}px;top:${h - ih + 30}px;width:${iw}px;height:${ih}px">
      <div class="abs" style="left:0;right:0;top:46px;text-align:center">${K.logo(70)}
        <div style="font:700 30px/1 var(--font-u);color:var(--ink-2);margin-top:18px">Találd meg a hozzád illő kutyát · 124 fajta egy élő felhőben</div></div>`;
  },

  /* ---------- E3 · LinkedIn-borító ---------- */
  li_banner({ w, h }) {
    const ih = 340, iw = ih * 3;
    return `<div class="bgl" style="background:#FEF9EC"></div>
      <img class="kv" src="${K.kv('kv_lineup')}" style="left:${w - iw - 16}px;top:${h - ih + 24}px;width:${iw}px;height:${ih}px">
      <div class="abs" style="left:56px;top:54px;width:520px">${K.logo(62)}
        <div style="font:700 26px/1.35 var(--font-u);color:var(--ink-2);margin-top:20px">Vizuális kutyafajta-választó<br>124 fajta · kvíz · összehasonlítás</div></div>`;
  },

  /* ---------- E5 · YouTube-szalagcím (2560×1440; minden eszközön látszó biztonságos sáv: középen 1546×423) ---------- */
  yt_banner({ w, h }) {
    const sx = (w - 1546) / 2, sy = (h - 423) / 2, lw = 1080, lh = lw / 3;
    const deco = pickIds(18).map((id, i) => ({ id, d: [150, 120, 104, 92][i % 4] }));
    K.pack(deco.slice(0, 9), { cx: 330, cy: h / 2, gap: 14, ax: .8, ay: 2.2, seed: 3 });
    K.pack(deco.slice(9), { cx: w - 330, cy: h / 2, gap: 14, ax: .8, ay: 2.2, seed: 7 });
    return `<div class="bgl" style="background:#FEF9EC"></div>${K.blobs(w, h, 1)}
      ${deco.map(it => K.bub(it.id, it.x, it.y, it.d, { z: 1, op: .95 })).join('')}
      <div class="abs" style="left:${sx}px;top:${sy}px;width:1546px;height:423px;border-radius:40px;background:rgba(254,249,236,.92);z-index:2"></div>
      <img class="kv" src="${K.kv('kv_lineup')}" style="left:${sx + 1546 - lw - 10}px;top:${sy + (423 - lh) / 2 + 8}px;width:${lw}px;height:${lh}px;z-index:3">
      <div class="abs" style="left:${sx + 50}px;top:${sy + 70}px;width:470px;z-index:4">${K.logo(92)}
        <div style="font:700 34px/1.3 var(--font-u);color:var(--ink-2);margin-top:26px">Találd meg a hozzád illő kutyát</div>
        <div style="margin-top:22px"><span class="tag hot" style="font-size:30px">${K.ic('paw', 28)} ${K.site}</span></div></div>`;
  },

  /* ---------- E6 · LinkedIn céges oldal borítója (1128×191; a logó a bal alsó sarokra lóg) ---------- */
  li_cover({ w, h }) {
    const lh = h - 8, lw = lh * 3;
    return `<div class="bgl" style="background:#FEF9EC"></div>${K.blobs(w, h, 2)}
      <img class="kv" src="${K.kv('kv_lineup')}" style="left:${w - lw + 20}px;top:${h - lh + 6}px;width:${lw}px;height:${lh}px">
      <div class="abs" style="left:250px;top:38px;width:330px">
        <div style="font:800 30px/1.1 var(--font-d);font-variation-settings:'SOFT' 100,'opsz' 72;letter-spacing:-.02em;color:var(--ink)">Találd meg a hozzád <span class="it">illő kutyát</span></div>
        <div style="font:700 15px/1.3 var(--font-u);color:var(--ink-2);margin-top:10px">124 fajta · Párkereső kvíz · ${K.site}</div></div>`;
  },

  /* ---------- E4 · Linkelőnézet (Open Graph) ---------- */
  og({ w, h }) {
    const items = pickIds(16, ['cavalier-king-charles-spaniel']).map((id, i) => ({ id, d: [120, 96, 84, 76][i % 4] }));
    K.pack(items, { cx: 930, cy: 330, gap: 10, ax: 1.1 });
    return `${K.blobs(w, h, 0)}
      ${items.map(it => K.bub(it.id, it.x, it.y, it.d, { z: 1 })).join('')}
      <div class="abs" style="left:640px;top:0;width:560px;height:100%;background:linear-gradient(90deg,rgba(251,246,238,.0),rgba(251,246,238,0))"></div>
      <div class="abs" style="left:0;top:0;width:640px;height:100%;background:linear-gradient(90deg,rgba(251,246,238,.96) 70%,rgba(251,246,238,0))"></div>
      <div class="abs" style="left:64px;top:70px;width:560px">${K.logo(52)}
        <div class="hd" style="font-size:78px;margin-top:40px">Melyik kutya illik <span class="it">hozzád?</span></div>
        <div class="body-m" style="margin-top:22px;font-size:28px;max-width:520px">124 kutyafajta egy élő felhőben: szűrők, párkereső kvíz, összehasonlítás. Ingyenes.</div>
        <div style="margin-top:30px"><span class="cta" style="font-size:32px;padding:16px 32px 16px 26px;gap:12px">${K.ic('paw', 32)} ${K.site}</span></div></div>`;
  },

  /* ---------- F1 · Hirdetés: portréfelhő + kvíz ---------- */
  ad_a({ w, h }) {
    const items = pickIds(34).map((id, i) => ({ id, d: [170, 140, 118, 104, 96][i % 5] }));
    K.pack(items, { cx: w / 2, cy: 720, gap: 12, ax: 1.35, ay: .85, seed: 2 });
    return `${K.blobs(w, h, 1)}
      ${items.map(it => K.bub(it.id, it.x, it.y, it.d, { z: 1 })).join('')}
      <div class="card-w" style="left:90px;right:90px;top:70px;padding:40px 48px 44px;text-align:center;z-index:5">
        <div class="hd" style="font-size:78px">Melyik kutya illik <span class="it">hozzád?</span></div>
        <div class="body-m" style="margin-top:16px">Derítsd ki 1 perc alatt – 124 fajta közül.</div>
        <div style="margin-top:28px"><span class="cta" style="font-size:34px;padding:20px 38px">${K.ic('sparkle', 34)} Párkereső kvíz</span></div>
      </div>
      <div class="abs" style="left:0;right:0;bottom:44px;text-align:center;z-index:5"><span class="tag" style="font-size:28px">${K.logo(34, { by: true })}</span></div>`;
  },

  /* ---------- F2 · Hirdetés: ne a legcukibbat ---------- */
  ad_b({ w, h }) {
    const fs = ['gyerek', 'lakas', 'csendes'];
    const cand = [['pomeraniai-torpespicc', 250], ['cavalier-king-charles-spaniel', 300], ['coton-de-tulear', 250]];
    const xs = [220, 540, 860];
    const cells = cand.map(([id, d], i) => {
      const m = match(id, fs), good = m >= 80;
      return K.bub(id, xs[i], 560, d, { ring: m, z: 2 }) +
        `<div class="abs" style="left:${xs[i] - 90}px;top:${560 + d / 2 + 34}px;width:180px;text-align:center"><span class="tag ${good ? 'hot' : ''}" style="font-size:30px;padding:10px 20px">${m}%</span></div>
         <div class="abs bname" style="left:${xs[i] - 150}px;width:300px;top:${560 + d / 2 + 104}px;font-size:26px">${K.esc(sname(id))}</div>`;
    }).join('');
    return `${K.blobs(w, h, 2)}
      <div class="abs" style="left:64px;right:64px;top:64px;text-align:center">
        <div class="hd" style="font-size:80px">Ne a legcukibbat válaszd. <span class="it">A hozzád illőt.</span></div></div>
      <div class="abs" style="left:0;right:0;top:318px;text-align:center"><span class="tag ink" style="font-size:26px">${K.ic('kid', 26)} Kisgyerek · ${K.ic('home', 26)} lakás · ${K.ic('quiet', 26)} vékony falak</span></div>
      ${cells}
      <div class="abs" style="left:0;right:0;bottom:60px;text-align:center">${K.logo(40)}<div class="url" style="margin-top:14px;font-size:26px">Mindegyik fajtára kiszámolja, mennyire illik hozzád.</div></div>`;
  },

  /* ---------- F3 · Story-hirdetés: kvíz ---------- */
  ad_story({ w, h }) {
    return `${K.blobs(w, h, 0)}
      <div class="abs" style="left:72px;top:160px">${K.logo(46)}</div>
      <div class="abs" style="left:72px;right:72px;top:260px">
        <div class="hd" style="font-size:122px;line-height:.98">124 fajta.<br>10 kérdés.<br><span class="it">1 perc.</span></div></div>
      ${K.phone(K.screen('m_quiz_result'), { x: 420, y: 700, sw: 430, rot: 4 })}
      <div class="abs" style="left:60px;top:1030px;z-index:5;display:flex;flex-direction:column;gap:20px;align-items:flex-start">
        <span class="tag" style="font-size:30px">🏙️ Városi flâneur</span><span class="tag" style="font-size:30px;margin-left:30px">Top 5 fajta</span></div>
      <div class="abs" style="left:0;right:0;top:1560px;text-align:center;z-index:5"><span class="cta" style="font-size:40px">${K.ic('sparkle', 38)} Töltsd ki a kvízt</span></div>`;
  },

  /* ---------- L1 · LinkedIn: termékbemutató (DarwinAI) ---------- */
  li_ux({ w, h }) {
    const stats = [['124', 'kutyafajta'], ['9', 'jellemző fajtánként'], ['10', 'kérdéses kvíz'], ['0', 'regisztráció, süti']];
    return `${K.blobs(w, h, 1)}
      <div class="abs" style="left:64px;right:64px;top:70px">
        <div class="row" style="justify-content:space-between"><div class="kicker">DarwinAI · Termékbemutató</div>${K.logo(40)}</div>
        <div class="hd" style="font-size:88px;margin-top:22px">Amikor a döntéstámogatás <span class="it">élmény</span></div>
        <div class="body-m" style="margin-top:20px">Szűrés helyett élő felhő: a fajták fizikailag reagálnak minden döntésre.</div></div>
      ${K.laptop(K.screen('d_rank'), { x: (w - 820 * 1.044) / 2, y: 476, w: 820 })}
      <div class="abs" style="left:64px;right:64px;bottom:56px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px">
        ${stats.map(([n, t]) => `<div style="background:#FFFDF9;border-radius:26px;padding:22px 20px;box-shadow:var(--shadow)"><div class="hd" style="font-size:66px;color:var(--primary-fill)">${n}</div><div style="font:700 22px/1.25 var(--font-u);color:var(--ink-2);margin-top:6px">${t}</div></div>`).join('')}
      </div>`;
  },

  /* ---------- L2 · LinkedIn: partnerkeresés ---------- */
  li_partner({ w, h }) {
    const ih = 400, iw = ih * 3;
    return `<div class="bgl" style="background:#FEF9EC"></div>
      <img class="kv" src="${K.kv('kv_lineup')}" style="left:${(w - iw) / 2}px;top:${h - ih + 16}px;width:${iw}px;height:${ih}px">
      <div class="abs" style="left:64px;right:64px;top:48px;text-align:center">
        <div class="kicker" style="font-size:22px">Partnerséget keresünk</div>
        <div class="hd" style="font-size:62px;margin-top:16px">Kutyás márka vagy? Legyél a Pacsi <span class="it">alapító partnere.</span></div>
      </div>`;
  },
};

/** felhő-töltelék a CLOUD listából, a kihagyandók nélkül */
function pickIds(n, skip = []) {
  const pri = CLOUD.filter(id => K.by[id] && !skip.includes(id));
  const rest = K.data.breeds.map(b => b.id).filter(id => !pri.includes(id) && !skip.includes(id));
  return [...pri, ...rest].slice(0, n);
}
