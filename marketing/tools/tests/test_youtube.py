"""A youtube.py automatikus próbái egy helyi álszerveren (mock_google.py) – a valódi Google-höz és a valódi naptárhoz nem nyúl.

Futtatás:  python marketing/tools/tests/test_youtube.py
A tartalom szintetikus (ideiglenes mappában), a „mostani idő” rögzített (2026-09-29 15:30 budapesti idő), a beállítás és a napló
is ideiglenes fájl: a valódi YouTube_API.json-hoz, naplóhoz és médiához nem ér hozzá.
"""
import contextlib
import datetime as dt
import http.client
import io
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import mock_google as mg  # noqa: E402
import youtube as yt  # noqa: E402

srv = mg.start()
B = mg.base()
tmp = pathlib.Path(tempfile.mkdtemp(prefix="yt_test_"))
FX = tmp / "mk"
FIXED_NOW = dt.datetime(2026, 9, 29, 13, 30, tzinfo=dt.timezone.utc)      # = 15:30 CEST

yt.API, yt.UPLOAD = f"{B}/youtube/v3", f"{B}/upload/youtube/v3"
yt.TOKEN_URL, yt.TOKENINFO_URL = f"{B}/token", f"{B}/tokeninfo"
yt.CFG_P, yt.LOG_P = tmp / "YouTube_API.json", tmp / "state" / "youtube_log.json"
yt.MK, yt.CONTENT_P, yt.EDITS_D = FX, FX / "content" / "content.json", FX / "edits"
yt.CHUNK = 1024 * 1024
yt.now = lambda: FIXED_NOW


class _T:                       # a várakozások kiiktatása a tesztben
    sleep = staticmethod(lambda s: None)
    time = staticmethod(time.time)


yt.time = _T

# ------------------------------------------------------------------ szintetikus tartalom
(FX / "content").mkdir(parents=True)
(FX / "out" / "videok").mkdir(parents=True)
(FX / "edits").mkdir()


def media_files(name, mb=2.5):
    (FX / "out" / "videok" / f"{name}.mp4").write_bytes(os.urandom(int(mb * 1024 * 1024)))
    (FX / "out" / "videok" / f"{name}_borito.jpg").write_bytes(os.urandom(20000))
    return [{"src": f"out/videok/{name}.mp4", "role": "main"}, {"src": f"out/videok/{name}_borito.jpg", "role": "cover"}]


def vid(i, title, date, time_, status, text_title, extra_slots=()):
    return {"id": i, "kind": "video", "title": title, "status": status, "files": media_files(i),
            "slots": [{"platform": "youtube", "date": date, "time": time_, "note": "Shorts"}, *extra_slots],
            "copy": {"youtube": {"text": f"{text_title} #shorts\n\nLeírás a(z) {i} videóhoz.\n\nNézd meg: https://pacsit.hu/y/{i}",
                                 "tags": "#pacsi #kutya #kutyafajták #shorts"}}}


