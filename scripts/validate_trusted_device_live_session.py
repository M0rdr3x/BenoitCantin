#!/usr/bin/env python3
"""Contrat statique de deux RPC d'appareils fiables, SANS connexion à Supabase.

Candidat SQL extrait du catalogue de la production puis enrichi d'un garde
sur auth.sessions. Il ne doit jamais être une migration automatiquement lancée.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "supabase/candidate-migrations/2026-10-31_trusted_device_live_session_guard_REVIEW_ONLY.sql"
TARGETS = {
    "security_resolve_connection_challenge": (
        "p_challenge_id uuid, p_device_key text, p_decision text",
        "pg_catalog', 'public', 'private', 'auth",
    ),
    "security_set_device_trust": (
        "p_device_id uuid, p_trusted boolean, p_primary boolean DEFAULT false",
        "pg_catalog', 'public', 'auth', 'private",
    ),
}
GUARD = re.compile(
    r"if\s+v_session\s+is\s+null\s+or\s+not\s+exists\s*\("
    r"\s*select\s+1\s+from\s+auth\.sessions\s+as\s+live_session"
    r"\s+where\s+live_session\.id\s*=\s*v_session"
    r"\s+and\s+live_session\.user_id\s*=\s*v_user"
    r"\s+and\s+\(live_session\.not_after\s+is\s+null\s+or"
    r"\s+live_session\.not_after\s*>\s*now\(\)\)"
    r"\s*\)\s*then\s*raise\s+exception\s*'ACTIVE_SESSION_REQUIRED'"
    r"\s+using\s+errcode\s*=\s*'42501';\s*end\s+if;",
    flags=re.IGNORECASE,
)


def code_only(source: str) -> str:
    """Ignorer les commentaires SQL; ne pas accepter une preuve dans --."""
    return "\n".join(line.split("--", 1)[0] for line in source.splitlines())


def errors(source: str) -> list[str]:
    sql = code_only(source)
    faults: list[str] = []

    if not re.search(r"(?im)^\s*begin\s*;\s*$", sql) or not re.search(r"(?im)^\s*commit\s*;\s*$", sql):
        faults.append("Transaction de revue manquante")

    parts = re.split(
        r"(?im)^CREATE\s+OR\s+REPLACE\s+FUNCTION\s+sinjira_security_internal\.",
        sql,
    )
    if len(parts) != 3:
        return faults + ["Le candidat doit contenir exactement deux fonctions internes"]

    preface, first, second = parts
    if re.search(r"(?im)\b(create\s+table|alter\s+table|drop\s+|grant\s+|revoke\s+|truncate\s+|set\s+role)\b", preface):
        faults.append("Instruction de privilèges extérieure interdite")
    if sql.lower().count("create or replace function") != 2:
        faults.append("Modification SQL additionnelle interdite")
    if len(re.findall(r"\$function\$", sql, re.I)) != 4:
        faults.append("Délimiteurs des fonctions invalides")
    if not re.search(r"(?is)\$function\$\s*;\s*commit\s*;\s*\Z", second):
        faults.append("SQL inattendu après la deuxième fonction")

    for name, body in zip(TARGETS, (first, second)):
        signature, path_fragment = TARGETS[name]
        compact = re.sub(r"\s+", " ", body)
        lower = compact.lower()
        if not body.startswith(name + "("):
            faults.append("Nom de fonction non conforme")
        if not re.search(r"(?is)^\w+\s*\(\s*" + re.escape(signature) + r"\s*\)", compact):
            faults.append("Signature d'origine modifiée : " + name)
        if "returns jsonb" not in lower or "language plpgsql" not in lower or "security definer" not in lower:
            faults.append("Contrat SECURITY DEFINER modifié : " + name)
        if path_fragment.lower() not in lower:
            faults.append("search_path de production modifié : " + name)

        matched = GUARD.search(body)
        if matched is None or len(GUARD.findall(body)) != 1:
            faults.append("Garde auth.sessions manquant ou modifié : " + name)
            continue
        # En toute circonstance, refuser une session absente/expirée avant
        # la lecture des appareils et le moindre DML.
        guard_pos = matched.start()
        first_device_select = body.lower().find("select * into v_")
        first_update = re.search(r"(?im)^\s*(update|insert|delete)\s+", body)
        mfa = body.lower().find("perform private.security_require_aal2_if_available")
        if first_device_select >= 0 and guard_pos > first_device_select:
            faults.append("Garde appliqué après lecture des appareils : " + name)
        if first_update is not None and guard_pos > first_update.start():
            faults.append("Garde appliqué après mutation des appareils : " + name)
        if mfa >= 0 and guard_pos > mfa:
            faults.append("Garde appliqué trop tard pour les opérations MFA : " + name)

        required = [
            "auth.uid()", "auth.jwt()->>'session_id'",
            "perform private.security_require_aal2_if_available",
            "where id=p_device_id and user_id=v_user" if name=="security_set_device_trust"
            else "where user_id=v_user",
        ]
        for invariant in required:
            if invariant not in lower:
                faults.append("Contrôle historique manquant : " + name)

        if name == "security_resolve_connection_challenge":
            for requirement in (
                "and device_key=p_device_key",
                "and is_trusted",
                "and revoked_at is null",
                "and last_session_id=v_session",
                "if v_device.id=v_ch.request_device_id then",
                "for update;",
                "if v_ch.status<>'pending' or v_ch.expires_at<=now() then",
            ):
                if requirement not in lower:
                    faults.append("Protection des challenges altérée")
        else:
            for requirement in (
                "if p_trusted and coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then",
                "and user_id=v_user and revoked_at is null",
                "v_row.last_session_id is distinct from v_session",
                "if v_has_other_trusted then",
                "if not v_recent_approved then",
            ):
                if requirement not in lower:
                    faults.append("Protection des appareils fiables altérée")

    # Aucune instruction additionnelle à la place des contrats internes.
    for match in re.finditer(r"(?im)^\s*(?:grant|revoke|drop|alter\s+table|truncate|create\s+table)\b", sql):
        faults.append("DDL ou permission non autorisée à la ligne " + str(sql.count("\n", 0, match.start()) + 1))
    return sorted(set(faults))


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    try:
        report=errors(CANDIDATE.read_text("utf-8"))
    except (OSError, UnicodeError):
        report=["Candidat SQL absent ou illisible"]
    if report:
        print("NO_GO: " + "; ".join(report))
        return 1
    print("PASS: deux fonctions SQL privilégiées vérifiées, session Supabase active obligatoire; aucun déploiement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
