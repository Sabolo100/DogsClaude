"""Pacsi eDM – kampányterv és minden levél tartalma (egy forrás).

Ebből készülnek a levelek (python marketing/tools/email_build.py), a CMS „E-mail” füle és a Mailchimp-piszkozatok
(python marketing/tools/mailchimp.py push). A blokkok leírása: marketing/email/frame.py.

Ütem (2026. okt. 1. – dec. 30.):
  - Indulás (launch): 3 levél 8 nap alatt – okt. 1. (Megérkezett a Pacsi), okt. 3. (Állatok világnapja, 9 magyar fajta),
    okt. 8. (Párkereső kvíz). A közösségi indulással (szept. 28.) együtt fut, ugyanazokra a posztokra hivatkozik.
  - Heti Pacsi-levél: csütörtök 10:00, okt. 15-től. Ünnepek körül: dec. 22. (kedd) és dec. 30. (szerda).
  - Üdvözlő sorozat: feliratkozás után 0., 3. és 7. nap (Mailchimp Customer Journey, kézzel kell összekötni).
  - Partnerlevél: havonta egyszer, kedden, csak a „partner” címkéjű feliratkozóknak.

Hangnem (spec 20. fejezet): tegező, meleg, humoros, de nem infantilis; rövid mondatok; komoly témában egyenes és kedves.
„Illik hozzád”, nem „ez a te kutyád”. Tények: csak az app fajtaadataiból (data/fajtak.json) vagy általánosan
elfogadott állatorvosi tanácsokból – élesítés előtt szakember nézze át (lásd README).
A „Tippelj!” fejtörők válasza mindig ott van a fajta kártyáján (Érdekesség), a megfejtés a következő levélben jön.
"""

HU9 = ["puli", "pumi", "mudi", "komondor", "kuvasz", "erdelyi-kopo", "magyar-vizsla", "drotszoru-magyar-vizsla", "magyar-agar"]
QUIZ_NOTE = "Kattints a tippedre: a fajta kártyáján, az **Érdekesség** rovatban ott a válasz. A megfejtés a következő levélben is jön."

# ---- sorozatok (a CMS címkéi és színei) ----
SERIES = {
    "launch": {"name": "Indulás", "color": "#EE5A2C"},
    "weekly": {"name": "Heti levél", "color": "#17756E"},
    "welcome": {"name": "Üdvözlő sorozat", "color": "#5B5BD6"},
    "partner": {"name": "Partnerlevél", "color": "#B8631A"},
}
STATUSES = {"terv": "Terv", "kesz": "Kész", "jovahagyva": "Jóváhagyva", "piszkozat": "Mailchimp-piszkozat",
            "utemezve": "Ütemezve", "kikuldve": "Kiküldve"}
SEGMENTS = {
    "all": "Minden feliratkozó",
    "partner": "Címke: partner (fajtaklubok, menhelyek, iskolák, állatorvosok, cégek, média)",
    "journey": "Üdvözlő sorozat (Customer Journey: feliratkozás után)",
}

# ---- fejlécképek: honnan készül a 1200×600-as kép ----
#   kv:     marketing/assets/kv/<src>.png levágva (fx, fy: a kivágás középpontja 0–1 között, z: nagyítás)
#   design: marketing/email/img/hero.html?d=<d> (HTML-kompozíció a közösségi képek építőkockáiból)
HEROES = {
    "L1": {"design": "e_launch"},
    "L2": {"design": "e_hu9"},
    "L3": {"design": "e_quiz"},
    "W01": {"design": "e_first"},
    "W02": {"kv": "ekv_osz_tura", "fy": .5},
    "W03": {"kv": "ekv_halloween", "fy": .52},
    "W04": {"kv": "ekv_sotet_seta", "fy": .5},
    "W05": {"design": "e_lowshed"},
    "W06": {"kv": "ekv_orokbefogadas", "fy": .5},
    "W07": {"design": "e_brachy"},
    "W08": {"kv": "ekv_mikulas", "fy": .5},
    "W09": {"kv": "ekv_ajandek", "fy": .52},
    "W10": {"kv": "ekv_szilveszter", "fy": .5},
    "W11": {"kv": "ekv_unnep", "fy": .55},
    "W12": {"kv": "ekv_szilveszter", "fx": .42, "fy": .55, "z": 1.25},
    "WLC1": {"design": "e_welcome"},
    "WLC2": {"design": "e_quiz", "p": "b"},
    "WLC3": {"design": "e_responsible"},
    "P1": {"design": "e_partner"},
    "P2": {"design": "e_partner_stats"},
    "P3": {"kv": "ekv_ajandek", "fx": .45, "fy": .5, "z": 1.1},
}


def hero(eid, kicker, title, lead, cta_label, cta_href, alt, note=None):
    b = {"t": "hero", "img": f"hero/{eid}.jpg", "alt": alt, "kicker": kicker, "title": title, "lead": lead,
         "cta": {"label": cta_label, "href": cta_href}}
    if note:
        b["cta"]["note"] = note
    return b


def quiz(question, opts, note=QUIZ_NOTE):
    """opts: [(felirat, fajta-id)] – minden válasz a fajta kártyájára visz (ott a megfejtés)."""
    return {"t": "quiz", "question": question, "options": [{"label": l, "href": f"app:tippelj#b={b}"} for l, b in opts], "note": note}


def social(*items):
    return {"t": "social", "items": [{"img": f"social/{i}.jpg", "label": l, "title": t, "platform": p} for i, l, t, p in items]}


TRY3 = {"t": "text", "kicker": "Kezdésnek", "title": "3 dolog, amit érdemes kipróbálni", "numbered": True, "content": "harom-dolog", "list": [
    "**Szűrj a saját életedre.** Lakás, kisgyerek, vékony falak? Három koppintás, és a 124 fajtából csak azok maradnak, amelyek tényleg illenek hozzád. [Kipróbálom](app:szures#f=lakas;gyerek;csendes&m=s)",
    "**Töltsd ki a Párkereső kvízt.** 10 gyors kérdés, a végén megtudod, milyen gazdi vagy, és melyik 5 fajta illik hozzád a legjobban. [Indulhat a kvíz](app:kviz#kviz)",
    "**Ismerd meg a 9 magyar fajtát.** Puli, pumi, mudi, komondor, kuvasz, erdélyi kopó, két vizsla és a magyar agár – egy koppintás a Magyar szűrőre. [Megnézem őket](app:magyar#f=magyar&m=s)",
]}
TYPES6 = [
    "🛋️ **Kanapé-kapitány** – nyugis esték, rövid séták, sok bújás.",
    "🏃 **Aktív kalandor** – futás, túra, bicikli: bírja a tempót.",
    "👨‍👩‍👧 **Családi karmester** – gyerekzsivaj, türelmes családtag.",
    "🏙️ **Városi flâneur** – kávézóterasz, parki séta, lift.",
    "🛡️ **Tanyasi őrangyal** – van udvar, kell egy hűséges őrző.",
    "🎓 **Kutyasuttogó** – tapasztalt vagy, kihívásra vágysz.",
]

