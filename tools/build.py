"""Pacsi by DarwinAI – build: egyfájlos standalone HTML + telepíthető PWA-csomag.

Használat:  python tools/build.py
Kimenet:
  dist/pacsi.html        minden egyben (képek base64-ben) – dupla kattintással megnyílik, offline is
  dist/pwa/              index.html + manifest + service worker + ikonok + képek – statikus tárhelyre
  dist/pacsi-artifact.html  claude.ai artifact-változat (keret nélküli törzs, artifact-mód jelzővel)
"""
import base64, hashlib, io, json, pathlib, re, shutil, sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, DIST = ROOT / "src", ROOT / "dist"
sys.path.insert(0, str(ROOT / "tools"))
import build_data  # noqa: E402


def b64(path, mime):
    return f"data:{mime};base64," + base64.b64encode(pathlib.Path(path).read_bytes()).decode()


def make_icon(size, maskable=False, transparent=False):
    """Kabala-portré körben, krém/korall háttéren."""
    port = Image.open(ROOT / "img" / "portrek" / "kabala-pacsi.webp").convert("RGB")
    bg = (0, 0, 0, 0) if transparent else (255, 107, 61, 255)
    im = Image.new("RGBA", (size, size), bg)
    d = int(size * (.66 if maskable else .86))
    ring = int(size * .035)
    x0 = (size - d) // 2
    mask = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    mask = mask.resize((d, d), Image.LANCZOS)
    white = Image.new("RGBA", (d + ring * 2, d + ring * 2), (0, 0, 0, 0))
    wm = Image.new("L", ((d + ring * 2) * 4,) * 2, 0)
    ImageDraw.Draw(wm).ellipse((0, 0, (d + ring * 2) * 4 - 1, (d + ring * 2) * 4 - 1), fill=255)
    wm = wm.resize((d + ring * 2,) * 2, Image.LANCZOS)
    white.paste((255, 253, 249, 255), (0, 0), wm)
    im.alpha_composite(white, (x0 - ring, x0 - ring))
    im.paste(port.resize((d, d), Image.LANCZOS), (x0, x0), mask)
    return im


