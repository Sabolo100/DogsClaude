"""LinkedIn-karusszel (Vibe Coding use case) – build.

Használat:  python marketing/tools/build_linkedin.py [--shots] [--dpr 2]
  --shots   friss képernyőképek: a CMS fülei, a pitch deck diái, három hírlevél (marketing/linkedin/shots/)
Kimenet:
  marketing/linkedin/pages/pNN.jpg                       oldalképek (1080×1350 × dpr)
  marketing/linkedin/Pacsi_vibe_coding_karusszel.pdf     a LinkedIn-dokumentumposzthoz csatolható PDF
A forrás: marketing/linkedin/src/carousel.html (böngészőben is megnyitható előnézetként).
Két menetben renderel: a +1 oldal az első menet oldalképeit mutatja bélyegképként.
"""
import hashlib, pathlib, shutil, subprocess, sys

from PIL import Image

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
LI = MK / "linkedin"
SHOTS = LI / "shots"
PAGES = LI / "pages"
TMP = MK / "tmp" / "linkedin"
PDF = LI / "Pacsi_vibe_coding_karusszel.pdf"
NODE = ["node", str(MK / "tools" / "linkedin_carousel.mjs")]


def build_id():
    h = hashlib.sha1()
    for p in [LI / "src" / "carousel.html", *sorted(SHOTS.glob("*.png"))]:
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()[:7]


def render(q, dpr):
    subprocess.run([*NODE, "pages", "--dpr", str(dpr), "--q", q], check=True, cwd=ROOT)
    PAGES.mkdir(exist_ok=True)
    for p in PAGES.glob("p*.jpg"):
        p.unlink()
    out = []
    for png in sorted(TMP.glob("p*.png")):
        jpg = PAGES / (png.stem + ".jpg")
        Image.open(png).convert("RGB").save(jpg, quality=90, optimize=True, progressive=True)
        out.append(jpg)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dpr = float(sys.argv[sys.argv.index("--dpr") + 1]) if "--dpr" in sys.argv else 2
    if "--shots" in sys.argv or not any(SHOTS.glob("deck_*.png")):
        subprocess.run([*NODE, "shots"], check=True, cwd=ROOT)
    ver = (LI / "VERSION").read_text(encoding="utf-8").strip()
    build = build_id()
    q = f"ver={ver}&build={build}"
    render(q, dpr)            # 1. menet – ebből lesznek a +1 oldal bélyegképei
    pages = render(q, dpr)    # 2. menet – a végleges oldalak
    ims = [Image.open(p).convert("RGB") for p in pages]
    ims[0].save(PDF, save_all=True, append_images=ims[1:], resolution=72 * dpr, quality=90,
                title="Amikor egy weboldal intézi a saját kommunikációját – Pacsi, Vibe Coding use case",
                author="DarwinAI", subject=f"LinkedIn-karusszel v{ver} (build {build})")
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"  karusszel v{ver} · build {build}: {PDF.relative_to(ROOT)} ({PDF.stat().st_size / 1e6:.1f} MB, {len(ims)} oldal)")


if __name__ == "__main__":
    main()
