"""Pacsi Marketing – a CMS „Áttekintés” és „Eredmények” fülének build-idejű adatai (marketing 1.4.0).

Három rész:
  1. Ellenőrzések: a tartalmak, levelek, beállítások és a kiküldés hibái és figyelmeztetései egy listában,
     mindegyik egy hivatkozással (melyik tartalom, levél vagy fül), hogy a CMS-ből egy kattintással odaugorj.
  2. Megkeresések: a partnerlevelek kiküldési naplójának összesítése (naponként, visszapattanás, hátralévő sor, szünet).
  3. Linkek: a posztokban, levelekben és profilokban szereplő linkek utolsó ellenőrzésének eredménye.

A build.py hívja (compute), de önállóan is futtatható:
  python marketing/tools/insights.py            az ellenőrzések kiírása
  python marketing/tools/insights.py --links    + minden link ellenőrzése a hálózaton (eredmény: content/linkcheck.json)
"""
import concurrent.futures as cf
import datetime as dt
import html
import importlib.util
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

MK = pathlib.Path(__file__).resolve().parents[1]
STATE = MK / "email" / "state"
LINKS_P = MK / "content" / "linkcheck.json"
BOUNCE_LIMIT = .05          # 5% fölötti visszapattanás: a küldést szüneteltetni kell
# ezek a szolgáltatók robotnak nézik az ellenőrzést (403/429/999), ilyenkor az eredmény „nem ellenőrizhető”, nem hiba
BOT_WALLED = ("instagram.com", "facebook.com", "tiktok.com", "linkedin.com", "x.com", "twitter.com", "claude.ai")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def H(lvl, area, text, t=None, id=None):
    """egy ellenőrzési sor: szint (hiba / figyelem / info), terület, szöveg, hivatkozás (item / email / tab)"""
    return {"lvl": lvl, "area": area, "text": text, "ref": {"t": t, "id": id} if t else None}


# ------------------------------------------------------------------ tartalmak
def content_checks(data):
    out, PF = [], data["platforms"]
    for it in data["items"]:
        name = f"{it['title']} ({it['id']})"
        for pf, c in (it.get("copy") or {}).items():
            if pf not in PF:
                continue
            full = c.get("text", "") + ("\n\n" + c["tags"] if c.get("tags") else "")
            lim = PF[pf]["limit"]
            if len(full) > lim:
                out.append(H("hiba", "tartalom", f"{name}: a {PF[pf]['name']}-szöveg {len(full)} karakter (a korlát {lim}).", "item", it["id"]))
            tags = re.findall(r"#[^\s#]+", c.get("tags", ""))
            if PF[pf].get("maxTags") and len(tags) > PF[pf]["maxTags"]:
                out.append(H("hiba", "tartalom", f"{name}: {len(tags)} hashtag a {PF[pf]['name']}-szövegben (legfeljebb {PF[pf]['maxTags']}).", "item", it["id"]))
            if pf == "tiktok" and len(tags) > 5:
                out.append(H("info", "tartalom", f"{name}: {len(tags)} hashtag TikTokon – 3–5 elég.", "item", it["id"]))
            if pf == "youtube" and len(c.get("text", "").split("\n", 1)[0]) > 100:
                out.append(H("hiba", "tartalom", f"{name}: a YouTube-cím (első sor) hosszabb 100 karakternél.", "item", it["id"]))
        for s in it.get("slots", []):   # a profilképet és a borítót feltölteni kell, nem kiposztolni: ahhoz nem kell szöveg
            if it.get("kind") != "profil" and s["platform"] not in (it.get("copy") or {}) and s["platform"] in PF:
                out.append(H("info", "tartalom", f"{name}: van {PF[s['platform']]['name']}-idősáv ({s['date']}), de nincs hozzá posztszöveg.", "item", it["id"]))
        if it.get("kind") in ("kep", "karusszel", "story", "hirdetes", "video") and not it.get("alt"):
            out.append(H("figyelem", "tartalom", f"{name}: nincs alternatív szöveg (akadálymentesség).", "item", it["id"]))
        for f in it.get("files", []):
            if not f.get("bytes") and not f["src"].endswith(".zip"):
                out.append(H("hiba", "tartalom", f"{name}: hiányzik a fájl: {f['src']}", "item", it["id"]))
    return out


