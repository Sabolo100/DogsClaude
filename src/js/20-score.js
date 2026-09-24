/* ==========================================================================
   Szűrők, pontozás, kvíz
   ========================================================================== */
const SIZES = [['toy', 'Toy'], ['kicsi', 'Kicsi'], ['kozepes', 'Közepes'], ['nagy', 'Nagy'], ['orias', 'Óriás']];
const SIZE_I = Object.fromEntries(SIZES.map(([k], i) => [k, i]));
const SIZE_L = Object.fromEntries(SIZES);
const COATS = [['rovid', 'Rövid'], ['kozepes', 'Közepes'], ['hosszu', 'Hosszú'], ['drot', 'Drótszőrű'], ['gondor', 'Göndör'], ['zsinoros', 'Zsinóros'], ['szortelen', 'Szőrtelen']];
const COAT_L = Object.fromEntries(COATS);
const ROLES = [['CSA', 'Családi társ'], ['VAR', 'Városi társ'], ['PAS', 'Pásztor'], ['ORZ', 'Őrző'], ['VAD', 'Vadász'], ['SPO', 'Sport'], ['MUN', 'Munka'], ['ESZ', 'Északi']];
const ROLE_L = Object.fromEntries(ROLES);
const ROLE_C = { CSA: '#FF6B3D', VAR: '#E86A92', PAS: '#17756E', ORZ: '#5B5BD6', VAD: '#C7772B', SPO: '#2FA3D6', MUN: '#6E7B8B', ESZ: '#5AB0F0' };
const ENERGY = [['nyugis', 'Nyugis', 1.5], ['mersekelt', 'Mérsékelt', 3], ['sportos', 'Sportos', 4.6]];
const FCI = { 1: 'Juhász- és pásztorkutyák', 2: 'Pinscherek, molosszerek', 3: 'Terrierek', 4: 'Tacskók', 5: 'Spiccek, ősi típusok', 6: 'Kopók', 7: 'Vizslák', 8: 'Retrieverek, spánielek', 9: 'Társasági kutyák', 10: 'Agarak' };
const SC = [0, 0, .15, .5, .85, 1];

/* Kapcsoló típusú szűrők (8.1 fejezet) */
const TOGGLES = [
  { id: 'gyerek', l: 'Gyerekbarát', s: 'Gyerek', i: 'kid', c: '#FFD9C2', g: 'eletmod', sub: 'Türelmes a gyerekekkel', score: b => SC[b.t.Gy], pass: b => b.t.Gy >= 4, why: ['Gyerekbarát', 'Gyerekekkel óvatosan'] },
  { id: 'lakas', l: 'Lakásba való', s: 'Lakás', i: 'home', c: '#CFE6FA', g: 'eletmod', sub: 'Városi lakásban is jól elvan', score: b => SC[b.t.L], pass: b => b.t.L >= 4, why: ['Lakásba való', 'Inkább kertes házba illik'] },
  { id: 'kezdo', l: 'Kezdő gazdinak', s: 'Kezdő', i: 'sprout', c: '#E5F2C4', g: 'eletmod', sub: 'Első kutyának is jó választás', score: b => SC[b.t.K], pass: b => b.t.K >= 4, why: ['Kezdőknek is jó', 'Tapasztalt gazdit igényel'] },
  { id: 'csendes', l: 'Csendes', s: 'Csendes', i: 'quiet', c: '#E2D9FF', g: 'eletmod', sub: 'Ritkán ugat', score: b => SC[6 - b.t.U], pass: b => b.t.U <= 2, why: ['Csendes', 'Hangos lehet'] },
  { id: 'orzo', l: 'Őrző típus', s: 'Őrző', i: 'shield', c: '#D6CCFF', g: 'eletmod', sub: 'Éber, védi a házat', score: b => SC[b.t.O], pass: b => b.t.O >= 4, why: ['Jó házőrző', 'Nem kifejezetten őrző'] },
  { id: 'hullas', l: 'Kevés szőrhullás', s: 'Hullás', i: 'feather', c: '#FFE6A0', g: 'gondozas', sub: 'Allergiásoknak barátságosabb', score: b => SC[6 - b.t.H], pass: b => b.t.H <= 2, why: ['Kevés szőrt hullat', 'Sokat hullat'] },
  { id: 'apolas', l: 'Kevés ápolás', s: 'Ápolás', i: 'comb', c: '#FFC8D6', g: 'gondozas', sub: 'Nem kell sokat fésülni', score: b => SC[6 - b.t.A], pass: b => b.t.A <= 2, why: ['Könnyen ápolható', 'Rendszeres ápolást igényel'] },
  { id: 'tanul', l: 'Könnyen tanul', s: 'Tanul', i: 'cap', c: '#BDE8D3', g: 'gondozas', sub: 'Jól idomítható', score: b => SC[b.t.I], pass: b => b.t.I >= 4, why: ['Könnyen tanul', 'Önálló, makacs lehet'] },
  { id: 'nyal', l: 'Nem nyáladzik', s: 'Nyál', i: 'drop', c: '#BFDDF7', g: 'gondozas', sub: 'Nincs nyálcsík a nadrágon', score: b => b.nyal ? 0 : 1, pass: b => !b.nyal, why: ['Nem nyáladzik', 'Erősen nyáladzik'] },
  { id: 'elet', l: 'Hosszú életű', s: 'Élet', i: 'pulse', c: '#FFC8D6', g: 'egeszseg', sub: 'Várhatóan 14+ év', score: b => clamp((b.elet[1] - 9) / 8, 0, 1), pass: b => b.elet[1] >= 14, why: ['Hosszú életű', 'Rövidebb élettartam'] },
  { id: 'legzes', l: 'Könnyű légzés', s: 'Légzés', i: 'nose', c: '#DDEDB2', g: 'egeszseg', sub: 'Nem lapos orrú fajta', score: b => [1, .4, 0][b.brachy], pass: b => !b.brachy, why: ['Nem lapos orrú', 'Lapos orrú – légzési kockázat'] },
  { id: 'magyar', l: 'Magyar fajta', s: 'Magyar', i: 'flag', c: '#fff', g: 'kulonleges', sub: 'A 9 magyar kutyafajta', score: b => b.hu ? 1 : 0, pass: b => b.hu, why: ['Magyar fajta', 'Nem magyar fajta'] },
];
const TBY = Object.fromEntries(TOGGLES.map(t => [t.id, t]));

