"""Pacsi – Facebook-oldal automatikus posztolása a Meta Graph API-val (csak szabványos Python, külső csomag nélkül).

A posztok a Facebook SAJÁT ütemezőjébe kerülnek (scheduled_publish_time): a megadott időpontban akkor is kimennek,
ha a laptop ki van kapcsolva. Az ütemezés legfeljebb 28 nappal előre és legalább 15 perccel későbbre kérhető.

Beállítások (egyszer, a felhasználó saját termináljában – a tokeneket senki más nem látja):
  python marketing/tools/facebook.py setup
    bekéri az App ID-t, az App Secretet és a Graph API Explorerből másolt felhasználói tokent (rejtett bevitel),
    tartós oldaltokenre cseréli (nem jár le), és a repó gyökerébe menti: Facebook_API.json (gitignore-olt).
    Az App Secret nem kerül mentésre. A token soha nem íródik ki.

Parancsok:
  python marketing/tools/facebook.py check                  token, jogosultságok, oldal ellenőrzése
  python marketing/tools/facebook.py test --yes             próba: egy 20 nap múlvára ütemezett (nem nyilvános) posztot
                                                            létrehoz, visszaolvas és töröl – semmi nem jelenik meg
  python marketing/tools/facebook.py plan [--days 28]       a naptár Facebook-idősávjai: mi, mikor, milyen formában, milyen állapotban
  python marketing/tools/facebook.py schedule [--days 28]   minden esedékes, még nem kint lévő idősáv ütemezése a Facebookon
       --only v2,k_quiz   csak ezek         --yes   valóban ütemez (nélküle csak kiírja, mit tenne)
  python marketing/tools/facebook.py post <id> [--slot N] [--now | --at "2026-10-05 12:00"] --yes
                                                            egy tartalom közzététele most vagy egy adott időpontra
  python marketing/tools/facebook.py scheduled              a Facebookon ütemezett posztok és a napló összevetése
  python marketing/tools/facebook.py cancel <id> [--slot N] --yes   ütemezett poszt visszavonása (törlése a Facebookról)
  python marketing/tools/facebook.py posts [--limit 20]     az oldal legutóbbi posztjai (a kézzel kitettek is)
  python marketing/tools/facebook.py insights [--json F]    a kitett posztok statisztikája (elérés, reakció, komment,
                                                            megosztás, kattintás) – a CMS Eredmények fülének formájában is
  --version: verzió.

Tartalom: marketing/content/content.json (python marketing/tools/build.py --no-render). A CMS-ben átírt szövegek és
kipipált idősávok a CMS közös tárolójából jönnek: Claude az ArtifactData eszközzel a marketing/tmp/cms_db/edits mappába
menti őket (egy dokumentum = egy JSON), ez az eszköz onnan olvassa és rárakja az alapszövegre.
Napló (mi van kint / ütemezve, a Facebook-azonosítókkal): marketing/social/state/facebook_log.json (nincs verziókezelve).

Formák: videó → Reels (9:16, 3–90 mp) · kép → fotóposzt · karusszel → több képes poszt · story → oldalstory (csak
azonnal, a Meta nem enged storyt ütemezni) · hirdetés → kimarad (a Hirdetéskezelőben készül), kivéve az „organikus” idősávot
· profil → kimarad (az oldal beállításához tartozik).
"""
import datetime as dt
import getpass
import json
import mimetypes
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
VERSION = (MK / "VERSION").read_text(encoding="utf-8").strip()
API = "v25.0"
GRAPH = f"https://graph.facebook.com/{API}"
RUPLOAD = f"https://rupload.facebook.com/video-upload/{API}"
CFG_P = ROOT / "Facebook_API.json"
LOG_P = MK / "social" / "state" / "facebook_log.json"
CONTENT_P = MK / "content" / "content.json"
EDITS_D = MK / "tmp" / "cms_db" / "edits"
SCOPES = ["pages_show_list", "pages_read_engagement", "pages_manage_posts"]
OPTIONAL_SCOPES = ["read_insights", "business_management"]
MIN_LEAD = dt.timedelta(minutes=15)       # a Meta legalább 10 percet kér – ráhagyással
MAX_AHEAD = dt.timedelta(days=28)         # feed: 30 nap, Reels: 29 nap – ráhagyással
ARGS = sys.argv[1:]
YES = "--yes" in ARGS

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Budapest")
except Exception:                           # tzdata nélkül: kézi CET/CEST
    TZ = None


