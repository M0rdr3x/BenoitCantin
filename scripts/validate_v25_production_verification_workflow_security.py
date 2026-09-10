#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-v25-production-deploy.yml'
HARNESS = ROOT / '.github' / 'workflows' / 'sinjira-consciousness-vault-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_CLI = 'supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
ALLOWED_USES = {CHECKOUT, SETUP_PYTHON, SETUP_CLI}
SELF_TEST = 'python3 scripts/validate_v25_production_verification_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_v25_production_verification_workflow_security.py'
SELF_TEST_LINE = f'        run: {SELF_TEST}'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}'
TOKEN_LINE = '          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}'
MANAGEMENT_URL = 'https://api.supabase.com/v1/projects/gpvivleexywljowcqkru/database/migrations'
FUNCTIONS_CMD = 'supabase functions list --project-ref "gpvivleexywljowcqkru" | tee "$functions_list"'

EXPECTED_NAMES = (
    'sinjira_v25_0_security_risk_model_convergence',
    'sinjira_v25_0_personal_consciousness_vault',
    'sinjira_v25_0_conscience_vault_challenge_continuity',
    'sinjira_v25_0_device_key_privacy_and_trust_hardening',
    'sinjira_v25_conscience_vault_audit_session_index',
)

STATIC_CHECKS = (
    'python3 scripts/validate_conscience_vault_edge_v25.py',
    'python3 scripts/validate_edge_function_inventory.py',
    'python3 scripts/validate_production_schema_manifest.py',
    'python3 scripts/validate_v25_production_deploy_workflow.py',
    SELF_CHECK,
)

FORBIDDEN_ACTIVE = (
    'SUPABASE_PROJECT_REF:',
    'SUPABASE_MANAGEMENT_API:',
    '$SUPABASE_PROJECT_REF',
    '$SUPABASE_MANAGEMENT_API',
    'SUPABASE_DB_PASSWORD',
    'SERVICE_ROLE_KEY',
    'SUPABASE_SERVICE_ROLE_KEY',
    'supabase db push',
    'supabase functions deploy',
    'supabase migration repair',
    'supabase secrets set',
    'supabase link',
    'supabase db reset',
    '--linked',
    '--no-verify-jwt',
    '--request POST',
    '--request PUT',
    '--request PATCH',
    '--request DELETE',
    '-X POST',
    '-X PUT',
    '-X PATCH',
    '-X DELETE',
    '--data ',
    '--data=',
    '--data-binary',
    '--form ',
    '--form=',
    '--upload-file',
    '--location',
    '--location-trusted',
    '--proxy ',
    '--proxy=',
    '--preproxy',
    '--connect-to',
    '--resolve',
    'continue-on-error:',
    'set -x',
    'gh api',
    'wget ',
    'git push',
    'http://',
)


def fail(message: str) -> None:
    raise ValueError(message)


def block(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    if begin < 0:
        fail(f'section absente: {start.strip()}')
    finish = text.find(end, begin + len(start))
    if finish < 0:
        fail(f'fin de section absente: {end.strip()}')
    return text[begin:finish]


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def trigger_keys(on_block: str) -> set[str]:
    keys: set[str] = set()
    for line in on_block.splitlines()[1:]:
        match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line)
        if match:
            keys.add(match.group(1))
    return keys


def step_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r'(?m)^      - name: (.+)$', text))
    out: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        out.append((match.group(1).strip(), text[match.start():end]))
    return out


def step_map(text: str) -> dict[str, str]:
    return {name: body for name, body in step_blocks(text)}


def exact_line_count(text: str, line: str) -> int:
    return text.splitlines().count(line)


