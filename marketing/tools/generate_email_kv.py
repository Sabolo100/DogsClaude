"""Pacsi eDM – szezonális kulcsvizuálok a hírlevelekhez (OpenAI gpt-image-2), a portrékkal azonos gouache stílusban.

Használat:  python marketing/tools/generate_email_kv.py [név …]
Kimenet:    marketing/assets/kv/<név>.png (+ _prompt.txt)

A levelekben ezekből 1200×600-as (2:1) fejléckép készül (email_build.py). A Mailchimp képkorlátja miatt
a kész levélkép sosem nagyobb 1200×1200 px-nél. A kulcs az OpenAI_API.txt-ből jön, sosem kerül kimenetbe.
"""
import concurrent.futures as cf
import sys
import time
import urllib.error

import generate_keyvisuals as G

SIZE = "2048x1024"
WIDE = ("Wide 2:1 composition. Keep the main subjects inside the central 80 percent of the width so the picture can be "
        "cropped slightly at the sides. ")

JOBS = {
    # W02 – hosszú hétvége, őszi túra
    "ekv_osz_tura": (SIZE, f"{G.STYLE} {WIDE}An autumn forest hiking trail in the Hungarian hills in soft morning light, golden, "
        "rust and amber leaves on the ground and gently falling. A happy Hungarian Vizsla (short golden-rust coat) and "
        f"{G.MASCOT} trot side by side along the path toward the viewer, both on loose leashes held by an unseen walker "
        "outside the frame. Birch and beech trees, a soft misty background, warm cream sky. Joyful, calm, outdoorsy."),
    # W03 – Halloween: jelmez igen, csoki nem
    "ekv_halloween": (SIZE, f"{G.STYLE} {WIDE}A cosy, playful (not scary) Halloween scene on a plain warm cream background "
        "(#FBF6EE): three dogs sit side by side in harmless, loose homemade costumes next to carved smiling pumpkins: a "
        "Dachshund dressed as a hot dog in a soft bun costume, a French Bulldog with small felt bat wings, and "
        f"{G.MASCOT} wearing a tiny purple witch hat. Candle-lit paper lanterns, a few autumn leaves. A bowl of wrapped "
        "sweets sits high up on a shelf in the background, clearly out of the dogs' reach."),
    # W04 – sötétedik: láthatóság séta közben
    "ekv_sotet_seta": (SIZE, f"{G.STYLE} {WIDE}An evening dog walk at dusk on a quiet Hungarian town street with warm "
        f"streetlights and wet pavement reflections, a few autumn leaves. {G.MASCOT[0].upper() + G.MASCOT[1:]} trots on a "
        "leash wearing a softly glowing LED collar and a small reflective safety vest; only the walker's legs in dark "
        "trousers with a bright reflective ankle band are visible. Deep blue dusk sky with warm orange light accents. "
        "Cosy, safe, reassuring mood."),
    # W06 – örökbefogadás
    "ekv_orokbefogadas": (SIZE, f"{G.STYLE} {WIDE}A warm, hopeful adoption moment in the sunny yard of a small, clean animal "
        "shelter: a gentle medium-sized mixed-breed dog with a brindle coat and soft ears sits and offers its paw to a "
        "kneeling young person seen from the side (casual oat-coloured sweater), whose open hand meets the paw. Other "
        "shelter dogs watch curiously from behind a simple wooden fence. Soft autumn light, trees, heartwarming and "
        "optimistic, not sad."),
    # W08 – Mikulás: kutyabarát csizma
    "ekv_mikulas": (SIZE, f"{G.STYLE} {WIDE}Hungarian St. Nicholas (Mikulás) morning: a pair of shiny polished children's "
        "boots stands on a snowy-looking windowsill, filled with dog-safe treats (carrot sticks, apple slices, a rope chew "
        f"toy, bone-shaped biscuits) instead of chocolate. {G.MASCOT[0].upper() + G.MASCOT[1:]}, wearing a small red Santa "
        "hat, peeks at the boots curiously with its nose close to them. Soft winter light through the window, frosty glass, "
        "warm cream wall, a sprig of fir."),
    # W09 – kutyát karácsonyra? Előbb gondold át
    "ekv_ajandek": (SIZE, f"{G.STYLE} {WIDE}A calm, thoughtful Christmas scene on a warm cream background: a puppy sits "
        "NEXT TO (not inside) a big wrapped gift box with a coral ribbon, looking up with big honest eyes. Beside the box: a "
        "neatly coiled leash, a small food bowl, a soft round dog bed and a chew toy, as if everything must be ready before "
        "a dog arrives. Fir branches and warm fairy lights in the background. Cosy, sincere, responsible mood."),
    # W10 + W12 – szilveszter: biztonságos búvóhely
    "ekv_szilveszter": (SIZE, f"{G.STYLE} {WIDE}New Year's Eve, a safe calm den for a dog: a relaxed Border Collie rests "
        "inside a cosy covered crate draped with a thick knitted blanket, next to a warm table lamp, a water bowl and a chew "
        "toy, with a soft white-noise speaker on the floor. In the background a window with heavy curtains partly drawn, "
        "colourful fireworks visible far away in the night sky. The room is warm and quiet, the dog feels safe."),
    # W11 – ünnepi falka
    "ekv_unnep": (SIZE, f"{G.STYLE} {WIDE}A joyful winter holiday lineup on a warm cream background with gentle falling "
        "snow: five dogs sit in a row wearing cosy knitted scarves in coral, mustard and teal: a Hungarian Vizsla (short "
        "golden-rust coat), a Golden Retriever, a Hungarian Puli (black corded coat), a French Bulldog, and in the centre "
        f"{G.MASCOT}. A small decorated fir tree with warm lights and a few wrapped presents beside them. Festive, warm, happy."),
}


def run(name):
    size, prompt = JOBS[name]
    t = time.time()
    try:
        img = G.call(prompt, size)
    except urllib.error.HTTPError as e:
        return f"{name}: HTTP {e.code} {e.read().decode(errors='ignore')[:300]}"
    except Exception as e:  # noqa: BLE001
        return f"{name}: {e}"
    (G.OUT / f"{name}.png").write_bytes(img)
    (G.OUT / f"{name}_prompt.txt").write_text(f"{size}\n\n{prompt}\n", encoding="utf-8")
    return f"{name}: OK {size} {len(img) // 1024} KB {time.time() - t:.0f}s"


if __name__ == "__main__":
    G.OUT.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or [n for n in JOBS if not (G.OUT / f"{n}.png").exists()]
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(run, names):
            print(r, flush=True)
