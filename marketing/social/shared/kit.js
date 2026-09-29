/* Pacsi Marketing – építőkockák a képekhez és a videókhoz (portrébuborék, felhő, telefon, chip, logó).
   Minden elérési út a repó gyökeréhez képest abszolút (a render.mjs a gyökeret szolgálja ki). */
(() => {
  const K = {
    data: null, by: {},
    site: 'pacsit.hu',   // az app saját domainje (a posztszövegekben: marketing/content/content.py → SITE)
    async init() {
      const [d, svg] = await Promise.all([
        fetch('/data/fajtak.json').then(r => r.json()),
        fetch('/marketing/social/shared/icons.svg').then(r => r.text()),
      ]);
      K.data = d;
      for (const b of [...d.breeds, ...d.spares]) K.by[b.id] = b;
      const holder = document.createElement('div');
      holder.innerHTML = svg;
      document.body.prepend(holder.firstElementChild);
      return K;
    },
    img: id => `/img/portrek/${id}.webp`,
    thumb: id => `/img/thumbs/${id}.webp`,
    kv: n => `/marketing/assets/kv/${n}.png`,
    screen: n => `/marketing/assets/screens/${n}.png`,
    name: id => (K.by[id] || {}).nev || id,
    ic: (n, s = 24, cls = '') => `<svg class="ic ${cls}" width="${s}" height="${s}" aria-hidden="true"><use href="#i-${n}"/></svg>`,
    esc: s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])),

    /** Logó: „Pacsı” + korall mancs; px = betűméret */
    logo(px = 60, { by = true, inv = false } = {}) {
      return `<span class="brand${inv ? ' inv' : ''}" style="font-size:${px}px"><span class="logo">Pacs<span class="i">ı<svg viewBox="0 0 24 24"><use href="#i-paw"/></svg></span></span>${by ? '<span class="byline">by <b>DarwinAI</b></span>' : ''}</span>`;
    },

    /** Portrébuborék, középpont (x,y), átmérő d. ring: illeszkedési gyűrű % (0–100) vagy true = teljes. */
    bub(id, x, y, d, { ring = 0, rot = 0, z = 1, op = 1, cls = '', style = '' } = {}) {
      const r = ring === true ? 100 : ring;
      const ringSvg = r ? `<svg class="bring" viewBox="0 0 100 100" style="position:absolute;inset:${-d * .11}px;width:${d * 1.22}px;height:${d * 1.22}px;transform:rotate(-90deg);overflow:visible">
          <circle cx="50" cy="50" r="47" fill="none" stroke="rgba(255,107,61,.16)" stroke-width="2.6"/>
          <circle cx="50" cy="50" r="47" fill="none" stroke="#FF6B3D" stroke-width="2.6" stroke-linecap="round" pathLength="100" stroke-dasharray="${r} 100"/></svg>` : '';
      return `<div class="bub ${cls}" style="--d:${d}px;left:${x - d / 2}px;top:${y - d / 2}px;width:${d}px;height:${d}px;background-image:url('${K.img(id)}');z-index:${z};opacity:${op};transform:rotate(${rot}deg);${style}">${ringSvg}</div>`;
    },

    /** Determinisztikus körpakolás: items [{id,d}] → x,y a (cx,cy) körül; ax/ay: a forma nyújtása */
    pack(items, { cx, cy, gap = 8, iters = 420, ax = 1, ay = 1, seed = 1 } = {}) {
      const ga = Math.PI * (3 - Math.sqrt(5));
      const avg = items.reduce((s, it) => s + it.d, 0) / items.length;
      items.forEach((it, i) => {
        const rr = Math.sqrt(i + .5) * avg * .52;
        it.x = cx + Math.cos(i * ga + seed) * rr * ax;
        it.y = cy + Math.sin(i * ga + seed) * rr * ay;
      });
      for (let k = 0; k < iters; k++) {
        for (let i = 0; i < items.length; i++) {
          const a = items[i];
          for (let j = i + 1; j < items.length; j++) {
            const b = items[j];
            let dx = b.x - a.x, dy = b.y - a.y, dist = Math.hypot(dx, dy) || .01;
            const min = (a.d + b.d) / 2 + gap;
            if (dist < min) {
              const push = (min - dist) / 2, ux = dx / dist, uy = dy / dist;
              a.x -= ux * push; a.y -= uy * push; b.x += ux * push; b.y += uy * push;
            }
          }
          const g = k < iters * .8 ? .012 : .004;
          a.x += (cx - a.x) * g / ax; a.y += (cy - a.y) * g / ay;
        }
      }
      return items;
    },

    /** Telefonkeret képernyőképpel (390×844-es képernyő, a sw a képernyő szélessége px-ben) */
    phone(src, { x = 0, y = 0, sw = 390, rot = 0, time = '9:41', dark = false, cls = '', z = 2 } = {}) {
      const s = sw / 390;
      const col = dark ? '#F4EFE8' : '#111';
      return `<div class="phone ${cls}" style="--pw:390px;--ph:844px;left:${x}px;top:${y}px;transform-origin:0 0;transform:scale(${s}) rotate(${rot}deg);z-index:${z}">
        <div class="phone-screen"><img src="${src}" style="position:absolute;inset:0;width:390px;height:844px;display:block">
        <div class="statusbar" style="color:${col}"><div class="sb-time">${time}</div><div class="sb-island"></div>
          <div class="sb-icons" style="color:${col}"><svg viewBox="0 0 18 12" width="18" height="12" style="fill:${col}"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>
          <svg viewBox="0 0 16 12" width="16" height="12" style="fill:${col}"><path d="M8 11.5 5.6 9a3.4 3.4 0 0 1 4.8 0L8 11.5Zm-4.2-4.3L2.3 5.7a8 8 0 0 1 11.4 0l-1.5 1.5a5.9 5.9 0 0 0-8.4 0Z"/></svg>
          <svg viewBox="0 0 27 13" width="27" height="13" style="fill:${col}"><rect x=".5" y=".5" width="23" height="12" rx="3.6" fill="none" stroke="${col}" opacity=".45"/><rect x="2" y="2" width="18" height="9" rx="2.2"/><rect x="24.6" y="4.3" width="1.8" height="4.4" rx=".9" opacity=".5"/></svg></div></div>
        <div class="homebar" style="background:${col}"></div></div></div>`;
    },
    /** a telefon teljes (kerettel együtt) mérete adott képernyőszélességnél */
    phoneSize: sw => ({ w: (390 + 28) * sw / 390, h: (844 + 28) * sw / 390 }),

    /** Laptop (1440×900-as képernyőkép), w = képernyőszélesség */
    laptop(src, { x = 0, y = 0, w = 900, z = 2 } = {}) {
      const h = w * 900 / 1440, b = w * .022;
      return `<div class="laptop" style="position:absolute;left:${x}px;top:${y}px;z-index:${z};width:${w + 2 * b}px">
        <div style="padding:${b}px;border-radius:${b * 1.4}px ${b * 1.4}px 6px 6px;background:linear-gradient(160deg,#2b2724,#110f0e);box-shadow:0 30px 80px rgba(60,30,10,.28),0 0 0 2px #3d3732 inset">
          <img src="${src}" style="display:block;width:${w}px;height:${h}px;border-radius:4px"></div>
        <div style="height:${b * 1.1}px;margin:0 -${b * 3}px;border-radius:0 0 ${b * 2}px ${b * 2}px;background:linear-gradient(#d9d3cc,#a39b93);box-shadow:0 18px 30px rgba(60,30,10,.25)"></div></div>`;
    },

    /** Szűrőchip matrica (az app ikonjaival) */
    chip(icon, label, { on = true, size = 1, extra = '' } = {}) {
      return `<span class="mchip${on ? ' on' : ''}" style="font-size:${30 * size}px;${extra}"><span class="o">${K.ic(icon, 30 * size)}</span>${label}${on ? `<b class="ck">${K.ic('check', 18 * size)}</b>` : ''}</span>`;
    },

    /** Háttér: három elmosott színfolt (a kép méretéhez skálázva) */
    blobs(w, h, v = 0) {
      const m = Math.max(w, h);
      const sets = [
        [[-.25, -.22, .95, 'g1'], [.55, .35, .9, 'g2'], [-.2, .72, .85, 'g3']],
        [[.45, -.3, 1, 'g1'], [-.35, .25, .85, 'g2'], [.4, .75, .9, 'g3']],
        [[-.3, .1, 1, 'g1'], [.5, -.25, .8, 'g3'], [.3, .7, .95, 'g2']],
      ][v % 3];
      return `<div class="bgl">${sets.map(([x, y, s, g]) => `<i class="${g}" style="left:${x * w}px;top:${y * h}px;width:${s * m}px;height:${s * m}px"></i>`).join('')}</div>`;
    },

    /** Konfetti-pöttyök (a szerepszínekből), determinisztikus */
    dots(n, { x0 = 0, y0 = 0, w = 1000, h = 1000, seed = 3, rmin = 5, rmax = 12 } = {}) {
      const cols = ['#FF6B3D', '#FFC845', '#17756E', '#5B5BD6', '#E86A92', '#2FA3D6', '#2E9E6A'];
      let s = seed * 9301 + 49297;
      const rnd = () => (s = (s * 9301 + 49297) % 233280) / 233280;
      let out = '';
      for (let i = 0; i < n; i++) {
        const r = rmin + rnd() * (rmax - rmin);
        out += `<i class="dot" style="left:${x0 + rnd() * w}px;top:${y0 + rnd() * h}px;width:${r * 2}px;height:${r * 2}px;background:${cols[i % cols.length]};opacity:${.55 + rnd() * .4}"></i>`;
      }
      return out;
    },
    /** 1–5 pöttyös jellemzősáv */
    meter(v, { on = '#FF6B3D', off = '#EFE6DA', d = 22, g = 8 } = {}) {
      return `<span class="meter">${[1, 2, 3, 4, 5].map(i => `<i style="width:${d}px;height:${d}px;margin-right:${g}px;background:${i <= v ? on : off}"></i>`).join('')}</span>`;
    },
  };

  /** képek betöltésének megvárása */
  K.settle = async root => {
    const imgs = [...(root || document).querySelectorAll('img')];
    const bgs = [...(root || document).querySelectorAll('.bub')].map(e => (e.style.backgroundImage.match(/url\(["']?(.*?)["']?\)/) || [])[1]).filter(Boolean);
    await Promise.all([
      ...imgs.map(i => i.decode ? i.decode().catch(() => {}) : null),
      ...bgs.map(u => { const i = new Image(); i.src = u; return i.decode().catch(() => {}); }),
      document.fonts.ready,
    ]);
  };
  window.K = K;
})();
