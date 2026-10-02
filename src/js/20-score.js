/* ==========================================================================
   Szűrők, pontozás, kvíz
   ========================================================================== */
/* A nyelvfüggő címkék (méret, szőr, szerep…) üres táblákban élnek, amelyeket a labels() tölt fel: induláskor és
   nyelvváltáskor (lásd 12-i18n.js). Az azonosítók nyelvfüggetlenek – ezek vannak a szűrőkben és az URL-ben is. */
const SIZE_IDS = ['toy', 'kicsi', 'kozepes', 'nagy', 'orias'];
const SIZES = [], SIZE_L = {};
const SIZE_I = Object.fromEntries(SIZE_IDS.map((k, i) => [k, i]));
const COAT_IDS = ['rovid', 'kozepes', 'hosszu', 'drot', 'gondor', 'zsinoros', 'szortelen'];
const COATS = [], COAT_L = {};
const ROLE_IDS = ['CSA', 'VAR', 'PAS', 'ORZ', 'VAD', 'SPO', 'MUN', 'ESZ'];
const ROLES = [], ROLE_L = {};
const ROLE_C = { CSA: '#FF6B3D', VAR: '#E86A92', PAS: '#17756E', ORZ: '#5B5BD6', VAD: '#C7772B', SPO: '#2FA3D6', MUN: '#6E7B8B', ESZ: '#5AB0F0' };
const ENERGY_V = { nyugis: 1.5, mersekelt: 3, sportos: 4.6 };
const ENERGY = [];                                   // [azonosító, címke, érték]
const FCI = {};
const fillLabels = (arr, obj, ns, ids) => { arr.length = 0; for (const k of ids) { obj[k] = t(`${ns}.${k}`); arr.push([k, obj[k]]); } };
labels(() => {
  fillLabels(SIZES, SIZE_L, 'size', SIZE_IDS);
  fillLabels(COATS, COAT_L, 'coat', COAT_IDS);
  fillLabels(ROLES, ROLE_L, 'role', ROLE_IDS);
  ENERGY.length = 0;
  for (const k in ENERGY_V) ENERGY.push([k, t(`energy.${k}`), ENERGY_V[k]]);
  for (let k = 1; k <= 10; k++) FCI[k] = t(`fci.${k}`);
});
const SC = [0, 0, .15, .5, .85, 1];

/* Kapcsoló típusú szűrők (8.1 fejezet). A szövegek a szótárban vannak: tog.<id>.l (név), .sub (alcím), .y / .n (a kártyán: megfelel / nem) */
const TOGGLES = [
  { id: 'gyerek', i: 'kid', c: '#FFD9C2', g: 'eletmod', score: b => SC[b.t.Gy], pass: b => b.t.Gy >= 4 },
  { id: 'lakas', i: 'home', c: '#CFE6FA', g: 'eletmod', score: b => SC[b.t.L], pass: b => b.t.L >= 4 },
  { id: 'kezdo', i: 'sprout', c: '#E5F2C4', g: 'eletmod', score: b => SC[b.t.K], pass: b => b.t.K >= 4 },
  { id: 'csendes', i: 'quiet', c: '#E2D9FF', g: 'eletmod', score: b => SC[6 - b.t.U], pass: b => b.t.U <= 2 },
  { id: 'orzo', i: 'shield', c: '#D6CCFF', g: 'eletmod', score: b => SC[b.t.O], pass: b => b.t.O >= 4 },
  { id: 'hullas', i: 'feather', c: '#FFE6A0', g: 'gondozas', score: b => SC[6 - b.t.H], pass: b => b.t.H <= 2 },
  { id: 'apolas', i: 'comb', c: '#FFC8D6', g: 'gondozas', score: b => SC[6 - b.t.A], pass: b => b.t.A <= 2 },
  { id: 'tanul', i: 'cap', c: '#BDE8D3', g: 'gondozas', score: b => SC[b.t.I], pass: b => b.t.I >= 4 },
  { id: 'nyal', i: 'drop', c: '#BFDDF7', g: 'gondozas', score: b => b.nyal ? 0 : 1, pass: b => !b.nyal },
  { id: 'elet', i: 'pulse', c: '#FFC8D6', g: 'egeszseg', score: b => clamp((b.elet[1] - 9) / 8, 0, 1), pass: b => b.elet[1] >= 14 },
  { id: 'legzes', i: 'nose', c: '#DDEDB2', g: 'egeszseg', score: b => [1, .4, 0][b.brachy], pass: b => !b.brachy },
  { id: 'magyar', i: 'flag', c: '#fff', g: 'kulonleges', score: b => b.hu ? 1 : 0, pass: b => b.hu },
];
labels(() => { for (const g of TOGGLES) Object.assign(g, { l: t(`tog.${g.id}.l`), sub: t(`tog.${g.id}.sub`), why: [t(`tog.${g.id}.y`), t(`tog.${g.id}.n`)] }); });
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
  why: [t(`why.${key}.y`), t(`why.${key}.n`)],
});
const energyCrit = (target, w = 1, src) => ({
  key: src ? 'q-E' : 'energia', w, src, label: ENERGY.find(e => e[2] === target)?.[1] || t('energy.label'),
  score: b => clamp(1 - Math.abs(b.t.E - target) / 3, 0, 1),
  pass: b => target < 2 ? b.t.E <= 2 : target > 4 ? b.t.E >= 4 : b.t.E === 3,
  why: [t('why.energy.y'), b => b.t.E > target ? t('why.energy.more') : t('why.energy.less')],
});

