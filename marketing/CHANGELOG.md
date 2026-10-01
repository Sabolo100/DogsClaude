# Változásnapló – Pacsi Marketing Studio

A verziószám a `marketing/VERSION` fájlban van (FŐ.MELLÉK.JAVÍTÁS). A build-azonosító a tartalom és a CMS forrásának rövid hash-e, és a CMS-ben is látszik.

## 1.7.0 – 2026-10-01
- **Új: „Google Ads (fizetett)” kártya az Indítás fülön** (9 lépés): MCC és „Pacsit” ügyfélfiók (HUF, Budapest), automatikus ajánlás-alkalmazás és gclid kikapcsolása, Google Cloud projekt + Google Ads API + *Apply for access* (Explorer; a developer token 2026. szept. 9-én megszűnt), szolgáltatásfiók és JSON-kulcs (a céges szervezeti szabály figyelmeztetésével), hozzáadás az MCC-hez, csak-olvasó Umami-felhasználó, kulcsok a szerver titkos változóiba, majd „kész”. A részletes leírás az Ads Engine repójában van (`docs/GOOGLE_ADS_BEALLITAS.md`).
- A fizetett csatornát egy **önálló szolgáltatás (Ads Engine)** kezeli a szerveren; a CMS nem hívja a Google-t. A keretet és a szünetet az ember állítja a Google Ads-ben. A kommunikációs CMS tervrajza új **8.9** fejezetet kapott (`KOMMUNIKACIOS_CMS_LEIRAS.md` 1.1.0).
- Csak hozzáadás: a meglévő fülek, adatok és állapotok működése nem változott. Az Indítás haladásjelzője az új lépéseket is számolja.
- A `.gitignore` a Google-szolgáltatásfiók kulcsfájljait is kizárja.

## 1.6.0 – 2026-09-29
- **Új: YouTube Shorts feltöltése és ütemezése** (`tools/youtube.py`, YouTube Data API v3, csak szabványos Python).
  - A naptár YouTube-idősávjai privát feltöltésként, `publishAt` időponttal kerülnek a **YouTube saját ütemezőjébe**: a videó a megadott időpontban maga válik nyilvánossá, a laptop nélkül is.
  - Folytatható feltöltés 8 MB-os szeletekben (hálózati hibánál onnan folytatja, ahol megszakadt), borítókép, kategória (Kisállatok és állatok), magyar nyelv, „nem gyerekeknek készült”.
  - A CMS YouTube-szövegéből: az első sor a cím (a végi hashtagek nélkül, legfeljebb 100 karakter), a többi a leírás, alatta a hashtagek; a hashtagekből lesznek a kulcsszavak.
  - Csak videó megy a YouTube-ra; a kép, karusszel, story, hirdetés és profil kimarad. A `plan` ffprobe-bal ellenőrzi, hogy a fájl álló és legfeljebb 3 perces (Short) legyen.
  - Parancsok: `setup`, `check`, `test`, `plan`, `copy`, `schedule`, `post`, `scheduled`, `update`, `cancel`, `videos`, `adopt`, `link`, `insights`.
  - `--yes` nélkül semmit nem tölt fel, csak kiírja, mit tenne. `--draft`: privát piszkozat ütemezés nélkül.
- **A Google korlátja és az ellenőrző próba.** A 2020. július 28. után létrehozott, nem auditált API-projektből feltöltött videó privátra zárolódik, és a Studióban sem tehető nyilvánossá (nincs fellebbezés).
  - A `test --yes` egy 3 mp-es, nem listázott próbavideóval kideríti, hogy a projekt zárolt-e, majd törli a videót.
  - A `schedule` és a `post` addig nem tölt fel éles videót, amíg a próba sikeres nem volt (`--skip-check` kikapcsolja).
  - Kiutak (régi projekt, API-audit, kézi feltöltés a `copy` segítségével) és az audit űrlapjának teljes listája: `marketing/YOUTUBE_API.md`.
