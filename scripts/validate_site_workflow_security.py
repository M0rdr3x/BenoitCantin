#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/validate-site.yml'
PREVIEW_WORKFLOW = ROOT / '.github/workflows/validate-netlify-preview.yml'
PRODUCTION_WORKFLOW = ROOT / '.github/workflows/validate-web-production.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE_SHA = '249970729cb0ef3589644e2896645e5dc5ba9c38'
PYTHON_VERSION = '3.12.14'
NODE_VERSION = '22.23.2'
V18_SELF = 'python scripts/validate_admin_v18_privacy_security.py --self-test'
V18_VALIDATE = 'python scripts/validate_admin_v18_privacy_security.py'
ADMIN_CONSOLE_SELF = 'python scripts/validate_admin_console_security.py --self-test'
ADMIN_CONSOLE_VALIDATE = 'python scripts/validate_admin_console_security.py'
ADMIN_PRIVATE_READS_SELF = 'python scripts/validate_admin_private_reads_security.py --self-test'
ADMIN_PRIVATE_READS_VALIDATE = 'python scripts/validate_admin_private_reads_security.py'
NETLIFY_PUBLIC_CHECK = 'python3 scripts/build_netlify_public.py --check'
WEB_RELEASE_SCOPE_SELF = 'python3 scripts/validate_web_release_scope.py --self-test'
WEB_RELEASE_SCOPE_VALIDATE = 'python3 scripts/validate_web_release_scope.py'
WEB_RELEASE_HTTP_SELF = 'python3 scripts/validate_web_release_http.py --self-test'
PUBLIC_AI_ASSISTANT_SELF = 'python3 scripts/validate_public_ai_assistant.py --self-test'
PUBLIC_AI_ASSISTANT_VALIDATE = 'python3 scripts/validate_public_ai_assistant.py'
AI_TRANSPARENCY_SELF = 'python3 scripts/validate_ai_transparency.py --self-test'
AI_TRANSPARENCY_VALIDATE = 'python3 scripts/validate_ai_transparency.py'
WEB_RELEASE_SCOPE_IF = "if: github.event_name == 'pull_request' && startsWith(github.head_ref, 'a1/web-release-')"
WEB_RELEASE_VALIDATE_IF = "if: github.event_name != 'pull_request' || github.event.pull_request.draft == false || startsWith(github.head_ref, 'a1/web-release-')"


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


