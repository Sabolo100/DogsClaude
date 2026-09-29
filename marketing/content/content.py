"""Pacsi Marketing – a tartalomnaptár és a posztszövegek forrása.

Ebből készül a content.json (python marketing/tools/build.py), a CMS ezt olvassa.
A CMS-ben szerkesztett szövegek a CMS saját tárolójába kerülnek (felülírásként), ezt a fájlt nem módosítják.
Hangnem (spec 20. fejezet): tegező, meleg, humoros, de nem infantilis; rövid mondatok;
a komoly témákban (egészség, felelősség) egyenes és kedves. „Illik hozzád”, nem „ez a te kutyád”.
"""

import re

SITE = "https://pacsit.hu/"
SITE_LABEL = "pacsit.hu"

# Rövid, követhető linkek (a pacsit.hu szervere UTM-paraméterekre irányít, a statisztika így látja a platformot
# és a posztot): https://pacsit.hu/f/v1 → /?utm_source=facebook&utm_medium=social&utm_campaign=pacsi&utm_content=v1.
# Poszt nélkül bio-link: https://pacsit.hu/i → utm_content=bio. A hirdetések teljes UTM-es cél-URL-t kapnak.
SHORT = {"facebook": "f", "instagram": "i", "tiktok": "t", "linkedin": "l", "youtube": "y"}


def link(platform, post=None):
    return SITE + SHORT[platform] + (f"/{post}" if post else "")

# Alap hashtag-készletek
H_CORE = "#pacsi #kutya #kutyafajta #kutyafajták #kutyásélet #kutyagazdi #kutyaimádó"
H_TT = "#kutya #kutyafajták #kutyásélet #kutyatiktok #pacsi"

PLATFORMS = {
    "tiktok": {"name": "TikTok", "limit": 4000, "color": "#111111",
               "tip": "A linket nem lehet kattinthatóvá tenni a leírásban: „Link a bióban”. 3–5 hashtag elég."},
    "instagram": {"name": "Instagram", "limit": 2200, "color": "#D6336C", "maxTags": 30,
                  "tip": "Reels + feed. A link a bióba kerül (vagy storyban link-matrica). Legfeljebb 30 hashtag; 8–15 a jó."},
    "facebook": {"name": "Facebook", "limit": 63206, "color": "#1877F2",
                 "tip": "Ide jöhet a kattintható link. Hashtag alig kell (0–3)."},
    "linkedin": {"name": "LinkedIn", "limit": 3000, "color": "#0A66C2",
                 "tip": "A külső link csökkentheti az elérést: tedd az első kommentbe. Szakmai hangnem, 3–5 hashtag."},
    "youtube": {"name": "YouTube", "limit": 5000, "color": "#FF0000",
                "tip": "Shorts: függőleges videó (max. 3 perc) – magától Short lesz. Az első sor a cím (max. 100 karakter), a többi a leírás. A link a leírásban kattintható."},
}

KINDS = {
    "video": "Videó", "kep": "Kép", "karusszel": "Karusszel", "story": "Story",
    "hirdetes": "Hirdetés", "profil": "Profil", "otlet": "Ötlet",
}

STATUSES = {"otlet": "Ötlet", "tervezett": "Tervezett", "kesz": "Kész", "kiposztolva": "Kiposztolva"}


def slot(platform, date, time, note=""):
    return {"platform": platform, "date": date, "time": time, "note": note}


