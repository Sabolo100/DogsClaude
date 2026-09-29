"""Pacsi eDM – Mailchimp Marketing API (csak szabványos Python, külső csomag nélkül).

A kulcs: a repó gyökerében a Mailchimp_API.txt (csak a kulcs, pl. abcd…-us21). Soha nem íródik ki, nem kerül
a kimenetbe és a verziókezelésbe. Az állapot (közönség, kampányok, feltöltött képek, statisztika):
marketing/email/state/mailchimp.json (szintén nincs verziókezelve).

Parancsok:
  python marketing/tools/mailchimp.py ping                 kulcs és fiók ellenőrzése (csomag, feliratkozók)
  python marketing/tools/mailchimp.py setup [--use <id>]   a Pacsi közönség létrehozása (vagy egy meglévő átvétele) + mezők, csoportok, „partner” címke
  python marketing/tools/mailchimp.py images [L1 …]        a levélképek feltöltése a Mailchimp tárhelyére (max. 1200×1200 px)
  python marketing/tools/mailchimp.py push L1 W01 …        kampány PISZKOZAT létrehozása / frissítése (képek + HTML + sima szöveg)
       --all              minden kész, nem helykitöltős, jövőbeli levél
       --test a@b.hu      tesztlevél a megadott címre (a Mailchimp napi tesztkeretéből)
       --force            helykitöltős (todo) levelet is feltölt
  python marketing/tools/mailchimp.py templates            az üdvözlő sorozat leveleit sablonként tölti fel (Customer Journey-hez)
  python marketing/tools/mailchimp.py schedule L1 …        jóváhagyott piszkozat ütemezése (fizetős csomag; config: mailchimp.mode = schedule)
  python marketing/tools/mailchimp.py send-due --yes       a lejárt időpontú, jóváhagyott piszkozatok kiküldése (ingyenes csomagon; mode = send-due)
  python marketing/tools/mailchimp.py sync                 kampányállapot, megnyitás/kattintás, közönség-statisztika → state → CMS
  python marketing/tools/mailchimp.py import [--yes]       a „Kéri a hírlevelet” állapotú partnerek felvétele (pending = megerősítő levél)
  python marketing/tools/mailchimp.py status               áttekintő táblázat
  --dry-run: semmit nem küld, csak kiírja, mit tenne.   --version: verzió.

Jóváhagyás: marketing/email/state/approvals.json – {"L1": {"approved": true, "subject": "…"}}. A CMS „Jóváhagyom”
gombja a claude.ai-s tárolóba ír; Claude onnan másolja ide (ArtifactData), mielőtt ütemez vagy kiküld.
"""
import base64
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
STATE_P = MK / "email" / "state" / "mailchimp.json"
APPROVALS_P = MK / "email" / "state" / "approvals.json"
KEY_P = ROOT / "Mailchimp_API.txt"
VERSION = (MK / "VERSION").read_text(encoding="utf-8").strip()
DRY = "--dry-run" in sys.argv


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B = _load("email_build", MK / "tools" / "email_build.py")     # levélrender, képlista, terv, config
P, F, CFG = B.P, B.F, B.CFG
BY = {e["id"]: e for e in P.EMAILS}


# ------------------------------------------------------------------ állapot
def load_state():
    return json.loads(STATE_P.read_text(encoding="utf-8")) if STATE_P.exists() else {}


def save_state(st):
    if DRY:                      # próbaüzemben semmi nem íródik az állapotba
        return
    STATE_P.parent.mkdir(parents=True, exist_ok=True)
    STATE_P.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def approvals():
    return json.loads(APPROVALS_P.read_text(encoding="utf-8")) if APPROVALS_P.exists() else {}


# ------------------------------------------------------------------ API
class MCError(Exception):
    pass


def key():
    if not KEY_P.exists():
        raise MCError("Nincs Mailchimp API-kulcs: tedd a repó gyökerébe a Mailchimp_API.txt fájlba (csak a kulcsot).")
    k = KEY_P.read_text(encoding="utf-8").strip().split()[0]
    if "-" not in k:
        raise MCError("A kulcs formátuma nem jó: a végén az adatközpont kell legyen, pl. …-us21.")
    return k


