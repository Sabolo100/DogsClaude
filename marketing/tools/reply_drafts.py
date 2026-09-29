"""Pacsi – válaszpiszkozatok a partnerek válaszleveleire (hello@pacsit.hu, Forward Email IMAP).

A felhasználó kérése (2026-09-28): minden érdemi válaszra rövid, kedves válasz megy – ha ötletet írnak: feljegyeztük,
a következő frissítésnél megpróbáljuk betenni; ha kérést: azon leszünk, hogy teljesítsük. A válasz PISZKOZAT lesz
a Drafts mappában, a felhasználó nézi át és küldi el. Ez a szkript semmit nem küld el.

Használat:
  python marketing/tools/reply_drafts.py --list                 megválaszolatlan válaszok (az automatikus válaszok
                                                                 és a visszapattanások nélkül), ha van már rájuk piszkozat, azt is jelzi
  python marketing/tools/reply_drafts.py --spec valaszok.json   piszkozatok: [{"message_id": "<…>", "body": "…"}]
  --dry-run: csak kiírja a piszkozatokat.

A piszkozat a levelezési szálba kerül (In-Reply-To, References), a címzett a válaszoló (Reply-To, különben From),
másolatban a levelükben szereplő többi cím (a sajátunk nélkül), a tárgy „Re: …”, alul az ő levelük idézve.
"""
import email
import email.header
import email.message
import email.policy
import email.utils
import imaplib
import json
import pathlib
import re
import sys
import time

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
CFG = json.loads((MK / "email" / "config.json").read_text(encoding="utf-8"))
FROM = CFG["sender"]["from_email"]
HU_DAY = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]
HU_MON = ["jan.", "febr.", "márc.", "ápr.", "máj.", "jún.", "júl.", "aug.", "szept.", "okt.", "nov.", "dec."]
AUTO_SUBJ = re.compile(r"automatikus|auto(matic)?[ -]?reply|out of office|házon kívül|tájékoztatás|abwesen", re.I)
AUTO_BODY = re.compile(r"automatikus válasz|ez egy automatikus|automatic reply|auto-?generated", re.I)
BOUNCE = re.compile(r"mailer-daemon|postmaster|mail delivery|delivery status|undeliver", re.I)


def dec(s):
    return str(email.header.make_header(email.header.decode_header(s or "")))


def addr_of(raw):
    """(név, cím) a nyers fejlécből – előbb bontunk, csak utána dekódolunk, mert a névben lehet vessző"""
    name, addr = email.utils.parseaddr(raw or "")
    return dec(name), addr


def password():
    return (ROOT / "ForwardEmail_hello.txt").read_text(encoding="utf-8").strip().split()[0]


def text_of(msg):
    """a levél saját szövege (sima szöveg, vagy a HTML-ből kinyerve), az idézett előzmények nélkül"""
    body = ""
    for p in msg.walk():
        if p.get_content_type() == "text/plain" and not p.get_filename():
            body = p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "replace")
            break
    if not body:
        for p in msg.walk():
            if p.get_content_type() == "text/html":
                h = p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "replace")
                h = re.sub(r"(?is)<(style|script).*?</\1>", "", h)
                h = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", h)
                body = re.sub(r"&nbsp;", " ", re.sub(r"<[^>]+>", "", h))
                break
    cut = re.search(r"\n\s*(>|-{3,}\s*Original|_{5,}|From: |Feladó: |.*(írta|wrote)\s*:\s*\n|Pacsi <hello@pacsit\.hu> ezt írta)", body)
    body = body[:cut.start()] if cut else body
    return re.sub(r"\n{3,}", "\n\n", body.replace("\r", "")).strip()


def is_auto(msg):
    if (msg.get("Auto-Submitted") or "no").lower() != "no" or msg.get("X-Autoreply") or msg.get("X-Autorespond"):
        return True
    return bool(AUTO_SUBJ.search(dec(msg.get("Subject"))) or AUTO_BODY.search(text_of(msg)[:600]))


def connect():
    M = imaplib.IMAP4_SSL("imap.forwardemail.net", 993)
    M.login(FROM, password())
    return M


def replied_ids(M):
    """azok az üzenetazonosítók, amelyekre már van válasz (piszkozat vagy elküldött levél)"""
    out = {}
    for box, label in (("Drafts", "piszkozat"), ('"Sent Mail"', "elküldve")):
        M.select(box, readonly=True)
        for i in M.search(None, "ALL")[1][0].split():
            h = email.message_from_bytes(M.fetch(i, "(BODY.PEEK[HEADER.FIELDS (IN-REPLY-TO)])")[1][0][1])
            if h.get("In-Reply-To"):
                out[re.sub(r"\s+", "", dec(h["In-Reply-To"]))] = label
    return out


