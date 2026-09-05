#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / 'scripts' / 'smoke_personal_ai_functional_local.py'
AAL2_HELPER = ROOT / 'scripts' / 'smoke_sensitive_aal2_local.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-personal-ai-functional-v25.yml'
EDGE = ROOT / 'supabase' / 'functions' / 'personal-ai' / 'index.ts'


def fail(message: str) -> None:
    print(f'ECHEC smoke fonctionnel Mon IA V25: {message}', file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (SMOKE, AAL2_HELPER, WORKFLOW, EDGE):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    smoke = SMOKE.read_text('utf-8')
    helper = AAL2_HELPER.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')
    edge = EDGE.read_text('utf-8')

    # La preuve fonctionnelle doit réutiliser le vrai TOTP/AAL2 local, pas fabriquer un JWT.
    require('from smoke_sensitive_aal2_local import' in smoke, 'le helper AAL2 réel doit être réutilisé')
    require('enroll_totp' in smoke and 'verify_totp' in smoke, 'enrôlement/vérification TOTP absents')
    require('get("aal") == "aal2"' in smoke, 'claim aal2 non vérifié')
    require('/auth/v1/factors' in helper and '/challenge' in helper and '/verify' in helper,
            'le helper AAL2 doit traverser GoTrue réel')

    # Bootstrap autorisé du premier appareil uniquement : courant + AAL2 + RPC utilisateur.
    require('/rest/v1/rpc/{name}' in smoke, 'les RPC sécurité doivent passer par PostgREST utilisateur')
    require('security_register_device' in smoke, 'enregistrement appareil utilisateur absent')
    require('security_set_device_trust' in smoke, 'bootstrap de confiance absent')
    require('"p_trusted": True' in smoke and '"p_primary": True' in smoke,
            'le premier appareil doit être explicitement fiable et principal')
    require('is_current' in smoke and 'is_trusted' in smoke and 'is_primary' in smoke,
            'preuves appareil courant/fiable/principal insuffisantes')
    require('security_list_devices' in smoke, 'liste assainie des appareils non vérifiée')
    require('"device_key" not in' in smoke and '"last_session_id" not in' in smoke,
            'la confidentialité des secrets appareil doit être vérifiée')
    require('security_resolve_connection_challenge' not in smoke,
            'le bootstrap du premier appareil ne doit pas inventer une auto-approbation de challenge')

    # Mon IA doit rester une fondation sans runtime conversationnel.
    for action in ('get_state', 'update_settings', 'set_source_permission', 'delete_personal_ai_data'):
        require(f'"{action}"' in smoke, f'action fonctionnelle manquante: {action}')
    require('runtime_status' in smoke and 'not_configured' in smoke, 'runtime_status non verrouillé')
    for flag in ('conversation_enabled', 'memory_enabled', 'source_retrieval_enabled', 'provider_configured'):
        require(flag in smoke, f'drapeau runtime non vérifié: {flag}')
    require('runtime.get(key) is False' in smoke, 'les drapeaux runtime doivent être exigés à false')
    require('runtime_access_enabled' in smoke and 'is False' in smoke,
            'les consentements source ne doivent pas activer la récupération de contenu')

    require('"life_story"' in smoke and '"employment"' in smoke, 'sources autorisées incomplètes')
    require('source_type="conscience"' in smoke, 'le refus explicite du Coffre comme source doit être testé')
    require('PERSONAL_AI_SOURCE_FORBIDDEN' in smoke, 'code de refus source conscience non vérifié')
    require('user_id=' in smoke and 'CLIENT_IDENTITY_FORBIDDEN' in smoke,
            'identité client interdite non testée')
    require('"chat"' in smoke and 'UNKNOWN_ACTION' in smoke, 'absence de runtime chat non testée')
    require('prompt="Aucune donnée réelle"' in smoke, 'tout contenu de test doit être explicitement synthétique')

    # Le script ne doit jamais contourner l'Edge ni les ACL privées.
    forbidden = (
        'SUPABASE_SERVICE_ROLE_KEY', 'SERVICE_ROLE_KEY', 'SUPABASE_ACCESS_TOKEN', 'sb_secret_',
        '/auth/v1/admin/', 'gpvivleexywljowcqkru', 'private.personal_ai_',
        '/rest/v1/personal_ai_', 'service_personal_ai_', 'psql ', 'execute_sql',
    )
    for marker in forbidden:
        require(marker not in smoke, f'surface privilégiée/directe interdite dans le smoke: {marker}')
    require('127.0.0.1' in helper and 'localhost' in helper, 'le helper doit rester local-only')

    # Le contrat Edge reste lui-même borné.
    require("const RISK_SCOPE = 'ai_private';" in edge, 'scope ai_private non fixé côté Edge')
    require("['life_story','employment']" in edge, 'allowlist source Edge inattendue')
    require("action === 'get_state'" in edge and "action === 'delete_personal_ai_data'" in edge,
            'surface fonctionnelle Edge inattendue')
    require('Aucun endpoint chat/memory/retrieve_source/complete/generate' in edge,
            'contrat sans runtime conversationnel absent')

    # CI : pile complète, pgTAP avant HTTP, aucun secret ni production.
    require('pull_request:' in workflow and 'workflow_dispatch:' in workflow, 'déclencheurs CI incomplets')
    require('supabase start' in workflow, 'pile Supabase complète obligatoire')
    require('supabase db start' not in workflow, 'db start seul ne suffit pas')
    require('supabase test db supabase/tests/personal_ai_v25.test.sql --local' in workflow,
            '35 pgTAP Mon IA doivent être exécutés')
    require('python3 scripts/validate_personal_ai_v25.py' in workflow, 'validateur statique Mon IA absent')
    require('python3 scripts/validate_sensitive_aal2_smoke.py' in workflow, 'garde AAL2 partagé absent')
    require('python3 scripts/validate_personal_ai_functional_smoke.py' in workflow, 'garde fonctionnel absent')
    require('python3 scripts/smoke_personal_ai_functional_local.py' in workflow, 'smoke fonctionnel non exécuté')
    require('SINJIRA_LOCAL_API_URL="$API_URL"' in workflow and 'SINJIRA_LOCAL_ANON_KEY="$ANON_KEY"' in workflow,
            'URL/clé publique locales non injectées')
    require('--no-verify-jwt' not in workflow, 'JWT Edge ne doit jamais être désactivé')
    require('environment: production' not in workflow, 'environnement production interdit')
    require('SUPABASE_ACCESS_TOKEN' not in workflow, 'PAT production interdit')
    secret_refs = set(re.findall(r'secrets\.([A-Z0-9_]+)', workflow))
    require(not secret_refs, f'secrets GitHub interdits: {sorted(secret_refs)}')

    pg_index = workflow.index('supabase test db supabase/tests/personal_ai_v25.test.sql --local')
    smoke_index = workflow.index('python3 scripts/smoke_personal_ai_functional_local.py')
    require(pg_index < smoke_index, 'pgTAP doit passer avant le smoke HTTP')

    print('OK smoke fonctionnel Mon IA V25: AAL2 réel, premier appareil fiable légitime, runtime désactivé, sources bornées et suppression vérifiée sans privilège.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
