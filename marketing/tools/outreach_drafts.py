"""Pacsi – személyre szabott megkereső levelek PISZKOZATKÉNT a hello@pacsit.hu postafiókba (Forward Email, IMAP).

Semmit nem küld el: a levelek a Drafts mappába kerülnek, onnan a Forward Email appban nézed át és küldöd el.
A jelszó a repó gyökerében: ForwardEmail_hello.txt (gitignore-olva). A kapcsolatokra az állandó azonosítóval
hivatkozunk (PK0001…). Napló: marketing/email/state/outreach_log.json – egy azonosítóhoz csak egyszer készül piszkozat.

Használat:
  python marketing/tools/outreach_drafts.py PK0014 PK0205 …      ezekhez készít piszkozatot
  python marketing/tools/outreach_drafts.py --dry-run PK0014     csak kiírja a levelet
"""
import datetime as dt
import email.message
import email.utils
import imaplib
import importlib.util
import json
import pathlib
import sys
import time
import urllib.parse

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
LOG_P = MK / "email" / "state" / "outreach_log.json"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = load("email_plan", MK / "content" / "email_plan.py")
CFG = json.loads((MK / "email" / "config.json").read_text(encoding="utf-8"))
CONTACTS = json.loads((MK / "email" / "data" / "contacts.json").read_text(encoding="utf-8"))["contacts"]
BN = {b["id"]: b["nev"] for b in json.loads((ROOT / "data" / "fajtak.json").read_text(encoding="utf-8"))["breeds"]}
HU9 = P.HU9
SITE = CFG["links"]["site"]
_ST = MK / "email" / "state" / "mailchimp.json"
SIGNUP = CFG["links"].get("signup") or (json.loads(_ST.read_text(encoding="utf-8")).get("list", {}).get("subscribe_url_short") if _ST.exists() else "") or SITE


def by_pid(pid):
    for c in CONTACTS:
        if pid in c.get("eids", []):
            k = c["eids"].index(pid)
            return c, (c["emails"][k] if k < len(c["emails"]) else "")
    raise SystemExit(f"Nincs ilyen azonosító: {pid}")


def az(w):
    return "Az" if w[:1].lower() in "aáeéiíoóöőuúüű" else "A"


def low_first(w):
    return w[0].lower() + w[1:] if len(w) > 1 and w[1] == w[1].lower() else w


def compose(c, pid):
    t = P.OUTREACH.get(c["category"], P.OUTREACH["kozossegek"])
    breeds = [b for b in c.get("breeds", []) if b in HU9] or c.get("breeds", [])
    breed = breeds[0] if breeds else ""
    fajta = BN.get(breed, breed)
    q = urllib.parse.urlencode({"utm_source": "partner", "utm_medium": "email", "utm_campaign": "megkereses", "utm_content": pid})
    link = f"{SITE}?{q}" + (f"#b={breed}" if breed else "")
    sig = "\n".join(x for x in [CFG["sender"].get("signature_name") or "A Pacsi csapata",
                                "Pacsi · https://pacsit.hu", CFG["sender"]["from_email"]] if x)
    pitch = CFG["links"]["pitch"]
    if c["category"] == "cegek":
        pitch += "#p-" + "-".join(c["name"].split())
    vals = {
        "nev": c["name"], "fajta": fajta, "varos": c.get("city", ""), "fajta_vagy_nev": fajta or c["name"],
        "fajta_mondat": f"{az(fajta)} {low_first(fajta)} is szerepel benne, itt a kártyája: {link}" if breed else f"Itt kipróbálható: {link}",
        "fajta_link": link, "feliratkozas": SIGNUP, "pitch": pitch, "alairas": sig, "site": SITE,
    }
    fill = lambda s: s.format(**vals)
    # a szövegben lévő pacsit.hu hivatkozás is kapja meg a követő paramétert
    body = fill(t["body"])
    if "{fajta_mondat}" not in t["body"]:          # ahol nincs fajtás link, a nyitó link kapja a követő paramétert
        body = body.replace("A Pacsi (https://pacsit.hu)", f"A Pacsi ({SITE}?{q})", 1)
    if not CFG["sender"].get("signature_name"):    # név nélkül a csapat nevében, többes számban
        body = body.replace("A Pacsi csapatából írok", "A Pacsi csapatából írunk").replace("Köszönöm, hogy", "Köszönjük, hogy")
    return fill(t["subject"]), body


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    dry = "--dry-run" in args
    pids = [a for a in args if a.startswith("PK")]
    log = json.loads(LOG_P.read_text(encoding="utf-8")) if LOG_P.exists() else {}
    M = None
    if not dry:
        pw = (ROOT / "ForwardEmail_hello.txt").read_text(encoding="utf-8").strip().split()[0]
        M = imaplib.IMAP4_SSL("imap.forwardemail.net", 993)
        M.login(CFG["sender"]["from_email"], pw)
    made = 0
    for pid in pids:
        if pid in log and not dry:
            print(f"  {pid}: már van piszkozat ({log[pid]['drafted']}) – kihagyva")
            continue
        c, to = by_pid(pid)
        if not to or c.get("person") or to in c.get("mx_bad", []):
            print(f"  {pid}: KIHAGYVA ({'nincs e-mail' if not to else 'magánszemély' if c.get('person') else 'a domain nem fogad levelet'})")
            continue
        subject, body = compose(c, pid)
        msg = email.message.EmailMessage()
        msg["From"] = email.utils.formataddr((CFG["sender"]["from_name"], CFG["sender"]["from_email"]))
        msg["To"] = to
        msg["Subject"] = subject
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid(domain="pacsit.hu")
        msg["X-Pacsi-ID"] = pid
        msg.set_content(body, charset="utf-8")
        if dry:
            print(f"--- {pid} · {to}\nTárgy: {subject}\n\n{body}\n")
            continue
        M.append("Drafts", r"(\Draft)", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        log[pid] = {"email": to, "org": c["name"], "category": c["category"], "subject": subject,
                    "drafted": dt.datetime.now().isoformat(timespec="seconds"), "status": "piszkozat"}
        LOG_P.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        made += 1
        print(f"  {pid}: piszkozat · {c['name']} · {to}")
    if M:
        M.logout()
    if not dry:
        print(f"  kész: {made} új piszkozat a hello@pacsit.hu Drafts mappájában (nem küldtem el semmit)")


if __name__ == "__main__":
    main()