items = [
    vid("v1", "Első", "2026-09-28", "19:15", "kiposztolva", "Első videó 🐾"),
    vid("v2", "Második", "2026-10-02", "18:45", "kesz", "Második videó 🤔"),
    vid("v3", "Harmadik", "2026-10-04", "11:15", "kesz", "Harmadik videó – ismered mindet? 🇭🇺"),
    vid("v4", "Negyedik", "2026-09-30", "19:15", "kiposztolva", "Zsebrakéta vagy kanapé-óriás? 🐕"),
    vid("v5", "Ötödik", "2026-10-06", "12:00", "kiposztolva", "Ötödik videó"),      # máshol már kiposztolva → „ellenőrizd”
    {"id": "v6", "kind": "video", "title": "Hatodik (nincs videófájl)", "status": "kesz", "files": [],
     "slots": [{"platform": "youtube", "date": "2026-10-05", "time": "10:00"}],
     "copy": {"youtube": {"text": "Hatodik #shorts\n\nLeírás", "tags": "#pacsi"}}},
    {"id": "v7", "kind": "video", "title": "Hetedik (hiányzó fájl a lemezről)", "status": "kesz",
     "files": [{"src": "out/videok/nincs_ilyen.mp4", "role": "main"}],
     "slots": [{"platform": "youtube", "date": "2026-10-05", "time": "11:00"}],
     "copy": {"youtube": {"text": "Hetedik #shorts\n\nLeírás", "tags": "#pacsi"}}},
    {"id": "k_img", "kind": "kep", "title": "Kép", "status": "kesz", "files": [], "copy": {},
     "slots": [{"platform": "youtube", "date": "2026-10-03", "time": "12:00"}]},
    {"id": "p_banner", "kind": "profil", "title": "Szalagcím", "status": "kesz", "files": [], "copy": {},
     "slots": [{"platform": "youtube", "date": "2026-09-27", "time": "11:00"}]},
]
yt.CONTENT_P.write_text(json.dumps({"items": items}, ensure_ascii=False), encoding="utf-8")
(yt.EDITS_D / "v4.json").write_text(json.dumps({"slots": {"0": {"done": True}}, "status": "kiposztolva"}), encoding="utf-8")

OK, BAD = [], []


def check(name, cond, extra=""):
    (OK if cond else BAD).append(name)
    print(("  ✓ " if cond else "  ✗ ") + name + (f"   [{extra}]" if extra and not cond else ""))


FNS = {"setup": yt.cmd_setup, "check": yt.cmd_check, "test": yt.cmd_test, "plan": yt.cmd_plan, "copy": yt.cmd_copy,
       "schedule": yt.cmd_schedule, "post": yt.cmd_post, "scheduled": yt.cmd_scheduled, "update": yt.cmd_update,
       "cancel": yt.cmd_cancel, "videos": yt.cmd_videos, "adopt": yt.cmd_adopt, "link": yt.cmd_link, "insights": yt.cmd_insights}


def run(args):
    """Egy parancs futtatása; visszaad: (kilépési üzenet vagy None, kimenet)."""
    yt.ARGS = list(args)
    buf = io.StringIO()
    code = None
    with contextlib.redirect_stdout(buf):
        try:
            FNS[args[0]]()
        except SystemExit as e:
            code = str(e.code)
        except (yt.ApiError, yt.TokenError, yt.UploadError) as e:
            code = "ERR: " + str(e)
    return code, buf.getvalue()


def write_cfg(**extra):
    cfg = {"client_id": "cid", "client_secret": "sec", "refresh_token": "RT1", "channel_id": yt.EXPECTED_CHANNEL}
    cfg.update(extra)
    yt.CFG_P.write_text(json.dumps(cfg), encoding="utf-8")


def fresh(locked=False, **cfg):
    mg.reset(locked=locked)
    yt.LOG_P.unlink(missing_ok=True)
    yt._TOK.update(access=None, exp=0)
    write_cfg(**cfg)


def log():
    return json.loads(yt.LOG_P.read_text(encoding="utf-8"))["videos"] if yt.LOG_P.exists() else {}


def add_manual(vid_id, title, desc, privacy="public", views="12"):
    mg.STATE["videos"][vid_id] = {"id": vid_id, "snippet": {"title": title, "publishedAt": "2026-09-27T06:16:43Z", "description": desc},
                                  "status": {"privacyStatus": privacy, "uploadStatus": "processed"},
                                  "statistics": {"viewCount": views, "likeCount": "3", "commentCount": "0"}}


print("\n== 1. OAuth (helyi visszahívás + PKCE)")
seen = {}