ITEMS = [
    # ------------------------------------------------------------------ VIDEÓK
    {
        "id": "v1", "kind": "video", "status": "kesz",
        "title": "Melyik kutya illik hozzád?",
        "sub": "Szűrés élőben: Lakás → Gyerek → Csendes – 124 fajtából 10 marad, és az agár meglepetés.",
        "format": "9:16 · 17 mp · 1080×1920",
        "files": [
            {"label": "Videó (MP4, 9:16)", "src": "out/videok/v1_melyik_kutya_illik_hozzad.mp4", "role": "main"},
            {"label": "Borítókép", "src": "out/videok/v1_melyik_kutya_illik_hozzad_borito.jpg", "role": "cover"},
        ],
        "copy": {
            "youtube": {"text": "Melyik kutya illik hozzád? 124 fajtából 3 koppintás 🐾 #shorts\n\nLakás, kisgyerek, vékony falak – 3 szűrő, és 124 kutyafajtából 10 marad. A meglepetés: az agár!\n\nPróbáld ki ingyen, regisztráció nélkül: https://pacsit.hu/", "tags": "#pacsi #kutya #kutyafajták #shorts"},
            "tiktok": {"text": "124 kutyafajta, 3 koppintás: lakás, kisgyerek, vékony falak. Ennyi maradt – és az agár nagyon meglepett! 😮🐾 Te mit kapcsolnál be? Link a bióban.",
                       "tags": H_TT + " #lakásbavalókutya"},
            "instagram": {"text": "Melyik kutya illik hozzád? 🐾\n\n124 fajtából indultunk. Lakás, kisgyerek, vékony falak: három koppintás, és csak 10 fajta maradt a felhőben. A meglepetés? Az agár! Otthon csendes, nyugodt kanapészobor. 🛋️\n\n👉 Próbáld ki ingyen, regisztráció nélkül – link a bióban.",
                          "tags": H_CORE + " #lakásbavalókutya #gyerekbarátkutya #agár"},
            "facebook": {"text": "Melyik kutya illik hozzád? 🐾\n\n124 fajtából indultunk: lakás, kisgyerek, vékony falak – három koppintás után 10 fajta maradt. A legnagyobb meglepetés? Az agár! Otthon csendes, nyugodt lakótárs.\n\nPróbáld ki te is, ingyen és regisztráció nélkül: " + SITE,
                         "tags": ""},
            "linkedin": {"text": "Így néz ki, amikor a szűrés nem táblázat, hanem élmény. 🐾\n\nA Pacsiban 124 kutyafajta lebeg egy élő felhőben. Minden szűrőre fizikailag reagálnak: a nem illő fajták kirepülnek, a legjobb találatok előrejönnek. Három koppintás (lakás, kisgyerek, csend), és 124-ből 10 marad.\n\nA link az első kommentben. Kíváncsi vagyok, nálatok melyik fajta maradna a végén!",
                         "tags": "#UX #termékfejlesztés #döntéstámogatás #DarwinAI"},
        },
        "firstComment": "Nálad melyik szűrő lenne az első? 🏢 Lakás, 👶 Gyerek vagy 🤫 Csendes?",
        "alt": "Animáció: kutyaportrék felhője, majd a Pacsi app telefonon. A Lakás, Gyerek és Csendes szűrő után 10 fajta marad, végül megnyílik az angol agár fajtakártyája.",
        "notes": ["Zene: az appban válassz vidám, felkapott hangot (TikTok: Hangok → Népszerű; Reels: Zene). A videó hang nélkül készült.",
                  "Borítókép: a mellékelt borítókép, vagy a 0:01-es kocka.",
                  "LinkedIn: natív videóként töltsd fel, a linket az első kommentbe tedd."],
        "slots": [slot("youtube", "2026-09-28", "19:15", "Shorts"), slot("tiktok", "2026-09-28", "19:00"), slot("instagram", "2026-09-28", "19:30", "Reels"),
                  slot("facebook", "2026-09-28", "20:00", "Reels / videó"), slot("linkedin", "2026-10-01", "08:30", "natív videó")],
    },
    {
        "id": "v2", "kind": "video", "status": "kesz",
        "title": "Milyen gazdi vagy? – Párkereső kvíz",
        "sub": "10 gyors kérdés az appban, a végén gazditípus és top 5 fajta. Kommentcsali: „Te mi lettél?”",
        "format": "9:16 · 20 mp · 1080×1920",
        "files": [
            {"label": "Videó (MP4, 9:16)", "src": "out/videok/v2_milyen_gazdi_vagy.mp4", "role": "main"},
            {"label": "Borítókép", "src": "out/videok/v2_milyen_gazdi_vagy_borito.jpg", "role": "cover"},
        ],
        "copy": {
            "youtube": {"text": "Milyen gazdi vagy? 10 kérdés, 1 perc 🤔 #shorts\n\nKanapé-kapitány, Aktív kalandor vagy Városi flâneur? A Pacsi Párkereső kvíze megmutatja a gazditípusodat és a hozzád illő top 5 fajtát. Te mi lettél? Írd meg kommentben!\n\nKvíz: https://pacsit.hu/", "tags": "#pacsi #kutya #kutyafajták #shorts"},
            "tiktok": {"text": "10 kérdés, 1 perc, és kiderül, milyen gazdi vagy. Én Városi flâneur lettem 🏙️ Te? Írd meg kommentben! 👇",
                       "tags": H_TT + " #kvíz"},
            "instagram": {"text": "Milyen gazdi vagy? 🤔🐾\n\nKanapé-kapitány, Aktív kalandor, Családi karmester, Városi flâneur, Tanyasi őrangyal vagy Kutyasuttogó?\n\n10 gyors kérdés a Pacsi Párkereső kvízében, a végén megkapod a gazditípusodat és a hozzád illő top 5 fajtát.\n\nÍrd meg kommentben, mi lettél! 👇 Link a bióban.",
                          "tags": H_CORE + " #kvíz #melyikkutyaillikhozzám"},
            "facebook": {"text": "Milyen gazdi vagy? 🐾 10 kérdés, 1 perc – és a Pacsi megmondja a gazditípusodat, meg a hozzád illő top 5 fajtát. Én Városi flâneur lettem 🏙️ Te mi lettél? Írd meg kommentben!\n\n👉 " + SITE,
                         "tags": ""},
        },
        "firstComment": "Kanapé-kapitányok, jelentkezzetek! 🛋️😄",
        "alt": "Animáció: hat gazditípus ikonja pörög, majd a Pacsi app telefonon: az ujj végigkattintja a 10 kvízkérdést, az eredmény Városi flâneur, alatta a top 5 fajta.",
        "notes": ["Zene: pörgős, játékos hang illik hozzá – a „Tekerjünk előre!” résznél gyorsul a tempó.",
                  "Kommentekre válaszolj a gazditípus emojijával (pl. 🛋️, 🏃) – ez növeli az elérést."],
        "slots": [slot("youtube", "2026-10-02", "18:45", "Shorts"), slot("tiktok", "2026-10-02", "18:30"), slot("instagram", "2026-10-02", "19:00", "Reels"), slot("facebook", "2026-10-02", "19:30")],
    },
    {
        "id": "v3", "kind": "video", "status": "kesz",
        "title": "A 9 magyar kutyafajta",
        "sub": "Fajtaparádé portrékkal és jellemzéssel, majd egy koppintás a Magyar szűrőre: 124-ből 9 marad. Állatok világnapjára.",
        "format": "9:16 · 23 mp · 1080×1920",
        "files": [
            {"label": "Videó (MP4, 9:16)", "src": "out/videok/v3_9_magyar_kutyafajta.mp4", "role": "main"},
            {"label": "Borítókép", "src": "out/videok/v3_9_magyar_kutyafajta_borito.jpg", "role": "cover"},
        ],
        "copy": {
            "youtube": {"text": "A 9 magyar kutyafajta – ismered mindet? 🇭🇺 #shorts\n\nPuli, pumi, mudi, komondor, kuvasz, erdélyi kopó, két vizsla és a magyar agár. Melyik a kedvenced?\n\nMind a 9 a Pacsiban: https://pacsit.hu/", "tags": "#pacsi #kutya #kutyafajták #shorts"},
            "tiktok": {"text": "Ismered mind a 9 magyar kutyafajtát? 🇭🇺 Puli, pumi, mudi, komondor, kuvasz, erdélyi kopó, két vizsla és a magyar agár. Melyik a kedvenced? 👇",
                       "tags": "#magyarkutyafajták #puli #vizsla #mudi #kutya #pacsi"},
            "instagram": {"text": "9 magyar kutyafajta – ismered mindet? 🇭🇺🐾\n\nPuli, pumi, mudi, komondor, kuvasz, erdélyi kopó, rövidszőrű és drótszőrű magyar vizsla, magyar agár.\n\nA Pacsiban egy koppintás a Magyar szűrő, és a 124 fajtából csak ők maradnak a felhőben. Melyik a kedvenced? Írd meg kommentben! 👇\n\nLink a bióban.",
                          "tags": "#pacsi #magyarkutyafajták #magyarkutya #puli #pumi #mudi #komondor #kuvasz #magyarvizsla #erdélyikopó #magyaragár #kutya #kutyásélet"},
            "facebook": {"text": "Boldog Állatok világnapját! 🐾🇭🇺\n\nMa a 9 magyar kutyafajtát ünnepeljük: puli, pumi, mudi, komondor, kuvasz, erdélyi kopó, a rövidszőrű és a drótszőrű magyar vizsla, valamint a magyar agár. Melyik a kedvenced?\n\nNézd meg mindet a Pacsiban: " + SITE,
                         "tags": ""},
        },
        "firstComment": "Tipp: a pumit 2016-ban az Amerikai Kennel Klub is elismerte, azóta a tengerentúlon is egyre népszerűbb. 🐾",
        "alt": "Animáció: a 9 magyar kutyafajta portréja egymás után, névvel és egymondatos jellemzéssel, majd a Pacsi appban a Magyar szűrő után csak ők maradnak.",
        "notes": ["Október 4. – Állatok világnapja: ezen a napon érdemes posztolni.",
                  "Zene: népzenei ihletésű vagy vidám, büszke hangulatú hang illik hozzá."],
        "slots": [slot("youtube", "2026-10-04", "11:15", "Shorts"), slot("tiktok", "2026-10-04", "11:00"), slot("instagram", "2026-10-04", "11:30", "Reels"), slot("facebook", "2026-10-04", "12:00")],
    },
    {
        "id": "v4", "kind": "video", "status": "kesz",
        "title": "Zsebrakéta vagy kanapé-óriás?",
        "sub": "Térkép nézet az appban, majd animált 4 kutyatípus (méret × energia). Kommentcsali: 1, 2, 3 vagy 4?",
        "format": "9:16 · 18 mp · 1080×1920",
        "files": [
            {"label": "Videó (MP4, 9:16)", "src": "out/videok/v4_zsebraketa_vagy_kanape_orias.mp4", "role": "main"},
            {"label": "Borítókép", "src": "out/videok/v4_zsebraketa_vagy_kanape_orias_borito.jpg", "role": "cover"},
        ],
        "copy": {
            "youtube": {"text": "Zsebrakéta vagy kanapé-óriás? 🐕 #shorts\n\nKicsi vagy nagy, pörgős vagy nyugis? A Pacsi Térkép nézetében egy pillantással látod, melyik fajta hova tartozik.\n\nNézd meg: https://pacsit.hu/", "tags": "#pacsi #kutya #kutyafajták #shorts"},
            "tiktok": {"text": "Zsebrakéta 🚀 vagy kanapé-óriás 🛋️? A Pacsi térképén minden kutya a helyére kerül: méret × energia. Te melyiket választanád: 1, 2, 3 vagy 4? 👇",
                       "tags": H_TT},
            "instagram": {"text": "Zsebrakéta vagy kanapé-óriás? 🐾\n\n1️⃣ Zsebrakéták – kicsi, de pörgős\n2️⃣ Sportgépek – nagy és fáradhatatlan\n3️⃣ Nyugis törpék – kicsi és kényelmes\n4️⃣ Kanapé-óriások – nagy, de nyugodt\n\nA Pacsi Térkép nézetében mind a 124 fajta a helyére kerül. Te melyiket választanád? Írd meg egy számmal! 👇\n\nLink a bióban.",
                          "tags": H_CORE + " #jackrussell #bernáthegyi #vizsla"},
            "facebook": {"text": "Zsebrakéta vagy kanapé-óriás? 🐾\n1️⃣ Zsebrakéták · 2️⃣ Sportgépek · 3️⃣ Nyugis törpék · 4️⃣ Kanapé-óriások\n\nTe melyiket választanád? Írd meg egy számmal! A Pacsi Térkép nézetében mind a 124 fajtát megnézheted: " + SITE,
                         "tags": ""},
        },
        "firstComment": "Én a 4-es vagyok: nagy kutya, de kanapén. 🛋️😄",
        "alt": "Animáció: egy pörgő Jack Russell és egy álmos bernáthegyi, majd a Pacsi app Térkép nézete, végül négy csoport: Zsebrakéták, Sportgépek, Nyugis törpék, Kanapé-óriások.",
        "notes": ["Zene: kontrasztos, vicces hang (pörgős → lassú) működik jól a nyitó két kutyához."],
        "slots": [slot("youtube", "2026-09-30", "19:15", "Shorts"), slot("tiktok", "2026-09-30", "19:00"), slot("instagram", "2026-09-30", "19:30", "Reels"), slot("facebook", "2026-09-30", "20:00")],
    },

    # ------------------------------------------------------------------ KÉPEK – bemutatkozás és funkciók
    {
        "id": "k_launch", "kind": "kep", "status": "kesz",
        "title": "Adj egy pacsit! – bemutatkozó poszt",
        "sub": "A kabala pacsit ad: az indító poszt Facebookra és Instagramra.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "launch", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Adj egy pacsit a hozzád illő kutyának! 🐾\n\nMegjött a Pacsi: 124 kutyafajta egy élő, lebegő felhőben. Kapcsold be, ami neked fontos (lakás, gyerek, csend, szőrhullás…), és figyeld, ki marad. Van Párkereső kvíz, összehasonlítás és gazdi-tudástár is.\n\nIngyenes, regisztráció nélkül, és telefonon appként is telepíthető.\n\n👉 Link a bióban.",
                          "tags": H_CORE + " #újkutya #kiskutya #kutyaválasztás"},
            "facebook": {"text": "Megjött a Pacsi! 🐾\n\n124 népszerű kutyafajta egy élő felhőben: szűrj arra, ami neked fontos, és figyeld, melyik fajta marad. Párkereső kvíz, összehasonlítás, felelős gazdi tippek – ingyenesen, regisztráció nélkül.\n\nPróbáld ki: " + SITE,
                         "tags": ""},
        },
        "firstComment": "Mi alapján választanál kutyát? Méret, szőr, vagy a természete? 🐾",
        "alt": "Illusztráció: egy kéz pacsit ad egy narancssárga kendős, bolyhos kiskutyának. Felirat: Adj egy pacsit a hozzád illő kutyának!",
        "slots": [slot("instagram", "2026-09-28", "12:00"), slot("facebook", "2026-09-28", "12:00")],
    },
    {
        "id": "k_before_after", "kind": "kep", "status": "kesz",
        "title": "124 kutyából 10 – előtte/utána",
        "sub": "Két telefon: a teljes felhő és a három szűrő utáni 10 fajta.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "before_after", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "124 kutyából 10, ami tényleg illik hozzád. 🐾\n\nElőtte: a teljes felhő. Utána: csak azok a fajták, amelyek lakásba valók, gyerekbarátok és csendesek. Minden koppintásra élőben reagál a felhő – a kiesők egyszerűen kirepülnek. 😄\n\nPróbáld ki – link a bióban.",
                          "tags": H_CORE + " #lakásbavalókutya #gyerekbarátkutya #csendeskutya"},
            "facebook": {"text": "124 kutyából 10, ami tényleg illik hozzád. 🐾 Lakásba való, gyerekbarát és csendes: három koppintás, és a felhőben csak ők maradnak. Próbáld ki a saját szempontjaiddal: " + SITE,
                         "tags": ""},
        },
        "alt": "Két telefon a Pacsi appal: bal oldalon 124 kutyaportré, jobb oldalon a Lakás, Gyerek és Csendes szűrő után maradt 10 fajta.",
        "slots": [slot("instagram", "2026-09-30", "12:00"), slot("facebook", "2026-09-30", "12:00")],
    },
    {
        "id": "k_quiz", "kind": "kep", "status": "kesz",
        "title": "Milyen gazdi vagy? – 6 gazditípus",
        "sub": "A kvíz hat gazditípusa kártyákon; kommentcsali.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "feat_quiz", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Milyen gazdi vagy? 🤔\n\n🛋️ Kanapé-kapitány · 🏃 Aktív kalandor · 👨‍👩‍👧 Családi karmester · 🏙️ Városi flâneur · 🛡️ Tanyasi őrangyal · 🎓 Kutyasuttogó\n\nA Pacsi Párkereső kvíze 10 kérdésből megmondja, és a hozzád illő top 5 fajtát is megmutatja. Írd meg kommentben, mi lettél! 👇\n\nLink a bióban.",
                          "tags": H_CORE + " #kvíz"},
            "facebook": {"text": "Milyen gazdi vagy? 🤔 Kanapé-kapitány, Aktív kalandor, Családi karmester, Városi flâneur, Tanyasi őrangyal vagy Kutyasuttogó? 10 kérdés, 1 perc – a végén a top 5 fajtád is kiderül. Írd meg, mi lettél! 👉 " + SITE,
                         "tags": ""},
        },
        "alt": "Hat kártya a Pacsi gazditípusaival: Kanapé-kapitány, Aktív kalandor, Családi karmester, Városi flâneur, Tanyasi őrangyal, Kutyasuttogó, mindegyiken két kutyaportré.",
        "slots": [slot("instagram", "2026-10-02", "12:00"), slot("facebook", "2026-10-02", "12:00")],
    },
    {
        "id": "k_compare", "kind": "kep", "status": "kesz",
        "title": "Vizsla, golden vagy border collie? – összehasonlítás",
        "sub": "Pókhálódiagram három népszerű fajtáról.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "feat_compare", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Vizsla, golden vagy border collie? 🐾\n\nMindhárom okos, tanulékony és szereti a gyerekeket, mégis nagyon mások. A vizsla keveset hullat, de napi 1,5–2 óra mozgás kell neki. A golden hármuk közül a legcsendesebb. A border collie pedig munka nélkül unatkozik – ha nem adsz neki feladatot, keres magának. 😄\n\nA Pacsiban bármelyik 3 fajtát egymás mellé teheted. Link a bióban.",
                          "tags": H_CORE + " #vizsla #goldenretriever #bordercollie"},
            "facebook": {"text": "Vizsla, golden vagy border collie? A Pacsi Összehasonlítás funkciójával bármelyik 3 fajtát egymás mellé teheted: energia, gyerekbarátság, tanulékonyság, csend, szőrhullás, ápolás. Próbáld ki: " + SITE,
                         "tags": ""},
        },
        "alt": "Pókhálódiagram: a rövidszőrű magyar vizsla, a golden retriever és a border collie hat jellemzője (energia, gyerekbarát, tanulékony, csendes, kevés hullás, kevés ápolás).",
        "slots": [slot("instagram", "2026-10-09", "12:00"), slot("facebook", "2026-10-09", "12:00")],
    },
    {
        "id": "k_card", "kind": "kep", "status": "kesz",
        "title": "Minden, ami számít – egy kártyán",
        "sub": "A fajtakártya magyarázó feliratokkal.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "feat_card", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Nem csak cuki – hozzád is illik? 🐾\n\nA Pacsi minden fajtáról megmutatja, ami számít: mennyire illik hozzád, méret, súly, élettartam, 9 jellemző 1-től 5-ig, egészségügyi tudnivalók, költségek, és hogy kinek ajánlott – és kinek nem.\n\nMind a 124 fajtáról. Link a bióban.",
                          "tags": H_CORE + " #felelősgazdi"},
            "facebook": {"text": "Nem csak cuki – hozzád is illik? A Pacsi fajtakártyáin minden benne van, ami a döntéshez kell: illeszkedés, jellemzők, egészség, költség, kinek ajánlott és kinek nem. 👉 " + SITE,
                         "tags": ""},
        },
        "alt": "Telefon a Pacsi fajtakártyájával (angol agár), számozott feliratokkal: jellemzés egy mondatban, illeszkedés, méret-súly-élettartam, 9 jellemző.",
        "slots": [slot("instagram", "2026-10-16", "12:00"), slot("facebook", "2026-10-16", "12:00")],
    },

    # ------------------------------------------------------------------ KÉPEK – tartalom-sorozatok
    {
        "id": "k_hu9", "kind": "kep", "status": "kesz",
        "title": "Ismered mind a 9 magyar kutyafajtát?",
        "sub": "A 9 magyar fajta portrérácsban.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "hu9", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Ismered mind a 9 magyar kutyafajtát? 🇭🇺🐾\n\nPuli, pumi, mudi, komondor, kuvasz, erdélyi kopó, rövidszőrű és drótszőrű magyar vizsla, magyar agár.\n\nHányat ismertél fel elsőre? Írd meg! 👇 A Pacsiban a Magyar szűrővel egy koppintással megtalálod őket – link a bióban.",
                          "tags": "#pacsi #magyarkutyafajták #puli #pumi #mudi #komondor #kuvasz #magyarvizsla #erdélyikopó #magyaragár #kutya"},
            "facebook": {"text": "Ismered mind a 9 magyar kutyafajtát? 🇭🇺 Hányat ismertél fel elsőre? Írd meg kommentben! A Pacsiban a Magyar szűrővel egy koppintással megtalálod őket: " + SITE,
                         "tags": ""},
        },
        "alt": "A 9 magyar kutyafajta portréja 3×3-as rácsban: puli, pumi, mudi, komondor, kuvasz, erdélyi kopó, rövidszőrű vizsla, drótszőrű vizsla, magyar agár.",
        "slots": [slot("facebook", "2026-10-04", "18:00"), slot("instagram", "2026-10-04", "18:00")],
    },
    {
        "id": "k_map4", "kind": "kep", "status": "kesz",
        "title": "Zsebrakéta vagy kanapé-óriás? – 4 kutyatípus",
        "sub": "Méret × energia négyes rács, kommentcsali számokkal.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "map4", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Zsebrakéta vagy kanapé-óriás? 🐾\n\n1️⃣ Zsebrakéták – kicsi, de pörgős\n2️⃣ Sportgépek – nagy és fáradhatatlan\n3️⃣ Nyugis törpék – kicsi és kényelmes\n4️⃣ Kanapé-óriások – nagy, de nyugodt\n\nTe melyiket választanád? Írd meg egy számmal! 👇 A Pacsi Térkép nézetében mind a 124 fajtát megtalálod – link a bióban.",
                          "tags": H_CORE},
            "facebook": {"text": "Zsebrakéta vagy kanapé-óriás? Te melyiket választanád: 1, 2, 3 vagy 4? 👇 A Pacsi Térkép nézetében mind a 124 fajta a helyére kerül: " + SITE,
                         "tags": ""},
        },
        "alt": "Négyes rács: Zsebrakéták (Jack Russell, pumi, papillon), Sportgépek (vizsla, dalmata, malinois), Nyugis törpék (shih tzu, mopsz, pekingi), Kanapé-óriások (bernáthegyi, új-fundlandi, komondor).",
        "slots": [slot("instagram", "2026-10-12", "12:00"), slot("facebook", "2026-10-12", "12:00")],
    },
    {
        "id": "c_lakas", "kind": "karusszel", "status": "kesz",
        "title": "5 kutya, amiért a szomszéd is hálás lesz",
        "sub": "7 diás karusszel: lakásba való és csendes fajták, őszinte „figyelj” megjegyzésekkel.",
        "format": "4:5 · 7 dia · 1080×1350",
        "design": {"d": "car_lakas", "w": 1080, "h": 1350, "pages": 7},
        "copy": {
            "instagram": {"text": "5 kutya, amiért a szomszéd is hálás lesz 🤫🐾\n\nKis lakás, vékony falak? Ezek a fajták lakásba valók, és ritkán ugatnak:\n1. Cavalier King Charles spániel\n2. Coton de Tuléar\n3. Whippet\n4. Basenji\n5. Angol agár – igen, az agár! 😄\n\nLapozz, és nézd meg, kinél mire kell figyelni. A teljes listát (16 fajta) a Pacsiban találod – link a bióban.",
                          "tags": H_CORE + " #lakásbavalókutya #csendeskutya #cavalier #whippet #basenji #agár #cotondetulear"},
            "facebook": {"text": "5 kutya, amiért a szomszéd is hálás lesz 🤫🐾 Lakásba valók és ritkán ugatnak – az utolsó meglep! A teljes listát (16 fajta) a Pacsiban találod, a Lakás + Csendes szűrővel: " + SITE,
                         "tags": ""},
            "linkedin": {"text": "Egy jó szűrő többet ér egy hosszú listánál. 🐾\n\nA Pacsiban a Lakás + Csendes szűrő 124 fajtából 16-ot hagy meg – köztük olyat is, amire kevesen gondolnának (az agár!). Minden fajtánál ott az őszinte „figyelj” megjegyzés is, mert a jó döntéshez a buktatók is kellenek.\n\nA link az első kommentben.",
                         "tags": "#UX #döntéstámogatás #DarwinAI"},
        },
        "alt": "Hét dia: borító, majd öt fajta (Cavalier King Charles spániel, Coton de Tuléar, whippet, basenji, angol agár) portréval, jellemzőkkel és megjegyzéssel, végül a Pacsi app a Lakás és Csendes szűrővel.",
        "notes": ["Instagramon és Facebookon is több képes (karusszel) posztként töltsd fel, sorrendben (1–7).",
                  "LinkedInen PDF-dokumentumként működik a legjobban: a 7 képet egy PDF-be fűzve töltsd fel."],
        "slots": [slot("instagram", "2026-10-05", "12:00"), slot("facebook", "2026-10-05", "12:00"), slot("linkedin", "2026-10-13", "08:30", "PDF-karusszel")],
    },
    {
        "id": "k_tudtad_basenji", "kind": "kep", "status": "kesz",
        "title": "Tudtad? – A basenji jódlizik",
        "sub": "„Tudtad?” sorozat #1.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "tudtad", "p": "basenji", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Tudtad? 🐾 A basenji nem ugat – jódlizik!\n\nAz „ugatás nélküli kutya” jellegzetes, jódlizó hangot ad, és úgy mosakszik, mint egy macska. Csendes lakótárs, de nem kezdőknek való: önfejű, és sok mozgás kell neki.\n\nMég 123 fajta meglepetés a Pacsiban – link a bióban.",
                          "tags": "#tudtad #érdekesség #basenji " + H_CORE},
            "facebook": {"text": "Tudtad? 🐾 A basenji nem ugat – jódlizik! Úgy mosakszik, mint egy macska, és ritkán hallod. Még 123 fajta érdekességei a Pacsiban: " + SITE,
                         "tags": ""},
        },
        "alt": "Basenji portré. Felirat: Tudtad? Ez a kutya nem ugat. Jódlizik.",
        "slots": [slot("instagram", "2026-10-07", "12:00"), slot("facebook", "2026-10-07", "12:00")],
    },
    {
        "id": "k_tudtad_agar", "kind": "kep", "status": "kesz",
        "title": "Tudtad? – 70 km/h, mégis kanapészobor",
        "sub": "„Tudtad?” sorozat #2.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "tudtad", "p": "agar", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Tudtad? 70 km/h sprintben – otthon mégis kanapészobor. 🛋️🐾\n\nAz angol agár a leggyorsabb kutyafajta, a lakásban mégis csendes, nyugodt társ. Sok mentett agár keres gazdit, ezért érdemes az örökbefogadáson is elgondolkodni.\n\nA Pacsiban mind a 124 fajta érdekességeit megtalálod – link a bióban.",
                          "tags": "#tudtad #agár #greyhound #örökbefogadás " + H_CORE},
            "facebook": {"text": "Tudtad? Az angol agár sprintben akár 70 km/h-ra is képes – otthon mégis csendes kanapészobor. 🛋️ Sok mentett agár keres gazdit, gondolj az örökbefogadásra is! 🐾 " + SITE,
                         "tags": ""},
        },
        "alt": "Angol agár portré. Felirat: Tudtad? 70 km/h sprintben. Otthon: kanapészobor.",
        "slots": [slot("instagram", "2026-10-14", "12:00"), slot("facebook", "2026-10-14", "12:00")],
    },
    {
        "id": "k_tudtad_border", "kind": "kep", "status": "kesz",
        "title": "Tudtad? – Chaser, a zseni border collie",
        "sub": "„Tudtad?” sorozat #3.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "tudtad", "p": "border", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "Tudtad? 🧠🐾 Chaser, egy amerikai border collie több mint 1000 játékát ismerte fel név szerint – a képességeit tudományos cikk is leírta.\n\nA border collie a kutyavilág zsenije, de munka és napi 2 óra mozgás nélkül unatkozik. Neked való? Nézd meg a Pacsiban – link a bióban.",
                          "tags": "#tudtad #bordercollie #érdekesség " + H_CORE},
            "facebook": {"text": "Tudtad? Chaser, egy amerikai border collie több mint 1000 játékát ismerte fel név szerint. 🧠🐾 Zseni – de munka nélkül unatkozik. Hozzád illik? " + SITE,
                         "tags": ""},
        },
        "alt": "Border collie portré. Felirat: Tudtad? Több mint 1000 játékát ismerte név szerint.",
        "slots": [slot("instagram", "2026-10-21", "12:00"), slot("facebook", "2026-10-21", "12:00")],
    },
    {
        "id": "k_het_vizsla", "kind": "kep", "status": "kesz",
        "title": "A hét fajtája – Rövidszőrű magyar vizsla",
        "sub": "Heti sorozat #1: portré, jellemzők, érdekesség, kinek ajánlott és kinek nem.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "het", "p": "magyar-vizsla", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "A hét fajtája: a rövidszőrű magyar vizsla 🇭🇺🐾\n\nAranybarna tépőzár-kutya: mindig a gazdája mellett. Energikus, tanulékony, imádja a gyerekeket – de napi 1,5–2 óra mozgás kell neki, és nem szeret sokáig egyedül maradni.\n\nTudtad? Többször a kihalás szélére került, legutóbb a II. világháború után.\n\nA teljes fajtakártya a Pacsiban – link a bióban.",
                          "tags": "#ahétfajtája #magyarvizsla #vizsla #magyarkutyafajták " + H_CORE},
            "facebook": {"text": "A hét fajtája: a rövidszőrű magyar vizsla 🇭🇺🐾 Aranybarna tépőzár-kutya, aki mindig a gazdája mellett van. Aktív családoknak ideális – mozgásszegény életmódhoz nem. A teljes fajtakártya: " + SITE,
                         "tags": ""},
        },
        "alt": "A hét fajtája: rövidszőrű magyar vizsla portré, méret, súly, élettartam, jellemzők, érdekesség, kinek ajánlott és kinek nem.",
        "slots": [slot("instagram", "2026-10-08", "12:00"), slot("facebook", "2026-10-08", "12:00")],
    },
    {
        "id": "k_het_mudi", "kind": "kep", "status": "kesz",
        "title": "A hét fajtája – Mudi",
        "sub": "Heti sorozat #2.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "het", "p": "mudi", "w": 1080, "h": 1350},
        "copy": {
            "instagram": {"text": "A hét fajtája: a mudi 🇭🇺🐾\n\nA magyar titkos fegyver: sokoldalú, tanulékony, igazi agility-bajnok. Önálló fajtaként csak 1936-ban írta le dr. Fényes Dezső.\n\nAktív, sportos családoknak ideális – mozgásszegény, otthonülő életmódhoz nem.\n\nA teljes fajtakártya a Pacsiban – link a bióban.",
                          "tags": "#ahétfajtája #mudi #magyarkutyafajták #agility " + H_CORE},
            "facebook": {"text": "A hét fajtája: a mudi 🇭🇺🐾 Sokoldalú, tanulékony, igazi agility-bajnok – aktív családoknak való. Ismerd meg a Pacsiban: " + SITE,
                         "tags": ""},
        },
        "alt": "A hét fajtája: mudi portré, méret, súly, élettartam, jellemzők, érdekesség, kinek ajánlott és kinek nem.",
        "slots": [slot("instagram", "2026-10-15", "12:00"), slot("facebook", "2026-10-15", "12:00")],
    },

    # ------------------------------------------------------------------ STORYK
    {
        "id": "s_hello", "kind": "story", "status": "kesz",
        "title": "Story: Szia, én vagyok a Pacsi!",
        "sub": "Bemutatkozó story az integető kabalával, hellyel a link-matricának.",
        "format": "9:16 · 1080×1920",
        "design": {"d": "story_hello", "w": 1080, "h": 1920},
        "copy": {
            "instagram": {"text": "(Storyban nem kell hosszú szöveg.) Link-matrica szövege: Próbáld ki!", "tags": ""},
            "facebook": {"text": "(Storyban nem kell hosszú szöveg.) Link-matrica szövege: Próbáld ki!", "tags": ""},
        },
        "alt": "Integető, narancssárga kendős kiskutya. Felirat: Szia! Én vagyok a Pacsi. Segítek megtalálni a hozzád illő kutyát – 124 fajta közül.",
        "notes": ["Tedd a link-matricát a „Koppints a linkre!” felirat alá, bal oldalra. Link: " + SITE,
                  "Mentsd el Kiemelt történetként („Pacsi”), így a profilodon is ott marad."],
        "slots": [slot("instagram", "2026-09-29", "20:00", "story"), slot("facebook", "2026-09-29", "20:00", "story")],
    },
    {
        "id": "s_quiz", "kind": "story", "status": "kesz",
        "title": "Story: Milyen gazdi vagy? (szavazás)",
        "sub": "Story a 6 gazditípussal – szavazás-matricával.",
        "format": "9:16 · 1080×1920",
        "design": {"d": "story_quiz", "w": 1080, "h": 1920},
        "copy": {
            "instagram": {"text": "Szavazás-matrica: „Melyik vagy?” – Kanapé-kapitány / Aktív kalandor (vagy kvíz-matrica 4 opcióval).", "tags": ""},
        },
        "alt": "Hat gazditípus ikonja körben a kabala körül. Felirat: Milyen gazdi vagy? Tippelj, aztán töltsd ki a kvízt!",
        "notes": ["Tegyél rá kvíz-matricát (4 opció): Kanapé-kapitány · Aktív kalandor · Családi karmester · Városi flâneur.",
                  "Másnap oszd meg az eredményt egy új storyban, link-matricával a Pacsira."],
        "slots": [slot("instagram", "2026-10-01", "20:00", "story")],
    },

    # ------------------------------------------------------------------ HIRDETÉSEK
    {
        "id": "h_sq", "kind": "hirdetes", "status": "kesz",
        "title": "Hirdetés A – Melyik kutya illik hozzád? (szűrők)",
        "sub": "Meta-hirdetés (Facebook + Instagram), 1:1 – szűrőchipek és telefon.",
        "format": "1:1 · 1080×1080",
        "design": {"d": "launch_sq", "w": 1080, "h": 1080},
        "copy": {
            "facebook": {"text": "Elsődleges szöveg: Lakás, gyerek, vékony falak? Kapcsold be, ami neked fontos, és a Pacsi 124 kutyafajtából megmutatja, melyik illik hozzád. Ingyenes, regisztráció nélkül.\n\nCímsor: Melyik kutya illik hozzád?\nLeírás: 124 fajta · kvíz · összehasonlítás\nCTA-gomb: További információ\nCél-URL: " + SITE + "?utm_source=meta&utm_medium=paid&utm_campaign=indulas&utm_content=hirdetes_a",
                         "tags": ""},
        },
        "alt": "Telefon a Pacsi appal, mellette Lakásba való, Gyerekbarát és Csendes szűrőchip; felirat: Melyik kutya illik hozzád? 124 → 10 fajta illik hozzád.",
        "notes": ["A/B teszt a B hirdetéssel: ugyanaz a célközönség, 3–4 nap után a jobb kattintási arányú marad.",
                  "Javasolt célközönség: Magyarország, 22–45 év, érdeklődés: kutyák, kiskutya, állattartás, örökbefogadás."],
        "slots": [slot("facebook", "2026-09-28", "09:00", "hirdetés indul (Meta)")],
    },
    {
        "id": "h_cloud", "kind": "hirdetes", "status": "kesz",
        "title": "Hirdetés B – Portréfelhő + kvíz",
        "sub": "Meta-hirdetés, 1:1 – sok cuki portré, középen a kvíz CTA.",
        "format": "1:1 · 1080×1080",
        "design": {"d": "ad_a", "w": 1080, "h": 1080},
        "copy": {
            "facebook": {"text": "Elsődleges szöveg: Nem tudod, melyik kutya illik hozzád? A Pacsi Párkereső kvíze 10 kérdésből megmondja – és a 124 fajtából a te top 5-ödet is megmutatja. Ingyenes.\n\nCímsor: Derítsd ki 1 perc alatt!\nLeírás: Párkereső kvíz · 124 fajta\nCTA-gomb: További információ\nCél-URL: " + SITE + "?utm_source=meta&utm_medium=paid&utm_campaign=indulas&utm_content=hirdetes_b",
                         "tags": ""},
        },
        "alt": "Sok kutyaportré egy felhőben, felül fehér kártya: Melyik kutya illik hozzád? Derítsd ki 1 perc alatt – Párkereső kvíz.",
        "slots": [slot("facebook", "2026-09-28", "09:00", "hirdetés indul (Meta)")],
    },
    {
        "id": "h_cuki", "kind": "hirdetes", "status": "kesz",
        "title": "Hirdetés C – Ne a legcukibbat válaszd",
        "sub": "Meta-hirdetés vagy organikus poszt, 1:1 – felelős gazdi üzenet illeszkedési %-okkal.",
        "format": "1:1 · 1080×1080",
        "design": {"d": "ad_b", "w": 1080, "h": 1080},
        "copy": {
            "facebook": {"text": "Elsődleges szöveg: A legcukibb nem mindig a legjobb pár. 🐾 Kisgyerek, lakás, vékony falak? A pompon-törpespicc hangos, és kisgyerek mellé sem ideális – a cavalier és a coton viszont 95%-ban illik hozzátok. A Pacsi minden fajtára kiszámolja, mennyire illik az életedhez.\n\nCímsor: Ne a legcukibbat válaszd. A hozzád illőt.\nLeírás: Ingyenes kutyafajta-választó\nCTA-gomb: További információ\nCél-URL: " + SITE + "?utm_source=meta&utm_medium=paid&utm_campaign=indulas&utm_content=hirdetes_c",
                         "tags": ""},
            "instagram": {"text": "Ne a legcukibbat válaszd. A hozzád illőt. 🐾\n\nKisgyerek, lakás, vékony falak? A pompon-törpespicc hangos, és kisgyerek mellé sem ideális – a cavalier és a coton viszont 95%-ban illik. A Pacsi minden fajtára kiszámolja, mennyire illik az életedhez.\n\nLink a bióban.",
                          "tags": H_CORE + " #felelősgazdi"},
        },
        "alt": "Három kutyaportré illeszkedési százalékkal: törpespicc 38%, cavalier 95%, Coton de Tuléar 95%. Felirat: Ne a legcukibbat válaszd. A hozzád illőt.",
        "notes": ["A százalékok a Pacsi saját pontozásából jönnek (Gyerek + Lakás + Csendes szűrő)."],
        "slots": [slot("instagram", "2026-10-19", "12:00", "organikus"), slot("facebook", "2026-10-19", "12:00", "organikus")],
    },
    {
        "id": "h_story", "kind": "hirdetes", "status": "kesz",
        "title": "Hirdetés D – Story/Reels: 124 fajta, 10 kérdés, 1 perc",
        "sub": "Meta story-/Reels-hirdetés 9:16, kvízeredménnyel.",
        "format": "9:16 · 1080×1920",
        "design": {"d": "ad_story", "w": 1080, "h": 1920},
        "copy": {
            "facebook": {"text": "Elsődleges szöveg: 124 fajta. 10 kérdés. 1 perc. Töltsd ki a Pacsi Párkereső kvízét, és nézd meg a hozzád illő top 5 kutyafajtát!\n\nCímsor: Milyen gazdi vagy?\nCTA-gomb: További információ\nCél-URL: " + SITE + "?utm_source=meta&utm_medium=paid&utm_campaign=indulas&utm_content=hirdetes_d",
                         "tags": ""},
        },
        "alt": "Telefon a Pacsi kvízeredményével (Városi flâneur, top 5 fajta). Felirat: 124 fajta. 10 kérdés. 1 perc.",
        "notes": ["Hagyj szabadon kb. 250 px-t felül és alul (a Meta ide teszi a saját feliratait) – a kép ehhez igazodik."],
        "slots": [slot("instagram", "2026-09-28", "09:00", "story-hirdetés indul")],
    },

    # ------------------------------------------------------------------ LINKEDIN
    {
        "id": "l_ux", "kind": "kep", "status": "kesz",
        "title": "LinkedIn – Amikor a döntéstámogatás élmény",
        "sub": "DarwinAI termékbemutató poszt: laptop + 4 kulcsszám.",
        "format": "4:5 · 1080×1350",
        "design": {"d": "li_ux", "w": 1080, "h": 1350},
        "copy": {
            "linkedin": {"text": "Hogyan lesz egy döntésből élmény? 🐾\n\nKutyát választani nagy döntés: 10–15 évre szól. Mégis sokan a külső vagy egy trend alapján döntenek. Ezért készítettük el a DarwinAI-nál a Pacsit, egy vizuális kutyafajta-választót. 124 fajta lebeg benne egy élő felhőben, és minden szűrőre fizikailag reagál: a nem illő fajták kirepülnek, a legjobb találatok előrejönnek.\n\nNéhány döntés, amire büszkék vagyunk:\n→ szűrés helyett élő vizualizáció (Felhő, Csoportok, Térkép nézet)\n→ 10 kérdéses Párkereső kvíz gazditípussal és top 5 fajtával\n→ felelős gazdi réteg: lapos orrú fajták egészségi jelölése, örökbefogadási tippek\n→ telepíthető PWA, offline is működik – nincs regisztráció, nincs süti\n\nPróbáld ki (link az első kommentben), és írd meg, mit gondolsz!",
                         "tags": "#UX #termékfejlesztés #PWA #döntéstámogatás #DarwinAI"},
        },
        "firstComment": "Itt kipróbálható: " + SITE,
        "alt": "Laptop a Pacsi asztali nézetével (szűrőpanel és kutyafelhő), alatta: 124 kutyafajta, 9 jellemző fajtánként, 10 kérdéses kvíz, 0 regisztráció.",
        "slots": [slot("linkedin", "2026-09-29", "08:30")],
    },
    {
        "id": "l_partner", "kind": "kep", "status": "kesz",
        "title": "LinkedIn – Alapító partnereket keresünk",
        "sub": "Partnerkereső poszt kutyás márkáknak (a pitch deck előszobája).",
        "format": "1,91:1 · 1200×627",
        "design": {"d": "li_partner", "w": 1200, "h": 627},
        "copy": {
            "linkedin": {"text": "Kutyás márkákat keresünk partnernek. 🐾\n\nA Pacsi ott segít, ahol a gazdi-lét elkezdődik: a fajtaválasztásnál. 124 fajta, Párkereső kvíz, felelős gazdi tartalmak – ingyenesen, regisztráció nélkül.\n\nAlapító partnereket keresünk, kategóriánként egy márkát (eledel, felszerelés, állatorvosi ellátás, biztosítás). A partner hiteles segítőként jelenhet meg a fajtakártyákon, a kvíz eredményében és a gazdi-tudástárban.\n\nHa érdekel, írj üzenetet, és elküldjük a partneri ajánlatot!",
                         "tags": "#partnerség #petcare #kutya #marketing #DarwinAI"},
        },
        "alt": "Tizenhárom különböző kutya egy sorban ül. Felirat: Kutyás márka vagy? Legyél a Pacsi alapító partnere.",
        "slots": [slot("linkedin", "2026-10-06", "08:30")],
    },

    # ------------------------------------------------------------------ PROFIL / ARCULAT
    {
        "id": "p_avatar", "kind": "profil", "status": "kesz",
        "title": "Profilkép (minden platform)",
        "sub": "A kabala korall alapon – körbevágva is jól mutat.",
        "format": "1:1 · 1080×1080",
        "design": {"d": "avatar", "w": 1080, "h": 1080},
        "copy": {
            "instagram": {"text": "🐾 Találd meg a hozzád illő kutyát!\n124 fajta · kvíz · összehasonlítás\nIngyenes, regisztráció nélkül 👇", "tags": ""},
            "tiktok": {"text": "Találd meg a hozzád illő kutyát 🐾 124 fajta, 1 perces kvíz 👇", "tags": ""},
            "facebook": {"text": "A Pacsi vizuális kutyafajta-választó: 124 népszerű fajta egy élő felhőben, szűrőkkel, Párkereső kvízzel és összehasonlítással. Ingyenes, regisztráció nélkül. Fejlesztette: DarwinAI.", "tags": ""},
            "linkedin": {"text": "Vizuális kutyafajta-választó – 124 fajta, kvíz, összehasonlítás. A DarwinAI terméke.", "tags": ""},
        },
        "alt": "Profilkép: integető, narancssárga kendős kiskutya fehér körben, korall háttéren.",
        "notes": ["A szövegek itt a profilok bemutatkozó szövegei (bio): Instagram max. 150, TikTok max. 80 karakter.",
                  "Felhasználónév-ötletek (a foglaltságot ellenőrizd): pacsi.app · pacsiapp · pacsi_kutyavalaszto.",
                  "Link a bióban: " + SITE],
        "slots": [slot("instagram", "2026-09-26", "10:00", "profil beállítása"), slot("tiktok", "2026-09-26", "10:00", "profil beállítása"),
                  slot("facebook", "2026-09-26", "10:00", "oldal beállítása"), slot("linkedin", "2026-09-26", "10:00", "oldal beállítása")],
    },
    {
        "id": "p_fb_cover", "kind": "profil", "status": "kesz",
        "title": "Facebook-borítókép",
        "sub": "13 kutya sorban, középen a kabala.",
        "format": "1640×624",
        "design": {"d": "fb_cover", "w": 1640, "h": 624},
        "copy": {},
        "alt": "Tizenhárom különböző kutya egy sorban, középen a narancssárga kendős kabala. Felirat: Pacsi – Találd meg a hozzád illő kutyát.",
        "notes": ["Mobilon a Facebook a két szélét levághatja – a lényeg középen van."],
        "slots": [slot("facebook", "2026-09-26", "10:00", "oldal beállítása")],
    },
    {
        "id": "p_li_banner", "kind": "profil", "status": "kesz",
        "title": "LinkedIn-borítókép (személyes profil)",
        "sub": "A saját LinkedIn-profilod fejléce, ha a Pacsit ott is mutatnád. A céges oldalhoz a „LinkedIn céges borító” kell.",
        "format": "1584×396",
        "design": {"d": "li_banner", "w": 1584, "h": 396},
        "copy": {},
        "alt": "Pacsi logó és felirat balra, jobbra tizenhárom kutya egy sorban.",
        "notes": ["A LinkedIn a bal alsó sarokra teszi a céglogót – ott nincs fontos tartalom."],
        "slots": [slot("linkedin", "2026-09-26", "10:00", "oldal beállítása")],
    },
    {
        "id": "p_li_cover", "kind": "profil", "status": "kesz",
        "title": "LinkedIn céges borító",
        "sub": "A Pacsi LinkedIn-oldalának (céges vagy bemutatóoldal) fejléce.",
        "format": "1128×191",
        "design": {"d": "li_cover", "w": 1128, "h": 191},
        "copy": {},
        "alt": "Felirat: Találd meg a hozzád illő kutyát, jobbra tizenhárom kutya egy sorban.",
        "notes": ["A LinkedIn a logót a bal alsó sarokra teszi – ott szándékosan nincs szöveg."],
        "slots": [slot("linkedin", "2026-09-27", "10:00", "céges oldal beállítása")],
    },
    {
        "id": "p_yt_banner", "kind": "profil", "status": "kesz",
        "title": "YouTube-szalagcím",
        "sub": "A YouTube-csatorna fejléce. Telefonon csak a középső sáv látszik, tévén a teljes kép.",
        "format": "2560×1440",
        "design": {"d": "yt_banner", "w": 2560, "h": 1440},
        "copy": {},
        "alt": "Pacsi logó, felirat és tizenhárom kutya egy sorban, körülötte fajtaportrék.",
        "notes": ["A logó, a felirat és a kutyasor a minden eszközön látszó 1546×423-as középső sávban van."],
        "slots": [slot("youtube", "2026-09-27", "11:00", "csatorna beállítása")],
    },
    {
        "id": "p_og", "kind": "profil", "status": "kesz",
        "title": "Linkelőnézeti kép (Open Graph)",
        "sub": "Ez jelenik meg, amikor a Pacsi linkjét megosztják (Facebook, Messenger, LinkedIn, Viber).",
        "format": "1,91:1 · 1200×630",
        "design": {"d": "og", "w": 1200, "h": 630},
        "copy": {},
        "alt": "Pacsi logó, felirat: Melyik kutya illik hozzád? Mellette kutyaportrék felhője.",
        "notes": ["Kész: a pacsit.hu már ezt a képet mutatja linkmegosztáskor (og:image → https://pacsit.hu/og.jpg).",
                  "Ellenőrzés: Facebook Sharing Debugger (developers.facebook.com/tools/debug) → pacsit.hu → Újrakaparás, ha régi előnézet ragadt be."],
        "slots": [],
    },
]