def api(method, path, body=None, query=None):
    """Mailchimp Marketing API hívás. Hiba esetén MCError a Mailchimp üzenetével (a kulcs soha nem jelenik meg)."""
    if DRY:
        print(f"    [dry-run] {method} {path}" + (f"  {json.dumps(body, ensure_ascii=False)[:160]}…" if body else ""))
        return {"id": f"dry-{hashlib.sha1(path.encode()).hexdigest()[:6]}", "web_id": 0, "status": "save", "full_size_url": f"https://example.invalid/{path}"}
    k = key()
    url = f"https://{k.rsplit('-', 1)[1]}.api.mailchimp.com/3.0{path}" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Basic " + base64.b64encode(f"pacsi:{k}".encode()).decode(),
        "Content-Type": "application/json", "User-Agent": f"pacsi-edm/{VERSION}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "ignore")
            if e.code == 429 and attempt < 3:
                time.sleep(2 + attempt * 3)
                continue
            try:
                j = json.loads(txt)
                msg = f"{j.get('title', '')}: {j.get('detail', '')}"
                if j.get("errors"):
                    msg += " " + "; ".join(f"{x.get('field')}: {x.get('message')}" for x in j["errors"])
            except ValueError:
                msg = txt[:300]
            raise MCError(f"HTTP {e.code} {method} {path} – {msg}") from None
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(2)
                continue
            raise MCError(f"Hálózati hiba: {e.reason}") from None


def paged(path, key_name, query=None):
    out, off = [], 0
    while True:
        q = {"count": 200, "offset": off, **(query or {})}
        r = api("GET", path, query=q)
        items = r.get(key_name, [])
        out += items
        if DRY or len(items) < 200:
            return out
        off += 200


# ------------------------------------------------------------------ idő
def budapest_to_utc(date, hhmm):
    y, m, d = map(int, date.split("-"))
    hh, mm = map(int, hhmm.split(":"))
    try:
        from zoneinfo import ZoneInfo
        local = dt.datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(CFG["schedule"]["timezone"]))
        return local.astimezone(dt.timezone.utc)
    except Exception:  # noqa: BLE001 – zoneinfo adatbázis nélkül: EU-s nyári időszámítás kézzel
        def last_sunday(month):
            x = dt.date(y, month, 31)
            return x - dt.timedelta(days=(x.weekday() + 1) % 7)
        naive = dt.datetime(y, m, d, hh, mm)
        start = dt.datetime.combine(last_sunday(3), dt.time(2))
        end = dt.datetime.combine(last_sunday(10), dt.time(3))
        off = 2 if start <= naive < end else 1
        return (naive - dt.timedelta(hours=off)).replace(tzinfo=dt.timezone.utc)


# ------------------------------------------------------------------ parancsok
def cmd_ping(st):
    api("GET", "/ping")
    r = api("GET", "/")
    st["account"] = {"name": r.get("account_name"), "plan": r.get("pricing_plan_type"), "dc": key().rsplit("-", 1)[1] if not DRY else "dry",
                     "subscribers": r.get("total_subscribers"), "checked": dt.datetime.now().isoformat(timespec="seconds")}
    save_state(st)
    a = st["account"]
    print(f"  OK · fiók: {a['name']} · csomag: {a['plan']} · összes feliratkozó: {a['subscribers']}")
    if a["plan"] == "forever_free":
        print("  ! Ingyenes csomag: 250 kontakt, havi 500 küldés, nincs ütemezés → automatikus küldéshez a send-due mód kell.")


def config_ready():
    miss = [m for m in B.config_missing() if not m.startswith(("Közösségi", "Adatkezelési", "Aláíró", "Mailchimp API"))]
    if miss:
        raise MCError("A config.json hiányos:\n    - " + "\n    - ".join(miss))


def list_body():
    c, s, a = CFG["company"], CFG["sender"], CFG["audience"]
    return {"name": a["name"],
            "contact": {"company": c.get("legal_name") or c["name"], "address1": c["address1"], "city": c["city"], "state": "",
                        "zip": c["zip"], "country": c.get("country", "HU")},
            "permission_reminder": a["permission_reminder"],
            "campaign_defaults": {"from_name": s["from_name"], "from_email": s["from_email"], "subject": "", "language": a.get("language", "hu")},
            "email_type_option": False, "double_optin": bool(a.get("double_optin", True)),
            "marketing_permissions": bool(a.get("marketing_permissions", True)), "use_archive_bar": False}