/* Kritériumlista a szűrőállapotból (+ kvíz) */
function buildCrit(f = S.f, withQuiz = true) {
  const out = [];
  if (f.meret.size) out.push({ ...setCrit('meret', f.meret, SIZE_L, true), label: t('crit.size', { v: [...f.meret].map(v => SIZE_L[v]).join(', ') }) });
  if (f.szor.size) out.push({ ...setCrit('szor', f.szor, COAT_L), label: t('crit.coat', { v: [...f.szor].map(v => COAT_L[v]).join(', ') }) });
  if (f.szerep.size) out.push({ ...setCrit('szerep', f.szerep, ROLE_L), label: [...f.szerep].map(v => ROLE_L[v]).join(', ') });
  if (f.fci.size) out.push({ ...setCrit('fci', f.fci, Object.fromEntries(Object.keys(FCI).map(k => [k, 'FCI ' + k]))), label: t('crit.fci', { v: [...f.fci].sort((a, b) => a - b).join(', ') }) });
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
    if (c.key === 'meret' && cls === 'y') text = t('crit.size', { v: b.meret.map(v => SIZE_L[v]).join('–') });
    return { cls, text, w: c.w };
  }).sort((a, b) => ({ y: 0, h: 1, n: 2 }[a.cls] - { y: 0, h: 1, n: 2 }[b.cls]) || b.w - a.w);
}

/* ---------- Párkereső kvíz ---------- */
const qT = (id, w, hard) => ({ ...TBY[id], key: 'q-' + id, label: TBY[id].l, w, hard, src: 'quiz' });
const qSet = (key, vals, w, labels, lbl) => ({ ...setCrit(key, new Set(vals), labels, key === 'meret'), key: 'q-' + key, label: lbl, w, src: 'quiz' });
const qAlone = w => ({
  key: 'q-alone', label: t('qc.alone'), w, src: 'quiz',
  score: b => clamp((5 - b.t.E) / 3 - (b.szerep.includes('VAR') ? .15 : 0) + (b.szerep.includes('ORZ') ? .15 : 0), 0, 1),
  pass: b => b.t.E <= 3, why: [t('why.alone.y'), t('why.alone.n')],
});

