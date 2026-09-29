# Facebook-oldal automatikus posztolása (Meta Graph API)

A `marketing/tools/facebook.py` a CMS naptárának Facebook-idősávjait a **Facebook saját ütemezőjébe** teszi: a posztok a megadott időpontban akkor is kimennek, ha a laptop ki van kapcsolva. Ugyanez az eszköz azonnal is posztol, visszavon, és lekéri a statisztikát.

| Tartalom | Facebookon | Ütemezhető? |
|---|---|---|
| Videó (9:16) | Reels, a borítóképpel | igen, legfeljebb 29 nappal előre |
| Kép | fotóposzt | igen, legfeljebb 30 nappal előre |
| Karusszel | több képes poszt | igen |
| Story | oldalstory | **nem** – a Meta nem enged storyt ütemezni, csak azonnal kitenni |
| Hirdetés | kimarad (Hirdetéskezelő); az „organikus” idősáv fotóposzt: az elsődleges szöveg és a rövid link, címkék és fizetett UTM nélkül | igen |
| Profil | kimarad (oldalbeállítás) | – |

Az eszköz legalább 15 perccel későbbre és legfeljebb 28 nappal előre ütemez (a Meta határa 10 perc, illetve 29–30 nap).

## Egyszeri beállítás (kb. 20 perc)

**Előfeltétel:** a saját Facebook-fiókod teljes jogú kezelője a Pacsi Facebook-oldalnak.

1. **Fejlesztői fiók.** Nyisd meg a <https://developers.facebook.com> oldalt, és lépj be a saját Facebook-fiókoddal. Ha még nem vagy fejlesztő: **Get Started**, majd telefonszám vagy e-mail megerősítése.
2. **App létrehozása.** **My Apps → Create App**.
   - **App name:** `Pacsi posztoló`, **App contact email:** a te címed.
   - **Use cases:** válaszd ezt: **Manage everything on your Page** (a Content management szűrő alatt is megtalálod).
   - **Business:** kapcsold a céghez (ARworks), vagy válaszd: *I don't want to connect a business portfolio yet*. Mindkettő jó.
   - **Create app**, és add meg a jelszavad.
3. **Jogosultságok.** Bal oldalt **Use cases** → *Manage everything on your Page* → **Customize**. A **Permissions** listában add hozzá (Add):
   - `pages_manage_posts` (posztolás, ütemezés)
   - `pages_read_engagement` (a posztok olvasása)
   - `pages_show_list` (az oldal kiválasztása; gyakran már benne van)
   - `read_insights` (a statisztikához: elérés, kattintás)
4. **App settings → Basic.** Töltsd ki, majd **Save changes**:
   - **Privacy Policy URL:** `https://darwinai.hu/adatvedelem`
   - **User data deletion** (Data deletion instructions URL): `https://darwinai.hu/adatvedelem`
   - **Category:** *Business and pages*
   - **App icon** (1024×1024): `marketing/out/kepek/p_avatar_1024.png`
   - Innen kell majd az **App ID** és az **App Secret** (Show gomb, jelszót kér). A titkos kulcsot ne küldd el senkinek, chatben se.
5. **Élő (Live) mód.** Ez az **app** üzemmódja, nem a Facebook élő videós közvetítése (Live Producer). A „You can't go live yet” üzenet (60 napos fiók, 100 követő) a videós közvetítésre vonatkozik, itt nem számít.
   - A developers.facebook.com oldalon nyisd meg: **My Apps → Pacsi posztoló**.
   - Kapcsold át az appot **Development**-ről **Live**-ra. A kapcsolót a felső sávban találod (**App Mode**), vagy a bal oldali **Publish** menüpontban.
   - Ha a kapcsoló szürke, a Meta egy hiányzó beállításra figyelmeztet (általában a 4. lépésből).
   - Enélkül a képes és videós posztokat csak te látod, a követők nem.
6. **Token kérése.** Nyisd meg a **Graph API Explorert**: <https://developers.facebook.com/tools/explorer>.
   - Jobb oldalt **Meta App:** *Pacsi posztoló*, **User or Page:** *User Token*.
   - A **Permissions** mezőbe add hozzá a 3. lépés négy jogosultságát.
   - **Generate Access Token** → a felugró ablakban válaszd ki a **Pacsi oldalt**, és engedélyezd.
   - A tokent a másolás ikonnal másold ki. Ez rövid életű (1–2 óra), a következő lépés cseréli tartósra.
