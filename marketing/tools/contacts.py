"""Pacsi eDM – a kapcsolati adatbázis összefésülése és ellenőrzése.

A kutatás nyers eredménye: marketing/email/data/research/<kategória>.jsonl (egy sor = egy szervezet, forrásoldallal).
Ez a szkript:
  - egységesíti a mezőket, kisbetűsíti és ellenőrzi az e-mail-címeket (formátum + a domain MX/A rekordja);
  - összevonja az ismétlődéseket (azonos cím vagy azonos név ugyanabban a kategóriában);
  - megjelöli a magánszemélynek tűnő (ingyenes levelezős) címeket;
  - kimenet: marketing/email/data/contacts.json (a CMS „Kapcsolatok” füle) és kapcsolatok.csv (Excelhez).

Használat:  python marketing/tools/contacts.py [--no-mx]
Az adatok NEM kerülnek verziókezelésbe (.gitignore: marketing/email/data/).
"""
import concurrent.futures as cf
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import unicodedata

MK = pathlib.Path(__file__).resolve().parents[1]
DATA = MK / "email" / "data"
RES = DATA / "research"
VERSION = (MK / "VERSION").read_text(encoding="utf-8").strip()
BREEDS = {b["id"]: b["nev"] for b in json.loads((MK.parent / "data" / "fajtak.json").read_text(encoding="utf-8"))["breeds"]}

CATEGORIES = {
    "kinologia": "Kinológiai szervezetek, fajtaklubok",
    "tenyesztok": "Tenyésztők",
    "menhelyek": "Menhelyek, állatvédők",
    "kutyaiskolak": "Kutyaiskolák, trénerek",
    "allatorvosok": "Állatorvosok",
    "szolgaltatasok": "Kozmetikák, panziók, napközik, boltok",
    "media": "Média",
    "cegek": "Cégek, márkák",
    "kozossegek": "Közösségek, oktatás",
}
FREEMAIL = {"gmail.com", "googlemail.com", "freemail.hu", "citromail.hu", "yahoo.com", "yahoo.co.uk", "hotmail.com", "hotmail.hu",
            "outlook.com", "outlook.hu", "live.com", "msn.com", "icloud.com", "me.com", "vipmail.hu", "index.hu", "t-online.hu",
            "chello.hu", "upcmail.hu", "invitel.hu", "t-email.hu", "gmx.net", "gmx.com", "mail.com", "aol.com", "proton.me", "protonmail.com"}
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:48]


def norm_name(s):
    return re.sub(r"\s+", " ", slug(s).replace("-", " ")).strip()


def clean_email(e):
    e = (e or "").strip().strip(".,;:<>()[]\"'").replace("mailto:", "").lower()
    e = e.replace(" ", "")
    return e if EMAIL_RE.match(e) else ""


