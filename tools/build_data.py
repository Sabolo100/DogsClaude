"""pacsi – fajta-adatbázis összeállítása.

Források:
  Pacsi_kutyavalaszto_specifikacio.md  7.3+7.7 (azonosítók), 7.4+7.8 (jellemvonások), 7.5+7.9 (tagline)
  data/fajtak_kep.json                 id, kanonikus név, háttérszín, sprite-sorrend
  data/content/part_*.json             kártyaszövegek (leírás, kinek ajánlott, egészség …)
Kimenet:
  data/fajtak.json
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = (ROOT / "Pacsi_kutyavalaszto_specifikacio.md").read_text(encoding="utf-8")
KEP = json.loads((ROOT / "data" / "fajtak_kep.json").read_text(encoding="utf-8"))

SIZE = {"toy": "toy", "kicsi": "kicsi", "közepes": "kozepes", "nagy": "nagy", "óriás": "orias"}
COAT = {"rövid": "rovid", "közepes": "kozepes", "hosszú": "hosszu", "drót": "drot", "göndör": "gondor", "zsinóros": "zsinoros", "szőrtelen": "szortelen"}
ROLE = {"CSA": "CSA", "VÁR": "VAR", "PÁS": "PAS", "ŐRZ": "ORZ", "VAD": "VAD", "SPO": "SPO", "MUN": "MUN", "ÉSZ": "ESZ"}
# Keresési szinonimák (becenevek, köznyelvi nevek)
SYN = {
    "nemet-dog": ["dán dog", "great dane", "dog"], "tacsko": ["borzeb", "dackel"], "magyar-vizsla": ["vizsla"],
    "labrador-retriever": ["labrador", "labi"], "golden-retriever": ["golden"], "francia-bulldog": ["frenchie", "francia bulldog"],
    "yorkshire-terrier": ["yorkie"], "staffordshire-bullterrier": ["staffi", "staffie"], "amerikai-staffordshire-terrier": ["amstaff"],
    "sziberiai-husky": ["husky"], "west-highland-white-terrier": ["westie"], "cavalier-king-charles-spaniel": ["cavalier"],
    "pomeraniai-torpespicc": ["pomi", "törpespicc"], "jack-russell-terrier": ["jack russell"], "nemet-boxer": ["boxer"],
    "ausztral-juhaszkutya": ["aussie"], "ausztral-pasztorkutya": ["cattle dog", "heeler"], "berni-pasztorkutya": ["berni"],
    "uszkar": ["pudli", "poodle", "törpe uszkár", "toy uszkár"], "chihuahua": ["csivava"], "mopsz": ["pug"],
    "drotszoru-foxterrier": ["foxi", "foxterrier"], "angol-agar": ["greyhound"], "collie": ["lassie"], "bobtail": ["óangol juhász"],
    "nemet-juhaszkutya": ["németjuhász", "schäfer"], "malinois": ["belga juhász"], "tervueren": ["belga juhász"],
    "groenendael": ["belga juhász"], "kinai-meztelen-kutya": ["chinese crested"], "papillon": ["pillangó"],
    "csau-csau": ["chow chow"], "shar-pei": ["sharpei"], "csehszlovak-farkaskutya": ["farkaskutya", "cseh farkaskutya"],
    "ir-buzaszinu-terrier": ["wheaten"], "nemet-vadaszterrier": ["jagdterrier"], "drotszoru-nemet-vizsla": ["drahthaar"],
    "rovidszoru-nemet-vizsla": ["kurzhaar"], "bretagne-i-spaniel": ["breton"], "nova-scotia-retriever": ["toller"],
    "keeshond": ["wolfspitz"], "bloodhound": ["szent hubertus"], "spanyol-galgo": ["galgo"],
}


def section(title_prefix):
    m = re.search(rf"^### {re.escape(title_prefix)}.*?$(.*?)(?=^### |\Z)", SPEC, flags=re.M | re.S)
    if not m:
        sys.exit(f"nem található szakasz: {title_prefix}")
    return m.group(1)


def rows(text):
    out = []
    for line in text.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|(.*)\|\s*$", line)
        if m:
            out.append((int(m.group(1)), [c.strip() for c in m.group(2).split("|")]))
    return out


def rng(s):
    a, b = re.split(r"[–-]", s.replace(",", "."))
    return [float(a) if "." in a else int(a), float(b) if "." in b else int(b)]


def main():
    ident = {n: c for sec in ("7.3", "7.7") for n, c in rows(section(sec))}
    traits = {n: c for sec in ("7.4", "7.8") for n, c in rows(section(sec))}
    tags = {n: c for sec in ("7.5", "7.9") for n, c in rows(section(sec))}
    content = {}
    for p in sorted((ROOT / "data" / "content").glob("part_*.json")):
        content.update(json.loads(p.read_text(encoding="utf-8")))

    breeds, spares = [], []
    for k in sorted(KEP["fajtak"], key=lambda e: e["slot"]):
        base = {"id": k["id"], "nev": k["nev"], "bg": KEP["paletta"][k["bg"]], "sprite": k["slot"] - 1}
        if k.get("spare"):
            spares.append(base); continue
        n = base["n"] = k["n"]
        _, en, fci, meret, suly, elet, szor, szerep, orszag, jel, nep = ident[n]
        t = traits[n][1:]
        b = dict(base)
        b.update({
            "en": en,
            "fci": int(fci),
            "meret": [SIZE[x.strip().lower()] for x in meret.split(",")],
            "suly": rng(suly),
            "elet": rng(elet),
            "szor": [COAT[x.strip().lower()] for x in szor.split("/")],
            "szerep": [ROLE[x.strip()] for x in szerep.split(",")],
            "orszag": orszag,
            "hu": "🇭🇺" in jel,
            "brachy": (1 if "enyhe" in jel else 2) if "😮‍💨" in jel else 0,
            "korl": "⚖️" in jel,
            "nyal": "💧" in jel,
            "nep": nep.count("★"),
            "t": dict(zip(["E", "Gy", "I", "U", "H", "A", "L", "K", "O"], [int(re.sub(r"\D", "", v)) for v in t])),
            "vonyit": "*" in t[3],
            "tagline": tags[n][1],
            "syn": SYN.get(k["id"], []),
        })
        c = content.get(k["id"])
        if c:
            b.update({f: c[f] for f in ("leiras", "kinekIgen", "kinekNem", "mozgas", "egeszseg", "erdekesseg",
                                         "hasonlo", "marmagassag", "koltseg") if f in c})
        else:
            print(f"  ! nincs tartalom: {k['id']}")
        breeds.append(b)

    ids = {b["id"] for b in breeds}
    for b in breeds:
        bad = [h for h in b.get("hasonlo", []) if h not in ids or h == b["id"]]
        if bad:
            print(f"  ! hibás hasonló-id ({b['id']}): {bad}")
            b["hasonlo"] = [h for h in b["hasonlo"] if h not in bad]
    breeds.sort(key=lambda b: b["n"])
    out = {"breeds": breeds, "spares": spares, "spriteRows": (len(KEP["fajtak"]) + 7) // 8}
    (ROOT / "data" / "fajtak.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"fajtak.json: {len(breeds)} fajta, {len(spares)} tartalék, tartalommal: {sum(1 for b in breeds if 'leiras' in b)}")


if __name__ == "__main__":
    main()
