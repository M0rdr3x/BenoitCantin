#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/validate-site.yml'
PREVIEW_WORKFLOW = ROOT / '.github/workflows/validate-netlify-preview.yml'
NETLIFY_PRE_DNS_WORKFLOW = ROOT / '.github/workflows/validate-netlify-pre-dns.yml'
PRODUCTION_WORKFLOW = ROOT / '.github/workflows/validate-web-production.yml'
ARTIFACT_WORKFLOW = ROOT / '.github/workflows/build-web-release-artifact.yml'
PAGES_DEPLOY_WORKFLOW = ROOT / '.github/workflows/deploy-github-pages-isolated.yml'
ANON_NETLIFY_PREVIEW_WORKFLOW = ROOT / '.github/workflows/create-netlify-anonymous-preview.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE_SHA = '249970729cb0ef3589644e2896645e5dc5ba9c38'
UPLOAD_ARTIFACT_SHA = '043fb46d1a93c77aae656e7c1c64a875d1fc6a0a'
UPLOAD_PAGES_ARTIFACT_SHA = '56afc609e74202658d3ffba0e8f6dda462b719fa'
DEPLOY_PAGES_SHA = '368f82528645a54fb793d4d04e342629a3f51346'
PYTHON_VERSION = '3.12.14'
NODE_VERSION = '22.23.2'
NETLIFY_CLI_VERSION = '27.10.2'
V18_SELF = 'python scripts/validate_admin_v18_privacy_security.py --self-test'
V18_VALIDATE = 'python scripts/validate_admin_v18_privacy_security.py'
ADMIN_CONSOLE_SELF = 'python scripts/validate_admin_console_security.py --self-test'
ADMIN_CONSOLE_VALIDATE = 'python scripts/validate_admin_console_security.py'
ADMIN_PRIVATE_READS_SELF = 'python scripts/validate_admin_private_reads_security.py --self-test'
ADMIN_PRIVATE_READS_VALIDATE = 'python scripts/validate_admin_private_reads_security.py'
NETLIFY_PUBLIC_CHECK = 'python3 scripts/build_netlify_public.py --check'
PERSONAL_FORMSPREE_CONFIG_SELF = 'python3 scripts/configure_personal_formspree.py --self-test'
PRODUCTION_ENVIRONMENT_SELF = 'python3 scripts/validate_production_environment_boundary.py --self-test'
PRODUCTION_ENVIRONMENT_VALIDATE = 'python3 scripts/validate_production_environment_boundary.py'
WEB_RELEASE_SCOPE_SELF = 'python3 scripts/validate_web_release_scope.py --self-test'
WEB_RELEASE_SCOPE_VALIDATE = 'python3 scripts/validate_web_release_scope.py'
WEB_RELEASE_HTTP_SELF = 'python3 scripts/validate_web_release_http.py --self-test'
WEB_RELEASE_PRODUCTION_BASELINE = 'python3 scripts/validate_web_release_http.py "$origin" --context production'
WEB_RELEASE_ARTIFACT_BUILD = 'python3 scripts/build_netlify_public.py --output _site --standalone-netlify'
WEB_PREVIEW_ARTIFACT_BUILD = 'python3 scripts/build_netlify_public.py --output _preview_site --standalone-netlify'
WEB_PAGES_ARTIFACT_BUILD = 'python3 scripts/build_netlify_public.py --output _pages_site'
PAGES_PUBLIC_BUILD = 'python3 scripts/build_netlify_public.py --output _site'
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
    require(errors, exact_run_count(text, PERSONAL_FORMSPREE_CONFIG_SELF) == 1, 'auto-test transition Formspree personnelle absent ou dupliqué')
    require(errors, exact_run_count(text, PRODUCTION_ENVIRONMENT_SELF) == 1, 'auto-test frontière Environments production absent ou dupliqué')
    require(errors, exact_run_count(text, PRODUCTION_ENVIRONMENT_VALIDATE) == 1, 'validation frontière Environments production absente ou dupliquée')
    require(errors, exact_run_count(text, WEB_RELEASE_SCOPE_SELF) == 1, 'auto-test portée web-only absent ou dupliqué')
    require(errors, exact_run_count(text, WEB_RELEASE_SCOPE_VALIDATE) == 1, 'validation portée web-only absente ou dupliquée')
    require(errors, text.count(WEB_RELEASE_SCOPE_IF) == 3, 'les gardes et le résumé web-only doivent rester limités aux branches a1/web-release-*')
    require(errors, exact_run_count(text, WEB_RELEASE_HTTP_SELF) == 1, 'auto-test smoke HTTP release absent ou dupliqué')
    require(errors, WEB_RELEASE_PRODUCTION_BASELINE in text, 'baseline smoke production read-only absent')
    require(errors, 'timeout 90s ' + WEB_RELEASE_PRODUCTION_BASELINE in text, 'baseline smoke production doit rester borné à 90 secondes')
    require(errors, '### Baseline smoke production — lecture seule' in text, 'résumé baseline production absent')
    require(errors, 'echo "- Cible : $origin"' in text, 'résumé baseline production doit éviter la substitution Bash des backticks')
    require(errors, 'apex_origin="https://benoitcantin.com"' in text, 'baseline apex officiel absent')
    require(errors, 'Apex HTTP initial :' in text, 'code HTTP apex absent du résumé baseline')
    require(errors, 'Apex Location :' in text, 'Location apex absente du résumé baseline')
    require(errors, 'Apex Server :' in text, 'Server apex absent du résumé baseline')
    require(errors, 'Apex x-nf-request-id :' in text, 'signature Netlify apex absente du résumé baseline')
    require(errors, 'echo "- Code smoke : $smoke_status"' in text, 'code baseline production doit être rendu sans substitution Bash')
    require(errors, 'FAIL attendu tant que #450 est ouvert' in text, 'baseline production doit rester explicitement non bloquant avant #450')
    require(errors, 'Ce baseline est informatif et non bloquant. Il doit devenir PASS après la bascule #450.' in text, 'contrat baseline production non bloquant absent')
    require(errors, '### Readiness web-only' in text, 'résumé readiness web-only absent')
    require(errors, 'Fichiers modifiés : **$changed_count**' in text, 'compteur de diff readiness absent')
    require(errors, 'BubblaV : **fail-closed**' in text, 'état BubblaV fail-closed absent du résumé')
    require(errors, 'Artefact public : \\`_site\\` allowlisté + package Netlify autonome \\`_headers\\`/\\`_redirects\\`' in text, 'artefact Netlify autonome absent du résumé')
    require(errors, 'Artefact CI : \\`Web release — artefact public isolé\\` (aucun déploiement)' in text, 'workflow artefact CI absent du résumé')
    require(errors, 'Smoke deploy unitaire : \\`Netlify deploy — smoke HTTP\\` (permalink atomique, preview / production-candidate)' in text, 'smoke deploy unitaire absent du résumé readiness')
    require(errors, 'Gate pré-DNS combiné : \\`Netlify pré-DNS — gate combiné\\` (même site Netlify + même SHA)' in text, 'gate pré-DNS combiné absent du résumé readiness')
    require(errors, 'Smoke production : \\`Web production — smoke HTTP\\` (SHA + signature Netlify + apex canonique)' in text, 'preuve finale Netlify/apex absente du résumé readiness')
    require(errors, 'Portes restantes : master PDF démo exact (#363), bascule hébergeur sûre (#450), Formspree personnel distinct (#451), preuve réseau BubblaV (#444), protection serveur main (#135)' in text, 'portes readiness actuelles absentes')
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
    require(errors, 'deploy_permalink:' in text, 'input permalink atomique Netlify absent')
    require(errors, 'description: "Permalink atomique Netlify (DEPLOY_URL: deploy-id--site.netlify.app), jamais un alias preview/branche"' in text, 'description deploy_permalink doit rester quotée pour conserver un YAML GitHub valide')
    require(errors, 'preview_url:' not in text, 'alias preview générique interdit comme input de gate')
    require(errors, 'artifact_context:' in text, 'choix de contexte artefact Netlify absent')
    require(errors, 'type: choice' in text, 'contexte artefact Netlify doit rester un choice borné')
    require(errors, '          - preview' in text, 'option preview absente du smoke Netlify')
    require(errors, '          - production-candidate' in text, 'option production-candidate absente du smoke Netlify')
    require(errors, 'DEPLOY_PERMALINK: ${{ inputs.deploy_permalink }}' in text, 'permalink Netlify doit passer par une variable d’environnement')
    require(errors, 'SMOKE_CONTEXT: ${{ inputs.artifact_context }}' in text, 'contexte Netlify doit passer par une variable d’environnement')
    require(errors, 'expected_sha:' not in text, 'smoke Netlify ne doit accepter aucun SHA saisi manuellement')
    require(errors, "if: startsWith(github.ref, 'refs/heads/a1/web-release-')" in text, 'preview smoke doit rester borné à une branche web-release')
    require(errors, exact_run_count(text, WEB_RELEASE_HTTP_SELF) == 1, 'auto-test smoke HTTP preview absent ou dupliqué')
    require(errors, 'python3 scripts/validate_web_release_http.py "$DEPLOY_PERMALINK" --context "$SMOKE_CONTEXT" --expected-sha "$GITHUB_SHA"' in text, 'commande smoke permalink doit lier contexte borné et preuve au GITHUB_SHA')
    require(errors, '### Smoke HTTP — permalink atomique Netlify' in text, 'résumé preuve permalink preview absent')
    require(errors, 'GITHUB_STEP_SUMMARY' in text, 'preview smoke doit écrire une preuve dans GITHUB_STEP_SUMMARY')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'preview smoke ne doit référencer aucun secret')
    require(errors, 'contents: write' not in text, 'preview smoke ne doit jamais écrire dans le dépôt')
    return errors



