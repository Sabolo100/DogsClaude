"""pacsi – fajtaportrék generálása OpenAI képmodellel.

Használat:
  python tools/generate_sheets.py sheets 1 2 … 8     # 4x4-es rácsképek (16 portré / kép, slot szerint)
  python tools/generate_sheets.py egyedi mudi pumi    # egyedi újragenerálás (1 fajta / kép)

A kulcsot az OpenAI_API.txt-ből olvassa. SOHA ne kerüljön a kliens HTML-be.
"""
import base64, json, pathlib, sys, time, urllib.error, urllib.request
import concurrent.futures as cf

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "fajtak_kep.json").read_text(encoding="utf-8"))
PAL = DATA["paletta"]
BREEDS = sorted(DATA["fajtak"], key=lambda b: b["slot"])
MODEL = "gpt-image-2"
COLOR_NAMES = {"barack": "peach", "vaj": "butter yellow", "menta": "mint green", "egkek": "sky blue",
               "levendula": "lavender", "rozsa": "rose pink", "zsalya": "sage green", "homok": "sand beige",
               "korall": "light coral", "pisztacia": "pistachio green"}

STYLE = (
    "painterly gouache illustration portrait: head and upper chest, three-quarter view, friendly expression, "
    "centered. Consistent soft lighting from the upper left, subtle paper grain, visible soft brush strokes, "
    "warm premium children's-book-meets-editorial style. Breed-accurate coat color, coat texture, ear shape and "
    "head proportions. No collars or accessories unless stated, no humans, no text."
)


def key():
    return (ROOT / "OpenAI_API.txt").read_text(encoding="utf-8").strip().split()[0]


def call(prompt, size):
    body = json.dumps({"model": MODEL, "prompt": prompt, "size": size, "quality": "high", "n": 1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body,
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return base64.b64decode(json.load(r)["data"][0]["b64_json"])


def generate(name, prompt, sizes, out):
    for size in sizes:
        t = time.time()
        try:
            img = call(prompt, size)
            out.write_bytes(img)
            return f"{name}: OK {size} {len(img) // 1024} KB {time.time() - t:.0f}s"
        except urllib.error.HTTPError as e:
            print(f"{name}: {size} -> HTTP {e.code} {e.read().decode(errors='ignore')[:200]}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{name}: {size} -> {e}", flush=True)
    return f"{name}: FAILED"


def sheet_prompt(idx):
    tiles = BREEDS[(idx - 1) * 16: idx * 16]
    lines = []
    for i, b in enumerate(tiles):
        if i % 4 == 0:
            lines.append(f"Row {i // 4 + 1}:")
        lines.append(f"  Tile {i + 1}: {b['en']} - {b['desc']}. Tile background: flat {COLOR_NAMES[b['bg']]} {PAL[b['bg']]}.")
    return (
        "A 4x4 grid of 16 separate square illustration tiles on a plain cream (#FBF6EE) canvas. The tiles are "
        "perfectly aligned in exactly 4 rows and 4 columns, all exactly the same size, separated by thin even cream "
        "gutters (about 2% of the image width) with the same cream margin around the outside. No borders, no frames, "
        "no text, no letters, no numbers, no labels anywhere in the image.\n\n"
        "Each tile is filled edge-to-edge with ONE flat solid pastel background color (given below) and shows ONE dog "
        f"as a {STYLE} The whole head including the ears must fit inside a centered circle covering about 80% of the "
        "tile - keep the tile corners and edges as clear background, because every tile will be cropped to a circle. "
        "Same scale and framing in every tile.\n\n"
        "Tiles in reading order (left to right, top to bottom):\n" + "\n".join(lines)
    )


def single_prompt(b):
    return (
        f"A single square illustration: {b['en']} - {b['desc']}. A {STYLE} The tile is filled edge-to-edge with a "
        f"flat solid {COLOR_NAMES[b['bg']]} {PAL[b['bg']]} background. The whole head including the ears fits inside a "
        "centered circle covering about 80% of the image; corners are clear background because it will be cropped to "
        "a circle. No border, no text."
    )


if __name__ == "__main__":
    mode, args = sys.argv[1], sys.argv[2:]
    jobs = []
    if mode == "sheets":
        outdir = ROOT / "img" / "sheets"
        outdir.mkdir(parents=True, exist_ok=True)
        for a in args:
            i = int(a)
            (outdir / f"sheet_{i}_prompt.txt").write_text(sheet_prompt(i), encoding="utf-8")
            # gpt-image-2: max ~4,2 MP pixelkeret -> 2048x2048 a legnagyobb négyzetes méret
            jobs.append((f"sheet_{i}", sheet_prompt(i), ["2048x2048", "1536x1536", "1024x1024"],
                         outdir / f"sheet_{i}.png"))
    elif mode == "egyedi":
        outdir = ROOT / "img" / "egyedi"
        outdir.mkdir(parents=True, exist_ok=True)
        by_id = {b["id"]: b for b in BREEDS}
        for a in args:
            jobs.append((a, single_prompt(by_id[a]), ["1024x1024"], outdir / f"{a}.png"))
    with cf.ThreadPoolExecutor(max_workers=max(1, len(jobs))) as ex:
        for r in cf.as_completed([ex.submit(generate, *j) for j in jobs]):
            print(r.result(), flush=True)