def validate_workflow(text: str) -> None:
    triggers = block(text, 'on:\n', '\npermissions:')
    if trigger_keys(triggers) != {'workflow_dispatch'}:
        fail('vérification production non strictement manuelle')

    required = (
        'name: SINJIRA V25 — Vérification production coffre',
        'description: "Saisir exactement VERIFY-SINJIRA-V25"',
        'test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25"',
        'permissions:\n  contents: read',
        'cancel-in-progress: false',
        'runs-on: ubuntu-24.04',
        'timeout-minutes: 20',
        'environment: production',
        'EXPECTED_REMOTE_BASELINE: "20260901002241"',
        'EXPECTED_REMOTE_BASELINE_NAME: sinjira_v24_5_54_fracture_contribution_atomic_finalize',
        'test "$GITHUB_REF" = "refs/heads/main"',
        'ref: main',
        'persist-credentials: false',
        'fetch-depth: 1',
        "python-version: '3.12.14'",
        'check-latest: false',
        'version: 2.111.0',
        "--proto '=https'",
        '--tlsv1.2',
        '--request GET',
        MANAGEMENT_URL,
        '--header "Authorization: Bearer $SUPABASE_ACCESS_TOKEN"',
        'MIGRATION_HISTORY="$RUNNER_TEMP/v25-migrations.json" python3 - <<\'PY\'',
        'after_names[:len(required)] != required',
        FUNCTIONS_CMD,
        "grep -Fq 'conscience-vault'",
        'Vérification V25 terminée en lecture seule.',
        "Aucune migration, aucun secret et aucune Edge Function n'ont été modifiés par ce workflow.",
    )
    for marker in required:
        if marker not in text:
            fail(f'contrat production absent: {marker}')

    if exact_line_count(text, '    environment: production') != 1:
        fail('environment production doit rester une frontière de job unique')
    if exact_line_count(text, '          ref: main') != 1:
        fail('checkout production doit forcer exactement ref: main')
    if exact_line_count(text, '          persist-credentials: false') != 1:
        fail('checkout doit désactiver les credentials exactement une fois')

    uses = re.findall(r'(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)', text)
    unexpected = [value for value in uses if value not in ALLOWED_USES]
    if unexpected:
        fail('action réutilisable non autorisée/non épinglée: ' + ', '.join(unexpected))
    if uses.count(CHECKOUT) != 1 or uses.count(SETUP_PYTHON) != 1 or uses.count(SETUP_CLI) != 1:
        fail('checkout, setup-python et setup-cli doivent chacun apparaître exactement une fois')

    active = active_text(text)
    for marker in FORBIDDEN_ACTIVE:
        if marker in active:
            fail(f'opération distante ou affaiblissement interdit: {marker}')

    token_lines = [line for line in text.splitlines() if 'secrets.SUPABASE_ACCESS_TOKEN' in line]
    if len(token_lines) != 2:
        fail('SUPABASE_ACCESS_TOKEN doit être référencé exactement dans deux env d’étape')
    if any(line != TOKEN_LINE for line in token_lines):
        fail('SUPABASE_ACCESS_TOKEN doit rester strictement dans un env d’étape')
    sanitized = text.replace(TOKEN_LINE, '')
    if '${{ secrets.' in sanitized:
        fail('secret GitHub supplémentaire interdit')

    steps = step_map(text)
    required_steps = (
        'Refuser les lancements hors main',
        'Vérifier la confirmation',
        'Checkout de main',
        'Configurer Python',
        'Vérifier les contrats statiques V25',
        "Télécharger l'historique V25 en lecture seule",
        "Valider l'historique V25 sans secret",
        "Installer Supabase CLI pour l'inventaire Edge",
        'Vérifier la présence de conscience-vault en lecture seule',
        'Résumé lecture seule',
    )
    for name in required_steps:
        if name not in steps:
            fail(f'étape obligatoire absente: {name}')

    confirmation = steps['Vérifier la confirmation']
    download = steps["Télécharger l'historique V25 en lecture seule"]
    parse = steps["Valider l'historique V25 sans secret"]
    inventory = steps['Vérifier la présence de conscience-vault en lecture seule']

    if 'secrets.' in confirmation or 'SUPABASE_ACCESS_TOKEN' in confirmation:
        fail('la confirmation ne doit recevoir aucun secret production')
    if TOKEN_LINE not in download or TOKEN_LINE not in inventory:
        fail('les deux lectures distantes doivent chacune recevoir leur token dans leur étape')
    if 'secrets.' in parse or 'SUPABASE_ACCESS_TOKEN' in parse:
        fail('le parsing de l’historique doit rester sans secret')
    for name, body in step_blocks(text):
        if 'uses:' in body and ('secrets.' in body or 'SUPABASE_ACCESS_TOKEN:' in body):
            fail(f'secret production exposé à une action réutilisable: {name}')
        if 'secrets.SUPABASE_ACCESS_TOKEN' in body and name not in {
            "Télécharger l'historique V25 en lecture seule",
            'Vérifier la présence de conscience-vault en lecture seule',
        }:
            fail(f'token production exposé à une étape non autorisée: {name}')

    if active.count('curl ') != 1:
        fail('une seule commande curl distante est autorisée')
    if active.count(MANAGEMENT_URL) != 1:
        fail('l’historique doit cibler exactement une fois l’URL Supabase autorisée')
    if active.count('https://') != 1:
        fail('aucun autre endpoint HTTPS n’est autorisé dans le workflow production')
    for marker in (
        'curl --fail-with-body --silent --show-error \\',
        "--proto '=https' \\",
        '--tlsv1.2 \\',
        '--request GET \\',
        '--header "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \\',
        "--header 'Accept: application/json' \\",
        '--output "$history" \\',
        f'"{MANAGEMENT_URL}"',
    ):
        if marker not in download:
            fail(f'contrainte HTTP manquante dans le téléchargement: {marker}')

    remote_supabase = [line.strip() for line in active.splitlines() if line.strip().startswith('supabase ')]
    if remote_supabase != [FUNCTIONS_CMD]:
        fail(f'commandes Supabase distantes inattendues: {remote_supabase}')
    if inventory.count(FUNCTIONS_CMD) != 1:
        fail('inventaire Edge doit cibler exactement le projet attendu')

    for marker in STATIC_CHECKS:
        if marker not in text:
            fail(f'validateur statique absent: {marker}')
    for name in EXPECTED_NAMES:
        if f'"{name}"' not in text:
            fail(f'migration V25 attendue absente: {name}')

    indexes = [text.find(name) for name in required_steps]
    if min(indexes) < 0 or indexes != sorted(indexes):
        fail('ordre des barrières production non respecté')


