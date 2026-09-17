#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-parallel-user-rpc-v24-5-16.yml'

CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'
SELF_TEST = 'python scripts/validate_parallel_user_rpc_workflow_security.py --self-test'
META = 'python scripts/validate_parallel_user_rpc_workflow_security.py'
PARALLEL = 'python scripts/validate_parallel_user_rpc_v24_5_16.py'
SOCIAL = 'python scripts/validate_social_user_rpc_v24_5_15.py'
PARALLEL_ADMIN = 'python scripts/validate_parallel_world_admin_v24_4_92.py'
SITE = 'python scripts/validate_site.py'
SUPABASE = 'python scripts/validate_supabase.py'
FREE_ONLY = 'python scripts/validate_free_only_mode.py'
LEDGER = 'python scripts/validate_production_migration_ledger.py'
MANIFEST = 'python scripts/validate_production_schema_manifest.py'
TRIGGER = "      - 'scripts/validate_parallel_user_rpc_workflow_security.py'\n"
FORBIDDEN = ('supabase db push', 'supabase functions deploy', 'supabase secrets set', 'supabase link')


def validate_text(text: str) -> list[str]:
    errors: list[str] = []

    def need(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    need('permissions:\n  contents: read' in text, 'permissions.contents doit rester read')
    need('contents: write' not in text, 'permission contents:write interdite')
    need(re.search(r'\$\{\{\s*secrets\.', text) is None, 'aucun secret GitHub ne doit être référencé')
    need('pull_request_target:' not in text, 'pull_request_target interdit sur cette frontière')
    need('runs-on: ubuntu-24.04' in text, 'runner Ubuntu 24.04 exact requis')
    need('ubuntu-latest' not in text, 'ubuntu-latest interdit')
    need('timeout-minutes: 10' in text, 'timeout de 10 minutes requis')
    need(text.count(f'actions/checkout@{CHECKOUT_SHA}') == 1, 'checkout SHA exact requis')
    need(text.count(f'actions/setup-python@{SETUP_PYTHON_SHA}') == 1, 'setup-python SHA exact requis')
    need(text.count('persist-credentials: false') == 1, 'credentials checkout non persistés requis')
    need('persist-credentials: true' not in text, 'persist-credentials=true interdit')
    need(f"python-version: '{PYTHON_VERSION}'" in text, 'Python exact requis')
    need('continue-on-error: true' not in text, 'continue-on-error=true interdit')
    need('if: always()' not in text, 'if: always() interdit sur les preuves bloquantes')

    actions = re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$', text, flags=re.MULTILINE)
    need(len(actions) == 2, f'nombre inattendu d’actions réutilisables: {len(actions)}')
    for action in actions:
        need(re.search(r'@[0-9a-f]{40}$', action) is not None, f'action non immuable: {action}')

    required = (
        SELF_TEST, META, PARALLEL, SOCIAL, PARALLEL_ADMIN, SITE, SUPABASE, FREE_ONLY, LEDGER, MANIFEST,
    )
    for command in required:
        need(command in text, f'commande requise absente: {command}')
        need(text.count(f'        run: {command}\n') == 1, f'commande doit rester directe et unique: {command}')

    positions = [text.find(command) for command in (
        PARALLEL, SOCIAL, PARALLEL_ADMIN, SITE, SUPABASE, FREE_ONLY, LEDGER, MANIFEST,
    )]
    need(all(position >= 0 for position in positions), 'preuves locales et production doivent toutes être présentes')
    need(
        positions == sorted(positions),
        'ordre requis: Monde parallèle -> social historique -> admin historique -> site -> Supabase -> mode gratuit -> ledger -> manifeste',
    )

    need(text.count(TRIGGER) == 1, 'le méta-garde doit déclencher le workflow')
    for command in FORBIDDEN:
        need(command not in text, f'commande production distante interdite: {command}')

    return errors


def self_test(text: str) -> None:
    free_step = '\n      - name: Mode gratuit et services externes\n' + f'        run: {FREE_ONLY}\n'
    manifest_step = '\n      - name: Manifeste du schéma production\n' + f'        run: {MANIFEST}\n'
    free_after_production = text.replace(free_step, '', 1).replace(manifest_step, manifest_step + free_step, 1)

    mutations = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'runner mobile': text.replace('ubuntu-24.04', 'ubuntu-latest', 1),
        'python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'secret ajouté': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      BAD: ${{ secrets.BAD }}', 1),
        'pull_request_target ajouté': text.replace('  pull_request:\n', '  pull_request_target:\n', 1),
        'auto-test retiré': text.replace(f'        run: {SELF_TEST}\n', '', 1),
        'métagarde retiré': text.replace(f'        run: {META}\n', '', 1),
        'contrat Monde parallèle retiré': text.replace(f'        run: {PARALLEL}\n', '', 1),
        'historique social retiré': text.replace(f'        run: {SOCIAL}\n', '', 1),
        'mode gratuit retiré': text.replace(f'        run: {FREE_ONLY}\n', '', 1),
        'mode gratuit repoussé après production': free_after_production,
        'ledger retiré': text.replace(f'        run: {LEDGER}\n', '', 1),
        'manifeste retiré': text.replace(f'        run: {MANIFEST}\n', '', 1),
        'continue-on-error ajouté': text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    continue-on-error: true\n', 1),
        'if always ajouté': text.replace('      - name: Ledger production\n', '      - name: Ledger production\n        if: always()\n', 1),
        'commande db push': text + '\n# supabase db push\n',
        'déclencheur métagarde retiré': text.replace(TRIGGER, '', 1),
    }

    source_errors = validate_text(text)
    if source_errors:
        raise SystemExit('ERREUR auto-test workflow Monde parallèle utilisateur: workflow source invalide: ' + '; '.join(source_errors))

    for label, mutated in mutations.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test workflow Monde parallèle utilisateur: mutation sans effet: {label}')
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test workflow Monde parallèle utilisateur: mutation non détectée: {label}')

    print(f'OK auto-test workflow Monde parallèle utilisateur: {len(mutations)}/{len(mutations)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide le durcissement du workflow RPC Monde parallèle utilisateur.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    if not WORKFLOW.is_file():
        print(f'ÉCHEC workflow Monde parallèle utilisateur: fichier absent: {WORKFLOW.relative_to(ROOT)}')
        return 1

    text = WORKFLOW.read_text('utf-8', errors='strict')
    if args.self_test:
        self_test(text)
        return 0

    errors = validate_text(text)
    if errors:
        print(f'ÉCHEC workflow Monde parallèle utilisateur: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print(
        'OK workflow Monde parallèle utilisateur: actions/runtimes immuables, credentials non persistés, '
        'preuves Monde parallèle/sociales et mode gratuit avant ledger/manifeste production bloquants.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
