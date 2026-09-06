#!/usr/bin/env python3
"""Smoke local V25 pour la continuité des challenges entre appareils du Coffre."""

from __future__ import annotations

import re
from typing import Any

from smoke_sensitive_aal2_local import (
    API_URL,
    ANON_KEY,
    Response,
    enroll_totp,
    jwt_claims,
    request,
    require,
    sign_in,
    signup,
    verify_totp,
)

UUID_RE = re.compile(r"^[0-9a-f-]{36}$", re.I)
DEVICE_A = "sinjira-local-challenge-device-a-00000001"
DEVICE_B = "sinjira-local-challenge-device-b-00000001"
DEVICE_C = "sinjira-local-challenge-device-c-00000001"


def rpc_response(name: str, token: str, body: dict[str, Any]) -> Response:
    return request("POST", f"/rest/v1/rpc/{name}", token=token, body=body)


def rpc(name: str, token: str, body: dict[str, Any]) -> Any:
    response = rpc_response(name, token, body)
    require(200 <= response.status < 300, f"RPC {name}: HTTP {response.status} {response.raw}")
    return response.body


def expect_rpc_refused(response: Response, marker: str, context: str) -> None:
    require(response.status >= 400, f"{context}: un refus HTTP était attendu, reçu {response.status}")
    require(marker in response.raw, f"{context}: marqueur {marker} absent: {response.raw}")


def register_device(token: str, device_key: str, label: str) -> dict[str, Any]:
    result = rpc("security_register_device", token, {
        "p_device_key": device_key,
        "p_display_name": label,
        "p_device_type": "browser",
        "p_platform": "ci-local",
    })
    require(isinstance(result, dict), f"{label}: réponse d’enregistrement invalide")
    device = result.get("device")
    require(isinstance(device, dict), f"{label}: appareil absent")
    device_id = device.get("id")
    require(isinstance(device_id, str) and UUID_RE.match(device_id), f"{label}: UUID appareil absent")
    require(device.get("is_current") is True, f"{label}: l’appareil doit être courant")
    require("device_key" not in device and "last_session_id" not in device,
            f"{label}: aucun secret appareil ne doit sortir de la RPC")
    return device


def trust_first_device(token: str, device_id: str) -> None:
    result = rpc("security_set_device_trust", token, {
        "p_device_id": device_id,
        "p_trusted": True,
        "p_primary": True,
    })
    require(isinstance(result, dict), "confiance appareil A: réponse invalide")
    require(result.get("is_current") is True, "appareil A doit être courant")
    require(result.get("is_trusted") is True and result.get("is_primary") is True,
            "appareil A doit devenir fiable et principal")
    require("device_key" not in result and "last_session_id" not in result,
            "la confiance appareil ne doit pas révéler les secrets")


def vault_open(token: str, device_key: str, label: str) -> Response:
    return request("POST", "/functions/v1/conscience-vault", token=token, body={
        "action": "open_session",
        "device_key": device_key,
        "display_name": label,
        "device_type": "browser",
        "platform": "ci-local",
        "ttl_seconds": 60,
    })


def expect_challenge(response: Response, expected_confirmation: str, context: str) -> str:
    require(response.status == 403, f"{context}: HTTP 403 attendu, reçu {response.status} {response.raw}")
    require(isinstance(response.body, dict), f"{context}: JSON invalide")
    require(response.body.get("code") == "SECURITY_CHALLENGE_REQUIRED",
            f"{context}: challenge de sécurité attendu: {response.raw}")
    security = response.body.get("security")
    require(isinstance(security, dict), f"{context}: décision sécurité absente")
    require(security.get("risk_model_version") == "v25.0", f"{context}: modèle V25 absent")
    require(security.get("mandatory_step_up") is True and security.get("requires_step_up") is True,
            f"{context}: step-up obligatoire absent")
    require(security.get("trusted_device_confirmation") == expected_confirmation,
            f"{context}: confirmation {expected_confirmation} attendue, reçu {security}")
    challenge_id = security.get("challenge_id")
    require(isinstance(challenge_id, str) and UUID_RE.match(challenge_id), f"{context}: UUID challenge absent")
    return challenge_id


def expect_vault_success(response: Response, context: str) -> str:
    require(200 <= response.status < 300, f"{context}: succès attendu, reçu {response.status} {response.raw}")
    require(isinstance(response.body, dict) and response.body.get("ok") is True,
            f"{context}: succès JSON invalide")
    security = response.body.get("security")
    require(isinstance(security, dict), f"{context}: décision sécurité absente")
    require(security.get("risk_model_version") == "v25.0", f"{context}: modèle V25 absent")
    require(security.get("mandatory_step_up") is True and security.get("requires_step_up") is True,
            f"{context}: step-up obligatoire absent")
    require(security.get("outcome") in ("allow", "approved"), f"{context}: décision non autorisée")
    session_id = response.body.get("vault_session_id")
    require(isinstance(session_id, str) and UUID_RE.match(session_id), f"{context}: capacité Coffre absente")
    return session_id


def resolve(token: str, challenge_id: str, device_key: str, decision: str) -> dict[str, Any]:
    result = rpc("security_resolve_connection_challenge", token, {
        "p_challenge_id": challenge_id,
        "p_device_key": device_key,
        "p_decision": decision,
    })
    require(isinstance(result, dict), "résolution challenge: réponse invalide")
    require("device_key" not in result and "last_session_id" not in result,
            "la résolution challenge ne doit révéler aucun secret appareil")
    return result


