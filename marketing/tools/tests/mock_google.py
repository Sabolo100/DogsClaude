"""Helyi álszerver a Google OAuth + YouTube Data API v3 (folytatható feltöltés) tesztelésére."""
import base64
import hashlib
import http.server
import json
import threading
import urllib.parse
import uuid

STATE = {}


def reset(locked=False):
    STATE.clear()
    STATE.update(
        locked=locked,
        videos={},            # id -> video resource
        sessions={},          # upload_id -> {meta, received(bytearray), size}
        faults=[],            # egyszer használatos hibák a PUT-ra: "503", "drop", "404"
        thumb_status=200,
        log=[],               # (method, path)
        token_calls=[],
        challenge=None,
        channel_id="UCO8Hj95k0ouOE-wQmhk6TpA",
        insert_count=0,
    )


reset()
BASE = {"port": 0}


def base():
    return f"http://127.0.0.1:{BASE['port']}"


class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, status, obj=None, headers=None, raw=None):
        body = raw if raw is not None else (json.dumps(obj).encode("utf-8") if obj is not None else b"")
        self.send_response(status)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        if status != 204:
            self.send_header("Content-Type", "application/json; charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _auth_ok(self):
        return (self.headers.get("Authorization") or "").startswith("Bearer AT")

    def _err(self, status, reason, message="x"):
        self._send(status, {"error": {"code": status, "message": message, "errors": [{"reason": reason, "message": message}]}})

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PUT(self):
        self._route("PUT")

    def do_DELETE(self):
        self._route("DELETE")

    def _route(self, method):
        u = urllib.parse.urlsplit(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        STATE["log"].append((method, u.path))
        p = u.path
        if p == "/token" and method == "POST":
            f = {k: v[0] for k, v in urllib.parse.parse_qs(self._body().decode()).items()}
            STATE["token_calls"].append(f)
            if f.get("grant_type") == "refresh_token":
                if f.get("refresh_token") != "RT1":
                    return self._send(400, {"error": "invalid_grant", "error_description": "Token has been expired or revoked."})
                return self._send(200, {"access_token": "AT" + uuid.uuid4().hex[:6], "expires_in": 3600, "token_type": "Bearer"})
            if f.get("grant_type") == "authorization_code":
                exp = base64.urlsafe_b64encode(hashlib.sha256(f["code_verifier"].encode()).digest()).rstrip(b"=").decode()
                if STATE["challenge"] and exp != STATE["challenge"]:
                    return self._send(400, {"error": "invalid_grant", "error_description": "PKCE mismatch"})
                return self._send(200, {"access_token": "AT1", "refresh_token": "RT1", "expires_in": 3600,
                                        "scope": "https://www.googleapis.com/auth/youtube", "token_type": "Bearer"})
        if p == "/tokeninfo":
            return self._send(200, {"scope": "https://www.googleapis.com/auth/youtube", "expires_in": "3000"})
        if not self._auth_ok():
            return self._err(401, "authError", "Invalid Credentials")
        if p == "/youtube/v3/channels" and method == "GET":
            return self._send(200, {"items": [{"id": STATE["channel_id"], "snippet": {"title": "Pacsi - kutyafajta választó"},
                                               "statistics": {"subscriberCount": "3", "videoCount": str(len(STATE["videos"])), "viewCount": "10"},
                                               "contentDetails": {"relatedPlaylists": {"uploads": "UUxyz"}},
                                               "status": {"longUploadsStatus": "allowed"}}]})
        if p == "/youtube/v3/playlistItems" and method == "GET":
            ids = list(STATE["videos"])
            return self._send(200, {"items": [{"contentDetails": {"videoId": i}} for i in ids]})
        if p == "/youtube/v3/videos" and method == "GET":
            if STATE.get("hide_list"):
                return self._send(200, {"items": []})
            ids = q.get("id", "").split(",")
            return self._send(200, {"items": [STATE["videos"][i] for i in ids if i in STATE["videos"]]})
        if p == "/youtube/v3/videos" and method == "DELETE":
            if q["id"] not in STATE["videos"]:
                return self._err(404, "videoNotFound", "not found")
            del STATE["videos"][q["id"]]
            return self._send(204)
        if p == "/youtube/v3/videos" and method == "PUT":
            b = json.loads(self._body())
            v = STATE["videos"].get(b["id"])
            if not v:
                return self._err(404, "videoNotFound")
            v["snippet"].update(b["snippet"])
            if "status" in b and not STATE["locked"]:
                v["status"].update(b["status"])
            return self._send(200, v)
        if p == "/upload/youtube/v3/videos" and method == "POST" and q.get("uploadType") == "resumable":
            meta = json.loads(self._body())
            uid = uuid.uuid4().hex
            STATE["sessions"][uid] = {"meta": meta, "data": bytearray(), "size": int(self.headers["X-Upload-Content-Length"]),
                                      "ctype": self.headers.get("X-Upload-Content-Type")}
            return self._send(200, headers={"Location": f"{base()}/upload/youtube/v3/videos?uploadType=resumable&upload_id={uid}"})
        if p == "/upload/youtube/v3/videos" and method == "PUT":
            s = STATE["sessions"].get(q.get("upload_id"))
            if not s:
                return self._err(404, "notFound")
            body = self._body()
            cr = self.headers.get("Content-Range", "")
            if STATE["faults"] and not cr.startswith("bytes */"):
                f = STATE["faults"].pop(0)
                if f == "503":
                    return self._err(503, "backendError")
                if f == "drop":
                    # a szerver „megeszi” a kérést, de a kapcsolatot bontja (a teljes adat megérkezett-e? fele igen)
                    s["data"] += body[: len(body) // 2]
                    self.close_connection = True
                    self.connection.close()
                    return
                if f == "404":
                    return self._err(404, "notFound")
            if cr.startswith("bytes */"):
                got = len(s["data"])
                if got >= s["size"]:
                    return self._finish(s)
                return self._send(308, headers={"Range": f"bytes=0-{got - 1}"} if got else {})
            rng, total = cr[len("bytes "):].split("/")
            a, b = (int(x) for x in rng.split("-"))
            assert a == len(s["data"]), f"hibás kezdőbájt: {a} != {len(s['data'])}"
            assert int(total) == s["size"]
            assert len(body) == b - a + 1
            if b + 1 < s["size"]:
                assert len(body) % (256 * 1024) == 0, "a köztes szelet nem 256 KB többszöröse"
            s["data"] += body
            if len(s["data"]) >= s["size"]:
                return self._finish(s)
            return self._send(308, headers={"Range": f"bytes=0-{len(s['data']) - 1}"})
        if p == "/upload/youtube/v3/thumbnails/set" and method == "POST":
            self._body()
            if STATE["thumb_status"] != 200:
                return self._err(STATE["thumb_status"], "forbidden", "thumb forbidden")
            return self._send(200, {"items": [{}]})
        return self._err(404, "notFound", f"{method} {p}")

    def _finish(self, s):
        STATE["insert_count"] += 1
        vid = "VID" + uuid.uuid4().hex[:8]
        meta = s["meta"]
        status = dict(meta.get("status", {}))
        if STATE["locked"]:
            status["privacyStatus"] = "private"
            status.pop("publishAt", None)
        status["uploadStatus"] = "processed"
        v = {"id": vid, "snippet": dict(meta.get("snippet", {}), publishedAt="2026-09-29T12:00:00Z"), "status": status,
             "statistics": {"viewCount": "7", "likeCount": "2", "commentCount": "1"}, "contentDetails": {}}
        STATE["videos"][vid] = v
        STATE["last_upload_bytes"] = len(s["data"])
        return self._send(201, v)


def start():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    BASE["port"] = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