def opt(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS and ARGS.index(name) + 1 < len(ARGS) else default


def local(date, time_="12:00"):
    """'2026-10-05', '12:00' → időzónás datetime (Budapest)."""
    naive = dt.datetime.fromisoformat(f"{date}T{time_}")
    if TZ:
        return naive.replace(tzinfo=TZ)
    # EU-szabály: CEST a márc. utolsó vasárnap 01:00 UTC-től okt. utolsó vasárnap 01:00 UTC-ig
    y = naive.year
    last_sun = lambda m: max(d for d in (dt.date(y, m, day) for day in range(25, 32)) if d.weekday() == 6)
    start = dt.datetime.combine(last_sun(3), dt.time(1), dt.timezone.utc)
    end = dt.datetime.combine(last_sun(10), dt.time(1), dt.timezone.utc)
    utc_guess = naive.replace(tzinfo=dt.timezone(dt.timedelta(hours=1)))
    off = 2 if start <= utc_guess < end else 1
    return naive.replace(tzinfo=dt.timezone(dt.timedelta(hours=off)))


def now():
    return dt.datetime.now(dt.timezone.utc)


# ------------------------------------------------------------------ Graph API
class GraphError(Exception):
    def __init__(self, status, err):
        self.status, self.err = status, err or {}
        e = self.err
        hint = {190: "a token lejárt vagy érvénytelen – futtasd újra: facebook.py setup",
                10: "hiányzó jogosultság (App-szerepkör / Live mód?)",
                200: "hiányzó jogosultság: pages_manage_posts / pages_read_engagement",
                368: "a Facebook ideiglenesen korlátozta a posztolást (spam-gyanú) – várj",
                100: "hibás paraméter"}.get(e.get("code"), "")
        super().__init__(f"Graph API hiba {status}: {e.get('message', '')} (code {e.get('code')}"
                         f"{', subcode ' + str(e.get('error_subcode')) if e.get('error_subcode') else ''})"
                         f"{' – ' + hint if hint else ''}{' · fbtrace ' + e['fbtrace_id'] if e.get('fbtrace_id') else ''}")


def _request(method, url, params=None, files=None, headers=None, body=None, timeout=120):
    params = {k: (json.dumps(v) if isinstance(v, (list, dict)) else str(v)) for k, v in (params or {}).items() if v is not None}
    hdrs = dict(headers or {})
    data = body
    if files:
        boundary = "----pacsi" + uuid.uuid4().hex
        parts = []
        for k, v in params.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode("utf-8"))
        for k, path in files.items():
            path = pathlib.Path(path)
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{path.name}"\r\n'
                         f"Content-Type: {ctype}\r\n\r\n".encode("utf-8") + path.read_bytes() + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        data = b"".join(parts)
        hdrs["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif method == "POST" and body is None:
        data = urllib.parse.urlencode(params).encode("utf-8")
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    elif params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8") or "{}"
                return json.loads(raw) if raw.strip().startswith(("{", "[")) else {"raw": raw}
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode("utf-8")).get("error", {})
            except Exception:
                err = {"message": str(e)}
            if err.get("is_transient") and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise GraphError(e.code, err) from None
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise GraphError(0, {"message": f"hálózati hiba: {e.reason}"}) from None


def g(method, path, token, **kw):
    params = dict(kw.pop("params", {}) or {})
    params["access_token"] = token
    return _request(method, f"{GRAPH}/{path.lstrip('/')}", params=params, **kw)


# ------------------------------------------------------------------ beállítások, napló
def load_cfg():
    if not CFG_P.exists():
        sys.exit("Nincs Facebook-beállítás. Futtasd a saját terminálodban: python marketing/tools/facebook.py setup")
    return json.loads(CFG_P.read_text(encoding="utf-8"))


def load_log():
    return json.loads(LOG_P.read_text(encoding="utf-8")) if LOG_P.exists() else {"posts": {}}


def save_log(log):
    LOG_P.parent.mkdir(parents=True, exist_ok=True)
    tmp = LOG_P.with_suffix(".tmp")
    tmp.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(LOG_P)                                   # atomi csere


