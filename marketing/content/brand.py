"""Pacsi – arculati csomag és szövegbank (a CMS „Arculat” füle, marketing 1.4.0).

Egy helyen minden, ami a következetes kommunikációhoz kell: bemutatkozó szövegek, bio-szövegek, hashtag-készletek,
hangnem, színek, betűk, logók és profilképek, fontos linkek, valamint az UTM-linképítő előbeállításai.

A szövegek nagy része a meglévő forrásokból jön (content.py, setup_plan.py, email_plan.py, email/config.json).
Itt csak összegyűjtjük őket, hogy ugyanabból a szövegből ne legyen két változat. Ha valamit át kell írni,
az eredeti helyén írd át, és futtasd a buildet.
"""
import collections
import importlib.util
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
MK = HERE.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


C = _load("content")
SP = _load("setup_plan")
EP = _load("email_plan")
CFG = json.loads((MK / "email" / "config.json").read_text(encoding="utf-8"))

# A CMS claude.ai-s címe: a naptárexport (.ics) eseményei ide mutatnak vissza (#<tartalom-id>).
CMS_URL = "https://claude.ai/artifact/2LWG8yFub1TArPhBuWERmH"


def _top_tags(platform, n=12):
    """a posztszövegekben ténylegesen használt hashtagek, gyakoriság szerint"""
    cnt = collections.Counter()
    for it in C.ITEMS:
        c = (it.get("copy") or {}).get(platform)
        if c:
            cnt.update(t.lower() for t in re.findall(r"#[^\s#]+", c.get("tags", "") + " " + c.get("text", "")))
    return " ".join(t for t, _ in cnt.most_common(n))


_co, _se = CFG["company"], CFG["sender"]
_legal = f"{_co['legal_name']} · {_co['zip']} {_co['city']}, {_co['address1']}"

