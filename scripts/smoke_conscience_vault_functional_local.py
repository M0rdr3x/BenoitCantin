#!/usr/bin/env python3
"""Smoke fonctionnel local du Coffre SINJIRA V25, sans donnée intime réelle."""

from __future__ import annotations

import re
from typing import Any

from smoke_sensitive_aal2_local import (
    API_URL, ANON_KEY, Response, enroll_totp, jwt_claims, request, require, signup, verify_totp,
)

UUID_RE = re.compile(r"^[0-9a-f-]{36}$", re.I)
CONTENT_1 = "Donnée synthétique de test local — aucune information personnelle réelle."
CONTENT_2 = "Donnée synthétique modifiée — aucun contenu intime ni donnée personnelle réelle."
ENTRY_TYPE = "local_test_marker"
DEVICE_KEY = "sinjira-local-vault-functional-device-0001"


def rpc(name: str, token: str, body: dict[str, Any]) -> Any:
    response = request("POST", f"/rest/v1/rpc/{name}", token=token, body=body)
    require(200 <= response.status < 300, f"RPC {name}: HTTP {response.status} {response.raw}")
    return response.body


def bootstrap_device(aal2: str) -> None:
    registered = rpc("security_register_device", aal2, {
        "p_device_key": DEVICE_KEY,
        "p_display_name": "Coffre synthétique local",
        "p_device_type": "browser",
        "p_platform": "ci-local",
    })
    require(isinstance(registered, dict), "enregistrement appareil invalide")
    device = registered.get("device")
    require(isinstance(device, dict), "device absent")
    device_id = device.get("id")
    require(isinstance(device_id, str) and UUID_RE.match(device_id), "UUID appareil absent")
    require(device.get("is_current") is True and device.get("is_trusted") is False,
            "un nouvel appareil doit être courant mais non fiable")
    require("device_key" not in device and "last_session_id" not in device,
            "les secrets appareil ne doivent pas être exposés")

    trusted = rpc("security_set_device_trust", aal2, {
        "p_device_id": device_id,
        "p_trusted": True,
        "p_primary": True,
    })
    require(isinstance(trusted, dict), "réponse de confiance invalide")
    require(trusted.get("is_current") is True and trusted.get("is_trusted") is True and trusted.get("is_primary") is True,
            "le premier appareil AAL2 doit devenir courant, fiable et principal")
    require("device_key" not in trusted and "last_session_id" not in trusted,
            "la confiance ne doit pas révéler les secrets appareil")

    devices = rpc("security_list_devices", aal2, {"p_current_device_key": DEVICE_KEY})
    require(isinstance(devices, list) and len(devices) == 1 and isinstance(devices[0], dict),
            "la liste assainie doit contenir le seul appareil synthétique")
    current = devices[0]
    require(current.get("id") == device_id and current.get("is_current") is True,
            "la liste assainie doit reconnaître l'appareil courant")
    require(current.get("is_trusted") is True and current.get("is_primary") is True,
            "la liste assainie doit confirmer la confiance du premier appareil")
    require("device_key" not in current and "last_session_id" not in current,
            "security_list_devices ne doit jamais révéler les secrets appareil")


def vault(token: str, action: str, **extra: Any) -> Response:
    body = {"action": action, **extra}
    return request("POST", "/functions/v1/conscience-vault", token=token, body=body)


def ok(token: str, action: str, **extra: Any) -> dict[str, Any]:
    response = vault(token, action, **extra)
    require(200 <= response.status < 300, f"Coffre {action}: HTTP {response.status} {response.raw}")
    require(isinstance(response.body, dict) and response.body.get("ok") is True,
            f"Coffre {action}: succès JSON attendu")
    return response.body


def expect_code(response: Response, status: int, code: str, context: str) -> None:
    require(response.status == status, f"{context}: HTTP {status} attendu, reçu {response.status}")
    require(isinstance(response.body, dict) and response.body.get("code") == code,
            f"{context}: code {code} attendu, reçu {response.raw}")