def validate_harness(text: str) -> None:
    pr = block(text, '  pull_request:', '  push:')
    push = block(text, '  push:', '  workflow_dispatch:')
    for marker in (
        "'scripts/validate_v25_production_verification_workflow_security.py'",
        "'scripts/validate_v25_production_deploy_workflow.py'",
        "'.github/workflows/sinjira-v25-production-deploy.yml'",
    ):
        if marker not in pr or marker not in push:
            fail(f'contrat production non couvert PR+push par le Coffre: {marker}')
    if exact_line_count(text, SELF_TEST_LINE) != 1:
        fail('auto-test du vérificateur production absent ou dupliqué dans la CI locale')
    if exact_line_count(text, SELF_CHECK_LINE) != 1:
        fail('contrat réel du vérificateur production absent ou dupliqué dans la CI locale')
    if text.index(SELF_TEST_LINE) > text.index(SELF_CHECK_LINE):
        fail('auto-test production doit précéder le contrat réel')
    if 'python3 scripts/validate_v25_production_deploy_workflow.py' not in text:
        fail('validateur historique production absent de la CI locale')


def validate_pair(workflow: str, harness: str) -> None:
    validate_workflow(workflow)
    validate_harness(harness)


def add_automatic_push(text: str) -> str:
    return text.replace(
        'on:\n  workflow_dispatch:',
        'on:\n  push:\n    branches: [main]\n  workflow_dispatch:',
        1,
    )


def mutate_step(text: str, name: str, old: str, new: str) -> str:
    blocks = step_blocks(text)
    for step_name, body in blocks:
        if step_name == name and old in body:
            return text.replace(body, body.replace(old, new, 1), 1)
    return text