- **Nincs duplikáció.** Kimarad minden idősáv, amely a CMS-ben ki van pipálva, a naplóban szerepel (`social/state/youtube_log.json`, minden feltöltés után mentve), vagy a csatornán már fent van.
  - A csatorna átnézése a leírásban lévő követhető link (`pacsit.hu/y/<id>`) vagy a cím alapján ismeri fel a kézzel feltöltött videókat (`adopt`, `link`).
  - Ha a tartalom a CMS-ben már „Kiposztolva”, a jövőbeli idősáva „ellenőrizd” jelzést kap, és csak külön kérésre (`--only`) töltődik fel (ugyanaz a szabály, mint a `facebook.py`-nál).
- **Beállítás:** `youtube.py setup` a felhasználó saját termináljában. A Google Cloud „Asztali alkalmazás” OAuth-kliensét használja (helyi visszahívás + PKCE, `youtube` jogosultság), és csak a Pacsi-csatornát (`UCO8Hj95k0ouOE-wQmhk6TpA`) fogadja el.
  - A kliens titkát és a frissítő tokent a gitignore-olt `YouTube_API.json` tartalmazza; az eszköz soha nem írja ki. Útmutató: `marketing/YOUTUBE_API.md`.
- **Statisztika:** az `insights` kimenete (megtekintés → „elérés”, kedvelés, komment) a CMS Eredmények fülének formájában van.
- **A CMS felülete nem változott.** A verziót a `youtube.py --version` is kiírja.
- **Ellenőrzés:** a Google protokollját utánzó helyi álszerveren 98 automatikus próba fut (`tools/tests/test_youtube.py`, `python marketing/tools/tests/test_youtube.py`): OAuth, feltöltés hibák után is, ütemezés, duplikációvédelem, zárolt projekt, minden parancs. Szintetikus tartalommal és rögzített idővel dolgozik, a valódi naptárhoz, naplóhoz és kulcsokhoz nem ér. Élesben az első `test --yes` igazolja a Google tényleges viselkedését.

## 1.5.1 – 2026-09-29
- **Élesítve:** a Pacsi Facebook-oldalán 16 poszt ütemezve a Facebook saját ütemezőjébe (szept. 30. – okt. 21.): 3 Reels, 12 fotóposzt, 1 hétképes poszt.
  - A CMS közös tárolójában a Facebook-idősávjaik kipipálva.
  - A korábban kézzel kitett bemutatkozó posztot és a v1 videót is kipipáltam.
- **Javítás:** a hirdetés organikus idősávja eddig a hirdetés formátumával ment volna ki (Elsődleges szöveg, Címsor, CTA-gomb, fizetett UTM-es cél-URL).
  - Mostantól csak az elsődleges szöveg és a követhető rövid link kerül ki (`pacsit.hu/f/<id>`).
  - A h_cuki posztot ezzel a szöveggel újraütemeztem.
- **Javítás:** a `facebook.py scheduled` a Reels posztjait is a naplóhoz párosítja (ütemezési idő szerint). Eddig ezek „nem a naplóból” jelzéssel jelentek meg.

## 1.5.0 – 2026-09-29
- **Új: Facebook-oldal automatikus posztolása** (`tools/facebook.py`, Meta Graph API v25.0, csak szabványos Python).
  - A naptár Facebook-idősávjai a **Facebook saját ütemezőjébe** kerülnek, így a posztok akkor is kimennek, ha a laptop ki van kapcsolva.
  - Az ütemezés legalább 15 perccel későbbre és legfeljebb 28 nappal előre kérhető.
  - Formák: videó → Reels (borítóképpel), kép → fotóposzt, karusszel → több képes poszt, story → oldalstory (csak azonnal).
  - Kimarad a hirdetés (kivéve az „organikus” idősávot) és a profil.
  - A szöveg a CMS-ben szerkesztett Facebook-szöveg és hashtagek, a követhető rövid linkkel.
  - Parancsok: `setup`, `check`, `test`, `plan`, `schedule`, `post`, `scheduled`, `cancel`, `posts`, `insights`.
  - `--yes` nélkül semmit nem tesz ki, csak kiírja, mit tenne.
