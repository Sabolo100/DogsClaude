"""Pacsi – nyelvek kezelése: szövegek kinyerése, fordítás beolvasása, ellenőrzés, csomag az apphoz.

A forrásnyelv a magyar. Egy új nyelv (pl. német) hozzáadása:
  1. data/i18n/languages.json: új sor (kód, név, zászló-azonosító); src/flags/<flag>.svg: a zászló.
  2. python tools/i18n.py extract de        → munkacsomagok a scratch/ mappába (JSON-darabok + PROMPT.md)
  3. a darabok lefordítása (Claude Code-dal vagy:  python tools/i18n.py translate de --provider anthropic)
  4. python tools/i18n.py merge de <kimenet-fájlok>   → beírja a data/i18n/de/ fájlokba
  5. python tools/i18n.py check de          → hiányzó / hibás / elavult fordítások
A build (tools/build.py) a bundle()-t hívja: minden nyelv egy csomagban kerül az appba, a hiányzó szöveg magyarul jelenik meg.

Fájlok (data/i18n/):
  languages.json                  a támogatott nyelvek listája (a menü sorrendje)
  hu/ui.json                      a felület magyar szövegei (kulcs → szöveg) – EZ a forrás, kézzel szerkesztve
  <nyelv>/ui.json                 ugyanezek lefordítva
  <nyelv>/content.json            fajtaszövegek (a magyarok a data/fajtak.json-ból jönnek): "<id>.leiras" → szöveg
  <nyelv>/aliases.json            további keresőszavak fajtánként (nem fordítás, kézzel)
  <nyelv>/glossary.json           stílus + szakszavak a fordítóknak (a PROMPT.md-be kerül)
  <nyelv>/_src.json               melyik magyar szövegből készült a fordítás (hash) – ebből látszik, ha a magyar megváltozott
"""
import argparse, hashlib, json, os, pathlib, re, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
I18N = ROOT / "data" / "i18n"
SRC = "hu"
TEXT_F = ["tagline", "leiras", "mozgas", "erdekesseg"]          # fajtánként egy szöveg
LIST_F = ["kinekIgen", "kinekNem", "egeszseg"]                  # fajtánként szöveglista
CTX = {"nev": "breed name", "tagline": "one-line tagline on the breed card", "leiras": "breed description paragraph",
       "mozgas": "daily exercise note", "erdekesseg": "fun fact ('Did you know?')",
       "kinekIgen": "'Who is it for?' bullet", "kinekNem": "'Who is it NOT for?' bullet",
       "egeszseg": "health issue bullet (veterinary term)", "country": "country / region of origin"}
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def rj(path, default=None):
    p = pathlib.Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else ({} if default is None else default)


def wj(path, obj):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n", encoding="utf-8")


def h8(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]


def languages():
    return rj(I18N / "languages.json", [])


# ---------------------------------------------------------------- források (magyar)
def breeds():
    f = ROOT / "data" / "fajtak.json"
    if not f.exists():
        sys.exit("hiányzik a data/fajtak.json – futtasd: python tools/build_data.py")
    return json.loads(f.read_text(encoding="utf-8"))["breeds"]


def hu_ui():
    return rj(I18N / SRC / "ui.json")


def country_atoms(s):
    return [a.strip() for a in s.split(" / ")]


def hu_content():
    """A fajtaszövegek magyar forrása, laposan: kulcs → szöveg (sorrend: fajták szerint)."""
    out = {}
    for b in breeds():
        out[f"{b['id']}.nev"] = b["nev"]
        for f in TEXT_F:
            if b.get(f):
                out[f"{b['id']}.{f}"] = b[f]
        for f in LIST_F:
            for i, t in enumerate(b.get(f) or []):
                out[f"{b['id']}.{f}.{i}"] = t
    for b in breeds():
        for a in country_atoms(b["orszag"]):
            out.setdefault(f"country.{a}", a)
    return out


def src_of(bundle):
    return hu_ui() if bundle == "ui" else hu_content()


def stamp(src):
    return h8(src)


