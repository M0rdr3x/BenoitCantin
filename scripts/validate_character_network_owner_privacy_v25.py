#!/usr/bin/env python3
"""Valide que Réseau personnage délègue l'identité propriétaire au serveur."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "assets" / "js" / "sinjira-community-character.js"
DOC = ROOT / "CHARACTER_NETWORK_OWNER_PRIVACY_V25.md"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-character-network-owner-privacy-v25.yml"
OWNER_ROLE_GUARD = ROOT / "scripts" / "validate_owner_role_invoker.py"
OWNER_CHARACTER_GUARD = ROOT / "scripts" / "validate_owner_character_rpc_v24_5_20.py"
IDENTITY_GUARD = ROOT / "scripts" / "validate_character_identity_rls.py"
SOCIAL_RPC_GUARD = ROOT / "scripts" / "validate_social_user_rpc_v24_5_15.py"
SECRET_GUARD = ROOT / "scripts" / "validate_no_committed_secrets.py"


def fail(message: str) -> None:
    print(f"ECHEC confidentialité Réseau personnage V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (
        RUNTIME,
        DOC,
        WORKFLOW,
        OWNER_ROLE_GUARD,
        OWNER_CHARACTER_GUARD,
        IDENTITY_GUARD,
        SOCIAL_RPC_GUARD,
        SECRET_GUARD,
    ):
        require(path.is_file(), f"fichier manquant: {path.relative_to(ROOT)}")

    runtime = RUNTIME.read_text("utf-8")
    folded = runtime.casefold()

    for marker in (
        "async function isCurrentUserOwner()",
        "rpc('is_sinjira_owner',{p_user_id:user.id})",
        "return data===true;",
        "const owner=await isCurrentUserOwner();",
        "rpc('ensure_sinjira_owner_character')",
        "if(!me&&owner){repair=await tryOwnerRepair();me=await getMyCharacter();}",
    ):
        require(marker in runtime, f"contrat runtime manquant: {marker}")

    for forbidden in (
        "owner_login_email",
        "user.email",
        "user?.email",
        "session.user.email",
        "auth.user.email",
    ):
        require(forbidden not in folded, f"identité réelle interdite dans le runtime: {forbidden}")

    email_literal = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
    require(not email_literal.search(runtime), "adresse courriel littérale interdite dans le runtime public")

    owner_check = runtime.index("const owner=await isCurrentUserOwner();")
    repair_gate = runtime.index("if(!me&&owner){repair=await tryOwnerRepair();me=await getMyCharacter();}")
    require(owner_check < repair_gate, "la décision serveur du rôle doit précéder la réparation propriétaire")

    doc = DOC.read_text("utf-8")
    doc_folded = doc.casefold()
    for marker in (
        "L’HUMAIN AVANT TOUT",
        "Protéger sans surveiller",
        "is_sinjira_owner",
        "ensure_sinjira_owner_character",
        "aucune adresse courriel",
        "auth.uid()",
        "migrations historiques",
        "aucune écriture Supabase",
    ):
        require(marker.casefold() in doc_folded, f"documentation incomplète: {marker}")

    workflow = WORKFLOW.read_text("utf-8")
    for marker in (
        "python3 scripts/validate_character_network_owner_privacy_v25.py",
        "python3 scripts/validate_owner_role_invoker.py",
        "python3 scripts/validate_owner_character_rpc_v24_5_20.py",
        "python3 scripts/validate_character_identity_rls.py",
        "python3 scripts/validate_social_user_rpc_v24_5_15.py",
        "python3 scripts/validate_no_committed_secrets.py",
    ):
        require(marker in workflow, f"preuve CI manquante: {marker}")

    for forbidden in (
        "environment: production",
        "SUPABASE_ACCESS_TOKEN",
        "${{ secrets.",
        "supabase db",
        "supabase migration",
        "supabase link",
    ):
        require(forbidden not in workflow, f"capacité production interdite dans le workflow: {forbidden}")

    print(
        "OK confidentialité Réseau personnage V25: le navigateur demande le rôle au serveur, "
        "aucune adresse courriel ne décide du privilège et la réparation reste bornée côté serveur."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