- **Nincs duplikáció.** Kimarad minden idősáv, amely a CMS-ben ki van pipálva vagy a naplóban szerepel (`social/state/facebook_log.json`, minden poszt után mentve).
  - Ha a tartalom a CMS-ben már „Kiposztolva”, a jövőbeli idősáva „ellenőrizd” jelzést kap, és csak külön kérésre (`--only`) ütemeződik.
- **Beállítás:** `facebook.py setup` a felhasználó saját termináljában, rejtett bevitellel.
  - A rövid életű tokent nem lejáró oldaltokenre cseréli.
  - A tokent a gitignore-olt `Facebook_API.json` fájlba menti; az App Secret nem kerül bele.
  - Útmutató: `marketing/FACEBOOK_API.md`.
- **Statisztika:** az `insights` kimenete (elérés, reakció, komment, megosztás, kattintás) a CMS Eredmények fülének formájában van. Innen tölthető fel a közös tárolóba.
- **Új fájl:** app-ikon a Meta-apphoz (`out/kepek/p_avatar_1024.png`, 1024×1024).
- **A CMS felülete nem változott.** A verziót a `facebook.py --version` is kiírja.

## 1.4.1 – 2026-09-28
- **Partnermegkeresések ütemezett kiküldése** (`tools/outreach_queue.py`, 2026-09-26 óta használatban, eddig nem szerepelt a naplóban):
  - egyenként, véletlen szünettel (`--gap 3-6`) vagy egy időpontig elosztva (`--until 16:30`); `--status`, `--dry-run`;
  - szervezetenként egy levél; előbb a megírt piszkozatok, utána kategóriánként;
  - vészfék: `email/state/STOP`; napi felső határ 150; indulás előtt kigyűjti a visszapattanásokat;
  - a napló írása atomi (ideiglenes fájl → csere), és 300 MB szabad hely alatt nem küld (a 2026-09-26-i, megtelt lemez miatti naplóvesztés után).
- **Új: automatikus szünet.** Futás közben 5 levelenként újra megnézi a visszapattanásokat. Ha aznap legalább 3 cím visszapattant, és ez több az aznapi levelek 5%-ánál, létrehozza a STOP fájlt az okkal, és leáll.
- **Új: a CMS-ben kezelt kapcsolatok kimaradnak.** Aki a CMS-ben már nem „Új” állapotú (megkeresve, válaszolt, nem kér, hibás cím…), nem kap levelet (`email/state/contact_overrides.json`, a közös tárolóból másolva).
- **Kimaradnak a biztosan rossz címek:** `gmail.hu` (elírás), megszűnt szolgáltatók (`freeweb.hu`, `freestart.hu`), és a nem kutyás szervezet (PK0566, macskamentés).
- **Új: válaszpiszkozatok** (`tools/reply_drafts.py`). A felhasználó kérése: minden érdemi partnerválaszra rövid, kedves válasz készül piszkozatként a Drafts mappába (ötletre: feljegyeztük, a következő frissítésnél megpróbáljuk betenni; kérésre: azon leszünk, hogy teljesítsük). A felhasználó nézi át és küldi el.
  - `--list`: a megválaszolatlan válaszok; az automatikus válaszokat és a visszapattanásokat kiszűri.
  - `--spec valaszok.json`: piszkozat a levelezési szálban (In-Reply-To, References), idézettel, a többi címzett másolatban. Semmit nem küld el.
  - Első kör: 3 válasz (Magyar Pumi Klub, Vigyél Haza Alapítvány, Eb-Árvaház).
- **A felhasználó döntése (2026-09-28): címellenőrzés nélkül, napi 20 levéllel folytatódik a kiküldés.** Ezért az automatikus szünet mostantól csak aznapra szól (`email/state/PAUSE`, benne a dátum és az ok), másnap magától folytatódik. A `STOP` fájl kézi vészfék maradt. A CMS Áttekintése a napi szünetet is mutatja.
- **Javítás:** az átmeneti késleltetést (pl. megtelt postafiók, „Delayed”, 4.x.x) a kiküldő nem számolja visszapattanásnak. 2026-09-28-án egy ilyen értesítés miatt kapcsolt be az automatikus szünet; a valódi arány 2/15 volt, így a szünet ettől függetlenül is indokolt maradt.
- **Javítás:** a PK0621 (Ebgondolat Kutyaiskola) 2026-09-26-án hálózati hiba miatt nem ment ki. A helyreállított napló tévesen elküldöttnek jelölte; újra a sorba került (a CMS-ben is).

