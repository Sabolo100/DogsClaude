"""Pacsi partneri ajánlat (pitch deck) – build.

Használat:  python marketing/tools/build_pitch.py [--pdf] [--public]
Kimenet:
  marketing/pitch/dist/index.html       a léptethető webes prezentáció a claude.ai artifacthoz (privát példány)
  marketing/pitch/dist/assets/          optimalizált képek és rövid, néma videók
  marketing/pitch/Pacsi_partneri_ajanlat.pdf   (--pdf) tömörített PDF, diánként egy oldal
  marketing/pitch/public/               (--public) a nyilvános GitHub Pages-oldal teljes tartalma:
                                        index.html (linkelőnézettel, keresőktől elrejtve), assets/, PDF, og.jpg
A nyilvános oldal kitelepítése: python marketing/tools/deploy_pitch.py
"""
import hashlib, html as htmlmod, json, pathlib, shutil, subprocess, sys

from PIL import Image

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
P = MK / "pitch"
DIST = P / "dist"
A = DIST / "assets"

PUBLIC = P / "public"
PUBLIC_URL = "https://sabolo100.github.io/pacsi-partner/"
PDF_LINK = ('<a class="pdfl" href="Pacsi_partneri_ajanlat.pdf" download aria-label="PDF letöltése" title="PDF letöltése">'
            '<svg viewBox="0 0 24 24"><path d="M12 4v11m0 0-4.5-4.5M12 15l4.5-4.5M5 19h14"/></svg></a>')
OG_TITLE = "Pacsi – partneri ajánlat kutyás márkáknak"
OG_DESC = "Ahol a gazdi-lét elkezdődik: a Pacsi kutyafajta-választó és a partnerség lehetőségei. DarwinAI"

IMG = [  # (forrás, cél, max. szélesség)
    (MK / "assets/kv/kv_pacsi_highfive.png", "kv_highfive.webp", 1400),
    (MK / "assets/kv/kv_lineup.png", "kv_lineup.webp", 2400),
    (MK / "assets/kv/kv_mascot_wave.png", "kv_mascot.webp", 1000),
] + [(MK / f"assets/screens/{n}.png", f"{n}.webp", 780) for n in
     ["m_cloud", "m_filtered", "m_card_cavalier", "m_card_agar", "m_quiz_result", "m_compare", "m_map", "m_magyar", "m_tips"]] + \
    [(MK / f"assets/screens/{n}.png", f"{n}.webp", 1920) for n in ["d_rank", "d_card", "d_compare", "d_quiz", "d_map"]]
PORTRAITS = ["cavalier-king-charles-spaniel", "magyar-vizsla", "golden-retriever", "puli", "bichon-frise", "border-collie", "mopsz",
             "szamojed", "beagle", "whippet", "komondor", "shiba-inu", "mudi", "labrador-retriever", "havanese", "angol-agar",
             "francia-bulldog", "jack-russell-terrier", "bernathegyi", "kuvasz", "pumi", "uszkar", "dalmata", "basenji"]
VIDEOS = [  # (forrás, cél, kezdet, hossz) – néma, 540×960, a diákon végtelenítve
    ("v1_melyik_kutya_illik_hozzad.mp4", "v1.mp4", 0, 17.2),
    ("v2_milyen_gazdi_vagy.mp4", "v2.mp4", 0, 20.4),
    ("v3_9_magyar_kutyafajta.mp4", "v3.mp4", 0, 23.3),
    ("v4_zsebraketa_vagy_kanape_orias.mp4", "v4.mp4", 0, 18.4),
    ("v1_melyik_kutya_illik_hozzad.mp4", "demo_szures.mp4", 3.0, 5.0),
]
# a V1 videóban 2,75–8,1 mp között a telefon áll: ennek a képernyőjét vágjuk ki (valódi képernyőfelvétel-hatás)
CROP = {"demo_szures.mp4": "crop=632:1368:225:492,scale=468:1012:flags=lanczos"}


