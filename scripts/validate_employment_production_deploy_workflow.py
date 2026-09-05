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
        raise AssertionError('La vérification Emploi production doit rester strictement manuelle.')

    require(workflow, [
        'name: SINJIRA V25 — Vérification production Emploi',
        'VERIFY-SINJIRA-V25-EMPLOYMENT',
        'environment: production',
        'SUPABASE_PROJECT_REF: gpvivleexywljowcqkru',
        'EXPECTED_REMOTE_BASELINE: "20260905131659"',
        'EXPECTED_REMOTE_BASELINE_NAME: sinjira_v25_conscience_vault_audit_session_index',
        'EXPECTED_EMPLOYMENT_VERSION: "20260905133130"',
        'EXPECTED_EMPLOYMENT_NAME: sinjira_v25_employment_foundation',
        'SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
        'ref: main',
        'persist-credentials: false',
        '/projects/$SUPABASE_PROJECT_REF/database/migrations',
        "if observed != employment:",
        "if len(matches) != 1:",
        'Aucune migration, aucune Edge Function et aucun secret',
        'Emploi reste séparé du Registre personnel',
    ], 'contrat post-déploiement Emploi')

    forbid(active, [
        'DEPLOY-SINJIRA-V25-EMPLOYMENT',
        '--request POST',
        'SUPABASE_DB_PASSWORD',
        'supabase db push',
        'supabase functions deploy',
        'supabase secrets set',
        'continue-on-error: true',
        'set -x',
    ], 'la vérification Emploi doit rester en lecture seule')

    if active.count('/projects/$SUPABASE_PROJECT_REF/database/migrations') != 1:
        raise AssertionError('Le workflow Emploi doit effectuer une seule lecture de l’historique distant.')

    contracts = active.find('Vérifier les contrats Emploi')
    history = active.find("Vérifier l'historique Emploi en lecture seule")
    summary = active.find('Résumé lecture seule')
    if min(contracts, history, summary) < 0 or not contracts < history < summary:
        raise AssertionError('Ordre attendu: contrats locaux, historique distant, résumé lecture seule.')

    print(
        'OK production Emploi V25: vérification manuelle lecture seule, '
        'version distante figée et séparation Mon IA préservée.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
