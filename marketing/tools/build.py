"""Pacsi Marketing – build.

Használat:
  python marketing/tools/build.py            # képek renderelése + borítók + content.json + CMS
  python marketing/tools/build.py --no-render   # csak adat és CMS (a meglévő képekből)
  python marketing/tools/build.py --only k_launch,c_lakas   # csak ezek a képek renderelődnek újra

Kimenet:
  marketing/out/kepek/*.png            posztképek (és karusszelnél PDF + ZIP)
  marketing/out/videok/*_borito.jpg    videók borítóképei
  marketing/content/content.json       a CMS adatai
  marketing/cms/index.html             CMS helyi használatra (python -m http.server a marketing mappában)
  marketing/cms/artifact.html          CMS a claude.ai-ra (a médiafájlok az artifact eszköztárából jönnek)

A videókat külön kell renderelni: node marketing/tools/render.mjs video <kompozíció> <kimenet.mp4>
"""
import base64, hashlib, importlib.util, io, json, pathlib, subprocess, sys, zipfile
from datetime import date

from PIL import Image

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
OUT = MK / "out"
spec = importlib.util.spec_from_file_location("content", MK / "content" / "content.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)

# a videók borítóképe ennél az időpontnál (mp) készül
POSTER_T = {"v1": 1.55, "v2": 1.7, "v3": 1.9, "v4": 1.7}


def design_files(it):
    d = it["design"]
    pages = d.get("pages")
    if pages:
        files = [{"label": f"{i}. dia (PNG)", "src": f"out/kepek/{it['id']}_{i}.png", "role": "page"} for i in range(1, pages + 1)]
        files += [{"label": "Mind egyben (ZIP)", "src": f"out/kepek/{it['id']}.zip", "role": "zip"},
                  {"label": "PDF-karusszel (LinkedIn)", "src": f"out/kepek/{it['id']}.pdf", "role": "pdf"}]
        return files
    return [{"label": f"Kép (PNG, {d['w']}×{d['h']})", "src": f"out/kepek/{it['id']}.png", "role": "main"}]


def render_manifest(only):
    items = []
    for it in C.ITEMS:
        d = it.get("design")
        if not d or (only and it["id"] not in only):
            continue
        pages = d.get("pages") or 0
        for n in (range(1, pages + 1) if pages else [None]):
            q = f"d={d['d']}&w={d['w']}&h={d['h']}"
            p = n if n else d.get("p")
            if p:
                q += f"&p={p}"
            out = f"marketing/out/kepek/{it['id']}_{n}.png" if n else f"marketing/out/kepek/{it['id']}.png"
            items.append({"src": f"marketing/social/images/post.html?{q}", "out": out, "w": d["w"], "h": d["h"]})
    return items


def carousel_extras(it):
    pages = it["design"]["pages"]
    pngs = [OUT / "kepek" / f"{it['id']}_{i}.png" for i in range(1, pages + 1)]
    pdf = OUT / "kepek" / f"{it['id']}.pdf"
    if pdf.exists() and all(p.stat().st_mtime < pdf.stat().st_mtime for p in pngs):
        return                      # csak akkor készül újra, ha valamelyik dia változott (a PDF időbélyeget is tartalmaz)
    imgs = [Image.open(OUT / "kepek" / f"{it['id']}_{i}.png").convert("RGB") for i in range(1, pages + 1)]
    imgs[0].save(OUT / "kepek" / f"{it['id']}.pdf", save_all=True, append_images=imgs[1:], resolution=144)
    with zipfile.ZipFile(OUT / "kepek" / f"{it['id']}.zip", "w", zipfile.ZIP_STORED) as z:
        for i in range(1, pages + 1):
            z.write(OUT / "kepek" / f"{it['id']}_{i}.png", f"{it['id']}_{i}.png")


def posters():
    for it in C.ITEMS:
        if it["kind"] != "video":
            continue
        mp4 = ROOT / "marketing" / it["files"][0]["src"]
        jpg = ROOT / "marketing" / it["files"][1]["src"]
        if not mp4.exists():
            print(f"  ! hiányzó videó: {mp4.name}")
            continue
        if jpg.exists() and jpg.stat().st_mtime > mp4.stat().st_mtime:
            continue
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(POSTER_T.get(it["id"], 1.5)), "-i", str(mp4),
                            "-frames:v", "1", "-q:v", "2", str(jpg)])
        print(f"  borító: {jpg.name}" if r.returncode == 0 else f"  ! a borító nem készült el (fut még a renderelés?): {mp4.name}")