def validate_netlify_pre_dns_workflow_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'workflow_dispatch:' in text, 'gate pré-DNS doit rester manuel')
    require(errors, 'pull_request:' not in text, 'gate pré-DNS ne doit pas se déclencher sur pull_request')
    require(errors, 'push:' not in text, 'gate pré-DNS ne doit pas se déclencher sur push')
    require(errors, 'permissions:\n  contents: read' in text, 'gate pré-DNS doit rester contents:read')
    require(errors, 'cancel-in-progress: false' in text, 'gate pré-DNS ne doit pas être annulé automatiquement')
    require(errors, 'preview_permalink:' in text, 'permalink preview requis absent du gate pré-DNS')
    require(errors, 'production_permalink:' in text, 'permalink production-candidate requis absent du gate pré-DNS')
    require(errors, 'expected_sha:' not in text, 'gate pré-DNS ne doit accepter aucun SHA manuel')
    require(errors, "if: startsWith(github.ref, 'refs/heads/a1/web-release-')" in text, 'gate pré-DNS doit rester borné à une branche web-release')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'gate pré-DNS doit utiliser Ubuntu 24.04')
    require(errors, 'timeout-minutes: 8' in text, 'gate pré-DNS doit rester borné à 8 minutes')
    require(errors, f'uses: actions/checkout@{CHECKOUT_SHA}' in text, 'checkout gate pré-DNS non épinglé')
    require(errors, 'persist-credentials: false' in text, 'gate pré-DNS doit désactiver les credentials Git')
    require(errors, f'uses: actions/setup-python@{SETUP_PYTHON_SHA}' in text, 'setup-python gate pré-DNS non épinglé')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python gate pré-DNS inattendue')
    require(errors, 'PREVIEW_PERMALINK: ${{ inputs.preview_permalink }}' in text, 'permalink preview doit passer par env')
    require(errors, 'PRODUCTION_PERMALINK: ${{ inputs.production_permalink }}' in text, 'permalink production doit passer par env')
    require(errors, '[ "$PREVIEW_PERMALINK" = "$PRODUCTION_PERMALINK" ]' in text, 'garde deploys distincts absente')
    require(errors, exact_run_count(text, WEB_RELEASE_HTTP_SELF) == 1, 'auto-test smoke pré-DNS absent ou dupliqué')
    require(errors, 'python3 scripts/validate_web_release_http.py "$PREVIEW_PERMALINK" --context preview --expected-sha "$GITHUB_SHA"' in text, 'preuve preview pré-DNS absente')
    require(errors, 'python3 scripts/validate_web_release_http.py "$PRODUCTION_PERMALINK" --context production-candidate --same-netlify-site-as "$PREVIEW_PERMALINK" --expected-sha "$GITHUB_SHA"' in text, 'preuve production-candidate même site pré-DNS absente')
    require(errors, 'python3 scripts/validate_web_release_http.py "$PREVIEW_PERMALINK" --print-netlify-site' in text, 'extraction du nom canonique Netlify absente')
    require(errors, 'NETLIFY_SITE_NAME=$site_name' in text, 'nom canonique Netlify doit être exporté vers le résumé')
    require(errors, 'Projet Netlify canonique : \\`$NETLIFY_SITE_NAME\\` — **même site confirmé pour les deux deploys**' in text, 'preuve du nom canonique Netlify absente du résumé')
    require(errors, '### Gate Netlify pré-DNS combiné' in text, 'résumé gate pré-DNS absent')
    require(errors, 'DNS : **non modifié par ce workflow**' in text, 'frontière non-déploiement DNS absente')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'gate pré-DNS ne doit référencer aucun secret')
    require(errors, 'contents: write' not in text, 'gate pré-DNS ne doit jamais écrire dans le dépôt')
    return errors


