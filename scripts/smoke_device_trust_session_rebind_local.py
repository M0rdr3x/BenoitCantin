#!/usr/bin/env python3
"""Smoke local V25 : une device_key copiée ne transporte jamais la confiance."""

from __future__ import annotations

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

DEVICE_A = "sinjira-local-session-rebind-device-a-00000001"


def rpc_response(name: str, token: str, body: dict[str, Any]) -> Response:
    return request("POST", f"/rest/v1/rpc/{name}", token=token, body=body)


def rpc(name: str, token: str, body: dict[str, Any]) -> Any:
    response = rpc_response(name, token, body)
    require(200 <= response.status < 300, f"RPC {name}: HTTP {response.status} {response.raw}")
    return response.body


def expect_refused(response: Response, marker: str, context: str) -> None:
    require(response.status >= 400, f"{context}: refus HTTP attendu, reçu {response.status}")
    require(marker in response.raw, f"{context}: marqueur {marker} absent: {response.raw}")


def register(token: str, label: str) -> dict[str, Any]:
    result = rpc("security_register_device", token, {
        "p_device_key": DEVICE_A,
        "p_display_name": label,
        "p_device_type": "browser",
        "p_platform": "ci-local",
    })
    require(isinstance(result, dict), f"{label}: réponse invalide")
    device = result.get("device")
    require(isinstance(device, dict), f"{label}: appareil absent")
    require(device.get("is_current") is True, f"{label}: appareil courant attendu")
    require("device_key" not in device and "last_session_id" not in device,
            f"{label}: secret appareil exposé")
    return device


def set_trust(token: str, device_id: str, trusted: bool = True, primary: bool = True) -> Response:
    return rpc_response("security_set_device_trust", token, {
        "p_device_id": device_id,
        "p_trusted": trusted,
        "p_primary": primary,
    })


def main() -> int:
    require(API_URL.startswith("http://127.0.0.1") or API_URL.startswith("http://localhost"),
            "API locale obligatoire")
    require(bool(ANON_KEY), "clé publique locale absente")

    # Session A : bootstrap légitime du premier appareil fiable après AAL2.
    aal1_a, _user_id, email, password = signup()
    factor_id, secret = enroll_totp(aal1_a)
    aal2_a = verify_totp(aal1_a, factor_id, secret)
    require(jwt_claims(aal2_a).get("aal") == "aal2", "session A: AAL2 attendu")

    device_a = register(aal2_a, "Appareil A initial")
    device_id = str(device_a.get("id"))
    trusted_a_response = set_trust(aal2_a, device_id)
    require(200 <= trusted_a_response.status < 300,
            f"bootstrap confiance A impossible: {trusted_a_response.status} {trusted_a_response.raw}")
    trusted_a = trusted_a_response.body
    require(isinstance(trusted_a, dict), "bootstrap confiance A: JSON invalide")
    require(trusted_a.get("is_trusted") is True and trusted_a.get("is_primary") is True,
            "session A: appareil fiable/principal attendu")

    # Session B : possession du compte en AAL1 + copie de la même device_key.
    # Avant le correctif, security_register_device réécrivait last_session_id tout en
    # conservant is_trusted/is_primary, transférant implicitement la confiance.
    aal1_b = sign_in(email, password)
    require(jwt_claims(aal1_b).get("aal") == "aal1", "session B: AAL1 attendu avant TOTP")
    rebound = register(aal1_b, "Même clé depuis nouvelle session")
    require(rebound.get("id") == device_id, "le rebind doit viser la même ligne appareil")
    require(rebound.get("is_trusted") is False,
            "une device_key copiée ne doit jamais conserver la confiance après changement de session")
    require(rebound.get("is_primary") is False,
            "une device_key copiée ne doit jamais conserver le statut principal après changement de session")

    # L'ancienne session n'est plus la session courante de cette ligne et ne peut pas
    # restaurer silencieusement la confiance après le rebind.
    old_session_retrust = set_trust(aal2_a, device_id)
    expect_refused(old_session_retrust, "CURRENT_DEVICE_REQUIRED",
                   "ancienne session après rebind")

    # La nouvelle session AAL1 possède la clé mais pas la preuve MFA : la clé seule reste insuffisante.
    copied_key_retrust = set_trust(aal1_b, device_id)
    expect_refused(copied_key_retrust, "AAL2_REQUIRED",
                   "nouvelle session AAL1 avec clé copiée")

    # Récupération légitime : après TOTP réel, la nouvelle session peut bootstrapper à nouveau
    # puisqu'aucun autre appareil fiable n'existe. On protège sans verrouiller définitivement l'humain.
    aal2_b = verify_totp(aal1_b, factor_id, secret)
    require(jwt_claims(aal2_b).get("aal") == "aal2", "session B: AAL2 attendu après TOTP")
    recovered_response = set_trust(aal2_b, device_id)
    require(200 <= recovered_response.status < 300,
            f"récupération AAL2 impossible: {recovered_response.status} {recovered_response.raw}")
    recovered = recovered_response.body
    require(isinstance(recovered, dict), "récupération AAL2: JSON invalide")
    require(recovered.get("is_trusted") is True and recovered.get("is_primary") is True,
            "récupération AAL2 doit restaurer explicitement la confiance")
    require("device_key" not in recovered and "last_session_id" not in recovered,
            "la restauration de confiance ne doit révéler aucun secret appareil")

    print(
        "OK smoke rebind appareil V25: clé copiée => confiance/principal retirés; ancienne session rejetée; "
        "AAL1 insuffisant; restauration humaine possible uniquement après AAL2 réel."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
