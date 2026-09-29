"""Pacsi – közösségi profilok indítása (a CMS „Indítás” füle).

Platformonként lépések: mit csinálj, mit másolj be (szöveg), mit tölts fel (kép a CMS tartalmai közül), melyik linket add meg.
Lépéselem: {"do": "…", "copy": "szöveg" | None, "file": ("tartalom-id", fájlindex) | None, "link": "url" | None, "limit": n}
A szövegek hosszát a build ellenőrzi (limit). A kipipálás a CMS közös tárolójába kerül (setup/<platform>).
"""

MAIL = "hello@pacsit.hu"
HANDLE = "pacsit.hu"

BIO_IG = "🐾 Találd meg a hozzád illő kutyát!\n124 fajta · kvíz · összehasonlítás\nIngyenes, regisztráció nélkül 👇"
BIO_TT = "Találd meg a hozzád illő kutyát 🐾 124 fajta, 1 perces kvíz 👇"
FB_INTRO = "Találd meg a hozzád illő kutyát! 124 fajta, szűrők, 1 perces kvíz – ingyen, regisztráció nélkül."
FB_ABOUT = ("A Pacsi vizuális kutyafajta-választó: 124 népszerű fajta egy élő felhőben, szűrőkkel (lakás, gyerek, mozgás, ugatás, "
            "szőrhullás), Párkereső kvízzel és összehasonlítással. Ingyenes, regisztráció nélkül, telefonon appként is telepíthető.\n\n"
            "Célunk a felelős kutyaválasztás: hogy mindenki olyan kutyát válasszon, amelyik tényleg illik az életéhez.\n\n"
            "Heti kutyás levél: https://pacsit.hu/hirlevel/\nFejlesztette: DarwinAI")
YT_DESC = ("A Pacsi vizuális kutyafajta-választó: 124 népszerű kutyafajta egy élő, interaktív felhőben. Szűrj a saját életedre "
           "(lakás, gyerek, mozgás, ugatás), töltsd ki az 1 perces Párkereső kvízt, és hasonlítsd össze a kedvenceidet. "
           "Ingyenes, regisztráció nélkül.\n\n"
           "Itt rövid videók jönnek fajtákról, gazdi-tippekről és arról, hogyan válassz felelősen kutyát.\n\n"
           "👉 Próbáld ki: https://pacsit.hu/y\n✉️ Heti kutyás levél: https://pacsit.hu/hirlevel/\n\nA Pacsit a DarwinAI fejlesztette.")
LI_TAGLINE = "Vizuális kutyafajta-választó: 124 fajta, szűrők és kvíz – hogy mindenki a hozzá illő kutyát válassza."
LI_ABOUT = ("A Pacsi egy ingyenes, magyar kutyafajta-választó web-app és telepíthető alkalmazás. 124 népszerű fajta lebeg egy élő "
            "felhőben, és minden szűrőre reagál: a nem illő fajták kirepülnek, a legjobb találatok előrejönnek. A Párkereső kvíz "
            "10 kérdésből megmutatja a gazditípust és a hozzá illő fajtákat, a fajtakártyák pedig őszintén beszélnek a "
            "mozgásigényről, a költségekről és az egészségügyi kockázatokról.\n\n"
            "Célunk a felelős kutyaválasztás: kevesebb elhamarkodott döntés, kevesebb gazdátlan kutya. Együttműködünk "
            "fajtaklubokkal, menhelyekkel, kutyaiskolákkal és állatorvosokkal.\n\n"
            "A Pacsit a DarwinAI tervezte és fejlesztette. Partneri együttműködés: hello@pacsit.hu")

AVATAR = ("p_avatar", 0)