# ------------------------------------------------------------------ levelek, beállítások, indítás
def email_checks(data):
    em, out = data.get("email"), []
    if not em:
        return [H("figyelem", "email", "Az e-mail modul adatai hiányoznak (python marketing/tools/email_build.py).", "tab", "email")]
    for e in em["emails"]:
        errs = [t for k, t in e.get("checks", []) if k == "hiba"]
        if errs:
            when = f" ({e['date']})" if e.get("date") else ""
            more = f" (+{len(errs) - 1} további)" if len(errs) > 1 else ""
            out.append(H("hiba", "email", f"{e['id']}{when}: {errs[0]}{more}", "email", e["id"]))
    for m in em.get("configMissing", []):
        out.append(H("figyelem", "beallitas", f"Hiányzó beállítás: {m}", "tab", "email"))
    return out


def setup_checks(data):
    out = []
    for pl in data.get("setup") or []:
        for st in pl["steps"]:
            if st.get("limit") and st.get("copy") and len(st["copy"]) > st["limit"]:
                out.append(H("hiba", "inditas", f"{pl['name']}: túl hosszú szöveg ({len(st['copy'])}/{st['limit']}).", "tab", "inditas"))
    return out


# ------------------------------------------------------------------ megkeresések (kiküldési napló)
def outreach():
    log_p = STATE / "outreach_log.json"
    if not log_p.exists():
        return None, []
    try:
        log = json.loads(log_p.read_text(encoding="utf-8"))
    except ValueError:
        return None, [H("hiba", "kikuldes", "A kiküldési napló (email/state/outreach_log.json) sérült – a küldés addig ne induljon.", "tab", "attekintes")]
    days, bounces = {}, []
    for pid, v in log.items():
        if v.get("status") in ("elkuldve", "hiba") and v.get("sent"):
            d = days.setdefault(v["sent"][:10], {"date": v["sent"][:10], "sent": 0, "bounced": 0})
            d["sent"] += 1
            if v["status"] == "hiba":
                d["bounced"] += 1
        if v.get("status") == "hiba":
            bounces.append({"pid": pid, "org": v.get("org", ""), "email": v.get("email", ""), "error": v.get("error", ""), "sent": (v.get("sent") or "")[:16]})
    sent = sum(d["sent"] for d in days.values())
    bounced = sum(d["bounced"] for d in days.values())
    remaining, by_cat, cap = None, {}, None
    try:
        Q = _load("outreach_queue", MK / "tools" / "outreach_queue.py")
        q = Q.queue(log)
        remaining, cap = len(q), Q.DAILY_CAP
        for _, c, _ in q:
            by_cat[c["category"]] = by_cat.get(c["category"], 0) + 1
    except Exception as e:  # noqa: BLE001 – az áttekintés akkor is elkészül, ha a sor nem számolható
        print(f"  (a hátralévő sor nem számolható: {e})")
    stop = STATE / "STOP"
    pause = STATE / "PAUSE"
    paused_today = pause.exists() and pause.read_text(encoding="utf-8").startswith(dt.date.today().isoformat())
    run_p = STATE / "outreach_run.log"
    tail = run_p.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-4:] if run_p.exists() else []
    summary = {
        "sent": sent, "bounced": bounced, "rate": round(bounced / sent, 4) if sent else 0, "drafts": sum(1 for v in log.values() if v.get("status") == "piszkozat"),
        "days": sorted(days.values(), key=lambda d: d["date"]), "bounces": sorted(bounces, key=lambda b: b["sent"], reverse=True)[:25],
        "remaining": remaining, "byCategory": by_cat, "dailyCap": cap, "limit": BOUNCE_LIMIT,
        "paused": stop.exists() or paused_today,
        "pauseReason": stop.read_text(encoding="utf-8", errors="replace").strip() if stop.exists()
        else pause.read_text(encoding="utf-8").split("\n", 1)[-1].strip() if paused_today else "",
        "tail": tail,
    }
    health = []
    if sent >= 10 and bounced / sent > BOUNCE_LIMIT:
        health.append(H("figyelem", "kikuldes", f"Magas a visszapattanási arány: {bounced}/{sent} ({bounced / sent:.0%}). A kiküldés a felhasználó döntése szerint "
                        "címellenőrzés nélkül, napi 20 levéllel folytatódik; ha aznap legalább 3 cím visszapattan, aznapra megáll.", "tab", "attekintes"))
    if stop.exists():
        health.append(H("figyelem", "kikuldes", "A partnerlevelek kiküldése szünetel (email/state/STOP). " + (summary["pauseReason"] or ""), "tab", "attekintes"))
    elif paused_today:
        health.append(H("info", "kikuldes", "Mára bekapcsolt az automatikus szünet, holnap folytatódik. " + summary["pauseReason"], "tab", "attekintes"))
    return summary, health


