#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-production-deploy.yml'

EXPECTED_MIGRATIONS = [
    '20260902211500_sinjira_v25_0_security_risk_model_convergence.sql',
    '20260902223000_sinjira_v25_0_personal_consciousness_vault.sql',
    '20260902231500_sinjira_v25_0_conscience_vault_challenge_continuity.sql',
    '20260903213000_sinjira_v25_0_device_key_privacy_and_trust_hardening.sql',
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


def active_shell_text(text: str) -> str:
    lines = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith('#'):
            continue
        lines.append(raw)
    return '\n'.join(lines)


def main() -> int:
    if not WORKFLOW.exists():
        raise AssertionError(f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')

    workflow = WORKFLOW.read_text('utf-8', errors='strict')
    triggers = top_level_block(workflow, 'on:\n', '\npermissions:')
    active = active_shell_text(workflow)

    require(triggers, ['workflow_dispatch:'], 'déclenchement production manuel')
    forbid(
        triggers,
        ['pull_request:', 'push:', 'schedule:', 'workflow_run:', 'repository_dispatch:'],
        'aucun déclenchement automatique du déploiement production',
    )

    require(workflow, [
        'Saisir exactement DEPLOY-SINJIRA-V25',
        'test "$DEPLOY_CONFIRMATION" = "DEPLOY-SINJIRA-V25"',
        'environment: production',
        'SUPABASE_PROJECT_REF: gpvivleexywljowcqkru',
        'V25_DEPLOY_SHA: fc8d9fe26c8f095a0e95dc6cadcbf43d7c61c9dd',
        'EXPECTED_REMOTE_BASELINE: "20260901002241"',
        'SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
        'SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}',
        'ref: ${{ env.V25_DEPLOY_SHA }}',
        'persist-credentials: false',
        'actual_sha="$(git rev-parse HEAD)"',
        'actual_baseline = max(remote_versions)',
        'if actual_baseline != baseline:',
        'if remote_only:',
        'if pending != expected:',
        'supabase migration list --linked',
        'supabase db push --linked --dry-run',
        'supabase db push --linked --yes',
        'supabase functions deploy conscience-vault',
        '--project-ref "$SUPABASE_PROJECT_REF"',
        '--use-api',
    ], 'contrat de déploiement V25')

    for migration in EXPECTED_MIGRATIONS:
        require(workflow, [f'supabase/migrations/{migration}'], f'migration gelée {migration}')

    require(workflow, [
        '"20260902211500"',
        '"20260902223000"',
        '"20260902231500"',
        '"20260903213000"',
    ], 'versions exactes autorisées')

    forbid(active, [
        '--no-verify-jwt',
        'supabase db reset',
        '--include-all',
        'continue-on-error: true',
        '20260904225000_sinjira_v25_employment_foundation.sql',
        '20260905000500_sinjira_v25_personal_ai_foundation.sql',
        '20260905001000_sinjira_v25_personal_ai_rls_hardening.sql',
    ], 'aucun élargissement ou contournement du rollout')

    if active.count('supabase functions deploy ') != 1:
        raise AssertionError('Le workflow doit déployer exactement une Edge Function.')

    dry_run = active.find('supabase db push --linked --dry-run')
    apply = active.find('supabase db push --linked --yes')
    edge = active.find('supabase functions deploy conscience-vault')
    if min(dry_run, apply, edge) < 0 or not (dry_run < apply < edge):
        raise AssertionError('Ordre obligatoire: dry-run SQL, db push, puis conscience-vault.')

    print(
        'OK déploiement V25: manuel uniquement, confirmation explicite, SHA/baseline gelés, '
        'quatre migrations exactes, dry-run avant écriture et conscience-vault avec JWT.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
