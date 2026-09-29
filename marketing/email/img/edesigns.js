/* Pacsi eDM – a hírlevelek fejlécképei (1200×600, 2:1). A levél címe HTML-szöveg, ezért a képen csak kevés,
   rövid felirat van (matrica, chip) – a kép képblokkolásnál vagy sötét módban is értelmes marad.
   Építőkockák: marketing/social/shared/kit.js (K), közös stílus: brand.css + designs.css. */
const HU9E = ['puli', 'pumi', 'mudi', 'komondor', 'kuvasz', 'erdelyi-kopo', 'magyar-vizsla', 'drotszoru-magyar-vizsla', 'magyar-agar'];
const SHORTE = { 'magyar-vizsla': 'Rövidszőrű vizsla', 'drotszoru-magyar-vizsla': 'Drótszőrű vizsla', 'erdelyi-kopo': 'Erdélyi kopó', 'magyar-agar': 'Magyar agár',
  'cavalier-king-charles-spaniel': 'Cavalier', 'golden-retriever': 'Golden retriever', 'labrador-retriever': 'Labrador', 'bichon-frise': 'Bichon frisé',
  'lagotto-romagnolo': 'Lagotto', 'portugal-vizikutya': 'Portugál vízikutya', 'tibeti-terrier': 'Tibeti terrier', 'francia-bulldog': 'Francia bulldog',
  'angol-bulldog': 'Angol bulldog', 'boston-terrier': 'Boston terrier', 'pekingi-palotakutya': 'Pekingi', 'shih-tzu': 'Shih tzu' };
const snameE = id => SHORTE[id] || K.name(id);
const FILL = ['cavalier-king-charles-spaniel', 'golden-retriever', 'puli', 'border-collie', 'mopsz', 'beagle', 'shiba-inu', 'szamojed', 'tacsko', 'whippet',
  'francia-bulldog', 'mudi', 'bernathegyi', 'uszkar', 'komondor', 'sziberiai-husky', 'dalmata', 'basenji', 'welsh-corgi-pembroke', 'magyar-vizsla', 'havanese'];

/** kulcsvizuál a jobb oldalon, balra elhalványuló szélű maszkkal (nincs éles képhatár) */
const kvRight = (name, { s, x, y, fade = 22 }) => `<img class="kv" src="${K.kv(name)}" style="left:${x}px;top:${y}px;width:${s.w}px;height:${s.h}px;
  -webkit-mask-image:linear-gradient(90deg,transparent 0,#000 ${fade}%);mask-image:linear-gradient(90deg,transparent 0,#000 ${fade}%)">`;

/** buborékfelhő egy téglalapban (determinisztikus) */
function cloud(ids, { cx, cy, sizes = [150, 118, 100, 88, 78], ax = 1.3, ay = .8, gap = 12, ring = [] } = {}) {
  const items = ids.map((id, i) => ({ id, d: sizes[i % sizes.length] }));
  K.pack(items, { cx, cy, gap, ax, ay });
  return items.map((it, i) => K.bub(it.id, it.x, it.y, it.d, { z: 2 + (i < 3 ? 2 : 0), ring: ring.includes(it.id) ? true : 0 })).join('');
}

/** sor-elrendezés névvel: ids középre igazítva, d átmérővel */
function row(ids, { y, d, gap, w, cx = w / 2, names = true, ring = 0, fs = 22 }) {
  const tot = ids.length * d + (ids.length - 1) * gap, x0 = cx - tot / 2 + d / 2;
  return ids.map((id, i) => {
    const x = x0 + i * (d + gap);
    return K.bub(id, x, y, d, { z: 3, ring }) + (names ? `<div class="abs bname" style="left:${x - 110}px;width:220px;top:${y + d / 2 + 16}px;font-size:${fs}px">${K.esc(snameE(id))}</div>` : '');
  }).join('');
}

/** chipek függőleges oszlopa a kép jobb harmadában, enyhe döntéssel */
const chipCol = chips => `<div class="abs" style="left:820px;top:0;height:600px;display:flex;flex-direction:column;justify-content:center;gap:30px;align-items:flex-start;z-index:9">
  ${chips.map((c, i) => `<span style="display:inline-block;transform:rotate(${[-3, 2.5, -1.5][i % 3]}deg);margin-left:${[0, 34, 12][i % 3]}px">${c}</span>`).join('')}</div>`;

