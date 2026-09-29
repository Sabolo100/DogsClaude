// Pacsi eDM – headless Edge renderelés a hírlevelekhez.
//   node marketing/tools/email_render.mjs images <manifest.json>   fejlécképek és logó (PNG; transparent:true → átlátszó háttér)
//   node marketing/tools/email_render.mjs shots  <manifest.json>   kész levelek teljes oldalas képe (ellenőrzéshez, CMS-bélyegképhez)
// manifest: [{ src: "marketing/email/img/hero.html?d=e_launch", out: "marketing/tmp/email/e_launch.png", w: 1200, h: 600, dpr: 1, transparent: false }]
// shots-nál h nem kell: a teljes dokumentummagasságot fotózza.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import { launch, serve, ROOT } from './lib/cdp.mjs';

const [cmd, manifest] = process.argv.slice(2);
if (!['images', 'shots'].includes(cmd) || !manifest) {
  console.log('Használat: email_render.mjs images|shots <manifest.json>');
  process.exit(1);
}
const list = JSON.parse(readFileSync(manifest, 'utf8'));
const { srv, base } = await serve();
const s = await launch({ width: 1200, height: 600 });
try {
  for (const it of list) {
    // egyedi lekérdezés minden címhez: a CDP nem tölt újra, ha az előzőtől csak a #-rész különbözik
    const [path, hash = ''] = it.src.replace(/\\/g, '/').split('#');
    const url = `${base}/${path}${path.includes('?') ? '&' : '?'}_r=${Date.now()}${hash ? '#' + hash : ''}`;
    const out = resolve(ROOT, it.out);
    mkdirSync(dirname(out), { recursive: true });
    if (cmd === 'images') {
      await s.resize(it.w, it.h, it.dpr || 1);
      await s.send('Emulation.setDefaultBackgroundColorOverride', it.transparent ? { color: { r: 0, g: 0, b: 0, a: 0 } } : {});
      await s.goto(url);
      await s.eval('window.__ready || document.fonts.ready');
      await sleep(it.wait || 400);
      writeFileSync(out, await s.shot({ clip: { x: 0, y: 0, width: it.w, height: it.h, scale: 1 }, captureBeyondViewport: false }));
    } else {
      await s.resize(it.w, 800, it.dpr || 1);
      await s.send('Emulation.setDefaultBackgroundColorOverride', {});
      if (it.dark) await s.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] });
      else await s.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] });
      let timer;
      await Promise.race([s.goto(url), new Promise(ok => { timer = setTimeout(() => { console.log('  ! betöltési időtúllépés: ' + it.src); ok(); }, 30000); })]);
      clearTimeout(timer);
      await s.eval('document.fonts.ready.then(() => Promise.all([...document.images].map(i => i.decode ? i.decode().catch(() => {}) : 0)))');
      await sleep(300);
      const hh = await s.eval('Math.ceil(document.documentElement.scrollHeight)');
      await s.resize(it.w, hh, it.dpr || 1);
      await sleep(200);
      writeFileSync(out, await s.shot({ clip: { x: 0, y: 0, width: it.w, height: hh, scale: 1 }, captureBeyondViewport: true }));
    }
    console.log(`  ${it.out}`);
  }
} finally {
  await s.close();
  srv.close();
  // Az Edge induláskor új folyamatnak adja át magát, amit a proc.kill() nem állít le: a „pacsi-edge-” profilú
  // headless példányokat itt zárjuk be (máskor párhuzamosan futó renderelésnél ezt ne használd).
  if (process.platform === 'win32' && !process.env.PACSI_KEEP_EDGE) {
    try {
      execFileSync('powershell', ['-NoProfile', '-Command',
        "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object { $_.CommandLine -like '*pacsi-edge-*' -and $_.CommandLine -like '*--headless*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
        { stdio: 'ignore' });
    } catch { /* nincs mit leállítani */ }
  }
}
