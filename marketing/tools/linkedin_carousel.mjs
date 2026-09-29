#!/usr/bin/env node
// LinkedIn-karusszel (Vibe Coding use case) – képernyőképek és oldalképek headless Edge-dzsel.
//   node marketing/tools/linkedin_carousel.mjs shots   → marketing/linkedin/shots/ (CMS-fülek, pitch-diák)
//   node marketing/tools/linkedin_carousel.mjs pages   → marketing/tmp/linkedin/pNN.png (1080×1350 × dpr)
// A PDF-et a build_linkedin.py fűzi össze az oldalképekből.
import { writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { launch, serve, ROOT } from './lib/cdp.mjs';

const mode = process.argv[2] || 'pages';
const dprI = process.argv.indexOf('--dpr');
const DPR = dprI > 0 ? +process.argv[dprI + 1] : 2;
const qI = process.argv.indexOf('--q');
const QS = qI > 0 ? '&' + process.argv[qI + 1] : '';   // pl. ver=1.0.0&build=abc1234 (a build_linkedin.py adja át)
const LI = join(ROOT, 'marketing', 'linkedin');
const SHOTS = join(LI, 'shots');

const ready = `(async () => {
  document.querySelectorAll('img[loading="lazy"]').forEach(i => i.loading = 'eager');
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.decode ? i.decode().catch(() => {}) : 0));
  return true;
})()`;

// A partneradatbázisban magánszemélyek is vannak: a nevek, címek, városok és a PK-azonosítók elmosva kerülnek a képre.
const BLUR_CONTACTS = `(() => {
  const st = document.createElement('style');
  st.textContent = 'table tbody td:not(:nth-child(3)):not(:last-child) { filter: blur(7px); } #layer { display: none; }';
  document.head.appendChild(st); return true;
})()`;

async function cms(s, base) {
  const views = [
    ['cms_attekintes', 'attekintes'], ['cms_naptar', 'naptar'], ['cms_tartalmak', 'tartalmak'], ['cms_item_v1', 'v1'],
    ['cms_email', 'email'], ['cms_email_L1', 'L1'], ['cms_kapcsolatok', 'kapcsolatok', BLUR_CONTACTS],
    ['cms_inditas', 'inditas'], ['cms_arculat', 'arculat'], ['cms_eredmenyek', 'eredmenyek'],
  ];
  await s.resize(1440, 1000, 2);
  for (const [name, hash, extra] of views) {
    await s.goto(`${base}/marketing/cms/index.html?v=${name}#${hash}`);
    await s.eval(ready);
    if (extra) await s.eval(extra);
    await sleep(1400);
    writeFileSync(join(SHOTS, `${name}.png`), await s.shot());
    console.log('  ', name);
  }
}

async function deck(s, base) {
  // prezentációs mód (1600×900), diánként az aktív dia – ugyanúgy, mint a pdf_deck.mjs
  await s.resize(1600, 900, 1.5);
  await s.goto(`${base}/marketing/pitch/dist/local.html?v=li`);
  await s.eval(ready);
  await sleep(1500);
  await s.eval(`document.querySelectorAll('.dnav, .hint, .prog').forEach(e => e.style.display = 'none'); true`);
  const n = await s.eval('document.querySelectorAll(".slide").length');
  for (let i = 0; i < n; i++) {
    await s.eval(`document.querySelectorAll('.slide').forEach((x, k) => { x.classList.toggle('on', k === ${i}); x.classList.toggle('past', k < ${i}); }); true`);
    await sleep(1600);
    writeFileSync(join(SHOTS, `deck_${String(i + 1).padStart(2, '0')}.png`), await s.shot());
  }
  console.log(`   ${n} dia`);
}

async function emails(s, base) {
  // két kész hírlevél teljes hosszban (asztali szélesség)
  await s.resize(680, 1000, 2);
  for (const id of ['L1', 'P1', 'W01']) {
    await s.goto(`${base}/marketing/out/email/${id}.html?v=li`);
    await s.eval(ready);
    await sleep(600);
    const h = await s.eval('Math.ceil(document.documentElement.scrollHeight)');
    writeFileSync(join(SHOTS, `email_${id}.png`), await s.shot({ clip: { x: 0, y: 0, width: 680, height: h, scale: 1 }, captureBeyondViewport: true }));
  }
  console.log('   3 hírlevél');
}

async function pages(s, base) {
  const out = join(ROOT, 'marketing', 'tmp', 'linkedin');
  rmSync(out, { recursive: true, force: true });
  mkdirSync(out, { recursive: true });
  await s.resize(1080, 1350, DPR);
  await s.goto(`${base}/marketing/linkedin/src/carousel.html?render=1${QS}`);
  await s.eval(ready);
  await sleep(1200);
  const n = await s.eval('document.querySelectorAll(".pg").length');
  for (let i = 0; i < n; i++) {
    await s.eval(`document.querySelectorAll('.pg').forEach((p, k) => p.hidden = k !== ${i}); window.scrollTo(0, 0); true`);
    await sleep(350);
    writeFileSync(join(out, `p${String(i + 1).padStart(2, '0')}.png`), await s.shot({ clip: { x: 0, y: 0, width: 1080, height: 1350, scale: 1 } }));
  }
  console.log(`   ${n} oldal: marketing/tmp/linkedin/`);
}

const { srv, base } = await serve();
const s = await launch({ width: 1440, height: 1000, dpr: 2 });
try {
  if (mode === 'shots') { mkdirSync(SHOTS, { recursive: true }); await cms(s, base); await deck(s, base); await emails(s, base); }
  else if (mode === 'emails') await emails(s, base);
  else await pages(s, base);
} finally { await s.close(); srv.close(); }