def exact_run_count(text: str, command: str) -> int:
    target = f'run: {command}'
    return sum(1 for line in text.splitlines() if line.strip() == target)


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'permissions:\n  contents: read' in text, 'permissions.contents doit rester read')
    require(errors, "group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}" in text, 'groupe concurrency PR exact requis')
    require(errors, "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text, 'annulation limitée aux pull requests requise')
    require(errors, 'cancel-in-progress: true' not in text, 'annulation inconditionnelle interdite')
    require(errors, 'contents: write' not in text, 'permission contents:write interdite')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'la validation centrale ne doit référencer aucun secret GitHub')
    require(errors, text.count('runs-on: ubuntu-24.04') == 2, 'les deux jobs doivent utiliser Ubuntu 24.04 explicite')
    require(errors, 'ubuntu-latest' not in text, 'ubuntu-latest interdit pour cette barrière critique')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 2, 'les deux checkouts doivent être épinglés au SHA vérifié')
    require(errors, text.count('persist-credentials: false') == 2, 'les deux checkouts doivent désactiver la persistance des credentials')
    require(errors, text.count('fetch-depth: 0') == 1, 'le job de contrat doit disposer de l’historique Git complet pour le contrôle web-only')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, text.count(f'uses: actions/setup-python@{SETUP_PYTHON_SHA}') == 1, 'setup-python doit être épinglé au SHA vérifié')
    require(errors, text.count(f'uses: actions/setup-node@{SETUP_NODE_SHA}') == 1, 'setup-node doit être épinglé au SHA vérifié')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python exacte requise')
    require(errors, f"node-version: '{NODE_VERSION}'" in text, 'version Node exacte requise')

    targets = action_targets(text)
    require(errors, len(targets) == 4, f'nombre inattendu d’actions réutilisables: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'référence d’action non immuable: {target}')

    require(errors, '  workflow-contract:\n' in text, 'job workflow-contract absent')
    require(errors, 'python3 scripts/validate_site_workflow_security.py --self-test' in text, 'auto-tests du contrat absents')
    require(errors, 'python3 scripts/validate_site_workflow_security.py\n' in text, 'validation du contrat absente')
    require(errors, text.count('needs: workflow-contract') == 1, 'le job validate doit dépendre du contrat')
    require(errors, text.count(WEB_RELEASE_VALIDATE_IF) == 1, 'la validation lourde web-only doit rester bornée aux branches a1/web-release-*')
    require(errors, 'python scripts/validate_site.py' in text, 'validation principale du site absente')
    require(errors, exact_run_count(text, NETLIFY_PUBLIC_CHECK) == 1, 'validation périmètre public Netlify absente ou dupliquée')
    require(errors, exact_run_count(text, WEB_RELEASE_SCOPE_SELF) == 1, 'auto-test portée web-only absent ou dupliqué')
    require(errors, exact_run_count(text, WEB_RELEASE_SCOPE_VALIDATE) == 1, 'validation portée web-only absente ou dupliquée')
    require(errors, text.count(WEB_RELEASE_SCOPE_IF) == 2, 'la portée web-only doit rester limitée aux branches a1/web-release-*')
    require(errors, exact_run_count(text, WEB_RELEASE_HTTP_SELF) == 1, 'auto-test smoke HTTP release absent ou dupliqué')
    require(errors, exact_run_count(text, AI_TRANSPARENCY_SELF) == 1, 'auto-test Transparence IA absent ou dupliqué')
    require(errors, exact_run_count(text, AI_TRANSPARENCY_VALIDATE) == 1, 'validation Transparence IA absente ou dupliquée')
    require(errors, exact_run_count(text, PUBLIC_AI_ASSISTANT_SELF) == 1, 'auto-test assistant IA public absent ou dupliqué')
    require(errors, exact_run_count(text, PUBLIC_AI_ASSISTANT_VALIDATE) == 1, 'validation assistant IA public absente ou dupliquée')
    require(errors, exact_run_count(text, V18_SELF) == 1, 'auto-test admin V18 absent ou dupliqué')
    require(errors, exact_run_count(text, V18_VALIDATE) == 1, 'validation admin V18 absente ou dupliquée')
    require(errors, exact_run_count(text, ADMIN_CONSOLE_SELF) == 1, 'auto-test admin-console absent ou dupliqué')
    require(errors, exact_run_count(text, ADMIN_CONSOLE_VALIDATE) == 1, 'validation admin-console absente ou dupliquée')
    require(errors, exact_run_count(text, ADMIN_PRIVATE_READS_SELF) == 1, 'auto-test lectures admin privées absent ou dupliqué')
    require(errors, exact_run_count(text, ADMIN_PRIVATE_READS_VALIDATE) == 1, 'validation lectures admin privées absente ou dupliquée')
    return errors


def validate_preview_workflow_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'workflow_dispatch:' in text, 'preview smoke doit rester manuel')
    require(errors, 'pull_request:' not in text, 'preview smoke ne doit pas se déclencher sur pull_request')
    require(errors, 'push:' not in text, 'preview smoke ne doit pas se déclencher sur push')
    require(errors, 'permissions:\n  contents: read' in text, 'preview smoke doit rester contents:read')
    require(errors, 'cancel-in-progress: false' in text, 'preview smoke manuel ne doit pas être annulé')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'preview smoke doit utiliser Ubuntu 24.04')
    require(errors, 'timeout-minutes: 5' in text, 'preview smoke doit rester borné à 5 minutes')
    require(errors, f'uses: actions/checkout@{CHECKOUT_SHA}' in text, 'checkout preview smoke non épinglé')
    require(errors, 'persist-credentials: false' in text, 'preview smoke doit désactiver les credentials Git')
    require(errors, f'uses: actions/setup-python@{SETUP_PYTHON_SHA}' in text, 'setup-python preview smoke non épinglé')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python preview smoke inattendue')
    require(errors, 'PREVIEW_URL: ${{ inputs.preview_url }}' in text, 'URL preview doit passer par une variable d’environnement')
    require(errors, exact_run_count(text, WEB_RELEASE_HTTP_SELF) == 1, 'auto-test smoke HTTP preview absent ou dupliqué')
    require(errors, 'python3 scripts/validate_web_release_http.py "$PREVIEW_URL" --context preview' in text, 'commande smoke preview absente')
    require(errors, '### Smoke HTTP — Deploy Preview Netlify' in text, 'résumé preuve preview absent')
    require(errors, 'GITHUB_STEP_SUMMARY' in text, 'preview smoke doit écrire une preuve dans GITHUB_STEP_SUMMARY')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'preview smoke ne doit référencer aucun secret')
    require(errors, 'contents: write' not in text, 'preview smoke ne doit jamais écrire dans le dépôt')
    return errors


