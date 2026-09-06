#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / 'scripts' / 'smoke_device_challenge_continuity_local.py'
HELPER = ROOT / 'scripts' / 'smoke_sensitive_aal2_local.py'
MIGRATION = ROOT / 'supabase' / 'migrations' / '20260905163000_sinjira_v25_device_challenge_continuity_hardening.sql'
BOUNDARY = ROOT / 'supabase' / 'migrations' / '20260822201257_sinjira_v24_5_10_security_rpc_boundary.sql'
PGTAP = ROOT / 'supabase' / 'tests' / 'device_challenge_continuity_v25.test.sql'
EDGE = ROOT / 'supabase' / 'functions' / 'conscience-vault' / 'index.ts'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-device-challenge-continuity-v25.yml'


def fail(message: str) -> None:
    print(f'ECHEC challenge appareils V25: {message}', file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (SMOKE, HELPER, MIGRATION, BOUNDARY, PGTAP, EDGE, WORKFLOW):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    smoke = SMOKE.read_text('utf-8')
    helper = HELPER.read_text('utf-8')
    migration = MIGRATION.read_text('utf-8')
    boundary = BOUNDARY.read_text('utf-8')
    pgtap = PGTAP.read_text('utf-8')
    edge = EDGE.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')

    # Le test traverse GoTrue réel et trois sessions distinctes du même compte synthétique.
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

    # Durcissement SQL : implémentations internes uniquement, liées à la session courante.
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

    # La frontière V24.5.10 reste en place : public = SECURITY INVOKER, interne = privilégié.
    require("alter function public.%I(%s) set schema sinjira_security_internal" in boundary,
            'frontière RPC sécurité historique introuvable')
    require("security invoker set search_path = ''" in boundary,
            'wrappers public SECURITY INVOKER non garantis par la migration de frontière')

    # pgTAP introspecte les mêmes invariants sans modifier les 32 tests historiques du Coffre.
    require('select plan(12);' in pgtap, 'le contrat pgTAP challenge doit contenir 12 assertions')
    for marker in ('last_session_id=v_session', 'CURRENT_TRUSTED_DEVICE_REQUIRED',
                   "v_action=''conscience_vault''", 'TRUSTED_OTHER_DEVICE_REQUIRED', 'resolver.id<>v_row.id'):
        require(marker in pgtap, f'assertion pgTAP manquante: {marker}')

    # Edge : le challenge du Coffre reste visible comme protection et ne crée pas de capacité avant approbation.
    require("code: 'SECURITY_CHALLENGE_REQUIRED'" in edge, 'code Edge de challenge absent')
    require("decision.outcome === 'challenge'" in edge, 'branche challenge Edge absente')
    require("service.rpc('service_conscience_open_session'" in edge, 'ouverture de capacité serveur absente')

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
    require('supabase test db supabase/tests/personal_consciousness_vault_v25.test.sql --local' in workflow,
            'socle pgTAP Coffre 32 absent')
    require('supabase test db supabase/tests/device_challenge_continuity_v25.test.sql --local' in workflow,
            'pgTAP challenge V25 absent')
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

    pg_index = workflow.index('supabase test db supabase/tests/device_challenge_continuity_v25.test.sql --local')
    smoke_index = workflow.index('python3 scripts/smoke_device_challenge_continuity_local.py')
    require(pg_index < smoke_index, 'pgTAP challenge doit passer avant le smoke HTTP')

    print('OK challenge appareils V25: session courante, autre appareil fiable, auto-MFA Coffre interdite, retry stable et refus final couverts sans privilège.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
