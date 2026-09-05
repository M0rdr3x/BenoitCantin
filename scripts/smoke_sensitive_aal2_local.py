#!/usr/bin/env python3
"""Smoke local AAL2 pour Mon IA et le Coffre SINJIRA V25.

Le test utilise uniquement Supabase local, une clé publique locale et un compte
synthétique. Il prouve le passage AAL1 -> TOTP -> AAL2 avant d'atteindre le
moteur de risque des deux Edge Functions sensibles.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


API_URL = os.environ.get("SINJIRA_LOCAL_API_URL", "").rstrip("/")
ANON_KEY = os.environ.get("SINJIRA_LOCAL_ANON_KEY", "")


def fail(message: str) -> None:
    print(f"ECHEC smoke AAL2 V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


@dataclass(frozen=True)
class Response:
    status: int
    body: Any
    raw: str


def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
) -> Response:
    headers = {"apikey": ANON_KEY, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")

    req = urllib.request.Request(f"{API_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except OSError as exc:
        fail(f"requête {method} {path} impossible: {exc}")

    try:
        parsed = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        parsed = raw
    return Response(status=status, body=parsed, raw=raw)


def jwt_claims(token: str) -> dict[str, Any]:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
        claims = json.loads(decoded.decode("utf-8"))
    except (IndexError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        fail(f"JWT local illisible: {exc}")
    require(isinstance(claims, dict), "payload JWT local invalide")
    return claims


def totp_code(secret: str, *, timestamp: int | None = None) -> str:
    normalized = secret.strip().replace(" ", "").upper()
    normalized += "=" * (-len(normalized) % 8)
    try:
        key = base64.b32decode(normalized, casefold=True)
    except ValueError as exc:
        fail(f"secret TOTP local invalide: {exc}")
    counter = int((timestamp if timestamp is not None else time.time()) // 30)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{binary % 1_000_000:06d}"


def signup() -> tuple[str, str, str, str]:
    email = "sinjira-sensitive-aal2-smoke@example.com"
    password = "SINJIRA-Local-AAL2-2026!"
    response = request(
        "POST",
        "/auth/v1/signup",
        body={
            "email": email,
            "password": password,
            "data": {
                "pseudo": "Smoke AAL2 V25",
                "birth_date": "1990-01-15",
                "date_of_birth": "1990-01-15",
                "gender": "Homme",
                "sex": "male",
            },
        },
    )
    require(response.status in (200, 201), f"signup refusé: HTTP {response.status} {response.raw}")
    require(isinstance(response.body, dict), "signup: réponse JSON invalide")
    token = response.body.get("access_token")
    user = response.body.get("user") or {}
    user_id = user.get("id") if isinstance(user, dict) else None
    require(isinstance(token, str) and token, "signup: access_token absent")
    require(isinstance(user_id, str) and user_id, "signup: user.id absent")
    require(jwt_claims(token).get("aal") in (None, "aal1"), "signup doit produire une session AAL1")
    return token, user_id, email, password


def sign_in(email: str, password: str) -> str:
    response = request(
        "POST",
        "/auth/v1/token?grant_type=password",
        body={"email": email, "password": password},
    )
    require(response.status == 200, f"sign-in refusé: HTTP {response.status} {response.raw}")
    require(isinstance(response.body, dict), "sign-in: réponse JSON invalide")
    token = response.body.get("access_token")
    require(isinstance(token, str) and token, "sign-in: access_token absent")
    return token


def enroll_totp(token: str) -> tuple[str, str]:
    response = request(
        "POST",
        "/auth/v1/factors",
        token=token,
        body={"factor_type": "totp", "friendly_name": "SINJIRA smoke AAL2 local"},
    )
    require(response.status == 200, f"enrôlement TOTP refusé: HTTP {response.status} {response.raw}")
    require(isinstance(response.body, dict), "enrôlement TOTP: réponse JSON invalide")
    factor_id = response.body.get("id")
    totp = response.body.get("totp") or {}
    secret = totp.get("secret") if isinstance(totp, dict) else None
    require(isinstance(factor_id, str) and factor_id, "factor id absent")
    require(isinstance(secret, str) and secret, "secret TOTP absent")
    return factor_id, secret


def verify_totp(token: str, factor_id: str, secret: str) -> str:
    challenge = request(
        "POST",
        f"/auth/v1/factors/{factor_id}/challenge",
        token=token,
        body={},
    )
    require(challenge.status == 200, f"challenge TOTP refusé: HTTP {challenge.status} {challenge.raw}")
    require(isinstance(challenge.body, dict), "challenge TOTP: réponse JSON invalide")
    challenge_id = challenge.body.get("id")
    require(isinstance(challenge_id, str) and challenge_id, "challenge id absent")

    # Une petite tolérance de fenêtre évite un faux négatif si le code change au milieu du round-trip.
    attempts = [int(time.time()), int(time.time()) - 30, int(time.time()) + 30]
    last: Response | None = None
    for moment in attempts:
        last = request(
            "POST",
            f"/auth/v1/factors/{factor_id}/verify",
            token=token,
            body={"challenge_id": challenge_id, "code": totp_code(secret, timestamp=moment)},
        )
        if last.status == 200 and isinstance(last.body, dict) and isinstance(last.body.get("access_token"), str):
            aal2 = last.body["access_token"]
            require(jwt_claims(aal2).get("aal") == "aal2", "verify TOTP n'a pas produit un JWT aal2")
            return aal2
    require(last is not None, "aucune tentative TOTP exécutée")
    fail(f"verify TOTP refusé: HTTP {last.status} {last.raw}")


def edge_body(function_name: str) -> dict[str, Any]:
    if function_name == "personal-ai":
        return {
            "action": "get_state",
            "device_key": "sinjira-local-aal2-personal-ai-device-0001",
            "display_name": "Smoke AAL2 local",
            "device_type": "browser",
            "platform": "ci-local",
        }
    if function_name == "conscience-vault":
        return {
            "action": "open_session",
            "device_key": "sinjira-local-aal2-vault-device-00000001",
            "display_name": "Smoke AAL2 local",
            "device_type": "browser",
            "platform": "ci-local",
            "ttl_seconds": 60,
        }
    fail(f"fonction sensible inconnue: {function_name}")


def call_edge(function_name: str, token: str) -> Response:
    return request(
        "POST",
        f"/functions/v1/{function_name}",
        token=token,
        body=edge_body(function_name),
    )


def response_code(response: Response) -> str:
    return str(response.body.get("code") or "") if isinstance(response.body, dict) else ""


def expect_edge_code(function_name: str, token: str, expected: str) -> None:
    response = call_edge(function_name, token)
    require(response.status == 403, f"{function_name}: HTTP 403 attendu pour {expected}, reçu {response.status} {response.raw}")
    require(response_code(response) == expected, f"{function_name}: code {expected} attendu, reçu {response.raw}")


def expect_after_aal2(function_name: str, token: str) -> None:
    response = call_edge(function_name, token)
    code = response_code(response)
    forbidden = {"AUTH_REQUIRED", "MFA_SETUP_REQUIRED", "MFA_REQUIRED", "MFA_STATE_UNAVAILABLE"}
    require(code not in forbidden, f"{function_name}: la requête aal2 est encore refusée par MFA: {response.raw}")
    if 200 <= response.status < 300:
        require(isinstance(response.body, dict) and response.body.get("ok") is True, f"{function_name}: succès JSON invalide")
        return
    require(
        response.status == 403 and code == "SECURITY_CHALLENGE_REQUIRED",
        f"{function_name}: après AAL2, succès ou challenge de risque attendu; reçu HTTP {response.status} {response.raw}",
    )


def main() -> int:
    require(API_URL.startswith("http://127.0.0.1") or API_URL.startswith("http://localhost"), "API locale obligatoire")
    require(bool(ANON_KEY), "clé publique locale absente")

    first_aal1, _user_id, email, password = signup()

    # Sans facteur vérifié, les deux zones sensibles refusent avant tout moteur de risque.
    for function_name in ("personal-ai", "conscience-vault"):
        expect_edge_code(function_name, first_aal1, "MFA_SETUP_REQUIRED")

    factor_id, secret = enroll_totp(first_aal1)
    enrollment_aal2 = verify_totp(first_aal1, factor_id, secret)
    require(jwt_claims(enrollment_aal2).get("aal") == "aal2", "session d'enrôlement non AAL2")

    # Une nouvelle connexion revient à AAL1 mais sait qu'un facteur AAL2 existe.
    second_aal1 = sign_in(email, password)
    require(jwt_claims(second_aal1).get("aal") == "aal1", "nouvelle connexion doit rester aal1 avant challenge TOTP")
    for function_name in ("personal-ai", "conscience-vault"):
        expect_edge_code(function_name, second_aal1, "MFA_REQUIRED")

    final_aal2 = verify_totp(second_aal1, factor_id, secret)
    require(jwt_claims(final_aal2).get("aal") == "aal2", "JWT final aal2 absent")

    # Après AAL2, le contrôle MFA est franchi. Un appareil inconnu peut encore être arrêté
    # par le moteur de risque V25, ce qui est une protection supplémentaire et non un échec.
    for function_name in ("personal-ai", "conscience-vault"):
        expect_after_aal2(function_name, final_aal2)

    print(
        "OK smoke AAL2 V25: Mon IA + Coffre refusent sans MFA, refusent une session aal1 après enrôlement, "
        "puis acceptent un JWT aal2 jusqu'au moteur de risque sans contourner le challenge appareil."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