const setCrit = (key, set, labels, adj) => ({
  key, w: 1,
  label: [...set].map(v => labels[v]).join(', '),
  score: b => {
    const vals = key === 'fci' ? [b.fci] : b[key];
    if (vals.some(v => set.has(v))) return 1;
    if (adj && vals.some(v => [...set].some(s => Math.abs(SIZE_I[s] - SIZE_I[v]) === 1))) return .5;
    return 0;
  },
  pass: b => (key === 'fci' ? [b.fci] : b[key]).some(v => set.has(v)),
  why: [key === 'meret' ? 'Megfelelő méret' : key === 'szor' ? 'Megfelelő szőrzet' : key === 'szerep' ? 'Megfelelő szerep' : 'Megfelelő FCI-csoport',
    key === 'meret' ? 'Más méretű' : key === 'szor' ? 'Más szőrzetű' : key === 'szerep' ? 'Más a szerepe' : 'Más FCI-csoport'],
});
const energyCrit = (target, w = 1, src) => ({
  key: src ? 'q-E' : 'energia', w, src, label: ENERGY.find(e => e[2] === target)?.[1] || 'Energia',
  score: b => clamp(1 - Math.abs(b.t.E - target) / 3, 0, 1),
  pass: b => target < 2 ? b.t.E <= 2 : target > 4 ? b.t.E >= 4 : b.t.E === 3,
  why: ['Megfelelő energiaszint', b => b.t.E > target ? 'Több mozgást igényel' : 'Nyugisabb, mint szeretnéd'],
});

/* Kritériumlista a szűrőállapotból (+ kvíz) */
function buildCrit(f = S.f, withQuiz = true) {
  const out = [];
  if (f.meret.size) out.push({ ...setCrit('meret', f.meret, SIZE_L, true), label: 'Méret: ' + [...f.meret].map(v => SIZE_L[v]).join(', ') });
  if (f.szor.size) out.push({ ...setCrit('szor', f.szor, COAT_L), label: 'Szőr: ' + [...f.szor].map(v => COAT_L[v]).join(', ') });
  if (f.szerep.size) out.push({ ...setCrit('szerep', f.szerep, ROLE_L), label: [...f.szerep].map(v => ROLE_L[v]).join(', ') });
  if (f.fci.size) out.push({ ...setCrit('fci', f.fci, Object.fromEntries(Object.keys(FCI).map(k => [k, 'FCI ' + k]))), label: 'FCI ' + [...f.fci].sort((a, b) => a - b).join(', ') });
  if (f.energia) out.push(energyCrit(ENERGY.find(e => e[0] === f.energia)[2]));
  for (const t of TOGGLES) if (f.t.has(t.id)) out.push({ key: t.id, label: t.l, w: 1, score: t.score, pass: t.pass, why: t.why });
  if (withQuiz && S.quiz) out.push(...S.quiz.crit);
  return out;
}

