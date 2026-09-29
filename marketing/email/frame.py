"""Pacsi eDM – a levélkeret és a tartalomblokkok (HTML e-mail).

Egy levél = keret (fejléc, lábléc, közös arculat) + egyedi blokkok. A blokkok a
marketing/content/email_plan.py-ban vannak leírva; ez a modul rajzolja meg őket.

Levél-HTML szabályai (ügyfélprogram-biztos):
  - 600 px széles, táblás elrendezés, inline stílusok (Outlook, Gmail, Apple Mail, mobilok);
  - minden kép legfeljebb 1200×1200 px (Mailchimp), 2× felbontásban, alt szöveggel;
  - betűk: Fraunces / Manrope a Google Fontsból, ahol nem tölthető: Georgia / Segoe UI / Arial;
  - sötét mód: Apple Mail, iOS, Outlook.com (a Gmail maga színez át);
  - a Gmail 102 kB fölött levágja a levelet, ezért a build figyelmeztet 90 kB fölött.

Linkek a tartalomban (a render feloldja):
  app:<tartalom>#<hash>   → https://pacsit.hu/?utm_source=pacsi-level&utm_medium=email&utm_campaign=<levél>&utm_content=<tartalom>#<hash>
  mc:archive | mc:forward | mc:subscribe | mc:unsub | mc:profile   → Mailchimp-mezőkód
  share:facebook | share:whatsapp | share:email                    → megosztó link
  social:instagram | social:tiktok | social:facebook | social:linkedin   → a config.json profilcíme
  pitch: → partneri prezentáció · privacy: → adatkezelési tájékoztató
Szövegben: **félkövér**, *dőlt*, [szöveg](link).
"""
import html
import json
import pathlib
import re
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
BREEDS = {b["id"]: b for b in json.loads((ROOT / "data" / "fajtak.json").read_text(encoding="utf-8"))["breeds"]}

# ---- arculat (az app design tokenjei) ----
C = {
    "bg": "#FBF6EE", "card": "#FFFDF9", "soft": "#F5EDE1", "line": "#EDE4D8",
    "ink": "#1E1B18", "ink2": "#6B625A", "ink3": "#9A9088",
    "coral": "#EE5A2C", "coral2": "#FF6B3D", "deep": "#C8431C", "sun": "#FFC845",
    "peach": "#FFF1E8", "lav": "#F1EDFF", "mint": "#E6F6EE", "sky": "#E7F3FA", "sand": "#FBF1DF",
    "teal": "#17756E", "violet": "#5B5BD6",
}
FD = "'Fraunces',Georgia,'Times New Roman',serif"
FU = "'Manrope','Segoe UI',Helvetica,Arial,sans-serif"
TRAITS = {"E": "Energia", "Gy": "Gyerekbarát", "I": "Tanulékony", "U": "Ugatás", "H": "Szőrhullás",
          "A": "Ápolásigény", "L": "Lakásba való", "O": "Őrzőösztön", "K": "Kezdőknek"}
TONES = {"peach": C["peach"], "lav": C["lav"], "mint": C["mint"], "sky": C["sky"], "sand": C["sand"], "soft": C["soft"]}

DARK_RULES = """
.bgo{background:#14121A!important}
.bgc{background:#1D1A25!important}
.bgs{background:#26222F!important}
.ink{color:#F4EFE8!important}
.ink2{color:#C4BBB2!important}
.lnk{color:#FF8A5E!important}
.bd{border-color:#39333F!important}
.lm{display:none!important;max-height:0!important;overflow:hidden!important}
.dm{display:block!important;max-height:none!important;overflow:visible!important}
"""

