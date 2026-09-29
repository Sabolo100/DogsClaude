# Pacsi Marketing Studio

A Pacsi kommunikációs anyagai: közösségimédia-videók, posztképek, karusszel, storyk, hirdetések, profilképek, posztszövegek és tartalomnaptár, valamint a heti hírlevél (eDM, Mailchimp) és a partneradatbázis. Mellette van egy belső CMS és egy partneri prezentáció kutyás márkáknak.

Ezek **nem részei** a Pacsi webes és PWA-élményének. A `dist/` mappához és az apphoz nem nyúlnak.

| Mi | Hol |
|---|---|
| **Az app** | <https://pacsit.hu> (tükör: sabolo100.github.io/DogsClaude) · statisztika: <https://stat.pacsit.hu> |
| **CMS** (naptár, letöltés, szövegek szerkesztése) | <https://claude.ai/artifact/2LWG8yFub1TArPhBuWERmH> (privát) · helyben: `marketing/cms/index.html` |
| **Partneri prezentáció – nyilvános link** (márkáknak küldhető) | <https://sabolo100.github.io/pacsi-partner/> · külön repó: `Sabolo100/pacsi-partner` |
| Partneri prezentáció – privát példány, PDF | <https://claude.ai/artifact/J7g3cu6mkjeXwe1TjNtTK2> · `marketing/pitch/Pacsi_partneri_ajanlat.pdf` |
| Kész videók (MP4, 1080×1920) és borítóképek | `marketing/out/videok/` |
| Kész képek (PNG), karusszel PDF/ZIP | `marketing/out/kepek/` |
| **LinkedIn-karusszel** (Vibe Coding use case, 13 oldal, PDF) | `marketing/linkedin/Pacsi_vibe_coding_karusszel.pdf` · forrás: `linkedin/src/carousel.html` · build: `python marketing/tools/build_linkedin.py [--shots]` |
| Posztszövegek, ütemterv, útmutató (forrás) | `marketing/content/content.py` → `content.json` |
| **Hírlevél (eDM):** kampányterv és minden levél (forrás) | `marketing/content/email_plan.py` → `content/email.json` · kész levelek: `marketing/out/email/` |
| Kapcsolati adatbázis (nincs verziókezelve) | `marketing/email/data/contacts.json`, `kapcsolatok.csv` |

## Mappák

```
marketing/
  content/content.py        a teljes tartalomnaptár és minden posztszöveg (egy forrás)
  social/shared/            közös arculat: brand.css, kit.js (buborék, felhő, telefon, logó), ikonok
  social/shared/comp.js     videófuttató (időfüggvény), phone.js (igazi app iframe-ben + szimulált ujj), fx.js (mozgás)
  social/images/            képsablonok: post.html?d=<design>&w=&h=  (designs.js)
  social/videos/            videókompozíciók: v1_felho, v2_kviz, v3_magyar9, v4_terkep
  assets/kv/                AI-kulcsvizuálok (gpt-image-2, a portrékkal azonos gouache stílus)
  assets/screens/           képernyőképek az igazi appról (mobil 3×, asztali 2×)
  out/                      a kész, kiposztolható fájlok
  cms/src/cms.html          a CMS forrása · cms/index.html (helyi) · cms/artifact.html (claude.ai)
  pitch/src/deck.html       a prezentáció forrása · pitch/dist/ (web) · pitch/*.pdf
  content/email_plan.py     a hírlevelek kampányterve és tartalma (egy forrás)
  content/brand.py          arculati csomag és szövegbank (CMS „Arculat” fül), a meglévő forrásokból összegyűjtve
  tools/insights.py         ellenőrzések, kiküldési napló, linkellenőrzés (CMS „Áttekintés” és „Eredmények” fül)
  tools/outreach_queue.py   partnerlevelek ütemezett kiküldése (napi keret, automatikus szünet, STOP-fájl)
  tools/reply_drafts.py     válaszpiszkozatok a partnerek válaszaira (--list, --spec) – semmit nem küld el
  tools/facebook.py         Facebook-oldal: posztok ütemezése a Facebook saját ütemezőjébe, azonnali poszt, statisztika
  tools/youtube.py          YouTube-csatorna: Shorts feltöltése a YouTube saját ütemezőjébe, azonnali közzététel, statisztika
  tools/tests/              a youtube.py automatikus próbái (mock_google.py = a Google protokollját utánzó álszerver)
  social/state/             posztolási naplók (facebook_log.json, youtube_log.json) – NEM kerülnek verziókezelésbe
  email/frame.py            levélkeret és tartalomblokkok (táblás, inline stílusú HTML, 600 px, sötét mód)
  email/img/                fejléckép-kompozíciók (hero.html + edesigns.js, 1200×600)
  email/config.json         feladó, postacím, közösségi profilok, Mailchimp-mód
  email/data/, email/state/ kapcsolati adatbázis és Mailchimp-állapot – NEM kerül verziókezelésbe
  tools/                    render.mjs, capture_screens.mjs, build.py, build_pitch.py, pdf_deck.mjs, generate_keyvisuals.py,
                            email_build.py, email_render.mjs, mailchimp.py, contacts.py, generate_email_kv.py
```