def fake_open(url):
    q = {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).items()}
    seen.update(q)
    mg.STATE["challenge"] = q["code_challenge"]
    port = int(q["redirect_uri"].rsplit(":", 1)[1])

    def go():
        time.sleep(0.3)
        c = http.client.HTTPConnection("127.0.0.1", port)
        c.request("GET", "/favicon.ico")            # a zaj nem téveszthet meg
        c.getresponse().read()
        mode = seen.get("_mode", "ok")
        st = q["state"] if mode != "badstate" else "rossz"
        qs = urllib.parse.urlencode({"error": "access_denied"} if mode == "deny" else {"code": "abc", "state": st})
        c = http.client.HTTPConnection("127.0.0.1", port)
        c.request("GET", "/?" + qs)
        c.getresponse().read()
    threading.Thread(target=go, daemon=True).start()
    return True


yt.webbrowser.open = fake_open
with contextlib.redirect_stdout(io.StringIO()):
    tok = yt.oauth_login("cid", "sec", wait=20)
check("oauth: refresh_token megjött", tok.get("refresh_token") == "RT1")
check("oauth: PKCE S256 + offline + consent", seen.get("code_challenge_method") == "S256" and seen.get("access_type") == "offline" and seen.get("prompt") == "consent")
check("oauth: csak a YouTube-jog kérve", seen.get("scope") == "https://www.googleapis.com/auth/youtube")
check("oauth: loopback átirányítás", seen.get("redirect_uri", "").startswith("http://127.0.0.1:"))
seen["_mode"] = "badstate"
try:
    with contextlib.redirect_stdout(io.StringIO()):
        yt.oauth_login("cid", "sec", wait=20)
    check("oauth: rossz state → hiba", False)
except yt.TokenError as e:
    check("oauth: rossz state → hiba", "állapotkód" in str(e))
seen["_mode"] = "deny"
try:
    with contextlib.redirect_stdout(io.StringIO()):
        yt.oauth_login("cid", "sec", wait=20)
    check("oauth: elutasítás → hiba", False)
except yt.TokenError as e:
    check("oauth: elutasítás → hiba", "elutasítva" in str(e))
seen["_mode"] = "ok"

print("\n== 2. setup (kliensfájl, csatorna-ellenőrzés)")
cj = tmp / "client_secret_test.json"
cj.write_text(json.dumps({"installed": {"client_id": "cid", "client_secret": "sec"}}), encoding="utf-8")
mg.reset()
code, out = run(["setup", "--client-json", str(cj)])
cfg = json.loads(yt.CFG_P.read_text(encoding="utf-8")) if yt.CFG_P.exists() else {}
check("setup: mentett konfig, benne a frissítő token", cfg.get("refresh_token") == "RT1" and cfg.get("channel_id") == yt.EXPECTED_CHANNEL, code)
check("setup: a titok nem kerül a kimenetre", "RT1" not in out and "sec\n" not in out, out[:200])
check("setup: elsőre nincs upload_check", "upload_check" not in cfg)
write_cfg(upload_check={"ok": True, "at": "2026-09-29T15:00:00"})
code, out = run(["setup", "--client-json", str(cj)])
cfg = json.loads(yt.CFG_P.read_text(encoding="utf-8"))
check("setup: azonos kliensnél megmarad a feltöltés-ellenőrzés eredménye", cfg.get("upload_check", {}).get("ok") is True)
write_cfg(client_id="MASIK", upload_check={"ok": True})
code, out = run(["setup", "--client-json", str(cj)])
cfg = json.loads(yt.CFG_P.read_text(encoding="utf-8"))
check("setup: másik kliensnél nem örökli", "upload_check" not in cfg)
yt.CFG_P.unlink()
mg.STATE["channel_id"] = "UCsomeoneelse"
code, out = run(["setup", "--client-json", str(cj)])
check("setup: rossz csatorna → nem ment", (not yt.CFG_P.exists()) and code and "NEM a Pacsi-csatorna" in code, code)
code, out = run(["setup", "--client-json", str(cj), "--any-channel"])
check("setup: --any-channel mentés", yt.CFG_P.exists())
yt.CFG_P.unlink()
mg.STATE["channel_id"] = yt.EXPECTED_CHANNEL
web = tmp / "client_web.json"
web.write_text(json.dumps({"web": {"client_id": "x", "client_secret": "y"}}), encoding="utf-8")
code, out = run(["setup", "--client-json", str(web)])
check("setup: webes kliens → érthető hiba", code and "Desktop app" in code, code)