/* Kiértékelés: b.m = illeszkedés 0–1 (null, ha nincs szűrő), b.ok = minden feltétel teljesül */
function evaluate() {
  const crit = S.crit = buildCrit();
  for (const b of BREEDS) {
    if (!crit.length) { b.m = null; b.ok = true; b.np = 0; continue; }
    let s = 0, w = 0, ok = true, hard = false, np = 0;
    for (const c of crit) {
      const v = c.score(b), p = c.pass(b);
      s += v * c.w; w += c.w;
      if (c.src === 'quiz') { if (c.hard && !p) { hard = true; ok = false; } }
      else if (!p) ok = false;
      if (p && c.src !== 'quiz') np++;
    }
    b.m = hard ? (s / w) * .25 : s / w;
    b.ok = ok;
    b.np = np;
  }
  return crit;
}
const filterCount = () => S.crit.filter(c => c.src !== 'quiz').length;
const fits = b => b.m == null || (b.ok && b.m >= .6);

/* Élő előnézet: hány fajta felelne meg, ha ezt a szűrőt is bekapcsolnád */
function previewCount(mut) {
  const f = { meret: new Set(S.f.meret), szor: new Set(S.f.szor), szerep: new Set(S.f.szerep), fci: new Set(S.f.fci), energia: S.f.energia, t: new Set(S.f.t) };
  mut(f);
  const crit = buildCrit(f, false);
  return BREEDS.filter(b => crit.every(c => c.pass(b))).length;
}

/* Magyarázat a kártyához: mi teljesül, mi nem */
function reasons(b) {
  return S.crit.map(c => {
    const v = c.score(b);
    const cls = c.pass(b) ? 'y' : v >= .4 ? 'h' : 'n';
    let text = cls === 'y' ? c.why[0] : (typeof c.why[1] === 'function' ? c.why[1](b) : c.why[1]);
    if (c.key === 'meret' && cls === 'y') text = 'Méret: ' + b.meret.map(v => SIZE_L[v]).join('–');
    return { cls, text, w: c.w };
  }).sort((a, b) => ({ y: 0, h: 1, n: 2 }[a.cls] - { y: 0, h: 1, n: 2 }[b.cls]) || b.w - a.w);
}

/* ---------- Párkereső kvíz ---------- */
const qT = (id, w, hard) => ({ ...TBY[id], key: 'q-' + id, label: TBY[id].l, w, hard, src: 'quiz' });
const qSet = (key, vals, w, labels, lbl) => ({ ...setCrit(key, new Set(vals), labels, key === 'meret'), key: 'q-' + key, label: lbl, w, src: 'quiz' });
const qAlone = w => ({
  key: 'q-alone', label: 'Bírja az egyedüllétet', w, src: 'quiz',
  score: b => clamp((5 - b.t.E) / 3 - (b.szerep.includes('VAR') ? .15 : 0) + (b.szerep.includes('ORZ') ? .15 : 0), 0, 1),
  pass: b => b.t.E <= 3, why: ['Jobban bírja az egyedüllétet', 'Nehezen viseli az egyedüllétet'],
});