## Hogyan készülnek a videók?

A videók nem videógenerátorral készülnek, hanem **animált weboldalként**. A kompozícióban az **igazi Pacsi app** fut egy telefonkeretben (`dist/pacsi.html` iframe-ben), és egy szimulált ujj nyomogatja: szűrőket kapcsol, kvízt tölt ki, kártyát nyit. Körülötte mozgó feliratok, portré-robbanás és záróképernyő van.

A `render.mjs` headless Edge-ben, **virtuális időben** rögzíti a kompozíciót képkockánként: a `performance.now`, a `requestAnimationFrame`, az időzítők és a CSS-animációk is a render órájára lépnek. Így a kimenet 30 fps-es, akadásmentes, és a gép sebességétől független. A képkockákból az ffmpeg készít H.264 MP4-et, néma hangsávval. A zenét a TikTok vagy Instagram appban kell hozzáadni.

```bash
node marketing/tools/render.mjs video marketing/social/videos/v1_felho.html marketing/out/videok/v1_melyik_kutya_illik_hozzad.mp4
node marketing/tools/render.mjs frames marketing/social/videos/v1_felho.html marketing/tmp/v1 --at 1,3.5,9   # gyors ellenőrzés
```

Böngészőben is megnyithatók előnézetként (valós időben futnak). Ehhez indíts egy helyi szervert a repó gyökerében: `python -m http.server 8790`, majd nyisd meg: <http://localhost:8790/marketing/social/videos/v1_felho.html>.

## Build

```bash
node marketing/tools/capture_screens.mjs            # friss képernyőképek az appról, ha az app változott
python marketing/tools/build.py                      # képek renderelése + borítók + content.json + CMS
python marketing/tools/build.py --no-render          # csak szövegek/CMS (pl. content.py módosítás után)
python marketing/tools/build.py --no-render --links  # + minden link ellenőrzése (content/linkcheck.json → Áttekintés)
python marketing/tools/insights.py                   # az ellenőrzések és a kiküldés állapota a konzolon
python marketing/tools/build_pitch.py --pdf          # prezentáció + tömörített PDF
python marketing/tools/deploy_pitch.py               # prezentáció → nyilvános GitHub Pages (build + commit + push)
```

A `build.py` a `marketing/tmp/upload_needed.json` fájlba írja, mely médiafájlok hiányoznak még a claude.ai-s CMS tárhelyéről. Új vagy módosult fájlnál ezeket fel kell tölteni az artifact eszköztárába. A kapott azonosítók a `cms/assets.json`-ba kerülnek, majd a `cms/artifact.html` újra közzétehető.

## CMS