print("\n== 3. check + test (nem zárolt projekt)")
fresh()
code, out = run(["check"])
check("check: csatorna kiírva", "Pacsi - kutyafajta választó" in out and yt.EXPECTED_CHANNEL in out, out)
check("check: jelzi, hogy a próba nem futott", "még nem futott" in out)
code, out = run(["test"])
check("test --yes nélkül nem tölt fel", mg.STATE["insert_count"] == 0 and "próba" in out)
code, out = run(["test", "--yes"])
cfg = json.loads(yt.CFG_P.read_text(encoding="utf-8"))
check("test: nem zárolt → ok=True", cfg.get("upload_check", {}).get("ok") is True, out)
check("test: a próbavideó törölve", len(mg.STATE["videos"]) == 0 and mg.STATE["insert_count"] == 1)
check("test: nem listázottként töltötte fel", "unlisted" in out)
check("test: a beállított titok nem szivárog a kimenetre", "RT1" not in out)

print("\n== 3b. test: ha a próbavideó nem olvasható vissza, nem mond ítéletet")
fresh()
mg.STATE["hide_list"] = True
code, out = run(["test", "--yes"])
cfg = json.loads(yt.CFG_P.read_text(encoding="utf-8"))
check("test: nem olvasható vissza → nincs ítélet, nem ír upload_check-et", "upload_check" not in cfg and "nem olvasható vissza" in out, out)
check("test: ilyenkor is törli a próbavideót", len(mg.STATE["videos"]) == 0)
mg.STATE["hide_list"] = False

print("\n== 4. test (zárolt projekt) + kapu")
fresh(locked=True)
code, out = run(["test", "--yes"])
cfg = json.loads(yt.CFG_P.read_text(encoding="utf-8"))
check("test: zárolt → ok=False", cfg.get("upload_check", {}).get("ok") is False, out)
check("test: zárolt esetén is törli a próbavideót", len(mg.STATE["videos"]) == 0)
check("test: érthető üzenet", "ZÁROLT" in out and "YOUTUBE_API.md" in out)
code, out = run(["schedule", "--yes"])
check("schedule --yes: zárolt projektnél nem tölt fel", code and "NEM auditált" in code and mg.STATE["insert_count"] == 1, code)
code, out = run(["post", "v2", "--yes"])
check("post --yes: zárolt projektnél nem tölt fel", code and "NEM auditált" in code and mg.STATE["insert_count"] == 1, code)
code, out = run(["check"])
check("check: kiírja, hogy ZÁROLT", "ZÁROLT" in out)
fresh()
code, out = run(["schedule", "--yes"])
check("schedule --yes: próba nélkül nem tölt fel", code and "Előbb futtasd" in code and mg.STATE["insert_count"] == 0, code)

print("\n== 5. plan (offline és a csatorna átnézésével)")
yt.CFG_P.unlink()
code, out = run(["plan"])
check("plan: konfig nélkül is működik (offline)", "nincs még API-beállítás" in out and "esedékes" in out, out)
fresh(upload_check={"ok": True, "at": "2026-09-29T15:00:00"})
add_manual("zs5doPK5n2A", "Egészen más cím", "Első videó leírása https://pacsit.hu/y/v1\n\n#pacsi")
add_manual("IhO3LzrRrHI", "Negyedik: Zsebrakéta vagy kanapé-óriás? 🐕".replace("Negyedik: ", ""), "Kicsi vagy nagy?")
code, out = run(["plan"])
rows = {}
for _l in out.splitlines():
    _m = re.match(r"\s+\d\d-\d\d \d\d:\d\d\s+(.+?)\s{2,}(\S+)\s", _l)
    if _m:
        rows[_m.group(2)] = _l
