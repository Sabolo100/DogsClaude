"""pacsi – rácsképek szeletelése portrékká.

Kimenet:
  img/portrek/<id>.webp     a csempe natív mérete (max. 768 px, jelenleg ~460–480 px), a kártyákhoz
  img/thumbs/<id>.webp      256 px, a buborékokhoz
  img/sprite-thumbs.webp    8 oszlopos, 256 px-es sprite (sorrend: slot)
  img/kontaktlap.png        feliratozott áttekintő (QA)
  data/sprite_index.json    id -> sprite pozíció

Ha létezik img/egyedi/<id>.png (újragenerált cella), az felülírja a rácsból vágott képet.
"""
import json, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "fajtak_kep.json").read_text(encoding="utf-8"))
BREEDS = sorted(DATA["fajtak"], key=lambda b: b["slot"])
SHEETS = (len(BREEDS) + 15) // 16
SP_ROWS = (len(BREEDS) + 7) // 8
CREAM = np.array([0xFB, 0xF6, 0xEE])
BIG, THUMB = 768, 256
# Sheetenkénti belső margó (a csempe szélének antialiasát vágja le). A 2–3. sheet kettős
# háttérárnyalatát a flatten_ring() egységesíti.
INSET = {1: 0.035, 2: 0.03, 3: 0.03, 4: 0.015}  # az új sheetek alapértéke 0.03