## 1.4.0 – 2026-09-26
- **Új CMS-fül: Áttekintés.** Egy képernyőn, mi a teendő ma és a következő 7 napban.
  - Esedékes és lekésett posztok, levelek és videóötletek. Minden sorra kattintva ott folytathatod, ahol dolgod van.
  - Hat mutató: kiposztolt idősávok, esedékes feladatok, jóváhagyott levelek, elküldött partnerlevelek, válaszok, a profilindítás állása.
  - **Teendők és figyelmeztetések** egy listában: lekésett idősáv, jóváhagyásra váró levél, esedékes emlékeztető, túl hosszú átírt szöveg, hiányzó beállítás, kitöltendő levél, magas visszapattanás, nem működő link.
  - **Partnermegkeresések:** naponkénti grafikon (kézbesítve / visszapattant), visszapattanási arány, hátralévő sor kategóriánként, szünet (STOP) állapota, a visszapattant címek listája.
  - **Legutóbbi változások:** ki mit módosított a közös tárolóban (szöveg, jóváhagyás, kapcsolat, indítás, ötlet, eredmény).
  - **Naptárexport (.ics):** posztok, levelek és videóötletek Google Naptárba, Outlookba vagy Apple Naptárba, 15 perces emlékeztetővel. Minden esemény visszamutat a CMS-re.
  - **Heti jelentés:** egy gombbal másolható összefoglaló (mi ment ki, mi késik, hírlevél, megkeresések, jövő hét, teendők).
- **Új CMS-fül: Eredmények.** A kiposztolt idősávokhoz beírható az elérés, a reakció, a komment, a megosztás, a mentés és a kattintás.
  - Összesítés platformonként, a legjobb posztok aktivitás szerint, a hírlevelek megnyitása és kattintása, a partnermegkeresések tölcsére.
  - Az adatok új közös gyűjteménybe mennek (`metrics/<tartalom-id>`), Claude is látja őket.
- **Új CMS-fül: Arculat.** Szövegbank (12 kész szöveg karakterszámmal), hashtag-készletek, hangnem, színek, betűk, logók és borítók letöltéssel, fontos és rövid linkek.
  - **UTM-linképítő** előbeállításokkal. Egységes, ékezet nélküli paramétereket ad, és megmutatja az egyenértékű rövid linket (pacsit.hu/f/<id>).
- **Globális keresés** (Ctrl+K, / vagy a fejléc Keresés gombja): tartalmak, levelek, kapcsolatok (PK-azonosítóval is), ötletek, indítási lépések, szövegbank. Ékezet nélkül is talál.
- A fejlécben a fülsor külön sorba került, hogy mind a tíz fül elférjen.
- **Build:**
  - `content/brand.py`: az arculati csomag, a meglévő forrásokból összegyűjtve.
  - `tools/insights.py`: ellenőrzések és a kiküldési napló összesítése. A `--links` kapcsolóval minden linket ellenőriz (eredmény: `content/linkcheck.json`); az első futáskor 78 cél, egyik sem hibás.
- **Leírás:** `KOMMUNIKACIOS_CMS_LEIRAS.md` a repó gyökerében. Általános tervrajz, amely alapján bármely app vagy weboldal ugyanilyen felépítésű kommunikációs CMS-t kaphat.

## 1.3.0 – 2026-09-25
- **Új CMS-fül: Indítás.** 56 kipipálható lépés a közösségi profilok elindításához, platformonként. A pipák a közös tárolóba mentődnek.
  - Platformok: Facebook-oldal, Instagram, TikTok, YouTube (Shorts), LinkedIn-oldal, plusz egy előkészítő és egy befejező rész.
  - Minden szöveg másolható, karakterszámmal (bio, leírás, szlogen). Minden kép letölthető, a követhető linkek is megvannak (pacsit.hu/f, /i, /t, /y, /l).