check("plan: v1 a leírásbeli link alapján felismerve", "kint van (YouTube)" in rows.get("v1", "") and "zs5doPK5n2A" in rows.get("v1", ""), out)
check("plan: v4 kint van (CMS pipa)", "kint van (CMS)" in rows.get("v4", ""), out)
check("plan: v2 és v3 esedékes", "esedékes" in rows.get("v2", "") and "esedékes" in rows.get("v3", ""), out)
check("plan: v5 (máshol kiposztolva) → ellenőrizd", "ellenőrizd" in rows.get("v5", ""), out)
check("plan: kép és profil kimarad", "kimarad" in rows.get("k_img", "") and "kimarad" in rows.get("p_banner", ""), out)
check("plan: videófájl nélküli tartalom kimarad, nem száll el", "kimarad" in rows.get("v6", "") and "nincs videófájl" in rows.get("v6", ""), out)
check("plan: a lemezről hiányzó fájl jelezve, nem ütemezhető", "hiányzó fájl" in rows.get("v7", "") and "HIÁNYZÓ FÁJL: nincs_ilyen.mp4" in rows.get("v7", ""), out)
check("plan: 2 ütemezhető", "2 idősáv ütemezhető most" in out, out)
code, out = run(["copy", "v2"])
check("copy: cím a végi #shorts nélkül, időponttal", "Második videó 🤔\n" in out and "2026-10-02 18:45" in out and "#pacsi #kutya" in out, out)
code, out = run(["copy", "p_banner"])
check("copy: nem videóra érthető hiba", code and "nem tölthető fel" in code, code)

print("\n== 6. schedule (próbafutás, majd élesen)")
code, out = run(["schedule"])
check("schedule próbafutás: nem tölt fel", mg.STATE["insert_count"] == 0 and "2 videó töltődne fel" in out, out)
code, out = run(["schedule", "--yes"])
check("schedule --yes: 2 feltöltés", mg.STATE["insert_count"] == 2, out)
vids = {v["snippet"]["title"]: v for v in mg.STATE["videos"].values() if v["id"].startswith("VID")}
v2 = vids.get("Második videó 🤔")
v3 = vids.get("Harmadik videó – ismered mindet? 🇭🇺")
check("v2 és v3 címe: a végi #shorts nélkül", v2 is not None and v3 is not None, list(vids))
if v2 and v3:
    check("v2 publishAt = 2026-10-02 18:45 CEST = 16:45Z", v2["status"].get("publishAt") == "2026-10-02T16:45:00.000Z", v2["status"])
    check("v3 publishAt = 2026-10-04 11:15 CEST = 09:15Z", v3["status"].get("publishAt") == "2026-10-04T09:15:00.000Z", v3["status"])
    check("privát + ütemezett", v2["status"]["privacyStatus"] == "private" and v3["status"]["privacyStatus"] == "private")
    check("nem gyerekeknek, nem szintetikus", v2["status"]["selfDeclaredMadeForKids"] is False and v2["status"]["containsSyntheticMedia"] is False)
    check("kategória 15, nyelv hu", v2["snippet"]["categoryId"] == "15" and v2["snippet"]["defaultLanguage"] == "hu")
    check("kulcsszavak a hashtagekből", v2["snippet"]["tags"] == ["pacsi", "kutya", "kutyafajták", "shorts"], v2["snippet"]["tags"])
    check("leírás: a többi sor + hashtagek, nincs benne a cím",
          v2["snippet"]["description"].startswith("Leírás a(z) v2 videóhoz.") and v2["snippet"]["description"].endswith("#pacsi #kutya #kutyafajták #shorts")
          and "https://pacsit.hu/y/v2" in v2["snippet"]["description"] and "Második videó" not in v2["snippet"]["description"], v2["snippet"]["description"])