7. **A beállító futtatása a saját terminálodban** (a Claude app Terminál paneljén vagy PowerShellben):
   ```
   cd "C:\Users\szbud\claude laptop\Dogs"
   python marketing/tools/facebook.py setup
   ```
   Beírod az App ID-t, az App Secretet és a tokent. Az utóbbi kettő nem látszik gépelés közben. A szkript:
   - tartós, **nem lejáró oldaltokenre** cseréli a tokent;
   - kiírja az oldal nevét és a jogosultságokat;
   - a repó gyökerébe menti: `Facebook_API.json` (gitignore-olt, az App Secret nem kerül bele).
8. **Szólj Claude-nak, hogy kész.** Ő lefuttatja:
   - `facebook.py check`: token, jogosultságok, oldal;
   - `facebook.py test --yes`: egy 20 nap múlvára ütemezett próbaposztot létrehoz, visszaolvas és töröl. Nyilvánosan semmi nem jelenik meg.

## Használat

```bash
python marketing/tools/facebook.py plan                 # a Facebook-idősávok állapota (esedékes, ütemezve, kint van, lekésett)
python marketing/tools/facebook.py schedule             # próbafutás: mi ütemeződne
python marketing/tools/facebook.py schedule --yes       # a következő 28 nap minden esedékes posztja a Facebook ütemezőjébe
python marketing/tools/facebook.py post k_quiz --now --yes          # egy poszt azonnal
python marketing/tools/facebook.py post v2 --at "2026-10-02 19:30" --yes
python marketing/tools/facebook.py scheduled            # mi van ütemezve a Facebookon
python marketing/tools/facebook.py cancel v2 --yes      # ütemezett poszt visszavonása
python marketing/tools/facebook.py posts                # az oldal legutóbbi posztjai (a kézzel kitettek is)
python marketing/tools/facebook.py insights --json marketing/tmp/fb_insights.json   # statisztika
```

- **A `--yes` nélkül semmi nem megy ki**, csak kiírja, mit tenne.
- **A szöveg** a CMS-ben szerkesztett Facebook-szöveg és hashtagek, a követhető rövid linkkel (`pacsit.hu/f/<id>`).
  - A CMS-ben átírt szövegeket Claude menti le a közös tárolóból (`marketing/tmp/cms_db/edits`) ütemezés előtt.
- **Kimarad** minden idősáv, amely a CMS-ben már ki van pipálva, a naplóban szerepel, vagy olyan tartalomhoz tartozik, ami máshol már „Kiposztolva” állapotú. Ez utóbbiakat csak külön kérésre (`--only v4`) ütemezi.
- **Napló:** `marketing/social/state/facebook_log.json` (poszt- és videóazonosítók). Megszakadás esetén sem duplikál.
- **Statisztika:** az `insights` kimenetének `metrics` része a CMS Eredmények fülének formájában van. Claude onnan tölti fel a közös tárolóba.

## Biztonság

- **Hol van az oldaltoken?** A `Facebook_API.json` fájlban. Olyan titok, mint a többi kulcsfájl a repó gyökerében: nincs verziókezelve, és az eszköz soha nem írja ki.
- **Visszavonás:**
  - a Facebookon: Beállítások → Üzleti integrációk → *Pacsi posztoló* → Eltávolítás;
  - vagy az app törlése a developers.facebook.com-on.
- **Új token:** futtasd újra a `setup` parancsot.
- **Mit tehet az app?** Csak az általad kijelölt oldalra posztol. Személyes profilra nem tud posztolni.

## Később

- **Instagram:** ugyanazzal az appal bekötható, ha az Instagram-fiók szakmai fiók és össze van kötve a Facebook-oldallal (`instagram_content_publish` jogosultság).
  - Az Instagram API nem ütemez, ezért ott időzítő kellene.
  - A médiát nyilvános URL-ről kéri.
- **Csak saját oldalra, App Review nélkül:** az app normál (Standard) hozzáféréssel működik, mert csak a saját oldaladra posztol. App Review akkor kellene, ha más emberek oldalait is kezelné.