def validate_production_workflow_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'workflow_dispatch:' in text, 'production smoke doit rester manuel')
    require(errors, 'pull_request:' not in text, 'production smoke ne doit pas se déclencher sur pull_request')
    require(errors, 'push:' not in text, 'production smoke ne doit pas se déclencher sur push')
    require(errors, 'permissions:\n  contents: read' in text, 'production smoke doit rester contents:read')
    require(errors, 'cancel-in-progress: false' in text, 'production smoke manuel ne doit pas être annulé')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'production smoke doit utiliser Ubuntu 24.04')
    require(errors, 'timeout-minutes: 5' in text, 'production smoke doit rester borné à 5 minutes')
    require(errors, f'uses: actions/checkout@{CHECKOUT_SHA}' in text, 'checkout production smoke non épinglé')
    require(errors, 'persist-credentials: false' in text, 'production smoke doit désactiver les credentials Git')
    require(errors, f'uses: actions/setup-python@{SETUP_PYTHON_SHA}' in text, 'setup-python production smoke non épinglé')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python production smoke inattendue')
    require(errors, exact_run_count(text, WEB_RELEASE_HTTP_SELF) == 1, 'auto-test smoke HTTP production absent ou dupliqué')
    require(
        errors,
        'python3 scripts/validate_web_release_http.py https://www.benoitcantin.com --context production' in text,
        'commande smoke production canonique absente',
    )
    require(errors, '### Smoke HTTP — production officielle' in text, 'résumé preuve production absent')
    require(errors, 'GITHUB_STEP_SUMMARY' in text, 'production smoke doit écrire une preuve dans GITHUB_STEP_SUMMARY')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'production smoke ne doit référencer aucun secret')
    require(errors, 'contents: write' not in text, 'production smoke ne doit jamais écrire dans le dépôt')
    require(errors, 'inputs:' not in text, 'production smoke ne doit accepter aucune URL ou entrée utilisateur')
    return errors


