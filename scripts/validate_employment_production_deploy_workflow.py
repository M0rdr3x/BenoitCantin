#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-employment-production.yml'


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


def trigger_keys(block: str) -> set[str]:
    keys = set()
    for line in block.splitlines()[1:]:
        match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line)
        if match:
            keys.add(match.group(1))
    return keys


def main() -> int:
    if not WORKFLOW.is_file():
        raise AssertionError(f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')

    workflow = WORKFLOW.read_text('utf-8', errors='strict')
    active = '\n'.join(line for line in workflow.splitlines() if not line.strip().startswith('#'))
    triggers = top_level_block(workflow, 'on:\n', '\npermissions:')

    if trigger_keys(triggers) != {'workflow_dispatch'}:
        raise AssertionError('Le déploiement Emploi production doit rester strictement manuel.')

    require(workflow, [
        'DEPLOY-SINJIRA-V25-EMPLOYMENT',
        'environment: production',
        'SUPABASE_PROJECT_REF: gpvivleexywljowcqkru',
        'EMPLOYMENT_DEPLOY_SHA: 2077ca7ff3a0ec77a27a908a9379e92149a4e0a5',
        'EXPECTED_REMOTE_BASELINE: "20260905131659"',
        'EXPECTED_REMOTE_BASELINE_NAME: sinjira_v25_conscience_vault_audit_session_index',
        'EMPLOYMENT_MIGRATION_NAME: sinjira_v25_employment_foundation',
        'SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
        'ref: ${{ env.EMPLOYMENT_DEPLOY_SHA }}',
        'persist-credentials: false',
        '20260904225000_sinjira_v25_employment_foundation.sql',
        'test ! -f supabase/migrations/20260905000500_sinjira_v25_personal_ai_foundation.sql',
        'test ! -f supabase/migrations/20260905001000_sinjira_v25_personal_ai_rls_hardening.sql',
        '/projects/$SUPABASE_PROJECT_REF/database/migrations',
        '--request POST',
        "json.dumps({'name': os.environ['EMPLOYMENT_MIGRATION_NAME'], 'query': sql})",
        "after not in ([], allowed)",
        'Aucun catalogue d\'offres, aucune Edge Function, aucun module Mon IA',
    ], 'contrat production Emploi')

    forbid(active, [
        'SUPABASE_DB_PASSWORD',
        'supabase db push',
        'supabase functions deploy',
        '--include-all',
        'continue-on-error: true',
        'set -x',
    ], 'aucun élargissement du lot Emploi')

    if active.count('--request POST') != 1:
        raise AssertionError('Le workflow Emploi doit contenir exactement une voie POST de migration.')

    baseline = active.find('Vérifier la baseline distante')
    apply_step = active.find('Appliquer uniquement la migration Emploi')
    verify = active.find("Vérifier l'historique après déploiement")
    if min(baseline, apply_step, verify) < 0 or not baseline < apply_step < verify:
        raise AssertionError('Ordre obligatoire: baseline, migration Emploi, vérification finale.')

    print('OK production Emploi V25: manuel, SHA gelé, une migration ciblée, Mon IA exclu et aucune Edge Function.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