L = log()
check("napló: v2#0 és v3#0 ütemezve", L.get("v2#0", {}).get("mode") == "scheduled" and L.get("v3#0", {}).get("mode") == "scheduled", L)
check("napló: borító beállítva", L.get("v2#0", {}).get("cover") is True)
check("v5 (ellenőrizd) nem került fel", "v5#0" not in L and mg.STATE["insert_count"] == 2)
code, out = run(["schedule", "--yes"])
check("újrafuttatás: nincs duplikáció", mg.STATE["insert_count"] == 2 and "Nincs ütemezhető" in out, out)
code, out = run(["plan"])
check("plan: ütemezve állapot", out.count("ütemezve") >= 2, out)
code, out = run(["schedule", "--only", "v5", "--yes"])
check("--only: az „ellenőrizd” tartalom is feltölthető", mg.STATE["insert_count"] == 3 and "v5#0" in log(), out)

print("\n== 6b. az ütemezett időpont után: nyilvános lett, vagy privát maradt (zárolás jele)")
_real_now = yt.now
yt.now = lambda: dt.datetime(2026, 10, 3, 0, 0, tzinfo=dt.timezone.utc)                     # v2 időpontja (okt. 2.) már elmúlt
vid_v2 = log()["v2#0"]["videoId"]
mg.STATE["videos"][vid_v2]["status"] = {"privacyStatus": "public", "uploadStatus": "processed"}           # a YouTube kiadta
code, out = run(["plan"])
check("plan: az időpont után a nyilvános videó „kint van (API)”", "kint van (API)" in out and "időpont elmúlt" not in out, out)
mg.STATE["videos"][vid_v2]["status"] = {"privacyStatus": "private", "uploadStatus": "processed"}          # zárolt: nem lett nyilvános
code, out = run(["plan"])
check("plan: ha az időpont után is privát, a zárolás gyanúját jelzi", "privát maradt (zárolt?)" in out, out)
code, out = run(["scheduled"])
check("scheduled: ugyanezt jelzi", "privát maradt" in out, out)
code, out = run(["plan", "--offline"])
check("plan --offline: a csatorna nélkül csak „ellenőrizd”-et mond", "időpont elmúlt (ellenőrizd)" in out, out)
yt.now = _real_now

print("\n== 7. megszakadás és folytatás (503, kapcsolatbontás)")
fresh(upload_check={"ok": True})
mg.STATE["faults"] = ["503", "drop", "503"]
f = FX / "out" / "videok" / "v3.mp4"
body = {"snippet": {"title": "t"}, "status": {"privacyStatus": "private"}}
cfg = json.loads(yt.CFG_P.read_text(encoding="utf-8"))
with contextlib.redirect_stdout(io.StringIO()):
    res = yt.upload_video(cfg, body, f)
check("feltöltés hibák után is befejeződik", res.get("id", "").startswith("VID"), res)
check("a szerver pontosan a fájl méretét kapta", mg.STATE["last_upload_bytes"] == f.stat().st_size, mg.STATE.get("last_upload_bytes"))
mg.STATE["faults"] = ["404"]
try:
    with contextlib.redirect_stdout(io.StringIO()):
        yt.upload_video(cfg, body, f)
    check("lejárt munkamenet → érthető hiba", False)
except yt.UploadError as e:
    check("lejárt munkamenet → érthető hiba", "lejárt" in str(e), str(e))
mg.STATE["faults"] = ["503"] * 10
try:
    with contextlib.redirect_stdout(io.StringIO()):
        yt.upload_video(cfg, body, f)
    check("tartós hiba → feladja", False)
except yt.UploadError as e:
    check("tartós hiba → feladja", "többszöri" in str(e), str(e))
empty = FX / "out" / "videok" / "ures.mp4"
empty.write_bytes(b"")
try:
    yt.upload_video(cfg, body, empty)
    check("üres fájl → hiba", False)
except yt.UploadError as e:
    check("üres fájl → hiba", "Üres fájl" in str(e))