def cmd_setup(st, args):
    config_ready()
    use = args[args.index("--use") + 1] if "--use" in args else None
    lists = paged("/lists", "lists")
    mine = next((x for x in lists if x.get("name") == CFG["audience"]["name"]), None)
    if use:
        lst = api("PATCH", f"/lists/{use}", list_body())
        print(f"  közönség átvéve és beállítva: {lst.get('name')} ({use})")
    elif mine:
        lst = mine
        print(f"  a közönség már létezik: {lst['name']} ({lst['id']})")
    else:
        try:
            lst = api("POST", "/lists", list_body())
            print(f"  közönség létrehozva: {lst.get('name')} ({lst.get('id')})")
        except MCError as e:
            if lists and ("maximum" in str(e).lower() or "limit" in str(e).lower() or "400" in str(e)):
                print("  ! Új közönség nem hozható létre (az ingyenes csomag 1 közönséget enged). A meglévők:")
                for x in lists:
                    print(f"      {x['id']}  {x['name']}  ({x['stats']['member_count']} tag)")
                print("    Egy meglévő átvétele (átnevezi és beállítja): python marketing/tools/mailchimp.py setup --use <id>")
                return
            raise
    lid = lst["id"]
    # egyedi mezők
    have = {f["tag"] for f in paged(f"/lists/{lid}/merge-fields", "merge_fields")}
    for mf in CFG["audience"]["merge_fields"]:
        if mf["tag"] not in have:
            api("POST", f"/lists/{lid}/merge-fields", {"tag": mf["tag"], "name": mf["name"], "type": mf["type"], "public": False})
            print(f"  mező: {mf['tag']} ({mf['name']})")
    # érdeklődési csoportok
    cats = paged(f"/lists/{lid}/interest-categories", "categories")
    cat = next((c for c in cats if c["title"] == CFG["audience"]["interests_title"]), None)
    if not cat:
        cat = api("POST", f"/lists/{lid}/interest-categories", {"title": CFG["audience"]["interests_title"], "type": "checkboxes"})
    ints = paged(f"/lists/{lid}/interest-categories/{cat['id']}/interests", "interests")
    names = {i["name"]: i["id"] for i in ints}
    for n in CFG["audience"]["interests"]:
        if n not in names:
            names[n] = api("POST", f"/lists/{lid}/interest-categories/{cat['id']}/interests", {"name": n})["id"]
    # „partner” címke (statikus szegmens) a partnerlevelekhez
    segs = paged(f"/lists/{lid}/segments", "segments", {"type": "static"})
    seg = next((x for x in segs if x["name"] == "partner"), None) or api("POST", f"/lists/{lid}/segments", {"name": "partner", "static_segment": []})
    full = api("GET", f"/lists/{lid}")
    st["list"] = {"id": lid, "web_id": full.get("web_id"), "name": full.get("name"), "subscribe_url_short": full.get("subscribe_url_short"),
                  "subscribe_url_long": full.get("subscribe_url_long"), "interest_category": cat["id"], "interests": names,
                  "partner_segment": seg["id"], "double_optin": full.get("double_optin")}
    save_state(st)
    if not CFG["links"].get("signup") and full.get("subscribe_url_long") and not DRY:
        cfg_p = MK / "email" / "config.json"
        c = json.loads(cfg_p.read_text(encoding="utf-8"))
        c["links"]["signup"] = full["subscribe_url_long"]
        cfg_p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  feliratkozó űrlap: {full['subscribe_url_long']} (bekerült a config.json-ba)")
    print("  kész. Következő: a Mailchimpben hitelesítsd a feladó domainjét (DKIM, DMARC), majd: push L1")


def folder_id(st, kind):
    """kind: file (képmappa) vagy campaign (kampánymappa)"""
    key_ = f"{kind}_folder"
    if st.get(key_):
        return st[key_]
    path, lk = ("/file-manager/folders", "folders") if kind == "file" else ("/campaign-folders", "folders")
    name = CFG["mailchimp"]["folder"]
    f = next((x for x in paged(path, lk) if x["name"] == name), None) or api("POST", path, {"name": name})
    st[key_] = f["id"]
    save_state(st)
    return f["id"]


def upload_images(st, names):
    files = st.setdefault("files", {})
    fid = folder_id(st, "file")
    n = 0
    for name in sorted(names):
        p = B.IMG / name
        if not p.exists():
            raise MCError(f"hiányzó kép: {name} – futtasd előbb az email_build.py-t")
        sha = hashlib.sha1(p.read_bytes()).hexdigest()
        if files.get(name, {}).get("sha1") == sha:
            continue
        from PIL import Image
        with Image.open(p) as im:
            if max(im.size) > B.MAX_SIDE:
                raise MCError(f"{name}: {im.size[0]}×{im.size[1]} px – a Mailchimp legfeljebb 1200×1200-at fogad")
        r = api("POST", "/file-manager/files", {"folder_id": fid, "name": "pacsi_" + name.replace("/", "_"),
                                                  "file_data": base64.b64encode(p.read_bytes()).decode()})
        files[name] = {"id": r.get("id"), "url": r.get("full_size_url"), "sha1": sha}
        n += 1
        save_state(st)
    print(f"  képek: {n} új/módosult feltöltve, {len(names) - n} már fent volt")