def mutations(workflow: str, harness: str):
    download = "Télécharger l'historique V25 en lecture seule"
    inventory = 'Vérifier la présence de conscience-vault en lecture seule'
    parse = "Valider l'historique V25 sans secret"
    yield 'déclencheur push', add_automatic_push(workflow), harness
    yield 'confirmation description altérée', workflow.replace('Saisir exactement VERIFY-SINJIRA-V25', 'Confirmer', 1), harness
    yield 'confirmation test contournée', workflow.replace('test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25"', 'test -n "$VERIFY_CONFIRMATION"', 1), harness
    yield 'permissions écriture', workflow.replace('contents: read', 'contents: write', 1), harness
    yield 'runner latest', workflow.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1), harness
    yield 'environnement production retiré', workflow.replace('    environment: production\n', '', 1), harness
    yield 'checkout mobile', workflow.replace(CHECKOUT, 'actions/checkout@v6', 1), harness
    yield 'setup-python mobile', workflow.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1), harness
    yield 'setup-cli mobile', workflow.replace(SETUP_CLI, 'supabase/setup-cli@v2', 1), harness
    yield 'action inconnue compacte', workflow.replace('    steps:\n', '    steps:\n      - uses: owner/action@v1\n', 1), harness
    yield 'credentials persistés', workflow.replace('persist-credentials: false', 'persist-credentials: true', 1), harness
    yield 'checkout hors main', workflow.replace('          ref: main', '          ref: develop', 1), harness
    yield 'fetch depth modifié', workflow.replace('fetch-depth: 1', 'fetch-depth: 0', 1), harness
    yield 'python large', workflow.replace("python-version: '3.12.14'", "python-version: '3.12'", 1), harness
    yield 'python latest', workflow.replace('check-latest: false', 'check-latest: true', 1), harness
    yield 'cli latest', workflow.replace('version: 2.111.0', 'version: latest', 1), harness
    yield 'baseline modifiée', workflow.replace('EXPECTED_REMOTE_BASELINE: "20260901002241"', 'EXPECTED_REMOTE_BASELINE: "0"', 1), harness
    yield 'hôte API modifié', workflow.replace('https://api.supabase.com/', 'https://example.invalid/', 1), harness
    yield 'projet API modifié', workflow.replace('projects/gpvivleexywljowcqkru/', 'projects/autreprojet/', 1), harness
    yield 'projet inventaire modifié', workflow.replace(FUNCTIONS_CMD, 'supabase functions list --project-ref "autreprojet" | tee "$functions_list"', 1), harness
    yield 'HTTP POST', workflow.replace('--request GET', '--request POST', 1), harness
    yield 'HTTP PUT', workflow.replace('--request GET', '--request PUT', 1), harness
    yield 'HTTP PATCH', workflow.replace('--request GET', '--request PATCH', 1), harness
    yield 'HTTP DELETE', workflow.replace('--request GET', '--request DELETE', 1), harness
    yield 'HTTPS forcé retiré', workflow.replace("            --proto '=https' \\\n", '', 1), harness
    yield 'TLS minimum retiré', workflow.replace('            --tlsv1.2 \\\n', '', 1), harness
    yield 'redirect autorisé', mutate_step(workflow, download, "            --tlsv1.2 \\\n", "            --tlsv1.2 \\\n            --location \\\n"), harness
    yield 'proxy ajouté', mutate_step(workflow, download, "            --tlsv1.2 \\\n", "            --tlsv1.2 \\\n            --proxy https://proxy.invalid \\\n"), harness
    yield 'connect-to ajouté', mutate_step(workflow, download, "            --tlsv1.2 \\\n", "            --tlsv1.2 \\\n            --connect-to api.supabase.com:443:example.invalid:443 \\\n"), harness
    yield 'resolve ajouté', mutate_step(workflow, download, "            --tlsv1.2 \\\n", "            --tlsv1.2 \\\n            --resolve api.supabase.com:443:127.0.0.1 \\\n"), harness
    yield 'HTTP data', mutate_step(workflow, download, "            --request GET \\\n", "            --request GET \\\n            --data '{}' \\\n"), harness
    yield 'second curl', mutate_step(workflow, download, '          curl --fail-with-body', '          curl https://example.invalid\n          curl --fail-with-body'), harness
    yield 'token confirmation', mutate_step(workflow, 'Vérifier la confirmation', '        env:\n', f'        env:\n{TOKEN_LINE}\n'), harness
    yield 'token job-level', workflow.replace('    environment: production\n', '    environment: production\n    env:\n      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n', 1), harness
    yield 'token téléchargement retiré', mutate_step(workflow, download, TOKEN_LINE + '\n', ''), harness
    yield 'token inventaire retiré', mutate_step(workflow, inventory, TOKEN_LINE + '\n', ''), harness
    yield 'token parsing ajouté', mutate_step(workflow, parse, '        shell: bash\n', f'        shell: bash\n        env:\n{TOKEN_LINE}\n'), harness
    yield 'db password', mutate_step(workflow, download, TOKEN_LINE, TOKEN_LINE + '\n          SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}'), harness
    yield 'db push', workflow.replace(FUNCTIONS_CMD, 'supabase db push --linked\n          ' + FUNCTIONS_CMD, 1), harness
    yield 'functions deploy', workflow.replace(FUNCTIONS_CMD, 'supabase functions deploy conscience-vault\n          ' + FUNCTIONS_CMD, 1), harness
    yield 'secrets set', workflow.replace(FUNCTIONS_CMD, 'supabase secrets set TEST=value\n          ' + FUNCTIONS_CMD, 1), harness
    yield 'migration repair', workflow.replace(FUNCTIONS_CMD, 'supabase migration repair 1 --status applied\n          ' + FUNCTIONS_CMD, 1), harness
    yield 'JWT bypass', workflow.replace(FUNCTIONS_CMD, FUNCTIONS_CMD + ' --no-verify-jwt', 1), harness
    yield 'continue on error', workflow.replace('    timeout-minutes: 20', '    timeout-minutes: 20\n    continue-on-error: true', 1), harness
    yield 'shell trace', workflow.replace('set -euo pipefail', 'set -x', 1), harness
    yield 'séquence migration retirée', workflow.replace('after_names[:len(required)] != required', 'False', 1), harness
    yield 'migration attendue retirée', workflow.replace(f'              "{EXPECTED_NAMES[0]}",\n', '', 1), harness
    yield 'contrat historique retiré', workflow.replace('          python3 scripts/validate_v25_production_deploy_workflow.py\n', '', 1), harness
    yield 'contrat sécurité retiré', workflow.replace(f'          {SELF_CHECK}\n', '', 1), harness
    yield 'résumé lecture seule retiré', workflow.replace('Vérification V25 terminée en lecture seule.', 'Vérification terminée.', 1), harness
    yield 'auto-test retiré du harness', workflow, harness.replace(SELF_TEST_LINE + '\n', '        run: echo auto-test-production-retire\n', 1)
    yield 'contrat réel retiré du harness', workflow, harness.replace(SELF_CHECK_LINE + '\n', '        run: echo contrat-production-retire\n', 1)
    yield 'path contrat sécurité retiré du harness', workflow, harness.replace("      - 'scripts/validate_v25_production_verification_workflow_security.py'\n", '', 2)
    yield 'path contrat historique retiré du harness', workflow, harness.replace("      - 'scripts/validate_v25_production_deploy_workflow.py'\n", '', 2)
    yield 'path workflow production retiré du harness', workflow, harness.replace("      - '.github/workflows/sinjira-v25-production-deploy.yml'\n", '', 2)