def main() -> int:
    require(API_URL.startswith("http://127.0.0.1") or API_URL.startswith("http://localhost"),
            "API locale obligatoire")
    require(bool(ANON_KEY), "clé publique locale absente")

    # Appareil A : première session AAL2, bootstrap légitime du premier appareil fiable.
    aal1_a, _user_id, email, password = signup()
    factor_id, secret = enroll_totp(aal1_a)
    aal2_a = verify_totp(aal1_a, factor_id, secret)
    require(jwt_claims(aal2_a).get("aal") == "aal2", "appareil A: JWT AAL2 absent")
    device_a = register_device(aal2_a, DEVICE_A, "Appareil A fiable")
    trust_first_device(aal2_a, str(device_a["id"]))

    # Appareil B : nouvelle session AAL2, connu mais volontairement non fiable.
    aal1_b = sign_in(email, password)
    require(jwt_claims(aal1_b).get("aal") == "aal1", "appareil B: session AAL1 attendue avant TOTP")
    aal2_b = verify_totp(aal1_b, factor_id, secret)
    require(jwt_claims(aal2_b).get("aal") == "aal2", "appareil B: JWT AAL2 absent")
    device_b = register_device(aal2_b, DEVICE_B, "Appareil B demandeur")
    require(device_b.get("is_trusted") is False, "appareil B doit rester non fiable avant approbation")

    first_b = vault_open(aal2_b, DEVICE_B, "Appareil B demandeur")
    challenge_b = expect_challenge(first_b, "reissued", "première demande B")

    retry_b = vault_open(aal2_b, DEVICE_B, "Appareil B demandeur")
    retry_b_id = expect_challenge(retry_b, "pending", "retry B avant approbation")
    require(retry_b_id == challenge_b, "un retry B doit réutiliser exactement le même challenge pending")

    # Le legacy MFA ne peut plus transformer le challenge Coffre en auto-approbation.
    self_mfa = rpc_response("security_resolve_connection_challenge_mfa", aal2_b, {
        "p_challenge_id": challenge_b,
        "p_device_key": DEVICE_B,
    })
    expect_rpc_refused(self_mfa, "TRUSTED_OTHER_DEVICE_REQUIRED", "auto-approbation MFA de B")

    # A, réellement fiable et courant dans sa propre session, approuve B.
    approved_b = resolve(aal2_a, challenge_b, DEVICE_A, "approved")
    require(approved_b.get("status") == "approved", "challenge B doit être approuvé")
    require(approved_b.get("request_device_id") == device_b.get("id"), "challenge B doit viser l’appareil B")
    require(approved_b.get("resolved_device_id") == device_a.get("id"),
            "challenge B doit être résolu par l’autre appareil A")

    session_b = expect_vault_success(
        vault_open(aal2_b, DEVICE_B, "Appareil B demandeur"),
        "B après approbation par A",
    )

    # Appareil C : une troisième session prouve qu’une clé A copiée ne suffit pas.
    aal1_c = sign_in(email, password)
    require(jwt_claims(aal1_c).get("aal") == "aal1", "appareil C: session AAL1 attendue avant TOTP")
    aal2_c = verify_totp(aal1_c, factor_id, secret)
    require(jwt_claims(aal2_c).get("aal") == "aal2", "appareil C: JWT AAL2 absent")
    device_c = register_device(aal2_c, DEVICE_C, "Appareil C demandeur")
    require(device_c.get("is_trusted") is False, "appareil C doit rester non fiable avant décision")

    challenge_c = expect_challenge(
        vault_open(aal2_c, DEVICE_C, "Appareil C demandeur"),
        "reissued",
        "première demande C",
    )

    stolen_key_attempt = rpc_response("security_resolve_connection_challenge", aal2_c, {
        "p_challenge_id": challenge_c,
        "p_device_key": DEVICE_A,
        "p_decision": "approved",
    })
    expect_rpc_refused(stolen_key_attempt, "CURRENT_TRUSTED_DEVICE_REQUIRED",
                       "clé A utilisée depuis la session C")

    denied_c = resolve(aal2_a, challenge_c, DEVICE_A, "denied")
    require(denied_c.get("status") == "denied", "challenge C doit être refusé")
    require(denied_c.get("request_device_id") == device_c.get("id"), "challenge C doit viser l’appareil C")
    require(denied_c.get("resolved_device_id") == device_a.get("id"),
            "challenge C doit être refusé par l’autre appareil A")

    blocked_c = vault_open(aal2_c, DEVICE_C, "Appareil C demandeur")
    require(blocked_c.status == 403, f"C révoqué: HTTP 403 attendu, reçu {blocked_c.status} {blocked_c.raw}")
    require(isinstance(blocked_c.body, dict) and blocked_c.body.get("code") == "SECURITY_BLOCKED",
            f"C révoqué doit être bloqué sans nouveau challenge: {blocked_c.raw}")
    blocked_security = blocked_c.body.get("security")
    require(isinstance(blocked_security, dict) and blocked_security.get("outcome") == "block",
            "C révoqué doit produire une décision block")
    require(blocked_security.get("challenge_id") in (None, ""),
            "C révoqué ne doit pas recevoir un nouveau challenge")

    # Nettoyage de la capacité synthétique B; aucune donnée intime n’a été créée.
    cleanup_b = request("POST", "/functions/v1/conscience-vault", token=aal2_b, body={
        "action": "revoke_session",
        "vault_session_id": session_b,
    })
    require(200 <= cleanup_b.status < 300, f"révocation capacité B: {cleanup_b.status} {cleanup_b.raw}")

    print(
        "OK smoke challenge appareils V25: retry pending stable, auto-approbation MFA du Coffre refusée, "
        "approbation liée à un autre appareil courant fiable, clé d’un autre appareil insuffisante et refus final bloquant vérifiés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