const EDESIGNS = {
  /* L1 – indulás: pacsi a kabalával + portréfelhő */
  e_launch({ w, h }) {
    const S = 880;
    return `<div class="bgl" style="background:#FCF7EC"></div>${K.blobs(w, h, 1)}
      ${kvRight('kv_pacsi_highfive', { s: { w: S, h: S }, x: w - S + 10, y: -S * .26, fade: 26 })}
      ${cloud(['golden-retriever', 'puli', 'francia-bulldog', 'border-collie', 'cavalier-king-charles-spaniel', 'magyar-vizsla', 'beagle', 'szamojed', 'tacsko', 'mopsz', 'uszkar', 'shiba-inu'],
        { cx: 250, cy: 300, sizes: [140, 112, 96, 84, 74], ax: 1.25, ay: 1.05, ring: ['golden-retriever'] })}
      ${K.dots(14, { x0: 30, y0: 30, w: 520, h: 540, seed: 5, rmin: 4, rmax: 9 })}
      <div class="abs" style="left:48px;top:44px;z-index:9"><span class="tag hot" style="font-size:26px;transform:rotate(-4deg);display:inline-flex">124 fajta · 1 perc</span></div>
      <div class="abs" style="left:56px;bottom:40px;z-index:9">${K.logo(40)}</div>`;
  },

  /* L2 – a 9 magyar fajta */
  e_hu9({ w, h }) {
    const d = 150;
    return `${K.blobs(w, h, 2)}
      <div class="abs" style="left:0;right:0;top:34px;text-align:center;z-index:5"><div class="row" style="justify-content:center;gap:16px">
        <span class="tricolor"><i></i><i></i><i></i></span><span class="kicker" style="font-size:24px">Magyar büszkeségek</span><span class="tricolor"><i></i><i></i><i></i></span></div></div>
      ${row(HU9E.slice(0, 5), { y: 188, d, gap: 64, w })}
      ${row(HU9E.slice(5), { y: 420, d, gap: 64, w })}
      ${K.dots(12, { x0: 20, y0: 20, w: 1160, h: 560, seed: 9, rmin: 4, rmax: 8 })}`;
  },

  /* L3 / WLC2 – a 6 gazditípus */
  e_quiz({ w, h }) {
    const TY = [
      { e: '🛋️', n: 'Kanapé-kapitány', c: '#FFD9C2', ids: ['mopsz', 'shih-tzu'] },
      { e: '🏃', n: 'Aktív kalandor', c: '#CDEFE0', ids: ['magyar-vizsla', 'border-collie'] },
      { e: '👨‍👩‍👧', n: 'Családi karmester', c: '#FFE6A0', ids: ['golden-retriever', 'labrador-retriever'] },
      { e: '🏙️', n: 'Városi flâneur', c: '#E2D6FF', ids: ['whippet', 'francia-bulldog'] },
      { e: '🛡️', n: 'Tanyasi őrangyal', c: '#BFDDF7', ids: ['komondor', 'kuvasz'] },
      { e: '🎓', n: 'Kutyasuttogó', c: '#FFC8D6', ids: ['malinois', 'nemet-juhaszkutya'] },
    ];
    const cw = 336, ch = 226, gx = 26, gy = 26, x0 = (w - 3 * cw - 2 * gx) / 2, y0 = (h - 2 * ch - gy) / 2 + 14;
    const cards = TY.map((t, i) => {
      const x = x0 + (i % 3) * (cw + gx), y = y0 + Math.floor(i / 3) * (ch + gy), rot = [-2, 1.5, -1, 1, -1.5, 2][i];
      return `<div class="card-w" style="left:${x}px;top:${y}px;width:${cw}px;height:${ch}px;border-radius:30px;overflow:hidden;transform:rotate(${rot}deg)">
        <div class="abs" style="left:0;top:0;right:0;height:10px;background:${t.c}"></div>
        <div class="abs" style="left:24px;top:30px;font-size:56px;line-height:1">${t.e}</div>
        <div class="abs hd" style="left:24px;right:20px;bottom:30px;font-size:36px;letter-spacing:-.02em">${t.n}</div>
        ${K.bub(t.ids[0], cw - 104, 70, 80, { z: 3 })}${K.bub(t.ids[1], cw - 44, 86, 62, { z: 2 })}</div>`;
    }).join('');
    return `${K.blobs(w, h, 0)}${cards}
      <div class="abs" style="left:${w / 2 - 44}px;top:${h / 2 - 30}px;z-index:9"><span class="tag hot" style="font-size:40px;width:88px;height:88px;justify-content:center;padding:0;border-radius:50%">?</span></div>`;
  },

  /* W01 – kezdőbarát fajták: rács balra, chipek jobbra */
  e_first({ w, h }) {
    const ids = ['golden-retriever', 'labrador-retriever', 'cavalier-king-charles-spaniel', 'havanese', 'uszkar', 'bichon-frise'];
    return `${K.blobs(w, h, 0)}
      ${row(ids.slice(0, 3), { y: 178, d: 168, gap: 64, w, cx: 470, ring: true })}
      ${row(ids.slice(3), { y: 430, d: 148, gap: 84, w, cx: 470 })}
      ${chipCol([K.chip('sprout', 'Kezdő gazdinak', { size: .9 }), K.chip('cap', 'Könnyen tanul', { size: .8 }), K.chip('heart', 'Türelmes', { size: .8, on: false })])}
      ${K.dots(12, { x0: 20, y0: 20, w: 1160, h: 560, seed: 3, rmin: 4, rmax: 8 })}`;
  },

  /* W05 – alig hulló fajták */
  e_lowshed({ w, h }) {
    const ids = ['uszkar', 'bichon-frise', 'lagotto-romagnolo', 'portugal-vizikutya', 'havanese', 'tibeti-terrier'];
    return `<div class="bgl" style="background:#F6F2FF"></div>${K.blobs(w, h, 2)}
      ${row(ids.slice(0, 3), { y: 178, d: 164, gap: 66, w, cx: 470 })}
      ${row(ids.slice(3), { y: 430, d: 148, gap: 84, w, cx: 470 })}
      ${chipCol([K.chip('feather', 'Kevés szőrhullás', { size: .9 }), `<span class="tag" style="font-size:28px">🤧 → 🙂</span>`, K.chip('comb', 'Rendszeres fésülés', { size: .78, on: false })])}
      ${K.dots(12, { x0: 20, y0: 20, w: 1160, h: 560, seed: 11, rmin: 4, rmax: 8 })}`;
  },

  /* W07 – lapos orrú fajták */
  e_brachy({ w, h }) {
    const ids = ['francia-bulldog', 'mopsz', 'angol-bulldog', 'boston-terrier', 'shih-tzu', 'pekingi-palotakutya'];
    return `${K.blobs(w, h, 1)}
      ${row(ids.slice(0, 3), { y: 178, d: 164, gap: 66, w, cx: 470 })}
      ${row(ids.slice(3), { y: 430, d: 148, gap: 84, w, cx: 470 })}
      ${chipCol([`<span class="tag hot" style="font-size:28px">Lapos orr, nagy szív ♥</span>`, K.chip('nose', 'Figyelj a légzésre', { size: .8, on: false }), K.chip('sun', 'Hőségben óvatosan', { size: .8, on: false })])}
      ${K.dots(12, { x0: 20, y0: 20, w: 1160, h: 560, seed: 7, rmin: 4, rmax: 8 })}`;
  },

  /* WLC1 – üdvözlés: integető kabala */
  e_welcome({ w, h }) {
    const S = { w: 600, h: 800 };
    return `<div class="bgl" style="background:#FCF7EC"></div>${K.blobs(w, h, 0)}
      ${kvRight('kv_mascot_wave', { s: S, x: w - S.w + 20, y: -150, fade: 18 })}
      ${cloud(['cavalier-king-charles-spaniel', 'puli', 'golden-retriever', 'francia-bulldog', 'border-collie', 'magyar-vizsla', 'beagle', 'szamojed', 'tacsko', 'havanese', 'mudi'],
        { cx: 300, cy: 320, sizes: [136, 110, 94, 82, 72], ax: 1.35, ay: 1.05 })}
      ${K.dots(14, { x0: 30, y0: 30, w: 600, h: 540, seed: 13, rmin: 4, rmax: 9 })}
      <div class="abs" style="left:48px;top:44px;z-index:9"><span class="tag hot" style="font-size:28px;transform:rotate(-4deg);display:inline-flex">Üdv a falkában!</span></div>
      <div class="abs" style="left:56px;bottom:40px;z-index:9">${K.logo(40)}</div>`;
  },

  /* WLC3 – felelős választás: fajtakártya + szűrőchipek */
  e_responsible({ w, h }) {
    return `${K.blobs(w, h, 2)}
      ${K.phone(K.screen('m_card_vizsla'), { x: 700, y: 36, sw: 250, rot: 6 })}
      <div class="abs" style="left:70px;top:120px;display:flex;flex-direction:column;gap:22px;align-items:flex-start;z-index:5">
        <span style="transform:rotate(-3deg)">${K.chip('home', 'Lakásba való', { size: .95 })}</span>
        <span style="transform:rotate(2deg);margin-left:40px">${K.chip('kid', 'Gyerekbarát', { size: .95 })}</span>
        <span style="transform:rotate(-2deg);margin-left:10px">${K.chip('quiet', 'Csendes', { size: .95 })}</span>
        <span style="transform:rotate(2deg);margin-left:56px">${K.chip('bolt', 'Energia: Mérsékelt', { size: .95, on: false })}</span>
      </div>
      <div class="abs" style="left:64px;top:40px;z-index:6"><span class="tag ink" style="font-size:24px">Ne a legcukibbat – azt, aki illik hozzád</span></div>
      ${K.bub('magyar-vizsla', 1080, 470, 120, { z: 4, ring: true })}${K.bub('mopsz', 600, 500, 92, { z: 4 })}
      ${K.dots(10, { x0: 20, y0: 20, w: 1160, h: 560, seed: 17, rmin: 4, rmax: 8 })}`;
  },

  /* P1 – partnerlevél: kutyasor */
  e_partner({ w, h }) {
    const iw = 1260, ih = iw / 3;
    return `<div class="bgl" style="background:#FEF9EC"></div>
      <img class="kv" src="${K.kv('kv_lineup')}" style="left:${(w - iw) / 2}px;top:${h - ih + 16}px;width:${iw}px;height:${ih}px">
      <div class="abs" style="left:0;right:0;top:44px;text-align:center">${K.logo(58)}
        <div style="margin-top:22px"><span class="tag" style="font-size:24px">🐾 Partnereknek · fajtaklubok · menhelyek · iskolák · állatorvosok</span></div></div>
      ${K.dots(10, { x0: 20, y0: 20, w: 1160, h: 200, seed: 21, rmin: 4, rmax: 8 })}`;
  },

  /* P2 – partnerlevél: statisztika – telefon + szűrők */
  e_partner_stats({ w, h }) {
    return `${K.blobs(w, h, 1)}
      ${K.phone(K.screen('m_filtered'), { x: 470, y: 26, sw: 250, rot: -4 })}
      <div class="abs" style="left:70px;top:90px;display:flex;flex-direction:column;gap:22px;align-items:flex-start;z-index:5">
        <span style="transform:rotate(-3deg)">${K.chip('kid', 'Gyerekbarát', { size: .9 })}</span>
        <span style="transform:rotate(2deg);margin-left:30px">${K.chip('home', 'Lakásba való', { size: .9 })}</span>
        <span style="transform:rotate(-2deg);margin-left:6px">${K.chip('feather', 'Kevés szőrhullás', { size: .9 })}</span>
      </div>
      <div class="abs" style="left:820px;top:110px;display:flex;flex-direction:column;gap:26px;align-items:flex-start;z-index:5">
        <span class="tag hot" style="font-size:30px;transform:rotate(3deg)">📊 Mit keresnek?</span>
        <span class="tag" style="font-size:26px;transform:rotate(-2deg)">❤️ Kedvenc fajták</span>
        <span class="tag" style="font-size:26px;transform:rotate(2deg)">🔎 Népszerű szűrők</span>
      </div>
      ${K.bub('golden-retriever', 960, 480, 110, { z: 4, ring: true })}${K.bub('puli', 1090, 430, 84, { z: 4 })}
      ${K.dots(10, { x0: 20, y0: 20, w: 1160, h: 560, seed: 23, rmin: 4, rmax: 8 })}`;
  },
};
