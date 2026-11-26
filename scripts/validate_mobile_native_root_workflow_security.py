#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys
from validate_mobile_locked_dependencies import verified_bytes

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-mobile-native.yml'
LOCKFILE = ROOT / 'mobile-native' / 'package-lock.json'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE = 'actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38'
SELF_TEST = 'python3 scripts/validate_mobile_native_root_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_mobile_native_root_workflow_security.py'
INSTALL = 'npm ci --ignore-scripts --no-audit --no-fund'
AUDIT = 'npm audit --json --package-lock-only --ignore-scripts'
SNAPSHOT = 'python3 ../scripts/validate_mobile_locked_dependencies.py --manifest package.json --lock package-lock.json'
HISTORICAL = (
    'npm run validate:vault',
    'npm run test:navigation-guard',
    'npm run test:deep-link-normalizer',
    'npm run test:notification-navigation',
    'npm run test:push-installation-binding',
    'npm run typecheck',
)


def fail(message: str) -> None:
    raise ValueError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def validate_text(text: str) -> None:
    active = active_text(text)

    require('pull_request:\n    branches: [ main ]' in text, 'Les PR doivent rester ciblées vers main.')
    require('push:\n    branches: [ main ]' in text, 'Le push main doit rester couvert tant que #135 n’est pas prouvé.')
    require(text.count("      - 'mobile-native/**'") == 2, 'mobile-native/** doit couvrir PR et push.')
    require(text.count("      - 'scripts/validate_mobile_native_root_workflow_security.py'") == 2, 'Le validateur CI doit couvrir PR et push.')
    require(text.count("      - '.github/workflows/sinjira-mobile-native.yml'") == 2, 'Le workflow doit se couvrir lui-même sur PR et push.')

    require('permissions:\n  contents: read' in text, 'permissions.contents doit rester en lecture seule.')
    require('runs-on: ubuntu-24.04' in text, 'Le runner doit rester figé sur Ubuntu 24.04.')
    require('ubuntu-latest' not in active, 'ubuntu-latest est interdit.')
    require('timeout-minutes: 10' in text, 'Le timeout de 10 minutes est obligatoire.')
    require('working-directory: mobile-native' in text, 'Le répertoire mobile-native doit rester le défaut des commandes applicatives.')

    for action in (CHECKOUT, SETUP_PYTHON, SETUP_NODE):
        require(f'uses: {action}' in text, f'Action épinglée absente: {action}')
    uses = [line.strip().split('uses:', 1)[1].strip().split()[0] for line in active.splitlines() if line.strip().startswith('uses: ')]
    require(uses == [CHECKOUT, SETUP_PYTHON, SETUP_NODE], f'Actions inattendues ou ordre modifié: {uses}')
    for action in uses:
        require(re.search(r'@[0-9a-f]{40}$', action) is not None, f'Action non immuable: {action}')

    require('persist-credentials: false' in text, 'Les credentials Git ne doivent pas être persistés.')
    require("python-version: '3.12.14'" in text, 'Python doit rester figé à 3.12.14.')
    require("node-version: '22.23.2'" in text, 'Node doit rester figé à 22.23.2.')
    require('package-manager-cache: false' in active, 'Cache implicite interdit.')
    require(re.search(r'(?m)^\s+cache:', active) is None, 'Cache npm explicite interdit.')
    require('cache-dependency-path:' not in active, 'Aucun faux chemin de lockfile ne doit être configuré.')

    require(f'run: {SELF_TEST}' in text, 'L’auto-test du contrat CI est absent.')
    require(f'run: {SELF_CHECK}' in text, 'La vérification du contrat CI est absente.')
    require(active.count(INSTALL) == 1, 'npm ci verrouillé obligatoire.')
    require('npm install ' not in active, 'Installation flottante interdite.')
    require(active.count(AUDIT) == 1 and active.count(SNAPSHOT) == 4, 'Audit et contrôles de snapshot obligatoires.')
    require(active.count('--registry=https://registry.npmjs.org/') == 2, 'Registre officiel obligatoire.')
    require(active.count('env -i PATH="$PATH" HOME=') == 2, 'Environnement npm isolé obligatoire.')
    require('--audit "$audit_dir/audit.json" --audit-exit "$status"' in active, 'Résultat audit obligatoire.')
    require("    - cron: '31 9 * * 1'" in active, 'Audit périodique obligatoire.')
    require("      - 'scripts/validate_mobile_locked_dependencies.py'" in active and active.count("      - 'scripts/validate_mobile_locked_dependencies.py'") == 2, 'Couverture du validateur lock requise.')
    require(active.count("      - 'scripts/validate_mobile_lock_candidate.py'") == 2, 'Couverture du parseur lock requise.')
    require("createFingerprintAsync(process.cwd())" in active and "assert.equal(meta.version, '11.0.9')" in active, 'Compatibilité Expo obligatoire.')
    for command in HISTORICAL:
        require(f'run: {command}' in text, f'Validation historique absente: {command}')

    order = [
        text.find(f'run: {SELF_TEST}'),
        text.find(f'run: {SELF_CHECK}\n'),
        text.find(SNAPSHOT),
        text.find(AUDIT),
        text.find(INSTALL),
        *(text.find(f'run: {command}') for command in HISTORICAL),
    ]
    require(min(order) >= 0 and order == sorted(order), 'Ordre attendu: garde CI, installation, vault, liaison push, typecheck.')

    forbidden = (
        '${{ secrets.',
        'contents: write',
        'persist-credentials: true',
        'environment: production',
        'SUPABASE_ACCESS_TOKEN',
        'SUPABASE_DB_PASSWORD',
        'SERVICE_ROLE_KEY',
        'supabase db push',
        'supabase functions deploy',
        'supabase secrets set',
        'supabase migration repair',
        'supabase link',
        '--linked',
        '--no-verify-jwt',
        'curl ',
        'wget ',
        'gh api',
        'git push',
        'continue-on-error: true',
        'set -x',
    )
    found = [marker for marker in forbidden if marker in active]
    require(not found, f'Écriture, secret, réseau distant ou contournement interdit: {found}')