const QUIZ = [
  { q: 'Hol laksz?', a: [
    { t: 'Lakásban, lift nélkül', e: '🏢', c: () => [qT('lakas', 3), qSet('meret', ['toy', 'kicsi', 'kozepes'], 1, SIZE_L, 'Kisebb méret')] },
    { t: 'Lakásban, lifttel', e: '🛗', c: () => [qT('lakas', 2)] },
    { t: 'Kertes házban', e: '🏡', c: () => [] },
    { t: 'Tanyán, nagy telken', e: '🌾', c: () => [qT('orzo', .6)] },
  ] },
  { q: 'Mennyi időt tudsz naponta mozgásra szánni?', a: [
    { t: 'Kevesebb mint 30 percet', e: '🛋️', c: () => [energyCrit(1.5, 3, 'quiz')] },
    { t: '30–60 percet', e: '🚶', c: () => [energyCrit(3, 3, 'quiz')] },
    { t: '1–2 órát', e: '🥾', c: () => [energyCrit(4.2, 2.5, 'quiz')] },
    { t: 'Több mint 2 órát – sportolok', e: '🏃', c: () => [energyCrit(4.9, 3, 'quiz')] },
  ] },
  { q: 'Van gyerek a háztartásban?', a: [
    { t: 'Nincs', e: '🙂', c: () => [] },
    { t: 'Van, 6 év feletti', e: '🧒', c: () => [qT('gyerek', 2)] },
    { t: 'Van, 6 év alatti is', e: '👶', c: () => [qT('gyerek', 3, true)] },
  ] },
  { q: 'Volt már kutyád?', a: [
    { t: 'Ez lesz az első', e: '🌱', c: () => [qT('kezdo', 3)] },
    { t: 'Volt már', e: '🐕', c: () => [qT('kezdo', 1)] },
    { t: 'Tapasztalt vagyok, képeztem is', e: '🎓', c: () => [] },
  ] },
  { q: 'Mennyit lesz egyedül a kutya?', a: [
    { t: 'Szinte soha – otthonról dolgozom', e: '🏠', c: () => [] },
    { t: 'Naponta pár órát', e: '⏳', c: () => [qAlone(1)] },
    { t: 'Egy teljes munkaidőt', e: '💼', c: () => [qAlone(2.5)] },
  ] },
  { q: 'Van allergiás a családban?', a: [
    { t: 'Nincs', e: '😊', c: () => [] },
    { t: 'Enyhe allergia', e: '🤧', c: () => [qT('hullas', 2)] },
    { t: 'Igen, erős', e: '🚫', c: () => [qT('hullas', 3, true)] },
  ] },
  { q: 'Mennyi időt szánnál szőrápolásra?', a: [
    { t: 'Szinte semennyit', e: '⏱️', c: () => [qT('apolas', 2.5)] },
    { t: 'Heti egy-két fésülést', e: '🪮', c: () => [qT('apolas', 1)] },
    { t: 'Szívesen kozmetikázom', e: '💇', c: () => [] },
  ] },
  { q: 'Mennyire zavarna a hangos kutya?', a: [
    { t: 'Nagyon – vékonyak a falak', e: '🤫', c: () => [qT('csendes', 3)] },
    { t: 'Kicsit', e: '🔉', c: () => [qT('csendes', 1)] },
    { t: 'Jó, ha jelez – legyen éber', e: '📣', c: () => [qT('orzo', 1.5)] },
  ] },
  { q: 'Mekkora kutyát képzelsz el?', a: [
    { t: 'Mindegy, a jelleme számít', e: '💛', c: () => [] },
    { t: 'Kicsit – elférjen az ölemben', e: '🐾', c: () => [qSet('meret', ['toy', 'kicsi'], 2, SIZE_L, 'Kis méret')] },
    { t: 'Közepeset', e: '🐕', c: () => [qSet('meret', ['kozepes'], 2, SIZE_L, 'Közepes méret')] },
    { t: 'Nagyot – legyen mit ölelni', e: '🐻', c: () => [qSet('meret', ['nagy', 'orias'], 2, SIZE_L, 'Nagy méret')] },
  ] },
  { q: 'Mire vágysz leginkább?', a: [
    { t: 'Kanapétársra', e: '🛋️', c: () => [qSet('szerep', ['VAR', 'CSA'], 1.5, ROLE_L, 'Társkutya')] },
    { t: 'Futó- és túratársra', e: '🏃', c: () => [qSet('szerep', ['SPO', 'VAD', 'PAS'], 2, ROLE_L, 'Sportos társ')] },
    { t: 'Igazi családtagra', e: '👨‍👩‍👧', c: () => [qSet('szerep', ['CSA'], 2, ROLE_L, 'Családi kutya')] },
    { t: 'Házőrzőre', e: '🛡️', c: () => [qT('orzo', 2.5)] },
    { t: 'Munkapartnerre, kutyasportra', e: '🎯', c: () => [qT('tanul', 2), qSet('szerep', ['MUN', 'PAS', 'SPO'], 1.5, ROLE_L, 'Munkakutya')] },
  ] },
];

const OWNER_TYPES = {
  suttogo: { e: '🎓', n: 'Kutyasuttogó', d: 'Tapasztalt vagy, és kihívásra vágysz. Nálad egy okos munkakutya is kiteljesedhet.' },
  orangyal: { e: '🛡️', n: 'Tanyasi őrangyal', d: 'Van hely, van udvar, és kell egy hűséges őrző, aki vigyáz a portára.' },
  kaland: { e: '🏃', n: 'Aktív kalandor', d: 'Futás, túra, bicikli: olyan társ kell, aki bírja a tempót, és még kér.' },
  csalad: { e: '👨‍👩‍👧', n: 'Családi karmester', d: 'Gyerekzsivaj, közös programok: türelmes, vidám családtagot keresel.' },
  kanape: { e: '🛋️', n: 'Kanapé-kapitány', d: 'Nyugis esték, rövid séták, sok bújás. A kényelem a te nyelved.' },
  varos: { e: '🏙️', n: 'Városi flâneur', d: 'Kávézó teraszok, parki séták, lift. Rugalmas városi társat keresel.' },
};
function ownerType(a) {
  if (a[3] === 2 && a[9] === 4) return 'suttogo';
  if (a[0] === 3 || a[9] === 3) return 'orangyal';
  if (a[1] >= 2 && (a[9] === 1 || a[1] === 3)) return 'kaland';
  if (a[2] >= 1 || a[9] === 2) return 'csalad';
  if (a[1] === 0 || a[9] === 0) return 'kanape';
  return 'varos';
}
function quizCrit(answers) {
  const crit = [];
  answers.forEach((ai, qi) => { if (ai != null && QUIZ[qi] && QUIZ[qi].a[ai]) crit.push(...QUIZ[qi].a[ai].c()); });
  return crit;
}