CLDR = {"zero", "one", "two", "few", "many", "other"}


def typo(s):
    """Írásjelek egységesítése: egyenes aposztróf a szavak között → ívelt (a fordítók vegyesen használják)."""
    return re.sub(r"(?<=\w)'(?=\w)", "’", s.strip())


def has_tr(tr, k):
    """Van-e fordítás: a kulcson, vagy többes számú alakokban (kulcs.one / kulcs.other …)."""
    return k in tr or f"{k}.other" in tr


def plural_keys():
    """A kódban tn()-nel használt (számmal változó) felületi kulcsok."""
    out = set()
    for f in (ROOT / "src" / "js").glob("*.js"):
        out.update(re.findall(r"\btn\(\s*['\"`]([\w.\-]+)['\"`]", f.read_text(encoding="utf-8")))
    return out


# ---------------------------------------------------------------- egységek (amit egyben fordítunk)
PLURAL = set()


def units(bundle):
    """azonosító → {src, keys, ctx}. A kontent-szövegek (azonos magyar szöveg = egy egység) egyszer fordítódnak;
    a felületi szövegek és a nevek kulcsonként, mert ugyanaz a magyar szó mást jelenthet (pl. „Közepes”)."""
    out = {}
    by = {b["id"]: b for b in breeds()}
    PLURAL.update(plural_keys())
    for key, src in src_of(bundle).items():
        field = key.split(".")[1] if bundle == "content" and not key.startswith("country.") else None
        dedupe = bundle == "content" and field not in ("nev",)
        uid = h8(f"{bundle}|{src}" if dedupe else f"{bundle}|{key}|{src}")
        if bundle == "ui":
            ctx = key + (" – PLURAL: shown with a number {n}; answer with a JSON object of the target language's CLDR plural forms, e.g. {\"one\": \"…\", \"other\": \"…\"}" if key in PLURAL else "")
        elif key.startswith("country."):
            ctx = CTX["country"]
        else:
            bid = key.split(".")[0]
            ctx = f"{field}" + (f" – {CTX.get(field, '')}" if field in CTX else "")
            if field == "nev" or field in TEXT_F:
                ctx += f" – breed: {by[bid]['nev']} ({by[bid]['en']})"
        u = out.setdefault(uid, {"src": src, "keys": [], "ctx": ctx, "bundle": bundle})
        u["keys"].append(key)
    return out


def groups(bundle):
    """Munkacsoportok (a fordítók külön kapják): név → egységazonosítók."""
    us = units(bundle)
    g = {}
    for uid, u in us.items():
        k = u["keys"][0]
        if bundle == "ui":
            name = "ui"
        elif k.startswith("country."):
            name = "countries"
        else:
            f = k.split(".")[1]
            name = {"nev": "names", "egeszseg": "health", "kinekIgen": "who", "kinekNem": "who"}.get(f, "breeds")
        g.setdefault(name, []).append(uid)
    return g


# ---------------------------------------------------------------- állapot
def tr_path(lang, bundle):
    return I18N / lang / f"{bundle}.json"


def load_tr(lang, bundle):
    return rj(tr_path(lang, bundle))


def stamps(lang):
    return rj(I18N / lang / "_src.json")


def coverage(lang):
    """{bundle: (kész, elavult, hiányzik: [kulcs])}"""
    res = {}
    st = stamps(lang)
    for bundle in ("ui", "content"):
        tr, src = load_tr(lang, bundle), src_of(bundle)
        ok, stale, missing = 0, [], []
        for k, s in src.items():
            if not has_tr(tr, k):
                missing.append(k)
            elif st.get(f"{bundle}:{k}") not in (None, stamp(s)):
                stale.append(k)
            else:
                ok += 1
        res[bundle] = (ok, stale, missing)
    return res