HEAD_CSS = """
:root{color-scheme:light dark;supported-color-schemes:light dark}
body{margin:0!important;padding:0!important;width:100%!important;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}
table{border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt}
img{border:0;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic}
a{text-decoration:none}
a[x-apple-data-detectors]{color:inherit!important;text-decoration:none!important}
u+#body a{color:inherit;text-decoration:none}
@media (max-width:620px){
.w{width:100%!important;max-width:100%!important}
.px{padding-left:22px!important;padding-right:22px!important}
.col{display:block!important;width:100%!important;max-width:100%!important}
.cp{padding:0 0 18px 0!important}
.ctr{text-align:center!important}
.ctr table{margin:0 auto!important}
.h1{font-size:30px!important;line-height:34px!important}
.h2{font-size:24px!important;line-height:28px!important}
.fw{width:100%!important;height:auto!important}
.th{width:100%!important;max-width:100%!important;display:block!important;padding:0 0 14px 0!important}
.hm{display:none!important;max-height:0!important;overflow:hidden!important}
}
@media (prefers-color-scheme:dark){""" + DARK_RULES + """}
[data-ogsc] .ink{color:#F4EFE8!important}
[data-ogsc] .ink2{color:#C4BBB2!important}
[data-ogsc] .lnk{color:#FF8A5E!important}
[data-ogsb] .bgo{background:#14121A!important}
[data-ogsb] .bgc{background:#1D1A25!important}
[data-ogsb] .bgs{background:#26222F!important}
"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


class Ctx:
    """Egy levél renderelésének környezete.
    mode: 'mc' (Mailchimp: mezőkódok maradnak) vagy 'preview' (CMS/helyi előnézet: mintaértékek)
    img:  képnév → URL (pl. 'hero/L1.jpg')"""

    def __init__(self, email, cfg, img, mode="mc", version="", build=""):
        self.e, self.cfg, self.img, self.mode = email, cfg, img, mode
        self.version, self.build = version, build
        self.site = cfg["links"]["site"]

    def app(self, content, hsh=""):
        q = urllib.parse.urlencode({"utm_source": self.cfg["utm"]["source"], "utm_medium": self.cfg["utm"]["medium"],
                                    "utm_campaign": self.e["id"].lower(), "utm_content": content})
        return f"{self.site}?{q}" + (f"#{hsh}" if hsh else "")

    def href(self, tok, content="link"):
        if not tok:
            return ""
        if tok.startswith(("http://", "https://", "mailto:")):
            return tok
        kind, _, rest = tok.partition(":")
        if kind == "app":
            c, _, h = rest.partition("#")
            return self.app(c or content, h)
        if kind == "mc" and rest == "subscribe" and self.cfg["links"].get("signup"):   # a saját feliratkozó oldal
            return self.cfg["links"]["signup"] + f"?utm_source=pacsi-level&utm_medium=email&utm_campaign={self.e['id'].lower()}&utm_content={content}"
        if kind == "mc":
            return {"archive": "*|ARCHIVE|*", "forward": "*|FORWARD|*", "subscribe": "*|LIST:SUBSCRIBE|*",
                    "unsub": "*|UNSUB|*", "profile": "*|UPDATE_PROFILE|*"}[rest]
        if kind == "share":
            url = f"{self.site}?utm_source={rest}-share&utm_medium=referral&utm_campaign={self.e['id'].lower()}"
            txt = "Nézd meg a Pacsit – ingyenes kutyafajta-választó, 124 fajtával. Szerintem neked is tetszeni fog:"
            if rest == "facebook":
                return "https://www.facebook.com/sharer/sharer.php?u=" + urllib.parse.quote(url, safe="")
            if rest == "whatsapp":
                return "https://wa.me/?text=" + urllib.parse.quote(f"{txt} {url}", safe="")
            if rest == "email":
                return "mailto:?subject=" + urllib.parse.quote("Melyik kutya illik hozzád? 🐾") + "&body=" + urllib.parse.quote(f"{txt}\n{url}")
        if kind == "social":
            return self.cfg["social"].get(rest, "")
        if kind == "pitch":
            return self.cfg["links"]["pitch"] + (f"#p-{rest}" if rest else "")
        if kind == "privacy":
            return self.cfg["links"]["privacy"]
        raise ValueError(f"ismeretlen link: {tok}")


# ---------------------------------------------------------------- szöveg
INLINE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|\*(.+?)\*")


def rich(ctx, s, content="szoveg", color=None):
    """**félkövér**, *dőlt*, [szöveg](link) → HTML (a többi karakter escape-elve)."""
    out, pos = [], 0
    s = str(s)
    for m in INLINE.finditer(s):
        out.append(esc(s[pos:m.start()]))
        if m.group(1):
            out.append(f'<a class="lnk" href="{esc(ctx.href(m.group(2), content))}" style="color:{color or C["coral"]};font-weight:800;text-decoration:underline">{esc(m.group(1))}</a>')
        elif m.group(3):
            out.append(f'<strong style="font-weight:800">{rich(ctx, m.group(3), content)}</strong>')
        else:
            out.append(f"<em>{rich(ctx, m.group(4), content)}</em>")
        pos = m.end()
    out.append(esc(s[pos:]))
    return "".join(out).replace("\n", "<br>")


def plain(s):
    """rich-szöveg → sima szöveg (a link címe zárójelben marad a render_text-ben)"""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", str(s))
    return re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"\1", s)


# ---------------------------------------------------------------- építőelemek
def P(ctx, s, content="szoveg", size=16, lh=25, color=None, mt=0, align="left", weight=500):
    return (f'<p class="{"ink2" if color == C["ink2"] else "ink"}" style="margin:{mt}px 0 0;font-family:{FU};font-size:{size}px;'
            f'line-height:{lh}px;font-weight:{weight};color:{color or C["ink"]};text-align:{align}">{rich(ctx, s, content)}</p>')


def kicker(s, color=None, mt=0):
    return (f'<p style="margin:{mt}px 0 0;font-family:{FU};font-size:11px;line-height:14px;font-weight:800;letter-spacing:2px;'
            f'text-transform:uppercase;color:{color or C["coral"]}">{esc(s)}</p>')


def H(s, lvl=2, mt=8, align="left"):
    size, lh, cls = (32, 36, "h1") if lvl == 1 else (24, 29, "h2") if lvl == 2 else (19, 24, "h3")
    return (f'<h{lvl} class="ink {cls}" style="margin:{mt}px 0 0;font-family:{FD};font-size:{size}px;line-height:{lh}px;'
            f'font-weight:800;letter-spacing:-0.5px;color:{C["ink"]};text-align:{align}">{s}</h{lvl}>')


def button(ctx, label, tok, content="cta", mt=22, align="left", ghost=False):
    href = esc(ctx.href(tok, content))
    if ghost:
        cell = f'<td align="center" style="border-radius:999px">'
        a_style = (f"display:inline-block;padding:11px 22px;border:2px solid {C['coral']};border-radius:999px;font-family:{FU};font-size:15px;"
                   f"line-height:20px;font-weight:800;color:{C['coral']};text-decoration:none;white-space:nowrap")
    else:
        cell = f'<td align="center" bgcolor="{C["coral"]}" style="border-radius:999px;background:{C["coral"]}">'
        a_style = (f"display:inline-block;padding:14px 28px;border-radius:999px;font-family:{FU};font-size:16px;line-height:20px;"
                   f"font-weight:800;color:#FFFFFF;text-decoration:none;white-space:nowrap")
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="{align}" style="margin-top:{mt}px;border-collapse:separate">'
            f'<tr>{cell}<a class="{"lnk" if ghost else ""}" href="{href}" target="_blank" style="{a_style}">{esc(label)}</a></td></tr></table>'
            f'<div style="clear:both;font-size:0;line-height:0">&nbsp;</div>')


def img(ctx, name, alt, w, h=None, radius=0, cls="fw", href=None, content="kep", extra=""):
    src = esc(ctx.img(name))
    hh = f' height="{h}"' if h else ""
    tag = (f'<img src="{src}" width="{w}"{hh} alt="{esc(alt)}" class="{cls}" style="display:block;width:{w}px;max-width:100%;'
           f'{"height:auto;" if not h else f"height:{h}px;"}border:0;border-radius:{radius}px;{extra}">')
    return f'<a href="{esc(ctx.href(href, content))}" target="_blank">{tag}</a>' if href else tag


def dots(v, on=None):
    v = max(0, min(5, int(v)))
    return (f'<span style="color:{on or C["coral2"]};letter-spacing:3px;font-size:13px">{"●" * v}</span>'
            f'<span style="color:#E6DACB;letter-spacing:3px;font-size:13px">{"●" * (5 - v)}</span>')


def row(inner, pad="0 36px", mt=28, cls="px"):
    return f'<tr><td class="{cls}" style="padding:{mt}px {pad.split()[1]} 0">{inner}</td></tr>'


def box(inner, tone="peach", pad=22, radius=20, border=False):
    bd = f"border:1px solid {C['line']};" if border else ""
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td class="bgs bd" bgcolor="{TONES.get(tone, tone)}" style="background:{TONES.get(tone, tone)};border-radius:{radius}px;padding:{pad}px;{bd}">'
            f'{inner}</td></tr></table>')


# ---------------------------------------------------------------- blokkok
def b_hero(ctx, b):
    parts = []
    if b.get("img"):
        parts.append(f'<tr><td style="padding:0;line-height:0">{img(ctx, b["img"], b.get("alt", ""), 600, href=b.get("cta", {}).get("href"), content="hero-kep")}</td></tr>')
    t = ""
    if b.get("kicker"):
        t += kicker(b["kicker"])
    t += H(rich(ctx, b["title"]), 1, mt=10 if b.get("kicker") else 0)
    if b.get("lead"):
        t += P(ctx, b["lead"], "hero", size=17, lh=27, color=C["ink2"], mt=12)
    if b.get("cta"):
        t += button(ctx, b["cta"]["label"], b["cta"]["href"], "hero")
        if b["cta"].get("note"):
            t += P(ctx, b["cta"]["note"], "hero", size=13, lh=19, color=C["ink3"], mt=10)
    parts.append(f'<tr><td class="px" style="padding:28px 36px 0">{t}</td></tr>')
    return "".join(parts)


def b_intro(ctx, b):
    greet = ("*|IF:FNAME|*Kedves *|FNAME|*!*|ELSE:|*Kedves Partnerünk!*|END:IF|*" if b.get("partner")
             else "*|IF:FNAME|*Szia *|FNAME|*!*|ELSE:|*Szia!*|END:IF|*")
    t = "" if b.get("nogreet") else f'<p class="ink" style="margin:0;font-family:{FU};font-size:17px;line-height:26px;font-weight:800;color:{C["ink"]}">{greet}</p>'
    for i, p in enumerate(b["paras"]):
        t += P(ctx, p, "bevezeto", mt=(12 if (i or t) else 0))
    return row(t)


def b_text(ctx, b):
    t = kicker(b["kicker"]) if b.get("kicker") else ""
    if b.get("title"):
        t += H(rich(ctx, b["title"]), 2, mt=8 if t else 0)
    for i, p in enumerate(b.get("paras", [])):
        t += P(ctx, p, b.get("content", "szoveg"), mt=12 if (i or t) else 0)
    if b.get("list"):
        items = "".join(
            f'<tr><td valign="top" style="padding:10px 12px 0 0;width:26px;font-family:{FU};font-size:16px;line-height:24px;font-weight:800;color:{C["coral"]}">{esc(b.get("marker", "●") if not b.get("numbered") else f"{i + 1}.")}</td>'
            f'<td class="ink" style="padding:10px 0 0;font-family:{FU};font-size:16px;line-height:24px;color:{C["ink"]}">{rich(ctx, it, b.get("content", "lista"))}</td></tr>'
            for i, it in enumerate(b["list"]))
        t += f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:4px">{items}</table>'
    if b.get("after"):
        t += P(ctx, b["after"], b.get("content", "szoveg"), mt=14)
    if b.get("cta"):
        t += button(ctx, b["cta"]["label"], b["cta"]["href"], b.get("content", "szoveg"), ghost=b["cta"].get("ghost", False))
    return row(box(t, b["tone"]) if b.get("tone") else t)


def breed_meta(bid):
    b = BREEDS[bid]
    return b


def b_breed(ctx, b):
    br = BREEDS[b["id"]]
    content = b.get("content", "het-fajtaja")
    link = f"app:{content}#b={br['id']}"
    traits = b.get("traits") or ["E", "Gy", "L"]
    tr = "".join(
        f'<tr><td class="ink2" style="padding:5px 12px 0 0;font-family:{FU};font-size:13px;line-height:18px;font-weight:700;color:{C["ink2"]};white-space:nowrap">{esc(TRAITS[k])}</td>'
        f'<td style="padding:5px 0 0;font-size:13px;line-height:18px;white-space:nowrap">{dots(br["t"][k])}</td></tr>' for k in traits)
    who = b.get("who") or br["kinekIgen"][:2]
    why = b.get("text") or br["leiras"].split(". ")[0] + "."
    right = (kicker(b.get("kicker", "A hét fajtája"))
             + H(esc(br["nev"]), 2, mt=8)
             + f'<p style="margin:6px 0 0;font-family:{FD};font-style:italic;font-size:16px;line-height:22px;font-weight:700;color:{C["coral"]}">{esc(b.get("tagline") or br["tagline"])}</p>'
             + P(ctx, why, content, size=15, lh=23, mt=10)
             + f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:10px">{tr}</table>'
             + P(ctx, "**Kinek ajánlott?** " + " · ".join(who), content, size=14, lh=21, color=C["ink2"], mt=12)
             + button(ctx, b.get("cta", "Nyisd meg a kártyáját →"), link, content, mt=16))
    left = img(ctx, f"breed/{br['id']}.png", f"{br['nev']} – portré", 190, 190, href=link, content=content + "-kep", cls="")
    inner = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
             f'<td class="col cp ctr" width="206" valign="top" style="width:206px;padding:0 20px 0 0" align="center">{left}</td>'
             f'<td class="col" valign="top">{right}</td></tr></table>')
    if b.get("fact"):
        inner += (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:18px"><tr>'
                  f'<td class="bd" style="border-top:1px dashed #E3D3C0;padding-top:14px;font-family:{FU};font-size:14px;line-height:21px;color:{C["ink2"]}">'
                  f'<span class="ink2">🐾 <strong style="color:{C["ink"]}" class="ink">Érdekesség:</strong> {rich(ctx, b["fact"] if isinstance(b["fact"], str) else br["erdekesseg"], content)}</span></td></tr></table>')
    return row(box(inner, b.get("tone", "peach"), pad=22))


def b_breeds(ctx, b):
    """Fajtarács: 3 oszlop, kerek portré + név + egy sor; minden elem a kártyájára visz."""
    content = b.get("content", "fajtak")
    cells = []
    for bid in b["ids"]:
        br = BREEDS[bid]
        note = (b.get("notes") or {}).get(bid) or br["tagline"]
        link = f"app:{content}#b={bid}"
        cells.append(
            f'<td width="33%" valign="top" align="center" style="width:33%;padding:0 4px 18px">'
            f'{img(ctx, f"breed/{bid}.png", br["nev"], 120, href=link, content=content, cls="", extra="margin:0 auto;")}'
            f'<p class="ink" style="margin:10px 0 0;font-family:{FU};font-size:15px;line-height:19px;font-weight:800;color:{C["ink"]};text-align:center">'
            f'<a class="ink" href="{esc(ctx.href(link, content))}" style="color:{C["ink"]};text-decoration:none">{esc(br["nev"])}</a></p>'
            f'<p class="ink2" style="margin:4px 0 0;font-family:{FU};font-size:13px;line-height:18px;color:{C["ink2"]};text-align:center">{rich(ctx, note, content)}</p></td>')
    rows = "".join("<tr>" + "".join(cells[i:i + 3]) + ("<td></td>" * (3 - len(cells[i:i + 3]))) + "</tr>" for i in range(0, len(cells), 3))
    t = kicker(b["kicker"]) if b.get("kicker") else ""
    if b.get("title"):
        t += H(rich(ctx, b["title"]), 2, mt=8 if t else 0)
    if b.get("lead"):
        t += P(ctx, b["lead"], content, mt=10, color=C["ink2"])
    t += f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:22px">{rows}</table>'
    if b.get("cta"):
        t += button(ctx, b["cta"]["label"], b["cta"]["href"], content, mt=4, align="center")
    return row(t)


def b_fact(ctx, b):
    big = b.get("big", "")
    left = (f'<td class="col cp" width="120" valign="middle" align="center" style="width:120px;padding:0 18px 0 0">'
            f'<p style="margin:0;font-family:{FD};font-size:{b.get("bigsize", 52)}px;line-height:1;font-weight:800;color:{C["coral"]}">{esc(big)}</p></td>') if big else ""
    t = kicker(b.get("kicker", "Tudtad?"), color=C["violet"]) + H(rich(ctx, b["title"]), 3, mt=8) + P(ctx, b["text"], b.get("content", "tudtad"), size=15, lh=23, mt=8)
    if b.get("cta"):
        t += button(ctx, b["cta"]["label"], b["cta"]["href"], b.get("content", "tudtad"), mt=14, ghost=True)
    inner = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>{left}<td class="col" valign="middle">{t}</td></tr></table>'
    return row(box(inner, b.get("tone", "lav")))


def b_tip(ctx, b):
    items = "".join(
        f'<tr><td valign="top" style="padding:12px 12px 0 0;width:30px"><div style="width:24px;height:24px;border-radius:12px;background:{C["teal"]};'
        f'color:#FFFFFF;font-family:{FU};font-size:13px;line-height:24px;font-weight:800;text-align:center">{"✓" if not b.get("numbered") else i + 1}</div></td>'
        f'<td class="ink" style="padding:12px 0 0;font-family:{FU};font-size:15px;line-height:23px;color:{C["ink"]}">{rich(ctx, it, b.get("content", "tipp"))}</td></tr>'
        for i, it in enumerate(b["items"]))
    t = kicker(b.get("kicker", "Gazdi-tipp"), color=C["teal"]) + H(rich(ctx, b["title"]), 3, mt=8)
    if b.get("lead"):
        t += P(ctx, b["lead"], b.get("content", "tipp"), size=15, lh=23, mt=8, color=C["ink2"])
    t += f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:4px">{items}</table>'
    if b.get("after"):
        t += P(ctx, b["after"], b.get("content", "tipp"), size=14, lh=21, mt=14, color=C["ink2"])
    if b.get("cta"):
        t += button(ctx, b["cta"]["label"], b["cta"]["href"], b.get("content", "tipp"), mt=16, ghost=True)
    return row(box(t, b.get("tone", "mint")))


def b_quiz(ctx, b):
    content = b.get("content", "tippelj")
    opts = "".join(
        f'<tr><td style="padding:10px 0 0"><a href="{esc(ctx.href(o["href"], content))}" target="_blank" class="bd" '
        f'style="display:block;padding:13px 16px;border:2px solid #EADFD1;border-radius:14px;background:#FFFFFF;font-family:{FU};'
        f'font-size:15px;line-height:20px;font-weight:800;color:{C["ink"]};text-decoration:none">'
        f'<span style="color:{C["coral"]}">{"ABCD"[i]})</span>&nbsp; {esc(o["label"])}</a></td></tr>'
        for i, o in enumerate(b["options"]))
    t = (kicker(b.get("kicker", "Tippelj!"), color=C["deep"]) + H(rich(ctx, b["question"]), 3, mt=8)
         + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:4px">{opts}</table>')
    if b.get("note"):
        t += P(ctx, b["note"], content, size=13, lh=19, mt=12, color=C["ink2"])
    return row(box(t, b.get("tone", "sand")))


def b_answer(ctx, b):
    t = (kicker("A múlt heti fejtörő megfejtése", color=C["deep"])
         + P(ctx, b["text"], "megfejtes", size=15, lh=23, mt=8))
    return row(box(t, "soft", pad=18, radius=16))


def b_social(ctx, b):
    content = "kozossegi"
    cells = []
    for it in b["items"]:
        href = f"social:{it['platform']}" if ctx.cfg["social"].get(it["platform"]) else f"app:{content}"
        cells.append(
            f'<td width="33%" valign="top" style="width:33%;padding:0 4px">'
            f'{img(ctx, it["img"], it["title"], 172, radius=14, href=href, content=content, cls="", extra="margin:0 auto;")}'
            f'<p class="ink2" style="margin:8px 0 0;font-family:{FU};font-size:12px;line-height:16px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{C["coral"]}">{esc(it["label"])}</p>'
            f'<p class="ink" style="margin:3px 0 0;font-family:{FU};font-size:14px;line-height:19px;font-weight:700;color:{C["ink"]}">{esc(it["title"])}</p></td>')
    while len(cells) < 3:
        cells.append('<td width="33%"></td>')
    prof = [(p, n) for p, n in (("instagram", "Instagram"), ("tiktok", "TikTok"), ("facebook", "Facebook"), ("linkedin", "LinkedIn")) if ctx.cfg["social"].get(p)]
    links = " &nbsp;·&nbsp; ".join(f'<a class="lnk" href="{esc(ctx.href("social:" + p))}" style="color:{C["coral"]};font-weight:800;text-decoration:none">{n}</a>' for p, n in prof)
    t = (kicker(b.get("kicker", "A héten a közösségin")) + H(rich(ctx, b.get("title", "Nézd meg, ha még nem láttad")), 3, mt=8)
         + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:16px"><tr>{"".join(cells[:3])}</tr></table>')
    if b.get("text"):
        t += P(ctx, b["text"], content, size=14, lh=21, mt=14, color=C["ink2"])
    if links:
        t += P(ctx, "", content, size=14, lh=21, mt=10).replace("</p>", f"Kövess minket: {links}</p>")
    return row(t)


def b_share(ctx, b):
    content = "ajanlas"
    pills = [("share:facebook", "Facebook"), ("share:whatsapp", "WhatsApp"), ("share:email", "E-mail"), ("mc:forward", "Levél továbbküldése")]
    cells = "".join(
        f'<a href="{esc(ctx.href(tok, content))}" target="_blank" class="bd" style="display:inline-block;margin:8px 8px 0 0;padding:10px 16px;border-radius:999px;'
        f'background:#FFFFFF;border:1px solid #EADFD1;font-family:{FU};font-size:14px;line-height:18px;font-weight:800;color:{C["ink"]};text-decoration:none;white-space:nowrap">{lab}</a>'
        for tok, lab in pills)
    t = (kicker(b.get("kicker", "Ajánld tovább"), color=C["deep"]) + H(rich(ctx, b.get("title", "Ismersz valakit, aki kutyát szeretne?")), 3, mt=8)
         + P(ctx, b.get("text", "Küldd el neki a Pacsit: 1 perc a kvíz, és sokkal könnyebb jól dönteni. Neked egy kattintás, egy kutyának egy jó gazdi."), content, size=15, lh=23, mt=8)
         + f'<div style="margin-top:6px">{cells}</div>'
         + P(ctx, "Neked küldték tovább ezt a levelet? [Iratkozz fel itt](mc:subscribe), és csütörtökönként hozzád is megérkezik.", content, size=13, lh=19, mt=14, color=C["ink2"]))
    return row(box(t, b.get("tone", "sky")))


def b_kit(ctx, b):
    """Partnereknek: kész, átmásolható posztszöveg (+ kép) a saját csatornáikra."""
    content = b.get("content", "partnerkit")
    t = kicker(b.get("kicker", "Kész anyag a csatornáitokra"), color=C["teal"]) + H(rich(ctx, b["title"]), 3, mt=8)
    if b.get("lead"):
        t += P(ctx, b["lead"], content, size=15, lh=23, mt=8, color=C["ink2"])
    t += (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px"><tr>'
          f'<td class="bgc bd" style="background:#FFFFFF;border:1px dashed #CFC2B2;border-radius:14px;padding:16px 18px;font-family:{FU};font-size:14px;line-height:22px;color:{C["ink"]}">'
          f'<span class="ink">{rich(ctx, b["post"], content)}</span></td></tr></table>')
    if b.get("img"):
        t += f'<div style="margin-top:14px">{img(ctx, b["img"], b.get("alt", ""), 528, radius=14, href=b.get("imghref"), content=content)}</div>'
    if b.get("after"):
        t += P(ctx, b["after"], content, size=13, lh=19, mt=12, color=C["ink2"])
    return row(box(t, b.get("tone", "mint")))


def b_stats(ctx, b):
    cells = "".join(
        f'<td width="{100 // len(b["items"])}%" align="center" valign="top" style="padding:0 4px">'
        f'<p style="margin:0;font-family:{FD};font-size:40px;line-height:44px;font-weight:800;color:{C["coral"]}">{esc(n)}</p>'
        f'<p class="ink2" style="margin:4px 0 0;font-family:{FU};font-size:13px;line-height:17px;font-weight:700;color:{C["ink2"]}">{esc(lab)}</p></td>'
        for n, lab in b["items"])
    return row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>{cells}</tr></table>')


def b_cta(ctx, b):
    t = ""
    if b.get("title"):
        t += H(rich(ctx, b["title"]), 2, mt=0, align="center")
    if b.get("text"):
        t += P(ctx, b["text"], "cta", mt=10, align="center", color=C["ink2"])
    t += button(ctx, b["label"], b["href"], b.get("content", "cta"), align="center")
    return row(f'<div style="text-align:center">{t}</div>')


def b_image(ctx, b):
    t = img(ctx, b["img"], b.get("alt", ""), 528, radius=b.get("radius", 16), href=b.get("href"), content=b.get("content", "kep"))
    if b.get("caption"):
        t += P(ctx, b["caption"], "kep", size=13, lh=19, mt=8, color=C["ink2"], align="center")
    return row(t)


def b_sign(ctx, b):
    name = ctx.cfg["sender"].get("signature_name")
    t = P(ctx, b.get("text", "Pacsi-pacsi,"), "alairas", mt=0)
    t += f'<p class="ink" style="margin:4px 0 0;font-family:{FD};font-size:20px;line-height:26px;font-weight:800;color:{C["ink"]}">{esc(name) if name else "a Pacsi csapata"}</p>'
    if name:
        t += P(ctx, ctx.cfg["sender"].get("signature_role", ""), "alairas", size=14, lh=20, mt=2, color=C["ink2"])
    if b.get("ps"):
        t += P(ctx, "**U.i.** " + b["ps"], "ui", size=15, lh=23, mt=16, color=C["ink2"])
    return row(t)


def b_divider(ctx, b):
    return row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td class="bd" style="border-top:1px solid {C["line"]};font-size:0;line-height:0">&nbsp;</td></tr></table>')


BLOCKS = {"hero": b_hero, "intro": b_intro, "text": b_text, "breed": b_breed, "breeds": b_breeds, "fact": b_fact, "tip": b_tip,
          "quiz": b_quiz, "answer": b_answer, "social": b_social, "share": b_share, "kit": b_kit, "stats": b_stats,
          "cta": b_cta, "image": b_image, "sign": b_sign, "divider": b_divider}


# ---------------------------------------------------------------- keret
def series_label(e):
    s = e["series"]
    d = e.get("date")
    if s == "weekly":
        return f"Pacsi-levél · {e['no']}. szám"
    if s == "launch":
        return "Pacsi · indulás"
    if s == "welcome":
        return f"Üdv a falkában · {e['no']}/3"
    if s == "partner":
        return f"Pacsi Partnerlevél · {e['no']}."
    return "Pacsi"


def date_hu(d):
    if not d:
        return ""
    y, m, dd = d.split("-")
    mon = ["január", "február", "március", "április", "május", "június", "július", "augusztus", "szeptember", "október", "november", "december"][int(m) - 1]
    return f"{y}. {mon} {int(dd)}."


def render(ctx):
    e, cfg = ctx.e, ctx.cfg
    pre = "*|MC_PREVIEW_TEXT|*" if ctx.mode == "mc" else esc(e["preheader"])
    filler = "&#847;&zwnj;&nbsp;" * 60
    date_line = date_hu(e.get("date")) if e["series"] != "welcome" else ""
    top = (f'<tr><td style="padding:0 6px 12px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
           f'<td class="ink2" style="font-family:{FU};font-size:12px;line-height:16px;font-weight:700;color:{C["ink3"]}">{esc(series_label(e))}{" · " + esc(date_line) if date_line else ""}</td>'
           f'<td align="right" style="font-family:{FU};font-size:12px;line-height:16px;font-weight:700"><a class="lnk" href="{esc(ctx.href("mc:archive"))}" style="color:{C["ink3"]};text-decoration:underline">Megnyitás böngészőben</a></td>'
           f'</tr></table></td></tr>')
    logo = (f'<a href="{esc(ctx.app("logo"))}" target="_blank" style="text-decoration:none">'
            f'<img class="lm" src="{esc(ctx.img("logo.png"))}" width="200" height="44" alt="Pacsi by DarwinAI" style="display:block;width:200px;height:44px;border:0">'
            f'<!--[if !mso]><!--><img class="dm" src="{esc(ctx.img("logo-dark.png"))}" width="200" height="44" alt="Pacsi by DarwinAI" '
            f'style="display:none;width:200px;height:44px;border:0;max-height:0;overflow:hidden;mso-hide:all"><!--<![endif]--></a>')
    badge = e.get("badge") or {"weekly": "heti kutyás levél", "launch": "új · ingyenes", "welcome": "üdv a falkában", "partner": "partnereknek"}[e["series"]]
    header = (f'<tr><td class="px" style="padding:22px 36px 18px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
              f'<td valign="middle">{logo}</td>'
              f'<td valign="middle" align="right"><span style="display:inline-block;padding:6px 12px;border-radius:999px;background:{C["peach"]};'
              f'font-family:{FU};font-size:12px;line-height:14px;font-weight:800;color:{C["deep"]}">{esc(badge)}</span></td></tr></table></td></tr>')
    body = "".join(BLOCKS[b["t"]](ctx, b) for b in e["blocks"])
    social = [(p, n) for p, n in (("instagram", "Instagram"), ("tiktok", "TikTok"), ("facebook", "Facebook"), ("linkedin", "LinkedIn")) if cfg["social"].get(p)]
    soc = (" · ".join(f'<a class="lnk" href="{esc(cfg["social"][p])}" style="color:{C["ink2"]};font-weight:800;text-decoration:none">{n}</a>' for p, n in social))
    privacy = cfg["links"].get("privacy")
    links = [f'<a href="{esc(ctx.href("mc:profile"))}" style="color:{C["ink2"]};text-decoration:underline">Beállítások módosítása</a>',
             f'<a href="{esc(ctx.href("mc:unsub"))}" style="color:{C["ink2"]};text-decoration:underline">Leiratkozás</a>']
    if privacy:
        links.append(f'<a href="{esc(privacy)}" style="color:{C["ink2"]};text-decoration:underline">Adatkezelés</a>')
    why = "*|LIST:DESCRIPTION|*" if ctx.mode == "mc" else esc(cfg["audience"]["permission_reminder"])
    foot = (f'<tr><td class="px" style="padding:26px 30px 8px;text-align:center">'
            f'<p class="ink" style="margin:0;font-family:{FD};font-size:18px;line-height:22px;font-weight:800;color:{C["ink"]}">Pacsi <span style="font-family:{FU};font-size:12px;font-weight:700;color:{C["ink2"]}">by DarwinAI</span></p>'
            f'<p class="ink2" style="margin:6px 0 0;font-family:{FU};font-size:13px;line-height:19px;color:{C["ink2"]}">Ingyenes kutyafajta-választó 124 fajtával · <a class="lnk" href="{esc(ctx.app("lablec"))}" style="color:{C["coral"]};font-weight:800;text-decoration:none">pacsit.hu</a></p>'
            + (f'<p class="ink2" style="margin:8px 0 0;font-family:{FU};font-size:13px;line-height:19px;color:{C["ink2"]}">{soc}</p>' if soc else "")
            + f'<p class="ink2" style="margin:14px 0 0;font-family:{FU};font-size:12px;line-height:18px;color:{C["ink3"]}">{why}<br>{" · ".join(links)}</p>'
            f'<p class="ink2" style="margin:8px 0 0;font-family:{FU};font-size:12px;line-height:18px;color:{C["ink3"]}">'
            + ("*|LIST:COMPANY|* · *|LIST:ADDRESSLINE|*" if ctx.mode == "mc" else esc(" · ".join(x for x in [cfg["company"].get("legal_name") or cfg["company"]["name"], ", ".join(x for x in [cfg["company"].get("zip", ""), cfg["company"].get("city", ""), cfg["company"].get("address1", "")] if x) or "[postacím – config.json]"] if x)))
            + '</p>'
            + ('<p style="margin:12px 0 0">*|IF:REWARDS|* *|REWARDS|* *|END:IF|*</p>' if ctx.mode == "mc" else "")
            + '</td></tr>')
    title = esc(e["subject"])
    doc = f"""<!doctype html>
