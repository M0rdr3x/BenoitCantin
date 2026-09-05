#!/usr/bin/env python3
"""Smoke fonctionnel local Mon IA V25 derrière AAL2 et appareil fiable.

Le parcours utilise uniquement un utilisateur synthétique, la clé publique locale,
les RPC utilisateur du Centre de sécurité et l'Edge `personal-ai`. Il n'accède
jamais directement aux tables privées Mon IA.
"""

from __future__ import annotations

from typing import Any

from smoke_sensitive_aal2_local import (
    API_URL,
    ANON_KEY,
    Response,
    enroll_totp,
    fail,
    jwt_claims,
    request,
    require,
    signup,
    verify_totp,
)

DEVICE_KEY = "sinjira-local-personal-ai-functional-device-0001"
DEVICE_META = {
    "device_key": DEVICE_KEY,
    "display_name": "Appareil Mon IA synthétique",
    "device_type": "browser",
    "platform": "ci-local",
}


def require_json_object(response: Response, context: str) -> dict[str, Any]:
    require(200 <= response.status < 300, f"{context}: HTTP {response.status} {response.raw}")
    require(isinstance(response.body, dict), f"{context}: réponse JSON objet attendue")
    return response.body


def rpc(name: str, token: str, body: dict[str, Any]) -> Any:
    response = request("POST", f"/rest/v1/rpc/{name}", token=token, body=body)
    require(200 <= response.status < 300, f"RPC {name} refusé: HTTP {response.status} {response.raw}")
    return response.body


def personal_ai(token: str, action: str, **extra: Any) -> Response:
    body: dict[str, Any] = {"action": action, **DEVICE_META}
    body.update(extra)
    return request("POST", "/functions/v1/personal-ai", token=token, body=body)


def personal_ai_ok(token: str, action: str, **extra: Any) -> dict[str, Any]:
    response = personal_ai(token, action, **extra)
    data = require_json_object(response, f"Mon IA {action}")
    require(data.get("ok") is True, f"Mon IA {action}: ok=true attendu, reçu {response.raw}")
    security = data.get("security")
    require(isinstance(security, dict), f"Mon IA {action}: décision sécurité absente")
    require(security.get("risk_model_version") == "v25.0", f"Mon IA {action}: modèle de risque inattendu")
    require(security.get("mandatory_step_up") is True, f"Mon IA {action}: step-up obligatoire absent")
    require(security.get("requires_step_up") is True, f"Mon IA {action}: requires_step_up absent")
    require(security.get("outcome") in ("allow", "approved"), f"Mon IA {action}: outcome non autorisé")
    score = security.get("risk_score")
    require(isinstance(score, int) and 0 <= score < 75, f"Mon IA {action}: score de risque invalide {score!r}")
    return data


def assert_runtime_disabled(state: dict[str, Any], context: str) -> None:
    settings = state.get("settings")
    runtime = state.get("runtime")
    permissions = state.get("source_permissions")
    require(isinstance(settings, dict), f"{context}: settings absents")
    require(isinstance(runtime, dict), f"{context}: runtime absent")
    require(isinstance(permissions, list), f"{context}: source_permissions doit être une liste")
    require(settings.get("runtime_status") == "not_configured", f"{context}: runtime_status doit rester not_configured")
    for key in ("conversation_enabled", "memory_enabled", "source_retrieval_enabled", "provider_configured"):
        require(runtime.get(key) is False, f"{context}: {key} doit rester false")


def permission_map(state: dict[str, Any]) -> dict[str, bool]:
    rows = state.get("source_permissions")
    require(isinstance(rows, list), "source_permissions invalide")
    result: dict[str, bool] = {}
    for row in rows:
        require(isinstance(row, dict), "permission source invalide")
        source = row.get("source_type")
        granted = row.get("granted")
        require(source in ("life_story", "employment"), f"source inattendue dans l'état: {source!r}")
        require(isinstance(granted, bool), f"permission {source}: granted invalide")
        result[str(source)] = granted
    return result


def bootstrap_first_trusted_device(aal2: str) -> str:
    registered = rpc(
        "security_register_device",
        aal2,
        {
            "p_device_key": DEVICE_KEY,
            "p_display_name": DEVICE_META["display_name"],
            "p_device_type": DEVICE_META["device_type"],
            "p_platform": DEVICE_META["platform"],
        },
    )
    require(isinstance(registered, dict), "security_register_device: objet JSON attendu")
    device = registered.get("device")
    require(isinstance(device, dict), "security_register_device: device absent")
    device_id = device.get("id")
    require(isinstance(device_id, str) and device_id, "security_register_device: id absent")
    require(device.get("is_current") is True, "le premier appareil doit être celui de la session AAL2 courante")
    require(device.get("is_trusted") is False, "un nouvel appareil ne doit jamais être fiable automatiquement")
    require("device_key" not in device and "last_session_id" not in device, "la réponse appareil ne doit pas exposer les secrets de possession")

    trusted = rpc(
        "security_set_device_trust",
        aal2,
        {"p_device_id": device_id, "p_trusted": True, "p_primary": True},
    )
    require(isinstance(trusted, dict), "security_set_device_trust: objet JSON attendu")
    require(trusted.get("id") == device_id, "security_set_device_trust: appareil inattendu")
    require(trusted.get("is_trusted") is True, "le bootstrap AAL2 du premier appareil doit établir la confiance")
    require(trusted.get("is_primary") is True, "le premier appareil fiable doit devenir principal dans ce smoke")
    require(trusted.get("is_current") is True, "l'appareil fiable doit rester celui de la session courante")
    require("device_key" not in trusted and "last_session_id" not in trusted, "la confiance ne doit pas révéler device_key/session")

    devices = rpc("security_list_devices", aal2, {"p_current_device_key": DEVICE_KEY})
    require(isinstance(devices, list) and len(devices) == 1, "security_list_devices: exactement un appareil synthétique attendu")
    listed = devices[0]
    require(isinstance(listed, dict), "security_list_devices: ligne invalide")
    require(listed.get("id") == device_id, "security_list_devices: id inattendu")
    require(listed.get("is_current") is True and listed.get("is_trusted") is True and listed.get("is_primary") is True,
            "security_list_devices: appareil courant/fiable/principal attendu")
    require("device_key" not in listed and "last_session_id" not in listed, "security_list_devices ne doit jamais exposer les secrets appareil")
    return device_id


