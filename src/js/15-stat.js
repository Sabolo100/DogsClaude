/* ==========================================================================
   Névtelen statisztika – Umami a saját szerverünkön (stat.pacsit.hu), sütik és személyes adat nélkül
   --------------------------------------------------------------------------
   Csak a saját domainen él (SITE.stat.hosts), és csak ha van website-azonosító (deploy/site.json).
   Nem küld semmit, ha a látogató kikapcsolta (Tippek → Beállítások), vagy a böngészője „ne kövess”
   (Do Not Track / Global Privacy Control) jelzést ad. Külső szkriptet sem tölt be: az eseményeket
   ugyanabban a formában küldi az Umami /api/send végpontjára, mint a hivatalos követőkód.
   Fejlesztéshez: localStorage 'pacsi:statlog' = true → minden esemény a konzolba is kiíródik.
   ========================================================================== */
const STAT = SITE.stat || {};
const statAllowed = () => !!STAT.website && !ARTIFACT && (STAT.hosts || []).includes(location.hostname) && !store.get('nostat', false)
  && navigator.doNotTrack !== '1' && window.doNotTrack !== '1' && !navigator.globalPrivacyControl;
// csak külső hivatkozó számít (a saját oldalon belüli nem)
const STAT_REF = (() => { try { const r = document.referrer; return r && new URL(r).origin !== location.origin ? r : ''; } catch (e) { return ''; } })();
let statCache = '', statOff = false;

/* stat() = oldalmegtekintés (az UTM-paraméterek innen látszanak); stat('név', { tulajdonság: érték }) = esemény */
function stat(name, data) {
  if (store.get('statlog', false)) console.info('[stat]', name || 'oldalmegtekintés', data || '');
  if (statOff || !statAllowed()) return;
  const payload = {
    website: STAT.website, hostname: location.hostname, url: location.origin + location.pathname + location.search,   // a # utáni rész (szűrők) nem kell
    referrer: STAT_REF, title: document.title, language: navigator.language, screen: `${screen.width}x${screen.height}`, tag: `v${APP_VERSION}`,
  };
  if (name) { payload.name = name.slice(0, 50); if (data) payload.data = data; }
  try {
    fetch(STAT.endpoint, {
      method: 'POST', keepalive: true, credentials: 'omit', body: JSON.stringify({ type: 'event', payload }),
      headers: { 'Content-Type': 'application/json', ...(statCache ? { 'x-umami-cache': statCache } : {}) },
    }).then(r => (r.ok ? r.json() : null)).then(r => { if (r) { statOff = !!r.disabled; statCache = r.cache || statCache; } }).catch(() => {});
  } catch (e) { /* offline vagy tiltott: a statisztika nem fontosabb az appnál */ }
}

/* Olvasható szűrőnév a kimutatásokhoz (pl. „Méret: Kicsi”, „Gyerekbarát”) */
function statFilter(k, v) {
  if (k === 't') return (TBY[v] && TBY[v].l) || v;
  if (k === 'meret') return 'Méret: ' + (SIZE_L[v] || v);
  if (k === 'energia') return 'Energia: ' + ((ENERGY.find(e => e[0] === v) || [])[1] || v);
  if (k === 'szor') return 'Szőr: ' + (COAT_L[v] || v);
  if (k === 'szerep') return 'Szerep: ' + (ROLE_L[v] || v);
  if (k === 'fci') return `FCI ${v}. ${FCI[v] || ''}`.trim();
  return `${k}: ${v}`;
}

/* Keresés: gépelés után 1,5 mp szünettel egyszer, ékezet nélkül, legfeljebb 40 karakter */
let statQTimer = 0, statQLast = '';
function statSearch(q, hits) {
  const nq = norm(q).trim().replace(/\s+/g, ' ').slice(0, 40);
  if (nq.length < 2 || nq === statQLast) return;   // a kereső bezárása (üres keresés) nem törli a függő eseményt
  clearTimeout(statQTimer);
  statQTimer = setTimeout(() => {
    statQLast = nq;
    stat('kereses', { kifejezes: nq, talalat: hits[0] ? hits[0].b.nev : '–', db: hits.length });
  }, 1500);
}

/* Indulás: oldalmegtekintés + hogyan használják (telepített app vagy böngésző, mobil vagy asztal) */
function statStart() {
  stat();
  const app = matchMedia('(display-mode: standalone)').matches || navigator.standalone;
  stat('inditas', { mod: app ? 'telepített app' : 'böngésző', eszkoz: S.mobile ? 'mobil' : 'asztali', tema: isDark() ? 'sötét' : 'világos' });
}
addEventListener('appinstalled', () => stat('telepites', { mod: 'app' }));