- **Új képek:** YouTube-szalagcím (2560×1440, a tartalom a minden eszközön látszó középső sávban) és LinkedIn céges borító (1128×191).
- **YouTube Shorts:** a 4 videóhoz YouTube-cím és -leírás (pacsit.hu/y/… követhető linkkel), és YouTube-idősávok a naptárban.
- **Megkeresések:** az első 20 partnerlevél kiküldése a hello@pacsit.hu-ról, kétpercenként (`tools/outreach_send.py`).

## 1.2.1 – 2026-09-25
- **Állandó azonosító minden e-mail-címhez:** `PK0001`–`PK0971`. A 961 cím és a 10 e-mail nélküli szervezet mind kapott egyet.
  - Egy nyilvántartás (`email/data/id_registry.json`) őrzi őket, ezért újraépítéskor sem változnak, és egy azonosító sosem kerül újra kiosztásra.
- **CSV:** soronként egy e-mail-cím, a sor elején az azonosítóval. Ez a `kapcsolatok.csv`-re és a CMS-ből letöltött CSV-re is igaz.
- **CMS:** az azonosító látszik a táblázatban, az adatlapon minden e-mail-cím előtt, és rá is lehet keresni (pl. PK0042).
- **Követhetőség:** a partnerek követhető linkjében (`utm_content`) az azonosító áll, így a statisztika is párosítható.
- **Mailchimp:** új mező a közönségben (PID, „Pacsi azonosító”). A partnerek importja ezt is kitölti.
- **Mailchimp beállítva:** „Pacsi” közönség, ARworks Kft. lábléccel. Az L1 piszkozat, a tesztlevél elment.

## 1.2.0 – 2026-09-25
- **Új: hírlevélrendszer (eDM) Mailchimphez.** A Pacsi heti levélben is kommunikál: kampányterv év végéig, kész levelek, Mailchimp-eszköz, kapcsolati adatbázis.
  - **21 kész levél:**
    - indulás: okt. 1., 3. és 8.;
    - heti Pacsi-levél csütörtökönként 10:00-kor, okt. 15-től dec. 30-ig (12 szám);
    - háromrészes üdvözlő sorozat az új feliratkozóknak;
    - havi partnerlevél (okt. 13., nov. 10., dec. 8.).
  - **Egységes levélkeret** az app arculatával. Minden levélben más a fő téma. Visszatérő rovatok: a hét fajtája, Tudtad?, gazdi-tipp, „Tippelj!” fejtörő (a válasz a fajta kártyáján), közösségi ajánló, ajánld tovább.
  - Sötét mód, mobilnézet, sima szöveges változat. Minden levél 40 kB alatt marad (a Gmail 102 kB fölött vágja le a levelet).
  - **Képek:** mind legfeljebb 1200×1200 px (Mailchimp-korlát). A 8 új szezonális illusztrációt gpt-image-2 készítette, a portrékkal azonos stílusban: őszi túra, Halloween, esti séta, örökbefogadás, Mikulás, ajándék, szilveszter, ünnepi falka. A többi fejléckép a meglévő építőkockákból készül.
  - **Követhető linkek:** minden link a levél azonosítójával kerül a statisztikába (`utm_source=pacsi-level`, `utm_campaign=<levél>`). A fajtás linkek egyből a fajta kártyáját nyitják meg.
- **Mailchimp-eszköz** (`tools/mailchimp.py`), csak szabványos Pythonnal:
  - `ping`, `setup` (közönség, mezők, érdeklődési csoportok, „partner” címke);
  - képfeltöltés (`images`);
  - **piszkozat** létrehozása (`push`), sablonok az üdvözlő sorozathoz (`templates`);
  - ütemezés (`schedule`), automatikus kiküldés időzítővel (`send-due`);
  - statisztika (`sync`), partnerfelvétel (`import`), áttekintés (`status`).
  - Próbaüzem (`--dry-run`): kulcs nélkül is kipróbálható, és ilyenkor semmit nem ír az állapotba.
