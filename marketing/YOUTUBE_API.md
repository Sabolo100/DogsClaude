# YouTube Shorts automatikus feltöltése (YouTube Data API v3)

A `marketing/tools/youtube.py` a CMS naptárának YouTube-idősávjait a **YouTube saját ütemezőjébe** teszi: a videó privátként töltődik fel, és a naptár szerinti időpontban a YouTube maga teszi nyilvánossá, akkor is, ha a laptop ki van kapcsolva. Ugyanez az eszköz azonnal is közzétesz, módosít, töröl, és lekéri a statisztikát.

| Tartalom | YouTube-on | Ütemezhető? |
|---|---|---|
| Videó (9:16, legfeljebb 3 perc) | Short, borítóképpel | igen |
| Kép, karusszel, story, hirdetés | kimarad (a YouTube-ra csak videó megy) | – |
| Profil (szalagcím) | kimarad (a csatorna beállítása) | – |

A csatorna: **Pacsi – kutyafajta választó** (`UCO8Hj95k0ouOE-wQmhk6TpA`). Az eszköz csak ehhez fogadja el a belépést.

## Fontos: a Google korlátja (privátra zárolás)

**Az új API-projektből feltöltött videó privátra zárolódik, és a Studióban sem lehet nyilvánossá tenni.** Ez a Google hivatalos szabálya, nem az eszköz hibája:

- A YouTube Data API dokumentációja (`videos.insert`): a **2020. július 28. után létrehozott, nem auditált API-projektből** feltöltött videók *„private viewing mode”*-ra korlátozottak, amíg a projekt át nem esik a YouTube **API-auditon**.
- A YouTube Súgó („Videos locked as private”): az ilyen videóknál **nincs fellebbezés**. A tulajdonosnak újra kell töltenie a videót a Studióban (vagy auditált API-val).

Vagyis egy frissen létrehozott projekttel **nincs jóváhagyható „draft”**: csak zárolt, privát videó jön létre. Ezért az eszköz:

- előbb egy **ellenőrző próbát** kér (`test --yes`): 3 mp-es, nem listázott próbavideót tölt fel, megnézi, hogy a Google privátra zárolta-e, és azonnal törli;
- **éles videót addig nem tölt fel**, amíg a próba sikeres nem volt.

**Három kiút, ha a próba zárolást mutat:**

1. **2020. július 28. előtt létrehozott Google Cloud projekt.** Ha a cégednek vagy neked van ilyen, használd: a szabály csak az utána létrehozottakra vonatkozik. Így ellenőrizheted egy projekt létrehozási dátumát: `gcloud projects list --format="table(projectId,name,createTime)"`. A beállítás ugyanaz, csak nem új projektet hozol létre, hanem a régit használod.
2. **API-audit** (a projekt hitelesítése). Lásd lent. Ingyenes, de a Google nem ad határidőt (napok–hetek), és nincs garancia a jóváhagyásra.
3. **Addig kézi feltöltés a Studióban.** `python marketing/tools/youtube.py copy v2` kiírja a címet, a leírást, a fájlok útját és az időpontot; a Studióban a *Láthatóság → Ütemezés* pontnál kell megadni. Ezt a `plan` is jelzi.

## Egyszeri beállítás (kb. 15 perc)

**Előfeltétel:** a saját Google-fiókod kezelője a Pacsi-csatornának. Ha a csatorna márkafiók, a belépésnél a csatornát is ki kell választani.