def open_session(aal2: str) -> str:
    data = ok(aal2, "open_session",
        device_key=DEVICE_KEY,
        display_name="Coffre synthétique local",
        device_type="browser",
        platform="ci-local",
        ttl_seconds=60,
    )
    session_id = data.get("vault_session_id")
    require(isinstance(session_id, str) and UUID_RE.match(session_id), "UUID session Coffre absent")
    require(data.get("expires_in_seconds") == 60, "TTL de 60 secondes attendu")
    require(data.get("geo_mode") == "disabled", "géolocalisation locale doit rester désactivée")
    privacy = data.get("privacy")
    require(isinstance(privacy, dict), "bloc privacy absent")
    require(privacy.get("identity_from_verified_jwt") is True, "identité JWT vérifiée obligatoire")
    require(privacy.get("raw_ip_stored") is False and privacy.get("gps_used") is False,
            "aucune IP brute/GPS ne doit être utilisé")
    require(privacy.get("client_geo_accepted") is False and privacy.get("legacy_access") is False,
            "géolocalisation client/accès legacy interdits")
    security = data.get("security")
    require(isinstance(security, dict) and security.get("risk_model_version") == "v25.0",
            "décision sécurité V25 absente")
    require(security.get("mandatory_step_up") is True and security.get("requires_step_up") is True,
            "step-up obligatoire absent")
    require(security.get("outcome") in ("allow", "approved"), "décision sécurité non approuvée")
    score = security.get("risk_score")
    require(isinstance(score, int) and 0 <= score < 75, "score de risque invalide")
    return session_id


def main() -> int:
    require(API_URL.startswith("http://127.0.0.1") or API_URL.startswith("http://localhost"), "API locale obligatoire")
    require(bool(ANON_KEY), "clé publique locale absente")

    aal1, _uid, _email, _password = signup()
    factor_id, secret = enroll_totp(aal1)
    aal2 = verify_totp(aal1, factor_id, secret)
    require(jwt_claims(aal2).get("aal") == "aal2", "JWT AAL2 absent")
    bootstrap_device(aal2)

    bad_ttl = vault(aal2, "open_session", device_key=DEVICE_KEY, ttl_seconds=59)
    expect_code(bad_ttl, 400, "VAULT_TTL_INVALID", "TTL trop court")

    injected = vault(aal2, "open_session", device_key=DEVICE_KEY, ttl_seconds=60,
                     user_id="00000000-0000-0000-0000-000000000000")
    expect_code(injected, 400, "CLIENT_IDENTITY_FORBIDDEN", "identité client injectée")

    session1 = open_session(aal2)
    require(ok(aal2, "list_entries", vault_session_id=session1).get("entries") == [], "Coffre doit être vide au départ")

    created = ok(aal2, "create_entry", vault_session_id=session1,
                 entry_type=ENTRY_TYPE, content_payload=CONTENT_1)
    entry_id = created.get("entry_id")
    require(isinstance(entry_id, str) and UUID_RE.match(entry_id), "UUID entrée absent")

    entries = ok(aal2, "list_entries", vault_session_id=session1).get("entries")
    require(isinstance(entries, list) and len(entries) == 1 and isinstance(entries[0], dict), "entrée synthétique attendue")
    require(entries[0].get("content_payload") == CONTENT_1, "contenu synthétique initial inattendu")

    updated = ok(aal2, "update_entry", vault_session_id=session1, entry_id=entry_id,
                 entry_type=ENTRY_TYPE, content_payload=CONTENT_2)
    require(updated.get("updated") is True, "mise à jour non confirmée")

    entries = ok(aal2, "list_entries", vault_session_id=session1).get("entries")
    require(isinstance(entries, list) and len(entries) == 1 and entries[0].get("content_payload") == CONTENT_2,
            "contenu synthétique modifié attendu")

    session2 = open_session(aal2)
    require(session2 != session1, "une nouvelle capacité doit avoir un nouvel UUID")
    expect_code(vault(aal2, "list_entries", vault_session_id=session1), 403, "VAULT_SESSION_INVALID",
                "ancienne capacité après rotation")

    entries = ok(aal2, "list_entries", vault_session_id=session2).get("entries")
    require(isinstance(entries, list) and len(entries) == 1 and entries[0].get("content_payload") == CONTENT_2,
            "entrée doit persister après rotation de capacité")

    require(ok(aal2, "delete_entry", vault_session_id=session2, entry_id=entry_id).get("deleted") is True,
            "suppression entrée non confirmée")
    require(ok(aal2, "list_entries", vault_session_id=session2).get("entries") == [], "Coffre doit être vide après suppression")

    require(ok(aal2, "revoke_session", vault_session_id=session2).get("revoked") is True,
            "révocation session non confirmée")
    expect_code(vault(aal2, "list_entries", vault_session_id=session2), 403, "VAULT_SESSION_INVALID",
                "capacité révoquée")
    expect_code(vault(aal2, "list_entries"), 403, "VAULT_SESSION_REQUIRED", "capacité absente")

    print("OK smoke Coffre V25: TOTP/AAL2 réel, premier appareil courant fiable sans privilège, capacité 60 s, CRUD synthétique, rotation, révocation et suppression vérifiées sans contenu intime réel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
