"""Pacsi – YouTube Shorts feltöltése és ütemezése a YouTube Data API v3-mal (csak szabványos Python, külső csomag nélkül).

A videók a YouTube SAJÁT ütemezőjébe kerülnek (privát feltöltés + publishAt): a megadott időpontban a YouTube maga teszi őket
nyilvánossá, akkor is, ha a laptop ki van kapcsolva.

A GOOGLE KORLÁTJA: az ÚJ (2020. július 28. után létrehozott) API-projektből feltöltött videó „privátra zárolt” marad, amíg a
projekt át nem esik a YouTube API-auditon. A zárolt videót a csatorna tulajdonosa sem teheti nyilvánossá (a Studióban sem,
fellebbezni sem lehet). Ezért a `schedule` és a `post` addig nem tölt fel éles videót, amíg a `test --yes` próba sikeres nem
volt: az egy kis próbavideót tölt fel, megnézi, zárolódott-e, és törli. Részletek és az audit menete: marketing/YOUTUBE_API.md

Beállítás (egyszer, a felhasználó saját termináljában – a kulcsokat senki más nem látja):
  python marketing/tools/youtube.py setup [--client-json C:\\...\\client_secret_....json] [--no-browser]
    A Google Cloudban létrehozott „Asztali alkalmazás” (Desktop app) OAuth-kliens adatait olvassa (fájlból, vagy rejtett bevitellel),
    megnyitja a Google engedélykérését, és a kapott frissítő tokent a repó gyökerébe menti: YouTube_API.json (gitignore-olt).
    A token és a kulcs soha nem íródik ki. Csak a Pacsi-csatornához (UCO8Hj95k0ouOE-wQmhk6TpA) fogadja el a belépést.

Parancsok:
  python marketing/tools/youtube.py check                  token, csatorna, jogosultság, a próba állapota
  python marketing/tools/youtube.py test --yes             próba: 3 mp-es próbavideót tölt fel (nem listázott), megnézi, zárolódott-e,
                                                           és azonnal törli. Ez dönti el, használható-e az API éles feltöltésre
  python marketing/tools/youtube.py plan [--days 28]       a naptár YouTube-idősávjai: mi, mikor, milyen állapotban (a csatornát is átnézi)
  python marketing/tools/youtube.py copy <id>              a videó címe, leírása, fájlja és időpontja kézi (Studio) feltöltéshez
  python marketing/tools/youtube.py schedule [--days 28]   minden esedékes, még nem kint lévő idősáv feltöltése a YouTube ütemezőjébe
       --only v2,v3   csak ezek         --draft   privát piszkozat (ütemezés nélkül)        --yes   valóban feltölt
  python marketing/tools/youtube.py post <id> [--slot N] [--now | --at "2026-10-05 12:00"] [--draft] --yes
                                                           egy videó közzététele most, vagy egy adott időpontra ütemezve
  python marketing/tools/youtube.py scheduled              az ütemezett videók élő állapota a YouTube-on a naplóval összevetve
  python marketing/tools/youtube.py update <id> --yes      a CMS-ben átírt cím/leírás/időpont ráírása a már feltöltött videóra
  python marketing/tools/youtube.py cancel <id> --yes      feltöltött videó törlése a YouTube-ról (és a naplóból)
  python marketing/tools/youtube.py videos [--limit 30]    a csatorna videói (a kézzel feltöltöttek is), és melyik naptári tartalom az
  python marketing/tools/youtube.py adopt [--yes]          a csatornán már fent lévő (kézzel feltöltött) naptári videók felvétele a naplóba
  python marketing/tools/youtube.py link <id> <videóAzonosító> [--slot N]    kézzel megadott videó hozzárendelése egy tartalomhoz
  python marketing/tools/youtube.py insights [--json F]    megtekintés, kedvelés, komment – a CMS Eredmények fülének formájában is
  --version: verzió.

Tartalom: marketing/content/content.json (python marketing/tools/build.py --no-render). A CMS-ben átírt szövegek és kipipált
idősávok a CMS közös tárolójából jönnek: Claude az ArtifactData eszközzel a marketing/tmp/cms_db/edits mappába menti őket
(egy dokumentum = egy JSON), ez az eszköz onnan olvassa és rárakja az alapszövegre.
Napló (mi van kint / ütemezve, YouTube-azonosítókkal): marketing/social/state/youtube_log.json (nincs verziókezelve).

Szöveg: a CMS YouTube-szövegének ELSŐ SORA a cím (a végi hashtagek nélkül, legfeljebb 100 karakter), a TÖBBI a leírás, alatta a
hashtagek; a hashtagekből lesznek a videó kulcsszavai is. Kategória: Kisállatok és állatok. Nyelv: magyar. Nem gyerekeknek
készült; nem tartalmaz valósághű mesterséges tartalmat (festett illusztrációk és képernyőfelvétel) – ezek a DEFAULTS-ban állíthatók.
Forma: csak videó (9:16, legfeljebb 3 perc – a YouTube magától Shortnak veszi). A kép, karusszel, story, hirdetés, profil kimarad.
"""
import base64
import datetime as dt
import getpass
import hashlib
import http.client
import http.server
import json
import pathlib
import re
import secrets
import shutil
import subprocess
import sys
import time
import urllib.parse
import webbrowser

MK = pathlib.Path(__file__).resolve().parents[1]
ROOT = MK.parent
VERSION = (MK / "VERSION").read_text(encoding="utf-8").strip()
CFG_P = ROOT / "YouTube_API.json"
LOG_P = MK / "social" / "state" / "youtube_log.json"
CONTENT_P = MK / "content" / "content.json"
EDITS_D = MK / "tmp" / "cms_db" / "edits"

EXPECTED_CHANNEL = "UCO8Hj95k0ouOE-wQmhk6TpA"          # Pacsi – kutyafajta választó
SCOPES = ["https://www.googleapis.com/auth/youtube"]   # feltöltés, módosítás, törlés, olvasás egy jogban
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3"
CHUNK = 8 * 1024 * 1024                                # a 256 KB többszöröse (a YouTube így kéri)
MIN_LEAD = dt.timedelta(minutes=15)                    # ennél közelebbi időpontra nem ütemezünk
SHORT_MAX_SECONDS = 180                                # Shorts: legfeljebb 3 perc

DEFAULTS = {                                           # egy helyen állítható; a feltöltés minden videóra ezt küldi
    "categoryId": "15",                                # Pets & Animals (Kisállatok és állatok)
    "defaultLanguage": "hu",
    "selfDeclaredMadeForKids": False,                  # nem gyerekeknek készült (a YouTube kötelezően kéri)
    "containsSyntheticMedia": False,                   # festett illusztrációk + képernyőfelvétel: nem „valósághű” szintetikus tartalom
    "embeddable": True,
    "publicStatsViewable": True,
    "license": "youtube",
}

ARGS = sys.argv[1:]

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Budapest")
except Exception:                                      # tzdata nélkül: kézi CET/CEST
    TZ = None