1. **Projekt.** <https://console.cloud.google.com> → felül a projektválasztó → **New project**. Név: `Pacsi Content Scheduler`. (Vagy egy 2020 előtti régi projekt kiválasztása, lásd fent.)
2. **API bekapcsolása.** **APIs & Services → Library** → keresd: **YouTube Data API v3** → **Enable**.
3. **Google Auth Platform** (a menüpontok neve kissé eltérhet): **Get started**.
   - **App information:** App name: `Pacsi Content Scheduler`, User support email és Developer contact: a te címed.
   - **Audience:** ha a projekt a céges (ARworks) Google Workspace szervezetben van, válaszd az **Internal**-t: nincs figyelmeztetés, és a token nem jár le. Egyébként **External**. Ilyenkor a létrehozás után az **Audience** oldalon nyomd meg a **Publish app** gombot (állapot: *In production*). Enélkül a token **7 nap után lejár**.
   - **Data Access → Add or remove scopes:** keresd a *YouTube Data API v3* jogait, és jelöld ezt: `…/auth/youtube` → **Update** → **Save**.
4. **Kliens.** **Clients → Create client** → Application type: **Desktop app** → Name: `Pacsi feltöltő` → **Create** → **Download JSON**.
   - **A titkos kulcs csak most tölthető le**, utána a Console csak az utolsó 4 karakterét mutatja.
   - A fájl neve `client_secret_….json`. Mentsd a repó gyökerébe (gitignore-olt), vagy jegyezd meg az útját.