def flatten_ring(tile):
    """A 2–3. sheet csempéin a négyzetes háttér és a belső, halványabb kör két árnyalata
    kettős gyűrűt adna a buborékon. A külső árnyalatot a belsőre toljuk (a papírtextúra
    megmarad): minden pixelt, amely a külső→belső színszakaszon fekszik, a belső szín felé
    eltolunk – csak a kép külső részén, ahol a kutya már nem jellemző."""
    a = np.asarray(tile).astype(float)
    s = a.shape[0]
    p = max(4, s // 20)
    outer = np.median(np.concatenate([a[:p, :p].reshape(-1, 3), a[:p, -p:].reshape(-1, 3)]), axis=0)
    yy, xx = np.mgrid[:s, :s]
    r = np.hypot(xx - s / 2, yy - s / 2) / (s / 2)
    ann = a[(r > 0.80) & (r < 0.95)]
    q = (ann // 12).astype(int)
    keys, counts = np.unique(q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2], return_counts=True)

    def chroma_dir(c):
        v = c - c.mean()
        return v / (np.linalg.norm(v) + 1e-6)

    inner = None
    for k in keys[np.argsort(-counts)][:12]:
        c = ann[(q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]) == k].mean(axis=0)
        dist = np.linalg.norm(c - outer)
        # a belső árnyalat a külső közeli rokona: hasonló színezet, 10–45 egység távolság,
        # és nem szürkés/fehér (különben fehér szőrt vennénk háttérnek)
        if 10 < dist < 45 and c.max() - c.min() > 20 and chroma_dir(c) @ chroma_dir(outer) > 0.85:
            inner = c; break
    if inner is None or np.linalg.norm(outer - inner) < 10:
        return tile
    d = outer - inner
    t = ((a - inner) @ d) / (d @ d)
    perp = np.linalg.norm(a - inner - t[..., None] * d, axis=2)
    sel = (r > 0.62) & (perp < 14) & (t > 0.05)
    a[sel] -= np.clip(t[sel], 0, 1.2)[:, None] * d
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def split4(profile, thr, min_run):
    """Egy tengely mentén 4 csempét keres: a kitöltött futamok közötti rések közül azt a
    hármat választja ki, amelyik a várható határokhoz (1/4, 2/4, 3/4) a legközelebb esik
    (±12%). A többi rés – pl. fehér szőr okozta lyuk – nem számít határnak.
    Ha egy határnál nincs rés (összeérő csempék), a várható pozíciót használja."""
    n = len(profile)
    filled = profile > thr
    runs, start = [], None
    for i, v in enumerate(filled):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i)); start = None
    if start is not None:
        runs.append((start, n))
    runs = [r for r in runs if r[1] - r[0] >= min_run]
    if not runs:
        return [(n * i // 4, n * (i + 1) // 4) for i in range(4)]
    gaps = [(runs[i][1], runs[i + 1][0]) for i in range(len(runs) - 1)]
    bounds = [runs[0][0]]
    for k in (1, 2, 3):
        exp = n * k / 4
        cands = [g for g in gaps if abs((g[0] + g[1]) / 2 - exp) < n * 0.12]
        if cands:
            g = min(cands, key=lambda g: abs((g[0] + g[1]) / 2 - exp))
            bounds += [g[0], g[1]]
        else:
            bounds += [int(exp), int(exp)]
    bounds.append(runs[-1][1])
    return [(bounds[2 * i], bounds[2 * i + 1]) for i in range(4)]


def tile_boxes(img, cy_ratio=0.5):
    """Megkeresi a 4x4 csempét a krémszínű rések alapján: előbb a sorsávokat, majd
    soronként – a sáv középső csíkjában mérve, hogy az alul kilógó mellkas ne zavarjon –
    a 4 csempe vízszintes határait. Az 1. sheet oválisai nem egyenletes rácson ülnek,
    ezért nem lehet egyszerű 4x4 felosztással vágni.
    Visszaad: (cx, cy, oldal) csempénként."""
    a = np.asarray(img.convert("RGB")).astype(int)
    mask = np.abs(a - CREAM).sum(axis=2) > 30
    h, w = mask.shape
    out = []
    for (y0, y1) in split4(mask.mean(axis=1), 0.35, h // 10):
        bh = y1 - y0
        mid = (y0 + y1) // 2
        strip = mask[mid - bh // 10: mid + bh // 10]
        for (x0, x1) in split4(strip.mean(axis=0), 0.5, 12):
            side = min(x1 - x0, bh)
            out.append(((x0 + x1) / 2, y0 + side * cy_ratio, side))
    return out


def square(img, box, inset=0.02):
    cx, cy, side = box
    side = int(round(side * (1 - 2 * inset)))
    x0, y0 = int(round(cx - side / 2)), int(round(cy - side / 2))
    return img.crop((x0, y0, x0 + side, y0 + side))


def main():
    for d in ("portrek", "thumbs"):
        (ROOT / "img" / d).mkdir(parents=True, exist_ok=True)
    tiles = {}
    for s in range(1, SHEETS + 1):
        p = ROOT / "img" / "sheets" / f"sheet_{s}.png"
        if not p.exists():
            print(f"hiányzik: {p.name}"); continue
        img = Image.open(p).convert("RGB")
        boxes = tile_boxes(img, 0.53 if s == 1 else 0.5)
        print(f"sheet_{s}: {img.size}, csempe ~{int(boxes[0][2])} px")
        for i, box in enumerate(boxes):
            n = (s - 1) * 16 + i + 1
            t = square(img, box, INSET.get(s, 0.03))
            tiles[n] = flatten_ring(t) if s != 1 else t
    for b in BREEDS:
        eg = ROOT / "img" / "egyedi" / f"{b['id']}.png"
        if eg.exists():
            e = Image.open(eg).convert("RGB")
            tiles[b["slot"]] = square(e, (e.size[0] / 2, e.size[1] / 2, min(e.size)), inset=0.01)
            print(f"  egyedi kép: {b['id']}")

    sprite = Image.new("RGB", (8 * THUMB, SP_ROWS * THUMB), tuple(CREAM))
    index = {}
    for b in BREEDS:
        t = tiles.get(b["slot"])
        if t is None:
            continue
        big = min(BIG, t.size[0])  # nem nagyítunk fel
        t.resize((big, big), Image.LANCZOS).save(ROOT / "img" / "portrek" / f"{b['id']}.webp", quality=82, method=6)
        th = t.resize((THUMB, THUMB), Image.LANCZOS)
        th.save(ROOT / "img" / "thumbs" / f"{b['id']}.webp", quality=80, method=6)
        i = b["slot"] - 1
        sprite.paste(th, ((i % 8) * THUMB, (i // 8) * THUMB))
        index[b["id"]] = {"i": i, "x": (i % 8) * THUMB, "y": (i // 8) * THUMB}
    sprite.save(ROOT / "img" / "sprite-thumbs.webp", quality=80, method=6)
    (ROOT / "data" / "sprite_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

    # Kontaktlap: kör alakú vágás + név, 8 oszlop
    cell, pad, lab = 220, 24, 46
    cols = 8
    rows = (len(BREEDS) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad + lab) + pad + 70), tuple(CREAM))
    d = ImageDraw.Draw(sheet)
    fdir = pathlib.Path("C:/Windows/Fonts")
    f_title = ImageFont.truetype(str(fdir / "georgiab.ttf"), 40)
    f_name = ImageFont.truetype(str(fdir / "seguisb.ttf"), 17)
    f_num = ImageFont.truetype(str(fdir / "segoeui.ttf"), 14)
    d.text((pad, 18), f"pacsi · {sum(1 for b in BREEDS if not b.get('spare'))} fajta + {sum(1 for b in BREEDS if b.get('spare'))} tartalék portré", fill=(30, 27, 24), font=f_title)
    circ = Image.new("L", (cell * 4, cell * 4), 0)
    ImageDraw.Draw(circ).ellipse((0, 0, cell * 4 - 1, cell * 4 - 1), fill=255)
    circ = circ.resize((cell, cell), Image.LANCZOS)
    for b in BREEDS:
        t = tiles.get(b["slot"])
        i = b["slot"] - 1
        x = pad + (i % cols) * (cell + pad)
        y = 70 + pad + (i // cols) * (cell + pad + lab)
        if t is not None:
            sheet.paste(t.resize((cell, cell), Image.LANCZOS), (x, y), circ)
            d.ellipse((x, y, x + cell - 1, y + cell - 1), outline=(255, 255, 255), width=4)
        name = b["nev"] if len(b["nev"]) <= 24 else b["nev"][:23] + "…"
        tw = d.textlength(name, font=f_name)
        d.text((x + (cell - tw) / 2, y + cell + 6), name, fill=(30, 27, 24), font=f_name)
        d.text((x + 4, y + 2), str(b.get("n", "·")), fill=(107, 98, 90), font=f_num)
    sheet.save(ROOT / "img" / "kontaktlap.png", optimize=True)
    print(f"kész: {len(index)} portré, sprite, kontaktlap")


if __name__ == "__main__":
    main()
