#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-production-deploy.yml'

MANAGEMENT_URL = 'https://api.supabase.com/v1/projects/gpvivleexywljowcqkru/database/migrations'
FUNCTIONS_CMD = 'supabase functions list --project-ref "gpvivleexywljowcqkru" | tee "$functions_list"'
TOKEN_LINE = '          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}'
EXPECTED_NAMES = [
    'sinjira_v25_0_security_risk_model_convergence',
    'sinjira_v25_0_personal_consciousness_vault',
    'sinjira_v25_0_conscience_vault_challenge_continuity',
    'sinjira_v25_0_device_key_privacy_and_trust_hardening',
    'sinjira_v25_conscience_vault_audit_session_index',
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
    return '\n'.join(raw for raw in text.splitlines() if not raw.strip().startswith('#'))


def trigger_keys(block: str) -> set[str]:
    keys = set()
    for line in block.splitlines()[1:]:
        match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line)
        if match:
            keys.add(match.group(1))
    return keys


def step_blocks(text: str) -> dict[str, str]:
    matches = list(re.finditer(r'(?m)^      - name: (.+)$', text))
    result = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1).strip()] = text[match.start():end]
    return result


def main() -> int:
    if not WORKFLOW.exists():
        raise AssertionError(f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')

    workflow = WORKFLOW.read_text('utf-8', errors='strict')
    triggers = top_level_block(workflow, 'on:\n', '\npermissions:')
    active = active_text(workflow)

    observed_triggers = trigger_keys(triggers)
    if observed_triggers != {'workflow_dispatch'}:
        raise AssertionError(
            'La vérification production V25 doit rester strictement manuelle: '
            f'triggers observés={sorted(observed_triggers)}'
        )

    require(workflow, [
        'name: SINJIRA V25 — Vérification production coffre',
        'Saisir exactement VERIFY-SINJIRA-V25',
        'test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25"',
        'environment: production',
        'EXPECTED_REMOTE_BASELINE: "20260901002241"',
        'EXPECTED_REMOTE_BASELINE_NAME: sinjira_v24_5_54_fracture_contribution_atomic_finalize',
        'ref: main',
        'persist-credentials: false',
        "python-version: '3.12.14'",
        'check-latest: false',
        "--proto '=https'",
        '--tlsv1.2',
        '--request GET',
        MANAGEMENT_URL,
        '--header "Authorization: Bearer $SUPABASE_ACCESS_TOKEN"',
        'MIGRATION_HISTORY="$RUNNER_TEMP/v25-migrations.json" python3 - <<\'PY\'',
        'after_names[:len(required)] != required',
        FUNCTIONS_CMD,
        "grep -Fq 'conscience-vault'",
        'Aucune migration, aucun secret et aucune Edge Function',
    ], 'contrat de vérification post-déploiement V25')

    for name in EXPECTED_NAMES:
        require(workflow, [f'"{name}"'], f'nom distant V25 {name}')

    forbid(active, [
        'SUPABASE_PROJECT_REF:',
        'SUPABASE_MANAGEMENT_API:',
        '$SUPABASE_PROJECT_REF',
        '$SUPABASE_MANAGEMENT_API',
        '--request POST',
        '--request PUT',
        '--request PATCH',
        '--request DELETE',
        '--data',
        '--form',
        '--upload-file',
        '--location',
        '--proxy',
        '--connect-to',
        '--resolve',
        'supabase functions deploy',
        'supabase db push',
        'supabase link',
        'supabase secrets set',
        'supabase migration repair',
        '--linked',
        '--no-verify-jwt',
        'continue-on-error:',
        'set -x',
    ], 'la vérification post-déploiement doit rester en lecture seule et non redirigeable')

    token_lines = [line for line in workflow.splitlines() if 'secrets.SUPABASE_ACCESS_TOKEN' in line]
    if len(token_lines) != 2 or any(line != TOKEN_LINE for line in token_lines):
        raise AssertionError('Le token Supabase doit être borné à exactement deux env d’étape.')

    steps = step_blocks(workflow)
    confirmation = steps.get('Vérifier la confirmation', '')
    download = steps.get("Télécharger l'historique V25 en lecture seule", '')
    parse = steps.get("Valider l'historique V25 sans secret", '')
    inventory = steps.get('Vérifier la présence de conscience-vault en lecture seule', '')
    if not all((confirmation, download, parse, inventory)):
        raise AssertionError('Étapes de frontière production V25 incomplètes.')
    if 'SUPABASE_ACCESS_TOKEN' in confirmation or 'secrets.' in confirmation:
        raise AssertionError('La confirmation ne doit pas recevoir le token Supabase.')
    if TOKEN_LINE not in download or TOKEN_LINE not in inventory:
        raise AssertionError('Les deux lectures distantes doivent recevoir chacune leur token borné.')
    if 'SUPABASE_ACCESS_TOKEN' in parse or 'secrets.' in parse:
        raise AssertionError('Le parsing de l’historique doit rester sans secret.')

    if active.count(MANAGEMENT_URL) != 1 or active.count('curl ') != 1:
        raise AssertionError('Le workflow doit effectuer une seule lecture HTTP vers l’endpoint migrations exact.')
    remote_supabase = [line.strip() for line in active.splitlines() if line.strip().startswith('supabase ')]
    if remote_supabase != [FUNCTIONS_CMD]:
        raise AssertionError(f'Inventaire Supabase inattendu: {remote_supabase}')

    history = active.find(MANAGEMENT_URL)
    parsing = active.find("Valider l'historique V25 sans secret")
    functions = active.find(FUNCTIONS_CMD)
    if min(history, parsing, functions) < 0 or not history < parsing < functions:
        raise AssertionError('Ordre attendu: GET migrations, parsing sans secret, puis inventaire Edge.')

    print(
        'OK vérification V25: manuel uniquement, GET HTTPS Supabase exact, '
        'token borné à deux lectures, parsing sans secret, cinq migrations ordonnées et conscience-vault inventoriée.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
