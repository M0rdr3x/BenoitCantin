#!/usr/bin/env python3
"""Exercise real Storage API with two local, synthetic accounts; never target production."""
import base64
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("SINJIRA_LOCAL_API_URL", "").rstrip("/")
KEY = os.environ.get("SINJIRA_LOCAL_ANON_KEY", "")
BUCKET = "sinjira-character-sources"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aUioAAAAASUVORK5CYII=")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

def check(condition, label):
    if not condition:
        raise RuntimeError(label)

def request(method, path, token=None, data=None, content_type="application/json"):
    check(path.startswith("/") and not path.startswith("//"), "Invalid local path")
    headers = {"apikey": KEY, "Authorization": "Bearer " + (token or KEY)}
    if data is not None:
        headers["Content-Type"] = content_type
        if not isinstance(data, bytes):
            data = json.dumps(data).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with OPENER.open(req, timeout=20) as res:
            return res.status, res.read(65536)
    except urllib.error.HTTPError as res:
        return res.code, res.read(65536)

def signup():
    status, raw = request("POST", "/auth/v1/signup", data={
        "email": "storage-" + secrets.token_hex(8) + "@example.com",
        "password": "Local-Storage-" + secrets.token_hex(20),
        "data": {"pseudo": "Storage ACL test", "birth_date": "1990-01-15",
                 "date_of_birth": "1990-01-15", "gender": "Homme", "sex": "male"}
    })
    check(status in (200, 201), "Local signup failed: HTTP " + str(status))
    response = json.loads(raw)
    return response["access_token"], response["user"]["id"]

def main():
    u = urllib.parse.urlsplit(BASE)
    check(u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost")
          and u.port == 54321 and not u.username and not u.password and not u.path
          and not u.query and not u.fragment and bool(KEY), "Local API required")
    a, uid_a = signup()
    b, uid_b = signup()
    check(uid_a != uid_b, "Distinct local users required")
    pa = uid_a + "/storage-acl.png"
    pb = uid_b + "/storage-acl.png"
    def obj(p): return "/storage/v1/object/" + BUCKET + "/" + p
    def read(p, token): return request("GET", "/storage/v1/object/authenticated/" + BUCKET + "/" + p, token)
    def sign(p, token): return request("POST", "/storage/v1/object/sign/" + BUCKET + "/" + p, token, {"expiresIn": 30})
    def delete(p, token): return request("DELETE", "/storage/v1/object/" + BUCKET, token, {"prefixes": [p]})
    for p, token in ((pa, a), (pb, b)):
        status, _ = request("POST", obj(p), token, PNG, "image/png")
        check(status in (200, 201), "Owner upload failed: HTTP " + str(status))
        check(read(p, token) == (200, PNG), "Owner read failed")
        status, raw = sign(p, token)
        check(status == 200 and bool(json.loads(raw).get("signedURL")), "Owner signing failed")
    for p, token in ((pa, b), (pb, a)):
        check(read(p, token)[0] in (400, 401, 403, 404), "Cross-account read not denied")
        check(sign(p, token)[0] in (400, 401, 403, 404), "Cross-account signing not denied")
    check(request("GET", "/storage/v1/object/public/" + BUCKET + "/" + pb)[0]
          in (400, 401, 403, 404), "Public read not denied")
    check(request("POST", obj(uid_b + "/cross.png"), a, PNG, "image/png")[0]
          in (400, 401, 403, 404), "Cross-account upload not denied")
    status, _ = delete(pb, a)
    check(status in (200, 204, 400, 401, 403, 404), "Unexpected cross-account delete status")
    check(read(pb, b) == (200, PNG), "Cross-account deletion altered B object")
    for p, token in ((pa, a), (pb, b)):
        status, _ = delete(p, token)
        check(status in (200, 204), "Owner deletion failed: HTTP " + str(status))
        check(read(p, token)[0] in (400, 403, 404), "Deleted object still readable")
    print("PASS: local two-account Storage upload, read, signing, deletion and public-access isolation")

if __name__ == "__main__":
    main()
