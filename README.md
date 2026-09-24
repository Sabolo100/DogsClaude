# 🐾 Pacsi by DarwinAI

**Kutyafajta-választó web és PWA** · Tervezte és fejlesztette a [DarwinAI](https://www.darwinai.hu) – [www.darwinai.hu](https://www.darwinai.hu)

124 népszerű, Európában tartott kutyafajta egy élő, interaktív felhőben. Szűrj, figyeld, ki ugrik előre (vagy repül ki), hasonlíts össze, töltsd ki a Párkereső kvízt.

### ▶ Élő verzió: **<https://sabolo100.github.io/DogsClaude/>**

Telepítés appként (az első megnyitás után offline is működik):

- **Android (Chrome):** nyisd meg a linket → ⋮ menü → *Alkalmazás telepítése* / *Hozzáadás a kezdőképernyőhöz*
- **iPhone / iPad (Safari):** nyisd meg a linket → Megosztás gomb → *Főképernyőhöz adás*
- **Laptop (Chrome, Edge):** a címsor jobb szélén a telepítés ikon → *Telepítés*

## Használat

| Mit | Hogyan |
|---|---|
| **Egyfájlos verzió** | Nyisd meg a `dist/pacsi.html` fájlt dupla kattintással. Minden benne van (adatok, 128 portré), offline is működik. Az egyetlen külső elem a Google Fonts: offline a rendszer betűtípusai lépnek helyette. |
| **PWA (telepíthető app)** | A `dist/pwa/` mappát a `.github/workflows/pages.yml` munkafolyamat minden `main`-re pusholt változás után automatikusan kiteszi GitHub Pagesre (lásd fent). Bármilyen más statikus tárhelyen is működik (Netlify, Cloudflare Pages): HTTPS-en telepíthető, és az első betöltés után teljesen offline megy. |
| **Helyi kipróbálás** | `python -m http.server 8765 --directory dist`, majd <http://localhost:8765/pacsi.html> vagy <http://localhost:8765/pwa/> |

Az app állapota a URL-ben tárolódik, így linkkel megosztható. Például:
`pacsi.html#f=meret:kicsi;gyerek;lakas&m=s&b=magyar-vizsla` (Kicsi + Gyerekbarát + Lakásba való szűrő, Csak találatok mód, nyitott vizsla-kártya).

## Build

```bash
python tools/build.py
```

Ez futtatja az adatépítőt (`tools/build_data.py`), összefűzi a `src/` fájlokat, beágyazza a képeket, és legyártja a `dist/pacsi.html` fájlt és a `dist/pwa/` mappát (manifest, service worker, ikonok).

**Élesítés:** build után commit + push a `main` ágra. A Pages-munkafolyamat pár percen belül kiteszi az új `dist/pwa/` tartalmat. A service worker verziója a tartalomból számolódik, ezért a már telepített appok a következő megnyitáskor „Új verzió érhető el” értesítést kapnak.

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