def png_bytes(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def main():
    build_data.main()
    data = json.loads((ROOT / "data" / "fajtak.json").read_text(encoding="utf-8"))
    ids = [b["id"] for b in data["breeds"]] + [s["id"] for s in data["spares"]]
    html = (SRC / "index.html").read_text(encoding="utf-8")
    css = (SRC / "app.css").read_text(encoding="utf-8")
    js_src = "\n".join(p.read_text(encoding="utf-8") for p in sorted((SRC / "js").glob("*.js")))
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    # Verzió: szemantikus verziószám a VERSION fájlból + build-azonosító (a forrás tartalmának rövid hash-e).
    # Mindkettő látszik az appban (Tippek → névjegy, asztali panel lábléce), így ellenőrizhető, melyik verzió fut.
    app_ver = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    hero = ROOT / "img" / "nyito-pacsi.webp"   # a nyitó ablak képe (tools/make_hero.py)
    # Saját domain + névtelen statisztika (Umami) – egy helyen: deploy/site.json
    site_raw = (ROOT / "deploy" / "site.json").read_text(encoding="utf-8")
    site = json.loads(site_raw)
    site_url = site["url"].rstrip("/")
    build_id = hashlib.sha1((css + js_src + data_json + site_raw).encode("utf-8") + hero.read_bytes()).hexdigest()[:7]
    site_js = json.dumps({"url": site_url, "stat": site.get("stat", {})}, ensure_ascii=False)
    js = ("(() => {\n'use strict';\n" + f"const APP_VERSION = {json.dumps(app_ver)}, APP_BUILD = {json.dumps(build_id)};\n"
          + f"const SITE = {site_js};\n" + js_src + "\n})();")
    # megosztási előnézet (Facebook, Messenger, LinkedIn…): kanonikus cím és kép a saját domainen
    site_head = "\n".join([
        f'<link rel="canonical" href="{site_url}/">',
        f'<meta property="og:url" content="{site_url}/">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Pacsi">',
        '<meta property="og:locale" content="hu_HU">',
        f'<meta property="og:image" content="{site_url}/og.jpg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="Egy kéz pacsit ad a Pacsi kabalájának – Melyik kutya illik hozzád? 124 kutyafajta egy élő felhőben.">',
        '<meta name="twitter:card" content="summary_large_image">',
    ])

    def assemble(img_script, head, favicon):
        out = html.replace("/*INLINE_CSS*/", css).replace("/*INLINE_JS*/", js.replace("</script", "<\\/script"))
        out = out.replace("/*INLINE_DATA*/", data_json).replace("<!--INLINE_IMG-->", img_script)
        out = out.replace("<!--SITE_HEAD-->", site_head)
        return out.replace("<!--PWA_HEAD-->", head).replace("/*FAVICON*/", favicon)

    DIST.mkdir(exist_ok=True)
    fav = make_icon(64, transparent=True)
    fav_uri = "data:image/png;base64," + base64.b64encode(png_bytes(fav)).decode()

    # 1) Standalone
    imgs = {i: b64(ROOT / "img" / "portrek" / f"{i}.webp", "image/webp") for i in ids}
    hero_js = ";window.PACSI_HERO=" + json.dumps(b64(hero, "image/webp"))
    img_script = ("<script>window.PACSI_SPRITE=" + json.dumps(b64(ROOT / "img" / "sprite-thumbs.webp", "image/webp")) +
                  ";window.PACSI_IMG=" + json.dumps(imgs) + hero_js + ";</script>")
    standalone = assemble(img_script, "", fav_uri)
    (DIST / "pacsi.html").write_text(standalone, encoding="utf-8")

    # 2) PWA
    pwa = DIST / "pwa"
    if pwa.exists():
        shutil.rmtree(pwa)
    (pwa / "img" / "portrek").mkdir(parents=True)
    (pwa / "icons").mkdir()
    shutil.copy(ROOT / "img" / "sprite-thumbs.webp", pwa / "img" / "sprite-thumbs.webp")
    shutil.copy(hero, pwa / "img" / hero.name)
    og = ROOT / "img" / "og.jpg"   # megosztási előnézet (tools/make_og.py) – offline nem kell, ezért nincs a precache-ben
    if og.exists():
        shutil.copy(og, pwa / "og.jpg")
    for i in ids:
        shutil.copy(ROOT / "img" / "portrek" / f"{i}.webp", pwa / "img" / "portrek" / f"{i}.webp")
    (pwa / "icons" / "icon-192.png").write_bytes(png_bytes(make_icon(192)))
    (pwa / "icons" / "icon-512.png").write_bytes(png_bytes(make_icon(512)))
    (pwa / "icons" / "maskable-512.png").write_bytes(png_bytes(make_icon(512, maskable=True)))
    (pwa / "icons" / "apple-touch-icon.png").write_bytes(png_bytes(make_icon(180).convert("RGB")))
    (pwa / "icons" / "favicon-64.png").write_bytes(png_bytes(fav))
    manifest = {
        "name": "Pacsi by DarwinAI", "short_name": "Pacsi", "lang": "hu",
        "description": f"{len(data['breeds'])} kutyafajta egy élő felhőben – szűrj, hasonlíts, találd meg a hozzád illőt.",
        "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
        "background_color": "#FBF6EE", "theme_color": "#FBF6EE", "categories": ["lifestyle", "education"],
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
        "shortcuts": [{"name": "Párkereső kvíz", "url": "./#kviz"}],
    }
    (pwa / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    head = ('<link rel="manifest" href="manifest.webmanifest">\n'
            '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">')
    index = assemble("<script>window.PACSI_PWA=true;</script>", head, "icons/favicon-64.png")
    (pwa / "index.html").write_text(index, encoding="utf-8")
    files = ["./", "index.html", "manifest.webmanifest", "img/sprite-thumbs.webp", f"img/{hero.name}"] + \
            [f"img/portrek/{i}.webp" for i in ids] + [f"icons/{p.name}" for p in (pwa / "icons").iterdir()]
    # a verzió minden előre gyorsítótárazott fájlból számolódik – egy képcsere is frissítést indít
    digest = hashlib.sha1()
    for f in files[1:]:
        digest.update(f.encode("utf-8"))
        digest.update((pwa / f).read_bytes())
    version = digest.hexdigest()[:10]
    sw = (SRC / "sw.js").read_text(encoding="utf-8").replace("__VERSION__", f"{app_ver}-{version}").replace("__FILES__", json.dumps(files))
    (pwa / "sw.js").write_text(sw, encoding="utf-8")

    # 3) claude.ai artifact: a publikáló maga adja a doctype/head/body vázat, ezért csak a törzs kell,
    #    a <title> legelöl; a keret :root-padding-je miatt az app 100% magas, a safe-area-t nem duplázzuk
    body = html.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    fonts = "\n".join(l for l in html.splitlines() if "fonts.g" in l)
    art_css = (".app { height: 100%; }\n@media (max-width: 899px) { .app { grid-template-rows: 58px 1fr auto auto; } "
               ".topbar { padding-top: 0; } .tabbar { padding-bottom: 6px; } }")
    art_img = ("<script>window.PACSI_ARTIFACT=true;window.PACSI_SPRITE=" + json.dumps(b64(ROOT / "img" / "sprite-thumbs.webp", "image/webp")) +
               ";window.PACSI_IMG=" + json.dumps(imgs) + hero_js + ";</script>")
    body = body.replace("/*INLINE_JS*/", js.replace("</script", "<\\/script")).replace("/*INLINE_DATA*/", data_json).replace("<!--INLINE_IMG-->", art_img)
    artifact = f"<title>Pacsi by DarwinAI</title>\n{fonts}\n<style>{css}\n{art_css}</style>\n{body}"
    (DIST / "pacsi-artifact.html").write_text(artifact, encoding="utf-8")

    size = lambda p: f"{p.stat().st_size / 1024 / 1024:.2f} MB"
    print(f"Pacsi v{app_ver} (build {build_id})")
    print(f"dist/pacsi.html  {size(DIST / 'pacsi.html')}")
    print(f"dist/pacsi-artifact.html  {size(DIST / 'pacsi-artifact.html')}")
    total = sum(p.stat().st_size for p in pwa.rglob('*') if p.is_file())
    print(f"dist/pwa/        {total / 1024 / 1024:.2f} MB, {len(files)} precache-elt fájl, sw v{version}")


if __name__ == "__main__":
    main()