def cmd_status(a):
    langs = [l["code"] for l in languages() if l["code"] != SRC] if not a.lang else [a.lang]
    for lang in langs:
        print(f"== {lang}")
        for bundle, (ok, stale, missing) in coverage(lang).items():
            tot = ok + len(stale) + len(missing)
            print(f"  {bundle:8} {ok}/{tot} kész, {len(stale)} elavult (a magyar azóta változott), {len(missing)} hiányzik")
            for k in (stale + missing)[:5]:
                print(f"     · {k}")


# ---------------------------------------------------------------- kinyerés
PROMPT = """# Translation task – Pacsi (dog-breed chooser web app), Hungarian → {lang_name}

You translate UI and content strings of **Pacsi**, a Hungarian web app that helps people pick a dog breed (124 breeds).
Audience: ordinary dog lovers, families, first-time owners. Tone: warm, clear, a little playful – like the Hungarian original.

## Rules
- Input is a JSON file: `{{ "<id>": {{ "src": "<Hungarian text>", "ctx": "<where it appears>" }}, ... }}`.
  Output ONE JSON object `{{ "<id>": "<translation>", ... }}` – every id, no extra keys, no comments, valid JSON (escape quotes).
- Keep placeholders such as `{{n}}`, `{{name}}` and HTML tags (`<b>`, `<i>`, `<br>`) exactly as they are; translate only the text around them.
- Do not invent facts, do not add or drop information. Keep numbers and units; convert the decimal comma to the target
  language's convention (Hungarian `1,5–2 óra` → English `1.5–2 hours`).
- Dog breed names: use the names in `breed_names.json` (Hungarian name → name to use in {lang_name}) whenever a breed is
  mentioned inside a text. Never translate a breed name word by word.
- Hungarian terms that are not obvious: see the glossary below. Veterinary / dog-world terms must be the standard terms
  used by vets and kennel clubs in {lang_name}, not literal translations.
- Texts are shown in small UI elements: stay about as short as the original (±30 %).
- Hungarian-specific institutions or references (MEOESZ = Hungarian Kennel Association, TV shows, places) may get a short
  clarification if a foreign reader would not understand them – otherwise keep them.
{style}
## Glossary (Hungarian → {lang_name})
{terms}
"""