def replies(M):
    """a beérkező mappa válaszlevelei a mi leveleinkre (In-Reply-To a pacsit.hu-ról, vagy egy megkeresett címről jött),
    visszapattanás nélkül"""
    log_p = MK / "email" / "state" / "outreach_log.json"
    contacted = {v.get("email", "").lower() for v in json.loads(log_p.read_text(encoding="utf-8")).values()} if log_p.exists() else set()
    M.select("INBOX", readonly=True)
    out = []
    for i in M.search(None, "ALL")[1][0].split():
        msg = email.message_from_bytes(M.fetch(i, "(BODY.PEEK[])")[1][0][1])
        fr = dec(msg.get("From"))
        threaded = "@pacsit.hu" in (msg.get("In-Reply-To") or "") + (msg.get("References") or "")
        if BOUNCE.search(fr) or not (threaded or addr_of(msg.get("From"))[1].lower() in contacted):
            continue
        out.append(msg)
    return out


def cmd_list():
    M = connect()
    done = replied_ids(M)
    for msg in replies(M):
        mid = (msg.get("Message-ID") or "").strip()
        state = "automatikus válasz – nem kell válaszolni" if is_auto(msg) else done.get(mid, "MEGVÁLASZOLATLAN")
        print(f"\n== {state} · {dec(msg['From'])} · {msg['Date']}\n   {dec(msg['Subject'])}\n   {mid}")
        if state == "MEGVÁLASZOLATLAN":
            print("   " + text_of(msg)[:700].replace("\n", "\n   "))
    M.logout()


def quote_line(msg):
    try:
        d = email.utils.parsedate_to_datetime(msg["Date"]).astimezone()
        when = f"{d.year}. {HU_MON[d.month - 1]} {d.day}., {HU_DAY[d.weekday()]} {d:%H:%M}"
    except (TypeError, ValueError):
        when = msg.get("Date", "")
    name, addr = addr_of(msg["From"])
    return f"{when} időpontban {name + ' ' if name else ''}<{addr}> ezt írta:"


def build(orig, body):
    to = addr_of(orig.get("Reply-To") or orig["From"])
    ours = {FROM.lower(), to[1].lower()}
    cc = [(dec(n), a) for n, a in email.utils.getaddresses([orig.get("To", ""), orig.get("Cc", "")]) if a and a.lower() not in ours]
    subj = re.sub(r"^\s*((re|vá|válasz|aw|fw|fwd)\s*:\s*)+", "", dec(orig["Subject"]), flags=re.I)
    # 998 karakteres sorhossz: a hosszú üzenetazonosító (pl. Outlook) így nem kerül kódolt szóba, a szálazás megmarad
    msg = email.message.EmailMessage(policy=email.policy.SMTP.clone(max_line_length=998))
    msg["From"] = email.utils.formataddr((CFG["sender"]["from_name"], FROM))
    msg["To"] = email.utils.formataddr(to)
    if cc:
        msg["Cc"] = ", ".join(email.utils.formataddr(a) for a in cc)
    msg["Subject"] = "Re: " + subj
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid(domain="pacsit.hu")
    mid = orig["Message-ID"].strip()
    msg["In-Reply-To"] = mid
    msg["References"] = ((orig.get("References") or "").strip() + " " + mid).strip()
    quoted = "\n".join("> " + l if l else ">" for l in text_of(orig).splitlines())
    msg.set_content(body.strip() + "\n\n" + quote_line(orig) + "\n" + quoted + "\n", charset="utf-8")
    return msg


def cmd_spec(path, dry):
    spec = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    M = connect()
    done = replied_ids(M)
    by_id = {(m.get("Message-ID") or "").strip(): m for m in replies(M)}
    for s in spec:
        mid = s["message_id"].strip()
        orig = by_id.get(mid)
        if not orig:
            print(f"  NINCS ilyen válaszlevél a beérkező mappában: {mid}")
            continue
        if mid in done and "--force" not in sys.argv:
            print(f"  már van rá válasz ({done[mid]}): {dec(orig['From'])} – kihagyom (--force: mégis)")
            continue
        msg = build(orig, s["body"])
        if dry:
            print("=" * 70)
            for k in ("To", "Cc", "Subject", "In-Reply-To"):
                if msg[k]:
                    print(f"{k}: {msg[k]}")
            print("\n" + msg.get_content())
            continue
        typ, resp = M.append("Drafts", r"(\Draft \Seen)", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        print(f"  {'PISZKOZAT KÉSZ' if typ == 'OK' else 'HIBA ' + str(resp)}: {msg['To']} · {msg['Subject']}")
    M.logout()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if "--list" in a:
        cmd_list()
    elif "--spec" in a:
        cmd_spec(a[a.index("--spec") + 1], "--dry-run" in a)
    else:
        print(__doc__)
