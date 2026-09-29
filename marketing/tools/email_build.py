"""Pacsi eDM – build: levélképek, levelek (Mailchimp + előnézet + sima szöveg), ellenőrzés, CMS-adat.

Használat:
  python marketing/tools/email_build.py              # minden: képek (hiányzók), levelek, ellenőrzés, content/email.json
  python marketing/tools/email_build.py --render     # a HTML-ből készülő fejlécképeket és a logót mindenképp újrarendereli
  python marketing/tools/email_build.py --shots      # + teljes oldalas képernyőkép minden levélről (marketing/tmp/email/shots)
  python marketing/tools/email_build.py --version    # verzió

Kimenet:
  marketing/out/email/<id>.html        előnézet (mintaértékekkel, helyi képekkel) – böngészőben megnyitható
  marketing/out/email/mc/<id>.html     Mailchimp-változat (mezőkódok; a képek a Mailchimp tárhelyéről, ha már fel vannak töltve)
  marketing/out/email/mc/<id>.txt      sima szöveges változat
  marketing/out/email/img/…            levélképek (mind ≤ 1200×1200 px, JPG/PNG)
  marketing/content/email.json         a CMS „E-mail” fülének adatai
Utána: python marketing/tools/build.py --no-render (CMS), és a claude.ai-s CMS újraközzététele.
"""
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import subprocess
import sys

from PIL import Image, ImageDraw

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
OUT = MK / "out" / "email"
IMG = OUT / "img"
TMP = MK / "tmp" / "email"
STATE = MK / "email" / "state" / "mailchimp.json"
MAX_SIDE, MAX_BYTES = 1200, 1_000_000       # Mailchimp: legfeljebb 1200×1200 px, ~1 MB
GMAIL_CLIP = 102_000                          # a Gmail e fölött levágja a levelet


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sys.path.insert(0, str(MK / "email"))
import frame as F  # noqa: E402

P = load("email_plan", MK / "content" / "email_plan.py")
C = load("content", MK / "content" / "content.py")
CFG = json.loads((MK / "email" / "config.json").read_text(encoding="utf-8"))
VERSION = (MK / "VERSION").read_text(encoding="utf-8").strip()


def state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


# ------------------------------------------------------------------ képek
def images_of(e):
    names = {"logo.png", "logo-dark.png"}
    for b in e["blocks"]:
        if b.get("img"):
            names.add(b["img"])
        if b["t"] == "breed":
            names.add(f"breed/{b['id']}.png")
        if b["t"] == "breeds":
            names |= {f"breed/{i}.png" for i in b["ids"]}
        if b["t"] == "social":
            names |= {it["img"] for it in b["items"]}
    return names


def social_source(item_id):
    it = next(i for i in C.ITEMS if i["id"] == item_id)
    if it["kind"] == "video":
        return MK / it["files"][1]["src"]
    pages = (it.get("design") or {}).get("pages")
    return MK / "out" / "kepek" / (f"{item_id}_1.png" if pages else f"{item_id}.png")


def save_jpg(im, path, q=84):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(path, "JPEG", quality=q, optimize=True, progressive=True)


def make_breed(bid, path):
    """kör alakú portré fehér gyűrűvel, átlátszó sarkokkal (380×380 = 190 px 2×)"""
    S, ring, k = 380, 10, 4
    src = Image.open(ROOT / "img" / "portrek" / f"{bid}.webp").convert("RGB")
    big = S * k
    out = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.ellipse((0, 0, big - 1, big - 1), fill=(255, 255, 255, 255))
    inner = big - 2 * ring * k
    pic = src.resize((inner, inner), Image.LANCZOS)
    mask = Image.new("L", (inner, inner), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, inner - 1, inner - 1), fill=255)
    out.paste(pic, (ring * k, ring * k), mask)
    out = out.resize((S, S), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, "PNG", optimize=True)


