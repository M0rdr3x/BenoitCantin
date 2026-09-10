#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / 'scripts' / 'smoke_device_challenge_continuity_local.py'
HELPER = ROOT / 'scripts' / 'smoke_sensitive_aal2_local.py'
MIGRATION = ROOT / 'supabase' / 'migrations' / '20260905163000_sinjira_v25_device_challenge_continuity_hardening.sql'
SESSION_BINDING_MIGRATION = ROOT / 'supabase' / 'migrations' / '20260910193000_sinjira_v25_device_challenge_session_binding.sql'
BOUNDARY = ROOT / 'supabase' / 'migrations' / '20260822201257_sinjira_v24_5_10_security_rpc_boundary.sql'
PGTAP = ROOT / 'supabase' / 'tests' / 'device_challenge_continuity_v25.test.sql'
SESSION_BINDING_PGTAP = ROOT / 'supabase' / 'tests' / 'device_challenge_session_binding_v25.test.sql'
EDGE = ROOT / 'supabase' / 'functions' / 'conscience-vault' / 'index.ts'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-device-challenge-continuity-v25.yml'


def fail(message: str) -> None:
    print(f'ECHEC challenge appareils V25: {message}', file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (
        SMOKE, HELPER, MIGRATION, SESSION_BINDING_MIGRATION, BOUNDARY,
        PGTAP, SESSION_BINDING_PGTAP, EDGE, WORKFLOW,
    ):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    smoke = SMOKE.read_text('utf-8')
    helper = HELPER.read_text('utf-8')
    migration = MIGRATION.read_text('utf-8')
    session_binding_migration = SESSION_BINDING_MIGRATION.read_text('utf-8')
    boundary = BOUNDARY.read_text('utf-8')
    pgtap = PGTAP.read_text('utf-8')
    session_binding_pgtap = SESSION_BINDING_PGTAP.read_text('utf-8')
    edge = EDGE.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')

    # Le test traverse GoTrue réel et plusieurs sessions distinctes du même compte synthétique.
    require('from smoke_sensitive_aal2_local import' in smoke, 'helper AAL2 partagé absent')
    for marker in ('enroll_totp', 'verify_totp', 'sign_in', 'get("aal") == "aal2"'):
        require(marker in smoke, f'preuve Auth/TOTP manquante: {marker}')
    require('/auth/v1/factors' in helper and '/challenge' in helper and '/verify' in helper,
            'le helper doit utiliser les endpoints GoTrue réels')
    require('127.0.0.1' in helper and 'localhost' in helper, 'helper AAL2 non borné au local')
    for key in ('DEVICE_A', 'DEVICE_B', 'DEVICE_C'):
        require(key in smoke, f'appareil synthétique manquant: {key}')

    # A est le seul bootstrap de confiance; B/C sont d’abord connus mais non fiables.
    for rpc_name in ('security_register_device', 'security_set_device_trust',
                     'security_resolve_connection_challenge', 'security_resolve_connection_challenge_mfa'):
        require(rpc_name in smoke, f'RPC fonctionnelle manquante: {rpc_name}')
    require('"p_trusted": True' in smoke and '"p_primary": True' in smoke,
            'bootstrap A fiable/principal absent')
    require(smoke.count('get("is_trusted") is False') >= 2,
            'B et C doivent être prouvés non fiables avant décision')

    # Continuité : premier challenge, retry identique pending, auto-MFA refusée.
    require('"reissued"' in smoke and '"pending"' in smoke,
            'états reissued/pending du challenge non testés')
    require('retry_b_id == challenge_b' in smoke,
            'le retry doit réutiliser le même challenge pending')
    require('TRUSTED_OTHER_DEVICE_REQUIRED' in smoke,
            'l’auto-approbation MFA du Coffre doit être explicitement refusée')
    require('CURRENT_TRUSTED_DEVICE_REQUIRED' in smoke,
            'une clé d’un autre appareil hors session courante doit être refusée')
    require('DEVICE_A, "approved"' in smoke and 'DEVICE_A, "denied"' in smoke,
            'A doit réellement approuver B puis refuser C')
    require('resolved_device_id' in smoke and 'request_device_id' in smoke,
            'identités des appareils demandeur/résolveur non vérifiées')
    require('SECURITY_BLOCKED' in smoke and 'challenge_id") in (None, "")' in smoke,
            'C révoqué doit être bloqué sans réémission de challenge')
    require('"device_key" not in' in smoke and '"last_session_id" not in' in smoke,
            'le smoke doit vérifier la non-exposition des secrets appareil')

    # Non-rejeu session-aware : B1 est approuvé, puis B2 réutilise la même device_key
    # sans enregistrement préalable. L'Edge + SQL doivent réassocier côté serveur et
    # refuser que l'approbation de B1 élève la confiance de B2.
    for marker in (
        'aal1_b2 = sign_in(email, password)',
        'aal2_b2 = verify_totp(aal1_b2, factor_id, secret)',
        'vault_open(aal2_b2, DEVICE_B, "Appareil B nouvelle session")',
        'challenge_b2 != challenge_b',
        'élévation de confiance B2 avec approbation B1',
        'TRUST_CONFIRMATION_REQUIRED',
    ):
        require(marker in smoke, f'preuve de non-rejeu multi-session manquante: {marker}')
    require('register_device(aal2_b2, DEVICE_B' not in smoke,
            'B2 ne doit pas dépendre d’un enregistrement client préalable pour fermer le rejeu')

    # Durcissement SQL historique : implémentations internes uniquement, liées à la session courante.
    require('create or replace function sinjira_security_internal.security_resolve_connection_challenge(' in migration,
            'résolveur standard interne non durci')
    require('create or replace function sinjira_security_internal.security_resolve_connection_challenge_mfa(' in migration,
            'résolveur MFA interne non durci')
    require('create or replace function public.security_resolve_connection_challenge(' not in migration,
            'la migration ne doit pas recréer une implémentation privilégiée dans public')
    require(migration.count("auth.jwt()->>'session_id'") >= 3,
            'liaison de session insuffisante dans les implémentations sensibles')
    require(migration.count('last_session_id=v_session') >= 2,
            'les deux résolveurs doivent lier la clé appareil à la session courante')
    require('CURRENT_TRUSTED_DEVICE_REQUIRED' in migration,
            'refus explicite de l’approbateur non courant absent')
    require("if v_action='conscience_vault'" in migration and 'TRUSTED_OTHER_DEVICE_REQUIRED' in migration,
            'le Coffre doit refuser l’auto-approbation MFA si un autre appareil fiable existe')
    require('resolver.id<>v_row.id' in migration,
            'security_set_device_trust doit exiger un résolveur différent de la cible')
    require('security definer' in migration.lower() and migration.lower().count('set search_path =') >= 3,
            'implémentations internes sans SECURITY DEFINER/search_path fixe')
    require('revoke all on function sinjira_security_internal.security_resolve_connection_challenge' in migration,
            'ACL interne du résolveur standard absente')
    require('grant execute on function sinjira_security_internal.security_resolve_connection_challenge' in migration,
            'grant interne nécessaire aux wrappers absent')

    # Nouveau contrat session-aware : session serveur validée, challenge lié, anciens chemins fermés.
    for marker in (
        'request_session_id uuid references auth.sessions(id) on delete set null',
        'create or replace function private.security_rebind_service_session(',
        'from auth.sessions s',
        'create or replace function private.security_challenge_request_session_guard()',
        "new.status := 'expired'",
        "raise exception 'CHALLENGE_SESSION_REQUIRED'",
        "raise exception 'CHALLENGE_SESSION_MISMATCH'",
        'create or replace function public.service_security_evaluate_context_session(',
        'create or replace function public.service_conscience_evaluate_access_session(',
        'and c.request_session_id=p_session_id',
        'c.request_session_id=v_session',
        'revoke execute on function public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text)',
    ):
        require(marker in session_binding_migration, f'liaison SQL challenge/session manquante: {marker}')

    # La frontière V24.5.10 reste en place : public = SECURITY INVOKER, interne = privilégié.
    require("alter function public.%I(%s) set schema sinjira_security_internal" in boundary,
            'frontière RPC sécurité historique introuvable')
    require("security invoker set search_path = ''" in boundary,
            'wrappers public SECURITY INVOKER non garantis par la migration de frontière')

    # Les deux pgTAP doivent exister : continuité historique + liaison session-aware additive.
    require('select plan(12);' in pgtap, 'le contrat pgTAP challenge doit contenir 12 assertions')
    for marker in ('last_session_id=v_session', 'CURRENT_TRUSTED_DEVICE_REQUIRED',
                   "v_action=''conscience_vault''", 'TRUSTED_OTHER_DEVICE_REQUIRED', 'resolver.id<>v_row.id'):
        require(marker in pgtap, f'assertion pgTAP challenge manquante: {marker}')
    require('select plan(12);' in session_binding_pgtap,
            'le contrat pgTAP liaison challenge/session doit contenir 12 assertions')
    for marker in ('request_session_id', 'service_security_evaluate_context_session',
                   'service_conscience_evaluate_access_session', 'CHALLENGE_SESSION_REQUIRED',
                   'CHALLENGE_SESSION_MISMATCH', 'c.request_session_id=v_session'):
        require(marker in session_binding_pgtap, f'assertion pgTAP session-aware manquante: {marker}')

    # Edge : le challenge du Coffre reste visible comme protection et ne crée pas de capacité avant approbation.
    require("code: 'SECURITY_CHALLENGE_REQUIRED'" in edge, 'code Edge de challenge absent')
    require("decision.outcome === 'challenge'" in edge, 'branche challenge Edge absente')
    require("service.rpc('service_conscience_open_session'" in edge, 'ouverture de capacité serveur absente')
    require("service.rpc('service_conscience_evaluate_access_session'" in edge,
            'le Registre doit utiliser le wrapper session-aware')
    require('p_session_id: authSessionId' in edge,
            'la session JWT vérifiée doit être transmise au wrapper du Registre')

    # Aucun privilège de test ni accès production.
    forbidden = (
        'SUPABASE_SERVICE_ROLE_KEY', 'SERVICE_ROLE_KEY', 'SUPABASE_ACCESS_TOKEN', 'sb_secret_',
        '/auth/v1/admin/', 'gpvivleexywljowcqkru', 'private.conscience_', '/rest/v1/conscience_',
        'service_conscience_', 'psql ', 'execute_sql', '--no-verify-jwt',
    )
    for marker in forbidden:
        require(marker not in smoke, f'surface privilégiée/directe interdite dans le smoke: {marker}')

    # Workflow entièrement local : pile complète, contrats SQL puis smoke HTTP.
    require('pull_request:' in workflow and 'workflow_dispatch:' in workflow, 'déclencheurs CI incomplets')
    require('supabase start' in workflow and 'supabase db start' not in workflow,
            'pile Supabase locale complète obligatoire')
    base_pg = 'supabase test db supabase/tests/personal_consciousness_vault_v25.test.sql --local'
    challenge_pg = 'supabase test db supabase/tests/device_challenge_continuity_v25.test.sql --local'
    session_pg = 'supabase test db supabase/tests/device_challenge_session_binding_v25.test.sql --local'
    require(base_pg in workflow, 'socle pgTAP Coffre 32 absent')
    require(challenge_pg in workflow, 'pgTAP challenge V25 absent')
    require(session_pg in workflow, 'pgTAP liaison challenge/session absent')
    require('python3 scripts/validate_device_challenge_continuity_smoke.py' in workflow,
            'validateur challenge non exécuté')
    require('python3 scripts/smoke_device_challenge_continuity_local.py' in workflow,
            'smoke challenge non exécuté')
    require('SINJIRA_LOCAL_API_URL="$API_URL"' in workflow and 'SINJIRA_LOCAL_ANON_KEY="$ANON_KEY"' in workflow,
            'URL/clé publique locales non injectées')
    require('--no-verify-jwt' not in workflow, 'JWT Edge ne doit jamais être désactivé')
    require('environment: production' not in workflow, 'environnement production interdit')
    require('SUPABASE_ACCESS_TOKEN' not in workflow, 'PAT production interdit')
    require(not set(re.findall(r'secrets\.([A-Z0-9_]+)', workflow)), 'secrets GitHub interdits dans ce workflow')

    base_index = workflow.index(base_pg)
    challenge_index = workflow.index(challenge_pg)
    session_index = workflow.index(session_pg)
    smoke_index = workflow.index('python3 scripts/smoke_device_challenge_continuity_local.py')
    require(base_index < challenge_index < session_index < smoke_index,
            'ordre attendu: pgTAP Coffre, challenge, liaison session, puis smoke HTTP')

    print('OK challenge appareils V25: session courante, liaison challenge/session pgTAP, non-rejeu après nouvelle session, auto-MFA Coffre interdite, retry stable et refus final couverts sans privilège.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