def cmd_setup():
    print("Pacsi · Facebook-beállítás. A beírt adatok nem jelennek meg a képernyőn, és a titkos kulcs nem kerül mentésre.\n")
    app_id = (opt("--app-id") or input("App ID (App settings → Basic): ")).strip()
    secret = getpass.getpass("App Secret (rejtett): ").strip()
    user_tok = getpass.getpass("Felhasználói token a Graph API Explorerből (rejtett): ").strip()
    if not (app_id and secret and user_tok):
        sys.exit("Mindhárom adat kell.")
    ll = _request("GET", f"{GRAPH}/oauth/access_token", params={
        "grant_type": "fb_exchange_token", "client_id": app_id, "client_secret": secret, "fb_exchange_token": user_tok})
    long_user = ll.get("access_token")
    if not long_user:
        sys.exit("A tartós tokenre cserélés nem sikerült.")
    pages = g("GET", "me/accounts", long_user, params={"fields": "id,name,access_token,tasks", "limit": 100}).get("data", [])
    if not pages:
        sys.exit("A token nem lát egyetlen oldalt sem. A Graph API Explorerben a tokenkérésnél a Pacsi oldalt is jelöld be,\n"
                 "és ha az oldal egy üzleti portfólióhoz tartozik, add hozzá a business_management jogosultságot is.")
    want = opt("--page")
    if want:
        pages = [p for p in pages if want.lower() in p["name"].lower() or p["id"] == want] or pages
    if len(pages) > 1:
        for i, p in enumerate(pages, 1):
            print(f"  {i}. {p['name']}  ({p['id']})")
        k = int(input("Melyik oldal? (szám): ").strip() or "1")
        page = pages[k - 1]
    else:
        page = pages[0]
    dbg = _request("GET", f"{GRAPH}/debug_token", params={"input_token": page["access_token"],
                                                           "access_token": f"{app_id}|{secret}"}).get("data", {})
    scopes = sorted(set(dbg.get("scopes", [])))
    missing = [s for s in SCOPES if s not in scopes]
    cfg = {"_doc": "Pacsi Facebook-beállítás – TITKOS (oldaltoken). Gitignore-olt, soha ne tedd verziókezelésbe, ne küldd el senkinek.",
           "app_id": app_id, "page_id": page["id"], "page_name": page["name"], "page_token": page["access_token"],
           "tasks": page.get("tasks", []), "scopes": scopes, "expires_at": dbg.get("expires_at", 0),
           "saved_at": dt.datetime.now().isoformat(timespec="seconds"), "api": API}
    CFG_P.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    exp = dbg.get("expires_at", 0)
    print(f"\n✓ Mentve: {CFG_P.name} (a repó gyökerében, gitignore-olt)")
    print(f"  Oldal: {page['name']} ({page['id']})")
    print(f"  Lejárat: {'soha' if not exp else dt.datetime.fromtimestamp(exp).isoformat(timespec='minutes')}")
    print(f"  Jogosultságok: {', '.join(scopes)}")
    if missing:
        print(f"  ! Hiányzó jogosultság: {', '.join(missing)} – kérd újra a tokent ezekkel együtt.")
    if "CREATE_CONTENT" not in page.get("tasks", []):
        print("  ! A fiókodnak nincs „tartalom létrehozása” jogköre ezen az oldalon.")
    print("\nKész. Szólj Claude-nak, hogy ellenőrizze: python marketing/tools/facebook.py check")


def cmd_check():
    cfg = load_cfg()
    tok, pid = cfg["page_token"], cfg["page_id"]
    me = g("GET", "me", tok, params={"fields": "id,name"})
    page = g("GET", pid, tok, params={"fields": "name,link,fan_count,followers_count,category,verification_status"})
    print(f"✓ Token érvényes · oldal: {page.get('name')} ({pid}) · {page.get('link', '')}")
    print(f"  Követők: {page.get('followers_count', '?')} · kedvelések: {page.get('fan_count', '?')} · kategória: {page.get('category', '')}")
    if me.get("id") != pid:
        print(f"  ! A token nem oldaltoken (me = {me.get('name')}). Futtasd újra a setupot.")
    try:
        d = g("GET", "debug_token", tok, params={"input_token": tok}).get("data", {})
        scopes = set(d.get("scopes", []))
        exp = d.get("expires_at", 0)
        print(f"  Lejárat: {'soha' if not exp else dt.datetime.fromtimestamp(exp).isoformat(timespec='minutes')}")
        miss = [s for s in SCOPES if s not in scopes]
        print(f"  Jogosultságok: {', '.join(sorted(scopes))}" + (f"  ! HIÁNYZIK: {', '.join(miss)}" if miss else ""))
        if "read_insights" not in scopes:
            print("  (read_insights nélkül a statisztika csak reakciót, kommentet, megosztást ad – elérést nem.)")
    except GraphError as e:
        print(f"  (a token részletei nem kérdezhetők le: {e})")
    try:
        sp = g("GET", f"{pid}/scheduled_posts", tok, params={"fields": "id", "limit": 100}).get("data", [])
        print(f"  Ütemezett posztok most a Facebookon: {len(sp)}")
    except GraphError as e:
        print(f"  ! Az ütemezett posztok nem olvashatók: {e}")
    print("\nFontos: az app legyen ÉLŐ (Live) módban, különben a képes posztokat csak te látod.")