print("\n== 8. borítókép hiba nem áll meg + azonnali közzététel + piszkozat")
fresh(upload_check={"ok": True})
mg.STATE["thumb_status"] = 403
code, out = run(["post", "v2", "--draft", "--yes"])
check("post --draft: privát, ütemezés nélkül", any(v["status"]["privacyStatus"] == "private" and "publishAt" not in v["status"] for v in mg.STATE["videos"].values()), out)
check("borítóhiba nem fatális", "borítókép beállítása nem sikerült" in out and "✓ https://www.youtube.com/shorts/" in out, out)
code, out = run(["post", "v2", "--yes"])
check("post: már a naplóban van → nem duplikál", code and "már a naplóban van" in code and mg.STATE["insert_count"] == 1, code)
code, out = run(["cancel", "v2", "--yes"])
check("cancel: törli a YouTube-ról és a naplóból", len(mg.STATE["videos"]) == 0 and "v2#0" not in log(), out)
mg.STATE["thumb_status"] = 200
code, out = run(["post", "v3", "--now", "--yes"])
v = next(iter(mg.STATE["videos"].values()))
check("post --now: nyilvános", v["status"]["privacyStatus"] == "public" and "publishAt" not in v["status"], v["status"])
code, out = run(["post", "v4", "--at", "2026-09-29 15:00", "--force", "--yes"])
check("post --at múltbeli időpont → elutasítja", code and "túl közel" in code, code)
code, out = run(["post", "v2"])
check("post --yes nélkül csak kiírja", "próbafutás" in out and mg.STATE["insert_count"] == 2, out)
add_manual("EXIST1", "Már fent lévő", "https://pacsit.hu/y/v2")
code, out = run(["post", "v2", "--yes"])
check("post: a csatornán már fent lévő videót nem tölti fel újra", code and "már a csatornán van" in code, code)

print("\n== 9. scheduled, update, videos, adopt, link, insights")
fresh(upload_check={"ok": True})
run(["schedule", "--yes"])
code, out = run(["scheduled"])
check("scheduled: kilistázza az ütemezetteket", "v2#0" in out and "v3#0" in out and "2026-10-02 18:45" in out, out)
(yt.EDITS_D / "v2.json").write_text(json.dumps({"copy": {"youtube": {"text": "ÚJ CÍM a v2-nek #shorts\n\nÚj leírás https://pacsit.hu/y/v2", "tags": "#pacsi #teszt"}}, "status": "kesz"}), encoding="utf-8")
code, out = run(["update", "v2"])
check("update próbafutás: mutatja a változást", "ÚJ CÍM a v2-nek" in out and "próbafutás" in out, out)
code, out = run(["update", "v2", "--yes"])
vv = next((v for v in mg.STATE["videos"].values() if v["snippet"]["title"] == "ÚJ CÍM a v2-nek"), None)
check("update: a YouTube-on átíródott a cím, az ütemezés megmaradt", vv and vv["status"]["publishAt"] == "2026-10-02T16:45:00.000Z" and vv["snippet"]["tags"] == ["pacsi", "teszt"], vv)
check("update: a napló címe is frissült", log()["v2#0"]["title"] == "ÚJ CÍM a v2-nek")
add_manual("MANUAL1", "Kézi", "https://pacsit.hu/y/v1")
code, out = run(["videos"])
check("videos: a kézzel feltöltött is látszik, tartalomhoz rendelve", "MANUAL1" in out and "[v1, NINCS a naplóban]" in out, out)
code, out = run(["adopt"])
check("adopt próbafutás", "v1" in out and "MANUAL1" in out and "próbafutás" in out, out)
code, out = run(["adopt", "--yes"])
check("adopt --yes: naplóba került", log().get("v1#0", {}).get("videoId") == "MANUAL1", out)
code, out = run(["link", "v4", "https://www.youtube.com/shorts/MANUAL1?feature=share", "--yes"])
check("link: URL-ből is kiveszi a videóazonosítót", log().get("v4#0", {}).get("videoId") == "MANUAL1", out)
outj = tmp / "ins.json"
code, out = run(["insights", "--json", str(outj)])
j = json.loads(outj.read_text(encoding="utf-8"))
check("insights: megtekintés/kedvelés a CMS metrics formájában",
      j["metrics"]["v1"]["s"]["0"]["reach"] == 12 and j["metrics"]["v1"]["s"]["0"]["likes"] == 3 and j["metrics"]["v1"]["s"]["0"]["source"] == "youtube-api", j)
