#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / 'scripts' / 'smoke_conscience_vault_functional_local.py'
AAL2_HELPER = ROOT / 'scripts' / 'smoke_sensitive_aal2_local.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-conscience-vault-functional-v25.yml'
EDGE = ROOT / 'supabase' / 'functions' / 'conscience-vault' / 'index.ts'
PGTAP = ROOT / 'supabase' / 'tests' / 'personal_consciousness_vault_v25.test.sql'


def fail(message: str) -> None:
    print(f'ECHEC smoke fonctionnel Coffre V25: {message}', file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (SMOKE, AAL2_HELPER, WORKFLOW, EDGE, PGTAP):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    smoke = SMOKE.read_text('utf-8')
    helper = AAL2_HELPER.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')
    edge = EDGE.read_text('utf-8')
    pgtap = PGTAP.read_text('utf-8')

    # Le smoke doit réutiliser le vrai flux GoTrue TOTP/AAL2 local.
    require('from smoke_sensitive_aal2_local import' in smoke, 'le helper AAL2 réel doit être réutilisé')
    require('enroll_totp' in smoke and 'verify_totp' in smoke, 'enrôlement/vérification TOTP absents')
    require('get("aal") == "aal2"' in smoke, 'claim aal2 non vérifié')
    require('/auth/v1/factors' in helper and '/challenge' in helper and '/verify' in helper,
            'le helper doit traverser GoTrue réel')
    require('127.0.0.1' in helper and 'localhost' in helper, 'le helper AAL2 doit rester local-only')

    # Bootstrap légitime du premier appareil courant uniquement.
    require('/rest/v1/rpc/{name}' in smoke, 'les RPC sécurité doivent passer par PostgREST utilisateur')
    for rpc_name in ('security_register_device', 'security_set_device_trust', 'security_list_devices'):
        require(rpc_name in smoke, f'RPC sécurité manquante: {rpc_name}')
    require('"p_trusted": True' in smoke and '"p_primary": True' in smoke,
            'le premier appareil doit être explicitement fiable et principal')
    require('is_current' in smoke and 'is_trusted' in smoke and 'is_primary' in smoke,
            'preuves appareil courant/fiable/principal insuffisantes')
    require('"device_key" not in' in smoke and '"last_session_id" not in' in smoke,
            'la confidentialité des secrets appareil doit être vérifiée')
    require('security_resolve_connection_challenge' not in smoke,
            'le smoke ne doit jamais auto-résoudre un challenge de connexion')

    # Capacité courte et cycle fonctionnel complet du Coffre.
    for action in ('open_session', 'list_entries', 'create_entry', 'update_entry', 'delete_entry', 'revoke_session'):
        require(f'"{action}"' in smoke, f'action Coffre manquante: {action}')
    require('ttl_seconds=60' in smoke, 'la capacité minimale de 60 secondes doit être utilisée')
    require('ttl_seconds=59' in smoke and 'VAULT_TTL_INVALID' in smoke,
            'le refus sous la borne de 60 secondes doit être testé')
    require('session2 != session1' in smoke, 'la rotation de capacité doit produire un nouvel identifiant')
    require(smoke.count('VAULT_SESSION_INVALID') >= 2,
            'ancienne capacité et capacité révoquée doivent être refusées')
    require('VAULT_SESSION_REQUIRED' in smoke, 'absence de capacité non testée')
    require('CLIENT_IDENTITY_FORBIDDEN' in smoke and 'user_id=' in smoke,
            'identité client injectée non testée')

    # Le contenu de test doit être explicitement synthétique et non intime.
    require('CONTENT_1 = "Donnée synthétique de test local — aucune information personnelle réelle."' in smoke,
            'marqueur synthétique initial inattendu')
    require('CONTENT_2 = "Donnée synthétique modifiée — aucun contenu intime ni donnée personnelle réelle."' in smoke,
            'marqueur synthétique modifié inattendu')
    require('content_payload=CONTENT_1' in smoke and 'content_payload=CONTENT_2' in smoke,
            'le CRUD doit utiliser uniquement les marqueurs synthétiques')
    require('ENTRY_TYPE = "local_test_marker"' in smoke, 'type d’entrée synthétique inattendu')

    # Confidentialité et décision de sécurité doivent être visibles dans la réponse Edge.
    for marker in ('identity_from_verified_jwt', 'raw_ip_stored', 'gps_used', 'client_geo_accepted', 'legacy_access'):
        require(marker in smoke, f'assertion privacy manquante: {marker}')
    require('risk_model_version' in smoke and 'v25.0' in smoke, 'modèle de risque V25 non vérifié')
    require('mandatory_step_up' in smoke and 'requires_step_up' in smoke, 'step-up obligatoire non vérifié')
    require('0 <= score < 75' in smoke, 'borne de risque acceptable non vérifiée')

    # Le smoke ne doit jamais contourner l’Edge ou les ACL privées.
    forbidden = (
        'SUPABASE_SERVICE_ROLE_KEY', 'SERVICE_ROLE_KEY', 'SUPABASE_ACCESS_TOKEN', 'sb_secret_',
        '/auth/v1/admin/', 'gpvivleexywljowcqkru', 'private.conscience_',
        '/rest/v1/conscience_', 'service_conscience_', 'psql ', 'execute_sql', '--no-verify-jwt',
    )
    for marker in forbidden:
        require(marker not in smoke, f'surface privilégiée/directe interdite dans le smoke: {marker}')

    # Le contrat Edge doit continuer à imposer AAL2 à chaque appel et une capacité aux opérations CRUD.
    require('AAL2 est vérifié à CHAQUE appel' in edge, 'contrat AAL2 à chaque appel absent')
    require("action === 'open_session'" in edge and "action === 'revoke_session'" in edge,
            'surface Edge Coffre inattendue')
    require("if (!validUuid(sessionId)) throw new Error('VAULT_SESSION_REQUIRED')" in edge,
            'capacité obligatoire avant opérations Coffre absente')
    require('identity_from_verified_jwt: true' in edge, 'preuve identité JWT absente de la réponse Edge')
    require('raw_ip_stored: false' in edge and 'gps_used: false' in edge,
            'garanties IP brute/GPS absentes de la réponse Edge')

    # Les 32 pgTAP historiques doivent rester le socle avant le smoke HTTP.
    require('select plan(32);' in pgtap, 'plan pgTAP Coffre doit rester à 32 assertions')
    require('pull_request:' in workflow and 'workflow_dispatch:' in workflow, 'déclencheurs CI incomplets')
    require('supabase start' in workflow, 'pile Supabase complète obligatoire')
    require('supabase db start' not in workflow, 'db start seul ne suffit pas au smoke Auth/Edge')
    require('supabase test db supabase/tests/personal_consciousness_vault_v25.test.sql --local' in workflow,
            '32 pgTAP Coffre doivent être exécutés')
    require('python3 scripts/validate_conscience_vault_edge_v25.py' in workflow,
            'validateur Edge Coffre absent')
    require('python3 scripts/validate_sensitive_aal2_smoke.py' in workflow,
            'garde AAL2 partagé absent')
    require('python3 scripts/validate_conscience_vault_functional_smoke.py' in workflow,
            'garde fonctionnel Coffre absent')
    require('python3 scripts/smoke_conscience_vault_functional_local.py' in workflow,
            'smoke fonctionnel Coffre non exécuté')
    require('SINJIRA_LOCAL_API_URL="$API_URL"' in workflow and 'SINJIRA_LOCAL_ANON_KEY="$ANON_KEY"' in workflow,
            'URL/clé publique locales non injectées')
    require('--no-verify-jwt' not in workflow, 'JWT Edge ne doit jamais être désactivé')
    require('environment: production' not in workflow, 'environnement production interdit')
    require('SUPABASE_ACCESS_TOKEN' not in workflow, 'PAT production interdit')
    secret_refs = set(re.findall(r'secrets\.([A-Z0-9_]+)', workflow))
    require(not secret_refs, f'secrets GitHub interdits: {sorted(secret_refs)}')

    pg_index = workflow.index('supabase test db supabase/tests/personal_consciousness_vault_v25.test.sql --local')
    smoke_index = workflow.index('python3 scripts/smoke_conscience_vault_functional_local.py')
    require(pg_index < smoke_index, 'pgTAP doit passer avant le smoke HTTP')

    print('OK smoke fonctionnel Coffre V25: AAL2 réel, appareil fiable légitime, capacité courte, CRUD synthétique, rotation/révocation et confidentialité sans privilège.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
