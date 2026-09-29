/* Pacsi Marketing – telefonkeret az igazi Pacsi appal (iframe) + szimulált ujj.
   Az app a repó dist/pacsi.html fájlja (egyfájlos build), azonos originről, így a kompozíció
   közvetlenül kattinthat benne, gépelhet a keresőbe, és kiolvashatja az elemek helyét. */
(() => {
  const SAT = 47, SAB = 22;               // iPhone-szerű státuszsáv és home-indikátor sáv (CSS px)
  const APP_CSS = `
  @media (max-width: 899px) {
    .app { grid-template-rows: calc(58px + ${SAT}px) 1fr auto auto !important; }
    .topbar { padding-top: ${SAT}px !important; }
    .panel, .card, .drawer { padding-bottom: ${SAB}px !important; }
    .tabbar { padding-bottom: calc(6px + ${SAB}px) !important; }
    .c-actions { padding-bottom: calc(14px + ${SAB}px) !important; }
    .mob-search { top: calc(8px + ${SAT}px) !important; }
    .toast { bottom: calc(160px + ${SAB}px) !important; }
  }
  * { cursor: none !important; }`;

  const statusBar = time => `
    <div class="sb-time">${time}</div>
    <div class="sb-island"></div>
    <div class="sb-icons">
      <svg viewBox="0 0 18 12" width="18" height="12"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>
      <svg viewBox="0 0 16 12" width="16" height="12"><path d="M8 11.5 5.6 9a3.4 3.4 0 0 1 4.8 0L8 11.5Zm-4.2-4.3L2.3 5.7a8 8 0 0 1 11.4 0l-1.5 1.5a5.9 5.9 0 0 0-8.4 0Z"/></svg>
      <svg viewBox="0 0 27 13" width="27" height="13"><rect x=".5" y=".5" width="23" height="12" rx="3.6" fill="none" stroke="currentColor" opacity=".45"/><rect x="2" y="2" width="18" height="9" rx="2.2"/><rect x="24.6" y="4.3" width="1.8" height="4.4" rx=".9" opacity=".5"/></svg>
    </div>`;

  class Phone {
    /** host: a kompozíció eleme; opts: {w, h, src, time} */
    constructor(host, opts = {}) {
      this.w = opts.w || 390; this.h = opts.h || 844;
      this.el = document.createElement('div');
      this.el.className = 'phone';
      this.el.style.cssText = `--pw:${this.w}px;--ph:${this.h}px`;
      this.el.innerHTML = `<div class="phone-screen"><iframe title="Pacsi app" scrolling="no"></iframe><div class="statusbar">${statusBar(opts.time || '9:41')}</div><div class="homebar"></div></div>`;
      host.appendChild(this.el);
      this.iframe = this.el.querySelector('iframe');
      this.iframe.width = this.w; this.iframe.height = this.h;
      this.src = opts.src || '/dist/pacsi.html?nocoach';
    }
    async load() {
      const ok = new Promise(r => this.iframe.addEventListener('load', r, { once: true }));
      this.iframe.src = this.src;
      await ok;
      this.win = this.iframe.contentWindow; this.doc = this.iframe.contentDocument;
      const st = this.doc.createElement('style'); st.textContent = APP_CSS; this.doc.head.appendChild(st);
      await this.doc.fonts.ready;
      for (let i = 0; i < 100 && !this.doc.querySelector('.b'); i++) await new Promise(r => setTimeout(r, 50));
      return this;
    }
    $(sel) { return typeof sel === 'string' ? this.doc.querySelector(sel) : sel; }
    $$(sel) { return [...this.doc.querySelectorAll(sel)]; }
    bubble(name) { return this.$$('.b').find(b => b.getAttribute('aria-label') === name); }
    /** az app egy elemének középpontja a kompozíció (felső oldal) koordinátáiban */
    point(sel, dx = 0, dy = 0) {
      const el = this.$(sel); if (!el) return null;
      const r = el.getBoundingClientRect(), fr = this.iframe.getBoundingClientRect();
      const s = fr.width / this.w;
      return { x: fr.left + (r.left + r.width / 2 + dx) * s, y: fr.top + (r.top + r.height / 2 + dy) * s, s };
    }
    /** app-koordinátából (iframe-viewport) oldalkoordináta */
    toPage(x, y) { const fr = this.iframe.getBoundingClientRect(), s = fr.width / this.w; return { x: fr.left + x * s, y: fr.top + y * s }; }
    click(sel) {
      const el = this.$(sel); if (!el) { console.warn('nincs ilyen elem: ' + sel); return; }
      const r = el.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
      const o = { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, pointerId: 7, pointerType: 'touch', isPrimary: true, view: this.win };
      el.dispatchEvent(new this.win.PointerEvent('pointerdown', o));
      el.dispatchEvent(new this.win.PointerEvent('pointerup', o));
      el.dispatchEvent(new this.win.MouseEvent('click', o));
    }
    /** érintéses húzás (kavarás) az app színpadán: pts = [[x,y],…] app-koordinátában */
    pointer(type, x, y, target) {
      const el = target || this.doc.elementFromPoint(x, y) || this.doc.body;
      el.dispatchEvent(new this.win.PointerEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, pointerId: 9, pointerType: 'touch', isPrimary: true, view: this.win }));
    }
    type(sel, text) {
      const inp = this.$(sel); if (!inp) return;
      inp.value = text;
      inp.dispatchEvent(new this.win.Event('input', { bubbles: true }));
    }
  }

  /* Szimulált ujj: kulcspontos pálya + koppintás (benyomás + hullámgyűrű). */
  class Finger {
    constructor(host) {
      this.el = document.createElement('div');
      this.el.className = 'finger';
      this.el.innerHTML = '<i class="ring"></i><i class="dot"></i>';
      host.appendChild(this.el);
      this.keys = [];             // {t, x, y}
      this.taps = [];             // t
      this.vis = [];              // {t, v}
      this.ring = this.el.querySelector('.ring');
      this.dot = this.el.querySelector('.dot');
    }
    move(t, x, y, dur = .55) { this.keys.push({ t0: t, t1: t + dur, x, y }); this.keys.sort((a, b) => a.t0 - b.t0); return this; }
    show(t, v = 1) { this.vis.push({ t, v }); this.vis.sort((a, b) => a.t - b.t); return this; }
    tap(t) { this.taps.push(t); return this; }
    pos(t) {
      let x = 540, y = 1500, px = x, py = y;
      for (const k of this.keys) {
        if (t >= k.t1) { x = k.x; y = k.y; px = x; py = y; continue; }
        if (t > k.t0) { const p = Comp.E.ioC((t - k.t0) / (k.t1 - k.t0)); x = px + (k.x - px) * p; y = py + (k.y - py) * p - Math.sin(p * Math.PI) * 40; }
        break;
      }
      return { x, y };
    }
    render(t) {
      let v = 0;
      for (const s of this.vis) if (t >= s.t) v = s.v;
      const last = this.vis.filter(s => s.t <= t).pop();
      const fade = last ? Comp.clamp((t - last.t) / .25) : 1;
      const op = last ? (last.v ? fade : 1 - fade) : 0;
      const { x, y } = this.pos(t);
      let press = 0, rp = -1;
      for (const tt of this.taps) {
        const d = t - tt;
        if (d > -0.12 && d < 0.22) press = Math.max(press, 1 - Math.abs(d - .02) / .2);
        if (d >= 0 && d < .7) rp = d / .7;
      }
      this.el.style.opacity = op.toFixed(3);
      this.el.style.transform = `translate(${x}px,${y}px)`;
      this.dot.style.transform = `translate(-50%,-50%) scale(${1 - press * .22})`;
      this.ring.style.opacity = rp < 0 ? 0 : (1 - rp) * .9;
      this.ring.style.transform = `translate(-50%,-50%) scale(${rp < 0 ? .5 : .6 + rp * 1.6})`;
    }
  }

  /** Egy koppintás megtervezése: odamegy, benyom, kattint az appban. A cél helyét a mozdulat indulásakor
      és a koppintás pillanatában is lekérdezzük (a buborékok mozognak). */
  function tapIn(phone, finger, tTap, sel, { lead = .6, dx = 0, dy = 0, click = true } = {}) {
    Comp.at(tTap - lead, () => {
      const p = phone.point(typeof sel === 'function' ? sel() : sel, dx, dy);
      if (p) finger.move(tTap - lead, p.x, p.y, lead - .05);
    });
    Comp.at(tTap, () => {
      const target = typeof sel === 'function' ? sel() : sel;
      const p = phone.point(target, dx, dy);
      if (p) finger.move(tTap - .04, p.x, p.y, .04);
      finger.tap(tTap);
      if (click) phone.click(target);
    });
  }

  window.Phone = Phone; window.Finger = Finger; window.tapIn = tapIn;
})();