def cmd_test():
    cfg = load_cfg()
    tok, pid = cfg["page_token"], cfg["page_id"]
    when = now() + dt.timedelta(days=20)
    if not YES:
        print(f"[próba] 20 nap múlvára ütemezett szöveges poszt létrehozása, visszaolvasása és törlése ({when:%Y-%m-%d}). Futtasd --yes kapcsolóval.")
        return
    r = g("POST", f"{pid}/feed", tok, params={"message": "Pacsi API-próba – ez a poszt azonnal törlődik.",
                                              "published": "false", "scheduled_publish_time": int(when.timestamp())})
    post_id = r.get("id")
    print(f"✓ Ütemezett próbaposzt létrehozva: {post_id}")
    sp = g("GET", f"{pid}/scheduled_posts", tok, params={"fields": "id,scheduled_publish_time", "limit": 100}).get("data", [])
    print(f"✓ Visszaolvasva az ütemezettek között: {'igen' if any(p['id'] == post_id for p in sp) else 'NEM (lassú lehet a lista)'}")
    g("DELETE", post_id, tok)
    print("✓ Törölve. A posztolás és az ütemezés működik – nyilvánosan semmi nem jelent meg.")


# ------------------------------------------------------------------ tartalom
def load_items():
    if not CONTENT_P.exists():
        sys.exit("Nincs content.json – futtasd: python marketing/tools/build.py --no-render")
    data = json.loads(CONTENT_P.read_text(encoding="utf-8"))
    edits = {}
    if EDITS_D.exists():
        for f in EDITS_D.glob("*.json"):
            try:
                edits[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                pass
    items = {}
    for it in data["items"]:
        e = edits.get(it["id"], {})
        fb = dict((it.get("copy") or {}).get("facebook") or {})
        fb.update(((e.get("copy") or {}).get("facebook")) or {})
        slots = []
        for i, s in enumerate(it.get("slots", [])):
            s = {**s, **((e.get("slots") or {}).get(str(i)) or {}), "i": i}
            slots.append(s)
        items[it["id"]] = {**it, "fb": fb, "slots": slots, "status": e.get("status", it.get("status")), "_edited": bool(e)}
    return items


def fb_form(it, slot):
    """Milyen Facebook-posztként megy ki? (forma, ok ha kimarad)"""
    k, note = it["kind"], (slot.get("note") or "").lower()
    if k == "profil":
        return None, "profilbeállítás – nem poszt"
    if k == "hirdetes" and "organikus" not in note:
        return None, "hirdetés – a Hirdetéskezelőben készül"
    if not (it["fb"].get("text") or "").strip():
        return None, "nincs Facebook-szöveg"
    return {"video": "reels", "karusszel": "tobbkepes", "story": "story"}.get(k, "foto"), ""


AD_LABELS = ("Elsődleges szöveg", "Címsor", "Leírás", "CTA-gomb", "Cél-URL")


def organic_from_ad(text, iid):
    """A hirdetésszöveg (Elsődleges szöveg / Címsor / … / Cél-URL) organikus posztként: az elsődleges szöveg
    (ha nincs, a címsor) és a követhető rövid link. A fizetett UTM-es cél-URL nem kerül organikus posztba."""
    f, cur = {}, None
    for line in text.splitlines():
        lab = next((l for l in AD_LABELS if line.strip().startswith(l + ":")), None)
        if lab:
            cur, f[lab] = lab, line.split(":", 1)[1].strip()
        elif cur:
            f[cur] += "\n" + line
    if not f:
        return text
    body = (f.get("Elsődleges szöveg") or f.get("Címsor") or "").strip()
    return f"{body} 👉 https://pacsit.hu/f/{iid}"


def caption(it):
    t, tags = (it["fb"].get("text") or "").strip(), (it["fb"].get("tags") or "").strip()
    if it.get("kind") == "hirdetes":
        t = organic_from_ad(t, it["id"])
    return f"{t}\n\n{tags}" if tags else t


def media(it, form):
    files = it.get("files", [])
    if form == "reels":
        return [MK / f["src"] for f in files if f["src"].endswith(".mp4")][:1], [MK / f["src"] for f in files if f.get("role") == "cover"][:1]
    if form == "tobbkepes":
        return [MK / f["src"] for f in files if f.get("role") == "page"], []
    return [MK / f["src"] for f in files if f.get("role") == "main" and f["src"].endswith((".png", ".jpg", ".jpeg"))][:1], []


def fb_slots(items, days):
    log = load_log()["posts"]
    horizon = now() + dt.timedelta(days=days)
    rows = []
    for it in items.values():
        for s in it["slots"]:
            if s["platform"] != "facebook":
                continue
            key = f"{it['id']}#{s['i']}"
            when = local(s["date"], s.get("time") or "12:00")
            form, why = fb_form(it, s)
            ent = log.get(key)
            if ent:
                state = {"scheduled": "ütemezve", "published": "kint van (API)"}.get(ent["mode"], ent["mode"])
            elif s.get("done"):
                state = "kint van (CMS)"
            elif not form:
                state = "kimarad"
            elif when < now():
                state = "LEKÉSETT" if it["status"] != "kiposztolva" else "kint van? (CMS: kiposztolva)"
            elif when > horizon:
                state = "később"
            elif it["status"] == "kiposztolva":
                state = "ellenőrizd (CMS: kiposztolva)"   # máshol már kint van – Facebookra csak kérésre (--only)
            else:
                state = "esedékes"
            rows.append({"key": key, "it": it, "slot": s, "when": when, "form": form, "why": why, "state": state, "log": ent})
    return sorted(rows, key=lambda r: r["when"])


FORM_HU = {"reels": "Reels", "tobbkepes": "több képes", "story": "story", "foto": "fotó"}


def cmd_plan():
    days = int(opt("--days", "28"))
    rows = fb_slots(load_items(), days)
    print(f"Facebook-idősávok (a következő {days} napra ütemezhető: 'esedékes')\n")
    for r in rows:
        files, _ = media(r["it"], r["form"]) if r["form"] else ([], [])
        miss = [p.name for p in files if not p.exists()]
        extra = r["why"] or (f"HIÁNYZÓ FÁJL: {', '.join(miss)}" if miss else f"{len(files)} fájl")
        if r["form"] == "story" and r["state"] == "esedékes":
            extra += " · story: csak azonnal tehető ki (post --now)"
        print(f"  {r['when']:%m-%d %H:%M}  {r['state']:<28} {FORM_HU.get(r['form'], '–'):<10} {r['it']['id']:<18} {r['it']['title'][:44]:<44}  {extra}")
    due = [r for r in rows if r["state"] == "esedékes" and r["form"] != "story"]
    print(f"\n{len(due)} idősáv ütemezhető most: python marketing/tools/facebook.py schedule --yes")


# ------------------------------------------------------------------ közzététel
def publish(cfg, it, slot, when, form):
    """Egy tartalom kitétele vagy ütemezése. when=None → azonnal. Visszaad: naplóbejegyzés."""
    tok, pid = cfg["page_token"], cfg["page_id"]
    files, cover = media(it, form)
    for p in files + cover:
        if not p.exists():
            raise SystemExit(f"Hiányzó fájl: {p}")
    if not files:
        raise SystemExit(f"{it['id']}: nincs feltölthető fájl")
    msg = caption(it)
    sched = {"published": "false", "scheduled_publish_time": int(when.timestamp())} if when else {"published": "true"}
    ent = {"item": it["id"], "slot": slot["i"], "form": form, "mode": "scheduled" if when else "published",
           "when": (when or now()).astimezone().isoformat(timespec="minutes"), "created": now().isoformat(timespec="seconds"),
           "caption_head": msg[:80]}
    if form in ("foto", "tobbkepes"):
        # egy vagy több kép: előbb rejtve feltöltjük őket, aztán egy posztba fűzzük (így az ütemezés és a
        # visszavonás minden képes posztnál ugyanúgy, a poszt azonosítójával működik)
        ids = []
        for p in files:
            r = g("POST", f"{pid}/photos", tok, params={"published": "false", "temporary": "true" if when else "false"}, files={"source": p})
            ids.append(r["id"])
            print(f"    kép feltöltve: {p.name}")
        r = g("POST", f"{pid}/feed", tok, params={"message": msg, "attached_media": [{"media_fbid": i} for i in ids], **sched})
        ent.update(photo_ids=ids, post_id=r.get("id"))
    elif form == "reels":
        st = g("POST", f"{pid}/video_reels", tok, params={"upload_phase": "start"})
        vid = st["video_id"]
        data = files[0].read_bytes()
        up = _request("POST", f"{RUPLOAD}/{vid}", body=data, timeout=600,
                      headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(len(data)),
                               "Content-Type": "application/octet-stream"})
        if not up.get("success"):
            raise SystemExit(f"A videó feltöltése nem sikerült: {up}")
        print(f"    videó feltöltve: {files[0].name} ({len(data) / 1e6:.1f} MB)")
        fin = {"upload_phase": "finish", "video_id": vid, "description": msg, "title": it["title"][:100]}
        fin.update({"video_state": "SCHEDULED", "scheduled_publish_time": int(when.timestamp())} if when else {"video_state": "PUBLISHED"})
        g("POST", f"{pid}/video_reels", tok, params=fin)
        ent.update(video_id=vid, post_id=vid)
        if cover:
            try:
                g("POST", f"{vid}/thumbnails", tok, params={"is_preferred": "true"}, files={"source": cover[0]})
                ent["cover"] = True
            except GraphError as e:
                print(f"    (a borítókép beállítása nem sikerült, a Facebook választ egyet: {e})")
    elif form == "story":
        if when:
            raise SystemExit("Storyt a Meta nem enged ütemezni – csak azonnal: post <id> --now --yes")
        r = g("POST", f"{pid}/photos", tok, params={"published": "false"}, files={"source": files[0]})
        s = g("POST", f"{pid}/photo_stories", tok, params={"photo_id": r["id"]})
        ent.update(photo_id=r["id"], post_id=s.get("post_id") or s.get("id"))
    return ent


