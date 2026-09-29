"""Pacsi – személyre szabott megkereső levelek KIKÜLDÉSE a hello@pacsit.hu-ról (Forward Email SMTP), egyenként, szünettel.

Csak a felhasználó kifejezett kérésére futtatható (--yes nélkül csak kiírja, mit küldene). Egy azonosítóra (PK…)
csak egyszer küld: a napló (marketing/email/state/outreach_log.json) „elkuldve” állapota véd az ismétléstől.
Az elküldött levél másolata a „Sent Mail” mappába kerül (IMAP), hogy a postafiókban látszódjon.

Használat:  python marketing/tools/outreach_send.py --yes --interval 120 PK0009 PK0014 …
"""
import datetime as dt
import email.message
import email.utils
import imaplib
import importlib.util
import json
import pathlib
import smtplib
import sys
import time

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
spec = importlib.util.spec_from_file_location("od", MK / "tools" / "outreach_drafts.py")
OD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OD)
LOG_P = OD.LOG_P
FROM = OD.CFG["sender"]["from_email"]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    args = sys.argv[1:]
    go = "--yes" in args
    interval = int(args[args.index("--interval") + 1]) if "--interval" in args else 120
    pids = [a for a in args if a.startswith("PK")]
    log = json.loads(LOG_P.read_text(encoding="utf-8")) if LOG_P.exists() else {}
    pw = (ROOT / "ForwardEmail_hello.txt").read_text(encoding="utf-8").strip().split()[0]
    sent = 0
    for n, pid in enumerate(pids):
        if (log.get(pid) or {}).get("status") == "elkuldve":
            print(f"  {pid}: már elküldve ({log[pid].get('sent')}) – kihagyva")
            continue
        c, to = OD.by_pid(pid)
        if not to or c.get("person") or to in c.get("mx_bad", []):
            print(f"  {pid}: KIHAGYVA (nem küldhető)")
            continue
        subject, body = OD.compose(c, pid)
        msg = email.message.EmailMessage()
        msg["From"] = email.utils.formataddr((OD.CFG["sender"]["from_name"], FROM))
        msg["To"] = to
        msg["Subject"] = subject
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid(domain="pacsit.hu")
        msg.set_content(body, charset="utf-8")
        if not go:
            print(f"  [próba] {pid} → {to} · {subject}")
            continue
        if sent:
            time.sleep(interval)
        try:
            with smtplib.SMTP_SSL("smtp.forwardemail.net", 465, timeout=60) as S:
                S.login(FROM, pw)
                S.send_message(msg)
        except smtplib.SMTPRecipientsRefused as e:
            print(f"  {pid}: ELUTASÍTVA ({to}) – {e}")
            log.setdefault(pid, {}).update(email=to, org=c["name"], status="hiba", error=str(e)[:200])
            LOG_P.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
            continue
        except smtplib.SMTPAuthenticationError as e:
            print(f"  ! SMTP-bejelentkezési hiba – leállok: {e}")
            break
        now = dt.datetime.now().isoformat(timespec="seconds")
        try:   # másolat az Elküldött mappába
            M = imaplib.IMAP4_SSL("imap.forwardemail.net", 993)
            M.login(FROM, pw)
            typ, resp = M.append('"Sent Mail"', r"(\Seen)", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
            M.logout()
            if typ != "OK":
                print(f"    (a Sent Mail másolat nem sikerült: {resp})")
        except Exception as e:  # noqa: BLE001
            print(f"    (a Sent Mail másolat nem sikerült: {e})")
        log.setdefault(pid, {}).update(email=to, org=c["name"], category=c["category"], subject=subject, status="elkuldve", sent=now)
        LOG_P.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        sent += 1
        print(f"  {now[11:16]} ELKÜLDVE {sent}: {pid} · {c['name']} · {to}")
    print(f"  kész: {sent} levél elküldve")


if __name__ == "__main__":
    main()
