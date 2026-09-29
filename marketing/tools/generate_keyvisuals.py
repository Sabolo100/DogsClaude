"""Pacsi Marketing – kulcsvizuálok generálása (OpenAI gpt-image-2), a fajtaportrékkal azonos gouache stílusban.

Használat:  python marketing/tools/generate_keyvisuals.py [név …]
Kimenet:    marketing/assets/kv/<név>.png

A kulcsot a repó gyökerében lévő OpenAI_API.txt-ből olvassa. SOHA ne kerüljön kliens HTML-be.
"""
import base64, json, pathlib, sys, time, urllib.error, urllib.request
import concurrent.futures as cf

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "marketing" / "assets" / "kv"
MODEL = "gpt-image-2"

STYLE = ("Painterly gouache illustration in a warm premium children's-book-meets-editorial style: subtle paper grain, "
         "visible soft brush strokes, consistent soft lighting from the upper left, breed-accurate coats and proportions. "
         "No text, no letters, no numbers, no logos, no watermark anywhere in the image.")
MASCOT = ("the Pacsi mascot: a fluffy, scruffy mixed-breed puppy with a cream-white wavy coat and warm ginger patches on the "
          "floppy ears and around the eyes, big shiny dark eyes, black nose, a happy open mouth with a pink tongue, wearing a "
          "coral-orange bandana (#EE5A2C) with a tiny white flower pattern")

JOBS = {
    "kv_pacsi_highfive": ("2048x2048",
        f"{STYLE} {MASCOT[0].upper() + MASCOT[1:]} sits on the right half of the picture and raises one front paw, paw pad "
        "visible, to give a high five to a human hand that enters from the left edge (only a relaxed open palm and part of "
        "the forearm with a simple oat-coloured knitted sleeve, warm natural skin tone). The paw and the palm are just about "
        "to touch slightly right of the centre, a tiny joyful moment. Plain flat cream background (#FBF6EE) filling the whole "
        "image, generous empty space in the top third for a headline, a soft warm shadow under the puppy."),
    "kv_lineup": ("3456x1152",
        f"{STYLE} A cheerful lineup of thirteen different dogs sitting side by side in a single row on a plain flat cream "
        "background (#FBF6EE), full bodies, facing the viewer, happy and relaxed, soft warm contact shadows on the ground, "
        "true relative sizes so the row forms a gentle wave from small to large. From left to right: Chihuahua, Jack Russell "
        "Terrier, French Bulldog, Beagle, Hungarian Puli (black coat of long corded dreadlocks), Border Collie, "
        f"in the exact centre {MASCOT}, Golden Retriever, Hungarian Vizsla (short golden-rust coat), Bernese Mountain Dog, "
        "Hungarian Komondor (ivory white corded coat), Cavalier King Charles Spaniel (Blenheim), Samoyed. "
        "The dogs occupy the middle 70 percent of the height, leaving clear cream space above and below."),
    "kv_mascot_wave": ("1536x2048",
        f"{STYLE} Full-body portrait of {MASCOT}, sitting upright on the ground, front view, tilting its head playfully and "
        "raising its right front paw high as if waving hello or offering a high five, paw pad visible. Plain flat cream "
        "background (#FBF6EE) filling the whole image, the puppy centred in the lower two thirds, a soft warm shadow "
        "under it, lots of empty space above its head."),
}


def key():
    return (ROOT / "OpenAI_API.txt").read_text(encoding="utf-8").strip().split()[0]


def call(prompt, size):
    body = json.dumps({"model": MODEL, "prompt": prompt, "size": size, "quality": "high", "n": 1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body,
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return base64.b64decode(json.load(r)["data"][0]["b64_json"])


def run(name):
    size, prompt = JOBS[name]
    t = time.time()
    try:
        img = call(prompt, size)
    except urllib.error.HTTPError as e:
        return f"{name}: HTTP {e.code} {e.read().decode(errors='ignore')[:300]}"
    except Exception as e:  # noqa: BLE001
        return f"{name}: {e}"
    (OUT / f"{name}.png").write_bytes(img)
    (OUT / f"{name}_prompt.txt").write_text(f"{size}\n\n{prompt}\n", encoding="utf-8")
    return f"{name}: OK {size} {len(img) // 1024} KB {time.time() - t:.0f}s"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(JOBS)
    with cf.ThreadPoolExecutor(3) as ex:
        for r in ex.map(run, names):
            print(r, flush=True)