def _check_when(when):
    if when is None:
        return
    if when < now() + MIN_LEAD:
        raise SystemExit(f"Az időpont túl közel van vagy elmúlt ({when:%Y-%m-%d %H:%M}) – legalább 15 perccel későbbre ütemezz, vagy használd a --now kapcsolót.")
    if when > now() + MAX_AHEAD:
        raise SystemExit(f"Az időpont túl messze van ({when:%Y-%m-%d}) – a Facebook legfeljebb ~28 nappal előre ütemez.")


def cmd_schedule():
    cfg = load_cfg() if YES else None
    only = set(filter(None, (opt("--only") or "").split(",")))
    rows = [r for r in fb_slots(load_items(), int(opt("--days", "28"))) if r["form"] and r["form"] != "story"
            and (r["state"] == "esedékes" or (r["state"].startswith("ellenőrizd") and r["it"]["id"] in only))
            and (not only or r["it"]["id"] in only)]
    rows = [r for r in rows if r["when"] >= now() + MIN_LEAD]
    if not rows:
        print("Nincs ütemezhető idősáv.")
        return
    print(("Ütemezés a Facebookon:" if YES else "[próbafutás – a --yes kapcsolóval ütemez]") + "\n")
    log = load_log()
    for r in rows:
        print(f"  {r['when']:%Y-%m-%d %H:%M}  {FORM_HU[r['form']]:<10} {r['it']['id']:<18} {r['it']['title'][:50]}")
        if not YES:
            continue
        try:
            ent = publish(cfg, r["it"], r["slot"], r["when"], r["form"])
        except GraphError as e:
            print(f"    ✗ {e}")
            continue
        log["posts"][r["key"]] = ent
        save_log(log)                                   # minden poszt után ment – megszakadás esetén sem duplikál
        print(f"    ✓ ütemezve · {ent.get('post_id')}")
        time.sleep(2)
    if not YES:
        print(f"\n{len(rows)} poszt ütemeződne.")