check("insights: az ütemezett (jövőbeli) videót kihagyja", "v2" not in j["metrics"], list(j["metrics"]))
mg.STATE["videos"].pop(log()["v2#0"]["videoId"])
code, out = run(["scheduled"])
check("scheduled: a kézzel törölt videót jelzi", "nincs a csatornán" in out, out)
code, out = run(["cancel", "v2", "--yes"])
check("cancel: a már törölt videónál sem hibázik", "törölve" in out and "v2#0" not in log(), out)
code, out = run(["cancel", "v2", "--yes"])
check("cancel: nincs a naplóban → üzenet", code and "Nincs ilyen bejegyzés" in code, code)

print("\n== 10. token- és API-hibák érthetően")
fresh(refresh_token="ROSSZ")
code, out = run(["check"])
check("lejárt/visszavont token → érthető üzenet", code and "invalid_grant" in code and "setup" in code, code)
e = yt.ApiError(403, {"message": "x", "errors": [{"reason": "quotaExceeded"}]})
check("ApiError: magyar tipp a kvótára", "napi API-keret" in str(e), str(e))
e = yt.ApiError(403, {"message": "API disabled", "details": [{"reason": "SERVICE_DISABLED"}]})
check("ApiError: SERVICE_DISABLED tipp", "nincs bekapcsolva" in str(e), str(e))
fresh()
mg.STATE["channel_id"] = "UCsomeoneelse"
code, out = run(["check"])
check("check: rossz csatornát jelzi", "NEM a várt csatorna" in out, out)

print("\n== 11. metaadat-építés szélső esetek")
it = {"id": "x", "kind": "video", "yt": {"text": "Cím <b>veszélyes</b> #shorts\n\nLeírás", "tags": "#a #b #a"}}
t, d, tg, w = yt.build_meta(it)
check("< és > kivéve, figyelmeztet", "<" not in t and ">" not in t and w, (t, w))
check("kulcsszavak duplikáció nélkül", tg == ["a", "b"], tg)
it = {"id": "x", "kind": "video", "yt": {"text": "H" * 150, "tags": ""}}
t, d, tg, w = yt.build_meta(it)
check("hosszú cím 100 karakterre vágva", len(t) == 100 and w, len(t))
it = {"id": "x", "kind": "video", "yt": {"text": "Csak cím #shorts", "tags": ""}}
t, d, tg, w = yt.build_meta(it)
check("csak cím: üres leírás, nincs hiba", t == "Csak cím" and d == "", (t, d))
it = {"id": "x", "kind": "video", "yt": {"text": "Cím\n\nLeírás", "tags": "#" + "x" * 300 + " #" + "y" * 300}}
t, d, tg, w = yt.build_meta(it)
check("kulcsszavak összhossza 500 alatt", sum(len(x) for x in tg) + 2 * len(tg) <= 500, tg)
it = {"id": "x", "kind": "video", "yt": {"text": "Idő?", "tags": ""}}
check("helyi idő: nyári időszámítás (CEST) UTC+2", yt.utc_iso(yt.local("2026-10-02", "18:45")) == "2026-10-02T16:45:00.000Z")
check("helyi idő: téli időszámítás (CET) UTC+1", yt.utc_iso(yt.local("2026-11-02", "18:45")) == "2026-11-02T17:45:00.000Z")

print(f"\n{'=' * 60}\nÖSSZESEN: {len(OK)} ✓, {len(BAD)} ✗")
for b in BAD:
    print("  HIBA:", b)
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if BAD else 0)