def make_social(item_id, path):
    im = Image.open(social_source(item_id)).convert("RGB")
    if item_id == "p_og":                                # linkelőnézeti kép: széles, a partnerkészletben 528 px-en
        im.thumbnail((1056, 1056), Image.LANCZOS)
        return save_jpg(im, path)
    w, h = im.size
    tw, th = w, round(w * 5 / 4)                         # 4:5-re vágva (a videóborító 9:16 → közép)
    if th > h:
        th, tw = h, round(h * 4 / 5)
    x0, y0 = (w - tw) // 2, max(0, (h - th) // 2 - (h - th) // 6)
    im = im.crop((x0, y0, x0 + tw, y0 + th)).resize((344, 430), Image.LANCZOS)
    save_jpg(im, path, q=82)


def make_kv_hero(spec, path):
    src = Image.open(MK / "assets" / "kv" / f"{spec['kv']}.png").convert("RGB")
    W, H = src.size
    z = spec.get("z", 1)
    cw, ch = min(W, H * 2) / z, min(W, H * 2) / 2 / z
    cx, cy = spec.get("fx", .5) * W, spec.get("fy", .5) * H
    x0 = min(max(0, cx - cw / 2), W - cw)
    y0 = min(max(0, cy - ch / 2), H - ch)
    im = src.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch))).resize((1200, 600), Image.LANCZOS)
    save_jpg(im, path)


def render_html_assets(jobs):
    """jobs: [(név, src-url, w, h, dpr, átlátszó)] → PNG a tmp-be a node rendererrel"""
    if not jobs:
        return
    TMP.mkdir(parents=True, exist_ok=True)
    man = [{"src": src, "out": str((TMP / "render" / f"{n}.png").relative_to(ROOT)).replace("\\", "/"), "w": w, "h": h, "dpr": dpr, "transparent": tr}
           for n, src, w, h, dpr, tr in jobs]
    mf = TMP / "render_manifest.json"
    mf.write_text(json.dumps(man, indent=1), encoding="utf-8")
    subprocess.run(["node", str(MK / "tools" / "email_render.mjs"), "images", str(mf)], check=True, cwd=ROOT)


def build_images(emails, force_render=False):
    need = set().union(*(images_of(e) for e in emails))
    jobs = []
    for n in sorted(need):
        p = IMG / n
        if n in ("logo.png", "logo-dark.png"):
            if force_render or not p.exists():
                jobs.append((n[:-4], "marketing/email/img/hero.html?d=logo&w=200&h=44&px=40" + ("&inv=1" if "dark" in n else ""), 200, 44, 2, True))
        elif n.startswith("breed/"):
            if not p.exists():
                make_breed(n[6:-4], p)
        elif n.startswith("social/"):
            if not p.exists():
                make_social(n[7:-4], p)
        elif n.startswith("hero/"):
            eid = n[5:-4]
            spec = P.HEROES[eid]
            if "kv" in spec:
                if not p.exists() or p.stat().st_mtime < (MK / "assets" / "kv" / f"{spec['kv']}.png").stat().st_mtime:
                    make_kv_hero(spec, p)
            elif force_render or not p.exists():
                q = f"d={spec['design']}&w=1200&h=600" + (f"&p={spec['p']}" if spec.get("p") else "")
                jobs.append((f"hero_{eid}", f"marketing/email/img/hero.html?{q}", 1200, 600, 1, False))
    render_html_assets(jobs)
    for n, *_ in jobs:
        png = TMP / "render" / f"{n}.png"
        if n.startswith("hero_"):
            save_jpg(Image.open(png), IMG / "hero" / f"{n[5:]}.jpg")
        else:
            IMG.mkdir(parents=True, exist_ok=True)
            Image.open(png).save(IMG / f"{n}.png", "PNG", optimize=True)
    # ellenőrzés: minden kép ≤ 1200×1200 és ≤ 1 MB
    problems = []
    for n in sorted(need):
        p = IMG / n
        if not p.exists():
            problems.append(f"hiányzó kép: {n}")
            continue
        with Image.open(p) as im:
            if max(im.size) > MAX_SIDE:
                problems.append(f"túl nagy kép ({im.size[0]}×{im.size[1]}): {n}")
        if p.stat().st_size > MAX_BYTES:
            problems.append(f"1 MB fölötti kép ({p.stat().st_size // 1024} kB): {n}")
    return need, problems