def render_mc(st, e, subject=None):
    e2 = dict(e, subject=subject or e["subject"])
    ctx = F.Ctx(e2, CFG, B.img_url_mc(st), mode="mc", version=VERSION, build=B.src_hash())
    html, text = F.render(ctx), F.render_text(ctx)
    missing = [n for n in B.images_of(e) if n not in st.get("files", {})]
    if missing and not DRY:
        raise MCError(f"{e['id']}: fel nem töltött képek: {', '.join(missing)}")
    return html, text


def recipients(st, e):
    r = {"list_id": st["list"]["id"]}
    if e["segment"] == "partner":
        r["segment_opts"] = {"saved_segment_id": st["list"]["partner_segment"]}
    return r


def cmd_push(st, ids, args):
    if not st.get("list") and not DRY:
        raise MCError("Nincs közönség: futtasd előbb a setup parancsot.")
    st.setdefault("list", {"id": "dry-list", "partner_segment": 0})
    appr = approvals()
    for eid in ids:
        e = BY[eid]
        if e["segment"] == "journey":
            print(f"  {eid}: üdvözlő levél – ez sablonként megy fel (templates parancs), kihagyva")
            continue
        if e.get("todo") and "--force" not in args:
            print(f"  {eid}: KIHAGYVA – kitöltendő tartalom: {e['todo']}")
            continue
        camp = st.setdefault("campaigns", {}).get(eid, {})
        if camp.get("campaign_id") and not DRY:
            cur = api("GET", f"/campaigns/{camp['campaign_id']}", query={"fields": "status,web_id"})
            if cur.get("status") not in ("save", "paused"):
                print(f"  {eid}: már {cur.get('status')} állapotú a Mailchimpben – nem írom felül")
                continue
        upload_images(st, B.images_of(e))
        subject = (appr.get(eid) or {}).get("subject") or e["subject"]
        html, text = render_mc(st, e, subject)
        s = CFG["sender"]
        body = {"type": "regular", "recipients": recipients(st, e),
                "settings": {"subject_line": subject, "preview_text": e["preheader"], "title": f"{eid} · {e['title']}",
                             "from_name": s["from_name"], "reply_to": s.get("reply_to") or s["from_email"], "to_name": "*|FNAME|*",
                             "auto_footer": False, "folder_id": folder_id(st, "campaign"), "fb_comments": False},
                "tracking": {"opens": True, "html_clicks": True, "text_clicks": True}}
        if camp.get("campaign_id") and not DRY:
            c = api("PATCH", f"/campaigns/{camp['campaign_id']}", body)
        else:
            c = api("POST", "/campaigns", body)
        api("PUT", f"/campaigns/{c['id']}/content", {"html": html, "plain_text": text})
        build = hashlib.sha1(html.encode("utf-8")).hexdigest()[:7]
        st["campaigns"][eid] = {**camp, "campaign_id": c["id"], "web_id": c.get("web_id"), "status": c.get("status", "save"),
                                "pushed": dt.datetime.now().isoformat(timespec="seconds"), "pushed_build": build, "subject": subject}
        save_state(st)
        dc = st.get("account", {}).get("dc", "usX")
        print(f"  {eid}: PISZKOZAT kész · {len(html.encode()) // 1024} kB · https://{dc}.admin.mailchimp.com/campaigns/edit?id={c.get('web_id')}")
        if "--test" in args:
            to = [x for x in args[args.index("--test") + 1].split(",") if "@" in x]
            api("POST", f"/campaigns/{c['id']}/actions/test", {"test_emails": to, "send_type": "html"})
            print(f"      tesztlevél elküldve: {len(to)} címre")


def cmd_templates(st):
    for e in [x for x in P.EMAILS if x["segment"] == "journey"]:
        upload_images(st, B.images_of(e))
        html, _ = render_mc(st, e)
        name = f"Pacsi – Üdvözlő {e['no']}/3 · {e['title']}"[:50]
        t = st.setdefault("templates", {}).get(e["id"])
        if t and not DRY:
            api("PATCH", f"/templates/{t['id']}", {"name": name, "html": html})
        else:
            r = api("POST", "/templates", {"name": name, "html": html})
            st["templates"][e["id"]] = {"id": r.get("id"), "name": name}
        save_state(st)
        print(f"  sablon: {name} (tárgysor a Journeyben: „{e['subject']}”, késleltetés: {e['delay']})")


