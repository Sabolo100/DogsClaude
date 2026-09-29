# Változásnapló – Pacsi partneri ajánlat (pitch deck)

A verziószám a `marketing/pitch/VERSION` fájlban van. A verzió és a build-azonosító az utolsó (Források) dián látszik.

## 1.1.4 – 2026-09-29
- **Javítás – a prezentáció újra lapozható.** Az 1.1.3-ban a QR-kód sorába került megjegyzés (`// …`) a sor többi részét is kikommentezte, ezért a teljes script szintaxishibával leállt. Következmények: nem volt diavetítés és lapozás, a videók nem indultak, a tartalomjegyzék és a partnernév (#p-…) sem működött.
- **Javítás – a letölthető PDF** emiatt 17-szer a nyitó diát tartalmazta. Újragenerálva, diánként egy oldal.

## 1.1.3 – 2026-09-25
- **Új domain:** a „Próbálja ki most” link és a QR-kód a <https://pacsit.hu> címre mutat (eddig a GitHub Pages-es cím). A statisztikában „partner / deck” forrásként látszik (`utm_source=partner&utm_medium=deck`).
- **Pontosítás a méréshez:** a pacsit.hu-n már él a sütimentes, névtelen statisztika (Umami, saját szerver). Ezért módosult három dia:
  - 7. dia: „0 regisztráció és süti – csak névtelen statisztika” (eddig: „nincs adatgyűjtés”);
  - 12. dia: a mérés már él, a partnerblokkok mérésével bővül;
  - 15. dia: „Él a v1.6 – pacsit.hu”.

## 1.1.2 – 2026-09-24
- **Telefonos nézet:** a nyitó dia szövege a teljes szélességet kihasználja.

## 1.1.1 – 2026-09-24
- **Telefonos nézet:** a nyitó dián a logó („Pacsi”) már nem törik két sorba.

## 1.1.0 – 2026-09-24
- **Nyilvános webes változat:** külön GitHub Pages-oldal a saját `Sabolo100/pacsi-partner` repójában. Az apptól és a CMS-től független, belépés nélkül megnyitható.
  - Cím: <https://sabolo100.github.io/pacsi-partner/>
  - Kitelepítés: `python marketing/tools/deploy_pitch.py`
- **Linkelőnézet:** e-mailben, LinkedInen és Messengerben a nyitó dia képe jelenik meg a link mellett.
- **Keresők:** az oldal nem jelenik meg a keresőkben (`noindex`), de a linkkel bárki megnyithatja.
- **PDF-letöltés:** a nyilvános oldal navigációjában letöltés gomb van. A claude.ai-s példány kerete ezt nem engedi, ott nincs ilyen gomb.

## 1.0.0 – 2026-09-24
- **17 dia, magyarul, kutyás márkák marketingeseinek.** A diák témái:
  - a döntés pillanata;
  - a probléma, forrásolt számokkal;
  - a piac;
  - a megoldás;
  - a termék;
  - számok és perszónák;
  - miért érdemes partnernek lenni;
  - integrációs látványtervek;
  - partnercsomagok;
  - mérés;
  - közösségi jelenlét;
  - márkabiztonság;
  - ütemterv;
  - következő lépések, QR-kóddal;
  - források.
- **Webes, léptethető prezentáció:**
  - billentyűvel, húzással vagy görgetéssel léptethető, tartalomjegyzékkel;
  - telefonon a diák egymás alatt görgethetők;
  - az aktív dián néma videók futnak.
- **Személyre szabható link:** `#p-Markanev`.
- **PDF-változat:** 17 oldal, 3,9 MB, e-mailben is küldhető.
