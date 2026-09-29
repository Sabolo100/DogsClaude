// Pacsi Marketing – headless Edge + Chrome DevTools Protocol segédkönyvtár.
// Egy beépített statikus szerver kiszolgálja a repó gyökerét, így a sablonok (marketing/…) és az igazi app
// (dist/pacsi.html) azonos originről jön – a videókompozíció iframe-ben vezérelheti az appot.
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, existsSync, rmSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, extname, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';

export const ROOT = resolve(fileURLToPath(new URL('../../..', import.meta.url)));
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.mp4': 'video/mp4',
  '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8',
};

/** Statikus szerver a repó gyökerére (csak 127.0.0.1). */
export function serve(root = ROOT) {
  const srv = createServer((req, res) => {
    try {
      const u = new URL(req.url, 'http://x');
      let p = normalize(join(root, decodeURIComponent(u.pathname)));
      if (!p.startsWith(root)) { res.writeHead(403); return res.end(); }
      if (existsSync(p) && statSync(p).isDirectory()) p = join(p, 'index.html');
      if (!existsSync(p)) { res.writeHead(404); return res.end('404'); }
      res.writeHead(200, { 'Content-Type': MIME[extname(p).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      res.end(readFileSync(p));
    } catch (e) { res.writeHead(500); res.end(String(e)); }
  });
  return new Promise(ok => srv.listen(0, '127.0.0.1', () => ok({ srv, base: `http://127.0.0.1:${srv.address().port}` })));
}

/** Minimális CDP-kliens egy oldal-targethez. */
class Session {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.pending = new Map(); this.handlers = new Map();
    ws.addEventListener('message', ev => {
      const m = JSON.parse(ev.data);
      if (m.id && this.pending.has(m.id)) {
        const { ok, err } = this.pending.get(m.id); this.pending.delete(m.id);
        m.error ? err(new Error(m.error.message + ' ' + (m.error.data || ''))) : ok(m.result);
      } else if (m.method) (this.handlers.get(m.method) || []).forEach(f => f(m.params));
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((ok, err) => this.pending.set(id, { ok, err }));
  }
  on(method, f) { (this.handlers.get(method) || this.handlers.set(method, []).get(method)).push(f); }
  once(method) { return new Promise(ok => { const f = p => { this.handlers.set(method, (this.handlers.get(method) || []).filter(x => x !== f)); ok(p); }; this.on(method, f); }); }
  async eval(expr, { await: aw = true } = {}) {
    const r = await this.send('Runtime.evaluate', { expression: expr, awaitPromise: aw, returnByValue: true });
    if (r.exceptionDetails) throw new Error('JS: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
    return r.result.value;
  }
}

/** Headless Edge indítása; visszaad egy megnyitott oldal-sessiont. */
export async function launch({ width = 1080, height = 1920, dpr = 1 } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'pacsi-edge-'));
  const proc = spawn(EDGE, [
    '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${dir}`,
    '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--mute-audio', '--disable-extensions',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows',
    '--force-color-profile=srgb', '--font-render-hinting=none', `--window-size=${width},${height}`, 'about:blank',
  ], { stdio: 'ignore' });
  let port = 0;
  for (let i = 0; i < 100 && !port; i++) {
    await sleep(100);
    try { port = +readFileSync(join(dir, 'DevToolsActivePort'), 'utf8').split('\n')[0]; } catch { /* még indul */ }
  }
  if (!port) throw new Error('Edge nem indult el');
  const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const tgt = list.find(t => t.type === 'page');
  const ws = new WebSocket(tgt.webSocketDebuggerUrl);
  await new Promise((ok, err) => { ws.onopen = ok; ws.onerror = err; });
  const s = new Session(ws);
  await s.send('Page.enable');
  await s.send('Runtime.enable');
  await s.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: dpr, mobile: false });
  s.on('Runtime.consoleAPICalled', p => {
    if (p.type === 'error' || p.type === 'warning') console.log(`  [${p.type}]`, p.args.map(a => a.value ?? a.description).join(' '));
  });
  s.on('Runtime.exceptionThrown', p => console.log('  [exception]', p.exceptionDetails.exception?.description || p.exceptionDetails.text));
  s.close = async () => { try { ws.close(); } catch { } proc.kill(); await sleep(400); try { rmSync(dir, { recursive: true, force: true }); } catch { } };
  s.resize = (w, h, d = dpr) => s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: d, mobile: false });
  s.goto = async url => { const ld = s.once('Page.loadEventFired'); await s.send('Page.navigate', { url }); await ld; };
  s.shot = async (opts = {}) => Buffer.from((await s.send('Page.captureScreenshot', { format: 'png', ...opts })).data, 'base64');
  return s;
}

