"""Pacsi – partnermegkeresések ütemezett kiküldése a hello@pacsit.hu-ról (Forward Email SMTP).

A felhasználó kérésére (2026-09-26): egyesével, időben elosztva. Egy szervezet csak EGYSZER kap levelet.
Hibás domainre, visszapattant és leiratkozott címre nem küld. Magánszemélyeknek (pl. tenyésztők) is küld (engedélyezve 2026-09-26).

Használat:
  python marketing/tools/outreach_queue.py --count 50 --gap 3-6            50 levél, 3–6 percenként (véletlen szünet)
  python marketing/tools/outreach_queue.py --count 100 --until 18:00       100 levél egyenletesen elosztva mostantól 18:00-ig
  python marketing/tools/outreach_queue.py --status                        hány van hátra, ma hány ment ki
  --dry-run: csak kiírja a sorrendet.

Leállítás: hozd létre a marketing/email/state/STOP fájlt (bármilyen tartalommal) – a következő levél előtt megáll.
Napi felső határ: 150 (a Forward Email 300-at enged; hideg megkeresésnél a kevesebb biztonságosabb).
Minden futás elején a beérkező mappából kigyűjti a visszapattanásokat, és azokat a címeket kizárja.
Automatikus szünet (2026-09-28): futás közben 5 levelenként újra megnézi a visszapattanásokat; ha aznap legalább 3 cím
visszapattant, és ez az aznapi levelek 5%-ánál több, AZNAPRA leáll (email/state/PAUSE, benne a dátum és az ok); másnap
magától folytatja. A felhasználó döntése (2026-09-28): címellenőrzés nélkül, napi 20 levéllel megy tovább.
A STOP fájl továbbra is kézi vészfék: amíg létezik, semmi nem megy ki.
Nem küld: a CMS-ben már kezelt kapcsolatoknak (email/state/contact_overrides.json: bármely állapot az „Új”-on kívül),
és a biztosan hibás domainekre (SKIP_DOMAINS, pl. gmail.hu elírás, megszűnt freeweb.hu).
Napló: marketing/email/state/outreach_log.json · futási napló: marketing/email/state/outreach_run.log
"""
import datetime as dt
import email
import email.message
import email.utils
import imaplib
import importlib.util
import json
import os
import pathlib
import shutil
import random
import re
import smtplib
import sys
import time

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
STATE = MK / "email" / "state"
STOP = STATE / "STOP"
PAUSE = STATE / "PAUSE"     # automatikus, csak az adott napra szóló szünet (az első sora a dátum)
RUNLOG = STATE / "outreach_run.log"
DAILY_CAP = 150
BOUNCE_LIMIT = .05          # aznapi visszapattanási arány, amely fölött a küldés magától szünetel …
BOUNCE_MIN = 3              # … de csak legalább ennyi visszapattanásnál (kis számoknál egy-két hiba még nem jel)
SKIP_DOMAINS = {"gmail.hu", "freeweb.hu", "freestart.hu"}   # elírás vagy megszűnt szolgáltató
SKIP_PIDS = {"PK0566"}      # nem kutyás szervezet (Happy Cats – macskamentés): a levél nekik nem releváns
OVERRIDES_P = STATE / "contact_overrides.json"             # a CMS kapcsolati állapotai (Claude másolja ide a közös tárolóból)
spec = importlib.util.spec_from_file_location("od", MK / "tools" / "outreach_drafts.py")
OD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OD)
FROM = OD.CFG["sender"]["from_email"]
# sorrend: ahol a legtöbb szervezeti cím és a legjobb partnerlehetőség van
ORDER = ["menhelyek", "kutyaiskolak", "kinologia", "allatorvosok", "szolgaltatasok", "kozossegek", "media", "cegek", "tenyesztok"]


def say(*a):
    line = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(RUNLOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_log():
    return json.loads(OD.LOG_P.read_text(encoding="utf-8")) if OD.LOG_P.exists() else {}


def save_log(log):
    """előbb ideiglenes fájlba ír, és csak a sikeres írás után cseréli le a naplót (2026-09-26-án a megtelt lemez
    0 bájtosra írta a naplót); ha az írás nem sikerül, a régi napló ép marad, és a küldés leáll"""
    tmp = OD.LOG_P.with_suffix(".tmp")
    tmp.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OD.LOG_P)


def password():
    return (ROOT / "ForwardEmail_hello.txt").read_text(encoding="utf-8").strip().split()[0]


