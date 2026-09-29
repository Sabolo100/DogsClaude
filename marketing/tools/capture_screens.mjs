#!/usr/bin/env node
// Pacsi Marketing – képernyőképek az igazi appról (dist/pacsi.html), nagy felbontásban.
//   node marketing/tools/capture_screens.mjs [név …]
// Kimenet: marketing/assets/screens/<név>.png
// Mobilnézetben iPhone-szerű státuszsáv- és home-sáv-hely marad (a sablon rajzolja rá az órát, a szigetet).
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { launch, serve, ROOT } from './lib/cdp.mjs';

const OUT = join(ROOT, 'marketing', 'assets', 'screens');
const SAT = 47, SAB = 22;
const MOB_CSS = `@media (max-width: 899px) {
  .app { grid-template-rows: calc(58px + ${SAT}px) 1fr auto auto !important; }
  .topbar { padding-top: ${SAT}px !important; }
  .panel, .card, .drawer { padding-bottom: ${SAB}px !important; }
  .tabbar { padding-bottom: calc(6px + ${SAB}px) !important; }
  .c-actions { padding-bottom: calc(14px + ${SAB}px) !important; }
  .mob-search { top: calc(8px + ${SAT}px) !important; }
  .toast { bottom: calc(160px + ${SAB}px) !important; } }`;

const QUIZ_VAROS = '1.1.0.0.1.0.1.0.1.1';
const QUIZ_CSALAD = '2.2.2.0.1.0.1.1.0.2';
const M = { w: 390, h: 844, dpr: 3 }, D = { w: 1440, h: 900, dpr: 2 };
const STATES = [
  { n: 'm_cloud', ...M, hash: '', wait: 4500 },
  { n: 'm_filtered', ...M, hash: '#f=lakas;gyerek;csendes&m=s', wait: 5000 },
  { n: 'm_lakas_csendes', ...M, hash: '#f=lakas;csendes&m=s', wait: 5000 },
  { n: 'm_card_agar', ...M, hash: '#f=lakas;gyerek;csendes&m=s&b=angol-agar', wait: 5000 },
  { n: 'm_card_vizsla', ...M, hash: '#b=magyar-vizsla', wait: 4500 },
  { n: 'm_card_cavalier', ...M, hash: '#f=lakas;kezdo&m=s&b=cavalier-king-charles-spaniel', wait: 5000 },
  { n: 'm_magyar', ...M, hash: '#f=magyar&m=s', wait: 5000 },
  { n: 'm_quiz_result', ...M, hash: `#k=${QUIZ_VAROS}&kviz`, wait: 5500 },
  { n: 'm_quiz_q', ...M, hash: '#kviz', wait: 4500 },
  { n: 'm_map', ...M, hash: '#v=terkep', wait: 5000 },
  { n: 'm_groups', ...M, hash: '#v=csoport.meret', wait: 5000 },
  { n: 'm_compare', ...M, hash: '', store: { cmp: ['magyar-vizsla', 'golden-retriever', 'border-collie'] }, js: `document.querySelector('[data-tab="osszevet"]').click()`, wait: 5000 },
  { n: 'm_tips', ...M, hash: '', js: `document.querySelector('[data-tab="tippek"]').click()`, wait: 4500 },
  { n: 'm_dark', ...M, hash: '#f=gyerek;csendes&m=s', store: { theme: 'dark' }, wait: 5000 },
  { n: 'd_rank', ...D, hash: '#f=meret:kicsi;gyerek;lakas&m=r', wait: 5000 },
  { n: 'd_strict', ...D, hash: '#f=lakas;gyerek&m=s', wait: 5000 },
  { n: 'd_card', ...D, hash: '#f=lakas;gyerek&m=r&b=cavalier-king-charles-spaniel', wait: 5000 },
  { n: 'd_map', ...D, hash: '#v=terkep&f=gyerek&m=r', wait: 5000 },
  { n: 'd_groups', ...D, hash: '#v=csoport.meret', wait: 5000 },
  { n: 'd_quiz', ...D, hash: `#k=${QUIZ_CSALAD}&kviz`, wait: 5500 },
  { n: 'd_compare', ...D, hash: '', store: { cmp: ['magyar-vizsla', 'golden-retriever', 'border-collie'] }, js: `document.querySelector('[data-drawer="osszevet"]').click()`, wait: 5000 },
];

const only = process.argv.slice(2);
mkdirSync(OUT, { recursive: true });
const { srv, base } = await serve();
const s = await launch({ width: 390, height: 844, dpr: 3 });
try {
  for (const st of STATES) {
    if (only.length && !only.includes(st.n)) continue;
    await s.resize(st.w, st.h, st.dpr);
    // tiszta állapot: localStorage ürítése, majd az előírt kulcsok beállítása
    await s.goto(`${base}/dist/pacsi.html?nocoach`);
    await s.eval(`localStorage.clear(); ${Object.entries(st.store || {}).map(([k, v]) => `localStorage.setItem('pacsi:${k}', ${JSON.stringify(JSON.stringify(v))});`).join('')} true`);
    await s.goto(`${base}/dist/pacsi.html?nocoach&x=${Date.now()}${st.hash}`);
    if (st.w < 900) await s.eval(`(() => { const e = document.createElement('style'); e.textContent = ${JSON.stringify(MOB_CSS)}; document.head.appendChild(e); return true; })()`);
    await s.eval('document.fonts.ready.then(() => true)');
    if (st.js) { await sleep(1800); await s.eval(`(() => { ${st.js}; return true; })()`); }
    await sleep(st.wait);
    const png = await s.shot();
    writeFileSync(join(OUT, st.n + '.png'), png);
    console.log(`  ${st.n}.png  ${st.w}x${st.h}@${st.dpr}`);
  }
} finally { await s.close(); srv.close(); }
