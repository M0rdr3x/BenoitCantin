#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-security-risk-v25.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_CLI_SHA = '3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
SUPABASE_VERSION = '2.111.0'


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def action_targets(text: str) -> list[str]:
    targets: list[str] = []
    for line in text.splitlines():
        match = re.match(r'^\s*(?:-\s*)?uses:\s+(\S+)', line)
        if match:
            targets.append(match.group(1))
    return targets


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'permissions:\n  contents: read' in text, 'permissions.contents doit rester read')
    require(errors, 'contents: write' not in text, 'permission contents:write interdite')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'aucun secret GitHub ne doit être référencé')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'runner Ubuntu 24.04 explicite requis')
    require(errors, 'ubuntu-latest' not in text, 'ubuntu-latest interdit')
    require(errors, 'timeout-minutes: 20' in text, 'timeout de 20 minutes requis')

    require(errors, 'pull_request:\n' in text, 'déclencheur pull_request requis')
    require(errors, 'push:\n    branches: [main]' in text, 'déclencheur push sur main requis tant que la protection serveur n’est pas prouvée')
    require(errors, 'workflow_dispatch:\n' in text, 'déclencheur manuel requis')
    require(errors, "- 'scripts/validate_security_risk_workflow_security.py'" in text, 'le contrat doit faire partie des chemins déclencheurs')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 1, 'checkout doit être épinglé au SHA vérifié')
    require(errors, text.count('persist-credentials: false') == 1, 'checkout doit désactiver les credentials persistés')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, text.count(f'uses: supabase/setup-cli@{SETUP_CLI_SHA}') == 1, 'setup-cli doit être épinglé au SHA vérifié')
    require(errors, f'version: {SUPABASE_VERSION}' in text, 'version Supabase CLI exacte requise')
    require(errors, 'github-token: ${{ github.token }}' in text, 'setup-cli doit utiliser uniquement le GITHUB_TOKEN éphémère')

    targets = action_targets(text)
    require(errors, len(targets) == 2, f'nombre inattendu d’actions réutilisables: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'référence d’action non immuable: {target}')

    require(errors, 'supabase db start' in text, 'démarrage Supabase local absent')
    require(errors, 'supabase test db supabase/tests/security_risk_model_v25.test.sql --local' in text, 'pgTAP local V25 absent')
    require(errors, 'supabase stop --no-backup' in text, 'arrêt local Supabase absent')
    require(errors, 'python scripts/validate_security_risk_workflow_security.py --self-test' in text, 'auto-tests du contrat absents')
    require(errors, 'python scripts/validate_security_risk_workflow_security.py\n' in text, 'validation du contrat absente')

    forbidden_remote = ('--linked', 'supabase db push', 'supabase functions deploy', 'supabase link ', 'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD')
    for marker in forbidden_remote:
        require(errors, marker not in text, f'opération ou secret distant interdit dans ce workflow local: {marker}')
    return errors


def run_self_tests(text: str) -> None:
    cases = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-cli mobile': text.replace(f'supabase/setup-cli@{SETUP_CLI_SHA}', 'supabase/setup-cli@v2', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'secret ajouté': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}', 1),
        'runner mobile': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1),
        'CLI latest': text.replace(f'version: {SUPABASE_VERSION}', 'version: latest', 1),
        'push main retiré': text.replace('  push:\n    branches: [main]\n', '', 1),
        'commande distante': text.replace('supabase db start', 'supabase db start --linked', 1),
        'pgTAP retiré': text.replace('          supabase test db supabase/tests/security_risk_model_v25.test.sql --local\n', '', 1),
    }
    for name, mutated in cases.items():
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test risk-model CI: mutation non détectée: {name}')
    print(f'OK auto-tests risk-model CI: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit(f'ERREUR risk-model CI: workflow absent: {WORKFLOW.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        return 0
    errors = validate_text(text)
    if errors:
        for error in errors:
            print(f'ERREUR sécurité risk-model CI: {error}')
        return 1
    print('OK sécurité risk-model CI: dépendances immuables, Supabase local uniquement, couverture PR/push main et aucun secret production.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