def scan_bounces(log, pw):
    """a beérkező visszapattanás-értesítésekből kigyűjti a hibás címeket, és a naplóban „hiba” állapotra teszi"""
    known = {v.get("email", "").lower(): k for k, v in log.items()}
    found = 0
    try:
        M = imaplib.IMAP4_SSL("imap.forwardemail.net", 993)
        M.login(FROM, pw)
        M.select("INBOX", readonly=True)
        ids = M.search(None, "FROM", "MAILER-DAEMON")[1][0].split() + M.search(None, "SUBJECT", "Undeliver")[1][0].split() \
            + M.search(None, "SUBJECT", "delivery")[1][0].split()
        for i in set(ids):
            raw = M.fetch(i, "(BODY.PEEK[])")[1][0][1]
            text = raw.decode("utf-8", "ignore")
            # átmeneti késleltetés (pl. megtelt postafiók, 4.x.x): a szolgáltató újrapróbálja – ez nem visszapattanás
            if re.search(r"^Subject:.*(Delayed|Delay|Warning|késleltet)", text, re.M | re.I) or re.search(r"^Action:\s*delayed", text, re.M | re.I):
                continue
            for addr in set(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)):
                pid = known.get(addr.lower())
                if pid and log[pid].get("status") == "elkuldve":
                    log[pid].update(status="hiba", error="visszapattant")
                    found += 1
        M.logout()
    except Exception as e:  # noqa: BLE001
        say("  (a visszapattanások ellenőrzése nem sikerült:", e, ")")
    if found:
        save_log(log)
        say(f"  visszapattant címek kizárva: {found}")


def queue(log):
    """a küldési sorrend: előbb a már megírt piszkozatok, aztán kategóriánként (ORDER); a magánszemélyként jelölt
    kapcsolatok (pl. tenyésztők saját címe) is sorra kerülnek – a felhasználó 2026-09-26-án engedélyezte"""
    done_orgs = {v.get("org") for v in log.values() if v.get("status") in ("elkuldve", "hiba", "leiratkozott")}
    try:
        ov = json.loads(OVERRIDES_P.read_text(encoding="utf-8")) if OVERRIDES_P.exists() else {}
    except ValueError:
        ov = {}
    handled = {k for k, v in ov.items() if (v or {}).get("status", "uj") != "uj"}   # a CMS-ben már kezelt (megkeresve, nem kér…)
    first, rest = [], []
    for cat in ORDER:
        for c in OD.CONTACTS:
            if c["category"] != cat or c["name"] in done_orgs or c["id"] in handled or set(c.get("eids", [])) & SKIP_PIDS:
                continue
            ems = [(pid, e) for pid, e in zip(c.get("eids", []), c.get("emails", []))
                   if e and e not in c.get("mx_bad", []) and e.split("@")[-1].lower() not in SKIP_DOMAINS]
            if not ems:
                continue
            drafted = [x for x in ems if (log.get(x[0]) or {}).get("status") == "piszkozat"]
            pid, e = (drafted or ems)[0]          # szervezetenként egy levél: a piszkozat címére, különben az első (általános) címre
            (first if drafted else rest).append((pid, c, e))
    return first + rest


def sent_today(log):
    today = dt.date.today().isoformat()
    return sum(1 for v in log.values() if v.get("status") == "elkuldve" and (v.get("sent") or "").startswith(today))


def bounce_today(log):
    """(aznapi kiküldött + visszapattant, ebből visszapattant) – a „hiba” a küldéskor elutasított címet is jelenti"""
    today = dt.date.today().isoformat()
    day = [v for v in log.values() if (v.get("sent") or "").startswith(today) and v.get("status") in ("elkuldve", "hiba")]
    return len(day), sum(1 for v in day if v["status"] == "hiba")


def too_many_bounces(log):
    n, b = bounce_today(log)
    if b >= BOUNCE_MIN and b / max(1, n) > BOUNCE_LIMIT:
        reason = f"automatikus napi szünet {dt.datetime.now():%Y-%m-%d %H:%M}: ma {b}/{n} levél visszapattant ({b / n:.0%})"
        PAUSE.write_text(f"{dt.date.today().isoformat()}\n{reason}\n", encoding="utf-8")
        say("! " + reason + " – mára leállok, holnap folytatom")
        return True
    return False