# Következő videók – ötletek (brief) a kétnaponta posztolt TikTok/Reels ritmushoz
IDEAS = [
    {"id": "o5", "date": "2026-10-06", "title": "Kavard meg a felhőt!", "hook": "Ez a legcukibb felhő, amit valaha megkavartál 🌀",
     "brief": "Ujjal kavarás a felhőn (hullámkörök), majd egy szűrő be-ki: a kutyák kirepülnek és visszahullanak. 8–10 mp, végtelenített (loop) videó, „satisfying” jelleg.",
     "app": "Felhő, ujjal kavarás, Csak találatok"},
    {"id": "o6", "date": "2026-10-08", "title": "Első kutyád lesz? Ez az 5 fajta neked való", "hook": "Első kutya? Ne kapkodj! 🌱",
     "brief": "Kezdő szűrő bekapcsolása, majd az 5 legjobb kezdő fajta kártyája gyors egymásutánban (labrador, golden, cavalier, havanese, uszkár).",
     "app": "Kezdő szűrő, fajtakártyák"},
    {"id": "o7", "date": "2026-10-10", "title": "Allergiás vagy? Ők alig hullatnak", "hook": "Szőr a kanapén? Nem nálad. 🤧",
     "brief": "Hullás szűrő + a „nincs 100%-ban allergiabarát kutya” felelős üzenet; uszkár, bichon, coton, lagotto, portugál vízikutya.",
     "app": "Hullás szűrő, felelős gazdi üzenet"},
    {"id": "o8", "date": "2026-10-12", "title": "Vizsla vs. golden vs. border collie", "hook": "3 okos kutya – melyik a tiéd?",
     "brief": "Összehasonlítás: a radar poligonjai egymás után „kinőnek”, majd a legjobb érték soronként kiemelve.",
     "app": "Összevet fül, radardiagram"},
    {"id": "o9", "date": "2026-10-14", "title": "A legkisebb és a legnagyobb", "hook": "1,5 kg vagy 90 kg? 😳",
     "brief": "Méret szűrő: Toy vs. Óriás váltogatva; a buborékok mérete és száma látványosan változik. Csihuahua vs. bernáthegyi.",
     "app": "Méret szűrő, Csoportok nézet (méret)"},
    {"id": "o10", "date": "2026-10-16", "title": "Gondolj az örökbefogadásra", "hook": "Sok fajtatiszta kutya is gazdit keres 🏠",
     "brief": "Tippek fül – örökbefogadás kártya, agár/galgó példák, felelős üzenet. Komolyabb, meleg hangvétel.",
     "app": "Tippek (gazdi-tudástár)"},
    {"id": "o11", "date": "2026-10-18", "title": "Lapos orrú fajták: mire figyelj?", "hook": "Cuki pofi – de tud rendesen lélegezni?",
     "brief": "Brachy jelölés a kártyán (francia bulldog, mopsz), Könnyű légzés szűrő, „csak egészségügyileg szűrt szülőktől” üzenet.",
     "app": "Fajtakártya figyelmeztetés, Légzés szűrő"},
    {"id": "o12", "date": "2026-10-20", "title": "3 meglepő kutyás tény", "hook": "A harmadikat biztos nem tudtad! 🤯",
     "brief": "Tudtad? sorozat videóban: Titanic-túlélő pomerániaiak, a shih tzu neve oroszlánt jelent, a labrador falánkságának génje.",
     "app": "Fajtakártyák – Érdekesség szakasz"},
    {"id": "o13", "date": "2026-10-22", "title": "Városi vs. tanyasi kutya", "hook": "Panel vagy tanya? A kutyád is számít! 🏢🌾",
     "brief": "Két kvíz-végigjátszás osztott képernyőn: az egyik lakásban, a másik tanyán él – teljesen más top 5 jön ki.",
     "app": "Párkereső kvíz (két eltérő válaszsor)"},
    {"id": "o14", "date": "2026-10-24", "title": "Az ősz legjobb túratársai", "hook": "Őszi túrára mennél? Vidd őket! 🍂",
     "brief": "Energia: Sportos szűrő + Szerep: Sport; vizsla, border collie, husky, ausztrál juhász. Őszi színekkel.",
     "app": "Energia szűrő, Szerep szűrő"},
]