EMAILS = [
    # =================================================================== INDULÁS
    {
        "id": "L1", "series": "launch", "date": "2026-10-01", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Megérkezett a Pacsi",
        "subject": "Adj egy pacsit! 🐾 Megérkezett a Pacsi",
        "subjectAlt": ["124 kutyafajta, 1 perc, 0 regisztráció", "Melyik kutya illik hozzád? Most kiderül 🐾"],
        "preheader": "Ingyenes kutyafajta-választó: élő fajtafelhő, szűrők és Párkereső kvíz – regisztráció nélkül.",
        "theme": "Indulás: mi a Pacsi, 3 dolog, amit érdemes kipróbálni. A közösségi indulás (szept. 28.) posztjaira épül.",
        "social": ["v1", "k_launch", "s_hello", "v4"],
        "blocks": [
            hero("L1", "Új · ingyenes · 124 kutyafajta", "Adj egy pacsit a hozzád *illő* kutyának!",
                 "A Pacsi ingyenes, magyar kutyafajta-választó. 124 fajta lebeg egy élő felhőben, és minden szűrődre reagál: ami nem illik hozzád, kirepül, ami igen, előrejön.",
                 "Kipróbálom", "app:hero", "A Pacsi kabalája pacsit ad egy kéznek, körülötte kutyaportré-buborékok.",
                 note="Regisztráció nélkül, telefonon és gépen is – és appként is telepíthető."),
            {"t": "intro", "paras": [
                "Kutyát választani izgalmas – és könnyű elrontani. Sokan a legcukibb kölyökfotó alapján döntenek, aztán kiderül, hogy a kis gombócból napi két óra futásra vágyó sportoló lesz egy harmadik emeleti lakásban.",
                "Ezért csináltuk a Pacsit. Nem mondja meg, melyik „a te kutyád”, de megmutatja, **melyik fajta illik az életedhez** – és azt is, miért.",
            ]},
            {"t": "stats", "items": [("124", "kutyafajta"), ("10", "kvízkérdés"), ("0", "regisztráció")]},
            TRY3,
            social(("v1", "TikTok · Reels", "Melyik kutya illik hozzád?", "tiktok"),
                   ("k_launch", "Instagram · Facebook", "Adj egy pacsit!", "instagram"),
                   ("v4", "Videó", "Zsebrakéta vagy kanapé-óriás?", "tiktok")),
            {"t": "share"},
            {"t": "sign", "ps": "Válaszolj erre a levélre, és írd meg: van már kutyád, vagy most választasz? Szívesen olvasunk minden választ."},
        ],
    },
    {
        "id": "L2", "series": "launch", "date": "2026-10-03", "time": "09:00", "segment": "all", "status": "kesz",
        "title": "Állatok világnapja: a 9 magyar kutyafajta",
        "subject": "Ismered mind a 9 magyar kutyafajtát? 🇭🇺",
        "subjectAlt": ["Puli, pumi, mudi… és még 6 magyar kincs", "Holnap Állatok világnapja – ünnepeljük a magyar fajtákat!"],
        "preheader": "Holnap Állatok világnapja: ünnepeljük a hazai fajtákat! Melyik illik hozzád?",
        "theme": "Október 4., Állatok világnapja: a 9 magyar fajta. A v3 videó és a k_hu9 poszt (okt. 4.) előzetese.",
        "social": ["v3", "k_hu9"],
        "blocks": [
            hero("L2", "Október 4. · Állatok világnapja", "9 magyar kutyafajta, *akire büszkék lehetünk*",
                 "Pásztorok, őrzők, vadászok és egy szélvész. Mindegyiknek megvan a maga története – és a maga gazdija.",
                 "Megnézem mind a 9-et", "app:hero#f=magyar&m=s", "A 9 magyar kutyafajta portréja buborékokban."),
            {"t": "intro", "paras": [
                "Holnap Állatok világnapja, mi pedig a hazai kedvencekkel ünneplünk. A Pacsiban egyetlen koppintás a **Magyar fajta** szűrő, és a 124 fajtából csak ők maradnak a felhőben.",
            ]},
            {"t": "breeds", "title": "Melyik illik hozzád?", "ids": HU9, "content": "magyar-fajtak", "notes": {
                "puli": "Élő raszta-felhő, örök kamasz", "pumi": "Göndör, pörgős terelő", "mudi": "Sokoldalú agility-bajnok",
                "komondor": "Zsinórbundás őrangyal", "kuvasz": "Nemes fehér őrző", "erdelyi-kopo": "A Kárpátok kitartó vadásza",
                "magyar-vizsla": "Aranybarna tépőzár-kutya", "drotszoru-magyar-vizsla": "Szakállas, strapabíró vizsla",
                "magyar-agar": "Sprint után nagy alvó"}},
            {"t": "fact", "big": "2016", "title": "A pumi Amerikában is befutott",
             "text": "Az Amerikai Kennel Klub 2016-ban ismerte el hivatalosan a pumit, azóta a tengerentúlon is egyre ismertebb.",
             "cta": {"label": "A pumi kártyája", "href": "app:tudtad#b=pumi"}},
            {"t": "tip", "kicker": "Mielőtt döntesz", "title": "Magyar fajtát választanál? Ezt nézd meg előtte", "items": [
                "Sok magyar fajta **munkakutya**: napi 1,5–2 óra mozgás és feladat kell nekik.",
                "A nagy őrzőfajták (komondor, kuvasz) **tapasztalt gazdit** és nagy, jól bekerített udvart kívánnak.",
                "Csendes lakótársat keresel? A **magyar agár** keveset ugat – de futni imád.",
                "Keress **szűrt szülőktől** származó kölyköt (pl. csípőízületi diszplázia), és kérdezd a fajtaklubot.",
            ]},
            social(("v3", "Holnap jön · TikTok · Reels", "A 9 magyar kutyafajta", "tiktok"),
                   ("k_hu9", "Instagram · Facebook", "Ismered mind a 9-et?", "instagram")),
            {"t": "share", "title": "Ki a legnagyobb magyarkutya-rajongó az ismerőseid között?",
             "text": "Küldd el neki ezt a levelet – vagy egyenesen a Pacsit. Egy koppintás a Magyar fajta szűrő, és ott van mind a kilenc."},
            {"t": "sign", "text": "Boldog Állatok világnapját!"},
        ],
    },
    {
        "id": "L3", "series": "launch", "date": "2026-10-08", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Milyen gazdi vagy? – Párkereső kvíz",
        "subject": "Milyen gazdi vagy? 10 kérdés, 1 perc 🤔",
        "subjectAlt": ["Kanapé-kapitány vagy aktív kalandor?", "Te melyik gazditípus vagy?"],
        "preheader": "A Párkereső kvíz megmutatja a gazditípusodat és a hozzád illő top 5 fajtát. A hét fajtája: a vizsla.",
        "theme": "A Párkereső kvíz, a 6 gazditípus. A hét fajtája: rövidszőrű magyar vizsla (egyezik a közösségi „A hét fajtája” okt. 8-i posztjával).",
        "social": ["v2", "k_quiz", "c_lakas", "k_tudtad_basenji", "k_het_vizsla"],
        "blocks": [
            hero("L3", "Párkereső kvíz", "Milyen gazdi vagy? *10 kérdés, 1 perc.*",
                 "Kanapé-kapitány, Aktív kalandor, Családi karmester, Városi flâneur, Tanyasi őrangyal vagy Kutyasuttogó? A végén azt is megmutatjuk, melyik 5 fajta illik hozzád a legjobban.",
                 "Indulhat a kvíz", "app:hero#kviz", "A hat gazditípus ikonjai kártyákon, középen egy nagy kérdőjel."),
            {"t": "intro", "paras": [
                "Van, aki hajnalban fut, és van, aki a kanapén olvas. A kutyák is ilyenek – ezért nem mindegy, ki kivel kerül egy fedél alá. A kvíz 10 gyors kérdéssel feltérképezi a napjaidat, és ehhez keres fajtát.",
            ]},
            {"t": "text", "kicker": "A 6 gazditípus", "title": "Te melyik vagy?", "marker": "", "content": "gazditipusok", "list": TYPES6,
             "after": "A kvíz végén egy gombbal a barátaidnak is elküldheted az eredményed."},
            {"t": "breed", "id": "magyar-vizsla", "traits": ["E", "Gy", "L"],
             "text": "Ahová te mész, oda ő is. Imádja a családját, a gyerekeket és a hosszú, pórázon kívüli futásokat. Napi 8–10 óra egyedüllét viszont nem neki való.",
             "fact": True},
            quiz("Melyik fajta kölykei születnek hófehéren, pöttyök nélkül?", [("Dalmata", "dalmata"), ("Border collie", "border-collie"), ("Beagle", "beagle")]),
            social(("v2", "TikTok · Reels", "Milyen gazdi vagy?", "tiktok"),
                   ("c_lakas", "Karusszel", "5 kutya, amiért a szomszéd is hálás lesz", "instagram"),
                   ("k_tudtad_basenji", "Tudtad?", "A basenji jódlizik", "instagram")),
            {"t": "share", "title": "Kíváncsi vagy, a barátaid milyen gazdik?",
             "text": "Küldd el nekik a kvízt, aztán hasonlítsátok össze az eredményt. Garantált beszélgetésindító."},
            {"t": "sign", "ps": "Te mi lettél? Írd meg válaszban – kíváncsiak vagyunk, melyik gazditípusból van a legtöbb."},
        ],
    },
    # =================================================================== HETI LEVÉL
    {
        "id": "W01", "series": "weekly", "no": 1, "date": "2026-10-15", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Első kutyád lesz?",
        "subject": "Első kutyád lesz? Ez a 6 fajta neked való",
        "subjectAlt": ["Kezdő gazdi? Ők türelmesek veled 🐾", "6 fajta, amelyik megbocsátja a kezdő hibákat"],
        "preheader": "Kezdőbarát fajták, 5 kérdés választás előtt, és a hét fajtája: a mudi.",
        "theme": "Kezdőbarát fajták (o6 videóötlet), 5 kérdés választás előtt. A hét fajtája: mudi (a közösségin is okt. 15.).",
        "social": ["k_map4", "k_tudtad_agar", "k_het_mudi", "k_compare"],
        "blocks": [
            hero("W01", "Pacsi-levél · 1. szám", "Első kutyád lesz? *Ők türelmesek veled.*",
                 "Vannak fajták, amelyek megbocsátják a kezdő hibákat, könnyen tanulnak, és nem kérnek napi két óra futást. Összeszedtük a legkezdőbarátabbakat.",
                 "Mutasd a kezdőbarát fajtákat", "app:hero#f=kezdo&m=s", "Hat kezdőbarát kutyafajta portréja buborékokban."),
            {"t": "intro", "paras": [
                "Az első kutya olyan, mint az első autó: sokat tanulsz vele, és jó, ha elnéző. Ez a levél azoknak szól, akik most vágnak bele.",
            ]},
            {"t": "breeds", "kicker": "Kezdőbarát hatos", "title": "Ők könnyen tanulnak és alkalmazkodnak", "content": "kezdobarat",
             "lead": "Hat fajta, amelyik a Pacsi szerint különösen jó első kutya lehet – persze csak akkor, ha az életmódodhoz is illik.",
             "ids": ["golden-retriever", "labrador-retriever", "cavalier-king-charles-spaniel", "havanese", "uszkar", "bichon-frise"],
             "notes": {"golden-retriever": "Türelmes családtag, imád hordani", "labrador-retriever": "Mindenki barátja – és a falatoké",
                       "cavalier-king-charles-spaniel": "Bújós, szelíd városi társ", "havanese": "Vidám, lakásba is ideális",
                       "uszkar": "Okos, és alig hullat", "bichon-frise": "Vattapamacs, kezdőknek is"},
             "cta": {"label": "Szűrés: Kezdő gazdinak", "href": "app:kezdobarat#f=kezdo&m=s"}},
            {"t": "tip", "kicker": "Mielőtt döntesz", "title": "5 kérdés, amit tegyél fel magadnak", "numbered": True, "content": "5-kerdes", "items": [
                "**Mennyi időd van naponta?** Egy kutya átlagosan napi 1–2 óra figyelmet kér: séta, játék, tanítás.",
                "**Hány órát lenne egyedül?** A legtöbb kutya nehezen bírja a napi 8–10 óra magányt.",
                "**Hol laksz?** Lakás, kert, lift, vékony falak – mind számít a fajtaválasztásnál.",
                "**Mennyi pénz fér bele?** Táp, állatorvos, oltások, kozmetika: a kutya havi kiadás, 10–15 évig.",
                "**Ki vigyáz rá, ha elutazol?** Jobb előre tudni, mint az utolsó pillanatban keresni.",
            ], "after": "A Pacsi kvíze ezekre is rákérdez – egy perc az egész.",
             "cta": {"label": "Kitöltöm a kvízt", "href": "app:5-kerdes#kviz"}},
            {"t": "breed", "id": "mudi", "traits": ["E", "I", "L"],
             "text": "Terel, őriz, és az agilitypályán is verhetetlen. Okos, bátor, a családjához nagyon kötődik – első kutyának viszont csak akkor jó, ha sportos életet élsz.",
             "fact": True},
            {"t": "answer", "text": "Múlt héten azt kérdeztük, melyik fajta kölykei születnek hófehéren. A válasz: a **dalmata**! A jellegzetes pöttyök csak az első hetekben kezdenek megjelenni."},
            quiz("Melyik fajta volt az első hivatalos olimpiai kabala?", [("Tacskó", "tacsko"), ("Uszkár", "uszkar"), ("Golden retriever", "golden-retriever")]),
            social(("k_map4", "Instagram · Facebook", "Zsebrakéta vagy kanapé-óriás?", "instagram"),
                   ("k_tudtad_agar", "Tudtad?", "70 km/h, mégis kanapészobor", "instagram"),
                   ("k_het_mudi", "A hét fajtája", "Mudi", "instagram")),
            {"t": "share", "title": "Ismersz valakit, aki most választ először kutyát?",
             "text": "Neki szól ez a levél. Küldd tovább, vagy küldd el neki a Pacsit – egy perc a kvíz."},
            {"t": "sign", "ps": "Tapasztalt gazdi vagy? Írd meg válaszban, mit tanácsolnál egy kezdőnek – a legjobb tippeket egy későbbi levélben megosztjuk (névvel vagy név nélkül, ahogy szeretnéd)."},
        ],
    },
    {
        "id": "W02", "series": "weekly", "no": 2, "date": "2026-10-22", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Hosszú hétvége: őszi túra kutyával",
        "subject": "Hosszú hétvége: vidd túrázni a kutyád! 🍂",
        "subjectAlt": ["Őszi túra kutyával: mit tegyél a hátizsákba?", "A legjobb őszi túratársak (és egy zseni)"],
        "preheader": "Túracsekklista, kullancsvédelem, és a hét fajtája: a border collie, a kutyavilág zsenije.",
        "theme": "Október 23. – hosszú hétvége: őszi túra. A hét fajtája: border collie (a közösségin okt. 21-én „Tudtad? Chaser”).",
        "social": ["k_card", "h_cuki", "k_tudtad_border"],
        "blocks": [
            hero("W02", "Pacsi-levél · 2. szám", "Hosszú hétvége: *irány az erdő!*",
                 "Pénteken ünnepnap, az erdők pedig most a legszebbek. Összeszedtük, mire figyelj, ha a kutyád is jön.",
                 "Túrabírók a Pacsiban", "app:hero#f=energia:sportos&m=s", "Vizsla és a Pacsi kabala őszi erdei ösvényen, hulló levelek között."),
            {"t": "intro", "paras": [
                "Az ősz a kutyások kedvenc évszaka: nincs kánikula, és minden levélkupac egy új szagtérkép. Ha a hosszú hétvégén túrázni mentek, ez a lista jól jöhet.",
            ]},
            {"t": "tip", "kicker": "Túracsekklista", "title": "Ez legyen a hátizsákban", "content": "tura", "items": [
                "**Víz és összecsukható tál** – a kutya is megszomjazik, a patakvíz nem mindig tiszta.",
                "**Póráz és jól illeszkedő hám** – erdőben vadra futhat, és sok helyen kötelező is a póráz.",
                "**Kullancsvédelem** – ősszel is aktívak. Túra után nézd át a fülét, a hónalját és az ujjai közét.",
                "**Rövidebb táv, mint gondolnád** – a kölyök, az idős és a lapos orrú kutya hamarabb elfárad.",
                "**Telefonszámos biléta a nyakörvön** – a chip mellett ez a leggyorsabb segítség, ha elkóborol.",
                "**Jutalomfalat és egy törölköző** – az egyik a visszahíváshoz, a másik az autóhoz.",
            ], "after": "Nem minden kutya túrakutya – és ez így van rendjén. A Pacsiban az **Energia** szűrővel megnézheted, kinek mennyi mozgás kell."},
            {"t": "breed", "id": "border-collie", "traits": ["E", "I", "L"],
             "text": "Túrán, terelésben, agilityben verhetetlen: napi két óra mozgás és sok szellemi feladat kell neki. Egy kényelmes, otthonülő életben viszont boldogtalan lenne.",
             "fact": True},
            {"t": "answer", "text": "Az első hivatalos olimpiai kabala egy **tacskó** volt: a csíkos Waldi, az 1972-es müncheni olimpián."},
            quiz("Melyik fajta szukái tüzelnek évente csak egyszer, mint a farkasok?", [("Basenji", "basenji"), ("Szibériai husky", "sziberiai-husky"), ("Akita inu", "akita-inu")]),
            social(("k_card", "Instagram · Facebook", "Minden, ami számít – egy kártyán", "instagram"),
                   ("h_cuki", "Instagram · Facebook", "Ne a legcukibbat válaszd", "instagram"),
                   ("k_tudtad_border", "Tudtad?", "Chaser, a zseni border collie", "instagram")),
            {"t": "share"},
            {"t": "sign", "ps": "Küldj egy fotót a túráról válaszlevélben! A kedvenceinket – a te engedélyeddel – megmutatjuk a közösségi oldalainkon."},
        ],
    },
    {
        "id": "W03", "series": "weekly", "no": 3, "date": "2026-10-29", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Halloween: jelmez talán, csoki soha",
        "subject": "Jelmez talán, csoki soha 🎃",
        "subjectAlt": ["Halloween kutyával: mi veszélyes, mi vicces?", "A hot dog jelmez oké. A csoki nem."],
        "preheader": "Mi veszélyes a kutyára Halloweenkor, mikor jó ötlet a jelmez – és a hét fajtája: a tacskó.",
        "theme": "Halloween (okt. 31.): veszélyes édességek, jó jelmez. A hét fajtája: tacskó (hot dog jelmez a képen).",
        "social": [],
        "socialPlan": ["Reels: 3 kutyabarát jelmez 10 másodpercben (hot dog, denevér, boszorkány) – a levél illusztrációjával",
                       "Story-kvíz: csoki, szőlő vagy alma – melyik veszélyes a kutyára?",
                       "Kép: Halloween-illusztráció, „Jelmez talán, csoki soha” felirattal"],
        "blocks": [
            hero("W03", "Pacsi-levél · 3. szám", "Jelmez talán, *csoki soha.*",
                 "Szombaton Halloween. A tökös mécses hangulatos, a hot dog jelmez vicces – az édességes tál viszont a kutyának komoly veszély.",
                 "A hét fajtája: a tacskó", "app:hero#b=tacsko", "Tacskó hot dog jelmezben, francia bulldog denevérszárnyakkal és a Pacsi kabala boszorkánykalapban, tökök között."),
            {"t": "intro", "paras": [
                "Október végén a boltok polcai tele vannak édességgel, a lépcsőházak tökös mécsessel. Összeszedtük, hogyan lesz a Halloween a kutyádnak is buli – és nem állatorvosi ügyelet.",
            ]},
            {"t": "tip", "kicker": "Vigyázat!", "title": "Ezek ne kerüljenek a kutya közelébe", "tone": "sand", "content": "veszelyes", "items": [
                "**Csokoládé** – a benne lévő teobromin mérgező a kutyáknak, az étcsoki a legveszélyesebb.",
                "**Xilit (nyírfacukor)** – sok cukormentes rágóban és édességben van; kis mennyiségben is életveszélyes.",
                "**Mazsola és szőlő** – veseelégtelenséget okozhat.",
                "**Csomagolás, pálcika, mécses** – lenyelve elzáródást, a láng égési sérülést okozhat.",
            ], "after": "Ha a kutyád mégis evett valamit ezek közül, **ne várd meg a tüneteket**: hívd az állatorvost vagy egy 0–24 órás ügyeletet."},
            {"t": "text", "kicker": "Jelmez vagy nem jelmez?", "title": "A jó jelmez olyan, amit észre sem vesz", "content": "jelmez", "list": [
                "Ne takarja el a szemét, fülét, orrát, és ne szorítsa a nyakát.",
                "Legyen laza és könnyen levehető – ha vakarja, vagy nem fekszik le tőle, vedd le.",
                "Egy színes kendő vagy egy vicces nyakörv a fotón ugyanolyan jól mutat.",
                "Ha a csengetés és a jelmezes gyerekek felzaklatják, legyen egy csendes szoba, ahová elvonulhat.",
            ]},
            {"t": "breed", "id": "tacsko", "traits": ["L", "U", "Gy"],
             "text": "Bátor, humoros, és imád szimatolni. Lakásban is jól elvan, ha van lift – a sok lépcső és az ugrálás ugyanis nem tesz jót a hátának.",
             "fact": "Hot dog jelmezben is jól mutat 🌭 – de a hátára vigyázz: a normál testsúly és a kevés ugrálás sokat segít a porckorongjainak.", "factLabel": "Gazdi-tipp"},
            {"t": "answer", "text": "A **basenji** szukái a farkasokhoz hasonlóan évente csak egyszer tüzelnek. (Bónusz: a basenji nem ugat, hanem jódlizik.)"},
            quiz("Melyik fajtának kékesfekete a nyelve?", [("Csau csau", "csau-csau"), ("Mopsz", "mopsz"), ("Szamojéd", "szamojed")]),
            {"t": "share"},
            {"t": "sign", "ps": "Van jelmezes kutyafotód? Küldd el válaszban! 🎃"},
        ],
    },
    {
        "id": "W04", "series": "weekly", "no": 4, "date": "2026-11-05", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Sötétedik: láthatóság az esti sétán",
        "subject": "Sötétedik. Látszik a kutyád? 🔦",
        "subjectAlt": ["Fél ötkor már sötét: 5 apróság az esti sétához", "Esti séta: így vesznek észre titeket"],
        "preheader": "Láthatósági tippek esti sétához, és a hét fajtája: a puli, az élő raszta-felhő.",
        "theme": "Óraátállítás után: esti séták, láthatóság. A hét fajtája: puli.",
        "social": [],
        "socialPlan": ["Reels: sötét utca, lámpafényben előbukkan a LED-nyakörves kutya – „Látszik a kutyád?”",
                       "Karusszel: 5 láthatósági kellék esti sétához",
                       "Story: szavazás – hánykor sétáltok este?"],
        "blocks": [
            hero("W04", "Pacsi-levél · 4. szám", "Sötétedik. *Látszik a kutyád?*",
                 "Az óraátállítás óta fél ötkor már szürkület van, a délutáni séta sokszor sötétben zajlik. Pár apróság, amitől az autósok és a biciklisek is időben észrevesznek titeket.",
                 "A hét fajtája: a puli", "app:hero#b=puli", "A Pacsi kabala világító nyakörvvel és fényvisszaverő mellényben sétál egy esti, lámpafényes utcán."),
            {"t": "intro", "paras": [
                "Novemberben a legtöbb gazdi munka előtt és után sétál – vagyis sötétben. A kutya szőre elnyeli a fényt, a sötét bundájúakat szinte lehetetlen észrevenni.",
            ]},
            {"t": "tip", "kicker": "Esti séta", "title": "5 apróság, amitől látszotok", "content": "lathatosag", "items": [
                "**Világító vagy fényvisszaverő nyakörv, hám** – a LED-es változat oldalról is jól látszik.",
                "**Fényvisszaverő mellény a kutyán** – főleg sötét bundánál, vidéken és út mellett.",
                "**Te is légy látható** – egy fényvisszaverő karszalag vagy mellény rajtad is sokat számít.",
                "**Rövid póráz a forgalom mellett** – a hosszú, feszes póráz sötétben szinte láthatatlan.",
                "**Zseblámpa a zacskós feladathoz** – mert a kupac akkor is ott van, ha nem látod. 😉",
            ]},
            {"t": "breed", "id": "puli", "traits": ["E", "A", "H"],
             "text": "A zsinórjai alig hullanak, de a bundaápolás komoly elköteleződés. Okos, figyelmes, sok játékot és feladatot kér – és sötét bundás pulival esti sétán a fényvisszaverő mellény kötelező kellék.",
             "fact": True},
            {"t": "answer", "text": "A **csau csau** nyelve kékesfekete – és nincs egyedül: a **shar pei** nyelve is ilyen."},
            quiz("Melyik fajta neve jelent kínaiul „oroszlánt”?", [("Shih tzu", "shih-tzu"), ("Csau csau", "csau-csau"), ("Pekingi palotakutya", "pekingi-palotakutya")]),
            {"t": "share"},
            {"t": "sign", "ps": "Van bevált esti sétás kütyüd? Írd meg válaszban – a legjobb tippeket továbbadjuk."},
        ],
    },
    {
        "id": "W05", "series": "weekly", "no": 5, "date": "2026-11-12", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Allergiás vagy? Ők alig hullatnak",
        "subject": "Allergiás vagy? Ők alig hullatnak 🤧",
        "subjectAlt": ["Kevés szőr a kanapén: 6 fajta, amelyik alig hullat", "A „hipoallergén” kutya mítosz"],
        "preheader": "Alig hulló fajták, egy fontos igazság a „hipoallergén” kutyákról – és miért nem jár libacsont Márton-napon.",
        "theme": "Kevés szőrhullás (o7 videóötlet), a hipoallergén-mítosz; Márton-nap (nov. 11.): libacsont tilos. A hét fajtája: uszkár.",
        "social": [],
        "socialPlan": ["Reels (o7 ötlet): Allergiás vagy? Ők alig hullatnak – 6 portré, a Pacsi Kevés szőrhullás szűrőjével",
                       "Kép: „A hipoallergén kutya mítosz” – tévhit vs. valóság",
                       "Story: Márton-nap – libacsont? Nem!"],
        "blocks": [
            hero("W05", "Pacsi-levél · 5. szám", "Allergiás vagy? *Ők alig hullatnak.*",
                 "Kevesebb szőr a kanapén, kevesebb tüsszentés. Hat fajta, amelyiknek alig hullik a szőre – és egy fontos igazság, mielőtt döntesz.",
                 "Szűrés: Kevés szőrhullás", "app:hero#f=hullas&m=s", "Hat göndör és selymes bundájú kutyafajta portréja buborékokban."),
            {"t": "intro", "paras": [
                "Sokan azért nem mernek kutyát tartani, mert allergiásak. Jó hír: vannak fajták, amelyek alig hullatják a szőrüket. Kevésbé jó hír: 100%-ban allergiabarát kutya nem létezik.",
            ]},
            {"t": "text", "kicker": "Fontos", "title": "A „hipoallergén” kutya mítosz", "tone": "lav", "content": "mitosz", "paras": [
                "Az allergiát nem maga a szőr okozza, hanem a kutya bőréből és nyálából származó fehérjék. A kevés szőrt hullató fajtáknál ezek kevésbé terjednek szét a lakásban, ezért sok allergiás jobban bírja őket – de ez kutyánként és emberenként is más.",
            ], "after": "**Tipp:** mielőtt döntesz, tölts több órát a kiszemelt fajta kutyáival (például egy tenyésztőnél vagy egy barátodnál), és kérd ki az orvosod véleményét is."},
            {"t": "breeds", "title": "Hat fajta, amelyik alig hullat", "content": "alig-hullat",
             "lead": "A göndör vagy selymes bunda folyamatosan nő, ezért rendszeres fésülés és kozmetikus kell – cserébe kevesebb szőr kerül a lakásba.",
             "ids": ["uszkar", "bichon-frise", "lagotto-romagnolo", "portugal-vizikutya", "havanese", "tibeti-terrier"],
             "notes": {"uszkar": "Négy méretben, okos és sportos", "bichon-frise": "Vidám vattapamacs", "lagotto-romagnolo": "Göndör szarvasgomba-kereső",
                       "portugal-vizikutya": "Az Obama család kedvence", "havanese": "Kubai táncos lélek", "tibeti-terrier": "Hótalpas szerencsehozó"}},
            {"t": "breed", "id": "uszkar", "traits": ["I", "H", "K"],
             "text": "Toy, törpe, közép és óriás méretben is létezik. Elegáns és sportos, alig hullat – és az egyik legkönnyebben tanítható fajta. A rendszeres kozmetikus viszont jár neki.",
             "fact": True},
            {"t": "tip", "kicker": "Márton-nap után", "title": "A libacsont nem kutyának való", "tone": "sand", "content": "marton-nap", "items": [
                "**A főtt vagy sült szárnyascsont szilánkosan törik**, és megsértheti a kutya száját, nyelőcsövét, beleit.",
                "**A zsíros bőr és a töltelék** hasnyálmirigy-gyulladást okozhat.",
                "**Hagyma, fokhagyma** – a töltelékben és a mártásban is ott lehet, és a kutyáknak ártalmas.",
            ], "after": "Jutalomnak jobb egy kutyáknak való rágócsont vagy egy falat főtt, fűszerezetlen hús – csont nélkül."},
            {"t": "answer", "text": "A **shih tzu** neve kínaiul „oroszlánt” jelent – a körben szétálló arcszőrzete miatt pedig „krizantémarcú kutyának” is becézik."},
            quiz("Melyik fajtát hívták a 19. századi angol bányászok „szegény ember versenylovának”?", [("Whippet", "whippet"), ("Angol agár", "angol-agar"), ("Jack Russell terrier", "jack-russell-terrier")]),
            {"t": "share", "title": "Ismersz valakit, aki allergia miatt nem mer kutyát tartani?",
             "text": "Küldd el neki ezt a levelet. Lehet, hogy mégis van számára megoldás – egy alapos próbával."},
            {"t": "sign", "ps": "Allergiás vagy, mégis kutyád van? Írd meg, neked mi vált be – sokaknak segíthet."},
        ],
    },
    {
        "id": "W06", "series": "weekly", "no": 6, "date": "2026-11-19", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Gondolj az örökbefogadásra",
        "subject": "A legjobb barátod lehet, hogy már vár rád 🏡",
        "subjectAlt": ["Gondoltál már az örökbefogadásra?", "Örökbefogadás lépésről lépésre"],
        "preheader": "Hogyan zajlik az örökbefogadás, mire figyelj – és a hét fajtája: a spanyol galgó.",
        "theme": "Örökbefogadás (o10 videóötlet). Partnermenhelyek bemutatása (P2 kérte be). A hét fajtája: spanyol galgó.",
        "social": [],
        "socialPlan": ["Reels (o10 ötlet): „Gondolj az örökbefogadásra” – a Pacsi kvíze segít típust választani a menhelyen is",
                       "Karusszel: Örökbefogadás 5 lépésben",
                       "Közös poszt egy partnermenhellyel: „Ők várnak rád” (a menhely fotóival, engedéllyel)"],
        "blocks": [
            hero("W06", "Pacsi-levél · 6. szám", "A legjobb barátod *lehet, hogy már vár rád.*",
                 "Rengeteg kutya vár új otthonra menhelyeken és állatvédő egyesületeknél. Ha kutyát szeretnél, érdemes velük kezdeni – a Pacsi ebben is segít.",
                 "Milyen típus illik hozzám?", "app:hero#kviz", "Egy fiatal pacsit fogad egy menhelyi kutyától, a háttérben kíváncsi kutyák a kerítés mögött."),
            {"t": "intro", "paras": [
                "A Pacsi fajtákról szól, de a kérdés, amit feltesz, mindenkire igaz: milyen kutya illik az életedhez? Ha tudod, milyen típust keresel (energia, méret, ugatás, gyerekek), a menhelyen is könnyebb jól választani.",
                "Egy felnőtt menhelyi kutyánál ráadásul sokszor már azt is látod, milyen a természete – nem kell a kölyökből kitalálni.",
            ]},
            {"t": "tip", "kicker": "Örökbefogadás", "title": "Így zajlik, lépésről lépésre", "numbered": True, "content": "orokbefogadas", "items": [
                "**Nézd át a menhelyek oldalait.** A legtöbb helyen fotó és rövid leírás van minden kutyáról: kor, méret, természet, kijön-e macskával, gyerekkel.",
                "**Kérdezz sokat.** Az önkéntesek jól ismerik a kutyákat, és őszintén elmondják, kinek valók.",
                "**Ismerkedj többször.** Sétáljatok együtt, vidd el a családot is. Van, ahol ideiglenes befogadásra is van lehetőség.",
                "**Készülj fel otthon.** Fekhely, tál, póráz, egy csendes sarok – és türelem: az első hetekben minden új neki.",
                "**Számíts szerződésre.** A legtöbb szervezet örökbefogadási szerződést köt, és sokszor díjat vagy adományt kér – ez a következő kutyák ellátását segíti.",
            ]},
            {"t": "breed", "id": "spanyol-galgo", "traits": ["U", "L", "Gy"],
             "text": "Sok galgó mentett kutyaként érkezik: nyugodtak, bújósak, és egy jó sprint után órákig alszanak. Csendes lakótárs – kisállatos háztartásban viszont egyedi mérlegelés kell.",
             "fact": True},
            {"t": "text", "kicker": "Menhelyeknek, egyesületeknek", "tone": "soft", "content": "menhelyeknek", "paras": [
                "Szívesen bemutatjuk a munkátokat vagy egy-egy gazdira váró kutyátokat a Pacsi-levélben és a közösségi oldalainkon. Írjatok egy válaszlevelet!",
            ]},
            {"t": "answer", "text": "A **whippetet** hívták a 19. századi észak-angliai bányászok „szegény ember versenylovának”: szabadidejükben versenyeken futtatták."},
            quiz("Melyik fajta híres mentőkutyája mentett meg a hagyomány szerint több mint 40 embert?", [("Bernáthegyi", "bernathegyi"), ("Új-fundlandi", "uj-fundlandi"), ("Németjuhász", "nemet-juhaszkutya")]),
            {"t": "share", "title": "Ismersz valakit, aki örökbe fogadna?",
             "text": "Küldd el neki ezt a levelet. Lehet, hogy egy kutya ettől talál otthont."},
            {"t": "sign", "ps": "Van örökbefogadott kutyád? Meséld el a történetét válaszban – ha engeded, megosztjuk."},
        ],
    },
    {
        "id": "W07", "series": "weekly", "no": 7, "date": "2026-11-26", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Lapos orrú fajták: mire figyelj?",
        "subject": "Lapos orr, nagy szív – mire figyelj? 🐶",
        "subjectAlt": ["Francia bulldog vagy mopsz? Ezt tudd előtte", "Cuki pofa, nehéz légzés? Olvasd el, mielőtt választasz"],
        "preheader": "Mit jelent a brachycephal szindróma, mit kérdezz a tenyésztőtől – és a hét fajtája: a francia bulldog.",
        "theme": "Lapos orrú (brachycephal) fajták (o11 videóötlet); Black Friday-hét. A hét fajtája: francia bulldog.",
        "social": [],
        "socialPlan": ["Reels (o11 ötlet): Lapos orrú fajták – mire figyelj? (légzés, hőség, tenyésztő)",
                       "Kép: A hét fajtája – francia bulldog",
                       "Story: „A kutyád legjobb ajándéka ingyen van” – 3 ötlet Black Fridayre"],
        "blocks": [
            hero("W07", "Pacsi-levél · 7. szám", "Lapos orr, nagy szív – *mire figyelj?*",
                 "A francia bulldog, a mopsz és társaik imádnivalók. A rövid orr azonban sokszor nehezebb légzéssel jár – ezt jó tudni, mielőtt választasz.",
                 "A francia bulldog kártyája", "app:hero#b=francia-bulldog", "Hat lapos orrú kutyafajta portréja buborékokban."),
            {"t": "intro", "paras": [
                "A lapos orrú (brachycephal) fajták évek óta a legnépszerűbbek között vannak – nem véletlenül: kedvesek, vidámak, lakásba valók. A Pacsi nem lebeszél róluk, csak őszintén elmondja, mire figyelj.",
            ]},
            {"t": "text", "kicker": "Brachycephal szindróma", "title": "Mit jelent a rövid orr?", "tone": "lav", "content": "brachy", "paras": [
                "A nagyon rövid orrú kutyáknál az orrlyukak és a légutak szűkebbek lehetnek. Ez horkolással, gyors kifulladással, hőségben akár életveszélyes túlmelegedéssel is járhat.",
            ], "list": [
                "**Figyeld a légzést:** ha a kutya nyugalomban is hangosan szuszog vagy horkol, kérdezd az állatorvost.",
                "**Kérdezd a tenyésztőt**, milyenek a szülők: tágak-e az orrlyukaik, bírják-e a sétát, volt-e légúti műtétjük.",
                "**Nyáron vigyázz:** csak hűvösben mozogjatok, és sose hagyd a kutyát autóban.",
                "**Tegyél félre** a nagyobb állatorvosi költségekre, vagy nézz utána a kisállat-biztosításnak.",
            ]},
            {"t": "breeds", "kicker": "A Pacsi lapos orrú fajtái", "title": "Ők a leggyakoribbak", "content": "lapos-orr",
             "ids": ["francia-bulldog", "mopsz", "angol-bulldog", "boston-terrier", "shih-tzu", "pekingi-palotakutya"],
             "notes": {"francia-bulldog": "Denevérfülű városi sztár", "mopsz": "Ráncos kis komédiás", "angol-bulldog": "Morcos arc, arany szív",
                       "boston-terrier": "Szmokingos kis úriember", "shih-tzu": "Krizantémarcú kis oroszlán", "pekingi-palotakutya": "Császári öleb"}},
            {"t": "breed", "id": "francia-bulldog", "traits": ["L", "U", "E"],
             "text": "Keveset ugat, lakásba ideális, és a gyerekekkel is jól kijön. Futótársnak viszont nem való, és hőségben különösen vigyázni kell rá.",
             "fact": True},
            {"t": "text", "kicker": "Black Friday", "title": "A kutyád legjobb ajándéka ingyen van", "tone": "mint", "content": "black-friday", "paras": [
                "Egy hosszabb séta új útvonalon, egy házi szimatjáték (jutalomfalat egy összegyűrt törölközőben), tíz perc közös trükktanulás. A pénztárcádnak is jót tesz. 😉",
            ]},
            {"t": "answer", "text": "A hagyomány szerint a **bernáthegyi** Barry több mint 40 embert mentett meg a 19. század elején – kitömött teste ma is látható a berni Természettudományi Múzeumban."},
            quiz("Melyik fajta régi jelmondata a „multum in parvo”, vagyis „sok egy kicsiben”?", [("Mopsz", "mopsz"), ("Chihuahua", "chihuahua"), ("Yorkshire terrier", "yorkshire-terrier")]),
            {"t": "share"},
            {"t": "sign", "ps": "Van lapos orrú kutyád? Írd meg, mi a legjobb tipped – továbbadjuk azoknak, akik most választanak."},
        ],
    },
    {
        "id": "W08", "series": "weekly", "no": 8, "date": "2026-12-03", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Mikulás: mi kerülhet a kutya csizmájába?",
        "subject": "Mi kerülhet a kutya csizmájába? 🎅",
        "subjectAlt": ["Mikulás a kutyának: igen, de ne csokival", "Kutyabarát Mikulás-csomag 5 perc alatt"],
        "preheader": "Kutyabarát Mikulás-csomag, mi jöhet és mi tilos – és a hét fajtája: a szamojéd, a mosolygó hófelhő.",
        "theme": "Mikulás (dec. 6.): kutyabarát csomag, tiltólista. A hét fajtája: szamojéd.",
        "social": [],
        "socialPlan": ["Reels: kutyabarát csizma összeállítása 10 másodpercben (répa, alma, rágójáték)",
                       "Kép: „Igen / Nem” – Mikulás-csomag kutyának",
                       "Kép: A hét fajtája – szamojéd"],
        "blocks": [
            hero("W08", "Pacsi-levél · 8. szám", "Mi kerülhet *a kutya csizmájába?*",
                 "Vasárnap Mikulás! Ha a kutya is kap csomagot, legyen benne csupa olyan jóság, ami neki is jót tesz.",
                 "A hét fajtája: a szamojéd", "app:hero#b=szamojed", "A Pacsi kabala Mikulás-sapkában szimatolja a kutyabarát jutalomfalatokkal teli csizmát."),
            {"t": "intro", "paras": [
                "December elején minden ablakban csizma, minden csizmában csoki. A kutyánál ez utóbbit érdemes kihagyni – attól még ő is lehet ünnepelt.",
            ]},
            {"t": "tip", "kicker": "Kutyabarát csomag", "title": "Ezek jöhetnek", "content": "mikulas-igen", "items": [
                "**Kutyáknak készült jutalomfalat** – kis darabokban, hogy tanításra is jó legyen.",
                "**Répa, alma (mag nélkül), főtt tök** – ropogós, egészséges nasi.",
                "**Rágójáték vagy szimatszőnyeg** – leköti, és a rágás megnyugtatja.",
                "**Egy új játék, amit együtt használtok** – a közös játék a legjobb ajándék.",
            ]},
            {"t": "tip", "kicker": "Ezek nem", "title": "Ezeket tartsd távol", "tone": "sand", "content": "mikulas-nem", "items": [
                "**Csokoládé és szaloncukor** – a teobromin mérgező, a csomagolás lenyelve veszélyes.",
                "**Makadámdió és más diófélék** – a makadámdió kifejezetten mérgező, a többi is okozhat gondot.",
                "**Mazsola, szőlő** – kis mennyiségben is veseelégtelenséget okozhat.",
                "**Xilit (nyírfacukor)** – cukormentes édességekben; életveszélyes.",
            ]},
            {"t": "breed", "id": "szamojed", "traits": ["Gy", "H", "E"],
             "text": "Imádja a hideget, a gyerekeket és a társaságot – házőrzőnek viszont túl barátságos. A szőrhullásra és a porszívózásra készülj fel.",
             "fact": True},
            {"t": "answer", "text": "A „multum in parvo” – vagyis „sok egy kicsiben” – a **mopsz** régi jelmondata."},
            {"t": "quiz", "question": "Mit vitt 1925-ben egy husky-staféta az alaszkai Nome városába?", "options": [
                {"label": "Karácsonyi leveleket", "href": "app:tippelj#b=sziberiai-husky"},
                {"label": "Diftéria elleni szérumot", "href": "app:tippelj#b=sziberiai-husky"},
                {"label": "Aranyrögöket", "href": "app:tippelj#b=sziberiai-husky"}],
             "note": "Kattints bármelyikre: a szibériai husky kártyáján, az **Érdekesség** rovatban ott a válasz. A megfejtés a következő levélben is jön."},
            {"t": "share"},
            {"t": "sign", "ps": "Kap a kutyád Mikulás-csomagot? Mutasd meg válaszban! 🎅"},
        ],
    },
    {
        "id": "W09", "series": "weekly", "no": 9, "date": "2026-12-10", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Kutyát karácsonyra? Előbb olvasd el ezt",
        "subject": "Kutyát karácsonyra? Előbb olvasd el ezt 🎁",
        "subjectAlt": ["Kiskutya a fa alatt? 7 kérdés előtte", "A legszebb ajándék – ha jól átgondolt"],
        "preheader": "7 kérdés, mielőtt kutyát ajándékoznál, és jobb ötletek, ha még nem biztos. A hét fajtája: a golden retriever.",
        "theme": "Felelős döntés karácsony előtt: a kutya nem meglepetés. A partnerlevél (P3) közös üzenete. A hét fajtája: golden retriever.",
        "social": [],
        "socialPlan": ["Reels: „Kutyát karácsonyra?” – 7 kérdés gyors vágásokkal",
                       "Karusszel: Ajándékozz készülődést – 4 jobb ötlet",
                       "Közös poszt partnermenhelyekkel és fajtaklubokkal (a P3 partnerlevél anyaga)"],
        "blocks": [
            hero("W09", "Pacsi-levél · 9. szám", "Kutyát karácsonyra? *Előbb olvasd el ezt.*",
                 "Egy kutya 10–15 évre szóló döntés, nem meglepetés. Ha a családotok tényleg készen áll, a karácsony gyönyörű kezdet lehet – de csak akkor.",
                 "Töltsük ki együtt a kvízt", "app:hero#kviz", "Kiskutya ül egy becsomagolt ajándék mellett; mellette póráz, tál és fekhely."),
            {"t": "intro", "paras": [
                "Az állatvédők minden évben arra kérik a családokat, hogy ne meglepetésként ajándékozzanak kutyát – mert az átgondolatlan döntés sokszor a menhelyen végződik. Pár kérdés előre sok fájdalmat megspórol.",
            ]},
            {"t": "tip", "kicker": "Mielőtt becsomagolnád", "title": "7 kérdés, amire a családnak igennel kell felelnie", "numbered": True, "content": "7-kerdes", "items": [
                "Mindenki szeretné, és tudja, hogy 10–15 évre szól?",
                "Megvan, ki sétáltat reggel és este – esőben, hóban is?",
                "Kinek a dolga a tanítás, a kozmetika, az állatorvos?",
                "Belefér a havi költség (táp, orvos, biztosítás, panzió)?",
                "Megvan, hol lesz nyaraláskor és betegség esetén?",
                "Illik a fajta a családhoz (energia, méret, ugatás, szőrhullás)?",
                "Tudjátok, honnan hozzátok (felelős tenyésztő vagy menhely)?",
            ], "after": "Ha bármelyikre „talán” a válasz, adjatok magatoknak még egy kis időt – a jó kutya megéri a várakozást."},
            {"t": "text", "kicker": "Jobb ötlet, ha még nem biztos", "title": "Ajándékozz készülődést", "tone": "peach", "content": "ajandekotletek", "list": [
                "**Egy közös menhelylátogatás** vagy önkéntes nap – ismerkedésnek tökéletes.",
                "**Egy kutyás könyv vagy tanfolyam** (például kölyökiskola-utalvány) a leendő gazdinak.",
                "**A Pacsi kvíze közösen, a karácsonyfa alatt** – és beszéljétek meg, mit mutat.",
                "**Kutyás kellékek egy „ígéret” kártyával:** a kutya tavasszal jön, amikor mindenki készen áll.",
            ]},
            {"t": "breed", "id": "golden-retriever", "traits": ["Gy", "K", "E"],
             "text": "A gyerekekkel is kiváló, és első kutyának is jó választás. Napi másfél óra mozgás és sok hulló szőr viszont jár a csomaghoz.",
             "fact": True},
            {"t": "answer", "text": "1925-ben a husky-staféta **diftéria elleni szérumot** vitt a járvány sújtotta Nome városába. A két leghíresebb vezérkutya, Balto és Togo is szibériai husky volt."},
            quiz("Melyik fajta nagy, lapos mancsai működnek hótalpként?", [("Tibeti terrier", "tibeti-terrier"), ("Szamojéd", "szamojed"), ("Bernáthegyi", "bernathegyi")]),
            {"t": "share", "title": "Ismersz valakit, aki kutyát ajándékozna?",
             "text": "Küldd el neki ezt a levelet – kedvesen, nem kioktatva. 🎁 Lehet, hogy pont ettől lesz jó a döntés."},
            {"t": "sign", "ps": "Nálatok is volt „kutya a fa alatt”? Írd meg, hogyan sikerült!"},
        ],
    },
    {
        "id": "W10", "series": "weekly", "no": 10, "date": "2026-12-17", "time": "10:00", "segment": "all", "status": "kesz",
        "title": "Szilveszter két hét múlva: készülj most",
        "subject": "Szilveszter 2 hét múlva: készítsd fel a kutyád 🎆",
        "subjectAlt": ["Fél a tűzijátéktól? Most kezdj el készülni", "Két hét is sokat számít a tűzijáték-félelem ellen"],
        "preheader": "Búvóhely, hangszoktatás, chip-adatok – és ami az ünnepi asztalról tilos. A hét fajtája: a beagle.",
        "theme": "Tűzijáték-felkészítés 2 héttel előre; ünnepi asztal veszélyei. A hét fajtája: beagle. A dec. 30-i levélbe olvasói tippeket kér.",
        "social": [],
        "socialPlan": ["Reels: búvóhely építése 20 másodpercben",
                       "Karusszel: Szilveszteri felkészülés 5 lépésben",
                       "Story-emlékeztető dec. 30-án és 31-én délután"],
        "blocks": [
            hero("W10", "Pacsi-levél · 10. szám", "Szilveszter két hét múlva: *kezdd el most.*",
                 "Sok kutya retteg a tűzijátéktól. A jó hír: két hét alatt is sokat tehetsz azért, hogy az év utolsó éjszakája nyugodtabb legyen.",
                 "A hét fajtája: a beagle", "app:hero#b=beagle", "Border collie pihen egy letakart, hangulatos búvóhelyen, az ablakon túl messzi tűzijáték."),
            {"t": "intro", "paras": [
                "A kutyák hallása sokkal élesebb a miénknél, ezért a durranás nekik még ijesztőbb. A félelem nem rossz nevelés és nem hiszti – valódi stressz, amin segíthetsz.",
            ]},
            {"t": "tip", "kicker": "Két hét alatt", "title": "Így készülj fel", "numbered": True, "content": "szilveszter-felkeszules", "items": [
                "**Alakíts ki búvóhelyet** egy csendes szobában: letakart boksz vagy asztal alatti fekhely, a kedvenc takarójával. Hagyd, hogy már most megszokja.",
                "**Szoktasd a hangokhoz fokozatosan:** tűzijáték-hangot játssz nagyon halkan, közben játssz vagy etesd. Csak akkor hangosíts, ha nyugodt marad.",
                "**Beszélj az állatorvossal**, ha a kutyád nagyon fél: vannak nyugtató megoldások, de ezeket előre, szakemberrel kell kipróbálni.",
                "**Frissítsd a chip adatait**, és tegyél telefonszámos bilétát a nyakörvre – szilveszterkor sok kutya ijedtében elszökik.",
                "**Tervezd meg a napot:** 31-én a nagy séta délután, sötétedés előtt legyen, pórázon.",
            ]},
            {"t": "tip", "kicker": "Ünnepi asztal", "title": "Ami neked finom, neki veszélyes lehet", "tone": "sand", "content": "unnepi-asztal", "items": [
                "**Csont, halszálka** – szilánkosan törik, sérülést okozhat.",
                "**Zsíros maradék, töltelék, bejgli** – hasnyálmirigy-gyulladást, gyomorrontást okozhat. A mákos és a diós bejgli sem kutyának való.",
                "**Hagyma, fokhagyma, szőlő, mazsola, csoki** – ezek mérgezőek a kutyának.",
            ]},
            {"t": "breed", "id": "beagle", "traits": ["U", "Gy", "E"],
             "text": "Imádja a gyerekeket és a társaságot, de hangos, és szökésre mindig kész – szilveszterkor különösen figyelj rá.",
             "fact": True},
            {"t": "answer", "text": "A **tibeti terrier** nagy, lapos, kerek mancsai hótalpként működnek, így könnyebben halad a havas, sziklás terepen."},
            quiz("Melyik fajta sok képviselője hordoz olyan génváltozatot, ami fokozza az éhségérzetét?", [("Labrador retriever", "labrador-retriever"), ("Beagle", "beagle"), ("Golden retriever", "golden-retriever")]),
            {"t": "share", "title": "Ismersz valakit, akinek a kutyája fél a tűzijátéktól?",
             "text": "Küldd el neki most – két hét elég ahhoz, hogy sokat javuljon a helyzet."},
            {"t": "sign", "ps": "Neked mi vált be szilveszterkor? Írd meg – a december 30-i levélben összegyűjtjük a legjobb tippeket."},
        ],
    },
    {
        "id": "W11", "series": "weekly", "no": 11, "date": "2026-12-22", "time": "10:00", "segment": "all", "status": "terv",
        "todo": "A „2026 kedvencei” toplistát dec. 18-án a stat.pacsit.hu „kedvenc” eseményeiből kell kitölteni (a mostani 6 fajta csak helykitöltő).",
        "title": "Boldog ünnepeket + 2026 kedvencei",
        "subject": "Boldog ünnepeket a falkától! 🎄",
        "subjectAlt": ["2026 kedvenc fajtái a Pacsiban", "Köszönjük, hogy velünk voltál idén 🐾"],
        "preheader": "Az idei kedvencek a Pacsiban, egy ünnepi fejtörő, és köszönet mindenkinek, aki velünk tartott.",
        "theme": "Év végi levél kedden (dec. 22.): a közösség kedvenc fajtái a névtelen statisztikából, ünnepi fejtörő.",
        "social": [],
        "socialPlan": ["Kép: 2026 kedvencei a Pacsiban (top 6, a valós statisztikából)",
                       "Reels: az ünnepi falka illusztrációja – „Boldog ünnepeket!”",
                       "Story: ünnepi kvíz – kinek volt pekingi palotakutyája?"],
        "blocks": [
            hero("W11", "Pacsi-levél · 11. szám", "Boldog ünnepeket *a falkától!*",
                 "Köszönjük, hogy idén velünk tartottál. Az ünnepek előtt egy utolsó, könnyű levél: az év kedvencei és egy fejtörő a fa alá.",
                 "Nyisd meg a Pacsit", "app:hero", "Öt kutya kötött sálban ül egy feldíszített fenyő mellett, hóesésben."),
            {"t": "intro", "paras": [
                "Szeptember végén indult a Pacsi, azóta sokan szűrtek, kvízeztek és gyűjtöttek kedvenc fajtákat. Megnéztük, melyik fajtákat jelölték meg a legtöbben kedvencnek.",
            ]},
            {"t": "breeds", "kicker": "2026 kedvencei", "title": "A Pacsi-közösség kedvenc fajtái", "content": "kedvencek-2026", "todo": True,
             "lead": "A névtelen statisztika szerint ezeket a fajtákat jelöltétek a legtöbbször kedvencnek.",
             "ids": ["magyar-vizsla", "golden-retriever", "border-collie", "francia-bulldog", "labrador-retriever", "puli"]},
            {"t": "answer", "text": "A **labradorok** közül sokan hordozzák a POMC gén egy hibás változatát, ami fokozza az éhségérzetet – ezért olyan falánkok. Az ünnepi asztal alatt különösen figyelj rájuk!"},
            quiz("Melyik fajtából kapott ajándékba egy kutyát Viktória királynő 1860-ban?", [("Pekingi palotakutya", "pekingi-palotakutya"), ("Mopsz", "mopsz"), ("Máltai selyemkutya", "maltai-selyemkutya")]),
            {"t": "text", "kicker": "Köszönjük", "content": "koszonjuk", "paras": [
                "Köszönjük mindenkinek, aki kipróbálta a Pacsit, továbbküldte a leveleinket vagy visszajelzést adott – sokat tanultunk belőle.",
            ]},
            {"t": "share", "title": "Ajándék, ami nem kerül semmibe",
             "text": "Küldd el a Pacsit valakinek, aki kutyáról álmodik. Az ünnepek alatt jut idő egy közös kvízre."},
            {"t": "sign", "text": "Boldog, nyugodt ünnepeket kívánunk – neked és a falkádnak!", "ps": "A következő levél december 30-án jön, egy szilveszteri gyorslistával."},
        ],
    },
    {
        "id": "W12", "series": "weekly", "no": 12, "date": "2026-12-30", "time": "10:00", "segment": "all", "status": "terv",
        "todo": "Az „Olvasóink tippjei” rész a dec. 17-i levélre érkező válaszokból töltendő ki (a beküldő engedélyével).",
        "title": "Szilveszteri gyorslista + 2027",
        "subject": "Holnap szilveszter: 8 pontos gyorslista 🎆",
        "subjectAlt": ["Utolsó simítások a nyugodt szilveszterhez", "Ma még ráérsz: így lesz nyugodt az éjfél"],
        "preheader": "Gyorslista a holnapi estére, olvasóink legjobb tippjei – és mi jön 2027-ben.",
        "theme": "Szilveszter előtti nap (szerda): gyorslista, olvasói tippek, 2027-es előzetes.",
        "social": [],
        "socialPlan": ["Story (dec. 31. délután): 8 pontos gyorslista",
                       "Kép: „Holnap szilveszter” gyorslista",
                       "Poszt jan. 1-jén: Boldog új évet a falkától!"],
        "blocks": [
            hero("W12", "Pacsi-levél · 12. szám", "Holnap szilveszter: *8 pontos gyorslista.*",
                 "Ha két hete elkezdtétek a készülődést, szuper. Ha nem, ez a lista még most is sokat segít.",
                 "Nyisd meg a Pacsit", "app:hero", "Nyugodt kutya a takaróval letakart búvóhelyén, az ablakon túl tűzijáték."),
            {"t": "intro", "paras": [
                "Holnap este durrognak a petárdák. Egy nyugodt este titka most a jó előkészület – és egy kis türelem.",
            ]},
            {"t": "tip", "kicker": "Szilveszteri gyorslista", "title": "8 pont holnapra", "numbered": True, "content": "gyorslista", "items": [
                "**Délutáni nagy séta**, sötétedés előtt, pórázon – este már csak egy rövid kör.",
                "**Biléta a nyakörvön**, a chip adatai frissek.",
                "**Ablakok, függönyök zárva**, halk zene vagy tévé szól a háttérben.",
                "**A búvóhely szabad:** ne húzd ki onnan, ha oda bújik.",
                "**Nyugodtan vigasztald:** ha megnyugtatod, simogatod, azzal nem „jutalmazod” a félelmet.",
                "**Kapu, erkélyajtó zárva** – a vendégeknek is szólj, hogy figyeljenek az ajtóra.",
                "**Rágójáték, szimatszőnyeg:** a rágás és a szimatolás nyugtat.",
                "**Ne vidd magaddal** a tűzijátékra, és ne hagyd egyedül a kertben.",
            ]},
            {"t": "text", "kicker": "Olvasóink tippjei", "title": "Amit ti írtatok", "tone": "soft", "content": "olvasoi-tippek", "todo": True, "paras": [
                "[Ide kerülnek a december 17-i levélre érkezett legjobb válaszok – névvel vagy név nélkül, ahogy a beküldő kérte.]",
            ]},
            {"t": "answer", "text": "Viktória királynő 1860-ban egy **pekingi palotakutyát** kapott ajándékba – az elsők egyikét, amelyet a pekingi Nyári Palotából vittek Angliába."},
            {"t": "text", "kicker": "2027", "title": "Mi jön jövőre?", "content": "2027", "paras": [
                "Januártól folytatjuk a csütörtöki leveleket: új fajtabemutatók, gazdi-tippek és fejtörők. Ha van ötleted, miről olvasnál szívesen, írd meg válaszban!",
            ]},
            {"t": "share"},
            {"t": "sign", "text": "Nyugodt szilvesztert és boldog új évet!",
             "ps": "Ha a kutyád mégis elszökne: azonnal jelezd a chip-nyilvántartásban (Petvetdata) és a környékbeli menhelyeken, és oszd meg a helyi kutyás csoportokban."},
        ],
    },
    # =================================================================== ÜDVÖZLŐ SOROZAT
    {
        "id": "WLC1", "series": "welcome", "no": 1, "delay": "feliratkozás után azonnal", "segment": "journey", "status": "kesz",
        "title": "Üdv a falkában!",
        "subject": "Üdv a falkában! 🐾 Itt a Pacsi-levél",
        "subjectAlt": ["Köszi, hogy feliratkoztál! Ezt várhatod", "Szia! Ezt a 3 dolgot próbáld ki elsőként"],
        "preheader": "Csütörtökönként jövünk fajtaajánlóval, gazdi-tippekkel és egy kis fejtörővel. Addig is: 3 dolog, amit érdemes kipróbálni.",
        "theme": "Üdvözlés: mit kap a feliratkozó, 3 dolog az appban, kérés: vegye fel a címet a névjegyzékbe, válaszoljon egy szóval.",
        "blocks": [
            hero("WLC1", "Üdv a falkában!", "Szia! *Örülünk, hogy itt vagy.*",
                 "Mostantól csütörtökönként érkezik a Pacsi-levél: a hét fajtája, gazdi-tippek, egy kis fejtörő – és semmi spam.",
                 "Nyisd meg a Pacsit", "app:hero", "A Pacsi kabalája integet, körülötte kutyaportré-buborékok."),
            {"t": "intro", "nogreet": True, "paras": [
                "Köszönjük, hogy feliratkoztál! Egy kérésünk van: tedd a címünket a névjegyzékedbe, hogy a levelek ne a Promóciók vagy a Spam mappában landoljanak.",
            ]},
            TRY3,
            {"t": "text", "kicker": "Mit kapsz tőlünk?", "title": "Hetente egy levél, csupa kutyás jóval", "tone": "peach", "content": "mit-kapsz", "list": [
                "**A hét fajtája** – egy fajta közelről: kinek illik, kinek nem.",
                "**Gazdi-tippek** – évszakhoz, ünnepekhez, élethelyzetekhez.",
                "**Tippelj!** – egy kis fejtörő; a megfejtés a Pacsi fajtakártyáin.",
                "**Csak hetente egyszer** – és bármikor leiratkozhatsz egy kattintással.",
            ]},
            {"t": "sign", "ps": "Válaszolj erre a levélre egyetlen szóval: van már kutyád, vagy most választasz? Ebből tudjuk, milyen tartalmat küldjünk."},
        ],
    },
    {
        "id": "WLC2", "series": "welcome", "no": 2, "delay": "a feliratkozás utáni 3. napon", "segment": "journey", "status": "kesz",
        "title": "Milyen gazdi vagy? (üdvözlő 2.)",
        "subject": "Te milyen gazdi vagy? 🤔",
        "subjectAlt": ["10 kérdés, és kiderül, melyik fajta illik hozzád", "Egy perc az egész – próbáld ki!"],
        "preheader": "Egy perc az egész: megtudod a gazditípusodat és a hozzád illő top 5 fajtát.",
        "theme": "A Párkereső kvíz, a 6 gazditípus, megosztás.",
        "blocks": [
            hero("WLC2", "Párkereső kvíz", "Milyen gazdi vagy? *Egy perc, és kiderül.*",
                 "10 gyors kérdés az életedről – a végén megkapod a gazditípusodat és a hozzád illő 5 fajtát.",
                 "Indulhat a kvíz", "app:hero#kviz", "A hat gazditípus ikonjai kártyákon."),
            {"t": "intro", "paras": [
                "Pár napja iratkoztál fel – itt az első feladat. 😉 A Párkereső kvíz 10 gyors kérdéssel megnézi, milyen az életed, és ehhez keres fajtát.",
            ]},
            {"t": "text", "kicker": "A 6 gazditípus", "title": "Te melyik leszel?", "marker": "", "content": "gazditipusok", "list": TYPES6,
             "cta": {"label": "Kiderítem", "href": "app:gazditipusok#kviz"}},
            {"t": "share", "title": "Kíváncsi vagy, a barátaid milyen gazdik?",
             "text": "Küldd el nekik a kvízt, aztán hasonlítsátok össze az eredményt."},
            {"t": "sign"},
        ],
    },
    {
        "id": "WLC3", "series": "welcome", "no": 3, "delay": "a feliratkozás utáni 7. napon", "segment": "journey", "status": "kesz",
        "title": "5 gyakori hiba kutyaválasztáskor (üdvözlő 3.)",
        "subject": "5 hiba, amit sokan elkövetnek kutyaválasztáskor",
        "subjectAlt": ["Ne a legcukibbat válaszd 🐾", "A jó döntés titka: az életmódod"],
        "preheader": "A legcukibb nem mindig a legjobb: így kerüld el a leggyakoribb hibákat – és ismerd meg a 9 magyar fajtát.",
        "theme": "Felelős választás: 5 gyakori hiba; a 9 magyar fajta.",
        "blocks": [
            hero("WLC3", "Üdv a falkában · 3/3", "Ne a legcukibbat válaszd – *hanem azt, aki illik hozzád.*",
                 "Öt gyakori hiba kutyaválasztáskor, és hogyan kerülheted el őket.",
                 "Szűrés a saját életemre", "app:hero", "Telefonon a Pacsi fajtakártyája, mellette szűrőchipek."),
            {"t": "intro", "paras": [
                "Az elmúlt napokban megnézhetted, milyen gazdi vagy (ha nem, [itt pótolhatod](app:bevezeto#kviz)). Most jöjjön a legfontosabb rész: hogyan lesz a választásból jó döntés.",
            ]},
            {"t": "tip", "kicker": "Felelős választás", "title": "5 gyakori hiba", "numbered": True, "tone": "sand", "content": "5-hiba", "items": [
                "**A külső alapján dönteni.** A kölyökfotó cuki – de a felnőtt kutya igényei számítanak. Nézd meg a kártyáján az energiát és az ugatást is.",
                "**Alábecsülni a mozgásigényt.** Egy vizslának vagy border collie-nak napi 1,5–2 óra kell, egy mopsznak fél óra is elég.",
                "**Elfelejteni a szomszédokat.** Vékony falú lakásba nem jó egy sokat ugató fajta.",
                "**Nem számolni a költségekkel.** Táp, orvos, kozmetika: egyes fajtáknál ez jóval több.",
                "**Rossz helyről hozni.** A felelős tenyésztő szűrt szülőket mutat, a menhely őszintén beszél a kutyáról – a hirdetési oldalak kiskutyái mögött viszont sokszor szaporítók állnak.",
            ]},
            {"t": "breeds", "kicker": "A 9 magyar fajta", "title": "Ismerd meg a hazai kincseket", "ids": HU9, "content": "magyar-fajtak"},
            {"t": "share"},
            {"t": "sign", "ps": "Mostantól csütörtökönként jövünk. Jó böngészést!"},
        ],
    },
    # =================================================================== PARTNERLEVÉL
    {
        "id": "P1", "series": "partner", "no": 1, "date": "2026-10-13", "time": "10:00", "segment": "partner", "status": "kesz",
        "title": "Partnerlevél 1. – kész anyag a tagjaitoknak",
        "subject": "Pacsi partnereknek: kész anyag a tagjaitoknak 🐾",
        "subjectAlt": ["Köszönjük! Így mutathatjátok meg a Pacsit", "Egy ingyenes eszköz a leendő gazdiknak – megosztanátok?"],
        "preheader": "Kész posztszöveg és kép a csatornáitokra, egy kérés a fajtaleírásokhoz – és a heti levél a tagjaitoknak.",
        "theme": "Első partnerlevél: kész posztszöveg + kép, lektorálási kérés, feliratkozó link a tagoknak.",
        "blocks": [
            hero("P1", "Pacsi Partnerlevél · 1.", "Köszönjük, hogy *velünk vagytok!*",
                 "A Pacsi ingyenes, magyar kutyafajta-választó: 124 fajta, szűrők, Párkereső kvíz. Abban segít, hogy a leendő gazdik az életmódjukhoz illő kutyát válasszanak – és ebben ti vagytok a legfontosabb szövetségeseink.",
                 "Nézd meg a Pacsit", "app:hero", "Tizenhárom kutya ül egy sorban, középen a Pacsi kabala."),
            {"t": "intro", "partner": True, "paras": [
                "Ebben a rövid levélben három dolgot kaptok: kész anyagot, amit megoszthattok a tagjaitokkal, egy kérést, amihez a szakértelmetekre számítunk, és egy linket, amellyel a tagjaitok is feliratkozhatnak a heti Pacsi-levélre.",
            ]},
            {"t": "kit", "title": "Posztszöveg a Facebook-oldalatokra vagy a hírlevélbe", "lead": "Nyugodtan írjátok át a saját hangotokra.",
             "post": "Kutyát szeretnél, de nem tudod, melyik fajta illik hozzád? 🐾 Próbáld ki a Pacsit: ingyenes, magyar kutyafajta-választó 124 fajtával. Szűrj a saját életedre (lakás, gyerek, mozgás, ugatás), vagy töltsd ki a 10 kérdéses Párkereső kvízt. Regisztráció nélkül: https://pacsit.hu",
             "img": "social/p_og.jpg", "alt": "A Pacsi linkelőnézeti képe: kutyaportrék felhője és a pacsit.hu felirat.", "imghref": "app:partnerkep",
             "after": "A képet jobb kattintással menthetitek, vagy írjatok, és elküldjük nagy felbontásban. Ha kéritek, saját követhető linket is adunk, így látjátok, hány embert hoztatok."},
            {"t": "text", "kicker": "Egy kérés", "title": "Nézzétek át a fajtátok kártyáját!", "content": "lektoralas", "paras": [
                "A fajtaleírások és a jellemző-pontszámok forrásokból, AI-segítséggel készültek – de a fajtákat ti ismeritek a legjobban. Ha nyitottak vagytok rá, nézzétek meg a számotokra fontos fajták kártyáit, és írjátok meg, ha valamit pontosítanátok. A javításokat a következő frissítésben átvezetjük.",
             ], "cta": {"label": "Fajták a Pacsiban", "href": "app:lektoralas", "ghost": True}},
            {"t": "text", "kicker": "A tagjaitoknak", "title": "Heti Pacsi-levél, csütörtökönként", "tone": "peach", "content": "tagoknak", "paras": [
                "Fajtaajánló, gazdi-tippek és egy kis fejtörő, hetente egyszer. Ha szívesen ajánlanátok, ez a feliratkozó link: [feliratkozás a Pacsi-levélre](mc:subscribe).",
            ]},
            {"t": "sign", "ps": "Kérdésetek vagy ötletetek van? Egyszerűen válaszoljatok erre a levélre."},
        ],
    },
    {
        "id": "P2", "series": "partner", "no": 2, "date": "2026-11-10", "time": "10:00", "segment": "partner", "status": "terv",
        "todo": "A számokat és a „mit mutatnak a számok” bekezdést nov. 9-én a stat.pacsit.hu adataiból kell kitölteni.",
        "title": "Partnerlevél 2. – első számok, örökbefogadás-téma",
        "subject": "Partnerhírek: mit keresnek a leendő gazdik? 📊",
        "subjectAlt": ["Első számok a Pacsiból", "November: örökbefogadás-téma a Pacsi-levélben"],
        "preheader": "Az első hetek számai, a novemberi örökbefogadás-témánk – és kész anyag menhelyeknek, kluboknak.",
        "theme": "Statisztikai visszajelzés a partnereknek; felhívás a nov. 19-i örökbefogadás-témához (menhelyek bemutatása).",
        "blocks": [
            hero("P2", "Pacsi Partnerlevél · 2.", "Mit keresnek *a leendő gazdik?*",
                 "Az első hetek névtelen statisztikája már mutatja, mire kíváncsiak az emberek, amikor kutyát választanak.",
                 "Nézd meg a Pacsit", "app:hero", "Telefonon a Pacsi, körülötte szűrőchipek és fajtaportrék."),
            {"t": "intro", "partner": True, "paras": ["Rövid frissítés az első hetekről – és egy felhívás a novemberi örökbefogadás-témánkhoz."]},
            {"t": "stats", "todo": True, "items": [("[x]", "látogató"), ("[x]", "kitöltött kvíz"), ("[x]", "kedvencnek jelölt fajta")]},
            {"t": "text", "kicker": "Amit a számok mutatnak", "todo": True, "content": "szamok", "paras": [
                "[Frissítendő a statisztikából: a 3 legnépszerűbb szűrő, a legtöbbször megnyitott fajták és egy meglepetés.]",
            ]},
            {"t": "text", "kicker": "November 19.", "title": "Örökbefogadás-téma a Pacsi-levélben", "tone": "peach", "content": "orokbefogadas-felhivas", "paras": [
                "November 19-én a heti levelünk az örökbefogadásról szól. Menhelyek, egyesületek: ha szeretnétek, bemutatunk titeket vagy egy-egy gazdira váró kutyátokat – a ti fotóitokkal, a ti engedélyetekkel. Írjatok november 16-ig!",
            ]},
            {"t": "kit", "title": "Posztszöveg novemberre",
             "post": "Örökbe fogadnál, de nem tudod, milyen kutya illene hozzád? 🐾 A Pacsi 10 kérdéses Párkereső kvíze megmutatja, milyen típus (energia, méret, ugatás) illik az életedhez – így a menhelyen is könnyebb jól választani. Ingyenes: https://pacsit.hu",
             "img": "hero/W06.jpg", "alt": "Örökbefogadási pillanat: egy menhelyi kutya pacsit ad.", "imghref": "app:partnerkep"},
            {"t": "sign"},
        ],
    },
    {
        "id": "P3", "series": "partner", "no": 3, "date": "2026-12-08", "time": "10:00", "segment": "partner", "status": "kesz",
        "title": "Partnerlevél 3. – karácsony előtt, közös üzenet",
        "subject": "Karácsony előtt: segítsetek, hogy jól döntsenek 🎁",
        "subjectAlt": ["Kutyát karácsonyra? Közös üzenet a partnerekkel", "Év végi köszönet a Pacsi partnereinek"],
        "preheader": "Kész anyag a „Kutyát karácsonyra?” témához, év végi köszönet, és mire készülünk 2027-ben.",
        "theme": "Közös üzenet a dec. 10-i levélhez (kutya nem meglepetésajándék), köszönet, 2027.",
        "blocks": [
            hero("P3", "Pacsi Partnerlevél · 3.", "Karácsony előtt: *segítsetek, hogy jól döntsenek.*",
                 "December 10-én a heti levelünk arról szól, miért ne legyen a kutya meglepetésajándék. Nagy segítség lenne, ha ti is megosztanátok.",
                 "A Pacsi kvíze", "app:hero#kviz", "Kiskutya egy becsomagolt ajándék mellett."),
            {"t": "intro", "partner": True, "paras": ["Az év utolsó partnerlevelében egy közös ügyhöz kérünk segítséget, és elmondjuk, mire készülünk jövőre."]},
            {"t": "kit", "title": "Posztszöveg decemberre",
             "post": "Kutyát karácsonyra? 🎁 Csak ha az egész család készen áll – hiszen 10–15 évre szól. Mielőtt becsomagolnád, tegyétek fel együtt a legfontosabb kérdéseket: ki sétáltat, mennyibe kerül, melyik fajta illik hozzátok. Ebben segít a Pacsi ingyenes kvíze: https://pacsit.hu",
             "img": "hero/W09.jpg", "alt": "Kiskutya ül egy becsomagolt ajándék mellett.", "imghref": "app:partnerkep"},
            {"t": "text", "kicker": "2027", "title": "Mire készülünk?", "content": "2027", "paras": [
                "Jövőre is folytatjuk a heti leveleket, és szeretnénk még több partnert bemutatni. Ha van ötletetek közös tartalomra (fajtanap, örökbefogadási hét, kutyás rendezvény), írjátok meg – szívesen tervezünk együtt.",
            ]},
            {"t": "text", "kicker": "Köszönjük", "tone": "peach", "content": "koszonjuk", "paras": [
                "Köszönjük, hogy idén velünk voltatok. Boldog ünnepeket kívánunk nektek és minden kutyának, akiért dolgoztok!",
            ]},
            {"t": "sign"},
        ],
    },
]

