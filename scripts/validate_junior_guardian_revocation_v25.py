#!/usr/bin/env python3
"""Valide le correctif fail-closed de révocation tuteur Junior V25."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql"
CASCADE_MIG = ROOT / "supabase/migrations/20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql"
TEST = ROOT / "supabase/tests/junior_guardian_revocation_v25.test.sql"
WORKFLOW = ROOT / ".github/workflows/sinjira-junior-guardian-revocation-v25.yml"


def fail(message: str) -> None:
    raise ValueError(message)


def segment(text: str, start: str, end: str | None = None) -> str:
    if start not in text:
        fail(f"marqueur absent: {start}")
    part = text.split(start, 1)[1]
    if end is not None:
        if end not in part:
            fail(f"marqueur de fin absent: {end}")
        part = part.split(end, 1)[0]
    return part


def validate(migration: str, cascade: str, test: str, workflow: str) -> None:
    enabled = segment(
        migration,
        "create or replace function private.sinjira_junior_community_enabled(p_user_id uuid)",
        "create or replace function public.guardian_junior_community_children()",
    )
    children = segment(
        migration,
        "create or replace function public.guardian_junior_community_children()",
        "comment on function private.sinjira_junior_community_enabled(uuid)",
    )

    if "g.status='verified'" not in enabled or "g.revoked_at is null" not in enabled:
        fail("activation Junior: lien tuteur vérifié ET non révoqué requis")
    if "c.revoked_at is null" not in enabled:
        fail("activation Junior: consentement Junior non révoqué requis")
    if "g.status='verified'" not in children or "g.revoked_at is null" not in children:
        fail("liste parent Junior: lien tuteur vérifié ET non révoqué requis")

    cascade_compact = "".join(cascade.lower().split())
    if "createorreplacefunctionprivate.sinjira_revoke_junior_consent_on_guardian_link()" not in cascade_compact:
        fail("cascade Junior: fonction de révocation durable absente")
    if "afterupdateofstatus,revoked_atordeleteonpublic.guardian_links" not in cascade_compact:
        fail("cascade Junior: trigger UPDATE/DELETE sur guardian_links absent")
    if "updatepublic.junior_community_guardian_consentssetrevoked_at=coalesce(revoked_at,now())" not in cascade_compact:
        fail("cascade Junior: le consentement Junior actif n'est pas révoqué durablement")
    if "tg_op='delete'" not in cascade_compact:
        fail("cascade Junior: suppression d'un lien tuteur non couverte")

    required_test = (
        "select plan(17);",
        "junior-revocation-guardian-a@example.test",
        "junior-revocation-guardian-b@example.test",
        "set revoked_at=now()",
        "not public.sinjira_junior_community_enabled()",
        "GUARDIAN_ACCESS_REQUIRED",
        "jsonb_array_elements(public.guardian_junior_community_children())",
        "(item->>'enabled')::boolean=false",
        "révoquer le lien A révoque durablement son consentement Junior",
        "'child_pending'",
        "redeem_guardian_signup_invite('YOUTH-RECONSENT1')",
        "l ancien consentement Junior de A reste révoqué",
        "une nouvelle activation Junior explicite est nécessaire",
    )
    for marker in required_test:
        if marker not in test:
            fail(f"preuve pgTAP multi-tuteur manquante: {marker}")

    forbidden_workflow = (
        "pull_request_target",
        "secrets.",
        "supabase link",
        "supabase db push",
        "supabase functions deploy",
        "continue-on-error: true",
    )
    for marker in forbidden_workflow:
        if marker in workflow:
            fail(f"workflow révocation Junior: capacité interdite détectée: {marker}")

    required_workflow = (
        "permissions:\n  contents: read",
        "persist-credentials: false",
        "ubuntu-24.04",
        "python-version: '3.12.14'",
        "version: 2.111.0",
        "supabase db reset",
        "supabase test db supabase/tests/child_community_v25.test.sql",
        "supabase test db supabase/tests/junior_guardian_revocation_v25.test.sql",
    )
    for marker in required_workflow:
        if marker not in workflow:
            fail(f"workflow révocation Junior: garde manquante: {marker}")


def self_test(migration: str, cascade: str, test: str, workflow: str) -> None:
    validate(migration, cascade, test, workflow)
    mutations = {
        "revoked_at activation retiré": (migration.replace("        and g.revoked_at is null\n", "", 1), cascade, test, workflow),
        "revoked_at liste parent retiré": (migration.rsplit("    and g.revoked_at is null\n", 1)[0] + migration.rsplit("    and g.revoked_at is null\n", 1)[1], cascade, test, workflow),
        "cascade consentement retirée": (migration, cascade.replace("  update public.junior_community_guardian_consents\n", "  -- update retiré\n", 1), test, workflow),
        "preuve second tuteur retirée": (migration, cascade, test.replace("junior-revocation-guardian-b@example.test", "guardian-b-missing"), workflow),
        "secret ajouté au workflow": (migration, cascade, test, workflow + "\n# secrets.TEST\n"),
    }
    for label, values in mutations.items():
        try:
            validate(*values)
        except ValueError:
            continue
        fail(f"auto-test non détecté: {label}")
    print(f"OK révocation Junior: {len(mutations)}/{len(mutations)} dérives critiques détectées")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    migration = MIGRATION.read_text(encoding="utf-8")
    cascade = CASCADE_MIG.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    if args.self_test:
        self_test(migration, cascade, test, workflow)
        return
    validate(migration, cascade, test, workflow)
    print("OK révocation Junior V25: lien tuteur, consentement Junior et réactivation de supervision restent fail-closed; nouvelle activation explicite prouvée.")


if __name__ == "__main__":
    main()