- **Áttekintés** (1.4.0): mi a teendő ma és a következő 7 napban, hat mutató, teendők és figyelmeztetések, a partnermegkeresések grafikonja, legutóbbi változások. Innen tölthető le a naptár (.ics), és innen másolható a heti jelentés.
- **Eredmények** (1.4.0): a kiposztolt tartalmak számai (elérés, reakció, komment, megosztás, mentés, kattintás), platformonként és a legjobb posztok szerint. Mellette a hírlevelek megnyitása és a partnermegkeresések tölcsére.
- **Arculat** (1.4.0): szövegbank, hashtag-készletek, hangnem, színek, betűk, logók, linkek és UTM-linképítő (forrás: `content/brand.py`).
- **Keresés** (1.4.0): Ctrl+K vagy `/`. Tartalmak, levelek, kapcsolatok (PK-azonosítóval is), ötletek, indítási lépések.
- **Naptár:** mikor, melyik platformra mi megy. Kétnaponta videó, heti 3–4 kép- vagy karusszelposzt, heti LinkedIn-poszt, és a hírlevelek (✉).
- **E-mail:** a kampányterv és minden levél előnézete, tárgysorválasztás, jóváhagyás, ellenőrzés, Mailchimp-állapot.
- **Kapcsolatok:** a partneradatbázis szűrése, állapotkövetés, személyre szabott megkereső levelek, CSV.
- **Tartalmak:** minden elkészült anyag. Előnézet, letöltés, és platformonként szerkeszthető szöveg (TikTok, Instagram, Facebook, LinkedIn) másolás gombokkal. Van még alternatív szöveg, első komment és időzítés.
- **Következő videók:** a naptár üres videóidősávjaihoz tartozó ötletek. Jelöld meg, melyiket kéred, és írj hozzá megjegyzést.
- **Útmutató:** posztolási időpontok, méretek, lépések, profilszövegek.
- **Hol mentődnek a szerkesztések?**
  - A claude.ai-s változatban közös tárolóba, amit Claude is ki tud olvasni. Így a következő körben látszik, mit írtál át, és melyik ötletet kérted.
  - A helyi változatban csak az adott böngészőbe.
- **„Új változatok” gomb:** a claude.ai-s változatban Claude-dal írathatsz új szövegváltozatokat a poszthoz.

## Facebook-oldal: automatikus posztolás

A `tools/facebook.py` a naptár Facebook-idősávjait a **Facebook saját ütemezőjébe** teszi (Meta Graph API). A posztok akkor is kimennek, ha a laptop ki van kapcsolva.
- **Formák:** videó → Reels, kép → fotóposzt, karusszel → több képes poszt, story → oldalstory (csak azonnal).
- **Szöveg:** a CMS-ben szerkesztett Facebook-szöveg és hashtagek.
- **Kimarad:** ami a CMS-ben már ki van pipálva, vagy a naplóban szerepel.
- **Beállítás** (egyszer, kb. 20 perc): lépésenként a [FACEBOOK_API.md](FACEBOOK_API.md) fájlban.

```bash
python marketing/tools/facebook.py setup               # a saját terminálodban: App ID, App Secret, token (rejtett bevitel)
python marketing/tools/facebook.py check               # token, jogosultságok, oldal
python marketing/tools/facebook.py plan                # a Facebook-idősávok állapota
python marketing/tools/facebook.py schedule --yes      # a következő 28 nap esedékes posztjai a Facebook ütemezőjébe
python marketing/tools/facebook.py post k_quiz --now --yes
python marketing/tools/facebook.py insights            # statisztika (a CMS Eredmények fülének formájában is)
```

A `--yes` nélkül semmi nem megy ki. Az oldaltoken a repó gyökerében lévő `Facebook_API.json` fájlban van (gitignore-olt, sosem íródik ki).

## YouTube-csatorna: automatikus feltöltés

A `tools/youtube.py` a naptár YouTube-idősávjait a **YouTube saját ütemezőjébe** teszi (YouTube Data API v3): a videó privátként töltődik fel, és a megadott időpontban maga válik nyilvánossá, a laptop nélkül is.
- **Forma:** csak videó (9:16, legfeljebb 3 perc → Short), borítóképpel. A kép, karusszel, story, hirdetés és profil kimarad.
- **Szöveg:** a CMS-ben szerkesztett YouTube-szöveg: az első sor a cím (a végi hashtagek nélkül), a többi a leírás, alatta a hashtagek.
- **Kimarad:** ami a CMS-ben már ki van pipálva, a naplóban szerepel, vagy a csatornán már fent van (a leírásbeli `pacsit.hu/y/<id>` link vagy a cím alapján ismeri fel, a kézzel feltöltötteket is).
- **A Google korlátja:** az új (2020. 07. 28. utáni), nem auditált API-projektből feltöltött videó **privátra zárolódik, és a Studióban sem tehető nyilvánossá**. Ezért a `test --yes` próba kideríti, hogy a projekt zárolt-e, és éles videót addig nem tölt fel. Kiutak (régi projekt, API-audit, kézi feltöltés) és az audit űrlapja: [YOUTUBE_API.md](YOUTUBE_API.md).
- **Beállítás** (egyszer, kb. 15 perc): lépésenként a [YOUTUBE_API.md](YOUTUBE_API.md) fájlban.