def cmd_post():
    pos = [a for a in ARGS[1:] if not a.startswith("--") and a not in {opt("--slot"), opt("--at")}]
    if not pos:
        sys.exit("Add meg a tartalom azonosítóját, pl.: post k_quiz --now --yes")
    items = load_items()
    it = items.get(pos[0]) or sys.exit(f"Nincs ilyen tartalom: {pos[0]}")
    fbs = [s for s in it["slots"] if s["platform"] == "facebook"]
    slot = next((s for s in fbs if str(s["i"]) == opt("--slot")), fbs[0] if fbs else {"i": -1, "platform": "facebook", "note": ""})
    form, why = fb_form(it, slot)
    if not form:
        sys.exit(f"{it['id']} nem posztolható Facebookra: {why}")
    when = None if "--now" in ARGS else (local(*opt("--at").split(" ")) if opt("--at") else local(slot["date"], slot.get("time") or "12:00"))
    _check_when(when)
    key = f"{it['id']}#{slot['i']}"
    log = load_log()
    if key in log["posts"] and "--force" not in ARGS:
        sys.exit(f"Ez már a naplóban van ({log['posts'][key]['mode']}, {log['posts'][key].get('post_id')}). Visszavonás: cancel {it['id']} --yes, vagy --force.")
    label = "most" if not when else f"{when:%Y-%m-%d %H:%M}"
    print(f"{it['id']} · {FORM_HU[form]} · {label}\n---\n{caption(it)}\n---")
    if not YES:
        print("[próbafutás – a --yes kapcsolóval teszi ki]")
        return
    ent = publish(load_cfg(), it, slot, when, form)
    log["posts"][key] = ent
    save_log(log)
    print(f"✓ {'kint van' if not when else 'ütemezve'} · {ent.get('post_id')}")