# Platform-útmutató (CMS „Útmutató” fül)
GUIDE = {
    "times": [
        {"platform": "tiktok", "when": "Hétköznap 18:00–21:00, hétvégén 10:00–12:00", "why": "Munka után és hétvégén délelőtt a legaktívabbak."},
        {"platform": "instagram", "when": "Reels: 19:00–21:00 · Feed: 11:30–13:00 · Story: 8:00 és 20:00", "why": "Ebédszünet és esti pihenő."},
        {"platform": "facebook", "when": "12:00 körül vagy 19:00–21:00", "why": "A kutyás csoportok este a legélénkebbek."},
        {"platform": "linkedin", "when": "Kedd–csütörtök 8:00–10:00", "why": "Munkakezdés előtti hírfolyam-görgetés."},
    ],
    "specs": [
        {"what": "TikTok / Reels / Shorts videó", "size": "1080×1920 (9:16), MP4 (H.264)", "note": "Feliratok a biztonsági zónában: felül 220 px, alul 400 px, jobbra 140 px szabadon."},
        {"what": "Instagram feed kép / karusszel", "size": "1080×1350 (4:5)", "note": "A karusszel legfeljebb 20 dia."},
        {"what": "Facebook poszt", "size": "1080×1350 (4:5) vagy 1080×1080", "note": "Linkes poszthoz az Open Graph kép jelenik meg."},
        {"what": "Story (IG / FB)", "size": "1080×1920 (9:16)", "note": "Felül és alul kb. 250 px-t takarnak a gombok."},
        {"what": "LinkedIn poszt", "size": "1080×1350, 1200×627 vagy PDF-karusszel", "note": "A PDF-dokumentum (karusszel) kapja a legtöbb figyelmet."},
        {"what": "Profilkép / borítók", "size": "1080×1080 · FB 1640×624 · LinkedIn 1584×396", "note": ""},
    ],
    "howto": [
        {"title": "TikTok / Reels feltöltése telefonról", "steps": [
            "A CMS-ben nyisd meg a videót, és a Letöltés gombbal mentsd a telefonodra (iPhone-on a megosztás lapon: „Videó mentése”).",
            "Másold ki a posztszöveget a Másolás gombbal.",
            "TikTok: + → Feltöltés → válaszd ki a videót → Hangok: adj hozzá egy felkapott, vidám zenét (a hangerőt vedd halkra, ha csak hangulatnak kell).",
            "Illeszd be a szöveget, válaszd ki a borítóképet (a CMS-ben külön letölthető), majd Közzététel.",
            "Instagram Reels: ugyanez – + → Reel → videó → zene → szöveg → Megosztás; a „Megosztás a Facebookon is” kapcsolóval egyszerre mehet FB-re is.",
            "A CMS-ben jelöld meg a posztot „Kiposztolva” állapotúra.",
        ]},
        {"title": "Link a bióban", "steps": [
            "Instagram és TikTok posztban a link nem kattintható: a profil bemutatkozásába (bio) tedd a Pacsi linkjét – platformonként a sajátját, hogy a statisztika lássa, honnan jöttek: "
            f"Instagram: {link('instagram')} · TikTok: {link('tiktok')} · Facebook: {link('facebook')} · LinkedIn: {link('linkedin')}.",
            "Instagram storyban használj link-matricát – ez kattintható (a story saját linkje a jegyzeteinél van).",
            "Facebookon a link mehet a poszt szövegébe; LinkedInen tedd az első kommentbe. A szövegekben már a posztonkénti rövid link szerepel (pl. pacsit.hu/f/v1) – így ne cseréld le.",
        ]},
        {"title": "Hirdetések (Meta)", "steps": [
            "Meta Hirdetéskezelő → Új kampány → Cél: Forgalom.",
            "Célközönség: Magyarország, 22–45 év, érdeklődés: kutyák, kiskutya, állattartás, örökbefogadás.",
            "Hirdetés A és B egyszerre fusson (A/B teszt); 3–4 nap után a jobb kattintási arányú maradjon.",
            "A cél-URL-ekben UTM-paraméterek vannak: a pacsit.hu sütimentes statisztikája (Umami, stat.pacsit.hu) ezekből mutatja, melyik hirdetés hozza a látogatókat.",
        ]},
        {"title": "Statisztika: melyik poszt hozott látogatót?", "steps": [
            "A posztok linkjei rövid, követhető címek: pacsit.hu/f/<poszt> (Facebook), /i (Instagram), /t (TikTok), /l/<poszt> (LinkedIn), /y (YouTube). A szerver UTM-paraméterekre irányít.",
            "A stat.pacsit.hu-n a Pacsi webhely → UTM nézet: forrás (utm_source) = platform, tartalom (utm_content) = a poszt azonosítója (pl. v1, k_launch), vagy bio.",
            "Az események fülön látszik, mely fajtákat kedvelik, milyen szűrőket kapcsolnak és mit keresnek.",
        ]},
    ],
}


def _tracked_links():
    """A posztszövegekben a sima webcím helyett posztonkénti rövid link álljon (a hirdetések UTM-es címe marad)."""
    bare = re.compile(re.escape(SITE) + r"(?![?\w/])")
    for it in ITEMS:
        for pf, c in (it.get("copy") or {}).items():
            if pf in SHORT and c.get("text"):
                c["text"] = bare.sub(link(pf, it["id"]), c["text"])
        if it.get("firstComment"):   # LinkedInen a link az első kommentbe kerül
            it["firstComment"] = bare.sub(link("linkedin", it["id"]), it["firstComment"])
        pfs = [s["platform"] for s in it.get("slots", []) if s["platform"] in SHORT]
        post = None if it.get("kind") == "profil" else it["id"]   # a profil (bio) linkje poszt nélküli: …/i, …/t
        notes = []
        for n in it.get("notes", []):
            if bare.search(n):   # pl. story link-matricája vagy bio: platformonként külön link
                n = bare.sub(" · ".join(f"{PLATFORMS[p]['name']}: {link(p, post)}" for p in dict.fromkeys(pfs)) or SITE, n)
            notes.append(n)
        if notes:
            it["notes"] = notes


_tracked_links()