```bash
python marketing/tools/youtube.py setup --client-json "C:\…\client_secret_….json"   # a saját terminálodban (Google-belépés a böngészőben)
python marketing/tools/youtube.py check               # token, csatorna, a próba állapota
python marketing/tools/youtube.py test --yes          # 3 mp-es próbavideó: zárolja-e a Google? (utána törli)
python marketing/tools/youtube.py plan                # a YouTube-idősávok állapota
python marketing/tools/youtube.py copy v2             # cím, leírás, fájl, időpont – kézi (Studio) feltöltéshez
python marketing/tools/youtube.py schedule --yes      # a következő 28 nap esedékes videói a YouTube ütemezőjébe
python marketing/tools/youtube.py insights            # statisztika (a CMS Eredmények fülének formájában is)
```

A `--yes` nélkül semmi nem töltődik fel. A kulcsok és a token a repó gyökerében lévő `YouTube_API.json` fájlban vannak (gitignore-olt, sosem íródnak ki). Automatikus próbák: `python marketing/tools/tests/test_youtube.py`.

## Hírlevél (eDM) és partneradatbázis

**Két külön lista – ez a rendszer alapja:**
- **Kapcsolatok (saját adatbázis):** 887 kutyás szervezet és vállalkozás, nyilvános oldalakon közzétett címmel, forrással.
  - Kategóriák: fajtaklubok, tenyésztők, menhelyek, kutyaiskolák, állatorvosok, szolgáltatások, média, cégek, közösségek.
  - Innen csak **egyedi, személyre szabott** megkeresés megy, a saját postafiókból. A CMS Kapcsolatok füle kész levelet ad minden kapcsolathoz.
- **Mailchimp-közönség („Pacsi – heti kutyás levél”):** csak az kerül bele, aki feliratkozott (dupla megerősítéssel), vagy írásban kérte.
  - A Mailchimp szabályzata tiltja a vásárolt, a nyilvános oldalakról gyűjtött és a „partner” listákat, ezekért felfüggeszti a fiókot.
  - Magánszemélynek reklámcélú levél csak előzetes hozzájárulással küldhető (Grt. 6. §).

**Kampányterv (2026. okt. 1. – dec. 30.):**
- Indulás: okt. 1., 3. és 8.
- Heti Pacsi-levél csütörtökönként 10:00-kor (12 szám).
- Havi partnerlevél kedden.
- Háromrészes üdvözlő sorozat az új feliratkozóknak.
- Minden levél a közösségi naptár témájára épül. Novembertől a levelekhez javasolt posztok is tartoznak (CMS → E-mail → levél → Közösségi kapcsolódás).

**Munkafolyamat:**
```bash
python marketing/tools/contacts.py          # kutatási fájlok → kapcsolati adatbázis (tisztítás, duplikátumok, MX-ellenőrzés)
python marketing/tools/email_build.py       # levélképek (≤1200×1200) + levelek + ellenőrzés → content/email.json
python marketing/tools/build.py --no-render # CMS (E-mail és Kapcsolatok fül)
python marketing/tools/mailchimp.py ping    # a kulcs ellenőrzése (Mailchimp_API.txt a repó gyökerében)
python marketing/tools/mailchimp.py setup   # közönség + mezők + „partner” címke
python marketing/tools/mailchimp.py push L1 W01 --test te@pelda.hu   # PISZKOZAT + tesztlevél
python marketing/tools/mailchimp.py sync    # állapot és statisztika vissza a CMS-be
```

