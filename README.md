# 🐾 Pacsi by DarwinAI

**Kutyafajta-választó web és PWA** · Tervezte és fejlesztette a [DarwinAI](https://www.darwinai.hu) – [www.darwinai.hu](https://www.darwinai.hu)

124 népszerű, Európában tartott kutyafajta egy élő, interaktív felhőben. Szűrj, figyeld, ki ugrik előre (vagy repül ki), hasonlíts össze, töltsd ki a Párkereső kvízt.

### ▶ Élő verzió: **<https://pacsit.hu>**

(Tükör, a korábbi cím: <https://sabolo100.github.io/DogsClaude/> – a GitHub Pages továbbra is frissül.)

Telepítés appként (az első megnyitás után offline is működik):

- **Android (Chrome):** nyisd meg a linket → ⋮ menü → *Alkalmazás telepítése* / *Hozzáadás a kezdőképernyőhöz*
- **iPhone / iPad (Safari):** nyisd meg a linket → Megosztás gomb → *Főképernyőhöz adás*
- **Laptop (Chrome, Edge):** a címsor jobb szélén a telepítés ikon → *Telepítés*

## Használat

| Mit | Hogyan |
|---|---|
| **Egyfájlos verzió** | Nyisd meg a `dist/pacsi.html` fájlt dupla kattintással. Minden benne van (adatok, 128 portré), offline is működik. Az egyetlen külső elem a Google Fonts: offline a rendszer betűtípusai lépnek helyette. |
| **PWA (telepíthető app)** | A `dist/pwa/` mappa. Élesben a pacsit.hu szolgálja ki (lásd lent: *Élesítés*), tükörként a GitHub Pages is (`.github/workflows/pages.yml`, minden `main`-re pusholt `dist/pwa/` változás után). HTTPS-en telepíthető, az első betöltés után teljesen offline megy. |
| **Helyi kipróbálás** | `python -m http.server 8765 --directory dist`, majd <http://localhost:8765/pacsi.html> vagy <http://localhost:8765/pwa/> |

Az app állapota a URL-ben tárolódik, így linkkel megosztható. Például:
`pacsi.html#f=meret:kicsi;gyerek;lakas&m=s&b=magyar-vizsla` (Kicsi + Gyerekbarát + Lakásba való szűrő, Csak találatok mód, nyitott vizsla-kártya).

**Első látogatás:** először egy nyitó ablak mondja el, mire való az oldal. A „Kezdjük!” után egy 3 lépéses bemutató következik, amely reflektorfénnyel mutatja meg a felhőt, a szűrőket és a kvízt. Újra megnézhető:
- a Tippek → „Bemutató újra” gombbal;
- a cím végére írt `?bemutato` paraméterrel, pl. <https://sabolo100.github.io/DogsClaude/?bemutato>.

A `?nocoach` paraméter kihagyja a bevezetést (képernyőképekhez és videókhoz).

## Build

```bash
python tools/build.py
```

Ez futtatja az adatépítőt (`tools/build_data.py`), összefűzi a `src/` fájlokat, beágyazza a képeket, és legyártja a `dist/pacsi.html` fájlt és a `dist/pwa/` mappát (manifest, service worker, ikonok).

**Élesítés:**
1. Build, majd commit és push a `main` ágra.
2. **pacsit.hu (Hetzner, Coolify):** a Coolify „Pacsi” projektjében a `pacsi-web` alkalmazás a repóból épít (`Dockerfile`: nginx + `dist/pwa`, beállítás: `deploy/nginx.conf`). A push után a Coolify-ban a **Deploy** gombbal (vagy az API `GET /api/v1/deploy?uuid=<app>` hívásával) indul az új verzió. Nyilvános repóforrás miatt pushra magától nem települ.
3. **Tükör (GitHub Pages):** a Pages-munkafolyamat pár percen belül magától kiteszi az új `dist/pwa/` tartalmat.

A service worker verziója a tartalomból számolódik, ezért a már telepített appok a következő megnyitáskor „Új verzió érhető el” értesítést kapnak.

**Rövid, követhető linkek** (nginx): `pacsit.hu/f/<poszt>` Facebook, `/i` Instagram, `/t` TikTok, `/l/<poszt>` LinkedIn, `/y` YouTube. Mind a `/?utm_source=<platform>&utm_medium=social&utm_campaign=pacsi&utm_content=<poszt vagy bio>` címre irányít.

## Statisztika (névtelen, sütik nélkül)

- **Eszköz:** Umami a saját szerveren (Coolify, „Pacsi” projekt, `pacsi-stat` szolgáltatás), a felülete: <https://stat.pacsit.hu>.
- **Beállítás:** `deploy/site.json`: a végpont, a webhely-azonosító (`website`) és a domainek, ahol mérünk. Üres azonosítóval nem mér.
- **Csak a pacsit.hu-n mér**, a Beállításokban kikapcsolható, és a böngésző „ne kövess” (DNT, GPC) jelzését is tiszteletben tartja. Külső szkriptet nem tölt be: az `src/js/15-stat.js` küldi az eseményeket.
- **Események:**

| Esemény | Tulajdonságok | Mit mutat |
|---|---|---|
| (megtekintés) | forrás, UTM | honnan jönnek |
| `inditas` | mod (telepített app / böngésző), eszkoz, tema | megnyitás módja |
| `kedvenc`, `kedvenc-torles` | fajta | a legkedveltebb fajták |
| `kartya` | fajta | mely fajták érdeklik az embereket |
| `szuro` | szuro (pl. „Méret: Kicsi”, „Gyerekbarát”) | milyen jellemzőkre szűrnek |
| `kereses` | kifejezes, talalat, db | mit keresnek (és mit nem találnak) |
| `kviz-indul`, `kviz-kesz` | tipus, elso | kvíz-befejezési arány, gazditípusok |
| `osszevetes`, `megosztas`, `meglepetes` | fajtak / mit / fajta | összehasonlítás, megosztás |
| `nezet`, `mod`, `bemutato` | nezet / mod / lepes | nézetek, mód, a bemutató tölcsére |
| `telepites`, `telepites-ajanlat` | valasz | PWA-telepítés |

- **Fejlesztéshez:** `localStorage.setItem('pacsi:statlog', 'true')`, ekkor az események a konzolba is kiíródnak.

## Verziózás

- **Hol van a verzió:** a verziószám a `VERSION` fájlban van (pl. `1.4.0`), a változásokat a [`CHANGELOG.md`](CHANGELOG.md) sorolja fel.
- **Minden kiadásnál:**
  1. Növeld a `VERSION`-t.
  2. Írj egy bejegyzést a `CHANGELOG.md`-be.
  3. Futtasd a `python tools/build.py`-t.
  4. Commit és push.
- **Build-azonosító:** a build a forrásból rövid azonosítót is számol.
- **Hol látszik:**
  - mobilon a Tippek panel névjegykártyáján;
  - asztalon a bal oldali panel alján;
  - a böngésző konzoljában;
  - a service worker gyorsítótárának nevében (`pacsi-1.4.0-…`).

## Projektstruktúra

```
Pacsi_kutyavalaszto_specifikacio.md   termék- és UX-specifikáció (a fajtatáblák forrása is!)
data/fajtak_kep.json                  fajta-id, név, képleírás, háttérszín, sprite-pozíció
data/content/part_1…8.json            kártyaszövegek (leírás, kinek ajánlott, egészség, érdekesség …)
data/fajtak.json                      generált, egyesített adatbázis (ne szerkeszd kézzel)
src/index.html, src/app.css           felület
src/js/10-core … 90-main.js           alkalmazáslogika (vanilla JS, keretrendszer nélkül)
src/sw.js                             service worker sablon
img/sheets/                           a 8 generált 4×4-es portré-rácskép + promptjaik
img/portrek/, img/thumbs/             szeletelt portrék (kártya / buborék)
img/sprite-thumbs.webp                a buborékok közös sprite-ja
img/nyito-pacsi.webp                  a nyitó ablak képe (tools/make_hero.py vágja a marketing „pacsi” kulcsképéből)
img/og.jpg                            linkelőnézeti kép (a marketingkészlet p_og terve: marketing/social/images/designs.js → og)
deploy/site.json                      saját domain + a statisztika beállítása (a build olvassa)
deploy/nginx.conf, Dockerfile         a pacsit.hu kiszolgálása (Coolify, Hetzner)
tools/generate_sheets.py              portrégenerálás (OpenAI gpt-image-2)
tools/slice_sheets.py                 rácsfelismerés + szeletelés
tools/build_data.py, tools/build.py   adat- és alkalmazás-build
mockups/                              a specifikáció koncepcióképei
screenshots/                          képernyőképek a kész appról
```

## Új fajta felvétele

1. Specifikáció: új sor a 7.7 (azonosító), 7.8 (jellemvonások) és 7.9 (tagline) táblába.
2. `data/fajtak_kep.json`: új elem (`n`, `slot`, `id`, `nev`, `en`, `bg`, `desc`).
3. Portré: `python tools/generate_sheets.py egyedi <id>`, majd `python tools/slice_sheets.py`.
4. Kártyaszöveg: új bejegyzés egy `data/content/part_*.json` fájlban.
5. `python tools/build.py`

## Fontos

- Az OpenAI API-kulcs (`OpenAI_API.txt`) csak a képgeneráló szkripthez kell. **Soha nem kerül a buildbe**, és ne tedd verziókezelésbe.
- A jellemző-pontszámok és a kártyaszövegek AI-segítséggel készültek. Indulás előtt **szakmai lektorálás szükséges** (kinológus vagy állatorvos).

---

**Pacsi by DarwinAI** · © 2026 [DarwinAI](https://www.darwinai.hu) – www.darwinai.hu