/**
 * Virtuális idő: minden frame-be (az iframe-ekbe is) bekerül dokumentum-létrehozáskor.
 * performance.now / Date / requestAnimationFrame / setTimeout / setInterval és a Web Animations
 * (CSS-animációk és -átmenetek) is a __advance(ms) hívásra lépnek – így minden képkocka pontos és egyenletes.
 */
export const VIRTUAL_TIME = String.raw`(() => {
  if (window.__vt) return;
  const RealDate = Date, base = RealDate.now();
  let vt = 0, rafId = 0, rafQ = new Map(), tId = 0;
  const timers = new Map(), seen = new WeakMap();
  window.__vt = () => vt;
  performance.now = () => vt;
  class VDate extends RealDate { constructor(...a) { a.length ? super(...a) : super(base + vt); } static now() { return base + vt; } }
  window.Date = VDate;
  window.requestAnimationFrame = cb => { const id = ++rafId; rafQ.set(id, cb); return id; };
  window.cancelAnimationFrame = id => { rafQ.delete(id); };
  const addT = (cb, ms, args, iv) => { const id = 1e6 + ++tId; const d = Math.max(0, +ms || 0); timers.set(id, { due: vt + (iv ? Math.max(1, d) : d), cb, args, iv: iv ? Math.max(1, d) : 0 }); return id; };
  window.setTimeout = (cb, ms, ...a) => addT(cb, ms, a, false);
  window.setInterval = (cb, ms, ...a) => addT(cb, ms, a, true);
  window.clearTimeout = window.clearInterval = id => { timers.delete(id); };
  function syncAnims() {
    let list; try { list = document.getAnimations(); } catch (e) { return; }
    for (const a of list) {
      let st = seen.get(a);
      if (st === undefined) { st = vt - (+a.currentTime || 0); seen.set(a, st); }
      if (st === 'done') continue;
      const tm = a.effect && a.effect.getComputedTiming ? a.effect.getComputedTiming() : null;
      const end = tm ? tm.endTime : Infinity;
      const ct = (vt - st) * (a.playbackRate || 1);
      if (isFinite(end) && ct >= end) { seen.set(a, 'done'); try { a.finish(); } catch (e) {} continue; }
      try { if (a.playState === 'running') a.pause(); a.currentTime = ct; } catch (e) {}
    }
  }
  window.__advance = ms => {
    const target = vt + ms;
    for (let guard = 0; guard < 10000; guard++) {
      let nid = 0, nt = null;
      for (const [id, t] of timers) if (t.due <= target && (!nt || t.due < nt.due)) { nid = id; nt = t; }
      if (!nt) break;
      vt = Math.max(vt, nt.due);
      if (nt.iv) nt.due += nt.iv; else timers.delete(nid);
      try { typeof nt.cb === 'function' ? nt.cb(...nt.args) : (0, eval)(nt.cb); } catch (e) { console.error(e); }
    }
    vt = target;
    const q = rafQ; rafQ = new Map();
    for (const cb of q.values()) { try { cb(vt); } catch (e) { console.error(e); } }
    syncAnims();
    for (const f of document.querySelectorAll('iframe')) { try { f.contentWindow.__advance && f.contentWindow.__advance(ms); } catch (e) {} }
  };
})();`;
