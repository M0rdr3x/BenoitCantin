#!/usr/bin/env python3
"""Valide le correctif fail-closed de révocation tuteur Junior V25."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260919010000_sinjira_v25_junior_guardian_revocation_hardening.sql"
CASCADE_MIG = ROOT / "supabase/migrations/20260919020000_sinjira_v25_junior_consent_revocation_cascade.sql"
ENABLE_AAL2_MIG = ROOT / "supabase/migrations/20260919040000_sinjira_v25_junior_enable_aal2.sql"
SUMMARY_AAL2_MIG = ROOT / "supabase/migrations/20260919073000_sinjira_v25_junior_guardian_summary_aal2.sql"
ALIAS_PRIVACY_MIG = ROOT / "supabase/migrations/20260919083000_sinjira_v25_guardian_junior_alias_privacy.sql"
RELATIONS_JS = ROOT / "assets/js/v24-relations.js"
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


def validate(migration: str, cascade: str, enable_aal2: str, summary_aal2: str, alias_privacy: str, relations_js: str, test: str, workflow: str) -> None:
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

    enable_compact = "".join(enable_aal2.lower().split())
    if "ifv_enabledandcoalesce(auth.jwt()->>'aal','aal1')<>'aal2'" not in enable_compact:
        fail("activation Junior: AAL2 serveur obligatoire absent")
    if "mfa_aal2_required" not in enable_compact:
        fail("activation Junior: erreur MFA_AAL2_REQUIRED absente")
    if "ifv_enabled" not in enable_compact or "revoked_at=casewhenv_enabledthennullelsenow()end" not in enable_compact:
        fail("activation Junior: activation/désactivation fail-safe non conservée")
    if (
        "frompublic.guardian_linksgwhereg.guardian_user_id=uidandg.minor_user_id=p_child_user_idandg.status='verified'andg.revoked_atisnullforupdate"
        not in enable_compact
        or "ifnotfoundthenraiseexception'guardian_access_required'" not in enable_compact
    ):
        fail("activation Junior: lien tuteur non sérialisé avant écriture du consentement")

    summary_compact = "".join(summary_aal2.lower().split())
    if "createorreplacefunctionpublic.junior_guardian_summary(p_child_user_iduuid)" not in summary_compact:
        fail("résumé Junior: migration AAL2/minimisation absente")
    if "coalesce(auth.jwt()->>'aal','aal1')<>'aal2'" not in summary_compact or "mfa_aal2_required" not in summary_compact:
        fail("résumé Junior: AAL2 serveur obligatoire absent")
    if "'last_activity_date'" not in summary_compact or "'last_activity_at'" in summary_compact:
        fail("résumé Junior: dernière activité non réduite à la date")
    if "content_visible_to_guardian',false" not in summary_compact or "private_messages_available',false" not in summary_compact:
        fail("résumé Junior: garde sans contenu/message privé perdue")

    alias_compact = "".join(alias_privacy.lower().split())
    if "createorreplacefunctionpublic.guardian_junior_community_children()" not in alias_compact:
        fail("liste parent Junior: migration de confidentialité alias absente")
    if "'junior_alias'" in alias_compact or "sinjira_junior_alias" in alias_compact:
        fail("liste parent Junior: alias pseudonyme encore exposé")
    if "'minor_user_id',g.minor_user_id" not in alias_compact or "'enabled',c.revoked_atisnullandc.minor_user_idisnotnull" not in alias_compact:
        fail("liste parent Junior: contrat fonctionnel enfant/état perdu")

    relations_compact = "".join(relations_js.lower().split())
    if "if(next)" not in relations_compact or "s.auth.mfa.getauthenticatorassurancelevel()" not in relations_compact:
        fail("interface Junior: vérification AAL2 avant activation absente")
    if "mfa_aal2_required" not in relations_compact:
        fail("interface Junior: refus serveur AAL2 non traité")
    if "activerlacommunautéjuniorexigeunsecondfacteur" not in relations_compact:
        fail("interface Junior: guidage vers second facteur absent")

    if "data-junior-community-summary" not in relations_compact or "junior_guardian_summary" not in relations_compact:
        fail("interface Junior: résumé de sécurité absent")
    if "lerésumédesécuritéexigeunsecondfacteur" not in relations_compact:
        fail("interface Junior: guidage AAL2 du résumé absent")
    if "summary.last_activity_date" not in relations_js or "summary.last_activity_at" in relations_js:
        fail("interface Junior: résumé utilise encore un timestamp précis")

    if "row.junior_alias" in relations_js:
        fail("interface Junior: alias pseudonyme encore affiché au tuteur")
    if "aliasjuniornonaffichéaututeur" not in relations_compact:
        fail("interface Junior: explication de confidentialité de l'alias absente")

    required_test = (
        "select plan(26);",
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
        "MFA_AAL2_REQUIRED",
        "tuteur AAL1 ne peut pas activer la Communauté Junior",
        "activation Junior sérialise le lien tuteur avant le consentement",
        "tuteur A active Junior sous AAL2 avant révocation",
        "tuteur AAL1 peut toujours désactiver Junior en voie fail-safe",
        "la désactivation AAL1 coupe immédiatement Junior pour l enfant",
        "tuteur AAL1 ne peut pas lire le résumé d activité Junior",
        "le résumé Junior ne révèle plus l heure précise de dernière activité",
        "le résumé Junior réduit la dernière activité à une date",
        "le résumé AAL2 conserve seulement le compte utile des publications",
        "la liste tuteur ne révèle jamais le pseudonyme Junior de l enfant",
        "$ select public.redeem_guardian_signup_invite('YOUTH-RECONSENT1') $",
    )
    for marker in required_test:
        if marker not in test:
            fail(f"preuve pgTAP multi-tuteur manquante: {marker}")

    test_compact = "".join(test.lower().split())
    guardian_sub = "selectset_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000001',true);"
    if test_compact.count(guardian_sub) < 4:
        fail("preuve pgTAP Junior: les quatre rétablissements explicites de auth.uid() du tuteur A sont requis")
    guardian_aal2 = "selectset_config('request.jwt.claims',jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal2')::text,true);"
    if guardian_sub + guardian_aal2 not in test_compact:
        fail("preuve pgTAP Junior: contexte tuteur AAL2 incohérent avant activation")
    reconsent_activation = (
        guardian_sub
        + guardian_aal2
        + "selectis((public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',true)->>'enabled')::boolean,true,'unenouvelleactivationjuniorexpliciteestnécessaireaprèsrétablissementdesupervision');"
    )
    if reconsent_activation not in test_compact:
        fail("preuve pgTAP Junior: auth.uid() du tuteur A non rétabli juste avant la réactivation après reconsentement")
    if guardian_sub + "selectset_config('request.jwt.claims',jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal1')::text,true);" not in test_compact:
        fail("preuve pgTAP Junior: contexte tuteur AAL1 incohérent avant désactivation fail-safe")

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


def self_test(migration: str, cascade: str, enable_aal2: str, summary_aal2: str, alias_privacy: str, relations_js: str, test: str, workflow: str) -> None:
    validate(migration, cascade, enable_aal2, summary_aal2, alias_privacy, relations_js, test, workflow)
    mutations = {
        "revoked_at activation retiré": (migration.replace("        and g.revoked_at is null\n", "", 1), cascade, enable_aal2, summary_aal2, alias_privacy, relations_js, test, workflow),
        "revoked_at liste parent retiré": (migration.rsplit("    and g.revoked_at is null\n", 1)[0] + migration.rsplit("    and g.revoked_at is null\n", 1)[1], cascade, enable_aal2, summary_aal2, alias_privacy, relations_js, test, workflow),
        "cascade consentement retirée": (migration, cascade.replace("  update public.junior_community_guardian_consents\n", "  -- update retiré\n", 1), enable_aal2, summary_aal2, alias_privacy, relations_js, test, workflow),
        "AAL2 activation retiré": (migration, cascade, enable_aal2.replace("if v_enabled and coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then", "if false then", 1), summary_aal2, alias_privacy, relations_js, test, workflow),
        "verrou activation retiré": (migration, cascade, enable_aal2.replace("  for update;\n", "  ;\n", 1), summary_aal2, alias_privacy, relations_js, test, workflow),
        "preuve second tuteur retirée": (migration, cascade, enable_aal2, summary_aal2, alias_privacy, relations_js, test.replace("junior-revocation-guardian-b@example.test", "guardian-b-missing"), workflow),
        "contexte auth.uid tuteur retiré": (migration, cascade, enable_aal2, summary_aal2, alias_privacy, relations_js, test.replace("select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000001',true);", "-- contexte tuteur retiré", 1), workflow),
        "contexte reconsent tuteur retiré": (
            migration,
            cascade,
            enable_aal2,
            summary_aal2,
            alias_privacy,
            relations_js,
            test.replace(
                "select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000001',true);\nselect set_config(\n  'request.jwt.claims',\n  jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal2')::text,\n  true\n);\nselect is(\n  (public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',true)->>'enabled')::boolean,\n  true,\n  'une nouvelle activation Junior explicite est nécessaire après rétablissement de supervision'\n);",
                "select set_config(\n  'request.jwt.claims',\n  jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal2')::text,\n  true\n);\nselect is(\n  (public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',true)->>'enabled')::boolean,\n  true,\n  'une nouvelle activation Junior explicite est nécessaire après rétablissement de supervision'\n);",
                1,
            ),
            workflow,
        ),
        "résumé AAL2 retiré": (migration, cascade, enable_aal2, summary_aal2.replace("coalesce(auth.jwt()->>'aal','aal1')<>'aal2'", "false", 1), alias_privacy, relations_js, test, workflow),
        "alias Junior réexposé": (migration, cascade, enable_aal2, summary_aal2, alias_privacy.replace("'enabled',c.revoked_at is null and c.minor_user_id is not null", "'enabled',c.revoked_at is null and c.minor_user_id is not null,'junior_alias','probe'", 1), relations_js, test, workflow),
        "secret ajouté au workflow": (migration, cascade, enable_aal2, summary_aal2, alias_privacy, relations_js, test, workflow + "\n# secrets.TEST\n"),
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
    enable_aal2 = ENABLE_AAL2_MIG.read_text(encoding="utf-8")
    summary_aal2 = SUMMARY_AAL2_MIG.read_text(encoding="utf-8")
    alias_privacy = ALIAS_PRIVACY_MIG.read_text(encoding="utf-8")
    relations_js = RELATIONS_JS.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    if args.self_test:
        self_test(migration, cascade, enable_aal2, summary_aal2, alias_privacy, relations_js, test, workflow)
        return
    validate(migration, cascade, enable_aal2, summary_aal2, alias_privacy, relations_js, test, workflow)
    print("OK Junior V25: révocation durable, activation explicite AAL2, résumé AAL2 minimisé et désactivation fail-safe AAL1 sont prouvés.")


if __name__ == "__main__":
    main()