def mx_ok(domain):
    """van-e levelezésre alkalmas DNS-rekord (MX, vagy legalább A) – Windows nslookup, gyorsítótárral"""
    try:
        out = subprocess.run(["nslookup", "-type=mx", domain], capture_output=True, text=True, timeout=12,
                             encoding="utf-8", errors="ignore").stdout
        if "mail exchanger" in out:
            return True
        out = subprocess.run(["nslookup", domain], capture_output=True, text=True, timeout=12, encoding="utf-8", errors="ignore").stdout
        return bool(re.search(r"Name:\s+\S+\s+Address(es)?:", out))
    except Exception:  # noqa: BLE001
        return None


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rows, bad = [], []
    for f in sorted(RES.glob("*.jsonl")):
        for ln, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                bad.append(f"{f.name}:{ln}")
                continue
            r["category"] = r.get("category") or f.stem
            rows.append(r)
    # tisztítás
    out, seen_email, seen_name = [], {}, {}
    dropped_email = 0
    for r in rows:
        emails = []
        for e in r.get("emails") or []:
            ce = clean_email(e)
            if ce and ce not in emails:
                emails.append(ce)
            elif not ce:
                dropped_email += 1
        name = re.sub(r"\s+", " ", (r.get("name") or "").strip())
        if not name:
            continue
        rec = {
            "name": name, "category": r["category"], "type": (r.get("type") or "").strip(), "breeds": r.get("breeds") or [],
            "emails": emails, "website": (r.get("website") or "").strip(), "phone": (r.get("phone") or "").strip(),
            "city": (r.get("city") or "").strip(), "county": (r.get("county") or "").strip(),
            "contact_person": (r.get("contact_person") or "").strip(), "person": bool(r.get("person")),
            "contact_form": (r.get("contact_form") or "").strip(), "source_url": (r.get("source_url") or "").strip(),
            "note": (r.get("note") or "").strip(), "found": r.get("found") or "",
        }
        rec["freemail"] = any(e.split("@")[1] in FREEMAIL for e in emails)
        # ismétlődés: azonos e-mail bárhol, vagy azonos név ugyanabban a kategóriában
        dup = next((seen_email[e] for e in emails if e in seen_email), None)
        nk = (rec["category"], norm_name(name))
        if dup is None and nk in seen_name:
            dup = seen_name[nk]
        if dup is not None:
            d = out[dup]
            for e in emails:
                if e not in d["emails"]:
                    d["emails"].append(e)
            for k in ("website", "phone", "city", "county", "contact_person", "contact_form", "note"):
                d[k] = d[k] or rec[k]
            d["breeds"] = sorted(set(d["breeds"]) | set(rec["breeds"]))
            if rec["category"] != d["category"]:
                d.setdefault("also", [])
                if rec["category"] not in d["also"]:
                    d["also"].append(rec["category"])
            for e in d["emails"]:
                seen_email[e] = dup
            continue
        idx = len(out)
        rec["id"] = f"{rec['category'][:4]}-{slug(name)[:32]}-{hashlib.sha1((rec['category'] + name).encode()).hexdigest()[:5]}"
        out.append(rec)
        for e in emails:
            seen_email[e] = idx
        seen_name[nk] = idx
    # domain-ellenőrzés
    if "--no-mx" not in sys.argv:
        cache_p = DATA / "mx_cache.json"
        cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
        domains = sorted({e.split("@")[1] for r in out for e in r["emails"]} - set(cache))
        if domains:
            print(f"  DNS-ellenőrzés: {len(domains)} domain…")
            with cf.ThreadPoolExecutor(16) as ex:
                for d, ok in zip(domains, ex.map(mx_ok, domains)):
                    cache[d] = ok
            cache_p.write_text(json.dumps(cache, indent=0, sort_keys=True), encoding="utf-8")
        for r in out:
            r["mx"] = {e: cache.get(e.split("@")[1]) for e in r["emails"]}
            r["mx_bad"] = [e for e, ok in r["mx"].items() if ok is False]
    for r in out:
        r["status"] = "hibas" if r["emails"] and len(r.get("mx_bad", [])) == len(r["emails"]) else "uj"
    out.sort(key=lambda r: (list(CATEGORIES).index(r["category"]) if r["category"] in CATEGORIES else 99, r["county"] != "Budapest", r["name"]))
    # Állandó azonosítók: minden e-mail-cím (és minden e-mail nélküli szervezet) kap egy PK0001-es ID-t.
    # A nyilvántartás (id_registry.json) megőrzi őket újraépítéskor is; egy ID-t soha nem osztunk ki újra.
    reg_p = DATA / "id_registry.json"
    reg = json.loads(reg_p.read_text(encoding="utf-8")) if reg_p.exists() else {"next": 1, "ids": {}}
    def pid(key):
        if key not in reg["ids"]:
            reg["ids"][key] = f"PK{reg['next']:04d}"
            reg["next"] += 1
        return reg["ids"][key]
    for r in out:
        r["eids"] = [pid(e) for e in r["emails"]] if r["emails"] else [pid("noemail:" + r["id"])]
    reg_p.write_text(json.dumps(reg, ensure_ascii=False, indent=0), encoding="utf-8")
    ids = [i for r in out for i in r["eids"]]
    assert len(ids) == len(set(ids)), "ismétlődő azonosító"

    stats = {c: {"all": sum(1 for r in out if r["category"] == c), "email": sum(1 for r in out if r["category"] == c and r["emails"]),
                 "person": sum(1 for r in out if r["category"] == c and (r["person"] or r["freemail"]))} for c in CATEGORIES}
    doc = {"version": VERSION, "built": dt.datetime.now().isoformat(timespec="seconds"), "count": len(out),
           "withEmail": sum(1 for r in out if r["emails"]), "uniqueEmails": len({e for r in out for e in r["emails"]}),
           "categories": CATEGORIES, "stats": stats, "contacts": out}
    (DATA / "contacts.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(DATA / "kapcsolatok.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ID", "e-mail", "e-mail sorszáma", "szervezet", "szervezet-azonosító", "kategória", "további kategóriák", "típus", "fajták",
                    "fajta-azonosítók", "weboldal", "kapcsolati űrlap", "telefon", "város", "megye", "kapcsolattartó", "magánszemély",
                    "ingyenes levelező", "domain fogad levelet", "állapot", "megjegyzés", "forrás", "gyűjtve", "szervezet összes e-mailje"])
        for r in out:
            ems = r["emails"] or [""]
            for k, (i, e) in enumerate(zip(r["eids"], ems), 1):
                dom = e.split("@")[1] if "@" in e else ""
                mx = (r.get("mx") or {}).get(e)
                w.writerow([i, e, f"{k}/{len(r['emails'])}" if e else "", r["name"], r["id"], CATEGORIES.get(r["category"], r["category"]),
                            ", ".join(CATEGORIES.get(x, x) for x in r.get("also", [])), r["type"], ", ".join(BREEDS.get(b, b) for b in r["breeds"]),
                            ", ".join(r["breeds"]), r["website"], r["contact_form"], r["phone"], r["city"], r["county"], r["contact_person"],
                            "igen" if r["person"] else "", "igen" if dom in FREEMAIL else "", "" if not e else ("igen" if mx else "nem" if mx is False else "?"),
                            "hibás cím" if mx is False else r["status"], r["note"], r["source_url"], r["found"], ", ".join(r["emails"])])
    print(f"  Azonosítók: {ids[0]}–{max(ids)} ({len(ids)} db, nyilvántartás: id_registry.json)")
    print(f"  Kapcsolatok: {len(out)} szervezet · e-maillel: {doc['withEmail']} · egyedi cím: {doc['uniqueEmails']} · "
          f"eldobott hibás cím: {dropped_email} · sérült sor: {len(bad)}")
    for c, s in stats.items():
        print(f"    {CATEGORIES[c]:42} {s['all']:4} db · e-mail: {s['email']:4} · magánszemélyes/ingyenes cím: {s['person']}")
    hib = sum(1 for r in out if r["status"] == "hibas")
    if hib:
        print(f"  ! {hib} szervezet összes címe nem fogad levelet (nincs MX/A rekord) – „Hibás cím” állapotot kaptak")


if __name__ == "__main__":
    main()