def main() -> int:
    require(API_URL.startswith("http://127.0.0.1") or API_URL.startswith("http://localhost"), "API locale obligatoire")
    require(bool(ANON_KEY), "clé publique locale absente")

    aal1, _user_id, _email, _password = signup()
    factor_id, secret = enroll_totp(aal1)
    aal2 = verify_totp(aal1, factor_id, secret)
    require(jwt_claims(aal2).get("aal") == "aal2", "JWT AAL2 absent")

    # Le premier appareil fiable est le seul bootstrap autorisé sans second appareil :
    # il doit être courant et la session doit être strictement AAL2.
    bootstrap_first_trusted_device(aal2)

    initial = personal_ai_ok(aal2, "get_state")
    state = initial.get("state")
    require(isinstance(state, dict), "get_state initial: state absent")
    assert_runtime_disabled(state, "get_state initial")
    settings = state["settings"]
    require(settings.get("enabled") is False, "Mon IA doit être désactivée par défaut")
    require(settings.get("display_name") is None, "nom IA doit être vide par défaut")
    require(settings.get("language_code") == "fr-CA", "langue par défaut inattendue")
    require(permission_map(state) == {}, "aucune source ne doit être consentie par défaut")

    updated = personal_ai_ok(
        aal2,
        "update_settings",
        enabled=True,
        ai_display_name="Mon IA Test Locale",
        language_code="fr-CA",
    )
    updated_settings = updated.get("settings")
    require(isinstance(updated_settings, dict), "update_settings: settings absents")
    require(updated_settings.get("enabled") is True, "update_settings: enabled=true attendu")
    require(updated_settings.get("display_name") == "Mon IA Test Locale", "update_settings: display_name inattendu")
    require(updated_settings.get("language_code") == "fr-CA", "update_settings: langue inattendue")
    require(updated_settings.get("runtime_status") == "not_configured", "update_settings ne doit jamais configurer un runtime")

    for source in ("life_story", "employment"):
        granted = personal_ai_ok(aal2, "set_source_permission", source_type=source, granted=True)
        require(granted.get("source_type") == source and granted.get("granted") is True,
                f"permission {source}: confirmation invalide")
        require(granted.get("runtime_access_enabled") is False,
                f"permission {source}: le consentement ne doit pas activer la récupération de contenu")

    after_permissions = personal_ai_ok(aal2, "get_state")
    state = after_permissions.get("state")
    require(isinstance(state, dict), "get_state après permissions: state absent")
    assert_runtime_disabled(state, "get_state après permissions")
    require(permission_map(state) == {"employment": True, "life_story": True},
            "seules les deux permissions préparatoires explicites doivent être présentes")

    forbidden_source = personal_ai(aal2, "set_source_permission", source_type="conscience", granted=True)
    require(forbidden_source.status == 400, f"source conscience: HTTP 400 attendu, reçu {forbidden_source.status}")
    require(isinstance(forbidden_source.body, dict) and forbidden_source.body.get("code") == "PERSONAL_AI_SOURCE_FORBIDDEN",
            f"source conscience: refus explicite attendu, reçu {forbidden_source.raw}")

    forbidden_identity = personal_ai(aal2, "get_state", user_id="00000000-0000-0000-0000-000000000000")
    require(forbidden_identity.status == 400, "une identité utilisateur fournie par le client doit être refusée")
    require(isinstance(forbidden_identity.body, dict) and forbidden_identity.body.get("code") == "CLIENT_IDENTITY_FORBIDDEN",
            f"identité client: refus explicite attendu, reçu {forbidden_identity.raw}")

    unknown_action = personal_ai(aal2, "chat", prompt="Aucune donnée réelle")
    require(unknown_action.status == 400, f"action chat: HTTP 400 attendu, reçu {unknown_action.status}")
    require(isinstance(unknown_action.body, dict) and unknown_action.body.get("code") == "UNKNOWN_ACTION",
            f"action chat: UNKNOWN_ACTION attendu, reçu {unknown_action.raw}")

    deleted = personal_ai_ok(aal2, "delete_personal_ai_data")
    require(deleted.get("deleted") is True, "suppression Mon IA non confirmée")

    reset = personal_ai_ok(aal2, "get_state")
    state = reset.get("state")
    require(isinstance(state, dict), "get_state après suppression: state absent")
    assert_runtime_disabled(state, "get_state après suppression")
    settings = state["settings"]
    require(settings.get("enabled") is False, "après suppression, enabled doit revenir à false")
    require(settings.get("display_name") is None, "après suppression, display_name doit être vide")
    require(settings.get("language_code") == "fr-CA", "après suppression, langue par défaut attendue")
    require(permission_map(state) == {}, "après suppression, aucune permission source ne doit subsister")

    print(
        "OK smoke Mon IA V25: TOTP/AAL2 réel, premier appareil courant fiabilisé sans privilège, "
        "runtime toujours not_configured, sources bornées à Histoire de vie/Emploi, conscience et identité client refusées, "
        "chat inexistant et suppression complète vérifiée."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