def webp(src, dst, w):
    im = Image.open(src).convert("RGB")
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(A / dst, "WEBP", quality=84, method=6)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # a Windows-konzol kódlapja nem ismer minden jelet
    A.mkdir(parents=True, exist_ok=True)
    for src, dst, w in IMG:
        if src.exists() and (not (A / dst).exists() or (A / dst).stat().st_mtime < src.stat().st_mtime):
            webp(src, dst, w)
    for pid in PORTRAITS:
        s = ROOT / "img" / "portrek" / f"{pid}.webp"
        if not (A / f"p_{pid}.webp").exists():
            shutil.copy(s, A / f"p_{pid}.webp")
    for src, dst, t0, dur in VIDEOS:
        s = MK / "out" / "videok" / src
        if not s.exists():
            print(f"  ! hiányzó videó: {src}")
            continue
        if (A / dst).exists() and (A / dst).stat().st_mtime > s.stat().st_mtime:
            continue
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t0), "-t", str(dur), "-i", str(s), "-an",
                            "-vf", CROP.get(dst, "scale=540:960:flags=lanczos"), "-c:v", "libx264", "-preset", "slow", "-crf", "27",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(A / dst)])
        if r.returncode:
            print(f"  ! a videó nem készült el (fut még a renderelés?): {src}")
            (A / dst).unlink(missing_ok=True)
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.2", "-i", str(A / dst), "-frames:v", "1",
                        "-q:v", "3", str(A / dst.replace(".mp4", "_poster.jpg"))], check=True)
        print(f"  videó: {dst} ({(A / dst).stat().st_size / 1e6:.1f} MB)")

    tpl = (P / "src" / "deck.html").read_text(encoding="utf-8")
    ver = (P / "VERSION").read_text(encoding="utf-8").strip()
    build = hashlib.sha1(tpl.encode("utf-8")).hexdigest()[:7]
    html = tpl.replace("{{VERSION}}", ver).replace("{{BUILD}}", build)
    pub_html = html.replace("<!--PDF_LINK-->", PDF_LINK)      # a nyilvános oldalon letölthető a PDF is
    html = html.replace("<!--PDF_LINK-->", "")                 # az artifact kerete nem enged letöltést
    (DIST / "index.html").write_text(html, encoding="utf-8")
    # teljes HTML-dokumentum a helyi megnyitáshoz / PDF-hez (a claude.ai a sajátját teszi köré)
    (DIST / "local.html").write_text('<!doctype html>\n<html lang="hu">\n<head>\n<meta charset="utf-8">\n' + html + "\n</html>\n", encoding="utf-8")
    size = sum(f.stat().st_size for f in A.iterdir())
    print(f"  deck kész: v{ver} · build {build} · assets {size / 1e6:.1f} MB ({len(list(A.iterdir()))} fájl)")
    if "--pdf" in sys.argv:
        # diaképek 1,5× felbontásban, majd JPEG-tömörítésű PDF (e-mailben is küldhető méret)
        subprocess.run(["node", str(MK / "tools" / "pdf_deck.mjs"), "--dpr", "1.5"], check=True, cwd=ROOT)
        pages = sorted((MK / "tmp" / "deck").glob("s*.png"))
        ims = [Image.open(p).convert("RGB") for p in pages]
        out = P / "Pacsi_partneri_ajanlat.pdf"
        ims[0].save(out, save_all=True, append_images=ims[1:], resolution=144, quality=84,
                    title="Pacsi – partneri ajánlat", author="DarwinAI")
        print(f"  PDF: {out.name} ({out.stat().st_size / 1e6:.1f} MB, {len(ims)} oldal)")
    if "--public" in sys.argv:
        public(pub_html, ver, build)


def public(page, ver, build):
    """A nyilvános GitHub Pages-oldal: teljes HTML-dokumentum linkelőnézettel, a keresőkből kizárva."""
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    shutil.copytree(A, PUBLIC / "assets")
    pdf = P / "Pacsi_partneri_ajanlat.pdf"
    if pdf.exists():
        shutil.copy(pdf, PUBLIC / pdf.name)
    shutil.copy(ROOT / "dist" / "pwa" / "icons" / "favicon-64.png", PUBLIC / "favicon.png")
    # linkelőnézeti kép a nyitó diából (1200×630)
    cover = MK / "tmp" / "deck" / "s01.png"
    if cover.exists():
        im = Image.open(cover).convert("RGB")
        im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
        top = (im.height - 630) // 2
        im.crop((0, top, 1200, top + 630)).save(PUBLIC / "og.jpg", quality=86)
    e = htmlmod.escape
    head = "\n".join([
        '<!doctype html>', '<html lang="hu">', '<head>', '<meta charset="utf-8">',
        '<meta name="robots" content="noindex, nofollow">',
        '<meta property="og:type" content="website">', '<meta property="og:locale" content="hu_HU">',
        f'<meta property="og:title" content="{e(OG_TITLE)}">', f'<meta property="og:description" content="{e(OG_DESC)}">',
        f'<meta property="og:url" content="{PUBLIC_URL}">', f'<meta property="og:image" content="{PUBLIC_URL}og.jpg">',
        '<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">', '<link rel="icon" href="favicon.png">', ''])
    (PUBLIC / "index.html").write_text(head + page + "\n</html>\n", encoding="utf-8")
    (PUBLIC / ".nojekyll").write_text("", encoding="utf-8")
    (PUBLIC / "README.md").write_text("\n".join([
        "# Pacsi – partneri ajánlat", "",
        f"Léptethető webes prezentáció kutyás márkáknak (v{ver}, build {build}).", "",
        f"- Élő oldal: {PUBLIC_URL}",
        "- Személyre szabás: a link végére `#p-Marka-Neve` (kötőjel = szóköz)",
        "- Pacsi by DarwinAI · www.darwinai.hu", "",
        "Ez a repó generált tartalom – a forrás a Pacsi projekt `marketing/pitch/` mappája.", ""]),
        encoding="utf-8")
    n = sum(1 for _ in PUBLIC.rglob("*") if _.is_file())
    size = sum(f.stat().st_size for f in PUBLIC.rglob("*") if f.is_file())
    print(f"  nyilvános oldal: marketing/pitch/public ({n} fájl, {size / 1e6:.1f} MB) → {PUBLIC_URL}")


if __name__ == "__main__":
    main()
