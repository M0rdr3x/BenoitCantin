#!/usr/bin/env python3
"""Audit de sécurité hors réseau des deux SECURITY DEFINER privés SINJIRA.

Le candidat SQL commence par BEGIN et se termine par ROLLBACK; il ne doit pas
être exécuté en production. L'option --render-tests crée UNIQUEMENT une fixture
pgTAP locale éphémère contenant les identités synthétiques de test.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "security/candidates/sinjira_private_definer_identity_staging.sql"
ASSERTIONS = ROOT / "security/candidates/sinjira_private_definer_identity_assertions.sql"
TEST_OUTPUT = ROOT / "supabase/tests/__sinjira_private_definer_identity_generated.test.sql"

# Empreintes des fonctions déployées, observées en lecture seule le 2026-11-21.
# Avant une migration de promotion, comparer sur la production via
# pg_get_functiondef + btrim + extensions.digest, puis revue du delta complet.
BASELINE_SHA256 = {
    "is_sinjira_admin": "5e3df1425976db0252e8c3b544929f60038d02581f4226d684819c7c4a347c06",
    "project_access_rank": "efc5da4d75817740e4e3ab12d84124fd4638c32d0d4df75b8496d07bfa08d4a3",
}

ADMIN_SIG = "CREATE OR REPLACE FUNCTION private.is_sinjira_admin(p_user_id uuid DEFAULT auth.uid())"
RANK_SIG = "CREATE OR REPLACE FUNCTION private.project_access_rank(p_project_id uuid, p_user_id uuid DEFAULT auth.uid())"
CLIENT_BOUNDARY = "AND p_user_id IS DISTINCT FROM (SELECT auth.uid()) THEN 0"
SERVER_ROLE = "coalesce(auth.jwt()->>'role','') = 'service_role'"
SERVER_ROLE_NEG = "coalesce(auth.jwt()->>'role','') <> 'service_role'"
TIER_RANKS = (
    "THEN 100", "THEN 30", "THEN 20", "THEN 10", "THEN 1", "ELSE 0",
)
ALLOWED = (
    "private.is_sinjira_admin", "private.project_access_rank",
)


def inspect(src: str) -> list[str]:
    errors: list[str] = []
    code = re.sub(r"(?m)^\s*--[^\n]*", "", src).strip()
    if not re.match(r"(?i)^BEGIN\s*;", code):
        errors.append("Transaction BEGIN absente")
    if not re.search(r"(?i)ROLLBACK\s*;\s*$", code):
        errors.append("ROLLBACK final obligatoire")
    if len(re.findall(r"(?im)^\s*ROLLBACK\s*;", code)) != 1:
        errors.append("ROLLBACK unique attendu")
    if re.search(r"(?im)^\s*(?:COMMIT|GRANT|REVOKE|DROP|TRUNCATE|INSERT|UPDATE|DELETE|ALTER)\b", code):
        errors.append("DDL/privilege/mutation hors candidat interdite")
    if len(re.findall(r"(?im)^\s*CREATE OR REPLACE FUNCTION\b", code)) != 2:
        errors.append("Exactement deux fonctions de sécurité attendues")

    pieces = code.split("CREATE OR REPLACE FUNCTION ")
    if len(pieces) != 3:
        return errors + ["Découpage des deux définitions impossible"]
    functions = [piece.split("$function$;", 1)[0] for piece in pieces[1:]]
    if not pieces[1].startswith(ADMIN_SIG.removeprefix("CREATE OR REPLACE FUNCTION ")):
        errors.append("Signature administrateur altérée")
    if not pieces[2].startswith(RANK_SIG.removeprefix("CREATE OR REPLACE FUNCTION ")):
        errors.append("Signature rang projet altérée")
    for name, fn in zip(ALLOWED, functions):
        if "STABLE SECURITY DEFINER" not in fn or "LANGUAGE sql" not in fn:
            errors.append(f"Contrat de privilège/volatilité modifié : {name}")
        if "SET search_path TO 'pg_catalog'" not in fn:
            errors.append(f"search_path immuable absent : {name}")
        if fn.count("$function$") != 1:
            errors.append(f"Début de délimiteur incorrect : {name}")
        if "p_user_id" not in fn or "auth.uid()" not in fn:
            errors.append(f"Liaison de l'identité absente : {name}")
        if "public." not in fn:
            errors.append(f"Consultation SQL qualifiée absente : {name}")

    admin, rank = functions
    if "p_user_id IS NOT NULL" not in admin:
        errors.append("L'identité administrateur n'est pas non-nulle")
    if SERVER_ROLE not in admin or "OR p_user_id = (SELECT auth.uid())" not in admin:
        errors.append("L'identité admin n'est pas liée au JWT")
    if "public.internal_admin_users" not in admin:
        errors.append("Table admin originale modifiée")
    if "WHERE a.user_id=p_user_id" not in admin:
        errors.append("Correspondance admin historique absente")
    if SERVER_ROLE_NEG not in rank or CLIENT_BOUNDARY not in rank:
        errors.append("Filtre anti-sondage du rang projet absent")
    if "WHEN private.is_sinjira_admin(p_user_id) THEN 100" not in rank:
        errors.append("Statut administrateur historique altéré")
    for fragment in TIER_RANKS:
        if fragment not in rank:
            errors.append("Classement historique altéré : " + fragment)
    for fragment in (
        "public.project_access pa", "pa.project_id=p_project_id",
        "pa.user_id=p_user_id", "pa.expires_at IS NULL OR pa.expires_at>now()",
        "pa.access_level='tester'", "pa.access_level='player'",
        "public.projects p", "p.id=p_project_id",
        "p.visibility IN('public','account')", "p.visibility='public'",
    ):
        expected = 2 if fragment in (
            "public.project_access pa",
            "pa.project_id=p_project_id",
            "pa.user_id=p_user_id",
            "pa.expires_at IS NULL OR pa.expires_at>now()",
            "public.projects p",
            "p.id=p_project_id",
        ) else 1
        if rank.count(fragment) != expected:
            errors.append("Filtre historique de projet altéré : " + fragment)
    if "REVOKE" in code or "GRANT" in code:
        errors.append("Modification de privilèges non autorisée")
    if code.count("$function$;") != 2:
        errors.append("Délimiteurs terminaux incorrects")
    return errors


def source() -> str:
    if not SQL.is_file() or SQL.is_symlink() or SQL.stat().st_size > 50_000:
        raise ValueError("Candidat SQL absent, trop volumineux ou lien symbolique")
    return SQL.read_text(encoding="utf-8", errors="strict")


def render() -> str:
    code = source()
    errors = inspect(code)
    if errors:
        raise ValueError("Candidat SQL non conforme : " + "; ".join(errors))
    assertions = ASSERTIONS.read_text(encoding="utf-8", errors="strict").strip()
    # Les commentaires de contexte ne sont pas des instructions pgTAP.
    clean_assertions = re.sub(r"(?m)^\s*--[^\n]*", "", assertions).strip()
    if not clean_assertions.startswith("CREATE EXTENSION IF NOT EXISTS pgtap"):
        raise ValueError("Assertions pgTAP manquantes")
    if not re.search(r"(?im)^SELECT \* FROM finish\(\);$", assertions):
        raise ValueError("Assertions pgTAP non terminées")
    if re.search(r"(?im)^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", assertions):
        raise ValueError("Les assertions ne doivent pas manipuler la transaction")
    prelude = re.sub(r"(?im)^ROLLBACK\s*;\s*$", "", code).rstrip()
    return prelude + "\n\n" + assertions + "\n\nROLLBACK;\n"


def self_test() -> None:
    code = source()
    if inspect(code):
        raise AssertionError("Source de référence non conforme : " + "; ".join(inspect(code)))
    mutants = (
        ("refus du tiers retiré", CLIENT_BOUNDARY, "THEN 0"),
        ("rôle serveur autorisé partout", SERVER_ROLE_NEG, "true"),
        ("lien admin à l'appelant retiré", "OR p_user_id = (SELECT auth.uid())", "OR true"),
        ("role admin falsifié", SERVER_ROLE, "coalesce(auth.jwt()->>'role','') = 'authenticated'"),
        ("identité admin nulle", "p_user_id IS NOT NULL", "true"),
        ("table admin remplacée", "public.internal_admin_users", "public.projects"),
        ("testeur promu", "THEN 30", "THEN 100"),
        ("RLS projet contournée", "pa.project_id=p_project_id", "true"),
        ("expiration du privilège ignorée", "pa.expires_at IS NULL OR pa.expires_at>now()", "true"),
        ("rôle propriétaire changé", "pa.user_id=p_user_id", "pa.user_id IS NOT NULL"),
        ("visibilité public élargie", "p.visibility='public'", "true"),
        ("search_path non fiable", "SET search_path TO 'pg_catalog'", "SET search_path TO 'public'"),
        ("definer supprimé", "STABLE SECURITY DEFINER", "STABLE SECURITY INVOKER"),
        ("rollback supprimé", "ROLLBACK;", ""),
        ("transaction validée", "ROLLBACK;", "COMMIT;"),
        ("droits élargis", "ROLLBACK;", "GRANT ALL ON ALL FUNCTIONS IN SCHEMA private TO PUBLIC;\nROLLBACK;"),
    )
    for title, original, replacement in mutants:
        if original not in code:
            raise AssertionError("Fixture de mutation absente : " + title)
        altered = code.replace(original, replacement, 1)
        if not inspect(altered):
            raise AssertionError("Mutation dangereuse acceptée : " + title)
    fixture = render()
    if fixture.count("ROLLBACK;") < 1 or not fixture.rstrip().endswith("ROLLBACK;"):
        raise AssertionError("La fixture pgTAP doit annuler toute modification")
    if "SELECT plan(22);" not in fixture:
        raise AssertionError("Plan pgTAP absent")
    if "INSERT INTO auth.users" not in fixture:
        raise AssertionError("Identités fictives non injectées")
    print(f"PASS : {len(mutants)} mutations de privilèges/identités rejetées; candidat ROLLBACK-only.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--render-tests", action="store_true")
    args = p.parse_args()
    try:
        if args.self_test:
            self_test()
        elif args.render_tests:
            if TEST_OUTPUT.is_symlink():
                raise ValueError("Sortie vers lien symbolique interdite")
            TEST_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            TEST_OUTPUT.write_text(render(), encoding="utf-8")
            print("PASS : fixture transactionnelle pgTAP générée pour Supabase local.")
        else:
            faults = inspect(source())
            if faults:
                for fault in faults:
                    print("ECHEC : " + fault)
                return 1
            print("PASS : deux SECURITY DEFINER liés au demandeur; aucune migration exécutable.")
    except (OSError, UnicodeError, ValueError, AssertionError) as exc:
        print("ECHEC : " + str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