- **Kapcsolati adatbázis:** 887 kutyás szervezet és vállalkozás, 961 egyedi e-mail-cím, mind nyilvános forrásoldallal (`tools/contacts.py`).
  - Kategóriák: fajtaklubok, tenyésztők, menhelyek, kutyaiskolák, állatorvosok, szolgáltatások, média, cégek, közösségek.
  - Minden címnél ellenőrzött domain (MX), és jelölés, ha magánszemélynek tűnik.
  - Az adatok nem kerülnek verziókezelésbe.
- **CMS:**
  - **E-mail fül:** kampányterv, levélelőnézet (asztali, mobil, sötét mód, sima szöveg), tárgysorváltozatok, jóváhagyás, megjegyzés, ellenőrzés és Mailchimp-állapot.
  - **Kapcsolatok fül:** szűrés, keresés, állapotkövetés, jegyzet, CSV-export. Minden kapcsolathoz személyre szabott megkereső levél, emlékeztető és saját követhető link tartozik.
  - A **naptárban** a levelek is látszanak (✉), a jeles napokkal együtt (Halloween, Márton-nap, Mikulás, szilveszter…).
- **Adatkezelési tájékoztató – tervezet** (`email/adatkezelesi_tajekoztato.md`): jogi átnézés után tehető ki.

## 1.1.0 – 2026-09-25
- **Új domain: pacsit.hu.** Minden anyag az új címet használja.
  - A posztszövegek linkjei **posztonként követhetők**: pl. `https://pacsit.hu/f/v1` (Facebook, v1). A pacsit.hu szervere UTM-paraméterekre irányít, így a stat.pacsit.hu-n látszik, melyik platform és melyik poszt hozta a látogatót.
  - Bio-linkek platformonként: `pacsit.hu/i` (Instagram), `/t` (TikTok), `/f` (Facebook), `/l` (LinkedIn).
  - A hirdetések cél-URL-je a pacsit.hu, változatlan UTM-mel.
  - A story link-matricája platformonként külön linket kap.
- **Videók:** a négy videó zárókártyáján „Link a bióban · pacsit.hu” áll – újrarenderelve.
- **Linkelőnézeti kép (p_og):** rákerült a pacsit.hu; ez a kép él a pacsit.hu og:image címkéjében is.
- **Útmutató:** új „Statisztika: melyik poszt hozott látogatót?” rész; a bio-link és a hirdetésmérés szövege frissült.
- **Partneri prezentáció:** lásd `pitch/CHANGELOG.md` (1.1.3).

## 1.0.0 – 2026-09-24
- **Videók (TikTok / Reels, 1080×1920, 30 fps):** mind a négyben az igazi app fut, szimulált ujjal.
  - „Melyik kutya illik hozzád?”
  - „Milyen gazdi vagy?” (Párkereső kvíz)
  - „A 9 magyar kutyafajta”
  - „Zsebrakéta vagy kanapé-óriás?” (Térkép nézet)
- **Képek (29 anyag):**
  - bemutatkozó és funkcióposztok;
  - 7 diás karusszel, PDF-változattal LinkedInre;
  - „Tudtad?” és „A hét fajtája” sorozat;
  - storyk;
  - Meta-hirdetések (4 változat, UTM-es linkkel);
  - LinkedIn-posztok;
  - profilkép, Facebook- és LinkedIn-borító, linkelőnézeti kép.
- **Posztszövegek:** platformonként (TikTok, Instagram, Facebook, LinkedIn), hashtagekkel, első kommenttel és alternatív szöveggel.
- **Tartalomnaptár:** 2026. szeptember 26. – október 24. Kétnaponta videó, a hiányzó videókhoz 10 ötlet (brief).
- **CMS:**
  - naptár, tartalomtár, letöltés, szerkeszthető szövegek;
  - „kint van” jelölés;
  - Claude-dal írt szövegváltozatok;
  - ötletek megjelölése;
  - útmutató;
  - CSV-export.
- **Új kulcsvizuálok (gpt-image-2):** pacsit adó kabala, integető kabala, 13 kutyás felsorakozás.
- **Eszközök:**
  - virtuális idejű videórenderelő (headless Edge + ffmpeg);
  - képernyőkép-készítő;
  - build.