def cmd_schedule(st, ids):
    appr = approvals()
    for eid in ids:
        e, camp = BY[eid], st.get("campaigns", {}).get(eid)
        if not camp:
            print(f"  {eid}: nincs piszkozat – előbb push")
            continue
        if not (appr.get(eid) or {}).get("approved"):
            print(f"  {eid}: nincs jóváhagyva (approvals.json) – nem ütemezem")
            continue
        when = budapest_to_utc(e["date"], e["time"])
        if when < dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=20):
            print(f"  {eid}: az időpont ({e['date']} {e['time']}) már elmúlt vagy túl közel van")
            continue
        api("POST", f"/campaigns/{camp['campaign_id']}/actions/schedule", {"schedule_time": when.strftime("%Y-%m-%dT%H:%M:%S+00:00"), "timewarp": False})
        camp.update(status="schedule", send_time=when.isoformat())
        save_state(st)
        print(f"  {eid}: ÜTEMEZVE {e['date']} {e['time']} (Budapest)")


def cmd_send_due(st, args):
    if CFG["mailchimp"]["mode"] != "send-due":
        raise MCError("A config.json mailchimp.mode értéke nem send-due – az automatikus kiküldés ki van kapcsolva.")
    appr, now = approvals(), dt.datetime.now(dt.timezone.utc)
    due = [e for e in P.EMAILS if e.get("date") and e["id"] in st.get("campaigns", {})
           and st["campaigns"][e["id"]].get("status") == "save" and (appr.get(e["id"]) or {}).get("approved")
           and budapest_to_utc(e["date"], e["time"]) <= now < budapest_to_utc(e["date"], e["time"]) + dt.timedelta(hours=20)]
    if not due:
        print("  nincs esedékes, jóváhagyott levél")
        return
    for e in due:
        if "--yes" not in args:
            print(f"  {e['id']}: esedékes – a kiküldéshez add hozzá: --yes")
            continue
        api("POST", f"/campaigns/{st['campaigns'][e['id']]['campaign_id']}/actions/send")
        st["campaigns"][e["id"]].update(status="sending", send_time=now.isoformat(timespec="seconds"))
        save_state(st)
        print(f"  {e['id']}: KIKÜLDVE")


def cmd_sync(st):
    if st.get("list"):
        l_ = api("GET", f"/lists/{st['list']['id']}")
        s = l_.get("stats", {})
        st["audience"] = {k: s.get(k) for k in ("member_count", "unsubscribe_count", "cleaned_count", "member_count_since_send",
                                                "campaign_count", "open_rate", "click_rate", "last_sub_date")}
    for eid, camp in st.get("campaigns", {}).items():
        c = api("GET", f"/campaigns/{camp['campaign_id']}", query={"fields": "status,send_time,emails_sent,web_id"})
        camp.update(status=c.get("status"), send_time=c.get("send_time"), emails_sent=c.get("emails_sent"))
        if c.get("status") == "sent":
            r = api("GET", f"/reports/{camp['campaign_id']}")
            camp["report"] = {"sent": r.get("emails_sent"), "open_rate": (r.get("opens") or {}).get("open_rate"),
                              "unique_opens": (r.get("opens") or {}).get("unique_opens"), "click_rate": (r.get("clicks") or {}).get("click_rate"),
                              "unique_clicks": (r.get("clicks") or {}).get("unique_subscriber_clicks"), "unsubscribed": r.get("unsubscribed"),
                              "bounces": sum((r.get("bounces") or {}).values()) if isinstance(r.get("bounces"), dict) else None}
    st["synced"] = dt.datetime.now().isoformat(timespec="seconds")
    save_state(st)
    a = st.get("audience") or {}
    print(f"  szinkron kész · feliratkozók: {a.get('member_count')} · kampányok: {len(st.get('campaigns', {}))}")