# ------------------------------------------------------------------ linkek
def collect_links(data):
    """minden külső link és az, hogy hol szerepel"""
    where = {}

    def add(u, w):
        u = html.unescape(u).rstrip(".,;:)!?”'")
        if u.startswith("http") and "*|" not in u and "{{" not in u and "<" not in u:
            where.setdefault(u, set()).add(w)

    url_re = re.compile(r"https?://[^\s\"'<>)]+")
    for it in data["items"]:
        texts = [c.get("text", "") for c in (it.get("copy") or {}).values()] + [it.get("firstComment") or ""] + list(it.get("notes") or [])
        for t in texts:
            for u in url_re.findall(t):
                add(u, f"tartalom: {it['id']}")
    for pl in data.get("setup") or []:
        for st in pl["steps"]:
            for t in (st.get("link") or "", st.get("copy") or "", st.get("do") or ""):
                for u in url_re.findall(t):
                    add(u, f"indítás: {pl['name']}")
    for e in (data.get("email") or {}).get("emails", []):
        for u in re.findall(r'href="(https?://[^"]+)"', e.get("html", "")):
            add(u, f"levél: {e['id']}")
    for l in (data.get("brand") or {}).get("links", []):
        if l.get("url"):
            add(l["url"], "arculat")
    return {u: sorted(w) for u, w in where.items()}


def _check(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (PacsiLinkCheck)", "Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return {"status": r.status, "ok": True, "final": r.geturl()}
    except urllib.error.HTTPError as e:
        host = urllib.parse.urlparse(u).hostname or ""
        if e.code in (403, 429, 999) and any(host.endswith(b) for b in BOT_WALLED):
            return {"status": e.code, "ok": None}
        return {"status": e.code, "ok": e.code < 400}
    except Exception as e:  # noqa: BLE001
        return {"status": 0, "ok": False, "error": str(e)[:120]}


def check_links(data):
    links = collect_links(data)
    # a levelek linkjei csak az UTM-paraméterekben különböznek: az ellenőrzéshez elég a cél (utm_* és # nélkül) egyszer
    targets = {}
    for u in links:
        p = urllib.parse.urlsplit(u)
        if p.netloc in ("wa.me", "www.facebook.com") and (p.netloc == "wa.me" or p.path.startswith("/sharer")):
            targets.setdefault(f"{p.scheme}://{p.netloc}{p.path}", []).append(u)    # megosztó link: a szöveg mindig más, a cél ugyanaz
            continue
        q = urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if not k.startswith("utm_")])
        targets.setdefault(urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, q, "")), []).append(u)
    with cf.ThreadPoolExecutor(8) as ex:
        res = dict(zip(targets, ex.map(_check, targets)))
    out = {"checked": dt.datetime.now().isoformat(timespec="seconds"), "count": len(targets), "results": {}}
    for base, r in res.items():
        out["results"][base] = {**r, "where": sorted({w for u in targets[base] for w in links[u]})}
    LINKS_P.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def link_summary():
    if not LINKS_P.exists():
        return None, []
    lc = json.loads(LINKS_P.read_text(encoding="utf-8"))
    bad = {u: r for u, r in lc["results"].items() if r.get("ok") is False}
    unk = sum(1 for r in lc["results"].values() if r.get("ok") is None)
    health = [H("hiba", "link", f"Nem működő link ({r.get('status') or r.get('error', 'hiba')}): {u} – {', '.join(r['where'][:3])}", "tab", "attekintes")
              for u, r in bad.items()]
    return {"checked": lc["checked"], "count": lc["count"], "bad": len(bad), "unknown": unk}, health


# ------------------------------------------------------------------ összesítés
def compute(data, links=False):
    health = content_checks(data) + email_checks(data) + setup_checks(data)
    ot, oh = outreach()
    if links:
        check_links(data)
    ls, lh = link_summary()
    health = oh + lh + health
    order = {"hiba": 0, "figyelem": 1, "info": 2}
    health.sort(key=lambda h: order[h["lvl"]])
    return {"generated": dt.datetime.now().isoformat(timespec="seconds"), "health": health, "outreach": ot, "links": ls}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    data = json.loads((MK / "content" / "content.json").read_text(encoding="utf-8"))
    ins = compute(data, links="--links" in sys.argv)
    for h in ins["health"]:
        print(f"  [{h['lvl']:9}] {h['area']:9} {h['text']}")
    o = ins["outreach"]
    if o:
        print(f"  Megkeresések: {o['sent']} elküldve · {o['bounced']} visszapattant ({o['rate']:.1%}) · hátra: {o['remaining']} · "
              f"{'SZÜNETEL' if o['paused'] else 'nem szünetel'}")
    if ins["links"]:
        l = ins["links"]
        print(f"  Linkek: {l['count']} cél · hibás: {l['bad']} · nem ellenőrizhető: {l['unknown']} ({l['checked']})")


if __name__ == "__main__":
    main()
