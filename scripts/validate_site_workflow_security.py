#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/validate-site.yml'
PREVIEW_WORKFLOW = ROOT / '.github/workflows/validate-netlify-preview.yml'
PRODUCTION_WORKFLOW = ROOT / '.github/workflows/validate-web-production.yml'
ARTIFACT_WORKFLOW = ROOT / '.github/workflows/build-web-release-artifact.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE_SHA = '249970729cb0ef3589644e2896645e5dc5ba9c38'
UPLOAD_ARTIFACT_SHA = '043fb46d1a93c77aae656e7c1c64a875d1fc6a0a'
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
WEB_RELEASE_PRODUCTION_BASELINE = 'python3 scripts/validate_web_release_http.py "$origin" --context production'
WEB_RELEASE_ARTIFACT_BUILD = 'python3 scripts/build_netlify_public.py --output _site --standalone-netlify'
WEB_PREVIEW_ARTIFACT_BUILD = 'python3 scripts/build_netlify_public.py --output _preview_site --standalone-netlify'
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
    require(errors, text.count(WEB_RELEASE_SCOPE_IF) == 3, 'les gardes et le résumé web-only doivent rester limités aux branches a1/web-release-*')
    require(errors, exact_run_count(text, WEB_RELEASE_HTTP_SELF) == 1, 'auto-test smoke HTTP release absent ou dupliqué')
    require(errors, WEB_RELEASE_PRODUCTION_BASELINE in text, 'baseline smoke production read-only absent')
    require(errors, 'timeout 90s ' + WEB_RELEASE_PRODUCTION_BASELINE in text, 'baseline smoke production doit rester borné à 90 secondes')
    require(errors, '### Baseline smoke production — lecture seule' in text, 'résumé baseline production absent')
    require(errors, 'echo "- Cible : $origin"' in text, 'résumé baseline production doit éviter la substitution Bash des backticks')
    require(errors, 'echo "- Code smoke : $smoke_status"' in text, 'code baseline production doit être rendu sans substitution Bash')
    require(errors, 'FAIL attendu tant que #450 est ouvert' in text, 'baseline production doit rester explicitement non bloquant avant #450')
    require(errors, 'Ce baseline est informatif et non bloquant. Il doit devenir PASS après la bascule #450.' in text, 'contrat baseline production non bloquant absent')
    require(errors, '### Readiness web-only' in text, 'résumé readiness web-only absent')
    require(errors, 'Fichiers modifiés : **$changed_count**' in text, 'compteur de diff readiness absent')
    require(errors, 'BubblaV : **fail-closed**' in text, 'état BubblaV fail-closed absent du résumé')
    require(errors, 'Artefact public : \\`_site\\` allowlisté + package Netlify autonome \\`_headers\\`/\\`_redirects\\`' in text, 'artefact Netlify autonome absent du résumé')
    require(errors, 'Artefact CI : \\`Web release — artefact public isolé\\` (aucun déploiement)' in text, 'workflow artefact CI absent du résumé')
    require(errors, 'Portes externes restantes : bascule hébergeur sûre (#450), #135, #443, #444' in text, 'portes externes readiness absentes')
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