5. **A beállító futtatása a saját terminálodban** (a Claude app Terminál paneljén vagy PowerShellben):
   ```
   cd "C:\Users\szbud\claude laptop\Dogs"
   python marketing/tools/youtube.py setup --client-json "C:\…\client_secret_….json"
   ```
   - Megnyílik a böngésző. Jelentkezz be a csatornát kezelő fiókkal, és a **Pacsi – kutyafajta választó** csatornát válaszd.
   - „A Google nem ellenőrizte ezt az alkalmazást” (*Google hasn't verified this app*): **Advanced → Go to Pacsi Content Scheduler (unsafe)**. Ez normális: az app csak a tiéd. **Internal** módban nem jelenik meg.
   - Engedélyezd a YouTube-fiók kezelését (**Continue**).
   - A szkript kiírja a csatorna nevét, és elmenti a repó gyökerébe: `YouTube_API.json` (gitignore-olt). A kulcsokat és a tokent sosem írja ki.
   - Ha rossz csatornát választasz, nem ment semmit; futtasd újra.
   - Végül töröld a letöltött `client_secret_….json` fájlt: a titok már a `YouTube_API.json`-ban van.
6. **Szólj Claude-nak, hogy kész.** Ő lefuttatja:
   - `youtube.py check`: token, csatorna, jogosultság;
   - `youtube.py test --yes`: 3 mp-es, nem listázott próbavideó feltöltése, a zárolás vizsgálata, törlés. Nyilvánosan semmi nem jelenik meg.

## Használat

```bash
python marketing/tools/youtube.py plan                  # a YouTube-idősávok állapota (a csatornát is átnézi)
python marketing/tools/youtube.py copy v2               # cím, leírás, fájl, időpont – kézi (Studio) feltöltéshez
python marketing/tools/youtube.py schedule              # próbafutás: mi töltődne fel
python marketing/tools/youtube.py schedule --yes        # a következő 28 nap esedékes videói a YouTube ütemezőjébe
python marketing/tools/youtube.py schedule --draft --yes   # privát piszkozatként, ütemezés nélkül (a Studióban te teszed közzé)
python marketing/tools/youtube.py post v2 --at "2026-10-02 18:45" --yes
python marketing/tools/youtube.py post v3 --now --yes   # azonnal nyilvános
python marketing/tools/youtube.py scheduled             # az ütemezett videók élő állapota a YouTube-on
python marketing/tools/youtube.py update v2 --yes       # a CMS-ben átírt cím/leírás/időpont ráírása a feltöltött videóra
python marketing/tools/youtube.py cancel v2 --yes       # feltöltött videó törlése
python marketing/tools/youtube.py videos                # a csatorna videói (a kézzel feltöltöttek is)
python marketing/tools/youtube.py adopt --yes           # a kézzel feltöltött naptári videók felvétele a naplóba
python marketing/tools/youtube.py insights --json marketing/tmp/yt_insights.json   # statisztika
```

- **A `--yes` nélkül semmi nem töltődik fel**, csak kiírja, mit tenne.
- **Cím és leírás** a CMS-ben szerkesztett YouTube-szövegből: az **első sor a cím** (a végi hashtagek nélkül, legfeljebb 100 karakter), a **többi a leírás**, alatta a hashtagek. A hashtagekből lesznek a videó kulcsszavai is.
- **Beállítások** (a `youtube.py` elején, a `DEFAULTS`-ban): kategória *Kisállatok és állatok*, nyelv magyar, *nem gyerekeknek készült*, *nem valósághű mesterséges tartalom* (festett illusztrációk és képernyőfelvétel).
- **Shorts:** a 9:16-os, legfeljebb 3 perces videót a YouTube magától Shortnak veszi. A `plan` figyelmeztet, ha egy fájl nem felel meg.
- **Kimarad** minden idősáv, amely a CMS-ben már ki van pipálva, a naplóban szerepel, vagy a csatornán már fent van. Ez utóbbit a leírásban lévő követhető link (`pacsit.hu/y/<id>`) vagy a cím alapján ismeri fel, így a kézzel feltöltött videókat sem duplikálja.
  - Ha a tartalom a CMS-ben már „Kiposztolva”, a jövőbeli idősávja „ellenőrizd” jelzést kap, és csak külön kérésre (`--only v2`) töltődik fel.
- **Napló:** `marketing/social/state/youtube_log.json` (videóazonosítók, minden feltöltés után mentve). Megszakadás esetén sem duplikál.
- **Megszakadt feltöltés:** a videót 8 MB-os szeletekben tölti, hálózati hibánál onnan folytatja, ahol megszakadt.
- **Borítókép:** a CMS borítója; ha a csatorna nincs telefonnal ellenőrizve, a YouTube nem engedi, ilyenkor a YouTube választ egyet.
- **Statisztika:** az `insights` kimenetének `metrics` része a CMS Eredmények fülének formájában van (a megtekintés az „elérés” mezőbe kerül). Claude onnan tölti fel a közös tárolóba.
- **Kvóta:** a `videos.insert` külön napi 100 feltöltést enged, a többi hívás napi 10 000 egységet. Ez bőven elég.

## API-audit kérése (ha a próba zárolást mutat)

Űrlap: <https://support.google.com/youtube/contact/yt_api_form> (*YouTube Data API Services – Audit and Quota Extension Form*). Ingyenes. A Google nem ad határidőt, és egyetlen csatornát kiszolgáló saját eszköznél nincs garancia a jóváhagyásra. Az űrlap a 2026. szeptemberi állapot szerint ezt kéri:

| Rész | Mit adj meg |
|---|---|
| Kérés típusa | *Complete a compliance audit to request for additional quota* |
| Ki kéri | szervezetként (ARworks Kft.), vagy magánszemélyként; név, weboldal, cím, méret (*Startup* / *Independent Developer*) |
| Üzleti modell | a YouTube-hoz kapcsolódó munka: a saját termékünk (Pacsi) YouTube-csatornájának tartalomütemezése; célközönség: *Internal Users*; bevétel: *Free service*; Google-kapcsolattartó: nincs |
| API-kliens | neve: `Pacsi Content Scheduler` (a „YouTube” szó nem szerepelhet benne); elérési cím: `https://pacsit.hu/`; adatvédelmi URL (kötelező); nyilvánosan elérhető: nem (belső parancssori eszköz) |
| Használati eset | *Video Uploading & Account Management* és *Internal Company Tool*; Google-bejelentkezés (OAuth): igen, csak a csatorna kezelője |
| Projekt | a Google Cloud **projektszám** (a Console kezdőlapján) |
| Végpontok | `videos.insert`, `videos.list`, `videos.update`, `videos.delete`, `thumbnails.set`, `channels.list`, `playlistItems.list`; várható használat: legfeljebb ~10 feltöltés hetente |

**Kötelező bizonyíték:**
- az **adatvédelmi tájékoztató képernyőképei**, a YouTube-os részekkel: a YouTube API Services használata, link a YouTube felhasználási feltételeire (<https://www.youtube.com/t/terms>) és a Google adatvédelmi irányelveire (<http://www.google.com/policies/privacy>), a hozzáférés visszavonásának módja (<https://security.google.com/settings/security/permissions>), adattörlés;
- a **kezdőlap képernyőképe**, ahol az adatvédelmi link látszik;
- a **felhasználási feltételek** dokumentuma.

**Feltételes bizonyíték:**
- az **OAuth-engedélykérő képernyők** (jogosultságok, visszavonás): a `setup` közben készíts róluk képernyőképet;
- a **feltöltő felület**: a terminál `plan` és `schedule` kimenete;
- az **Internal Company Tool** felülete: a CMS Naptár és Eredmények füle.

Javasolt adatvédelmi kiegészítés (angolul; jogász nézze át):

> **YouTube API Services.** Our internal content-scheduling tool uses YouTube API Services to upload and schedule videos on our own YouTube channel and to read basic statistics of those videos. By using it you agree to be bound by the YouTube Terms of Service (https://www.youtube.com/t/terms). Data handled through YouTube is also subject to the Google Privacy Policy (http://www.google.com/policies/privacy). The tool stores only an OAuth refresh token of the channel owner, on the owner's computer; it does not collect, store or share data about viewers or other users. Access can be revoked at any time at https://security.google.com/settings/security/permissions, and the stored token is deleted by deleting the credentials file.

Ha kéred, Claude előkészíti az audit-csomagot: az adatvédelmi és felhasználási feltételek szövegét, a képernyőképeket és a kitöltendő válaszokat.

## Biztonság

- **Hol van a token?** A `YouTube_API.json` fájlban (OAuth kliens + frissítő token). Olyan titok, mint a többi kulcsfájl a repó gyökerében: nincs verziókezelve, és az eszköz soha nem írja ki. Chatben se küldd el.
- **Visszavonás:** <https://myaccount.google.com/permissions> → *Pacsi Content Scheduler* → **Hozzáférés eltávolítása**. Új token: futtasd újra a `setup` parancsot.
- **Mit tehet a token?** A YouTube-fiók kezelését engedi (feltöltés, módosítás, törlés, olvasás) a kiválasztott csatornán. Más csatornához nem fér hozzá.

## Hibaelhárítás

| Üzenet | Teendő |
|---|---|
| `invalid_grant` | a token lejárt vagy visszavonták (*Testing* módú projektnél 7 nap után lejár): futtasd újra a `setup` parancsot, és állítsd a projektet *In production*-ra vagy *Internal*-ra |
| „NEM a Pacsi-csatorna” | a belépésnél a *Pacsi – kutyafajta választó* csatornát (márkafiókot) kell választani |
| `SERVICE_DISABLED` / `accessNotConfigured` | a YouTube Data API v3 nincs bekapcsolva a projektben (*APIs & Services → Library*) |
| `quotaExceeded` | a napi API-keret elfogyott; a Google időzónája szerinti éjfélkor (Budapesten kilenckor) újraindul |
| `uploadLimitExceeded` | a csatorna napi feltöltési korlátja; várj 24 órát |
| a videó az időpont után is privát | a videó zárolt lehet (nem auditált projekt): a `scheduled` jelzi; lásd az API-audit részt |
| `forbidden` a borítónál | a csatorna nincs telefonnal ellenőrizve (<https://www.youtube.com/verify>); a videó így is felkerül |

## Később

- **YouTube Analytics API:** benyomások, átkattintási arány, megtekintési idő (külön API és `yt-analytics.readonly` jogosultság kell hozzá).
- **Kommentek:** a `commentThreads` végpontokkal lehetne a válaszokat összegyűjteni és válaszjavaslatot készíteni.
