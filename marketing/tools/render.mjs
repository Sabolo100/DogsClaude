#!/usr/bin/env node
// Pacsi Marketing – renderelő.
//
//   node marketing/tools/render.mjs video  <kompozíció.html> <ki.mp4> [--fps 30] [--crf 18]
//   node marketing/tools/render.mjs frames <kompozíció.html> <mappa> --at 0.5,2,4.25
//   node marketing/tools/render.mjs images <manifest.json>
//
// A videókompozíciók virtuális időben futnak (lásd lib/cdp.mjs → VIRTUAL_TIME): minden képkocka
// pontosan 1/fps másodperccel később készül, akármilyen lassú is a gép. Az iframe-ben futó igazi Pacsi app
// is ugyanazt a virtuális órát kapja, így a buborékfizika és az animációk is egyenletesek.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync, existsSync, statSync } from 'node:fs';
import { dirname, resolve, relative, join } from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { launch, serve, ROOT, VIRTUAL_TIME } from './lib/cdp.mjs';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const urlFor = (base, p) => base + '/' + relative(ROOT, resolve(p.split('?')[0])).replace(/\\/g, '/') + (p.includes('?') ? '?' + p.split('?')[1] : '');

async function openComp(s, base, comp, extra = '') {
  await s.send('Page.addScriptToEvaluateOnNewDocument', { source: VIRTUAL_TIME });
  const u = urlFor(base, comp);
  await s.goto(u + (u.includes('?') ? '&' : '?') + 'render=1' + extra);
  await s.eval('window.__compReady');
  await sleep(1200);                                            // képek dekódolása (valós időben)
  const meta = await s.eval('JSON.stringify(window.__comp)');
  return JSON.parse(meta);
}

async function video(comp, out) {
  const fps = +opt('fps', 30), crf = opt('crf', '18');
  const { srv, base } = await serve();
  const s = await launch({ width: 1080, height: 1920 });
  try {
    const meta = await openComp(s, base, comp);
    const step = 1000 / fps;
    for (let t = 0; t < (meta.preroll || 0) * 1000; t += step) await s.eval(`__advance(${step})`, { await: false });
    const n = Math.round(meta.duration * fps);
    mkdirSync(dirname(resolve(out)), { recursive: true });
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
      '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
      '-map', '0:v', '-map', '1:a', '-shortest',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2',
      '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-r', String(fps), resolve(out)], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      if (i) await s.eval(`__advance(${step})`, { await: false });
      const png = await s.shot({ optimizeForSpeed: true });
      if (!ff.stdin.write(png)) await new Promise(ok => ff.stdin.once('drain', ok));
      if (i % 30 === 0) process.stdout.write(`\r  ${comp}: ${i}/${n} képkocka (${((Date.now() - t0) / 1000).toFixed(0)} s)   `);
    }
    ff.stdin.end();
    await new Promise(ok => ff.on('close', ok));
    console.log(`\n  kész: ${out} (${(statSync(out).size / 1e6).toFixed(1)} MB, ${n} képkocka)`);
  } finally { await s.close(); srv.close(); }
}

async function frames(comp, dir) {
  const at = opt('at', '0,1,2').split(',').map(Number);
  const fps = +opt('fps', 30);
  const { srv, base } = await serve();
  const s = await launch({ width: 1080, height: 1920 });
  try {
    const meta = await openComp(s, base, comp);
    const step = 1000 / fps;
    for (let t = 0; t < (meta.preroll || 0) * 1000; t += step) await s.eval(`__advance(${step})`, { await: false });
    mkdirSync(dir, { recursive: true });
    let cur = 0;
    for (const t of at.sort((a, b) => a - b)) {
      while (cur + step / 2 < t * 1000) { await s.eval(`__advance(${step})`, { await: false }); cur += step; }
      const f = join(dir, `f_${t.toFixed(2)}.png`);
      writeFileSync(f, await s.shot());
      console.log('  ' + f);
    }
  } finally { await s.close(); srv.close(); }
}

// Állóképek: manifest = [{ src: "marketing/social/images/x.html?v=1", out: "marketing/out/kepek/x.png", w: 1080, h: 1350 }]
async function images(manifest) {
  const list = JSON.parse(readFileSync(manifest, 'utf8'));
  const only = opt('only', '');
  const { srv, base } = await serve();
  const s = await launch({ width: 1080, height: 1350 });
  try {
    for (const it of list) {
      if (only && !it.out.includes(only)) continue;
      await s.resize(it.w, it.h, it.dpr || 1);
      await s.goto(urlFor(base, it.src));
      await s.eval('window.__ready || document.fonts.ready');
      await sleep(it.wait || 500);
      const out = resolve(it.out);
      mkdirSync(dirname(out), { recursive: true });
      writeFileSync(out, await s.shot({ clip: { x: 0, y: 0, width: it.w, height: it.h, scale: 1 } }));
      console.log(`  ${it.out}`);
    }
  } finally { await s.close(); srv.close(); }
}

const [cmd, a, b] = args;
if (cmd === 'video') await video(a, b);
else if (cmd === 'frames') await frames(a, b);
else if (cmd === 'images') await images(a);
else { console.log('Használat: render.mjs video|frames|images …'); process.exit(1); }
