#!/usr/bin/env python3
"""Test d'intégration HTTP/GoTrue/PostgREST sur Supabase LOCAL UNIQUEMENT.

Installe le candidat SQL dans une base éphémère locale (jamais une migration),
obtient un vrai JWT signé, vérifie une opération autorisée, révoque réellement
la session par sign-out, puis prouve que huit RPC publiques refusent le JWT
cryptographiquement valide restant. Aucune production, aucun compte réel.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import uuid

from smoke_sensitive_aal2_local import (
    API_URL, ANON_KEY, enroll_totp, jwt_claims, request, require,
    sign_in, signup, verify_totp,
)
from smoke_device_challenge_continuity_local import (
    register_device, trust_first_device,
)
from validate_revoked_session_rpc_candidate import SQL, inspect

LOCAL_API_URLS = {"http://127.0.0.1:54321", "http://localhost:54321"}
LOCAL_HOST = "127.0.0.1"
LOCAL_PG_PORT = "54322"
EXPLICIT_OPT_IN = "SINJIRA_LOCAL_SESSION_CANDIDATE_TEST"
INVALID_DEVICE = "ffffffff-ffff-4fff-8fff-ffffffffffff"
RPCS = (
    ("security_after_password_recovery", {"p_device_key": None}),
    ("security_compromise_account", {"p_current_device_key": None}),
    ("security_report_lost_device", {"p_device_id": INVALID_DEVICE}),
    ("security_resolve_connection_challenge", {
        "p_challenge_id": INVALID_DEVICE,
        "p_device_key": "local-fixture-key",
        "p_decision": "approved",
    }),
    ("security_resolve_connection_challenge_mfa", {
        "p_challenge_id": INVALID_DEVICE,
        "p_device_key": "local-fixture-key",
    }),
    ("security_revoke_device", {"p_device_id": INVALID_DEVICE}),
    ("security_set_device_trust", {
        "p_device_id": INVALID_DEVICE, "p_trusted": True, "p_primary": False,
    }),
    ("security_update_settings", {"p_notify_high_risk": False}),
)


def guard_local(api_url: str, opt_in: str, ci: str) -> None:
    if api_url not in LOCAL_API_URLS:
        raise ValueError("REFUS : API Supabase non locale, port 54321 obligatoire")
    if ci != "true" or opt_in != "1":
        raise ValueError("REFUS : exécution réservée à GitHub Actions avec opt-in explicite")


def local_sql_candidate() -> str:
    sql = SQL.read_text(encoding="utf-8", errors="strict")
    errors = inspect(sql)
    if errors:
        raise ValueError("Candidat SQL invalide : " + "; ".join(errors))
    # Le fichier de PR demeure obligatoirement BEGIN ... ROLLBACK.
    # La substitution COMMIT n'a lieu que dans la mémoire du test local.
    if not re.search(r"(?i)\bROLLBACK\s*;\s*$", sql):
        raise ValueError("Fin ROLLBACK du candidat absente")
    return re.sub(r"(?i)\bROLLBACK\s*;\s*$",
                  "COMMIT;\n", sql, count=1)


def psql(sql: str, *, tuples_only: bool = False) -> str:
    command = [
        "psql", "-X", "-w", "-v", "ON_ERROR_STOP=1",
        "-h", LOCAL_HOST, "-p", LOCAL_PG_PORT,
        "-U", "postgres", "-d", "postgres",
    ]
    if tuples_only:
        command.extend(("-t", "-A"))
    # Aucun PGHOST / DATABASE_URL / PGSERVICE externe n'est hérité.
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PGPASSWORD": "postgres",  # mot de passe de DEV local Supabase CLI
        "PGCONNECT_TIMEOUT": "5",
    }
    result = subprocess.run(
        command, input=sql, capture_output=True, text=True,
        env=env, check=False, timeout=45,
    )
    if result.returncode != 0:
        # Ne jamais imprimer une requête entière ni d'éventuelles valeurs Auth.
        raise RuntimeError("psql LOCAL : erreur lors d'une vérification de test")
    return result.stdout.strip()


def session_count(session_id: str) -> int:
    # Un UUID strict, normalisé avant composition SQL, interdit toute injection.
    safe_id = str(uuid.UUID(session_id))
    out = psql(
        "SELECT count(*) FROM auth.sessions "
        f"WHERE id = '{safe_id}'::uuid;\n",
        tuples_only=True,
    )
    if out not in ("0", "1"):
        raise AssertionError("Résultat de recherche de session locale inattendu")
    return int(out)


def rpc(name: str, token: str, params: dict):
    return request("POST", "/rest/v1/rpc/" + name, token=token, body=params)


def active_rpc(token: str) -> None:
    # Contrôle positif essentiel : ne pas accepter un correctif qui bloque tout.
    result = rpc("security_update_settings", token, {
        "p_notify_high_risk": True,
    })
    require(200 <= result.status < 300,
            f"une session AAL2 ACTIVE doit modifier ses paramètres, HTTP {result.status}")
    require(isinstance(result.body, dict) and result.body.get("ok") is True,
            "la RPC active ne renvoie pas de confirmation valide")


def revoked_rpcs(token: str) -> None:
    for name, payload in RPCS:
        response = rpc(name, token, payload)
        code = response.body.get("code") if isinstance(response.body, dict) else None
        message = response.body.get("message") if isinstance(response.body, dict) else None
        require(response.status in (400, 401, 403),
                f"{name}: refus HTTP attendu après sign-out, reçu {response.status}")
        require(code == "42501" and message == "AUTH_SESSION_INVALID",
                f"{name}: garde SQL de session absent (code={code})")
        # Aucun appel ne doit donner l'impression d'une mutation réussie.
    print("OK : huit endpoints PostgREST refusent le JWT révoqué avec 42501.")


def self_test() -> None:
    for url in ("https://gpvivleexywljowcqkru.supabase.co",
                "http://localhost:54322", "http://127.0.0.1:54322",
                "http://localhost.evil.invalid:54321", ""):
        try:
            guard_local(url, "1", "true")
        except ValueError:
            pass
        else:
            raise AssertionError("Une API distante ou un port incorrect a été accepté")
    for opt_in, ci in (("", "true"), ("1", ""), ("0", "true")):
        try:
            guard_local("http://127.0.0.1:54321", opt_in, ci)
        except ValueError:
            pass
        else:
            raise AssertionError("Un appel non autorisé a été accepté")
    guard_local("http://127.0.0.1:54321", "1", "true")
    assert local_sql_candidate().endswith("COMMIT;\n")
    assert SQL.read_text(encoding="utf-8").rstrip().endswith("ROLLBACK;")
    assert len(RPCS) == 8
    print("OK : refus prod/réseau/port externes, source SQL inchangée et huit endpoints.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    guard_local(API_URL, os.environ.get(EXPLICIT_OPT_IN, ""), os.environ.get("CI", ""))
    require(bool(ANON_KEY), "clé ANON locale absente")
    # Verrouillage supplémentaire : l'hôte/port DB sont codés en dur.
    require(psql("SELECT current_database();\n", tuples_only=True) == "postgres",
            "base locale inattendue")

    # La DDL candidate est appliquée et COMMITÉE UNIQUEMENT dans ce conteneur
    # Supabase local jetable, pour rendre les fonctions visibles aux requêtes HTTP.
    psql(local_sql_candidate())
    print("OK : fonctions candidates activées dans Supabase LOCAL éphémère.")

    aal1, user_id, email, password = signup()
    factor_id, secret = enroll_totp(aal1)
    aal2 = verify_totp(aal1, factor_id, secret)
    jwt = jwt_claims(aal2)
    sid = str(uuid.UUID(str(jwt.get("session_id", ""))))
    require(jwt.get("sub") == user_id and jwt.get("aal") == "aal2",
            "JWT signé ne correspond pas à l'utilisateur AAL2")
    require(session_count(sid) == 1,
            "la session Auth réelle doit être présente avant révocation")

    device = register_device(aal2, "sinjira-local-revoked-session-fixture-001",
                             "Appareil de test local révoqué")
    trust_first_device(aal2, str(device["id"]))
    active_rpc(aal2)
    print("OK : JWT réel AAL2, appareil enregistré et RPC autorisée AVANT révocation.")

    # Le vrai endpoint GoTrue met fin à la session du JWT, sans le supprimer
    # de la mémoire du test. Sa signature reste valide jusqu'à expiration.
    sign_out = request("POST", "/auth/v1/logout?scope=local",
                       token=aal2, body={})
    require(sign_out.status in (200, 204),
            f"sign-out Supabase local refusé, HTTP {sign_out.status}")
    require(session_count(sid) == 0,
            "la session doit disparaître de auth.sessions après sign-out")

    revoked_rpcs(aal2)

    # Une autre session nouvellement émise doit rester utilisable (fail-open
    # contrôlé pour utilisateur légitime seulement, pas pour session révoquée).
    new_aal1 = sign_in(email, password)
    new_aal2 = verify_totp(new_aal1, factor_id, secret)
    new_sid = str(uuid.UUID(str(jwt_claims(new_aal2).get("session_id", ""))))
    require(new_sid != sid and session_count(new_sid) == 1,
            "une nouvelle session légitime doit avoir un session_id actif distinct")
    active_rpc(new_aal2)
    print("OK : reconnexion AAL2 valide après révocation, sans contournement.")
    print("OK HTTP : session GoTrue réellement supprimée et huit RPC bloquées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