# ---------------------------------------------------------------------------------------------------
# Partnermegkeresés – EGYEDI, személyes levelek (NEM Mailchimp!). A kapcsolati adatbázis kategóriáihoz.
# Helyőrzők: {nev} {fajta} {fajta_link} {varos} {alairas} {feliratkozas} {pitch} {site}
# A CMS „Kapcsolatok” füle ezekből személyre szabott levelet készít (másolás / levelezőben megnyitás).
# ---------------------------------------------------------------------------------------------------
_INTRO = ("A Pacsi (https://pacsit.hu) egy ingyenes, magyar kutyafajta-választó: 124 fajta, szűrők (lakás, gyerek, mozgás, ugatás…) "
          "és egy 10 kérdéses Párkereső kvíz segít a leendő gazdiknak, hogy az életmódjukhoz illő fajtát válasszanak. "
          "Szeptember végén indult, regisztráció és reklám nélkül.")
_OPTOUT = "Ha nem szeretnétek több levelet tőlünk, elég egy rövid válasz, és nem keresünk többet."

OUTREACH = {
    "kinologia": {
        "label": "Fajtaklubok, kinológiai szervezetek",
        "subject": "{fajta_vagy_nev} a Pacsiban – kérnénk a szakmai véleményeteket",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok. " + _INTRO + "\n\n{fajta_mondat}\n\nKét dologban kérnénk a segítségeteket:\n"
                "1. Nézzétek át a fajta kártyáját, és írjátok meg, ha valamit pontosítanátok. A jellemzőket és a leírásokat forrásokból, AI-segítséggel állítottuk össze – a fajta szakértőinek véleménye sokat érne.\n"
                "2. Ha hasznosnak tartjátok, ajánljátok a tagjaitoknak és az érdeklődő leendő gazdiknak.\n\n"
                "Cserébe szívesen bemutatjuk a klubot a heti Pacsi-levélben és a közösségi oldalainkon. Ha kéritek, csütörtökönként nektek is elküldjük a levelet: {feliratkozas}\n\n"
                "Köszönöm, hogy elolvastátok!\n{alairas}\n\n" + _OPTOUT,
    },
    "tenyesztok": {
        "label": "Tenyésztők",
        "subject": "{fajta_vagy_nev} a Pacsiban – pontos a kártyája?",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok. " + _INTRO + "\n\n{fajta_mondat}\n\n"
                "Tenyésztőként a fajtát ti ismeritek a legjobban. Ha valami nem pontos (jellemzők, egészségügyi szűrések, kinek ajánlott), nagyon örülnénk egy rövid visszajelzésnek. "
                "A Pacsi a felelős választást támogatja: a kártyákon a fajtára jellemző egészségügyi kockázatok és szűrések is szerepelnek.\n\n"
                "Ha érdekel, csütörtökönként elküldjük a heti Pacsi-levelet is: {feliratkozas}\n\n{alairas}\n\n" + _OPTOUT.replace("szeretnétek", "szeretnél"),
    },
    "menhelyek": {
        "label": "Menhelyek, állatvédők",
        "subject": "Ingyenes eszköz, hogy az örökbefogadók jól válasszanak",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok. " + _INTRO + "\n\n"
                "A Pacsi fajtákról szól, de a legfontosabb kérdést minden leendő gazdinak felteszi: milyen kutya illik az életedhez (energia, méret, ugatás, gyerekek, lakás)? "
                "Úgy gondoljuk, ez az örökbefogadásnál is segíthet: aki tudja, mit keres, jobban választ – és ritkábban viszi vissza a kutyát.\n\n"
                "November 19-én a heti levelünk az örökbefogadásról szól. Szívesen bemutatnánk a munkátokat vagy egy-egy gazdira váró kutyátokat – a ti fotóitokkal, a ti engedélyetekkel.\n\n"
                "Ha kéritek, csütörtökönként nektek is elküldjük a Pacsi-levelet: {feliratkozas}\n\nKöszönjük, amit a kutyákért tesztek!\n{alairas}\n\n" + _OPTOUT,
    },
    "kutyaiskolak": {
        "label": "Kutyaiskolák, trénerek",
        "subject": "Leendő gazdiknak – ingyenes eszköz, amit ajánlhattok",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok. " + _INTRO + "\n\n"
                "Trénerként biztosan sokszor találkoztok olyan gazdikkal, akiknél a fajta és az életmód nem illik össze. A Pacsi ezt szeretné megelőzni: már a választás előtt megmutatja, mennyi mozgás, tanítás és figyelem kell egy-egy fajtának.\n\n"
                "Ha hasznosnak tartjátok, ajánljátok a kölyökiskolás vagy érdeklődő gazdiknak. Kérésre szívesen készítünk nektek egy nyomtatható, QR-kódos plakátot is.\n\n"
                "Csütörtökönként heti Pacsi-levelet is küldünk, ha érdekel: {feliratkozas}\n\n{alairas}\n\n" + _OPTOUT,
    },
    "allatorvosok": {
        "label": "Állatorvosok",
        "subject": "Mielőtt kutyát választanak – ingyenes eszköz a gazdiknak",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok. " + _INTRO + "\n\n"
                "Állatorvosként ti látjátok a legjobban, mi történik, ha a fajta nem illik a gazdihoz, vagy ha a gazdi nem tud a fajtára jellemző betegségekről. "
                "A Pacsi kártyáin minden fajtánál szerepelnek a gyakori egészségügyi kockázatok, a mozgásigény és az ápolás.\n\n"
                "Két kérésünk lenne: ha hasznosnak tartjátok, ajánljátok a leendő gazdiknak; és ha van rá egy kis időtök, jelezzétek, ha egy fajta egészségügyi leírását pontosítanátok. "
                "Kérésre nyomtatható, QR-kódos plakátot is küldünk a váróba.\n\n{alairas}\n\n" + _OPTOUT,
    },
    "szolgaltatasok": {
        "label": "Kozmetikák, panziók, napközik, boltok",
        "subject": "Egy ingyenes eszköz a leendő gazdiknak",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok. " + _INTRO + "\n\n"
                "Hozzátok sok kutyás és leendő kutyás megfordul – ha hasznosnak tartjátok, ajánljátok nekik a Pacsit, vagy osszátok meg a közösségi oldalatokon. "
                "Kérésre nyomtatható, QR-kódos plakátot is küldünk.\n\n"
                "Csütörtökönként heti Pacsi-levelet is küldünk, ha érdekel: {feliratkozas}\n\n{alairas}\n\n" + _OPTOUT,
    },
    "media": {
        "label": "Média",
        "subject": "Magyar fejlesztés: 124 kutyafajta egy élő felhőben – ingyenes kutyafajta-választó",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok egy olyan témával, ami talán az olvasóitokat is érdekli.\n\n" + _INTRO + "\n\n"
                "Röviden:\n"
                "• 124 népszerű fajta egy élő, animált felhőben – ami nem illik hozzád, kirepül, ami igen, előrejön;\n"
                "• a 9 magyar kutyafajta külön szűrővel;\n"
                "• Párkereső kvíz 6 gazditípussal (Kanapé-kapitány, Városi flâneur…);\n"
                "• regisztráció és sütik nélkül, telefonon appként is telepíthető;\n"
                "• a cél a felelős kutyaválasztás: a kártyákon a mozgásigény, a költségek és az egészségügyi kockázatok is szerepelnek.\n\n"
                "Képek, videók és háttéranyag: {pitch}\n\n"
                "Szívesen adunk interjút, képanyagot, és egy közös rovat is elképzelhető (például „A hét fajtája”).\n\n{alairas}\n\n" + _OPTOUT,
    },
    "cegek": {
        "label": "Cégek, márkák",
        "subject": "Partnerség a Pacsival – kutyafajta-választó a leendő gazdiknak",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok. " + _INTRO + "\n\n"
                "A Pacsi abban a pillanatban éri el az embereket, amikor még csak fontolgatják a kutyatartást – a döntés előtti szakaszban, amikor a legnyitottabbak a tanácsra. "
                "Összeállítottunk egy rövid partneri ajánlatot, személyre szabva: {pitch}\n\n"
                "Ha érdekesnek találjátok, szívesen egyeztetünk egy 20 perces hívásra.\n\n{alairas}\n\n" + _OPTOUT,
    },
    "kozossegek": {
        "label": "Közösségek, oktatás",
        "subject": "Ajánlanátok a tagjaitoknak? – ingyenes kutyafajta-választó",
        "body": "Kedves {nev}!\n\nA Pacsi csapatából írok. " + _INTRO + "\n\n"
                "Ha hasznosnak tartjátok, ajánljátok a tagjaitoknak, vagy osszátok meg a csatornáitokon – szívesen küldünk hozzá kész posztszöveget és képet is.\n\n"
                "Csütörtökönként heti Pacsi-levelet is küldünk, ha érdekel: {feliratkozas}\n\n{alairas}\n\n" + _OPTOUT,
    },
}
FOLLOWUP = {
    "subject": "Re: {targy}",
    "body": "Kedves {nev}!\n\nCsak finoman rákérdeznék az előző levelemre – tudom, sok levél jön. Ha most nem aktuális, semmi gond, egy rövid „nem” is segít, hogy ne zavarjunk többet.\n\n{alairas}",
}
# Kapcsolati állapotok (CMS) – a sorrend a folyamat
CONTACT_STATUSES = {
    "uj": "Új",
    "megkeresve": "Megkeresve",
    "emlekeztetve": "Emlékeztetve",
    "valaszolt": "Válaszolt",
    "partner": "Partner",
    "feliratkozna": "Kéri a hírlevelet",
    "mailchimpben": "Mailchimpben",
    "nem": "Nem kér",
    "hibas": "Hibás cím",
}