# ------------------------------------------------------------------ levelek
def img_url_mc(st):
    files = st.get("files", {})
    return lambda n: files.get(n, {}).get("url") or f"img/{n}"


def check(e, html_mc, imgs, st):
    out = []
    if len(e["subject"]) > 60:
        out.append(("figyelem", f"Hosszú tárgysor ({len(e['subject'])} karakter) – telefonon levágódhat."))
    if not 35 <= len(e["preheader"]) <= 120:
        out.append(("figyelem", f"Az előnézeti szöveg {len(e['preheader'])} karakter (ideális: 40–110)."))
    size = len(html_mc.encode("utf-8"))
    if size > 90_000:
        out.append(("hiba" if size > GMAIL_CLIP else "figyelem", f"A levél {size // 1024} kB – a Gmail 102 kB fölött levágja."))
    if e.get("todo"):
        out.append(("hiba", "Kitöltendő: " + e["todo"]))
    if any(b.get("todo") for b in e["blocks"]):
        out.append(("hiba", "Helykitöltő tartalom van a levélben (szaggatott keretes blokk)."))
    if re.search(r'href=""', html_mc):
        out.append(("hiba", "Üres link van a levélben."))
    missing = [n for n in imgs if n not in st.get("files", {})]
    if st.get("list") and missing:
        out.append(("info", f"{len(missing)} kép még nincs feltöltve a Mailchimpbe (a push feltölti)."))
    return out


def src_hash():
    """a levelek build-azonosítója: a terv, a keret és a beállítások tartalmából"""
    return hashlib.sha1((MK / "content" / "email_plan.py").read_bytes() + (MK / "email" / "frame.py").read_bytes()
                        + json.dumps(CFG, sort_keys=True).encode()).hexdigest()[:7]