def run_netlify_pre_dns_self_tests(text: str) -> None:
    cases = {
        'déclenchement PR ajouté': text.replace('  workflow_dispatch:\n', '  pull_request:\n  workflow_dispatch:\n', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'garde branche retirée': text.replace("    if: startsWith(github.ref, 'refs/heads/a1/web-release-')\n", '', 1),
        'permalink production retiré': text.replace('      production_permalink:\n', '      production_alias:\n', 1),
        'garde deploys distincts retirée': text.replace('          if [ "$PREVIEW_PERMALINK" = "$PRODUCTION_PERMALINK" ]; then\n', '          if false; then\n', 1),
        'preuve preview retirée': text.replace('        run: python3 scripts/validate_web_release_http.py "$PREVIEW_PERMALINK" --context preview --expected-sha "$GITHUB_SHA"\n', '', 1),
        'preuve candidat production retirée': text.replace('        run: python3 scripts/validate_web_release_http.py "$PRODUCTION_PERMALINK" --context production-candidate --same-netlify-site-as "$PREVIEW_PERMALINK" --expected-sha "$GITHUB_SHA"\n', '', 1),
        'preuve même site retirée': text.replace(' --same-netlify-site-as "$PREVIEW_PERMALINK"', '', 1),
        'extraction site canonique retirée': text.replace('          site_name="$(python3 scripts/validate_web_release_http.py "$PREVIEW_PERMALINK" --print-netlify-site)"\n', '', 1),
        'export site canonique retiré': text.replace('          echo "NETLIFY_SITE_NAME=$site_name" >> "$GITHUB_ENV"\n', '', 1),
        'résumé même site retiré': text.replace('            echo "- Projet Netlify canonique : \\`$NETLIFY_SITE_NAME\\` — **même site confirmé pour les deux deploys**"\n', '', 1),
        'SHA manuel ajouté': text.replace('      preview_permalink:\n', '      expected_sha:\n        required: true\n      preview_permalink:\n', 1),
        'secret ajouté': text.replace('    steps:\n', '    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}\n    steps:\n', 1),
        'frontière DNS retirée': text.replace('            echo "- DNS : **non modifié par ce workflow**"\n', '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test gate pré-DNS: mutation sans effet: {name}')
        if not validate_netlify_pre_dns_workflow_text(mutated):
            raise SystemExit(f'ERREUR auto-test gate pré-DNS: mutation non détectée: {name}')
    print(f'OK auto-tests gate pré-DNS: {len(cases)} affaiblissements critiques détectés.')


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
    require(errors, 'SINJIRA_RELEASE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}' in text, 'SHA source embarqué absent du workflow artefact')
    require(errors, text.count(f'uses: actions/upload-artifact@{UPLOAD_ARTIFACT_SHA}') == 3, 'les trois upload-artifact web doivent être épinglés')
    require(errors, exact_run_count(text, NETLIFY_PUBLIC_CHECK) == 1, 'validation allowlist avant artefact absente ou dupliquée')
    require(errors, exact_run_count(text, WEB_RELEASE_ARTIFACT_BUILD) == 1, 'construction _site avant artefact absente ou dupliquée')
    require(errors, exact_run_count(text, WEB_PREVIEW_ARTIFACT_BUILD) == 1, 'construction _preview_site avant artefact absente ou dupliquée')
    require(errors, exact_run_count(text, WEB_PAGES_ARTIFACT_BUILD) == 1, 'construction _pages_site avant artefact absente ou dupliquée')
    require(errors, 'CONTEXT: deploy-preview' in text, 'contexte deploy-preview absent de l’artefact preview')
    require(errors, text.count('include-hidden-files: true') == 3, 'les trois artefacts web doivent inclure .well-known et .nojekyll')
    require(errors, 'if-no-files-found: error' in text, 'artefact web doit échouer si le contenu est absent')
    require(errors, 'retention-days: 7' in text, 'rétention artefact web doit rester courte')
    require(errors, 'web-release-SHA256SUMS.txt' in text, 'manifeste SHA-256 de release absent')
    require(errors, 'web-preview-SHA256SUMS.txt' in text, 'manifeste SHA-256 preview absent')
    require(errors, 'web-pages-SHA256SUMS.txt' in text, 'manifeste SHA-256 Pages absent')
    require(errors, 'sinjira-web-release-${{ github.event.pull_request.head.sha || github.sha }}' in text, 'nom artefact production absent')
    require(errors, 'sinjira-web-preview-${{ github.event.pull_request.head.sha || github.sha }}' in text, 'nom artefact preview absent')
    require(errors, 'sinjira-web-pages-${{ github.event.pull_request.head.sha || github.sha }}' in text, 'nom artefact Pages absent')
    require(errors, 'test -f _site/.well-known/security.txt' in text, 'security.txt doit être prouvé dans l’artefact')
    require(errors, 'test -f _site/.well-known/release.json' in text, 'release.json production doit être prouvé dans l’artefact')
    require(errors, 'test -f _preview_site/.well-known/release.json' in text, 'release.json preview doit être prouvé dans l’artefact')
    require(errors, 'test -f _pages_site/.well-known/release.json' in text, 'release.json Pages doit être prouvé dans l’artefact')
    require(errors, 'test -f _site/CNAME' in text, 'CNAME doit être prouvé dans l’artefact')
    require(errors, 'test -f _site/_headers' in text, '_headers autonome doit être prouvé dans l’artefact')
    require(errors, 'test -f _site/_redirects' in text, '_redirects autonome doit être prouvé dans l’artefact')
    require(errors, 'test -f _preview_site/_headers' in text, '_headers preview doit être prouvé')
    require(errors, 'test -f _preview_site/_redirects' in text, '_redirects preview doit être prouvé')
    require(errors, 'test ! -e _pages_site/_headers' in text, '_headers doit être absent de l’artefact Pages')
    require(errors, 'test ! -e _pages_site/_redirects' in text, '_redirects doit être absent de l’artefact Pages')
    require(errors, 'production_global_headers=' in text, 'extraction du bloc global production absente')
    require(errors, 'preview_global_headers=' in text, 'extraction du bloc global preview absente')
    require(errors, 'production_release_headers=' in text, 'extraction des headers release.json production absente')
    require(errors, 'preview_release_headers=' in text, 'extraction des headers release.json preview absente')
    require(errors, text.count('grep -Fq "Cache-Control: no-store" <<<"$production_release_headers"') == 1, 'preuve no-store release.json production absente')
    require(errors, text.count('grep -Fq "Cache-Control: no-store" <<<"$preview_release_headers"') == 1, 'preuve no-store release.json preview absente')
    require(errors, 'ERREUR: noindex global interdit dans l’artefact production.' in text, 'garde noindex production absente')
    require(errors, 'ERREUR: noindex global requis dans l’artefact preview.' in text, 'garde noindex preview absente')
    require(errors, 'X-Robots-Tag: noindex, nofollow, noarchive' in text, 'preuve noindex globale preview absente')
    require(errors, 'test "$preview_count" -eq "$WEB_RELEASE_FILE_COUNT"' in text, 'parité fichiers production/preview non prouvée')
    require(errors, 'expected_pages_count="$((WEB_RELEASE_FILE_COUNT - 2))"' in text, 'relation de comptage Pages/Netlify absente')
    require(errors, 'test "$pages_count" -eq "$expected_pages_count"' in text, 'parité artefact Pages non prouvée')
    require(errors, 'Content-Security-Policy:' in text, 'preuve CSP embarquée absente du workflow artefact')
    require(errors, '/supabase/* /404.html 404!' in text, 'preuve 404 forcée embarquée absente du workflow artefact')
    require(errors, 'Configuration Netlify : \\`_headers\\` + \\`_redirects\\`; artefact Pages : aucun fichier de configuration Netlify' in text, 'résumé configurations Netlify/Pages absent')
    require(errors, 'Preview noindex :' in text, 'lien artefact preview absent du résumé')
    require(errors, 'GitHub Pages isolé :' in text, 'lien artefact Pages absent du résumé')
    require(errors, 'test ! -e _site/script.js' in text, 'script.js racine legacy doit être absent de l’artefact production')
    require(errors, 'test ! -e _preview_site/script.js' in text, 'script.js racine legacy doit être absent de l’artefact preview')
    require(errors, 'test ! -e _pages_site/script.js' in text, 'script.js racine legacy doit être absent de l’artefact Pages')
    require(errors, text.count('for endpoint in "https://formspree.io/f/xdenkzrv" "https://formspree.io/f/xkolwjdg"; do') == 3, 'les trois artefacts doivent refuser les endpoints Formspree historiques')
    require(errors, 'ERREUR: endpoint Formspree historique interdit dans l’artefact production:' in text, 'garde Formspree historique production absente')
    require(errors, 'ERREUR: endpoint Formspree historique interdit dans l’artefact preview:' in text, 'garde Formspree historique preview absente')
    require(errors, 'test ! -e "_site/$forbidden"' in text, 'absence des répertoires techniques production non prouvée')
    require(errors, 'test ! -e "_preview_site/$forbidden"' in text, 'absence des répertoires techniques preview non prouvée')
    require(errors, 'test ! -e "_pages_site/$forbidden"' in text, 'absence des répertoires techniques Pages non prouvée')
    require(errors, 'actions/deploy-pages@' not in text, 'workflow artefact ne doit jamais déployer GitHub Pages')
    require(errors, 'actions/configure-pages@' not in text, 'workflow artefact ne doit pas configurer GitHub Pages')
    require(errors, 'pages: write' not in text, 'permission Pages write interdite au workflow artefact')
    require(errors, 'id-token: write' not in text, 'permission OIDC write interdite au workflow artefact')
    require(errors, 'contents: write' not in text, 'permission contents write interdite au workflow artefact')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'workflow artefact ne doit référencer aucun secret')
    require(errors, 'Aucun déploiement n’est effectué par ce workflow.' in text, 'résumé non-déploiement absent du workflow artefact')

    targets = action_targets(text)
    require(errors, len(targets) == 5, f'nombre inattendu d’actions dans le workflow artefact: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'action artefact non immuable: {target}')
    return errors

def validate_pages_deploy_workflow_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'workflow_dispatch:' in text, 'confinement Pages doit rester manuel')
    require(errors, 'pull_request:' not in text, 'confinement Pages ne doit jamais partir sur pull_request')
    require(errors, 'push:' not in text, 'confinement Pages ne doit jamais partir sur push')
    require(errors, 'confirm_containment:' in text, 'confirmation explicite confinement absente')
    require(errors, 'acknowledge_header_gap:' in text, 'reconnaissance explicite du déficit headers absente')
    require(errors, 'expected_sha:' in text, 'SHA approuvé explicite absent')
    guard = "github.ref == 'refs/heads/main' && inputs.confirm_containment == 'CONTAIN' && inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'"
    require(errors, text.count(guard) == 2, 'double garde main + CONTAIN + ACK_HEADER_GAP requise')
    require(errors, 'group: pages-production-isolated' in text, 'concurrency Pages dédiée absente')
    require(errors, 'cancel-in-progress: false' in text, 'confinement Pages ne doit jamais être annulé automatiquement')
    require(errors, 'contents: write' not in text, 'confinement Pages ne doit jamais écrire dans le dépôt')
    require(errors, text.count('contents: read') >= 2, 'build Pages doit rester contents:read')
    require(errors, 'pages: write' in text, 'permission Pages write requise uniquement pour la publication')
    require(errors, 'id-token: write' in text, 'permission OIDC requise pour deploy-pages')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'confinement Pages ne doit référencer aucun secret')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'confinement Pages doit utiliser Ubuntu 24.04')
    require(errors, f'uses: actions/checkout@{CHECKOUT_SHA}' in text, 'checkout Pages non épinglé')
    require(errors, 'persist-credentials: false' in text, 'checkout Pages doit désactiver les credentials Git')
    require(errors, f'uses: actions/setup-python@{SETUP_PYTHON_SHA}' in text, 'setup-python Pages non épinglé')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python Pages inattendue')
    require(errors, f'uses: actions/upload-pages-artifact@{UPLOAD_PAGES_ARTIFACT_SHA}' in text, 'upload-pages-artifact non épinglé')
    require(errors, f'uses: actions/deploy-pages@{DEPLOY_PAGES_SHA}' in text, 'deploy-pages non épinglé')
    require(errors, exact_run_count(text, NETLIFY_PUBLIC_CHECK) == 1, 'validation allowlist Pages absente ou dupliquée')
    require(errors, exact_run_count(text, PAGES_PUBLIC_BUILD) == 1, 'construction _site Pages absente ou dupliquée')
    require(errors, '--standalone-netlify' not in text, 'artefact GitHub Pages ne doit pas dépendre des fichiers Netlify')
    require(errors, 'path: _site' in text, 'upload Pages doit cibler _site')
    require(errors, 'path: .' not in text, 'publication de la racine du dépôt interdite')
    require(errors, 'test ! -e _site/_headers' in text, '_headers Netlify doit rester hors artefact Pages')
    require(errors, 'test ! -e _site/_redirects' in text, '_redirects Netlify doit rester hors artefact Pages')
    require(errors, 'test ! -e _site/script.js' in text, 'script.js racine legacy doit rester hors Pages')
    require(errors, 'forbidden in .github docs mobile-native scripts supabase tests' in text, 'garde répertoires techniques Pages absente')
    require(errors, 'https://formspree.io/f/xdenkzrv' in text and 'https://formspree.io/f/xkolwjdg' in text, 'garde endpoints Formspree historiques Pages absente')
    require(errors, 'EXPECTED_SHA' in text and '[ "$EXPECTED_SHA" != "$GITHUB_SHA" ]' in text, 'garde SHA exact Pages absente')
    require(errors, 'needs: build' in text, 'publication Pages doit dépendre du build vérifié')
    require(errors, 'name: github-pages' in text, 'Environment github-pages absent')
    require(errors, 'url: ${{ steps.deployment.outputs.page_url }}' in text, 'URL environnement Pages absente')
    require(errors, 'id: deployment' in text, 'étape deploy Pages identifiable absente')
    require(errors, 'Racine du dépôt : **non publiée**' in text, 'preuve de frontière Pages absente du résumé')
    require(errors, 'Mode : **confinement temporaire**' in text, 'statut confinement temporaire absent du résumé')
    require(errors, 'les en-têtes HTTP complets de #450 ne sont pas fournis par GitHub Pages' in text, 'limite headers GitHub Pages absente')
    require(errors, 'Cible finale #450 : **Netlify avec _headers/_redirects**' in text, 'cible finale Netlify absente')
    targets = action_targets(text)
    require(errors, len(targets) == 4, f'nombre inattendu d’actions dans le workflow Pages: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'action Pages non immuable: {target}')
    return errors


def run_pages_deploy_self_tests(text: str) -> None:
    guard = "github.ref == 'refs/heads/main' && inputs.confirm_containment == 'CONTAIN' && inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'"
    cases = {
        'déclenchement push ajouté': text.replace('  workflow_dispatch:\n', '  push:\n  workflow_dispatch:\n', 1),
        'garde main retirée': text.replace("github.ref == 'refs/heads/main'", 'true', 1),
        'confirmation confinement retirée': text.replace("inputs.confirm_containment == 'CONTAIN'", 'true', 1),
        'reconnaissance headers retirée': text.replace("inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'", 'true', 1),
        'SHA attendu retiré': text.replace('      expected_sha:\n', '      autre_sha:\n', 1),
        'publication racine': text.replace('          path: _site\n', '          path: .\n', 1),
        'build racine': text.replace(PAGES_PUBLIC_BUILD, 'python3 scripts/build_netlify_public.py --output .', 1),
        'upload Pages mobile': text.replace(f'actions/upload-pages-artifact@{UPLOAD_PAGES_ARTIFACT_SHA}', 'actions/upload-pages-artifact@v3', 1),
        'deploy Pages mobile': text.replace(f'actions/deploy-pages@{DEPLOY_PAGES_SHA}', 'actions/deploy-pages@v5', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'garde dossiers retirée': text.replace('          for forbidden in .github docs mobile-native scripts supabase tests; do\n', '', 1),
        'secret ajouté': text.replace('    steps:\n', '    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}\n    steps:\n', 1),
        'limite headers retirée': text.replace('            echo "- Limite connue : **les en-têtes HTTP complets de #450 ne sont pas fournis par GitHub Pages**"\n', '', 1),
        'cible Netlify retirée': text.replace('            echo "- Cible finale #450 : **Netlify avec _headers/_redirects**"\n', '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test Pages: mutation sans effet: {name}')
        if not validate_pages_deploy_workflow_text(mutated):
            raise SystemExit(f'ERREUR auto-test Pages: mutation non détectée: {name}')
    print(f'OK auto-tests Pages: {len(cases)} affaiblissements critiques détectés.')


def validate_anon_netlify_preview_workflow_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'pull_request:' in text, 'preview Netlify anonyme doit partir uniquement d’une PR')
    require(errors, 'push:' not in text, 'preview Netlify anonyme ne doit jamais partir sur push')
    require(errors, 'workflow_dispatch:' not in text, 'preview anonyme ne doit pas exposer de dispatch non contrôlé')
    require(errors, "if: startsWith(github.head_ref, 'a1/web-release-')" in text, 'garde branche web-only absente du preview anonyme')
    require(errors, 'permissions:\n  contents: read' in text, 'preview anonyme doit rester contents:read')
    require(errors, 'contents: write' not in text, 'preview anonyme ne doit jamais écrire dans le dépôt')
    require(errors, 'pages: write' not in text and 'id-token: write' not in text, 'preview anonyme ne doit recevoir aucune permission de déploiement GitHub')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'preview anonyme ne doit référencer aucun secret')
    require(errors, 'cancel-in-progress: false' in text, 'preview anonyme déclenché ne doit pas être annulé')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'preview anonyme doit utiliser Ubuntu 24.04')
    require(errors, 'timeout-minutes: 12' in text, 'preview anonyme doit rester borné à 12 minutes')
    require(errors, f'uses: actions/checkout@{CHECKOUT_SHA}' in text, 'checkout preview anonyme non épinglé')
    require(errors, 'ref: ${{ github.event.pull_request.head.sha }}' in text, 'preview anonyme doit checkout le SHA HEAD PR exact')
    require(errors, 'persist-credentials: false' in text, 'preview anonyme doit désactiver les credentials Git')
    require(errors, f'uses: actions/setup-python@{SETUP_PYTHON_SHA}' in text, 'setup-python preview anonyme non épinglé')
    require(errors, f'uses: actions/setup-node@{SETUP_NODE_SHA}' in text, 'setup-node preview anonyme non épinglé')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python preview anonyme inattendue')
    require(errors, f"node-version: '{NODE_VERSION}'" in text, 'version Node preview anonyme inattendue')
    require(errors, '[netlify-anon-preview]' in text, 'marqueur explicite preview anonyme absent')
    require(errors, "steps.gate.outputs.enabled == 'true'" in text, 'garde de déploiement preview anonyme absente')
    require(errors, exact_run_count(text, NETLIFY_PUBLIC_CHECK) == 1, 'validation allowlist preview anonyme absente ou dupliquée')
    require(errors, exact_run_count(text, WEB_PREVIEW_ARTIFACT_BUILD) == 1, 'build preview autonome absent ou dupliqué')
    require(errors, 'CONTEXT: deploy-preview' in text, 'contexte deploy-preview absent')
    require(errors, 'X-Robots-Tag: noindex, nofollow, noarchive' in text, 'preuve noindex preview anonyme absente')
    require(errors, 'forbidden in .github docs mobile-native scripts supabase tests' in text, 'garde répertoires techniques preview anonyme absente')
    require(errors, 'https://formspree.io/f/xdenkzrv' in text and 'https://formspree.io/f/xkolwjdg' in text, 'garde Formspree historique preview anonyme absente')
    deploy_cmd = f'netlify-cli@{NETLIFY_CLI_VERSION} deploy --allow-anonymous --created-via integration --dir _preview_site --no-build --json'
    require(errors, deploy_cmd in text, 'commande Netlify anonyme figée absente')
    require(errors, 'timeout 240s npx --yes ' + deploy_cmd in text, 'déploiement Netlify anonyme doit être borné à 240 secondes')
    require(errors, '--prod' not in text, 'flag --prod interdit au preview anonyme')
    require(errors, '--auth' not in text and 'NETLIFY_AUTH_TOKEN' not in text, 'auth/token Netlify interdit au preview anonyme')
    require(errors, re.search(r'--site(?:\s|=)', text) is None, 'site Netlify existant interdit au preview anonyme')
    require(errors, '--site-name' not in text, 'création de site nommé interdite au preview anonyme')
    require(errors, '--created-via integration' in text, 'preview anonyme doit utiliser le mode integration sans mot de passe Drop')
    require(errors, "if data.get('password'):" in text, 'garde mot de passe Netlify anonyme absente')
    require(errors, '2>"$deploy_err"' in text, 'stderr Netlify doit être capturé hors logs')
    require(errors, 'cat "$deploy_json"' not in text and 'cat "$deploy_err"' not in text, 'sortie brute Netlify ne doit jamais être journalisée')
    require(errors, 'rm -f "$deploy_json" "$deploy_err"' in text, 'fichiers temporaires Netlify doivent être supprimés')
    require(errors, "raw_url = data.get('site_url')" in text, 'lecture explicite site_url Netlify absente')
    require(errors, "deploy_id = data.get('deploy_id')" in text, 'lecture explicite deploy_id Netlify absente')
    require(errors, "safe_keys = ','.join(sorted(str(key) for key in data.keys()))" in text, 'diagnostic sûr des clés JSON Netlify absent')
    require(errors, "raw_url.startswith('http://')" in text and "'https://' + raw_url" in text, 'normalisation HTTPS site_url absente')
    require(errors, "re.fullmatch(r'[a-z0-9-]+\\.netlify\\.app', site_host)" in text, 'validation stricte site_url preview anonyme absente')
    require(errors, "re.fullmatch(r'[a-z0-9-]{6,64}', deploy_id)" in text, 'validation stricte deploy_id preview anonyme absente')
    require(errors, "host = f'{deploy_id}--{site_host}'" in text, 'construction permalink immuable Netlify absente')
    require(errors, "re.fullmatch(r'[a-z0-9-]{6,64}--[a-z0-9-]+\\.netlify\\.app', host)" in text, 'validation stricte permalink Netlify absente')
    require(errors, "parsed.query" in text and "parsed.fragment" in text, 'refus query/fragment site_url absent')
    require(errors, "fh.write(f'NETLIFY_SITE_URL={raw_url}\\n')" in text, 'export alias principal Netlify absent')
    require(errors, "fh.write(f'NETLIFY_DEPLOY_URL={deploy_url}\\n')" in text, 'export permalink Netlify absent')
    require(errors, 'python3 scripts/validate_web_release_http.py "$NETLIFY_SITE_URL" --context preview' in text, 'smoke alias principal Netlify absent')
    require(errors, 'python3 scripts/validate_web_release_http.py "$NETLIFY_DEPLOY_URL" --context preview' in text, 'smoke permalink Netlify absent')
    require(errors, 'id: smoke_site' in text and 'id: smoke_deploy' in text, 'deux smokes Netlify identifiables requis')
    require(errors, text.count('continue-on-error: true') == 2, 'les deux diagnostics Netlify doivent rester non bloquants')
    require(errors, 'SITE_OUTCOME: ${{ steps.smoke_site.outcome }}' in text, 'résultat smoke alias absent du résumé')
    require(errors, 'DEPLOY_OUTCOME: ${{ steps.smoke_deploy.outcome }}' in text, 'résultat smoke permalink absent du résumé')
    require(errors, 'INCOMPATIBLE — diagnostic non bloquant' in text, 'verdict diagnostic anonyme non bloquant absent')
    require(errors, 'jamais une porte de release' in text, 'frontière release du diagnostic anonyme absente')
    require(errors, 'Jeton de réclamation : **non journalisé et non conservé**' in text, 'preuve non-conservation token absente')
    require(errors, 'Production/DNS : **inchangés**' in text, 'preuve non-production absente')
    targets = action_targets(text)
    require(errors, len(targets) == 3, f'nombre inattendu d’actions dans le workflow preview anonyme: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'action preview anonyme non immuable: {target}')
    return errors


def run_anon_netlify_preview_self_tests(text: str) -> None:
    cases = {
        'déclenchement push ajouté': text.replace('  pull_request:\n', '  push:\n  pull_request:\n', 1),
        'permission écriture ajoutée': text.replace('contents: read', 'contents: write', 1),
        'secret ajouté': text.replace('    steps:\n', '    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}\n    steps:\n', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'marqueur retiré': text.replace('[netlify-anon-preview]', '[preview]'),
        'anonyme retiré': text.replace('--allow-anonymous', ''),
        'diagnostic alias rendu bloquant': text.replace('        continue-on-error: true\n', '', 1),
        'diagnostic permalink rendu bloquant': text.replace('        continue-on-error: true\n', '', 2),
        'frontière release retirée': text.replace("            echo '- Portée : **preuve de capacité uniquement; jamais une porte de release**'\n", '', 1),
        'mode integration retiré': text.replace('--created-via integration', ''),
        'prod ajouté': text.replace('--no-build --json', '--no-build --json --prod', 1),
        'version CLI mobile': text.replace(f'netlify-cli@{NETLIFY_CLI_VERSION}', 'netlify-cli@latest', 1),
        'noindex retiré': text.replace("          grep -Fq 'X-Robots-Tag: noindex, nofollow, noarchive' <<<\"$preview_global_headers\"\n", '', 1),
        'site_url retiré': text.replace("          raw_url = data.get('site_url')\n", "          raw_url = data.get('url')\n", 1),
        'deploy_id retiré': text.replace("          deploy_id = data.get('deploy_id')\n", "          deploy_id = data.get('id')\n", 1),
        'permalink retiré': text.replace("          host = f'{deploy_id}--{site_host}'\n", "          host = site_host\n", 1),
        'sortie brute exposée': text.replace("          python3 - \"$deploy_json\" <<'PY'\n", "          cat \"$deploy_json\"\n          python3 - \"$deploy_json\" <<'PY'\n", 1),
        'smoke alias retiré': text.replace('        run: python3 scripts/validate_web_release_http.py "$NETLIFY_SITE_URL" --context preview\n', '', 1),
        'smoke permalink retiré': text.replace('        run: python3 scripts/validate_web_release_http.py "$NETLIFY_DEPLOY_URL" --context preview\n', '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test preview Netlify anonyme: mutation sans effet: {name}')
        if not validate_anon_netlify_preview_workflow_text(mutated):
            raise SystemExit(f'ERREUR auto-test preview Netlify anonyme: mutation non détectée: {name}')
    print(f'OK auto-tests preview Netlify anonyme: {len(cases)} affaiblissements critiques détectés.')


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
    require(errors, 'inputs:' not in text, 'production smoke ne doit accepter aucune entrée utilisateur')
    require(errors, "if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/heads/a1/web-release-')" in text, 'production smoke doit rester borné à main ou une branche web-release')
    require(errors, exact_run_count(text, WEB_RELEASE_HTTP_SELF) == 1, 'auto-test smoke HTTP production absent ou dupliqué')
    require(
        errors,
        'python3 scripts/validate_web_release_http.py https://www.benoitcantin.com --context production --require-netlify --expected-sha "$GITHUB_SHA"' in text,
        'commande smoke production doit lier la preuve au GITHUB_SHA et exiger Netlify',
    )
    require(errors, 'python3 scripts/validate_web_release_http.py https://benoitcantin.com --check-apex-redirect' in text, 'preuve redirection apex officielle absente')
    require(errors, 'Hébergement : **signature Netlify confirmée**' in text, 'preuve hébergement Netlify absente du résumé production')
    require(errors, 'Apex : \\`https://benoitcantin.com/\\` → \\`https://www.benoitcantin.com/\\` (**301/308 + Netlify** )' in text, 'preuve apex canonique absente du résumé production')
    require(errors, '### Smoke HTTP — production officielle' in text, 'résumé preuve production absent')
    require(errors, 'GITHUB_STEP_SUMMARY' in text, 'production smoke doit écrire une preuve dans GITHUB_STEP_SUMMARY')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'production smoke ne doit référencer aucun secret')
    require(errors, 'contents: write' not in text, 'production smoke ne doit jamais écrire dans le dépôt')
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
        'garde noindex production retirée': text.replace('            echo "ERREUR: noindex global interdit dans l’artefact production." >&2\n', '', 1),
        'garde noindex preview retirée': text.replace('            echo "ERREUR: noindex global requis dans l’artefact preview." >&2\n', '', 1),
        'script legacy production réintroduit': text.replace('          test ! -e _site/script.js\n', '', 1),
        'script legacy preview réintroduit': text.replace('          test ! -e _preview_site/script.js\n', '', 1),
        'script legacy Pages réintroduit': text.replace('          test ! -e _pages_site/script.js\n', '', 1),
        'build Pages retiré': text.replace(f'        run: {WEB_PAGES_ARTIFACT_BUILD}\n', '', 1),
        'garde Formspree production retirée': text.replace('          for endpoint in "https://formspree.io/f/xdenkzrv" "https://formspree.io/f/xkolwjdg"; do\n', '', 1),
        'SHA source artefact retiré': text.replace('      SINJIRA_RELEASE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}\n', '', 1),
        'release.json production retiré': text.replace('          test -f _site/.well-known/release.json\n', '', 1),
        'no-store release production retiré': text.replace('          grep -Fq "Cache-Control: no-store" <<<"$production_release_headers"\n', '', 1),
        'no-store release preview retiré': text.replace('          grep -Fq "Cache-Control: no-store" <<<"$preview_release_headers"\n', '', 1),
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
        'garde ref production retirée': text.replace("    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/heads/a1/web-release-')\n", '', 1),
        'preuve Netlify retirée de la commande': text.replace(' --require-netlify', '', 1),
        'preuve SHA GITHUB retirée de la commande': text.replace(' --expected-sha "$GITHUB_SHA"', '', 1),
        'preuve apex retirée': text.replace('        run: python3 scripts/validate_web_release_http.py https://benoitcantin.com --check-apex-redirect\n', '', 1),
        'input arbitraire ajouté': text.replace('  workflow_dispatch:\n', '  workflow_dispatch:\n    inputs:\n      expected_sha:\n        required: true\n', 1),
        'secret ajouté': text.replace('    steps:\n', '    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}\n    steps:\n', 1),
        'résumé hébergeur retiré': text.replace('            echo "- Hébergement : **signature Netlify confirmée**"\n', '', 1),
        'résumé apex retiré': text.replace('            echo "- Apex : \\`https://benoitcantin.com/\\` → \\`https://www.benoitcantin.com/\\` (**301/308 + Netlify** )"\n', '', 1),
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
        'garde ref preview retirée': text.replace("    if: startsWith(github.ref, 'refs/heads/a1/web-release-')\n", '', 1),
        'preuve SHA GITHUB retirée de la commande': text.replace(' --expected-sha "$GITHUB_SHA"', '', 1),
        'SHA manuel ajouté': text.replace('      deploy_permalink:\n', '      expected_sha:\n        required: true\n      deploy_permalink:\n', 1),
        'alias preview réintroduit': text.replace('      deploy_permalink:\n', '      preview_url:\n', 1),
        'description permalink non quotée': text.replace(
            '        description: "Permalink atomique Netlify (DEPLOY_URL: deploy-id--site.netlify.app), jamais un alias preview/branche"\n',
            '        description: Permalink atomique Netlify (DEPLOY_URL: deploy-id--site.netlify.app), jamais un alias preview/branche\n',
            1,
        ),
        'production-candidate retiré': text.replace('          - production-candidate\n', '', 1),
        'choice contexte retiré': text.replace('        type: choice\n', '        type: string\n', 1),
        'contexte env retiré': text.replace('      SMOKE_CONTEXT: ${{ inputs.artifact_context }}\n', '', 1),
        'contexte forcé preview': text.replace(' --context "$SMOKE_CONTEXT"', ' --context preview', 1),
        'injection directe URL': text.replace(
            'python3 scripts/validate_web_release_http.py "$DEPLOY_PERMALINK" --context "$SMOKE_CONTEXT" --expected-sha "$GITHUB_SHA"',
            'python3 scripts/validate_web_release_http.py "${{ inputs.deploy_permalink }}" --context "$SMOKE_CONTEXT" --expected-sha "$GITHUB_SHA"',
            1,
        ),
        'secret ajouté': text.replace(
            'DEPLOY_PERMALINK: ${{ inputs.deploy_permalink }}',
            'DEPLOY_PERMALINK: ${{ secrets.DEPLOY_PERMALINK }}',
            1,
        ),
        'résumé preuve retiré': text.replace('            echo "### Smoke HTTP — permalink atomique Netlify"\n', '', 1),
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
        'auto-test transition Formspree retiré': text.replace(f'        run: {PERSONAL_FORMSPREE_CONFIG_SELF}\n', '', 1),
        'auto-test Environments production retiré': text.replace(f'        run: {PRODUCTION_ENVIRONMENT_SELF}\n', '', 1),
        'validation Environments production retirée': text.replace(f'        run: {PRODUCTION_ENVIRONMENT_VALIDATE}\n', '', 1),
        'historique Git retiré': text.replace('          fetch-depth: 0\n', '', 1),
        'auto-test portée web retiré': text.replace(f'        run: {WEB_RELEASE_SCOPE_SELF}\n', '', 1),
        'validation portée web retirée': text.replace(f'        run: {WEB_RELEASE_SCOPE_VALIDATE}\n', '', 1),
        'condition portée web élargie': text.replace(WEB_RELEASE_SCOPE_IF, "if: github.event_name == 'pull_request'", 1),
        'auto-test smoke HTTP retiré': text.replace(f'        run: {WEB_RELEASE_HTTP_SELF}\n', '', 1),
        'baseline production retiré': text.replace('            echo "### Baseline smoke production — lecture seule"\n', '', 1),
        'baseline cible dangereuse': text.replace('            echo "- Cible : $origin"\n', '            echo "- Cible : `$origin`"\n', 1),
        'baseline apex retiré': text.replace('          apex_origin="https://benoitcantin.com"\n', '', 1),
        'baseline Location apex retirée': text.replace('            echo "- Apex Location : \\`${apex_location:-absente}\\`"\n', '', 1),
        'résumé readiness retiré': text.replace('            echo "### Readiness web-only"\n', '', 1),
        'état fail-closed readiness retiré': text.replace('            echo "- BubblaV : **fail-closed** (widget désactivé + CSP bloquante)"\n', '', 1),
        'smoke deploy readiness retiré': text.replace('            echo "- Smoke deploy unitaire : \\`Netlify deploy — smoke HTTP\\` (permalink atomique, preview / production-candidate)"\n', '', 1),
        'gate pré-DNS readiness retiré': text.replace('            echo "- Gate pré-DNS combiné : \\`Netlify pré-DNS — gate combiné\\` (même site Netlify + même SHA)"\n', '', 1),
        'preuve Netlify readiness retirée': text.replace('            echo "- Smoke production : \\`Web production — smoke HTTP\\` (SHA + signature Netlify + apex canonique)"\n', '', 1),
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
    if not NETLIFY_PRE_DNS_WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: gate pré-DNS absent: {NETLIFY_PRE_DNS_WORKFLOW.relative_to(ROOT)}')
    if not PRODUCTION_WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow production absent: {PRODUCTION_WORKFLOW.relative_to(ROOT)}')
    if not ARTIFACT_WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow artefact absent: {ARTIFACT_WORKFLOW.relative_to(ROOT)}')
    if not PAGES_DEPLOY_WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow Pages isolé absent: {PAGES_DEPLOY_WORKFLOW.relative_to(ROOT)}')
    if not ANON_NETLIFY_PREVIEW_WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow preview Netlify anonyme absent: {ANON_NETLIFY_PREVIEW_WORKFLOW.relative_to(ROOT)}')

    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    preview_text = PREVIEW_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    netlify_pre_dns_text = NETLIFY_PRE_DNS_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    production_text = PRODUCTION_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    artifact_text = ARTIFACT_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    pages_deploy_text = PAGES_DEPLOY_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    anon_netlify_preview_text = ANON_NETLIFY_PREVIEW_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        run_preview_self_tests(preview_text)
        run_netlify_pre_dns_self_tests(netlify_pre_dns_text)
        run_production_self_tests(production_text)
        run_artifact_self_tests(artifact_text)
        run_pages_deploy_self_tests(pages_deploy_text)
        run_anon_netlify_preview_self_tests(anon_netlify_preview_text)
        return 0

    errors = validate_text(text)
    errors.extend(validate_preview_workflow_text(preview_text))
    errors.extend(validate_netlify_pre_dns_workflow_text(netlify_pre_dns_text))
    errors.extend(validate_production_workflow_text(production_text))
    errors.extend(validate_artifact_workflow_text(artifact_text))
    errors.extend(validate_pages_deploy_workflow_text(pages_deploy_text))
    errors.extend(validate_anon_netlify_preview_workflow_text(anon_netlify_preview_text))
    if errors:
        for error in errors:
            print(f'ERREUR sécurité validation site: {error}')
        return 1
    print(
        'OK sécurité validation site: actions immuables, runtimes figés, credentials non persistés, '
        'garde web-only, artefact public inspectable non-déployant, diagnostic Netlify anonyme non bloquant, confinement Pages manuel isolé et smokes read-only obligatoires.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