def cmd_scheduled():
    cfg = load_cfg()
    tok, pid = cfg["page_token"], cfg["page_id"]
    log = load_log()["posts"]
    sp = g("GET", f"{pid}/scheduled_posts", tok, params={"fields": "id,message,scheduled_publish_time", "limit": 100}).get("data", [])
    by_post = {e.get("post_id"): k for k, e in log.items()}
    reels = {k: e for k, e in log.items() if e.get("form") == "reels" and e["mode"] == "scheduled"}
    # A Reels saját posztazonosítót kap (nem a videóét) – ütemezési idő szerint párosítjuk.
    reel_at = {e["when"][:16]: k for k, e in reels.items()}
    print(f"A Facebookon ütemezett posztok ({len(sp)}):")
    for p in sorted(sp, key=lambda p: p.get("scheduled_publish_time", 0)):
        t = dt.datetime.fromtimestamp(int(p.get("scheduled_publish_time", 0)))
        k = by_post.get(p["id"]) or (reel_at.get(f"{t:%Y-%m-%dT%H:%M}") and reel_at[f"{t:%Y-%m-%dT%H:%M}"] + " (Reels)")
        print(f"  {t:%m-%d %H:%M}  {k or '(nem a naplóból)':<22} {(p.get('message') or '').splitlines()[0][:60] if p.get('message') else ''}")
    for k, e in reels.items():
        try:
            v = g("GET", e["video_id"], tok, params={"fields": "status,permalink_url"})
            st = (v.get("status") or {}).get("video_status", "?")
        except GraphError as ex:
            st = f"hiba: {ex.err.get('message', '')[:40]}"
        print(f"  {e['when'][5:16].replace('T', ' ')}  {k:<22} Reels-videó · {st}")


def cmd_cancel():
    pos = [a for a in ARGS[1:] if not a.startswith("--") and a != opt("--slot")]
    if not pos:
        sys.exit("Add meg a tartalom azonosítóját: cancel k_quiz --yes")
    cfg = load_cfg()
    log = load_log()
    keys = [k for k in log["posts"] if k.split("#")[0] == pos[0] and (opt("--slot") is None or k.endswith("#" + opt("--slot")))]
    if not keys:
        sys.exit("Nincs ilyen bejegyzés a naplóban.")
    for k in keys:
        e = log["posts"][k]
        print(f"{k}: {e['mode']} · {e.get('post_id')}")
        if not YES:
            print("  [próbafutás – a --yes kapcsolóval törli a Facebookról]")
            continue
        g("DELETE", e.get("video_id") or e["post_id"], cfg["page_token"])
        del log["posts"][k]
        save_log(log)
        print("  ✓ törölve a Facebookról és a naplóból")