SETUP = [
    {"id": "elo", "name": "Előkészítés", "icon": "🧰", "day": "1. nap", "time": "15 perc", "steps": [
        {"do": "Minden fiókhoz ugyanazt a címet használd: **hello@pacsit.hu**. Az ellenőrző levelek a Forward Email appba érkeznek. Így bárki átveheti később a fiókokat, nincsenek a személyes címedhez kötve.", "copy": MAIL},
        {"do": "Jelszókezelőbe mentsd a jelszavakat, és mindenhol kapcsold be a kétlépcsős azonosítást (2FA). Ha egy közösségi fiókot ellopnak, azt a legnehezebb visszaszerezni."},
        {"do": "Felhasználónév: próbáld mindenhol ugyanazt, ebben a sorrendben: **pacsit.hu** → **pacsi.app** → **pacsikutya**. Instagrammal kezdd, ott a legszigorúbb. Ami ott szabad, azt vidd végig a többin.", "copy": HANDLE},
        {"do": "Töltsd le a profilképet. Ez megy minden platformra (FB, IG, TikTok, YouTube, LinkedIn).", "file": AVATAR},
    ]},
    {"id": "facebook", "name": "Facebook-oldal", "icon": "📘", "day": "1. nap", "time": "20 perc", "steps": [
        {"do": "Lépj be a saját Facebook-fiókoddal, és nyisd meg: **Oldal létrehozása**. (A Facebook-oldalt mindig egy személyes fiók kezeli, ez így rendben van.)", "link": "https://www.facebook.com/pages/create"},
        {"do": "Oldal neve:", "copy": "Pacsi – kutyafajta-választó"},
        {"do": "Kategória: kezdd el beírni, és válaszd ezt: **Alkalmazásoldal** (App page). Másodiknak választhatod az **Oktatási weboldal** kategóriát."},
        {"do": "Bemutatkozás (Bio, max. 101 karakter):", "copy": FB_INTRO, "limit": 101},
        {"do": "Profilkép:", "file": AVATAR},
        {"do": "Borítókép (1640×624; mobilon a két szélét levágja, a lényeg középen van):", "file": ("p_fb_cover", 0)},
        {"do": "Részletek → **Webhely**. Ez a követhető Facebook-link:", "copy": "https://pacsit.hu/f"},
        {"do": "Részletek → **E-mail**:", "copy": MAIL},
        {"do": "Részletek → **Leírás** (Névjegy):", "copy": FB_ABOUT},
        {"do": "Oldal felhasználóneve (Beállítások → Oldal adatai): **pacsit.hu**, vagy ami az Előkészítésnél szabad volt. Az oldal címe így facebook.com/pacsit.hu lesz."},
        {"do": "Művelet gomb: **+ Gomb hozzáadása** → „További információ” / „Weboldal megtekintése” → link:", "copy": "https://pacsit.hu/f"},
        {"do": "Hétfő után (szept. 28.) az első posztot (Adj egy pacsit!) **rögzítsd az oldal tetejére**: ⋯ → Rögzítés."},
    ]},
    {"id": "instagram", "name": "Instagram", "icon": "📸", "day": "1. nap", "time": "15 perc", "steps": [
        {"do": "Telefonon az Instagram appban: profil → ≡ → **Fiók hozzáadása** → **Új fiók létrehozása**, e-mailként:", "copy": MAIL},
        {"do": "Felhasználónév (ha szabad):", "copy": HANDLE},
        {"do": "Profil szerkesztése → **Név** (ebben is keresnek, max. 30 karakter):", "copy": "Pacsi | kutyafajta-választó", "limit": 30},
        {"do": "**Bemutatkozás** (max. 150 karakter):", "copy": BIO_IG, "limit": 150},
        {"do": "**Linkek** → Külső link hozzáadása. Ez a követhető Instagram-link:", "copy": "https://pacsit.hu/i"},
        {"do": "Profilkép:", "file": AVATAR},
        {"do": "Beállítások → **Fióktípus és eszközök** → **Váltás professzionális fiókra** → **Vállalkozás** → kategória: **Alkalmazásoldal**. Kapcsolattartó e-mail: hello@pacsit.hu. Így látod a statisztikát, és ütemezhetsz is."},
        {"do": "**Összekötés a Facebook-oldallal**: Beállítások → Fiókközpont → Fiókok hozzáadása → a Pacsi FB-oldal. Utána a Reels egy kapcsolóval a Facebookra is kimehet, és a Meta Business Suite-ban mindkettőt egy helyen ütemezheted.", "link": "https://business.facebook.com"},
    ]},
    {"id": "tiktok", "name": "TikTok", "icon": "🎵", "day": "1. nap", "time": "15 perc", "steps": [
        {"do": "TikTok app → Regisztráció → **E-mail cím** (nem telefonszám), a születési dátum a sajátod (felnőtt):", "copy": MAIL},
        {"do": "Felhasználónév:", "copy": HANDLE},
        {"do": "Profil szerkesztése → **Név**:", "copy": "Pacsi 🐾"},
        {"do": "**Bemutatkozás** (max. 80 karakter):", "copy": BIO_TT, "limit": 80},
        {"do": "Profilkép:", "file": AVATAR},
        {"do": "≡ → Beállítások és adatvédelem → Fiók → **Váltás üzleti fiókra**. Kategóriának válaszd a legközelebbit (pl. Oktatás vagy Alkalmazások). Az üzleti fióknál van statisztika és ütemezés."},
        {"do": "**Webhely** a profilban (üzleti fióknál a Profil szerkesztése alatt). Ha még nem engedi, mert új fióknál gyakran követőszámhoz kötött, a bió végére írd be: pacsit.hu", "copy": "https://pacsit.hu/t"},
        {"do": "Gépről kényelmesebb feltölteni és ütemezni: **TikTok Studio**. Zenét viszont csak a telefonos appban tudsz tenni a videó alá.", "link": "https://www.tiktok.com/tiktokstudio"},
    ]},
    {"id": "youtube", "name": "YouTube (Shorts)", "icon": "▶️", "day": "2. nap", "time": "25 perc", "steps": [
        {"do": "Hozz létre egy Google-fiókot a hello@pacsit.hu címmel: **Fiók létrehozása** → „Magamnak” → **„Inkább a meglévő e-mail-címemet használom”**. A csatorna így nem a személyes Gmailedhez tartozik.", "link": "https://accounts.google.com/signup", "copy": MAIL},
        {"do": "Ezzel a fiókkal: YouTube → profilkép → **Csatorna létrehozása**. Név:", "copy": "Pacsi – kutyafajta-választó", "link": "https://www.youtube.com"},
        {"do": "Handle (a csatorna @-címe):", "copy": "@" + HANDLE},
        {"do": "YouTube Studio → **Testreszabás** → **Arculat** → Profilkép:", "file": AVATAR, "link": "https://studio.youtube.com"},
        {"do": "Arculat → **Szalagcím kép** (2560×1440; telefonon csak a középső sáv látszik, ott van a lényeg):", "file": ("p_yt_banner", 0)},
        {"do": "Testreszabás → **Alapinformációk** → **Leírás**:", "copy": YT_DESC, "limit": 1000},
        {"do": "Alapinformációk → **Linkek** → Link hozzáadása. Cím: „Próbáld ki ingyen”, URL:", "copy": "https://pacsit.hu/y"},
        {"do": "Alapinformációk → **Kapcsolatfelvételi adatok** → e-mail:", "copy": MAIL},
        {"do": "**Shorts feltöltése:** függőleges MP4, max. 3 perc; ezt a YouTube magától Shortnak veszi. A CMS-ben a videónál van YouTube-szöveg: az első sor a cím, a többi a leírás. Feltöltésnél **Ütemezés** → a naptár szerinti időpont."},
    ]},
    {"id": "linkedin", "name": "LinkedIn-oldal", "icon": "💼", "day": "2. nap", "time": "20 perc", "steps": [
        {"do": "Ha a **DarwinAI-nak van LinkedIn-oldala**, és te vagy az adminja: az oldalon Adminisztrátori eszközök → **Bemutatóoldal létrehozása**. Ez a Pacsinak a legjobb, mert a DarwinAI alá tartozik. Ha nincs, hozz létre **Céges oldalt**:", "link": "https://www.linkedin.com/company/setup/new/"},
        {"do": "Név:", "copy": "Pacsi – kutyafajta-választó"},
        {"do": "LinkedIn-cím (linkedin.com/company/…):", "copy": "pacsi-hu"},
        {"do": "Webhely. Ez a követhető LinkedIn-link:", "copy": "https://pacsit.hu/l"},
        {"do": "Iparág: **Szoftverfejlesztés** (Software Development) · Méret: **2–10 fő** · Típus: **Magánkézben lévő** (csak céges oldalnál)."},
        {"do": "Logó (400×400-nál nagyobb is jó):", "file": AVATAR},
        {"do": "Szlogen (max. 120 karakter):", "copy": LI_TAGLINE, "limit": 120},
        {"do": "Oldal szerkesztése → **Áttekintés** (Névjegy, max. 2000 karakter):", "copy": LI_ABOUT, "limit": 2000},
        {"do": "Borítókép (céges oldal, 1128×191):", "file": ("p_li_cover", 0)},
        {"do": "Egyéni gomb: **Webhely felkeresése** →", "copy": "https://pacsit.hu/l"},
    ]},
    {"id": "vege", "name": "Befejezés", "icon": "✅", "day": "2. nap", "time": "15 perc", "steps": [
        {"do": "Ellenőrizd a követhető linkeket (mind a pacsit.hu-ra kell vigyen): pacsit.hu/f · /i · /t · /y · /l", "link": "https://pacsit.hu/i"},
        {"do": "Küldd el Claude-nak az 5 profil címét (FB, IG, TikTok, YouTube, LinkedIn). Bekerülnek a hírlevelek láblécébe és a „Kövess minket” sorba, a CMS-be és a partneri anyagokba."},
        {"do": "A Pacsi-levélben (pacsit.hu/hirlevel) iratkozz fel a hello@pacsit.hu címmel is, így látod, mit kapnak az olvasók. A saját címed már fent van."},
        {"do": "Ütemezd az első hetet a **Naptár** fül szerint (szept. 28., hétfő: indulás). Facebook + Instagram: Meta Business Suite; TikTok: TikTok Studio; YouTube: Studio → Ütemezés.", "link": "https://business.facebook.com/latest/content_calendar"},
        {"do": "Hétfő este nézz rá a statisztikára: stat.pacsit.hu → UTM-források (facebook, instagram, tiktok, youtube, linkedin, pacsi-level, partner).", "link": "https://stat.pacsit.hu"},
    ]},
]