/* A kvíz kérdései és válaszai (q, a[].t) a szótárból töltődnek (quiz.q<n>, quiz.q<n>.a<m>); itt csak az emoji és a szempontok vannak */
const QUIZ = [
  { a: [
    { e: '🏢', c: () => [qT('lakas', 3), qSet('meret', ['toy', 'kicsi', 'kozepes'], 1, SIZE_L, t('qc.smaller'))] },
    { e: '🛗', c: () => [qT('lakas', 2)] },
    { e: '🏡', c: () => [] },
    { e: '🌾', c: () => [qT('orzo', .6)] },
  ] },
  { a: [
    { e: '🛋️', c: () => [energyCrit(1.5, 3, 'quiz')] },
    { e: '🚶', c: () => [energyCrit(3, 3, 'quiz')] },
    { e: '🥾', c: () => [energyCrit(4.2, 2.5, 'quiz')] },
    { e: '🏃', c: () => [energyCrit(4.9, 3, 'quiz')] },
  ] },
  { a: [
    { e: '🙂', c: () => [] },
    { e: '🧒', c: () => [qT('gyerek', 2)] },
    { e: '👶', c: () => [qT('gyerek', 3, true)] },
  ] },
  { a: [
    { e: '🌱', c: () => [qT('kezdo', 3)] },
    { e: '🐕', c: () => [qT('kezdo', 1)] },
    { e: '🎓', c: () => [] },
  ] },
  { a: [
    { e: '🏠', c: () => [] },
    { e: '⏳', c: () => [qAlone(1)] },
    { e: '💼', c: () => [qAlone(2.5)] },
  ] },
  { a: [
    { e: '😊', c: () => [] },
    { e: '🤧', c: () => [qT('hullas', 2)] },
    { e: '🚫', c: () => [qT('hullas', 3, true)] },
  ] },
  { a: [
    { e: '⏱️', c: () => [qT('apolas', 2.5)] },
    { e: '🪮', c: () => [qT('apolas', 1)] },
    { e: '💇', c: () => [] },
  ] },
  { a: [
    { e: '🤫', c: () => [qT('csendes', 3)] },
    { e: '🔉', c: () => [qT('csendes', 1)] },
    { e: '📣', c: () => [qT('orzo', 1.5)] },
  ] },
  { a: [
    { e: '💛', c: () => [] },
    { e: '🐾', c: () => [qSet('meret', ['toy', 'kicsi'], 2, SIZE_L, t('qc.small'))] },
    { e: '🐕', c: () => [qSet('meret', ['kozepes'], 2, SIZE_L, t('qc.medium'))] },
    { e: '🐻', c: () => [qSet('meret', ['nagy', 'orias'], 2, SIZE_L, t('qc.large'))] },
  ] },
  { a: [
    { e: '🛋️', c: () => [qSet('szerep', ['VAR', 'CSA'], 1.5, ROLE_L, t('qc.companion'))] },
    { e: '🏃', c: () => [qSet('szerep', ['SPO', 'VAD', 'PAS'], 2, ROLE_L, t('qc.sporty'))] },
    { e: '👨‍👩‍👧', c: () => [qSet('szerep', ['CSA'], 2, ROLE_L, t('qc.family'))] },
    { e: '🛡️', c: () => [qT('orzo', 2.5)] },
    { e: '🎯', c: () => [qT('tanul', 2), qSet('szerep', ['MUN', 'PAS', 'SPO'], 1.5, ROLE_L, t('qc.working'))] },
  ] },
];
labels(() => QUIZ.forEach((qz, i) => { qz.q = t(`quiz.q${i + 1}`); qz.a.forEach((a, j) => { a.t = t(`quiz.q${i + 1}.a${j + 1}`); }); }));
// ugyanez magyarul, a statisztikához
const quizTH = (qi, ai) => ai == null ? tH(`quiz.q${qi + 1}`) : tH(`quiz.q${qi + 1}.a${ai + 1}`);

const OWNER_TYPES = {
  suttogo: { e: '🎓' }, orangyal: { e: '🛡️' }, kaland: { e: '🏃' }, csalad: { e: '👨‍👩‍👧' }, kanape: { e: '🛋️' }, varos: { e: '🏙️' },
};
labels(() => { for (const k in OWNER_TYPES) Object.assign(OWNER_TYPES[k], { n: t(`owner.${k}.n`), d: t(`owner.${k}.d`) }); });
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
