"""Nyitó ablak képe: a marketing „pacsi” kulcsképéből (ember keze + kabala mancsa) kivágott négyzet.

Használat:  python tools/make_hero.py
Forrás:     marketing/assets/kv/kv_pacsi_highfive.png (2048×2048, gpt-image-2)
Kimenet:    img/nyito-pacsi.webp (960×960) – az app kör alakban mutatja, a build beágyazza / a PWA-ba másolja.
"""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "marketing" / "assets" / "kv" / "kv_pacsi_highfive.png"
OUT = ROOT / "img" / "nyito-pacsi.webp"
CROP = (300, 420, 300 + 1640, 420 + 1640)   # a kéz és a mancs a kör bal felső negyedében találkozik


def main():
    im = Image.open(SRC).convert("RGB").crop(CROP).resize((960, 960), Image.LANCZOS)
    im.save(OUT, "WEBP", quality=80, method=6)
    print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
