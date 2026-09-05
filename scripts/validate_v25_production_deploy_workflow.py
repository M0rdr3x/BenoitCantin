#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-production-deploy.yml'

EXPECTED_MIGRATIONS = [
    '20260902211500_sinjira_v25_0_security_risk_model_convergence.sql',
    '20260902223000_sinjira_v25_0_personal_consciousness_vault.sql',
    '20260902231500_sinjira_v25_0_conscience_vault_challenge_continuity.sql',
    '20260903213000_sinjira_v25_0_device_key_privacy_and_trust_hardening.sql',
]
EXPECTED_NAMES = [
    'sinjira_v25_0_security_risk_model_convergence',
    'sinjira_v25_0_personal_consciousness_vault',
    'sinjira_v25_0_conscience_vault_challenge_continuity',
    'sinjira_v25_0_device_key_privacy_and_trust_hardening',
]


def require(text: str, markers: list[str], label: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text: str, markers: list[str], label: str) -> None:
    found = [marker for marker in markers if marker in text]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits: {found}')


def top_level_block(text: str, start: str, end: str) -> str:
    start_pos = text.find(start)
    if start_pos < 0:
        raise AssertionError(f'Bloc absent: {start.strip()}')
    end_pos = text.find(end, start_pos + len(start))
    if end_pos < 0:
        raise AssertionError(f'Fin de bloc absente: {end.strip()}')
    return text[start_pos:end_pos]


def active_text(text: str) -> str:
    return '\n'.join(
        raw for raw in text.splitlines()
        if not raw.strip().startswith('#')
    )


def trigger_keys(block: str) -> set[str]:
    keys = set()
    for line in block.splitlines()[1:]:
        match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line)
        if match:
            keys.add(match.group(1))
    return keys


def main() -> int:
    if not WORKFLOW.exists():
        raise AssertionError(f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')

    workflow = WORKFLOW.read_text('utf-8', errors='strict')
    triggers = top_level_block(workflow, 'on:\n', '\npermissions:')
    active = active_text(workflow)

    observed_triggers = trigger_keys(triggers)
    if observed_triggers != {'workflow_dispatch'}:
        raise AssertionError(
            'Le déploiement production doit être strictement manuel: '
            f'triggers observés={sorted(observed_triggers)}'
        )

    require(workflow, [
        'Saisir exactement DEPLOY-SINJIRA-V25',
        'test "$DEPLOY_CONFIRMATION" = "DEPLOY-SINJIRA-V25"',
        'environment: production',
        'SUPABASE_PROJECT_REF: gpvivleexywljowcqkru',
        'V25_DEPLOY_SHA: fc8d9fe26c8f095a0e95dc6cadcbf43d7c61c9dd',
        'EXPECTED_REMOTE_BASELINE: "20260901002241"',
        'EXPECTED_REMOTE_BASELINE_NAME: sinjira_v24_5_54_fracture_contribution_atomic_finalize',
        'SUPABASE_MANAGEMENT_API: https://api.supabase.com/v1',
        'SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
        'ref: ${{ env.V25_DEPLOY_SHA }}',
        'persist-credentials: false',
        'actual_sha="$(git rev-parse HEAD)"',
        '/projects/$SUPABASE_PROJECT_REF/database/migrations',
        '--header "Authorization: Bearer $SUPABASE_ACCESS_TOKEN"',
        '--request POST',
        'Idempotency-Key: sinjira-v25-$name',
        'json.dumps({"name": os.environ["MIGRATION_NAME"], "query": sql})',
        'after_names != expected[:len(after_names)]',
        'if after_names != expected:',
        'supabase functions deploy conscience-vault',
        '--project-ref "$SUPABASE_PROJECT_REF"',
        '--use-api',
    ], 'contrat de déploiement V25')

    for migration in EXPECTED_MIGRATIONS:
        require(workflow, [f'supabase/migrations/{migration}'], f'migration gelée {migration}')
    for name in EXPECTED_NAMES:
        require(workflow, [f'"{name}"'], f'nom distant V25 {name}')

    forbid(active, [
        'SUPABASE_DB_PASSWORD',
        '--no-verify-jwt',
        'supabase db push',
        'supabase db reset',
        'supabase migration repair',
        '--include-all',
        'continue-on-error: true',
        'set -x',
        '/database/query',
        '20260904225000_sinjira_v25_employment_foundation.sql',
        '20260905000500_sinjira_v25_personal_ai_foundation.sql',
        '20260905001000_sinjira_v25_personal_ai_rls_hardening.sql',
    ], 'aucun élargissement, fuite de secret ou contournement du rollout')

    if active.count('supabase functions deploy ') != 1:
        raise AssertionError('Le workflow doit déployer exactement une Edge Function.')

    first_history_read = active.find('/projects/$SUPABASE_PROJECT_REF/database/migrations')
    apply_migrations = active.find('--request POST')
    post_history_check = active.find('Vérifier l\'historique V25 après migration')
    edge = active.find('supabase functions deploy conscience-vault')
    if min(first_history_read, apply_migrations, post_history_check, edge) < 0:
        raise AssertionError('Étapes obligatoires du déploiement V25 introuvables.')
    if not (first_history_read < apply_migrations < post_history_check < edge):
        raise AssertionError(
            'Ordre obligatoire: lecture historique, migrations API, vérification historique, Edge Function.'
        )

    print(
        'OK déploiement V25: manuel uniquement, SHA/baseline gelés, '
        'quatre migrations Management API idempotentes, puis conscience-vault avec JWT.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