BRAND = {
    "name": "Pacsi",
    "cmsUrl": CMS_URL,
    "texts": [
        {"id": "tagline", "label": "Szlogen", "text": "Találd meg a hozzád illő kutyát!", "where": "Minden bio első mondata, hirdetések címe."},
        {"id": "short", "label": "Rövid bemutatkozás", "text": SP.FB_INTRO, "limit": 101, "where": "Facebook-bio, rövid leírások, sajtóanyag első mondata."},
        {"id": "ig_bio", "label": "Instagram-bio", "text": SP.BIO_IG, "limit": 150, "where": "Instagram profil → Bemutatkozás."},
        {"id": "tt_bio", "label": "TikTok-bio", "text": SP.BIO_TT, "limit": 80, "where": "TikTok profil → Bemutatkozás."},
        {"id": "li_tagline", "label": "LinkedIn-szlogen", "text": SP.LI_TAGLINE, "limit": 120, "where": "LinkedIn-oldal szlogenje."},
        {"id": "partner_intro", "label": "Bemutatkozás partnereknek", "text": EP._INTRO, "where": "Megkereső levelek, együttműködési ajánlatok eleje."},
        {"id": "about", "label": "Hosszú bemutatkozás", "text": SP.FB_ABOUT, "where": "Facebook Névjegy, sajtóanyag, pályázatok."},
        {"id": "about_li", "label": "Bemutatkozás (szakmai)", "text": SP.LI_ABOUT, "limit": 2000, "where": "LinkedIn Áttekintés, B2B anyagok."},
        {"id": "yt", "label": "YouTube-csatorna leírása", "text": SP.YT_DESC, "limit": 1000, "where": "YouTube Studio → Alapinformációk."},
        {"id": "optout", "label": "Leiratkozási mondat (megkeresésekhez)", "text": EP._OPTOUT, "where": "Minden egyedi megkereső levél végére."},
        {"id": "signature", "label": "Aláírás", "text": "\n".join(x for x in [_se.get("signature_name") or "A Pacsi csapata", "Pacsi · https://pacsit.hu", _se["from_email"]] if x),
         "where": "Levelek, válaszok alja."},
        {"id": "legal", "label": "Jogi lábléc", "text": _legal, "where": "Hírlevél lábléce, impresszum (a postacím kötelező)."},
    ],
    "hashtags": [
        {"label": "Alap (Instagram, Facebook)", "tags": C.H_CORE, "note": "Instagramon 8–15 hashtag a jó, legfeljebb 30."},
        {"label": "TikTok", "tags": C.H_TT, "note": "3–5 hashtag elég."},
        {"label": "Leggyakoribb: Instagram", "tags": _top_tags("instagram"), "note": "A kész posztszövegekből számolva."},
        {"label": "Leggyakoribb: LinkedIn", "tags": _top_tags("linkedin", 8), "note": "Szakmai hangnem, 3–5 hashtag posztonként."},
    ],
    "voice": {
        "summary": "Tegező, meleg, humoros, de nem infantilis. Rövid mondatok. A komoly témákban (egészség, felelősség, örökbefogadás) egyenes és kedves.",
        "do": [
            "Tegezz, és beszélj úgy, mint egy kutyás barát.",
            "Rövid mondatok, egy gondolat egy mondatban.",
            "„Illik hozzád” – a döntés mindig a gazdié.",
            "Tényt csak az app fajtaadataiból vagy elfogadott állatorvosi tanácsból írj.",
            "Minden poszt egy cselekvéssel záruljon: próbáld ki, link a bióban, írd meg kommentben.",
            "Instagramon és TikTokon a link nem kattintható: „link a bióban”.",
        ],
        "dont": [
            "Ne ígérj „tökéletes kutyát”, és ne írd, hogy „ez a te kutyád”.",
            "Ne állíts olyat, ami a fajtakártyán nincs benne.",
            "Ne legyen infantilis vagy reklámszagú.",
            "LinkedInen ne tedd a linket a posztba: az első kommentbe kerül.",
        ],
    },
    "colors": [
        {"name": "Korall", "hex": "#FF6B3D", "use": "Fő kiemelőszín, a mancs a logóban."},
        {"name": "Korall (kitöltés)", "hex": "#EE5A2C", "use": "Gombok, kitöltött felületek (fehér szöveggel)."},
        {"name": "Mély korall", "hex": "#C8431C", "use": "Szöveg világos háttéren, hover."},
        {"name": "Napsárga", "hex": "#FFC845", "use": "Másodlagos kiemelés, matricák."},
        {"name": "Kékeszöld", "hex": "#17756E", "use": "Hírlevél, információ, „kész” állapot."},
        {"name": "Levendula", "hex": "#5B5BD6", "use": "Üdvözlő sorozat, ötletek."},
        {"name": "Rózsa", "hex": "#E86A92", "use": "Díszítés, csillanás."},
        {"name": "Krém háttér", "hex": "#FBF6EE", "use": "Alapháttér (képek, levelek, app)."},
        {"name": "Tinta", "hex": "#1E1B18", "use": "Szöveg."},
        {"name": "Tinta 2", "hex": "#6B625A", "use": "Másodlagos szöveg."},
    ],
    "fonts": [
        {"name": "Fraunces", "use": "Címek, logó, nagy számok (SOFT 100, optikai méret).", "fallback": "Georgia, serif",
         "link": "https://fonts.google.com/specimen/Fraunces"},
        {"name": "Manrope", "use": "Szöveg, gombok, feliratok (400–800).", "fallback": "Segoe UI, Arial, sans-serif",
         "link": "https://fonts.google.com/specimen/Manrope"},
    ],
    "logos": [it["id"] for it in C.ITEMS if it.get("kind") == "profil"],
    "links": [
        {"label": "Weboldal / app", "url": C.SITE},
        {"label": "Hírlevél-feliratkozás", "url": CFG["links"].get("signup", "")},
        {"label": "Partneri prezentáció (nyilvános)", "url": CFG["links"].get("pitch", "")},
        {"label": "Statisztika (Umami)", "url": "https://stat.pacsit.hu"},
        {"label": "Marketing CMS (privát)", "url": CMS_URL},
        *({"label": f"{C.PLATFORMS[p]['name']}-profil", "url": u} for p, u in CFG["social"].items() if not p.startswith("_") and p in C.PLATFORMS),
    ],
    "shortLinks": [{"platform": p, "url": C.link(p), "post": C.link(p, "<tartalom-id>")} for p in C.SHORT],
    "utm": {
        "url": C.SITE,
        "presets": [
            {"id": "facebook", "label": "Facebook-poszt", "source": "facebook", "medium": "social", "campaign": "pacsi", "content": "", "short": "f"},
            {"id": "instagram", "label": "Instagram (bio, story)", "source": "instagram", "medium": "social", "campaign": "pacsi", "content": "bio", "short": "i"},
            {"id": "tiktok", "label": "TikTok (bio)", "source": "tiktok", "medium": "social", "campaign": "pacsi", "content": "bio", "short": "t"},
            {"id": "linkedin", "label": "LinkedIn (első komment)", "source": "linkedin", "medium": "social", "campaign": "pacsi", "content": "", "short": "l"},
            {"id": "youtube", "label": "YouTube-leírás", "source": "youtube", "medium": "social", "campaign": "pacsi", "content": "", "short": "y"},
            {"id": "level", "label": "Hírlevél (Pacsi-levél)", "source": CFG["utm"]["source"], "medium": CFG["utm"]["medium"], "campaign": "W01", "content": "cta"},
            {"id": "partner", "label": "Partner (saját link)", "source": "partner", "medium": "referral", "campaign": "menhelyek", "content": "PK0001"},
            {"id": "megkereses", "label": "Megkereső levél", "source": "partner", "medium": "email", "campaign": "megkereses", "content": "PK0001"},
            {"id": "hirdetes", "label": "Hirdetés (Meta)", "source": "meta", "medium": "paid", "campaign": "indulas", "content": "hirdetes_a"},
        ],
        "rules": [
            "Kisbetű, ékezet és szóköz nélkül (kötőjel mehet): utm_campaign=indulas, nem „Indulás”.",
            "utm_source = honnan jön (platform vagy partner), utm_medium = milyen csatorna (social, email, paid, referral).",
            "utm_content = a tartalom azonosítója (pl. v1, k_launch, W03, PK0042) – így a statisztika posztra pontosan párosítható.",
            "Közösségi posztban a rövid link a szabály: pacsit.hu/f/<tartalom-id> (a szerver alakítja UTM-re).",
        ],
    },
}