def send_one(pid, c, to, pw):
    subject, body = OD.compose(c, pid)
    msg = email.message.EmailMessage()
    msg["From"] = email.utils.formataddr((OD.CFG["sender"]["from_name"], FROM))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid(domain="pacsit.hu")
    msg.set_content(body, charset="utf-8")
    with smtplib.SMTP_SSL("smtp.forwardemail.net", 465, timeout=60) as S:
        S.login(FROM, pw)
        S.send_message(msg)
    try:
        M = imaplib.IMAP4_SSL("imap.forwardemail.net", 993)
        M.login(FROM, pw)
        typ, resp = M.append('"Sent Mail"', r"(\Seen)", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        M.logout()
        if typ != "OK":
            say("    (a Sent Mail másolat nem sikerült:", resp, ")")
    except Exception as e:  # noqa: BLE001
        say("    (a Sent Mail másolat nem sikerült:", e, ")")
    return subject


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    args = sys.argv[1:]
    STATE.mkdir(parents=True, exist_ok=True)
    log = load_log()
    q = queue(log)
    if "--status" in args:
        print(f"  hátralévő szervezet: {len(q)} · ma elküldve: {sent_today(log)} · összesen elküldve: "
              f"{sum(1 for v in log.values() if v.get('status') == 'elkuldve')} · hiba: {sum(1 for v in log.values() if v.get('status') == 'hiba')}")
        cats = {}
        for _, c, _ in q:
            cats[c["category"]] = cats.get(c["category"], 0) + 1
        print("  kategóriánként:", cats)
        return
    count = int(args[args.index("--count") + 1]) if "--count" in args else 10
    gap = args[args.index("--gap") + 1] if "--gap" in args else None
    until = args[args.index("--until") + 1] if "--until" in args else None
    batch = q[:count]
    if "--dry-run" in args:
        for pid, c, e in batch:
            print(f"  {pid} · {c['category']} · {c['name']} · {e}")
        print(f"  ({len(batch)} levél, hátra összesen {len(q)})")
        return
    if STOP.exists():
        say("STOP fájl létezik – nem indulok (marketing/email/state/STOP)")
        return
    if PAUSE.exists():
        if PAUSE.read_text(encoding="utf-8").startswith(dt.date.today().isoformat()):
            say("ma már bekapcsolt az automatikus szünet – holnap folytatom")
            return
        PAUSE.unlink()                          # a tegnapi napi szünet lejárt
    pw = password()
    scan_bounces(log, pw)
    log = load_log()
    if too_many_bounces(log):
        return
    batch = queue(log)[:count]
    if not batch:
        say("nincs több küldhető szervezet")
        return
    # időzítés: fix véletlen szünet (--gap a-b perc) vagy egyenletes elosztás a --until időpontig
    if until:
        end = dt.datetime.combine(dt.date.today(), dt.time.fromisoformat(until))
        span = max(60.0, (end - dt.datetime.now()).total_seconds())
        base = span / max(1, len(batch))
        waits = [0] + [max(60, base * random.uniform(.75, 1.25)) for _ in batch[1:]]
    else:
        lo, hi = (float(x) for x in (gap or "3-6").split("-"))
        waits = [0] + [random.uniform(lo, hi) * 60 for _ in batch[1:]]
    say(f"indul: {len(batch)} levél · {'eddig: ' + until if until else 'szünet: ' + (gap or '3-6') + ' perc'} · ma eddig: {sent_today(log)}")
    sent = 0
    for (pid, c, to), w in zip(batch, waits):
        if w:
            time.sleep(w)
        if STOP.exists():
            say("STOP fájl – leállok")
            break
        if until and dt.datetime.now() > dt.datetime.combine(dt.date.today(), dt.time.fromisoformat(until)) + dt.timedelta(minutes=30):
            say("lejárt az időablak – leállok")
            break
        if shutil.disk_usage(STATE).free < 300 * 1024 * 1024:
            say("kevés a szabad hely a lemezen (< 300 MB) – leállok, hogy a napló biztosan menthető legyen")
            break
        log = load_log()
        if sent_today(log) >= DAILY_CAP:
            say(f"elértem a napi felső határt ({DAILY_CAP}) – leállok")
            break
        try:
            subject = send_one(pid, c, to, pw)
        except smtplib.SMTPRecipientsRefused as e:
            log.setdefault(pid, {}).update(email=to, org=c["name"], category=c["category"], status="hiba", error=str(e)[:200])
            save_log(log)
            say(f"  {pid}: ELUTASÍTVA {to}")
            continue
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPDataError, smtplib.SMTPSenderRefused) as e:
            say(f"  ! SMTP-hiba – leállok: {e}")
            break
        except Exception as e:  # noqa: BLE001
            say(f"  ! hálózati hiba ({pid}): {e} – kihagyom, később újra sorra kerül")
            continue
        log.setdefault(pid, {}).update(email=to, org=c["name"], category=c["category"], subject=subject, status="elkuldve",
                                       sent=dt.datetime.now().isoformat(timespec="seconds"))
        save_log(log)
        sent += 1
        say(f"  ELKÜLDVE {sent}/{len(batch)}: {pid} · {c['name']} · {to}")
        if sent % 5 == 0:                      # a visszapattanás percek alatt megjön: 5 levelenként újra megnézzük
            scan_bounces(load_log(), pw)
            if too_many_bounces(load_log()):
                break
    else:
        time.sleep(120)                        # az utolsó levelek visszapattanásai is beérkezzenek
        scan_bounces(load_log(), pw)
        too_many_bounces(load_log())
    n, b = bounce_today(load_log())
    say(f"kész: {sent} levél elküldve · ma összesen: {sent_today(load_log())} · ma visszapattant: {b}/{n}")


if __name__ == "__main__":
    main()