def config_missing():
    miss = []
    s, c = CFG["sender"], CFG["company"]
    if not s.get("from_email"):
        miss.append("Feladó e-mail-cím (sender.from_email)")
    if not s.get("signature_name"):
        miss.append("Aláíró neve (sender.signature_name) – a levelek „a Pacsi csapata” aláírással mennek")
    if not all(c.get(k) for k in ("address1", "city", "zip")):
        miss.append("Postacím a láblécbe (company.address1, city, zip) – kötelező")
    if not c.get("legal_name"):
        miss.append("Cég hivatalos neve (company.legal_name)")
    if not any(CFG["social"].get(k) for k in ("instagram", "tiktok", "facebook", "linkedin")):
        miss.append("Közösségi profilok címei (social.*) – addig a levelek nem linkelnek a profilokra")
    if not CFG["links"].get("privacy"):
        miss.append("Adatkezelési tájékoztató webcíme (links.privacy)")
    if not (ROOT / "Mailchimp_API.txt").exists():
        miss.append("Mailchimp API-kulcs (Mailchimp_API.txt a repó gyökerében)")
    return miss


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # a Windows-konzol kódlapja ne akadjon el az emojikon
    args = sys.argv[1:]
    if "--version" in args:
        print(f"Pacsi eDM {VERSION}")
        return
    emails = P.EMAILS
    ids = [e["id"] for e in emails]
    assert len(ids) == len(set(ids)), "ismétlődő levélazonosító"
    need, problems = build_images(emails, force_render="--render" in args)
    st = state()
    (OUT / "mc").mkdir(parents=True, exist_ok=True)
    rows, total_warn = [], 0
    src_hash = globals()["src_hash"]()
    for e in emails:
        imgs = sorted(images_of(e))
        mc_ctx = F.Ctx(e, CFG, img_url_mc(st), mode="mc", version=VERSION, build=src_hash)
        html_mc = F.render(mc_ctx)
        text_mc = F.render_text(mc_ctx)
        pv_ctx = F.Ctx(e, CFG, lambda n: f"img/{n}", mode="preview", version=VERSION, build=src_hash)
        html_pv = F.render(pv_ctx)
        ebuild = hashlib.sha1(html_mc.encode("utf-8")).hexdigest()[:7]
        (OUT / "mc" / f"{e['id']}.html").write_text(html_mc, encoding="utf-8")
        (OUT / "mc" / f"{e['id']}.txt").write_text(text_mc, encoding="utf-8")
        (OUT / f"{e['id']}.html").write_text(html_pv, encoding="utf-8")
        chk = check(e, html_mc, imgs, st) + [("hiba", p) for p in problems if any(p.endswith(n) for n in imgs)]
        total_warn += sum(1 for k, _ in chk if k != "info")
        camp = st.get("campaigns", {}).get(e["id"], {})
        rows.append({
            **{k: e.get(k) for k in ("id", "series", "no", "date", "time", "delay", "segment", "status", "todo", "title", "subject",
                                      "subjectAlt", "preheader", "theme", "social", "socialPlan")},
            "build": ebuild, "bytes": len(html_mc.encode("utf-8")), "checks": chk, "images": imgs,
            "html": html_pv.replace('src="img/', 'src="{{IMG}}/').replace("url('img/", "url('{{IMG}}/"),
            "text": F.render_text(pv_ctx), "hero": f"hero/{e['id']}.jpg",
            "mc": {k: camp.get(k) for k in ("campaign_id", "web_id", "status", "send_time", "emails_sent", "report", "template_id", "pushed", "pushed_build") if camp.get(k) is not None},
        })
    miss = config_missing()
    data = {
        "version": VERSION, "build": src_hash, "series": P.SERIES, "statuses": P.STATUSES, "segments": P.SEGMENTS,
        "guide": P.GUIDE, "outreach": P.OUTREACH, "followup": P.FOLLOWUP, "contactStatuses": P.CONTACT_STATUSES,
        "config": {"sender": {k: CFG["sender"].get(k, "") for k in ("from_name", "from_email", "reply_to", "signature_name", "signature_role")},
                   "schedule": CFG["schedule"], "links": {k: v for k, v in CFG["links"].items() if not k.startswith("_")},
                   "social": {k: v for k, v in CFG["social"].items() if not k.startswith("_")}, "mode": CFG["mailchimp"]["mode"]},
        "configMissing": miss, "darkCss": F.DARK_RULES,
        "mailchimp": {"connected": bool(st.get("list")), "account": st.get("account"), "list": st.get("list"), "synced": st.get("synced"),
                      "audience": st.get("audience")},
        "emails": rows,
    }
    (MK / "content" / "email.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    # a claude.ai-s CMS-hez közzéteendő képek (published path → helyi fájl)
    pub = {f"email/img/{n}": str((IMG / n).relative_to(MK)).replace("\\", "/") for n in sorted(need)}
    (MK / "tmp").mkdir(exist_ok=True)
    (MK / "tmp" / "email_files.json").write_text(json.dumps(pub, indent=1), encoding="utf-8")
    print(f"  Pacsi eDM v{VERSION} · build {src_hash} · {len(emails)} levél · {len(need)} kép · figyelmeztetés: {total_warn}")
    for p in problems:
        print("  ! " + p)
    for m in miss:
        print("  – hiányzó beállítás: " + m)
    big = max(rows, key=lambda r: r["bytes"])
    print(f"  legnagyobb levél: {big['id']} {big['bytes'] // 1024} kB")
    if "--shots" in args:
        man = []
        for e in emails:
            man.append({"src": f"marketing/out/email/{e['id']}.html", "out": f"marketing/tmp/email/shots/{e['id']}.png", "w": 680})
            man.append({"src": f"marketing/out/email/{e['id']}.html", "out": f"marketing/tmp/email/shots/{e['id']}_m.png", "w": 390})
        mf = TMP / "shots_manifest.json"
        mf.write_text(json.dumps(man, indent=1), encoding="utf-8")
        subprocess.run(["node", str(MK / "tools" / "email_render.mjs"), "shots", str(mf)], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