def self_test(workflow: str, harness: str) -> None:
    validate_pair(workflow, harness)
    missed: list[str] = []
    total = 0
    for name, mutated_workflow, mutated_harness in mutations(workflow, harness):
        total += 1
        if mutated_workflow == workflow and mutated_harness == harness:
            missed.append(f'{name} (mutation sans effet)')
            continue
        try:
            validate_pair(mutated_workflow, mutated_harness)
        except ValueError:
            continue
        missed.append(name)
    if missed:
        raise ValueError('mutations non détectées: ' + ', '.join(missed))
    print(f'OK: {total}/{total} mutations critiques détectées')


def main() -> int:
    if not WORKFLOW.is_file() or not HARNESS.is_file():
        print('ECHEC CI vérification production V25: workflow ou harness absent', file=sys.stderr)
        return 1
    workflow = WORKFLOW.read_text('utf-8')
    harness = HARNESS.read_text('utf-8')
    try:
        if '--self-test' in sys.argv[1:]:
            self_test(workflow, harness)
        else:
            validate_pair(workflow, harness)
            print(
                'OK CI vérification production V25: manuel main-only, actions/runtimes épinglés, '
                'GET HTTPS Supabase exact, token borné à deux étapes de lecture et parsing sans secret.'
            )
    except ValueError as exc:
        print(f'ECHEC CI vérification production V25: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())