def run_production_self_tests(text: str) -> None:
    cases = {
        'déclenchement PR ajouté': text.replace('  workflow_dispatch:\n', '  pull_request:\n  workflow_dispatch:\n', 1),
        'annulation activée': text.replace('cancel-in-progress: false', 'cancel-in-progress: true', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'auto-test smoke retiré': text.replace(f'        run: {WEB_RELEASE_HTTP_SELF}\n', '', 1),
        'domaine remplacé': text.replace('https://www.benoitcantin.com --context production', 'https://example.com --context production', 1),
        'input ajouté': text.replace('  workflow_dispatch:\n', '  workflow_dispatch:\n    inputs:\n      url:\n        required: true\n', 1),
        'secret ajouté': text.replace('    steps:\n', '    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}\n    steps:\n', 1),
        'résumé preuve retiré': text.replace('            echo "### Smoke HTTP — production officielle"\n', '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test production workflow: mutation sans effet: {name}')
        if not validate_production_workflow_text(mutated):
            raise SystemExit(f'ERREUR auto-test production workflow: mutation non détectée: {name}')
    print(f'OK auto-tests production workflow: {len(cases)} affaiblissements critiques détectés.')


def run_preview_self_tests(text: str) -> None:
    cases = {
        'déclenchement PR ajouté': text.replace('  workflow_dispatch:\n', '  pull_request:\n  workflow_dispatch:\n', 1),
        'annulation activée': text.replace('cancel-in-progress: false', 'cancel-in-progress: true', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'auto-test smoke retiré': text.replace(f'        run: {WEB_RELEASE_HTTP_SELF}\n', '', 1),
        'injection directe URL': text.replace(
            'python3 scripts/validate_web_release_http.py "$PREVIEW_URL" --context preview',
            'python3 scripts/validate_web_release_http.py "${{ inputs.preview_url }}" --context preview',
            1,
        ),
        'secret ajouté': text.replace(
            'PREVIEW_URL: ${{ inputs.preview_url }}',
            'PREVIEW_URL: ${{ secrets.PREVIEW_URL }}',
            1,
        ),
        'résumé preuve retiré': text.replace('            echo "### Smoke HTTP — Deploy Preview Netlify"\n', '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test preview workflow: mutation sans effet: {name}')
        if not validate_preview_workflow_text(mutated):
            raise SystemExit(f'ERREUR auto-test preview workflow: mutation non détectée: {name}')
    print(f'OK auto-tests preview workflow: {len(cases)} affaiblissements critiques détectés.')


def run_self_tests(text: str) -> None:
    cases = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'setup-node mobile': text.replace(f'actions/setup-node@{SETUP_NODE_SHA}', 'actions/setup-node@v6', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'annulation globale': text.replace("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", 'cancel-in-progress: true', 1),
        'secret ajouté': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}', 1),
        'runner mobile': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1),
        'python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'node large': text.replace(f"node-version: '{NODE_VERSION}'", "node-version: '22'", 1),
        'dépendance contrat retirée': text.replace('    needs: workflow-contract\n', '', 1),
        'exception draft web-only retirée': text.replace(WEB_RELEASE_VALIDATE_IF, "if: github.event_name != 'pull_request' || github.event.pull_request.draft == false", 1),
        'exception draft web-only élargie': text.replace("startsWith(github.head_ref, 'a1/web-release-')", "true", 1),
        'validation Netlify retirée': text.replace(f'        run: {NETLIFY_PUBLIC_CHECK}\n', '', 1),
        'historique Git retiré': text.replace('          fetch-depth: 0\n', '', 1),
        'auto-test portée web retiré': text.replace(f'        run: {WEB_RELEASE_SCOPE_SELF}\n', '', 1),
        'validation portée web retirée': text.replace(f'        run: {WEB_RELEASE_SCOPE_VALIDATE}\n', '', 1),
        'condition portée web élargie': text.replace(WEB_RELEASE_SCOPE_IF, "if: github.event_name == 'pull_request'", 1),
        'auto-test smoke HTTP retiré': text.replace(f'        run: {WEB_RELEASE_HTTP_SELF}\n', '', 1),
        'auto-test Transparence IA retiré': text.replace(f'        run: {AI_TRANSPARENCY_SELF}\n', '', 1),
        'validation Transparence IA retirée': text.replace(f'        run: {AI_TRANSPARENCY_VALIDATE}\n', '', 1),
        'auto-test assistant IA retiré': text.replace(f'        run: {PUBLIC_AI_ASSISTANT_SELF}\n', '', 1),
        'validation assistant IA retirée': text.replace(f'        run: {PUBLIC_AI_ASSISTANT_VALIDATE}\n', '', 1),
        'auto-test V18 retiré': text.replace(f'        run: {V18_SELF}\n', '', 1),
        'validation V18 retirée': text.replace(f'        run: {V18_VALIDATE}\n', '', 1),
        'auto-test admin-console retiré': text.replace(f'        run: {ADMIN_CONSOLE_SELF}\n', '', 1),
        'validation admin-console retirée': text.replace(f'        run: {ADMIN_CONSOLE_VALIDATE}\n', '', 1),
        'auto-test lectures admin privées retiré': text.replace(f'        run: {ADMIN_PRIVATE_READS_SELF}\n', '', 1),
        'validation lectures admin privées retirée': text.replace(f'        run: {ADMIN_PRIVATE_READS_VALIDATE}\n', '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test validation site: mutation sans effet: {name}')
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test validation site: mutation non détectée: {name}')
    print(f'OK auto-tests validation site: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow absent: {WORKFLOW.relative_to(ROOT)}')
    if not PREVIEW_WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow preview absent: {PREVIEW_WORKFLOW.relative_to(ROOT)}')
    if not PRODUCTION_WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow production absent: {PRODUCTION_WORKFLOW.relative_to(ROOT)}')

    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    preview_text = PREVIEW_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    production_text = PRODUCTION_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        run_preview_self_tests(preview_text)
        run_production_self_tests(production_text)
        return 0

    errors = validate_text(text)
    errors.extend(validate_preview_workflow_text(preview_text))
    errors.extend(validate_production_workflow_text(production_text))
    if errors:
        for error in errors:
            print(f'ERREUR sécurité validation site: {error}')
        return 1
    print(
        'OK sécurité validation site: actions immuables, runtimes figés, credentials non persistés, '
        'garde web-only, smoke preview et smoke production manuels read-only obligatoires.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