def validate_artifact_workflow_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'pull_request:' in text, 'artefact web doit pouvoir se construire sur pull_request')
    require(errors, 'workflow_dispatch:' in text, 'artefact web doit pouvoir être construit manuellement')
    require(errors, 'push:' not in text, 'artefact web ne doit jamais se déclencher directement sur push')
    require(errors, 'permissions:\n  contents: read' in text, 'artefact web doit rester contents:read')
    require(errors, "group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}" in text, 'concurrency artefact web exacte requise')
    require(errors, "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text, 'annulation artefact limitée aux pull requests requise')
    require(errors, "if: github.event_name != 'pull_request' || startsWith(github.head_ref, 'a1/web-release-')" in text, 'garde branche web-only absente du workflow artefact')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'artefact web doit utiliser Ubuntu 24.04')
    require(errors, 'timeout-minutes: 8' in text, 'artefact web doit rester borné à 8 minutes')
    require(errors, f'uses: actions/checkout@{CHECKOUT_SHA}' in text, 'checkout artefact web non épinglé')
    require(errors, 'persist-credentials: false' in text, 'artefact web doit désactiver les credentials Git')
    require(errors, f'uses: actions/setup-python@{SETUP_PYTHON_SHA}' in text, 'setup-python artefact web non épinglé')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python artefact web inattendue')
    require(errors, text.count(f'uses: actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}') == 2, 'les deux upload-artifact web doivent être épinglés')
    require(errors, exact_run_count(text, NETLIFY_PUBLIC_CHECK) == 1, 'validation allowlist avant artefact absente ou dupliquée')
    require(errors, exact_run_count(text, WEB_RELEASE_ARTIFACT_BUILD) == 1, 'construction _site avant artefact absente ou dupliquée')
    require(errors, exact_run_count(text, WEB_PREVIEW_ARTIFACT_BUILD) == 1, 'construction _preview_site avant artefact absente ou dupliquée')
    require(errors, 'CONTEXT: deploy-preview' in text, 'contexte deploy-preview absent de l’artefact preview')
    require(errors, 'include-hidden-files: true' in text, 'artefact web doit inclure .well-known et .nojekyll')
    require(errors, 'if-no-files-found: error' in text, 'artefact web doit échouer si le contenu est absent')
    require(errors, 'retention-days: 7' in text, 'rétention artefact web doit rester courte')
    require(errors, 'web-release-SHA256SUMS.txt' in text, 'manifeste SHA-256 de release absent')
    require(errors, 'web-preview-SHA256SUMS.txt' in text, 'manifeste SHA-256 preview absent')
    require(errors, 'sinjira-web-release-${{ github.event.pull_request.head.sha || github.sha }}' in text, 'nom artefact production absent')
    require(errors, 'sinjira-web-preview-${{ github.event.pull_request.head.sha || github.sha }}' in text, 'nom artefact preview absent')
    require(errors, 'test -f _site/.well-known/security.txt' in text, 'security.txt doit être prouvé dans l’artefact')
    require(errors, 'test -f _site/CNAME' in text, 'CNAME doit être prouvé dans l’artefact')
    require(errors, 'test -f _site/_headers' in text, '_headers autonome doit être prouvé dans l’artefact')
    require(errors, 'test -f _site/_redirects' in text, '_redirects autonome doit être prouvé dans l’artefact')
    require(errors, 'test -f _preview_site/_headers' in text, '_headers preview doit être prouvé')
    require(errors, 'test -f _preview_site/_redirects' in text, '_redirects preview doit être prouvé')
    require(errors, 'X-Robots-Tag: noindex, nofollow, noarchive' in text, 'preuve noindex globale preview absente')
    require(errors, 'test "$preview_count" -eq "$WEB_RELEASE_FILE_COUNT"' in text, 'parité fichiers production/preview non prouvée')
    require(errors, 'Content-Security-Policy:' in text, 'preuve CSP embarquée absente du workflow artefact')
    require(errors, '/supabase/* /404.html 404!' in text, 'preuve 404 forcée embarquée absente du workflow artefact')
    require(errors, 'Configuration embarquée : \\`_headers\\` + \\`_redirects\\`' in text, 'résumé configuration autonome absent')
    require(errors, 'Preview noindex :' in text, 'lien artefact preview absent du résumé')
    require(errors, 'test ! -e "_site/$forbidden"' in text, 'absence des répertoires techniques non prouvée')
    require(errors, 'actions/deploy-pages@' not in text, 'workflow artefact ne doit jamais déployer GitHub Pages')
    require(errors, 'actions/configure-pages@' not in text, 'workflow artefact ne doit pas configurer GitHub Pages')
    require(errors, 'pages: write' not in text, 'permission Pages write interdite au workflow artefact')
    require(errors, 'id-token: write' not in text, 'permission OIDC write interdite au workflow artefact')
    require(errors, 'contents: write' not in text, 'permission contents write interdite au workflow artefact')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'workflow artefact ne doit référencer aucun secret')
    require(errors, 'Aucun déploiement n’est effectué par ce workflow.' in text, 'résumé non-déploiement absent du workflow artefact')

    targets = action_targets(text)
    require(errors, len(targets) == 4, f'nombre inattendu d’actions dans le workflow artefact: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'action artefact non immuable: {target}')
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



def run_artifact_self_tests(text: str) -> None:
    guard = "if: github.event_name != 'pull_request' || startsWith(github.head_ref, 'a1/web-release-')"
    cases = {
        'déclenchement push ajouté': text.replace('  workflow_dispatch:\n', '  push:\n  workflow_dispatch:\n', 1),
        'permission dépôt écriture': text.replace('contents: read', 'contents: write', 1),
        'permission Pages ajoutée': text.replace('permissions:\n  contents: read', 'permissions:\n  contents: read\n  pages: write', 1),
        'permission OIDC ajoutée': text.replace('permissions:\n  contents: read', 'permissions:\n  contents: read\n  id-token: write', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'upload-artifact mobile': text.replace(f'actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}', 'actions/upload-artifact@v7', 1),
        'garde branche retirée': text.replace(guard, 'if: always()', 1),
        'construction racine': text.replace(WEB_RELEASE_ARTIFACT_BUILD, 'python3 scripts/build_netlify_public.py --output .', 1),
        'contexte preview retiré': text.replace('          CONTEXT: deploy-preview\n', '          CONTEXT: production\n', 1),
        'fichiers cachés exclus': text.replace('include-hidden-files: true', 'include-hidden-files: false', 1),
        'secret ajouté': text.replace('    steps:\n', '    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}\n    steps:\n', 1),
        'résumé non-déploiement retiré': text.replace('            echo "> Aucun déploiement n’est effectué par ce workflow."\n', '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test artifact workflow: mutation sans effet: {name}')
        if not validate_artifact_workflow_text(mutated):
            raise SystemExit(f'ERREUR auto-test artifact workflow: mutation non détectée: {name}')
    print(f'OK auto-tests artifact workflow: {len(cases)} affaiblissements critiques détectés.')

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
        'exception draft web-only élargie': text.replace(
            WEB_RELEASE_VALIDATE_IF,
            "if: github.event_name != 'pull_request' || github.event.pull_request.draft == false || true",
            1,
        ),
        'condition résumé readiness élargie': text.replace(
            WEB_RELEASE_SCOPE_IF,
            "if: github.event_name == 'pull_request'",
            1,
        ),
        'validation Netlify retirée': text.replace(f'        run: {NETLIFY_PUBLIC_CHECK}\n', '', 1),
        'historique Git retiré': text.replace('          fetch-depth: 0\n', '', 1),
        'auto-test portée web retiré': text.replace(f'        run: {WEB_RELEASE_SCOPE_SELF}\n', '', 1),
        'validation portée web retirée': text.replace(f'        run: {WEB_RELEASE_SCOPE_VALIDATE}\n', '', 1),
        'condition portée web élargie': text.replace(WEB_RELEASE_SCOPE_IF, "if: github.event_name == 'pull_request'", 1),
        'auto-test smoke HTTP retiré': text.replace(f'        run: {WEB_RELEASE_HTTP_SELF}\n', '', 1),
        'baseline production retiré': text.replace('            echo "### Baseline smoke production — lecture seule"\n', '', 1),
        'baseline cible dangereuse': text.replace('            echo "- Cible : $origin"\n', '            echo "- Cible : `$origin`"\n', 1),
        'résumé readiness retiré': text.replace('            echo "### Readiness web-only"\n', '', 1),
        'état fail-closed readiness retiré': text.replace('            echo "- BubblaV : **fail-closed** (widget désactivé + CSP bloquante)"\n', '', 1),
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
    if not ARTIFACT_WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow artefact absent: {ARTIFACT_WORKFLOW.relative_to(ROOT)}')

    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    preview_text = PREVIEW_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    production_text = PRODUCTION_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    artifact_text = ARTIFACT_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        run_preview_self_tests(preview_text)
        run_production_self_tests(production_text)
        run_artifact_self_tests(artifact_text)
        return 0

    errors = validate_text(text)
    errors.extend(validate_preview_workflow_text(preview_text))
    errors.extend(validate_production_workflow_text(production_text))
    errors.extend(validate_artifact_workflow_text(artifact_text))
    if errors:
        for error in errors:
            print(f'ERREUR sécurité validation site: {error}')
        return 1
    print(
        'OK sécurité validation site: actions immuables, runtimes figés, credentials non persistés, '
        'garde web-only, artefact public inspectable non-déployant, smoke preview et smoke production manuels read-only obligatoires.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