def cmd_extract(a):
    lang = a.lang
    lg = {l["code"]: l for l in languages()}
    if lang not in lg:
        sys.exit(f"{lang}: nincs a data/i18n/languages.json-ban")
    out = pathlib.Path(a.out or (ROOT / "scratch" / f"i18n-{lang}"))
    out.mkdir(parents=True, exist_ok=True)
    gl = rj(I18N / lang / "glossary.json")
    terms = "\n".join(f"- {k} → {v}" for k, v in (gl.get("terms") or {}).items()) or "(none yet)"
    style = ("\n## Style\n" + "\n".join(f"- {s}" for s in gl["style"]) + "\n") if gl.get("style") else ""
    (out / "PROMPT.md").write_text(PROMPT.format(lang_name=lg[lang]["name"], terms=terms, style=style), encoding="utf-8")
    names = {b["nev"]: load_tr(lang, "content").get(f"{b['id']}.nev", b["nev"]) for b in breeds()}
    wj(out / "breed_names.json", names)
    n_files = 0
    tr = {"ui": load_tr(lang, "ui"), "content": load_tr(lang, "content")}
    st = stamps(lang)
    for bundle in ([a.only] if a.only else ["ui", "content"]):
        us = units(bundle)
        for gname, ids in groups(bundle).items():
            if a.group and gname != a.group:
                continue
            todo = [i for i in ids if a.all or any((k not in tr[bundle]) or not str(tr[bundle][k]).strip()
                                                   or st.get(f"{bundle}:{k}") not in (None, stamp(us[i]["src"])) for k in us[i]["keys"])]
            if not todo:
                continue
            nchunk = max(1, a.chunks if gname in ("breeds", "who") else 1)
            per = -(-len(todo) // nchunk)
            for c in range(nchunk):
                part = todo[c * per:(c + 1) * per]
                if not part:
                    continue
                name = f"{bundle}_{gname}_{c + 1:02d}.json"
                wj(out / name, {i: {"src": us[i]["src"], "ctx": us[i]["ctx"]} for i in part})
                n_files += 1
                print(f"  {name}: {len(part)} egység, {sum(len(us[i]['src']) for i in part)} karakter")
    print(f"{n_files} munkafájl → {out}")


# ---------------------------------------------------------------- beolvasás
def apply_translations(lang, data):
    """data: {egységazonosító: fordítás}. Visszaad: (alkalmazott egységek, ismeretlen azonosítók)."""
    allu = {}
    for bundle in ("ui", "content"):
        allu.update(units(bundle))
    tr = {"ui": load_tr(lang, "ui"), "content": load_tr(lang, "content")}
    st = stamps(lang)
    done, unknown = 0, []
    for uid, text in data.items():
        if uid not in allu:
            unknown.append(uid)
            continue
        u = allu[uid]
        forms = None
        if isinstance(text, dict):
            if set(text) <= CLDR and text and all(isinstance(v, str) and v.strip() for v in text.values()):
                forms = {c: typo(v) for c, v in text.items()}
            else:
                text = text.get("t") or text.get("tr") or text.get("translation")
        if forms is None and (not isinstance(text, str) or not text.strip()):
            unknown.append(uid)
            continue
        for k in u["keys"]:
            tb = tr[u["bundle"]]
            if forms:
                tb.pop(k, None)
                for c, v in forms.items():
                    tb[f"{k}.{c}"] = v
            else:
                for c in CLDR:
                    tb.pop(f"{k}.{c}", None)
                tb[k] = typo(text)
            st[f"{u['bundle']}:{k}"] = stamp(src_of(u["bundle"])[k])
        done += 1
    for bundle in tr:
        wj(tr_path(lang, bundle), tr[bundle])
    wj(I18N / lang / "_src.json", st)
    return done, unknown


def parse_json_loose(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    a, b = text.find("{"), text.rfind("}")
    return json.loads(text[a:b + 1])


def cmd_merge(a):
    tot_done, tot_unknown = 0, []
    for f in a.files:
        data = parse_json_loose(pathlib.Path(f).read_text(encoding="utf-8"))
        data = data.get("units", data) if isinstance(data.get("units"), dict) else data
        done, unknown = apply_translations(a.lang, data)
        tot_done += done
        tot_unknown += unknown
        print(f"  {pathlib.Path(f).name}: {done} egység beírva" + (f", {len(unknown)} ismeretlen/üres azonosító" if unknown else ""))
    if tot_unknown:
        print("  ismeretlen azonosítók:", ", ".join(tot_unknown[:20]))
    print(f"{tot_done} egység beírva → data/i18n/{a.lang}/")


def cmd_seal(a):
    """A jelenlegi magyar szövegekhez rögzíti a meglévő fordításokat (kézi szerkesztés után)."""
    st = stamps(a.lang)
    for bundle in ("ui", "content"):
        tr = load_tr(a.lang, bundle)
        for k, s in src_of(bundle).items():
            if has_tr(tr, k):
                st[f"{bundle}:{k}"] = stamp(s)
    wj(I18N / a.lang / "_src.json", st)
    print("rögzítve")


# ---------------------------------------------------------------- ellenőrzés
PH = re.compile(r"\{(\w+)\}")
TAG = re.compile(r"</?(\w+)")
HU_ONLY = re.compile(r"[őűŐŰ]")


def used_keys():
    """A kódban és a HTML-ben használt felületi kulcsok: (statikus kulcsok, dinamikus előtagok)."""
    static, prefixes = set(), set()
    files = list((ROOT / "src" / "js").glob("*.js")) + [ROOT / "src" / "index.html"]
    for f in files:
        s = f.read_text(encoding="utf-8")
        if f.suffix == ".js":
            s = re.sub(r"/\*(?!\s*i18n:).*?\*/", "", s, flags=re.S)
            s = re.sub(r"(?m)(^|\s)//\s.*$", "", s)
        for m in re.finditer(r"\b(?:t|tn|tH)\(\s*(['\"`])([\w.\-]*)(\$\{)?", s):
            (prefixes if m.group(3) else static).add(m.group(2))
        for m in re.finditer(r"data-i18n(?:-[a-z]+)?=\"([^\"]+)\"", s):
            for part in m.group(1).split(";"):
                static.add(part.split(":")[-1].strip())
        for m in re.finditer(r"/\*\s*i18n:\s*([\w.\-,\s*]+?)\s*\*/", s):      # kézzel jelölt dinamikus előtagok
            for p in m.group(1).split(","):
                prefixes.add(p.strip().rstrip("*"))
    return static, prefixes


def ui_base(k):
    return re.sub(r"\.(one|other)$", "", k)


def cmd_check(a):
    err, warn = 0, 0
    src = hu_ui()
    static, prefixes = used_keys()
    ui_keys = {ui_base(k) for k in src}
    for k in sorted(static):
        if k and k not in ui_keys and k not in src:
            print(f"  HIBA  a kód ismeretlen kulcsot használ: {k}")
            err += 1
    for k in sorted(ui_keys):
        if k not in static and not any(k.startswith(p) for p in prefixes):
            print(f"  figy  nem használt felületi kulcs: {k}")
            warn += 1
    langs = [a.lang] if a.lang else [l["code"] for l in languages() if l["code"] != SRC]
    for lang in langs:
        print(f"== {lang}")
        gl = rj(I18N / lang / "glossary.json")
        for bundle in ("ui", "content"):
            tr, s = load_tr(lang, bundle), src_of(bundle)
            ok, stale, missing = coverage(lang)[bundle]
            if missing:
                print(f"  figy  {bundle}: {len(missing)} hiányzó fordítás (magyarul jelenik meg): {', '.join(missing[:4])}…")
                warn += 1
            if stale:
                print(f"  figy  {bundle}: {len(stale)} elavult fordítás (a magyar szöveg megváltozott): {', '.join(stale[:4])}…")
                warn += 1
            for k, t in tr.items():
                base = ui_base(k) if bundle == "ui" else k
                if base not in s:
                    print(f"  figy  {bundle}: felesleges kulcs {k}")
                    warn += 1
                    continue
                hs = s[base]
                if not t:
                    continue
                if set(PH.findall(hs)) != set(PH.findall(t)):
                    print(f"  HIBA  {bundle}:{k}: a helyőrzők nem egyeznek: {PH.findall(hs)} ≠ {PH.findall(t)}")
                    err += 1
                if sorted(TAG.findall(hs)) != sorted(TAG.findall(t)):
                    print(f"  HIBA  {bundle}:{k}: a HTML-címkék nem egyeznek")
                    err += 1
                if len(hs) > 40 and not (0.35 < len(t) / len(hs) < 3):   # a nagyon rövid vagy hosszú fordítás gyanús
                    print(f"  figy  {bundle}:{k}: gyanús hossz ({len(hs)} → {len(t)})")
                    warn += 1
                if lang != "hu" and HU_ONLY.search(re.sub(r"[A-ZÁÉÍÓÖŐÚÜŰ]\w*", "", t)) and k.split(".")[1:2] != ["nev"] and not k.startswith("country."):
                    print(f"  figy  {bundle}:{k}: magyar betű (ő/ű) maradt a fordításban")
                    warn += 1
            # szakszavak: az egészségügyi tételeknél a szószedet nagybetűs (szaknyelvi) kifejezései egységesen jelenjenek meg
            for hu_term, want in (gl.get("terms") or {}).items():
                if bundle != "content" or not hu_term[:1].isupper():
                    continue
                core = re.split(r"\s*\(", want)[0].lower()
                for k, hs in s.items():
                    if ".egeszseg." in k and hs.lower().startswith(hu_term.lower()) and k in tr and core not in tr[k].lower():
                        print(f"  figy  {bundle}:{k}: a szószedet szerint „{hu_term}” → „{want}”, de a fordításban nincs")
                        warn += 1
        names = {k: v for k, v in load_tr(lang, "content").items() if k.endswith(".nev")}
        if len(names) < len(breeds()):
            print(f"  figy  csak {len(names)}/{len(breeds())} fajtanév van lefordítva")
    print(f"{err} hiba, {warn} figyelmeztetés")
    return 1 if err else 0


# ---------------------------------------------------------------- csomag az apphoz
def bundle(strict=False):
    """Az appba ágyazott nyelvi csomag. A magyar fajtaszöveg magában a fajtaadatban van; itt a többi nyelv fajtánként."""
    langs = languages()
    out = {"langs": [{k: v for k, v in l.items()} for l in langs], "ui": {}, "breeds": {}}
    bs = breeds()
    for l in langs:
        code = l["code"]
        out["ui"][code] = {k: v for k, v in (hu_ui() if code == SRC else load_tr(code, "ui")).items()}
        if code == SRC:
            continue
        tr = load_tr(code, "content")
        al = rj(I18N / code / "aliases.json")
        ov = {}
        for b in bs:
            e = {}
            for f in ["nev"] + TEXT_F:
                if tr.get(f"{b['id']}.{f}"):
                    e[f] = tr[f"{b['id']}.{f}"]
            for f in LIST_F:
                items = [tr.get(f"{b['id']}.{f}.{i}") for i in range(len(b.get(f) or []))]
                if items and all(items):
                    e[f] = items
            atoms = country_atoms(b["orszag"])
            if all(tr.get(f"country.{x}") for x in atoms):
                e["orszag"] = " / ".join(tr[f"country.{x}"] for x in atoms)
            if al.get(b["id"]):
                e["alias"] = al[b["id"]]
            if e:
                ov[b["id"]] = e
        out["breeds"][code] = ov
        if strict:
            cov = coverage(code)
            stale, miss = sum(len(c[1]) for c in cov.values()), sum(len(c[2]) for c in cov.values())
            if miss:
                print(f"  ! {code}: {miss} hiányzó fordítás – ezek magyarul jelennek meg")
            if stale:
                print(f"  ! {code}: {stale} elavult fordítás (a magyar szöveg azóta változott) – a régi fordítás marad, érdemes frissíteni")
    return out


# ---------------------------------------------------------------- fordítás API-val (opcionális)
API_BASE = {"anthropic": "https://api.anthropic.com", "openai": "https://api.openai.com"}


def read_key(provider, key_file):
    env = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}[provider]
    if os.environ.get(env):
        return os.environ[env].strip()
    if key_file:
        txt = pathlib.Path(key_file).read_text(encoding="utf-8")
        m = re.search(r"(sk-[A-Za-z0-9_\-]{20,})", txt)
        return (m.group(1) if m else txt).strip()
    sys.exit(f"nincs API-kulcs: állítsd be a {env} környezeti változót, vagy add meg a --key-file kapcsolót")


def call_llm(provider, model, key, system, user, base=None):
    base = (base or os.environ.get("PACSI_I18N_API_BASE") or API_BASE[provider]).rstrip("/")
    if provider == "anthropic":
        url, hdr = f"{base}/v1/messages", {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        body = {"model": model, "max_tokens": 16000, "system": system, "messages": [{"role": "user", "content": user}]}
    else:
        url, hdr = f"{base}/v1/chat/completions", {"Authorization": f"Bearer {key}", "content-type": "application/json"}
        body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "response_format": {"type": "json_object"}}
    req = urllib.request.Request(url, json.dumps(body).encode("utf-8"), hdr)
    with urllib.request.urlopen(req, timeout=300) as r:
        res = json.loads(r.read().decode("utf-8"))
    return res["content"][0]["text"] if provider == "anthropic" else res["choices"][0]["message"]["content"]


def cmd_translate(a):
    lg = {l["code"]: l for l in languages()}
    if a.lang not in lg:
        sys.exit(f"{a.lang}: nincs a data/i18n/languages.json-ban")
    if a.provider == "openai" and not a.model:
        sys.exit("OpenAI-hoz add meg a --model kapcsolót")
    model = a.model or "claude-sonnet-5-5"
    key = read_key(a.provider, a.key_file)
    gl = rj(I18N / a.lang / "glossary.json")
    terms = "\n".join(f"- {k} → {v}" for k, v in (gl.get("terms") or {}).items()) or "(none yet)"
    style = ("\n## Style\n" + "\n".join(f"- {s}" for s in gl["style"]) + "\n") if gl.get("style") else ""
    system = PROMPT.format(lang_name=lg[a.lang]["name"], terms=terms, style=style)
    names = {b["nev"]: load_tr(a.lang, "content").get(f"{b['id']}.nev", b["nev"]) for b in breeds()}
    system += "\n## breed_names.json\n" + json.dumps(names, ensure_ascii=False)
    tr = {"ui": load_tr(a.lang, "ui"), "content": load_tr(a.lang, "content")}
    st = stamps(a.lang)
    todo = []
    for bundle in ("ui", "content"):
        for uid, u in units(bundle).items():
            if any(k not in tr[bundle] or st.get(f"{bundle}:{k}") not in (None, stamp(u["src"])) for k in u["keys"]):
                todo.append((uid, u))
    # a nevek előbb: a szövegek hivatkoznak rájuk
    todo.sort(key=lambda x: 0 if x[1]["keys"][0].endswith(".nev") else 1)
    print(f"{len(todo)} egység fordítandó ({a.provider}, {model})")
    batch, size = [], 0
    def flush():
        nonlocal batch, size
        if not batch:
            return
        user = json.dumps({uid: {"src": u["src"], "ctx": u["ctx"]} for uid, u in batch}, ensure_ascii=False)
        got = {}
        for attempt in range(3):
            try:
                got.update(parse_json_loose(call_llm(a.provider, model, key, system, user)))
                break
            except Exception as e:                      # hálózat / szintaxis: újrapróbáljuk
                print("   újrapróbálás:", type(e).__name__, str(e)[:120])
                time.sleep(3 * (attempt + 1))
        done, unknown = apply_translations(a.lang, {k: v for k, v in got.items() if k in dict(batch)})
        print(f"   {done}/{len(batch)} egység kész")
        batch, size = [], 0
    for uid, u in todo:
        batch.append((uid, u))
        size += len(u["src"])
        if size > a.batch_chars:
            flush()
    flush()
    cmd_check(argparse.Namespace(lang=a.lang))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("status", help="fordítási lefedettség"); p.add_argument("lang", nargs="?"); p.set_defaults(f=cmd_status)
    p = sp.add_parser("extract", help="fordítandó szövegek munkafájlokba"); p.add_argument("lang")
    p.add_argument("--out"); p.add_argument("--only", choices=["ui", "content"]); p.add_argument("--group")
    p.add_argument("--chunks", type=int, default=5, help="ennyi részre bontja a fajta- és a „kinek” szövegeket")
    p.add_argument("--all", action="store_true", help="a már lefordítottakat is (újrafordításhoz)"); p.set_defaults(f=cmd_extract)
    p = sp.add_parser("merge", help="lefordított munkafájlok beolvasása"); p.add_argument("lang"); p.add_argument("files", nargs="+"); p.set_defaults(f=cmd_merge)
    p = sp.add_parser("seal", help="meglévő fordítások rögzítése a mostani magyarhoz"); p.add_argument("lang"); p.set_defaults(f=cmd_seal)
    p = sp.add_parser("check", help="ellenőrzés"); p.add_argument("lang", nargs="?"); p.set_defaults(f=cmd_check)
    p = sp.add_parser("translate", help="fordítás LLM-API-val (a hiányzó szövegekre)"); p.add_argument("lang")
    p.add_argument("--provider", choices=["anthropic", "openai"], default="anthropic"); p.add_argument("--model")
    p.add_argument("--key-file"); p.add_argument("--batch-chars", type=int, default=7000); p.set_defaults(f=cmd_translate)
    a = ap.parse_args()
    sys.exit(a.f(a) or 0)


if __name__ == "__main__":
    main()
