#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M1 = ROOT / 'supabase/migrations/20260905000500_sinjira_v25_personal_ai_foundation.sql'
M2 = ROOT / 'supabase/migrations/20260905001000_sinjira_v25_personal_ai_rls_hardening.sql'
M3 = ROOT / 'supabase/migrations/20260905150000_sinjira_v25_personal_ai_audit_user_index.sql'
EDGE = ROOT / 'supabase/functions/personal-ai/index.ts'
AUTH = ROOT / 'supabase/functions/_shared/auth.ts'
CONFIG = ROOT / 'supabase/config.toml'
TEST = ROOT / 'supabase/tests/personal_ai_v25.test.sql'
MANIFEST = ROOT / 'scripts/validate_production_schema_manifest.py'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ECHEC readiness Mon IA V25: {message}')


def main() -> int:
    for path in (M1, M2, M3, EDGE, AUTH, CONFIG, TEST, MANIFEST):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    m1 = M1.read_text('utf-8')
    m2 = M2.read_text('utf-8')
    m3 = M3.read_text('utf-8')
    edge = EDGE.read_text('utf-8')
    auth = AUTH.read_text('utf-8')
    config = CONFIG.read_text('utf-8')
    test = TEST.read_text('utf-8')
    manifest = MANIFEST.read_text('utf-8')

    require('private.personal_ai_settings' in m1, 'table settings absente')
    require('private.personal_ai_source_permissions' in m1, 'table permissions absente')
    require('private.personal_ai_audit' in m1, 'table audit absente')
    require("runtime_status text not null default 'not_configured'" in m1, 'runtime doit rester non configuré')
    require("source_type in ('life_story','employment')" in m1, 'sources préparatoires non bornées')
    require('conversation_enabled' in m1 and 'false' in m1, 'conversation doit rester désactivée')
    require('source_retrieval_enabled' in m1 and 'false' in m1, 'récupération de sources doit rester désactivée')
    require('enable row level security' in m2.lower(), 'durcissement RLS absent')
    require('create policy' not in m2.lower(), 'aucune policy client ne doit être créée sur Mon IA')
    require('create index if not exists personal_ai_audit_user_idx' in m3, 'index couvrant la FK audit.user_id absent')
    require('on private.personal_ai_audit(user_id)' in m3, 'index audit.user_id mal ciblé')

    for forbidden in ('conscience_entries', 'service_conscience_', "action === 'chat'", "action === 'memory'", "action === 'retrieve_source'", "action === 'complete'", "action === 'generate'"):
        require(forbidden not in edge, f'élément runtime/source interdit dans Edge: {forbidden}')

    require('requiredPersonalAiUser' in edge, 'auth serveur Mon IA absente')
    require('service_personal_ai_evaluate_access' in edge, 'moteur risque ai_private absent')
    require('CLIENT_IDENTITY_FORBIDDEN' in edge, 'identité client non explicitement refusée')
    require('private, no-store' in edge, 'réponses privées no-store absentes')
    require('requiredPersonalAiUser' in auth and 'assertPersonalAiMfa' in auth, 'AAL2 Mon IA incomplet')

    block = config.split('[functions.personal-ai]', 1)
    require(len(block) == 2, 'bloc config personal-ai absent')
    config_block = block[1].split('[functions.', 1)[0]
    require('verify_jwt = true' in config_block, 'JWT doit rester obligatoire')

    compact_manifest = manifest.replace('\n', '')
    require("'personal_ai_settings','personal_ai_source_permissions','personal_ai_audit'" in compact_manifest, 'tables Mon IA non classées ensemble dans le manifeste')
    require('select plan(36);' in test, 'contrat pgTAP Mon IA doit rester à 36 assertions')
    require("has_index('private','personal_ai_audit','personal_ai_audit_user_idx'" in test, 'test de l index audit absent')

    print('OK readiness Mon IA V25: fondation privée, 36 pgTAP, index audit, AAL2/ai_private, JWT obligatoire, runtime non configuré et aucune source Registre.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