def validate_repo_state() -> None:
    require(
        LOCKFILE.is_file() and not LOCKFILE.is_symlink(),
        'Lockfile approuvé obligatoire.',
    )
    manifest = LOCKFILE.with_name('package.json')
    require(manifest.is_file() and not manifest.is_symlink(), 'Manifest régulier obligatoire.')
    verified_bytes(manifest.read_bytes(), LOCKFILE.read_bytes())


def mutation_cases(text: str) -> tuple[tuple[str, str], ...]:
    node_version = "          node-version: '22.23.2'\n"
    return (
        ('runner mobile', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)),
        ('checkout mutable', text.replace(CHECKOUT, 'actions/checkout@v4', 1)),
        ('setup-python mutable', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)),
        ('setup-node mutable', text.replace(SETUP_NODE, 'actions/setup-node@v4', 1)),
        ('Python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ('Node large', text.replace("node-version: '22.23.2'", "node-version: '22'", 1)),
        ('credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)),
        ('permissions write', text.replace('contents: read', 'contents: write', 1)),
        ('cache npm ajouté', text.replace(node_version, node_version + '          cache: npm\n', 1)),
        ('faux lockfile cache', text.replace(node_version, node_version + '          cache: npm\n          cache-dependency-path: mobile-native/package-lock.json\n', 1)),
        ('scripts npm réactivés', text.replace(INSTALL, 'npm install --no-audit --no-fund', 1)),
        ('timeout retiré', text.replace('    timeout-minutes: 10\n', '', 1)),
        ('secret injecté', text.replace('    steps:\n', '    steps:\n      - run: echo "${{ secrets.SUPABASE_ACCESS_TOKEN }}"\n', 1)),
        ('production injectée', text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    environment: production\n', 1)),
        ('accès HTTP', text.replace('      - name: Vérifier TypeScript\n', '      - run: curl https://example.com\n\n      - name: Vérifier TypeScript\n', 1)),
        ('push Git', text.replace('      - name: Vérifier TypeScript\n', '      - run: git push origin HEAD:main\n\n      - name: Vérifier TypeScript\n', 1)),
        ('continue-on-error', text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    continue-on-error: true\n', 1)),
        ('set -x', text.replace('      - name: Vérifier TypeScript\n', '      - run: set -x\n\n      - name: Vérifier TypeScript\n', 1)),
        ('push main retiré', text.replace('  push:\n    branches: [ main ]\n', '  push:\n    branches: [ mobile ]\n', 1)),
        ('chemin mobile retiré', text.replace("      - 'mobile-native/**'\n", '', 1)),
        ('chemin garde retiré', text.replace("      - 'scripts/validate_mobile_native_root_workflow_security.py'\n", '', 1)),
        ('auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '', 1)),
        ('contrat retiré', text.replace(f'        run: {SELF_CHECK}\n', '', 1)),
        ('vault retiré', text.replace(f'        run: {HISTORICAL[0]}\n', '', 1)),
        ('liaison push retirée', text.replace(f'        run: {HISTORICAL[4]}\n', '', 1)),
        ('typecheck retiré', text.replace(f'        run: {HISTORICAL[5]}\n', '', 1)),
        ('navigation externe retirée', text.replace(f'        run: {HISTORICAL[1]}\n', '', 1)),
        ('liens profonds retirés', text.replace(f'        run: {HISTORICAL[2]}\n', '', 1)),
        ('notifications retirées', text.replace(f'        run: {HISTORICAL[3]}\n', '', 1)),
        ('audit retiré', text.replace(AUDIT, 'echo audit', 1)),
        ('snapshot retiré', text.replace(SNAPSHOT, 'echo snapshot', 1)),
        ('registre remplacé', text.replace('https://registry.npmjs.org/', 'https://example.org/', 1)),
        ('environnement non isolé', text.replace('env -i PATH="$PATH" HOME=', 'env PATH="$PATH" HOME=', 1)),
        ('cache implicite', text.replace('package-manager-cache: false', 'package-manager-cache: true', 1)),
        ('empreinte Expo retirée', text.replace('createFingerprintAsync(process.cwd())', 'null', 1)),
        ('audit périodique retiré', text.replace("    - cron: '31 9 * * 1'", "    - cron: '0 0 1 * *'", 1)),
    )


def self_test(text: str) -> None:
    validate_text(text)
    cases = mutation_cases(text)
    for name, mutated in cases:
        require(mutated != text, f'Mutation inopérante: {name}')
        try:
            validate_text(mutated)
        except ValueError:
            continue
        fail(f'Mutation critique non détectée: {name}')
    print(f'OK: {len(cases)}/{len(cases)} mutations critiques détectées')


def main() -> int:
    require(WORKFLOW.is_file(), f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if '--self-test' in sys.argv[1:]:
        self_test(text)
        return 0
    validate_text(text)
    validate_repo_state()
    print(
        'OK mobile natif racine: runner/Python/Node/actions immuables, Git en lecture seule, '
        'lockfile revu, npm ci, audit zéro, scripts npm désactivés et aucun cache.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