def opt(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS and ARGS.index(name) + 1 < len(ARGS) else default


def yes():
    return "--yes" in ARGS


def local(date, time_="12:00"):
    """'2026-10-05', '12:00' → időzónás datetime (Budapest)."""
    naive = dt.datetime.fromisoformat(f"{date}T{time_}")
    if TZ:
        return naive.replace(tzinfo=TZ)
    y = naive.year                                     # EU-szabály: CEST a márc. utolsó vasárnap 01:00 UTC-től okt. utolsó vasárnap 01:00 UTC-ig
    last_sun = lambda m: max(d for d in (dt.date(y, m, day) for day in range(25, 32)) if d.weekday() == 6)
    start = dt.datetime.combine(last_sun(3), dt.time(1), dt.timezone.utc)
    end = dt.datetime.combine(last_sun(10), dt.time(1), dt.timezone.utc)
    utc_guess = naive.replace(tzinfo=dt.timezone(dt.timedelta(hours=1)))
    off = 2 if start <= utc_guess < end else 1
    return naive.replace(tzinfo=dt.timezone(dt.timedelta(hours=off)))


def now():
    return dt.datetime.now(dt.timezone.utc)


def utc_iso(when):
    return when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def from_iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def loc_str(when):
    return when.astimezone(TZ or local("2026-01-01").tzinfo).strftime("%Y-%m-%d %H:%M")


# ------------------------------------------------------------------ hibák
HINTS = {
    "quotaExceeded": "a napi API-keret elfogyott – a Google időzónája szerinti éjfélkor (Budapesten kilenckor) újraindul",
    "uploadLimitExceeded": "a csatorna elérte a napi feltöltési korlátját – várj 24 órát",
    "youtubeSignupRequired": "ehhez a Google-fiókhoz nincs YouTube-csatorna – a csatorna fiókjával lépj be",
    "insufficientPermissions": "a token nem kapta meg a szükséges jogot – futtasd újra: youtube.py setup",
    "forbidden": "a művelet nem engedélyezett (jogosultság vagy csatorna-korlát; egyéni borítóhoz telefonos ellenőrzés kell)",
    "invalidPublishAt": "az ütemezett időpont érvénytelen (múltbeli vagy hibás formátum)",
    "videoNotFound": "a videó nem található (törölték?)",
    "accessNotConfigured": "a YouTube Data API v3 nincs bekapcsolva a Google Cloud projektben",
    "SERVICE_DISABLED": "a YouTube Data API v3 nincs bekapcsolva a Google Cloud projektben (APIs & Services → Library)",
    "authError": "hibás vagy lejárt token – futtasd újra: youtube.py setup",
    "rateLimitExceeded": "túl sok kérés – próbáld később",
    "invalidTitle": "érvénytelen cím (max. 100 karakter, nem lehet benne < vagy >)",
    "invalidDescription": "érvénytelen leírás (max. 5000 bájt, nem lehet benne < vagy >)",
    "invalidTags": "érvénytelen kulcsszavak (együtt max. 500 karakter)",
    "mediaBodyRequired": "üres a feltöltött fájl",
    "unauthorized": "hibás vagy lejárt token – futtasd újra: youtube.py setup",
}


class ApiError(Exception):
    def __init__(self, status, err):
        self.status = status
        self.err = err if isinstance(err, dict) else {"message": str(err)}
        reasons = [e.get("reason") for e in self.err.get("errors", []) if isinstance(e, dict) and e.get("reason")]
        for d in self.err.get("details") or []:
            if isinstance(d, dict) and d.get("reason"):
                reasons.append(d["reason"])
        self.reason = reasons[0] if reasons else ""
        hint = next((HINTS[r] for r in reasons if r in HINTS), "")
        msg = self.err.get("message", "")
        super().__init__(f"YouTube API hiba {status}: {msg}{' (' + ', '.join(dict.fromkeys(reasons)) + ')' if reasons else ''}"
                         f"{' – ' + hint if hint else ''}")


class TokenError(Exception):
    pass


class UploadError(Exception):
    pass


def parse_err(raw):
    try:
        j = json.loads(raw.decode("utf-8"))
        e = j.get("error", j) if isinstance(j, dict) else {"message": str(j)}
        return e if isinstance(e, dict) else {"message": str(e), "description": j.get("error_description", "")}
    except Exception:
        return {"message": raw.decode("utf-8", "replace")[:300]}


# ------------------------------------------------------------------ HTTP (átirányítás nélkül – a 308 a feltöltésnél „folytasd” jelzés)
def _open(method, url, headers=None, body=None, timeout=120):
    """Egy kérés http.client-tel. Visszaad: (státusz, fejlécek, bájtok). Hálózati hibánál OSError/HTTPException."""
    u = urllib.parse.urlsplit(url)
    conn_cls = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(u.netloc, timeout=timeout)
    try:
        conn.request(method, u.path + ("?" + u.query if u.query else ""), body=body, headers=headers or {})
        r = conn.getresponse()
        return r.status, r.headers, r.read()
    finally:
        conn.close()


def _retry_open(method, url, headers=None, body=None, timeout=120, tries=3):
    """_open ismétléssel hálózati hibára és 5xx-re (növekvő várakozás)."""
    for attempt in range(tries):
        try:
            st, hd, raw = _open(method, url, headers, body, timeout)
        except (OSError, http.client.HTTPException) as e:
            if attempt < tries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise ApiError(0, {"message": f"hálózati hiba: {e}"}) from None
        if st in (500, 502, 503, 504) and attempt < tries - 1:
            time.sleep(2 * (attempt + 1))
            continue
        return st, hd, raw


# ------------------------------------------------------------------ beállítások, token, napló
def load_cfg():
    if not CFG_P.exists():
        sys.exit("Nincs YouTube-beállítás. Futtasd a saját termináljodban: python marketing/tools/youtube.py setup\n"
                 "(lépésenként: marketing/YOUTUBE_API.md)")
    return json.loads(CFG_P.read_text(encoding="utf-8"))


def save_cfg(cfg):
    tmp = CFG_P.with_name(CFG_P.name + ".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(CFG_P)                                  # atomi csere


def load_log():
    return json.loads(LOG_P.read_text(encoding="utf-8")) if LOG_P.exists() else {"videos": {}}


def save_log(log):
    LOG_P.parent.mkdir(parents=True, exist_ok=True)
    tmp = LOG_P.with_suffix(".tmp")
    tmp.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(LOG_P)                                  # atomi csere


_TOK = {"access": None, "exp": 0.0}


def token_request(params):
    st, hd, raw = _retry_open("POST", TOKEN_URL, {"Content-Type": "application/x-www-form-urlencoded"},
                              urllib.parse.urlencode(params).encode("utf-8"))
    try:
        j = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        j = {}
    if st != 200:
        code = j.get("error", f"http_{st}")
        desc = j.get("error_description", "")
        hint = {"invalid_grant": "a frissítő token lejárt vagy visszavonták (Testing módú Google-projektnél 7 nap után lejár) – futtasd újra: youtube.py setup",
                "invalid_client": "hibás kliensazonosító vagy titok – futtasd újra: youtube.py setup",
                "access_denied": "az engedélykérést elutasították"}.get(code, "")
        raise TokenError(f"Google-token hiba: {code}{' – ' + desc if desc else ''}{' – ' + hint if hint else ''}")
    return j


def access_token(cfg):
    if _TOK["access"] and time.time() < _TOK["exp"] - 60:
        return _TOK["access"]
    r = token_request({"grant_type": "refresh_token", "refresh_token": cfg["refresh_token"],
                       "client_id": cfg["client_id"], "client_secret": cfg["client_secret"]})
    _TOK["access"], _TOK["exp"] = r["access_token"], time.time() + int(r.get("expires_in", 3600))
    return _TOK["access"]


def api(method, path, cfg, params=None, body=None, token=None):
    """YouTube Data API hívás; JSON vissza. A hibát ApiError-ral jelzi."""
    params = {k: ("true" if v is True else "false" if v is False else str(v)) for k, v in (params or {}).items() if v is not None}
    url = f"{API}/{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    headers = {"Authorization": f"Bearer {token or access_token(cfg)}", "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=UTF-8"
    st, hd, raw = _retry_open(method, url, headers, data)
    if 200 <= st < 300:
        return json.loads(raw.decode("utf-8")) if raw.strip() else {}
    raise ApiError(st, parse_err(raw))


# ------------------------------------------------------------------ OAuth (asztali kliens, helyi visszahívás + PKCE)
class _Callback(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        if "code" in q or "error" in q:
            self.server.result = {k: v[0] for k, v in q.items()}
            ok = "code" in q
            body = ("<html><head><meta charset='utf-8'><title>Pacsi</title></head><body style='font-family:sans-serif;padding:40px'>"
                    + ("<h2>Kész ✓</h2><p>Bezárhatod ezt a fület, és visszatérhetsz a terminálhoz.</p>" if ok else
                       "<h2>Az engedélykérés nem sikerült</h2><p>Térj vissza a terminálhoz.</p>")
                    + "</body></html>").encode("utf-8")
            self.send_response(200)
        else:
            body = b""
            self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def oauth_login(client_id, client_secret, open_browser=True, wait=300):
    """Böngészős engedélykérés; visszaad: a token-végpont válasza (access_token, refresh_token, scope…)."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    state = secrets.token_urlsafe(24)
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Callback)
    srv.result, srv.timeout = None, 1
    redirect = f"http://127.0.0.1:{srv.server_address[1]}"
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code", "scope": " ".join(SCOPES),
        "access_type": "offline", "prompt": "consent", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    print("Az engedélykéréshez nyisd meg ezt a címet abban a böngészőben (profilban), ahol a YouTube-csatorna\n"
          "fiókjával be vagy jelentkezve. Ha a böngésző magától megnyílik, ott folytasd:\n")
    print(url + "\n")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    print("Várom a visszajelzést a böngészőből (legfeljebb 5 perc)…")
    deadline = time.time() + wait
    try:
        while srv.result is None and time.time() < deadline:
            srv.handle_request()
    finally:
        srv.server_close()
    res = srv.result
    if not res:
        raise TokenError("Nem érkezett válasz a böngészőből (időtúllépés). Futtasd újra a setupot.")
    if res.get("error"):
        raise TokenError(f"Az engedélykérés elutasítva: {res['error']}")
    if res.get("state") != state:
        raise TokenError("A visszahívás állapotkódja nem egyezik – biztonsági okból megszakítva. Futtasd újra a setupot.")
    return token_request({"grant_type": "authorization_code", "code": res["code"], "client_id": client_id,
                          "client_secret": client_secret, "redirect_uri": redirect, "code_verifier": verifier})


def read_client():
    """(client_id, client_secret): a Cloudból letöltött JSON-ból, a repó gyökeréből, vagy rejtett bevitellel."""
    p = opt("--client-json")
    if not p:
        found = sorted(ROOT.glob("client_secret*.json"))
        if found:
            p = str(found[-1])
    if p:
        j = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        if "installed" not in j:
            sys.exit("Ez nem „Asztali alkalmazás” (Desktop app) típusú OAuth-kliens fájlja. A Google Cloud Console-ban:\n"
                     "Clients → Create client → Application type: Desktop app, és azt töltsd le (Download JSON).")
        c = j["installed"]
        print(f"Kliensadatok beolvasva: {pathlib.Path(p).name}")
        return c["client_id"].strip(), c["client_secret"].strip()
    print("Nincs kliensfájl (--client-json). Add meg kézzel; a titok nem látszik gépelés közben.")
    cid = input("Client ID: ").strip()
    sec = getpass.getpass("Client secret (rejtett): ").strip()
    return cid, sec


def cmd_setup():
    print("Pacsi · YouTube-beállítás. A titkos adatok nem jelennek meg a képernyőn, és nem kerülnek a chatbe.\n")
    cid, sec = read_client()
    if not (cid and sec):
        sys.exit("A Client ID és a Client secret is kell.")
    tok = oauth_login(cid, sec, open_browser="--no-browser" not in ARGS)
    refresh = tok.get("refresh_token")
    if not refresh:
        sys.exit("A Google nem adott frissítő tokent. Vond vissza a korábbi engedélyt (myaccount.google.com/permissions → az app → Hozzáférés\n"
                 "eltávolítása), és futtasd újra a setupot.")
    scopes = sorted(set((tok.get("scope") or "").split()))
    if not any(s in scopes for s in ("https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl")):
        sys.exit(f"Az engedélyben nincs YouTube-kezelési jog (kapott: {', '.join(scopes) or '–'}). A jelölőnégyzetet is pipáld be, és futtasd újra.")
    tmp_cfg = {"client_id": cid, "client_secret": sec, "refresh_token": refresh}
    ch = channel(tmp_cfg, token=tok["access_token"])
    title = ch["snippet"]["title"]
    print(f"\nBejelentkezve mint csatorna: {title} ({ch['id']})")
    if ch["id"] != EXPECTED_CHANNEL and "--any-channel" not in ARGS:
        sys.exit(f"✗ Ez NEM a Pacsi-csatorna (várt: {EXPECTED_CHANNEL}). Nem mentettem semmit.\n"
                 "  Futtasd újra a setupot, és az engedélykérésnél a „Pacsi – kutyafajta választó” csatornát (márkafiókot) válaszd ki.")
    cfg = {"_doc": "Pacsi YouTube-beállítás – TITKOS (OAuth kliens + frissítő token). Gitignore-olt, soha ne tedd verziókezelésbe, ne küldd el senkinek.",
           "client_id": cid, "client_secret": sec, "refresh_token": refresh, "channel_id": ch["id"], "channel_title": title,
           "scopes": scopes, "saved_at": dt.datetime.now().isoformat(timespec="seconds")}
    if CFG_P.exists():                                  # új token ugyanahhoz a klienshez: a feltöltés-ellenőrzés eredménye megmarad
        try:
            old = json.loads(CFG_P.read_text(encoding="utf-8"))
            if old.get("client_id") == cid and old.get("upload_check"):
                cfg["upload_check"] = old["upload_check"]
        except Exception:
            pass
    save_cfg(cfg)
    print(f"✓ Mentve: {CFG_P.name} (a repó gyökerében, gitignore-olt). Jogosultság: {', '.join(scopes)}")
    print("\nA következő lépés: szólj Claude-nak, hogy kész. Ő lefuttatja a `check` és a `test --yes` parancsot; a próba kiderít,\n"
          "hogy a Google zárolja-e az API-s feltöltéseket (részletek: marketing/YOUTUBE_API.md).")
    print("Ha a Google-fiók kliensfájlját (client_secret_….json) nem tartod meg, töröld – a titok most a YouTube_API.json-ban van.")


# ------------------------------------------------------------------ csatorna, videók
def channel(cfg, token=None):
    r = api("GET", "channels", cfg, {"part": "snippet,statistics,contentDetails,status", "mine": True}, token=token)
    if not r.get("items"):
        raise ApiError(404, {"message": "ehhez a tokenhez nincs YouTube-csatorna", "errors": [{"reason": "youtubeSignupRequired"}]})
    return r["items"][0]


def videos_by_ids(cfg, ids, part="snippet,status,statistics,contentDetails"):
    out = []
    ids = [i for i in ids if i]
    for i in range(0, len(ids), 50):
        out += api("GET", "videos", cfg, {"part": part, "id": ",".join(ids[i:i + 50])}).get("items", [])
    return out


def channel_videos(cfg):
    """(csatorna, összes videó a feltöltések listájából – a privátok és ütemezettek is, mert a tulajdonos látja őket)."""
    ch = channel(cfg)
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], None
    while True:
        r = api("GET", "playlistItems", cfg, {"part": "contentDetails", "playlistId": up, "maxResults": 50, "pageToken": page})
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        page = r.get("nextPageToken")
        if not page:
            break
    return ch, videos_by_ids(cfg, ids)


def norm(s):
    return re.sub(r"[\W_]+", "", (s or "").lower())      # betűk és számok; az emoji, írásjel, szóköz kiesik


def match_item(items, v):
    """Melyik naptári tartalom ez a videó? A leírásban lévő követhető link (pacsit.hu/y/<id>), különben a cím alapján."""
    for x in re.findall(r"pacsit\.hu/y/([A-Za-z0-9_\-]+)", v["snippet"].get("description") or ""):
        if x in items:
            return x
    t = norm(v["snippet"].get("title"))
    for it in items.values():
        if it["kind"] == "video" and t and t == norm(build_meta(it)[0]):
            return it["id"]
    return None


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
        yt = dict((it.get("copy") or {}).get("youtube") or {})
        yt.update(((e.get("copy") or {}).get("youtube")) or {})
        slots = []
        for i, s in enumerate(it.get("slots", [])):
            s = {**s, **((e.get("slots") or {}).get(str(i)) or {}), "i": i}
            slots.append(s)
        items[it["id"]] = {**it, "yt": yt, "slots": slots, "status": e.get("status", it.get("status")), "_edited": bool(e)}
    return items


def yt_form(it, slot):
    """Mi lehet ebből a YouTube-on? (forma, ok ha kimarad)"""
    if it["kind"] == "profil":
        return None, "profilbeállítás – nem videó"
    if it["kind"] != "video":
        return None, "nem videó (a YouTube-ra csak videó megy)"
    if not (it["yt"].get("text") or "").strip():
        return None, "nincs YouTube-szöveg"
    if not [f for f in it.get("files", []) if f["src"].endswith(".mp4")]:
        return None, "nincs videófájl"
    return "short", ""


def build_meta(it):
    """(cím, leírás, kulcsszavak, figyelmeztetések) a CMS YouTube-szövegéből: első sor = cím, a többi = leírás + hashtagek."""
    text = (it["yt"].get("text") or "").strip()
    tagline = (it["yt"].get("tags") or "").strip()
    lines = text.splitlines()
    first = lines[0].strip() if lines else ""
    title = re.sub(r"(?:\s+#\w+)+\s*$", "", first).strip() or first
    desc = "\n".join(lines[1:]).strip()
    if tagline:
        desc = f"{desc}\n\n{tagline}".strip()
    tags = list(dict.fromkeys(t.lstrip("#") for t in re.findall(r"#\w+", tagline)))
    warns = []
    if re.search(r"[<>]", title + desc):
        title, desc = (re.sub(r"[<>]", "", s) for s in (title, desc))
        warns.append("a < és > jel nem engedett – kivettem")
    if len(title) > 100:
        title = title[:99].rstrip() + "…"
        warns.append("a cím 100 karakterre rövidítve")
    if len(desc.encode("utf-8")) > 5000:
        warns.append("a leírás hosszabb 5000 bájtnál")
    while tags and sum(len(t) for t in tags) + 2 * len(tags) > 500:
        tags.pop()
    if not title:
        warns.append("üres cím")
    return title, desc, tags, warns


def media(it):
    files = it.get("files", [])
    videos = [MK / f["src"] for f in files if f["src"].endswith(".mp4")][:1]
    cover = [MK / f["src"] for f in files if f.get("role") == "cover"][:1]
    return videos, cover


def missing_files(it):
    files, cover = media(it)
    return [p.name for p in files + cover if not p.exists()]


def probe(path):
    """Videó adatai ffprobe-bal (ha van): szélesség, magasság, hossz. Nélküle None."""
    ff = shutil.which("ffprobe")
    if not ff or not path.exists():
        return None
    try:
        r = subprocess.run([ff, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                            "-of", "json", str(path)], capture_output=True, text=True, timeout=30)
        j = json.loads(r.stdout)
        return {"w": j["streams"][0]["width"], "h": j["streams"][0]["height"], "dur": float(j["format"]["duration"])}
    except Exception:
        return None


def status_block(mode, when=None):
    s = {"privacyStatus": "public" if mode == "public" else "private"}
    s.update({k: DEFAULTS[k] for k in ("selfDeclaredMadeForKids", "containsSyntheticMedia", "embeddable", "publicStatsViewable", "license")})
    if mode == "scheduled":
        s["publishAt"] = utc_iso(when)
    return s


def snippet_block(it):
    title, desc, tags, _ = build_meta(it)
    return {"title": title, "description": desc, "tags": tags, "categoryId": DEFAULTS["categoryId"], "defaultLanguage": DEFAULTS["defaultLanguage"]}


def yt_slots(items, days, log, found=None):
    """Minden YouTube-idősáv állapottal. found: {tartalomId: videó a csatornán} (ha a csatorna át lett nézve)."""
    horizon = now() + dt.timedelta(days=days)
    rows = []
    for it in items.values():
        for s in it["slots"]:
            if s["platform"] != "youtube":
                continue
            key = f"{it['id']}#{s['i']}"
            when = local(s["date"], s.get("time") or "12:00")
            form, why = yt_form(it, s)
            ent = log.get(key)
            v = (found or {}).get(it["id"])
            if ent:
                if ent["mode"] == "scheduled" and ent.get("publishAt") and from_iso(ent["publishAt"]) <= now():
                    pv = ((v or {}).get("status") or {}).get("privacyStatus")     # az ütemezett időpont elmúlt: mi lett a videóból?
                    state = ("kint van (API)" if pv == "public" else "! privát maradt (zárolt?)" if pv
                             else "időpont elmúlt (ellenőrizd)")
                else:
                    state = {"scheduled": "ütemezve", "published": "kint van (API)", "existing": "kint van (YouTube)",
                             "draft": "privát piszkozat"}.get(ent["mode"], ent["mode"])
            elif s.get("done"):
                state = "kint van (CMS)"
            elif v:
                st = v.get("status", {})
                state = ("kint van (YouTube)" if st.get("privacyStatus") == "public"
                         else "ütemezve (Studio)" if st.get("publishAt") else "privát a YouTube-on")
            elif not form:
                state = "kimarad"
            elif when < now():
                state = "LEKÉSETT" if it["status"] != "kiposztolva" else "kint van? (CMS: kiposztolva)"
            elif when < now() + MIN_LEAD:
                state = "túl közel (15 percen belül)"
            elif when > horizon:
                state = "később"
            elif it["status"] == "kiposztolva":
                state = "ellenőrizd (CMS: kiposztolva)"        # máshol már kint van – YouTube-ra csak kérésre (--only)
            else:
                state = "esedékes" if not missing_files(it) else "hiányzó fájl"
            rows.append({"key": key, "it": it, "slot": s, "when": when, "form": form, "why": why, "state": state, "log": ent, "video": v})
    return sorted(rows, key=lambda r: r["when"])


def scan(cfg, items):
    """A csatorna átnézése: ({tartalomId: videó}, csatorna, videók). Hiba esetén (None, None, None) és egy megjegyzés."""
    try:
        ch, vids = channel_videos(cfg)
    except (ApiError, TokenError) as e:
        print(f"  (a csatorna nem olvasható, csak a CMS és a napló alapján számolok: {e})")
        return None, None, None
    found = {}
    for v in vids:
        iid = match_item(items, v)
        if iid and iid not in found:
            found[iid] = v
    return found, ch, vids


# ------------------------------------------------------------------ feltöltés (folytatható protokoll)
def _query_upload(cfg, session, size):
    """Megszakadt feltöltés állapota: (következő bájt, kész videó vagy None)."""
    st, hd, raw = _open("PUT", session, {"Authorization": f"Bearer {access_token(cfg)}", "Content-Range": f"bytes */{size}"}, b"", timeout=60)
    if st in (200, 201):
        return size, json.loads(raw.decode("utf-8"))
    if st == 308:
        rng = hd.get("Range")
        return (int(rng.split("-")[-1]) + 1 if rng else 0), None
    raise UploadError(f"A feltöltés állapota nem kérdezhető le ({st}).")


def upload_video(cfg, body, path, parts="snippet,status", ctype="video/mp4"):
    size = path.stat().st_size
    if size == 0:
        raise UploadError(f"Üres fájl: {path.name}")
    init = {"Authorization": f"Bearer {access_token(cfg)}", "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": ctype}
    st, hd, raw = _retry_open("POST", f"{UPLOAD}/videos?uploadType=resumable&part={parts}", init, json.dumps(body, ensure_ascii=False).encode("utf-8"))
    if st != 200:
        raise ApiError(st, parse_err(raw))
    session = hd.get("Location")
    if not session:
        raise UploadError("A YouTube nem adott feltöltési címet.")
    off, fails, shown = 0, 0, 0
    with path.open("rb") as f:
        while True:
            f.seek(off)
            data = f.read(min(CHUNK, size - off))
            hdrs = {"Authorization": f"Bearer {access_token(cfg)}", "Content-Type": ctype,
                    "Content-Range": f"bytes {off}-{off + len(data) - 1}/{size}"}
            try:
                st, hd, raw = _open("PUT", session, hdrs, data, timeout=300)
            except (OSError, http.client.HTTPException):
                st, hd, raw = 0, {}, b""
            if st in (200, 201):
                return json.loads(raw.decode("utf-8"))
            if st == 308:
                rng = hd.get("Range")
                off = int(rng.split("-")[-1]) + 1 if rng else 0
                fails = 0
                pct = off * 100 // size
                if pct >= shown + 25:
                    shown = pct // 25 * 25
                    print(f"    feltöltés: {off / 1e6:.1f} / {size / 1e6:.1f} MB ({pct}%)")
                continue
            if st == 404:
                raise UploadError("A feltöltési munkamenet lejárt – indítsd újra a parancsot.")
            if st == 0 or st in (500, 502, 503, 504):
                fails += 1
                if fails > 6:
                    raise UploadError("A feltöltés többszöri próbára sem sikerült (hálózati vagy YouTube-hiba). Próbáld újra később.")
                time.sleep(min(30, 2 ** fails))
                try:
                    off, done = _query_upload(cfg, session, size)
                    if done:
                        return done
                except (OSError, http.client.HTTPException, UploadError):
                    pass                                    # a következő körben újra próbálja
                continue
            raise ApiError(st, parse_err(raw))


def set_thumbnail(cfg, vid, cover):
    data = cover.read_bytes()
    ctype = "image/png" if cover.suffix.lower() == ".png" else "image/jpeg"
    st, hd, raw = _retry_open("POST", f"{UPLOAD}/thumbnails/set?videoId={vid}&uploadType=media",
                              {"Authorization": f"Bearer {access_token(cfg)}", "Content-Type": ctype}, data, timeout=120)
    if st != 200:
        raise ApiError(st, parse_err(raw))


def read_back(cfg, vid, tries=3):
    for i in range(tries):
        r = videos_by_ids(cfg, [vid], part="snippet,status,contentDetails,processingDetails")
        if r:
            return r[0]
        time.sleep(2)
    return None


def publish(cfg, it, slot, when, mode, log, key):
    """Egy tartalom feltöltése. mode: scheduled (privát + publishAt) | public (azonnal nyilvános) | draft (privát, ütemezés nélkül).
    A naplót közvetlenül a feltöltés után menti, így megszakadás esetén sem duplikál."""
    files, cover = media(it)
    for p in files + cover:
        if not p.exists():
            raise SystemExit(f"Hiányzó fájl: {p}")
    if not files:
        raise SystemExit(f"{it['id']}: nincs feltölthető videófájl")
    title, desc, tags, warns = build_meta(it)
    for w in warns:
        print(f"    ! {w}")
    body = {"snippet": snippet_block(it), "status": status_block(mode, when)}
    print(f"    feltöltés: {files[0].name} ({files[0].stat().st_size / 1e6:.1f} MB)")
    video = upload_video(cfg, body, files[0])
    vid = video["id"]
    ent = {"item": it["id"], "slot": slot["i"], "mode": mode, "videoId": vid, "url": f"https://www.youtube.com/shorts/{vid}",
           "when": (when or now()).astimezone().isoformat(timespec="minutes"), "created": now().isoformat(timespec="seconds"),
           "title": title}
    if mode == "scheduled":
        ent["publishAt"] = body["status"]["publishAt"]
    log["videos"][key] = ent
    save_log(log)
    print(f"    ✓ feltöltve · {vid}")
    if cover:
        try:
            set_thumbnail(cfg, vid, cover[0])
            ent["cover"] = True
            save_log(log)
            print("    ✓ borítókép beállítva")
        except (ApiError, OSError) as e:
            print(f"    (a borítókép beállítása nem sikerült, a YouTube választ egyet: {e})")
    v = read_back(cfg, vid)
    if v:
        st = v.get("status", {})
        ent["privacy"] = st.get("privacyStatus")
        save_log(log)
        print(f"    YouTube szerint: {st.get('privacyStatus')} · feltöltés: {st.get('uploadStatus')}"
              f"{' · megjelenik: ' + loc_str(from_iso(st['publishAt'])) if st.get('publishAt') else ''}")
        if mode == "scheduled" and not st.get("publishAt"):
            print("    ! Az ütemezési időpont nem jelent meg a videón – ellenőrizd a YouTube Studióban.")
        if st.get("uploadStatus") in ("failed", "rejected"):
            print(f"    ! A YouTube elutasította: {st.get('rejectionReason') or st.get('failureReason')}")
    return ent


def require_check(cfg):
    """Éles feltöltés előtt: a próba kimutatta-e, hogy a projekt nem zárolt?"""
    c = cfg.get("upload_check") or {}
    if c.get("ok"):
        return
    if "--skip-check" in ARGS:
        print("! A feltöltés-ellenőrzés kihagyva (--skip-check). Ha a projekt zárolt, a videó privát marad.")
        return
    if c and c.get("ok") is False:
        sys.exit("✗ A legutóbbi próba (" + str(c.get("at", "?"))[:16] + ") szerint a Google-projekt NEM auditált: az API-val feltöltött videó privátra zárolódna,\n"
                 "  és nem tehető nyilvánossá. Nem töltök fel éles videót. Lásd: marketing/YOUTUBE_API.md (audit kérése; vagy 2020 előtti projekt használata).\n"
                 "  Ha az audit megvan, futtasd újra: youtube.py test --yes")
    sys.exit("✗ Előbb futtasd a feltöltés-ellenőrző próbát: python marketing/tools/youtube.py test --yes\n"
             "  (kis próbavideót tölt fel, megnézi, hogy a Google nem zárolja-e privátra, és törli; a részleteket lásd: marketing/YOUTUBE_API.md)")


# ------------------------------------------------------------------ parancsok
def cmd_check():
    cfg = load_cfg()
    ch = channel(cfg)
    sn, stt = ch["snippet"], ch.get("statistics", {})
    print(f"✓ Token érvényes · csatorna: {sn['title']} ({ch['id']}) · https://www.youtube.com/channel/{ch['id']}")
    print(f"  Feliratkozók: {'rejtett' if stt.get('hiddenSubscriberCount') else stt.get('subscriberCount', '?')} · videók: {stt.get('videoCount', '?')}"
          f" · megtekintések: {stt.get('viewCount', '?')}")
    if ch["id"] != EXPECTED_CHANNEL:
        print(f"  ! NEM a várt csatorna (várt: {EXPECTED_CHANNEL}). Futtasd újra a setupot a Pacsi-csatorna kiválasztásával.")
    lu = (ch.get("status") or {}).get("longUploadsStatus")
    if lu:
        print(f"  Hosszú videók / egyéni borító: {'engedélyezett' if lu == 'allowed' else 'a csatorna még nincs telefonnal ellenőrizve (youtube.com/verify)'}")
    try:
        st, hd, raw = _open("GET", f"{TOKENINFO_URL}?access_token={access_token(cfg)}")
        ti = json.loads(raw.decode("utf-8")) if st == 200 else {}
        if ti:
            scopes = ti.get("scope", "").split()
            need = any(s.endswith("/auth/youtube") or s.endswith("/auth/youtube.force-ssl") for s in scopes)
            print(f"  Jogosultság: {', '.join(s.rsplit('/', 1)[-1] for s in scopes)}" + ("" if need else "  ! HIÁNYZIK a YouTube-kezelési jog – futtasd újra a setupot"))
    except Exception:
        pass
    c = cfg.get("upload_check")
    if not c:
        print("  Feltöltés-ellenőrzés: még nem futott. Futtasd: python marketing/tools/youtube.py test --yes")
    elif c.get("ok"):
        print(f"  Feltöltés-ellenőrzés: ✓ rendben ({str(c.get('at', ''))[:16]}) – a Google nem zárolta a próbavideót, az éles feltöltés használható.")
    else:
        print(f"  Feltöltés-ellenőrzés: ✗ ZÁROLT ({str(c.get('at', ''))[:16]}) – a projekt nem auditált, az API-s videó privát maradna (marketing/YOUTUBE_API.md).")
    print("\nMegjegyzés: „Testing” állapotú Google-projektnél a token 7 nap után lejár; érdemes „In production”-ra (vagy Internalra) állítani.")


def make_test_video():
    """3 mp-es, 9:16-os próbavideó ffmpeg-gel; nélküle a legkisebb kész Short."""
    out = MK / "tmp" / "yt_test.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = shutil.which("ffmpeg")
    if ff:
        r = subprocess.run([ff, "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x2b2b2b:s=1080x1920:d=3:r=30",
                            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-shortest", str(out)], capture_output=True, text=True)
        if r.returncode == 0 and out.exists():
            return out
    vids = sorted((MK / "out" / "videok").glob("*.mp4"), key=lambda p: p.stat().st_size)
    return vids[0] if vids else None


def cmd_test():
    cfg = load_cfg()
    if not yes():
        print("[próba] Egy 3 mp-es próbavideót töltök fel a Pacsi-csatornára NEM LISTÁZOTTKÉNT (nem jelenik meg sehol), megnézem, hogy a Google\n"
              "zárolja-e privátra (ez történik, ha a Google-projekt még nem esett át az API-auditon), majd azonnal törlöm.\n"
              "Futtasd --yes kapcsolóval.")
        return
    src = make_test_video()
    if not src:
        sys.exit("Nincs próbavideó (az ffmpeg sem elérhető, és a marketing/out/videok üres).")
    print(f"Próbavideó: {src.name} ({src.stat().st_size / 1e3:.0f} kB)")
    body = {"snippet": {"title": "Pacsi API-próba – azonnal törlődik", "description": "Automatikus próba, azonnal törlődik.",
                        "categoryId": DEFAULTS["categoryId"]},
            "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False, "embeddable": True}}
    video = upload_video(cfg, body, src)
    vid = video["id"]
    print(f"✓ Feltöltve: {vid}")
    verdict, privacy, upload = None, None, None
    try:
        time.sleep(3)
        v = read_back(cfg, vid)
        if v is not None:
            st = v.get("status", {})
            privacy, upload = st.get("privacyStatus"), st.get("uploadStatus")
            verdict = privacy == "unlisted"
            print(f"  A YouTube szerint: {privacy} · feltöltés: {upload}" + (f" · ok: {st.get('rejectionReason') or st.get('failureReason')}" if st.get("rejectionReason") or st.get("failureReason") else ""))
    finally:
        try:
            api("DELETE", "videos", cfg, {"id": vid})
            print("✓ Próbavideó törölve.")
        except (ApiError, TokenError) as e:
            print(f"! A próbavideót nem sikerült törölni – töröld kézzel a Studióban: https://www.youtube.com/watch?v={vid}  ({e})")
        if src.parent == MK / "tmp":
            src.unlink(missing_ok=True)
    if verdict is None:
        print("\n! A próbavideó állapota nem olvasható vissza a YouTube-ról, ezért nem tudom eldönteni, zárolt-e a projekt. Futtasd újra a próbát.")
        return
    cfg = load_cfg()
    cfg["upload_check"] = {"ok": verdict, "at": dt.datetime.now().isoformat(timespec="seconds"), "privacy": privacy, "video": vid}
    save_cfg(cfg)
    if verdict:
        print("\n✓ Rendben: a Google nem zárolta a próbavideót – az API-s feltöltés használható éles videókra (schedule / post).")
    else:
        print("\n✗ ZÁROLT: a próbavideó a beállított nem listázott helyett privát lett. A Google-projekt nem auditált, ezért az API-val feltöltött\n"
              "  videók privátra zárolódnak, és a tulajdonos sem teheti őket nyilvánossá. Éles feltöltést ezért nem indítok.\n"
              "  Kiút: marketing/YOUTUBE_API.md (API-audit kérése, vagy 2020. július 28. előtti Google Cloud projekt használata).")


def kind_hu(v):
    st = v.get("status", {})
    p = st.get("privacyStatus", "?")
    return {"public": "nyilvános", "private": "privát", "unlisted": "nem listázott"}.get(p, p) + (
        f" → {loc_str(from_iso(st['publishAt']))}" if st.get("publishAt") else "")


def cmd_plan():
    days = int(opt("--days", "28"))
    items = load_items()
    log = load_log()["videos"]
    found = None
    if "--offline" not in ARGS and CFG_P.exists():
        found, ch, vids = scan(load_cfg(), items)
    elif not CFG_P.exists():
        print("  (még nincs API-beállítás: a csatornát nem nézem át, csak a CMS és a napló alapján számolok)")
    cfg_chk = json.loads(CFG_P.read_text(encoding="utf-8")).get("upload_check") if CFG_P.exists() else None
    print(f"YouTube-idősávok (a következő {days} napra ütemezhető: 'esedékes')")
    print("Feltöltés-ellenőrzés: " + ("nincs még API-beállítás" if not CFG_P.exists() else
                                       "még nem futott (test --yes)" if not cfg_chk else
                                       f"✓ rendben ({str(cfg_chk.get('at'))[:10]})" if cfg_chk.get("ok") else
                                       f"✗ ZÁROLT ({str(cfg_chk.get('at'))[:10]}) – az API-s feltöltés privát maradna") + "\n")
    rows = yt_slots(items, days, log, found)
    for r in rows:
        files, cover = media(r["it"]) if r["form"] else ([], [])
        miss = [p.name for p in files + cover if not p.exists()]
        pr = probe(files[0]) if files and files[0].exists() else None
        if r["why"]:
            extra = r["why"]
        elif miss:
            extra = f"HIÁNYZÓ FÁJL: {', '.join(miss)}"
        else:
            extra = (f"{pr['w']}×{pr['h']} · {pr['dur']:.0f} mp · {files[0].stat().st_size / 1e6:.1f} MB"
                     + ("" if pr["h"] >= pr["w"] and pr["dur"] <= SHORT_MAX_SECONDS else " · ! NEM lesz Short (álló, max. 3 perc kell)") if pr
                     else f"{files[0].stat().st_size / 1e6:.1f} MB") + ("" if cover else " · nincs borító")
        if r["video"]:
            extra = f"{r['video']['id']} · {kind_hu(r['video'])} · " + extra
        elif r["log"]:
            extra = f"{r['log'].get('videoId', '')} · " + extra
        print(f"  {r['when']:%m-%d %H:%M}  {r['state']:<30} {r['it']['id']:<12} {r['it']['title'][:40]:<40}  {extra}")
    due = [r for r in rows if r["state"] == "esedékes"]
    print(f"\n{len(due)} idősáv ütemezhető most" + (": python marketing/tools/youtube.py schedule --yes" if due else "."))
    if due:
        print("Kézi feltöltéshez (YouTube Studio → Ütemezés): python marketing/tools/youtube.py copy " + due[0]["it"]["id"])


def cmd_copy():
    pos = [a for a in ARGS[1:] if not a.startswith("--")]
    if not pos:
        sys.exit("Add meg a tartalom azonosítóját, pl.: copy v2")
    items = load_items()
    it = items.get(pos[0]) or sys.exit(f"Nincs ilyen tartalom: {pos[0]}")
    form, why = yt_form(it, {})
    if not form:
        sys.exit(f"{it['id']} nem tölthető fel YouTube-ra: {why}")
    title, desc, tags, warns = build_meta(it)
    files, cover = media(it)
    slot = next((s for s in it["slots"] if s["platform"] == "youtube"), None)
    print(f"── {it['id']} · {it['title']}\n")
    print(f"CÍM ({len(title)} karakter):\n{title}\n")
    print(f"LEÍRÁS ({len(desc.encode('utf-8'))} bájt):\n{desc}\n")
    print(f"VIDEÓ:   {files[0] if files else '–'}")
    print(f"BORÍTÓ:  {cover[0] if cover else '–'}")
    if slot:
        when = local(slot["date"], slot.get("time") or "12:00")
        print(f"IDŐPONT (Studio → Láthatóság → Ütemezés): {when:%Y-%m-%d %H:%M} (budapesti idő)")
    print("BEÁLLÍTÁSOK: Nem gyerekeknek készült · Kategória: Kisállatok és állatok · Nyelv: magyar · Módosított/mesterséges tartalom: nem")
    for w in warns:
        print(f"! {w}")


def cmd_schedule():
    cfg = load_cfg()
    only = set(filter(None, (opt("--only") or "").split(",")))
    items = load_items()
    log = load_log()
    found, _, _ = scan(cfg, items)
    rows = [r for r in yt_slots(items, int(opt("--days", "28")), log["videos"], found)
            if (r["state"] == "esedékes" or (r["state"].startswith("ellenőrizd") and r["it"]["id"] in only))
            and (not only or r["it"]["id"] in only)]
    if not rows:
        print("Nincs ütemezhető idősáv.")
        return
    mode = "draft" if "--draft" in ARGS else "scheduled"
    print(("Feltöltés a YouTube-ra" + (" (privát piszkozatként)" if mode == "draft" else " (ütemezve)") + ":" if yes() else
           "[próbafutás – a --yes kapcsolóval tölt fel]") + "\n")
    if yes():
        require_check(cfg)
    for r in rows:
        title = build_meta(r["it"])[0]
        print(f"  {r['when']:%Y-%m-%d %H:%M}  {r['it']['id']:<12} {title[:60]}")
        if not yes():
            continue
        try:
            publish(cfg, r["it"], r["slot"], r["when"], mode, log, r["key"])
        except (ApiError, UploadError, TokenError) as e:
            print(f"    ✗ {e}")
            continue
        time.sleep(2)
    if not yes():
        print(f"\n{len(rows)} videó töltődne fel.")
    else:
        print("\nKész. Az ütemezett videók a YouTube Studióban Privát + Ütemezett állapotúak, a megadott időpontban maguktól nyilvánosak lesznek.")


def cmd_post():
    pos = [a for a in ARGS[1:] if not a.startswith("--") and a not in {opt("--slot"), opt("--at")}]
    if not pos:
        sys.exit('Add meg a tartalom azonosítóját, pl.: post v2 --now --yes  vagy  post v2 --at "2026-10-02 18:45" --yes')
    cfg = load_cfg()
    items = load_items()
    it = items.get(pos[0]) or sys.exit(f"Nincs ilyen tartalom: {pos[0]}")
    yts = [s for s in it["slots"] if s["platform"] == "youtube"]
    slot = next((s for s in yts if str(s["i"]) == opt("--slot")), yts[0] if yts else {"i": -1, "platform": "youtube"})
    form, why = yt_form(it, slot)
    if not form:
        sys.exit(f"{it['id']} nem tölthető fel YouTube-ra: {why}")
    if "--draft" in ARGS:
        mode, when = "draft", None
    elif "--now" in ARGS:
        mode, when = "public", None
    else:
        mode = "scheduled"
        when = local(*opt("--at").split(" ")) if opt("--at") else local(slot["date"], slot.get("time") or "12:00")
        if when < now() + MIN_LEAD:
            sys.exit(f"Az időpont túl közel van vagy elmúlt ({when:%Y-%m-%d %H:%M}) – legalább 15 perccel későbbre ütemezz, vagy használd a --now / --draft kapcsolót.")
    key = f"{it['id']}#{slot['i']}"
    log = load_log()
    if key in log["videos"] and "--force" not in ARGS:
        e = log["videos"][key]
        sys.exit(f"Ez már a naplóban van ({e['mode']}, {e.get('videoId')}). Törlés: cancel {it['id']} --yes, vagy --force.")
    found, _, _ = scan(cfg, items)
    if found and it["id"] in found and "--force" not in ARGS:
        v = found[it["id"]]
        sys.exit(f"Ez a videó már a csatornán van ({v['id']}, {kind_hu(v)}). Felvétel a naplóba: adopt --yes. Mégis feltöltés: --force.")
    title, desc, tags, warns = build_meta(it)
    label = ("privát piszkozat" if mode == "draft" else "AZONNAL NYILVÁNOS" if mode == "public"
             else f"ütemezve: {when:%Y-%m-%d %H:%M}")
    print(f"{it['id']} · {label}\n---\n{title}\n\n{desc}\n---")
    for w in warns:
        print(f"! {w}")
    if not yes():
        print("[próbafutás – a --yes kapcsolóval tölti fel]")
        return
    require_check(cfg)
    ent = publish(cfg, it, slot, when, mode, log, key)
    print(f"✓ {ent['url']}")


def cmd_scheduled():
    cfg = load_cfg()
    log = load_log()["videos"]
    live = {v["id"]: v for v in videos_by_ids(cfg, [e.get("videoId") for e in log.values()])}
    print(f"A naplóban lévő videók ({len(log)}), élő állapotukkal a YouTube-on:")
    for k, e in sorted(log.items(), key=lambda kv: kv[1].get("when", "")):
        v = live.get(e.get("videoId"))
        if not v:
            print(f"  {k:<10} ✗ a videó nincs a csatornán (törölték?) · {e.get('videoId')}")
            continue
        st = v.get("status", {})
        note = ""
        if e["mode"] == "scheduled":
            pa = st.get("publishAt")
            if st.get("privacyStatus") == "private" and not pa and dt.datetime.fromisoformat(e["when"]) < now():
                note = "  ! az időpont elmúlt, de a videó privát maradt (zárolt lehet – lásd YOUTUBE_API.md)"
            elif st.get("privacyStatus") == "private" and not pa:
                note = "  ! nincs ütemezve"
        views = (v.get("statistics") or {}).get("viewCount", "–")
        print(f"  {e['when'][5:16].replace('T', ' ')}  {k:<10} {kind_hu(v):<32} {st.get('uploadStatus', '?'):<10} {views:>5} megtek. · {v['snippet']['title'][:40]}{note}")
    known = {e.get("videoId") for e in log.values()}
    others = [v for v in channel_videos(cfg)[1] if v["id"] not in known and v.get("status", {}).get("privacyStatus") != "public"]
    if others:
        print(f"\nA naplón kívüli, nem nyilvános videók a csatornán ({len(others)}):")
        for v in others:
            print(f"  {v['id']}  {kind_hu(v):<32} {v['snippet']['title'][:50]}")


def cmd_cancel():
    pos = [a for a in ARGS[1:] if not a.startswith("--") and a != opt("--slot")]
    if not pos:
        sys.exit("Add meg a tartalom azonosítóját: cancel v2 --yes")
    cfg = load_cfg()
    log = load_log()
    keys = [k for k in log["videos"] if k.split("#")[0] == pos[0] and (opt("--slot") is None or k.endswith("#" + opt("--slot")))]
    if not keys:
        sys.exit("Nincs ilyen bejegyzés a naplóban.")
    for k in keys:
        e = log["videos"][k]
        print(f"{k}: {e['mode']} · {e.get('videoId')} · {e.get('title', '')[:50]}")
        if not yes():
            print("  [próbafutás – a --yes kapcsolóval törli a YouTube-ról]")
            continue
        try:
            api("DELETE", "videos", cfg, {"id": e["videoId"]})
        except ApiError as ex:
            if ex.reason != "videoNotFound" and ex.status != 404:
                raise
            print("  (a videó már nem volt a YouTube-on)")
        del log["videos"][k]
        save_log(log)
        print("  ✓ törölve a YouTube-ról és a naplóból")


def cmd_update():
    pos = [a for a in ARGS[1:] if not a.startswith("--") and a != opt("--slot")]
    if not pos:
        sys.exit("Add meg a tartalom azonosítóját: update v2 --yes")
    cfg = load_cfg()
    items = load_items()
    log = load_log()
    keys = [k for k in log["videos"] if k.split("#")[0] == pos[0]]
    if not keys:
        sys.exit("Nincs ilyen bejegyzés a naplóban.")
    for k in keys:
        e = log["videos"][k]
        it = items.get(e["item"])
        if not it:
            continue
        cur = (videos_by_ids(cfg, [e["videoId"]]) or [None])[0]
        if not cur:
            print(f"{k}: ✗ a videó nincs a YouTube-on")
            continue
        slot = next((s for s in it["slots"] if s["i"] == e["slot"]), None)
        body = {"id": e["videoId"], "snippet": snippet_block(it)}
        parts = "snippet"
        if e["mode"] == "scheduled" and slot and cur["status"].get("privacyStatus") == "private":
            when = local(slot["date"], slot.get("time") or "12:00")
            if when > now() + MIN_LEAD:
                body["status"] = status_block("scheduled", when)
                parts = "snippet,status"
        print(f"{k}: {e['videoId']}\n  cím:     {cur['snippet']['title']!r}\n      →    {body['snippet']['title']!r}"
              + (f"\n  idő:     {kind_hu(cur)}\n      →    {loc_str(from_iso(body['status']['publishAt']))}" if "status" in body else ""))
        if not yes():
            print("  [próbafutás – a --yes kapcsolóval frissíti]")
            continue
        api("PUT", "videos", cfg, {"part": parts}, body=body)
        e["title"] = body["snippet"]["title"]
        if "status" in body:
            e["publishAt"] = body["status"]["publishAt"]
            e["when"] = when.astimezone().isoformat(timespec="minutes")
        save_log(log)
        print("  ✓ frissítve")


def cmd_videos():
    cfg = load_cfg()
    items = load_items()
    ch, vids = channel_videos(cfg)
    log = load_log()["videos"]
    by_vid = {e.get("videoId"): k for k, e in log.items()}
    vids.sort(key=lambda v: v["snippet"].get("publishedAt", ""), reverse=True)
    print(f"{ch['snippet']['title']} – {len(vids)} videó:")
    for v in vids[:int(opt("--limit", "30"))]:
        iid = match_item(items, v)
        views = (v.get("statistics") or {}).get("viewCount", "–")
        print(f"  {v['snippet'].get('publishedAt', '')[:10]}  {v['id']}  {kind_hu(v):<30} {views:>5} megtek.  "
              f"{('[' + iid + (', naplóban' if v['id'] in by_vid else ', NINCS a naplóban') + ']') if iid else '':<26} {v['snippet']['title'][:44]}")


def record_existing(log, it, slot_i, v):
    st = v.get("status", {})
    mode = "scheduled" if st.get("publishAt") and from_iso(st["publishAt"]) > now() else "existing"
    ent = {"item": it["id"], "slot": slot_i, "mode": mode, "videoId": v["id"], "url": f"https://www.youtube.com/shorts/{v['id']}",
           "when": (from_iso(st["publishAt"]) if st.get("publishAt") else from_iso(v["snippet"]["publishedAt"])).astimezone().isoformat(timespec="minutes"),
           "created": now().isoformat(timespec="seconds"), "title": v["snippet"]["title"], "privacy": st.get("privacyStatus"),
           "source": "adopt"}
    if st.get("publishAt"):
        ent["publishAt"] = st["publishAt"]
    log["videos"][f"{it['id']}#{slot_i}"] = ent
    return ent


def cmd_adopt():
    cfg = load_cfg()
    items = load_items()
    log = load_log()
    found, _, _ = scan(cfg, items)
    if found is None:
        return
    new = []
    for iid, v in found.items():
        it = items[iid]
        yts = [s for s in it["slots"] if s["platform"] == "youtube"]
        if not yts or f"{iid}#{yts[0]['i']}" in log["videos"]:
            continue
        new.append((it, yts[0]["i"], v))
    if not new:
        print("Nincs új, a naptárhoz tartozó videó a csatornán.")
        return
    for it, i, v in new:
        print(f"  {it['id']:<10} ← {v['id']} · {kind_hu(v)} · {v['snippet']['title'][:50]}")
        if yes():
            record_existing(log, it, i, v)
    if yes():
        save_log(log)
        print(f"✓ {len(new)} videó felvéve a naplóba.")
    else:
        print("[próbafutás – a --yes kapcsolóval felveszi a naplóba]")


def cmd_link():
    pos = [a for a in ARGS[1:] if not a.startswith("--") and a != opt("--slot")]
    if len(pos) < 2:
        sys.exit("Használat: link <tartalomId> <videóAzonosító> [--slot N]   pl.: link v1 zs5doPK5n2A")
    cfg = load_cfg()
    items = load_items()
    it = items.get(pos[0]) or sys.exit(f"Nincs ilyen tartalom: {pos[0]}")
    yts = [s for s in it["slots"] if s["platform"] == "youtube"]
    slot_i = int(opt("--slot")) if opt("--slot") else (yts[0]["i"] if yts else 0)
    vid = re.sub(r".*(?:v=|shorts/|youtu\.be/)", "", pos[1]).split("?")[0].split("&")[0]
    v = (videos_by_ids(cfg, [vid]) or [None])[0] or sys.exit(f"Ez a videó nincs a csatornán: {vid}")
    log = load_log()
    print(f"{it['id']}#{slot_i} ← {v['id']} · {kind_hu(v)} · {v['snippet']['title']}")
    if not yes():
        print("[próbafutás – a --yes kapcsolóval felveszi a naplóba]")
        return
    record_existing(log, it, slot_i, v)
    save_log(log)
    print("✓ felvéve a naplóba")


def cmd_insights():
    cfg = load_cfg()
    log = load_log()["videos"]
    out, metrics = {}, {}
    todo = {k: e for k, e in log.items() if e.get("videoId") and not (e["mode"] == "scheduled" and dt.datetime.fromisoformat(e["when"]) > now())}
    live = {v["id"]: v for v in videos_by_ids(cfg, [e["videoId"] for e in todo.values()], part="snippet,statistics,status")}
    for k, e in sorted(todo.items()):
        v = live.get(e["videoId"])
        if not v:
            out[k] = {"error": "a videó nincs a csatornán"}
            print(f"  {k:<10} ✗ a videó nincs a csatornán")
            continue
        s = v.get("statistics") or {}
        row = {"views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)), "comments": int(s.get("commentCount", 0)),
               "privacy": v["status"].get("privacyStatus"), "link": e.get("url")}
        out[k] = row
        item, slot = k.split("#")
        metrics.setdefault(item, {"s": {}})["s"][slot] = {"reach": row["views"], "likes": row["likes"], "comments": row["comments"],
                                                          "source": "youtube-api", "at": now().isoformat(timespec="minutes")}
        print(f"  {k:<10} megtekintés {row['views']:>6} · kedvelés {row['likes']} · komment {row['comments']} · {row['privacy']}  {v['snippet']['title'][:40]}")
    if opt("--json"):
        pathlib.Path(opt("--json")).write_text(json.dumps({"raw": out, "metrics": metrics}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n→ {opt('--json')} (a „metrics” rész a CMS Eredmények fülének formája; a megtekintés az „elérés” mezőbe kerül)")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    cmd = ARGS[0] if ARGS else "help"
    if cmd in ("--version", "version"):
        print(f"Pacsi youtube.py · marketing v{VERSION} · YouTube Data API v3")
        return
    fn = {"setup": cmd_setup, "check": cmd_check, "test": cmd_test, "plan": cmd_plan, "copy": cmd_copy, "schedule": cmd_schedule,
          "post": cmd_post, "scheduled": cmd_scheduled, "update": cmd_update, "cancel": cmd_cancel, "videos": cmd_videos,
          "adopt": cmd_adopt, "link": cmd_link, "insights": cmd_insights}.get(cmd)
    if not fn:
        print(__doc__)
        return
    try:
        fn()
    except (ApiError, TokenError, UploadError) as e:
        sys.exit(f"✗ {e}")
    except KeyboardInterrupt:
        sys.exit("Megszakítva.")


if __name__ == "__main__":
    main()