def cmd_posts():
    cfg = load_cfg()
    ps = g("GET", f"{cfg['page_id']}/posts", cfg["page_token"],
           params={"fields": "id,message,created_time,permalink_url", "limit": int(opt("--limit", "20"))}).get("data", [])
    for p in ps:
        print(f"  {p['created_time'][:16].replace('T', ' ')}  {p['id']:<34} {(p.get('message') or '').splitlines()[0][:60] if p.get('message') else '(nincs szöveg)'}")


def cmd_insights():
    cfg = load_cfg()
    tok = cfg["page_token"]
    log = load_log()["posts"]
    out, metrics = {}, {}
    for k, e in sorted(log.items()):
        if e["mode"] == "scheduled" and dt.datetime.fromisoformat(e["when"]) > now():
            continue
        oid = e.get("post_id")
        row = {}
        try:
            if e.get("form") == "reels":
                v = g("GET", e["video_id"], tok, params={"fields": "permalink_url,post_id"})
                row["link"] = v.get("permalink_url")
                oid = v.get("post_id") or oid
                try:
                    vi = g("GET", f"{e['video_id']}/video_insights", tok).get("data", [])
                    for m in vi:
                        if m.get("name") in ("blue_reels_play_count", "post_impressions_unique", "total_video_views"):
                            row[m["name"]] = (m.get("values") or [{}])[0].get("value")
                except GraphError:
                    pass
            p = g("GET", oid, tok, params={"fields": "permalink_url,shares,reactions.summary(total_count).limit(0),comments.summary(total_count).limit(0)"})
            row["link"] = row.get("link") or p.get("permalink_url")
            row["likes"] = ((p.get("reactions") or {}).get("summary") or {}).get("total_count", 0)
            row["comments"] = ((p.get("comments") or {}).get("summary") or {}).get("total_count", 0)
            row["shares"] = (p.get("shares") or {}).get("count", 0)
            for m in ("post_impressions_unique", "post_clicks"):      # read_insights kell hozzá; ami nem megy, kimarad
                try:
                    d = g("GET", f"{oid}/insights", tok, params={"metric": m}).get("data", [])
                    if d:
                        row[m] = (d[0].get("values") or [{}])[0].get("value")
                except GraphError:
                    pass
        except GraphError as ex:
            row["error"] = str(ex)
        out[k] = row
        reach = row.get("post_impressions_unique") or row.get("blue_reels_play_count")
        item, slot = k.split("#")
        metrics.setdefault(item, {"s": {}})["s"][slot] = {kk: vv for kk, vv in {
            "reach": reach, "likes": row.get("likes"), "comments": row.get("comments"), "shares": row.get("shares"),
            "clicks": row.get("post_clicks"), "source": "facebook-api", "at": now().isoformat(timespec="minutes")}.items() if vv is not None}
        print(f"  {k:<22} elérés {reach if reach is not None else '–':>6} · reakció {row.get('likes', '–')} · komment {row.get('comments', '–')}"
              f" · megosztás {row.get('shares', '–')} · kattintás {row.get('post_clicks', '–')}  {row.get('error', '')}")
    if opt("--json"):
        pathlib.Path(opt("--json")).write_text(json.dumps({"raw": out, "metrics": metrics}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n→ {opt('--json')} (a „metrics” rész a CMS Eredmények fülének formája)")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    cmd = ARGS[0] if ARGS else "help"
    if cmd in ("--version", "version"):
        print(f"Pacsi facebook.py · marketing v{VERSION} · Graph API {API}")
        return
    fn = {"setup": cmd_setup, "check": cmd_check, "test": cmd_test, "plan": cmd_plan, "schedule": cmd_schedule,
          "post": cmd_post, "scheduled": cmd_scheduled, "cancel": cmd_cancel, "posts": cmd_posts, "insights": cmd_insights}.get(cmd)
    if not fn:
        print(__doc__)
        return
    try:
        fn()
    except GraphError as e:
        sys.exit(f"✗ {e}")


if __name__ == "__main__":
    main()