<html lang="hu" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="x-apple-disable-message-reformatting">
<meta name="format-detection" content="telephone=no,address=no,email=no,date=no,url=no">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>{title}</title>
<!--[if !mso]><!--><link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT@0,9..144,700..800,100;1,9..144,700,100&family=Manrope:wght@500;700;800&display=swap" rel="stylesheet"><!--<![endif]-->
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><style>h1,h2,h3,p,td,a{{font-family:Georgia,Arial,sans-serif!important}}</style><![endif]-->
<style>{HEAD_CSS}</style>
</head>
<body id="body" class="bgo" style="margin:0;padding:0;background:{C["bg"]}">
<!-- pacsi-edm {ctx.version} · build {ctx.build} · {e["id"]} -->
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all">{pre}{filler}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="bgo" bgcolor="{C["bg"]}" style="background:{C["bg"]}">
<tr><td align="center" style="padding:22px 10px 30px">
<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" class="w" style="width:600px;max-width:600px">
{top}
<tr><td class="bgc" bgcolor="{C["card"]}" style="background:{C["card"]};border-radius:26px;overflow:hidden">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
{header}{body}
<tr><td style="padding:0 0 34px;font-size:0;line-height:0">&nbsp;</td></tr>
</table>
</td></tr>
{foot}
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr>
</table>
</body>
</html>
"""
    if ctx.mode != "mc":
        doc = preview_merge(doc, ctx)
    return doc


def preview_merge(doc, ctx):
    """Előnézet: a Mailchimp-mezőkódok helyett mintaértékek."""
    doc = re.sub(r"\*\|IF:FNAME\|\*(.*?)\*\|ELSE:\|\*(.*?)\*\|END:IF\|\*", r"\1", doc, flags=re.S)
    doc = re.sub(r"\*\|IF:REWARDS\|\*.*?\*\|END:IF\|\*", "", doc, flags=re.S)
    rep = {"*|FNAME|*": "Anna", "*|ARCHIVE|*": "#", "*|FORWARD|*": "#", "*|LIST:SUBSCRIBE|*": "#", "*|UNSUB|*": "#",
           "*|UPDATE_PROFILE|*": "#", "*|CURRENT_YEAR|*": "2026"}
    for k, v in rep.items():
        doc = doc.replace(k, v)
    return doc


# ---------------------------------------------------------------- sima szöveges változat
def render_text(ctx):
    e = ctx.e
    L = []

    def txt(s, content="szoveg"):
        return INLINE.sub(lambda m: (f"{m.group(1)} ({ctx.href(m.group(2), content)})" if m.group(1) else (m.group(3) or m.group(4))), str(s))

    L.append(f"{series_label(e)}{' · ' + date_hu(e.get('date')) if e['series'] != 'welcome' and e.get('date') else ''}")
    L.append("")
    for b in e["blocks"]:
        t = b["t"]
        if t == "hero":
            if b.get("kicker"):
                L.append(b["kicker"].upper())
            L.append(plain(b["title"]).upper())
            if b.get("lead"):
                L.append(txt(b["lead"]))
            if b.get("cta"):
                L.append(f"→ {b['cta']['label']}: {ctx.href(b['cta']['href'], 'hero')}")
        elif t == "intro":
            if not b.get("nogreet"):
                L.append("*|IF:FNAME|*Szia *|FNAME|*!*|ELSE:|*Szia!*|END:IF|*" if not b.get("partner") else "*|IF:FNAME|*Kedves *|FNAME|*!*|ELSE:|*Kedves Partnerünk!*|END:IF|*")
            L += [txt(p) for p in b["paras"]]
        elif t in ("text", "tip"):
            if b.get("kicker"):
                L.append(b["kicker"].upper())
            if b.get("title"):
                L.append(plain(b["title"]))
            L += [txt(p) for p in b.get("paras", [])]
            if b.get("lead"):
                L.append(txt(b["lead"]))
            L += [f"  - {txt(x)}" for x in b.get("list", []) + b.get("items", [])]
            if b.get("after"):
                L.append(txt(b["after"]))
            if b.get("cta"):
                L.append(f"→ {b['cta']['label']}: {ctx.href(b['cta']['href'], b.get('content', 'szoveg'))}")
        elif t == "breed":
            br = BREEDS[b["id"]]
            L.append(b.get("kicker", "A hét fajtája").upper())
            L.append(f"{br['nev']} – {b.get('tagline') or br['tagline']}")
            L.append(txt(b.get("text") or br["leiras"].split(". ")[0] + "."))
            L.append("Kinek ajánlott? " + " · ".join(b.get("who") or br["kinekIgen"][:2]))
            L.append(f"→ A kártyája: {ctx.href('app:' + b.get('content', 'het-fajtaja') + '#b=' + br['id'])}")
        elif t == "breeds":
            if b.get("title"):
                L.append(plain(b["title"]).upper())
            if b.get("lead"):
                L.append(txt(b["lead"]))
            for bid in b["ids"]:
                L.append(f"  - {BREEDS[bid]['nev']}: {ctx.href('app:' + b.get('content', 'fajtak') + '#b=' + bid)}")
        elif t == "fact":
            L.append(b.get("kicker", "Tudtad?").upper())
            L.append(plain(b["title"]))
            L.append(txt(b["text"]))
        elif t == "quiz":
            L.append(b.get("kicker", "Tippelj!").upper())
            L.append(plain(b["question"]))
            L += [f"  {'ABCD'[i]}) {o['label']}: {ctx.href(o['href'], b.get('content', 'tippelj'))}" for i, o in enumerate(b["options"])]
            if b.get("note"):
                L.append(txt(b["note"]))
        elif t == "answer":
            L.append("A MÚLT HETI FEJTÖRŐ MEGFEJTÉSE")
            L.append(txt(b["text"]))
        elif t == "social":
            L.append(b.get("kicker", "A héten a közösségin").upper())
            L += [f"  - {it['label']}: {it['title']}" for it in b["items"]]
        elif t == "share":
            L.append(plain(b.get("title", "Ismersz valakit, aki kutyát szeretne?")))
            L.append(f"Küldd el neki: {ctx.site}")
            L.append("Neked küldték tovább? Feliratkozás: *|LIST:SUBSCRIBE|*")
        elif t == "kit":
            L.append(plain(b["title"]).upper())
            L.append(txt(b["post"]))
        elif t == "stats":
            L.append(" · ".join(f"{n} {lab}" for n, lab in b["items"]))
        elif t == "cta":
            if b.get("title"):
                L.append(plain(b["title"]))
            L.append(f"→ {b['label']}: {ctx.href(b['href'], b.get('content', 'cta'))}")
        elif t == "sign":
            L.append(b.get("text", "Pacsi-pacsi,"))
            L.append(ctx.cfg["sender"].get("signature_name") or "a Pacsi csapata")
            if b.get("ps"):
                L.append("U.i. " + txt(b["ps"]))
        L.append("")
    L += ["—", "Pacsi by DarwinAI · ingyenes kutyafajta-választó · pacsit.hu", "*|LIST:DESCRIPTION|*",
          "Leiratkozás: *|UNSUB|*  ·  Beállítások: *|UPDATE_PROFILE|*", "*|LIST:COMPANY|* · *|LIST:ADDRESSLINE|*"]
    out = "\n".join(L)
    if ctx.mode != "mc":
        out = preview_merge(out, ctx)
    return out