def thumb(path, w=360):
    im = Image.open(path).convert("RGB")
    im.thumbnail((w, w * 2))
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=78, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    args = sys.argv[1:]
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else set()
    if "--no-render" not in args:
        man = render_manifest(only)
        if man:
            mf = MK / "tmp" / "manifest.json"
            mf.parent.mkdir(exist_ok=True)
            mf.write_text(json.dumps(man, indent=1), encoding="utf-8")
            subprocess.run(["node", str(MK / "tools" / "render.mjs"), "images", str(mf)], check=True, cwd=ROOT)
    for it in C.ITEMS:
        if it.get("design", {}).get("pages"):
            carousel_extras(it)
    posters()

    items = []
    for it in C.ITEMS:
        it = json.loads(json.dumps(it))
        if it.get("design"):
            it["files"] = design_files(it)
        for f in it.get("files", []):
            p = MK / f["src"]
            f["bytes"] = p.stat().st_size if p.exists() else 0
            f["name"] = p.name
        prev = next((f for f in it.get("files", []) if f["role"] in ("cover", "page", "main") and not f["src"].endswith(".mp4")), None)
        if prev and (MK / prev["src"]).exists():
            it["thumb"] = thumb(MK / prev["src"])
            with Image.open(MK / prev["src"]) as im:
                it["ratio"] = round(im.width / im.height, 4)
        items.append(it)

    version = (MK / "VERSION").read_text(encoding="utf-8").strip()
    data = {"version": version, "built": date.today().isoformat(), "site": C.SITE, "siteLabel": C.SITE_LABEL,
            "platforms": C.PLATFORMS, "kinds": C.KINDS, "statuses": C.STATUSES,
            "items": items, "ideas": C.IDEAS, "guide": C.GUIDE}
    # e-mail modul (python marketing/tools/email_build.py) és kapcsolati adatbázis (python marketing/tools/contacts.py)
    em_p, ct_p = MK / "content" / "email.json", MK / "email" / "data" / "contacts.json"
    data["email"] = json.loads(em_p.read_text(encoding="utf-8")) if em_p.exists() else None
    data["contacts"] = json.loads(ct_p.read_text(encoding="utf-8")) if ct_p.exists() else None
    sp = importlib.util.spec_from_file_location("setup_plan", MK / "content" / "setup_plan.py")
    SP = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(SP)
    for pl in SP.SETUP:
        for st in pl["steps"]:
            if st.get("limit") and st.get("copy") and len(st["copy"]) > st["limit"]:
                print(f"  ! túl hosszú szöveg ({len(st['copy'])}/{st['limit']}): {pl['name']} – {st['do'][:40]}")
    data["setup"] = SP.SETUP
    fajtak = json.loads((ROOT / "data" / "fajtak.json").read_text(encoding="utf-8"))["breeds"]
    data["breedNames"] = {b["id"]: b["nev"] for b in fajtak}
    # 1.4.0: arculat és szövegbank (Arculat fül), ellenőrzések és kiküldési napló (Áttekintés fül); --links: linkellenőrzés is
    bp = importlib.util.spec_from_file_location("brand", MK / "content" / "brand.py")
    BR = importlib.util.module_from_spec(bp)
    bp.loader.exec_module(BR)
    data["brand"] = BR.BRAND
    ip = importlib.util.spec_from_file_location("insights", MK / "tools" / "insights.py")
    INS = importlib.util.module_from_spec(ip)
    ip.loader.exec_module(INS)
    data["insights"] = INS.compute(data, links="--links" in args)
    generated = data["insights"].pop("generated")      # az időbélyeg nem része a build-azonosítónak (az a tartalom hash-e)
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))  # tartalmazza az e-mail és a kapcsolati adatokat is
    tpl = (MK / "cms" / "src" / "cms.html").read_text(encoding="utf-8")
    build = hashlib.sha1((body + tpl).encode("utf-8")).hexdigest()[:7]
    data["build"] = build
    data["insights"]["generated"] = generated
    (MK / "content" / "content.json").write_text(json.dumps({k: v for k, v in data.items()}, ensure_ascii=False, indent=1), encoding="utf-8")

    # helyi CMS: a médiafájlok relatív útvonalon (marketing/cms/ → ../out/…)
    def page(media, drop_missing=False, email_img=""):
        d = json.loads(json.dumps(data))
        d["emailImg"] = email_img
        for it in d["items"]:
            for f in it.get("files", []):
                f["url"] = media(f["src"])
            if drop_missing:   # az artifact eszköztára pl. ZIP-et nem fogad: ami nincs feltöltve, az ott nem jelenik meg
                it["files"] = [f for f in it.get("files", []) if f["url"]]
        js = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        return tpl.replace("/*CMS_DATA*/", js)

    (MK / "cms" / "index.html").write_text('<!doctype html>\n<html lang="hu">\n<head>\n<meta charset="utf-8">\n' + page(lambda s: "../" + s, email_img="../out/email/img") + '\n</html>\n', encoding="utf-8")
    amap_p = MK / "cms" / "assets.json"
    amap = json.loads(amap_p.read_text(encoding="utf-8")) if amap_p.exists() else {}
    missing = [f["src"] for it in data["items"] for f in it.get("files", [])
               if not f["src"].endswith(".zip") and (f["src"] not in amap or amap[f["src"]].get("sha1") != sha1(MK / f["src"]))]
    (MK / "cms" / "artifact.html").write_text(page(lambda s: amap.get(s, {}).get("url", ""), drop_missing=True, email_img="email/img"), encoding="utf-8")
    (MK / "tmp").mkdir(exist_ok=True)
    (MK / "tmp" / "upload_needed.json").write_text(json.dumps(missing, indent=1), encoding="utf-8")
    print(f"  CMS kész: v{version} · build {build} · {len(items)} tartalom · feltöltendő médiafájl: {len(missing)}")


def sha1(p):
    return hashlib.sha1(p.read_bytes()).hexdigest() if p.exists() else ""


if __name__ == "__main__":
    main()