# ---- útmutató az E-mail fülhöz ----
GUIDE = [
    {"title": "Miért két lista?", "steps": [
        "A **Kapcsolatok** a saját partneradatbázisunk: nyilvános oldalakon közzétett szervezeti címek, forrással. Innen csak **egyedi, személyes** levél megy (másolás vagy levelezőben megnyitás), tömeges hírlevél nem.",
        "A **Mailchimp-közönségbe** csak az kerül, aki feliratkozott (dupla megerősítéssel), vagy írásban kérte. A Mailchimp szabályzata tiltja a nyilvános oldalakról gyűjtött, vásárolt vagy „partner” listákat – ilyen feltöltésért felfüggesztik a fiókot.",
        "Magánszemélynek (pl. tenyésztő saját címe) reklámcélú levél csak előzetes, kifejezett hozzájárulással küldhető (Grt. 6. §). Ezeket a CMS „magánszemély” jelzéssel mutatja – velük óvatosan, személyesen, vagy a fajtaklubon keresztül vedd fel a kapcsolatot.",
    ]},
    {"title": "Mailchimp beállítása (egyszer)", "steps": [
        "Az API-kulcsot tedd a repó gyökerébe, a **Mailchimp_API.txt** fájlba (csak a kulcs; a fájl nem kerül verziókezelésbe).",
        "Töltsd ki a **marketing/email/config.json** üres mezőit: feladó e-mail, cégnév, postacím, közösségi profilok.",
        "Feladó-domain hitelesítése: a Mailchimpben *Website → Domains → Authenticate*. A kapott CNAME (DKIM) és TXT (DMARC) rekordokat a Rackhost DNS-ében kell felvenni – enélkül a Gmail és a Yahoo spambe teheti a leveleket.",
        "Futtasd: `python marketing/tools/mailchimp.py ping`, majd `python marketing/tools/mailchimp.py setup` – létrejön a „Pacsi – heti kutyás levél” közönség a mezőkkel és érdeklődési csoportokkal.",
        "Az ingyenes csomag korlátai: 250 kontakt, havi 500 küldés, nincs ütemezés. Heti levélhez kb. 120 feliratkozó fölött fizetős csomag kell.",
    ]},
    {"title": "Levelek a Mailchimpbe (piszkozatként)", "steps": [
        "A CMS-ben nézd át a levelet, és nyomd meg a **Jóváhagyom** gombot (vagy írj megjegyzést).",
        "Szólj Claude-nak, vagy futtasd: `python marketing/tools/mailchimp.py push L1 W01 …` – a képek feltöltődnek a Mailchimp tárhelyére (max. 1200×1200 px), és létrejön a kampány **piszkozatként**.",
        "A Mailchimpben küldj magadnak tesztlevelet (*Send test*), nézd meg telefonon is, aztán küldd ki kézzel.",
        "Később automatikus kiküldés: a config.json `mailchimp.mode` értéke `schedule` (fizetős csomag: a Mailchimp maga küld az időpontban), vagy `send-due` (ingyenes csomagon egy időzítő küldi ki a lejárt, jóváhagyott leveleket).",
    ]},
    {"title": "Üdvözlő sorozat (Customer Journey)", "steps": [
        "A `mailchimp.py templates` parancs feltölti a három üdvözlő levelet sablonként („Pacsi – Üdvözlő 1/3” …).",
        "Mailchimp: *Automations → Customer Journeys → Create* → indító esemény: *Signs up* (feliratkozik) a Pacsi közönségbe.",
        "Lépések: 1. levél azonnal, várakozás 3 nap, 2. levél, várakozás 4 nap, 3. levél – mindegyikhez a megfelelő sablon.",
        "Az ingyenes csomag csak egylépéses útvonalat enged: ott csak az 1. levél megy automatikusan.",
    ]},
    {"title": "Partnerek felvétele a listára", "steps": [
        "Ha egy partner válaszában kéri a hírlevelet, a Kapcsolatok fülön állítsd „Kéri a hírlevelet” állapotra.",
        "A `mailchimp.py import` a „Kéri a hírlevelet” állapotú kapcsolatokat „pending” állapottal veszi fel: a Mailchimp megerősítő levelet küld nekik, és csak kattintás után kerülnek a listára. Címkék: partner + kategória.",
        "Aki nem kér levelet, annak állítsd be a „Nem kér” állapotot – így senki nem keresi újra.",
    ]},
]