def cmd_import(st, args):
    """A kapcsolati adatbázisból a „Kéri a hírlevelet” állapotúak (a CMS felülírásaival együtt) → Mailchimp."""
    cp = MK / "email" / "data" / "contacts.json"
    ov_p = MK / "email" / "state" / "contact_overrides.json"
    if not cp.exists():
        raise MCError("Nincs kapcsolati adatbázis (marketing/email/data/contacts.json).")
    contacts = json.loads(cp.read_text(encoding="utf-8"))["contacts"]
    ov = json.loads(ov_p.read_text(encoding="utf-8")) if ov_p.exists() else {}
    want = [c for c in contacts if (ov.get(c["id"], {}).get("status") or c.get("status")) == "feliratkozna"]
    want += [c for c in ov.values() if c.get("added") and c.get("status") == "feliratkozna"]
    if not want:
        print("  nincs „Kéri a hírlevelet” állapotú kapcsolat")
        return
    status = CFG["mailchimp"].get("import_status", "pending")
    for c in want:
        email = ((ov.get(c.get("id"), {}).get("email")) or (c.get("emails") or [c.get("email", "")])[0]).strip().lower()
        if not email:
            continue
        if "--yes" not in args:
            print(f"  [próba] {pid_of(c, email)} {email} · {c.get('name')} · {c.get('category')} → {status}")
            continue
        h = hashlib.md5(email.encode()).hexdigest()
        api("PUT", f"/lists/{st['list']['id']}/members/{h}", {
            "email_address": email, "status_if_new": status,
            "merge_fields": {"ORG": (c.get("name") or "")[:255], "TIPUS": c.get("category", ""), "PID": pid_of(c, email)}})
        api("POST", f"/lists/{st['list']['id']}/members/{h}/tags", {"tags": [{"name": "partner", "status": "active"},
                                                                         {"name": c.get("category", "egyeb"), "status": "active"}]})
        print(f"  felvéve ({status}): {pid_of(c, email)} {email}")
    if "--yes" not in args:
        print("  Ez csak próba volt. Felvétel: import --yes")


def pid_of(c, email):
    """a kapcsolati adatbázis állandó azonosítója (PK0001…) az adott e-mail-címhez"""
    em, ids = c.get("emails") or [], c.get("eids") or []
    return ids[em.index(email)] if email in em and em.index(email) < len(ids) else ""


def cmd_status(st):
    appr = approvals()
    print(f"  {'ID':6} {'dátum':16} {'szegmens':8} {'terv':8} {'jóváhagyva':10} {'Mailchimp':10} tárgy")
    for e in P.EMAILS:
        c = st.get("campaigns", {}).get(e["id"], {})
        when = f"{e.get('date', '')} {e.get('time', '')}" if e.get("date") else e.get("delay", "")[:16]
        print(f"  {e['id']:6} {when:16} {e['segment']:8} {e['status']:8} {'igen' if (appr.get(e['id']) or {}).get('approved') else '–':10} {c.get('status', '–'):10} {e['subject']}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # a Windows-konzol kódlapja ne akadjon el az emojikon
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "--version":
        print(f"Pacsi eDM – mailchimp.py {VERSION}")
        return
    cmd, rest = args[0], args[1:]
    ids = [a for a in rest if a in BY]
    unknown = [a for a in rest if not a.startswith("--") and a not in BY and "@" not in a and cmd in ("push", "images", "schedule")]
    if unknown:
        raise SystemExit(f"Ismeretlen levélazonosító: {', '.join(unknown)} (lehetséges: {', '.join(BY)})")
    st = load_state()
    try:
        if cmd == "ping":
            cmd_ping(st)
        elif cmd == "setup":
            cmd_setup(st, rest)
        elif cmd == "images":
            upload_images(st, set().union(*(B.images_of(BY[i]) for i in (ids or list(BY)))))
        elif cmd == "push":
            if "--all" in rest:
                today = dt.date.today().isoformat()
                ids = [e["id"] for e in P.EMAILS if e["segment"] != "journey" and e["status"] in ("kesz", "jovahagyva") and not e.get("todo") and e.get("date", "") >= today]
            if not ids:
                raise SystemExit("Adj meg levélazonosítót (pl. push L1 W01) vagy --all.")
            cmd_push(st, ids, rest)
        elif cmd == "templates":
            cmd_templates(st)
        elif cmd == "schedule":
            cmd_schedule(st, ids)
        elif cmd == "send-due":
            cmd_send_due(st, rest)
        elif cmd == "sync":
            cmd_sync(st)
        elif cmd == "import":
            cmd_import(st, rest)
        elif cmd == "status":
            cmd_status(st)
        else:
            raise SystemExit(f"Ismeretlen parancs: {cmd}")
    except MCError as e:
        raise SystemExit(f"  ! {e}")


if __name__ == "__main__":
    main()