**Lépések:**
1. **Jóváhagyás:** a CMS-ben a levélnél „Jóváhagyom”, és kiválasztod a tárgysort. Ez a claude.ai-s közös tárolóba kerül, Claude onnan olvassa ki.
2. **Mailchimp:** Claude feltölti a jóváhagyott levelet **piszkozatként**. A Mailchimpben tesztlevél után kézzel küldöd ki.
3. **Automatikus kiküldés később:** a `config.json` `mailchimp.mode` beállításával.
   - `schedule`: fizetős csomagon a Mailchimp maga ütemez.
   - `send-due`: az ingyenes csomagon egy időzítő küldi ki a lejárt, jóváhagyott leveleket.

**Mailchimp-korlátok:**
- **Képek:** legfeljebb 1200×1200 px. A build ellenőrzi, a feltöltő pedig visszautasítja a nagyobbat.
- **Ingyenes csomag:** 250 kontakt, havi 500 küldés, nincs ütemezés, egylépéses útvonal. Heti levélhez kb. 120 feliratkozó fölött fizetős csomag kell.
- **Saját HTML:** egyes csomagokon korlátozott lehet. Az első `push` megmutatja, hogy a fiók elfogadja-e.

**Még kitöltendő** (`marketing/email/config.json`, a CMS E-mail fülén is látszik):
- feladó e-mail-cím és a domain hitelesítése (DKIM és DMARC a Rackhost DNS-ében);
- cégnév és postacím;
- az aláíró neve;
- a közösségi profilok címe;
- az adatkezelési tájékoztató webcíme (tervezet: `marketing/email/adatkezelesi_tajekoztato.md`).

## Partneri prezentáció

- **Léptetés:** ← / → billentyű, lapozás vagy húzás; a T billentyű tartalomjegyzéket nyit.
- **Mobilon:** a diák egymás alatt görgethetők.
- **Nyilvános link:** <https://sabolo100.github.io/pacsi-partner/>.
  - Belépés nélkül bárki megnyithatja, akinek elküldöd.
  - A keresőkben nem jelenik meg (`noindex`).
  - Az apptól és a CMS-től független, külön repóból fut.
- **Személyre szabás:** a link végére írd a márka nevét, a szóközök helyére kötőjelet. Például <https://sabolo100.github.io/pacsi-partner/#p-Royal-Canin>. Ekkor a nyitó és az integrációs dia a márka nevével jelenik meg.
- **Frissítés:** a `pitch/src/deck.html` módosítása után futtasd a `python marketing/tools/deploy_pitch.py` parancsot. A claude.ai-s példány külön, privát másolat.
- **Kapcsolat:** a prezentációban kapcsolatként most csak a www.darwinai.hu szerepel. Ha kell név, e-mail vagy telefon, a `pitch/src/deck.html` 16. diáján add hozzá.

## Verziózás

- **CMS és tartalomcsomag:**
  - verzió: `marketing/VERSION`;
  - változásnapló: `marketing/CHANGELOG.md`;
  - a verzió és a build-azonosító a CMS láblécében és fejlécében látszik.
- **Prezentáció:**
  - verzió: `marketing/pitch/VERSION`;
  - változásnapló: `marketing/pitch/CHANGELOG.md`;
  - a verzió és a build-azonosító az utolsó dián látszik.

## Fontos

- A kártyaszövegek és az érdekességek AI-segítséggel készültek (lásd a fő README-t). A posztokba csak jól ismert, ellenőrizhető tények kerültek. Élesítés előtt ezeket is érdemes egy szakemberrel átnézetni.
- **A prezentáció számai forrásból jönnek** (FEDIAF, Magyar Állatorvosok Lapja, TÁRKI, NIQ/Trade magazin, NÉBIH, DataReportal).
  - A forráslista az utolsó dián van.
  - Ahol a mérések eltérnek, a dia ezt jelzi.
- A kulcsvizuálokat (`assets/kv/`) az OpenAI gpt-image-2 generálta, a portrékkal azonos stílusban. A kulcs (`OpenAI_API.txt`) soha nem kerül a kimenetbe.
- **Méret:** a `marketing/out` és a `marketing/assets` mappa együtt kb. 180 MB bináris fájl. A repó publikus, ezért commit előtt érdemes eldönteni, hogy ezek felkerüljenek-e. A renderelt fájlok a forrásból bármikor újragenerálhatók; egy lehetőség a Git LFS.
