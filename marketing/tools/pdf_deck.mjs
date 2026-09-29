#!/usr/bin/env node
// Pacsi partneri ajánlat → diaképek (1600×900 × dpr) a PDF-hez és ellenőrzéshez.
//   node marketing/tools/pdf_deck.mjs [--dpr 1.5] [--vector]
// Kimenet: marketing/tmp/deck/sNN.png; a --vector kapcsolóval a böngésző nyomtatási PDF-je is
// (marketing/pitch/Pacsi_partneri_ajanlat_vektoros.pdf – szöveg kijelölhető, de nagy fájl).
// A küldhető, tömörített PDF-et a build_pitch.py --pdf fűzi össze a diaképekből.
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { launch, serve, ROOT } from './lib/cdp.mjs';

const argv = process.argv, dprI = argv.indexOf('--dpr');
const dpr = dprI > 0 ? +argv[dprI + 1] : 1;
const shots = true, vector = argv.includes('--vector');
const { srv, base } = await serve();
const s = await launch({ width: 1600, height: 900, dpr });
try {
  await s.goto(`${base}/marketing/pitch/dist/local.html`);
  await s.eval(`(async () => {
    document.querySelectorAll('img[loading="lazy"]').forEach(i => i.loading = 'eager');
    await document.fonts.ready;
    await Promise.all([...document.images].map(i => i.decode ? i.decode().catch(() => {}) : 0));
    return true;
  })()`);
  await sleep(1500);
  await s.eval(`document.querySelectorAll('.dnav, .hint, .prog').forEach(e => e.style.display = 'none'); true`);
  if (shots) {
    mkdirSync(join(ROOT, 'marketing', 'tmp', 'deck'), { recursive: true });
    const n = await s.eval('document.querySelectorAll(".slide").length');
    for (let i = 0; i < n; i++) {
      await s.eval(`document.querySelectorAll('.slide').forEach((x, k) => { x.classList.toggle('on', k === ${i}); x.classList.toggle('past', k < ${i}); }); true`);
      await sleep(1600);
      writeFileSync(join(ROOT, 'marketing', 'tmp', 'deck', `s${String(i + 1).padStart(2, '0')}.png`), await s.shot());
    }
    console.log(`  ${n} diakép: marketing/tmp/deck/`);
  }
  if (vector) {
    const r = await s.send('Page.printToPDF', { printBackground: true, preferCSSPageSize: true, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 });
    const out = join(ROOT, 'marketing', 'pitch', 'Pacsi_partneri_ajanlat_vektoros.pdf');
    writeFileSync(out, Buffer.from(r.data, 'base64'));
    console.log(`  PDF: ${out}`);
  }
} finally { await s.close(); srv.close(); }
