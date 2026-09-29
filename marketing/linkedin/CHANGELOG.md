# Változásnapló – LinkedIn-karusszel (Vibe Coding use case)

A verziószám a `marketing/linkedin/VERSION` fájlban van (FŐ.MELLÉK.JAVÍTÁS). A verzió és a build-azonosító (a forrás és a képernyőképek rövid hash-e) a 12. (+1) oldalon látszik, és a PDF tulajdonságai között is.

## 1.0.0 – 2026-09-29
- **13 oldalas, 1080×1350-es (4:5) karusszel-PDF** a LinkedIn-dokumentumposzthoz: „Amikor egy weboldal intézi a saját kommunikációját”.
  - 1: borító · 2: a kiindulás, idővonal és számok (a Claude Code-munkanaplókból) · 3–4: az app · 5–9: a Marketing Studio (áttekintés, tartalomgyártás, naptár, eDM és kontaktok, indítás és dashboard) · 10–11: a B2B pitch deck (egy teljes dia, majd mind a 17 mozaikban) · 12: +1 – a karusszel is így készült · 13: tanulságok és szponzorkeresés.
- **Forrás:** `src/carousel.html` (böngészőben is megnyitható előnézet). **Build:** `python marketing/tools/build_linkedin.py [--shots]`.
- **Képernyőképek** (`shots/`): a CMS fülei, a pitch deck 17 diája és három hírlevél, headless Edge-dzsel (`tools/linkedin_carousel.mjs shots`). A partneradatbázis képén a nevek, a címek, a városok és az azonosítók elmosva látszanak (magánszemélyek is vannak benne).
- Két menetben renderel: a +1 oldal az első menet oldalképeit mutatja bélyegképként.
