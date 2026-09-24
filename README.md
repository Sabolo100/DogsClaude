# 🐾 Pacsi by DarwinAI

**Kutyafajta-választó web és PWA** · Tervezte és fejlesztette a [DarwinAI](https://www.darwinai.hu) – [www.darwinai.hu](https://www.darwinai.hu)

124 népszerű, Európában tartott kutyafajta egy élő, interaktív felhőben. Szűrj, figyeld, ki ugrik előre (vagy repül ki), hasonlíts össze, töltsd ki a Párkereső kvízt.

## Használat

| Mit | Hogyan |
|---|---|
| **Egyfájlos verzió** | Nyisd meg a `dist/pacsi.html` fájlt dupla kattintással. Minden benne van (adatok, 128 portré), offline is működik. Az egyetlen külső elem a Google Fonts: offline a rendszer betűtípusai lépnek helyette. |
| **PWA (telepíthető app)** | Töltsd fel a `dist/pwa/` mappa tartalmát bármilyen statikus tárhelyre (GitHub Pages, Netlify, Cloudflare Pages). HTTPS-en telepíthető, és az első betöltés után teljesen offline működik. |
| **Helyi kipróbálás** | `python -m http.server 8765 --directory dist`, majd <http://localhost:8765/pacsi.html> vagy <http://localhost:8765/pwa/> |

Az app állapota a URL-ben tárolódik, így linkkel megosztható. Például:
`pacsi.html#f=meret:kicsi;gyerek;lakas&m=s&b=magyar-vizsla` (Kicsi + Gyerekbarát + Lakásba való szűrő, Csak találatok mód, nyitott vizsla-kártya).

## Build

```bash
python tools/build.py
```

Ez futtatja az adatépítőt (`tools/build_data.py`), összefűzi a `src/` fájlokat, beágyazza a képeket, és legyártja a `dist/pacsi.html` fájlt és a `dist/pwa/` mappát (manifest, service worker, ikonok).

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
