#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'nova-seo-normalize.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'
TARGET_BRANCH = 'nova-a1-reference-documents'
TARGET_REF = f'refs/heads/{TARGET_BRANCH}'
NORMALIZE_IF = "if: ${{ github.repository == 'M0rdr3x/BenoitCantin' && github.ref == 'refs/heads/nova-a1-reference-documents' }}"
COMMIT_IF = "if: ${{ needs.normalize.outputs.changed == 'true' && github.repository == 'M0rdr3x/BenoitCantin' && github.ref == 'refs/heads/nova-a1-reference-documents' }}"


def fail(message: str) -> None:
    raise ValueError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def section(text: str, start: str, end: str | None = None) -> str:
    begin = text.find(start)
    require(begin >= 0, f'Section absente: {start.strip()}')
    if end is None:
        return text[begin:]
    finish = text.find(end, begin + len(start))
    require(finish >= 0, f'Fin de section absente: {end.strip()}')
    return text[begin:finish]


def action_targets(text: str) -> list[str]:
    return [
        line.split('uses:', 1)[1].strip().split()[0]
        for line in active_text(text).splitlines()
        if line.strip().startswith('uses: ')
    ]


def validate_text(text: str) -> None:
    active = active_text(text)
    normalize = section(text, '  normalize:\n', '  commit:\n')
    commit = section(text, '  commit:\n')

    require('pull_request:' not in active, 'Le workflow d’écriture SEO ne doit jamais tourner sur pull_request.')
    require('workflow_dispatch:' not in active, 'Le workflow d’écriture SEO ne doit pas être déclenchable manuellement.')
    require('paths-ignore:' not in active, 'paths-ignore est interdit pour ce workflow d’écriture.')
    require(f'branches: [ {TARGET_BRANCH} ]' in text, 'La branche de déclenchement SEO doit rester strictement bornée.')
    require("      - 'scripts/normalize_nova_seo.py'" in text, 'Le script de normalisation doit rester dans les chemins déclencheurs.')
    require("      - '.github/workflows/nova-seo-normalize.yml'" in text, 'Le workflow doit se déclencher quand sa définition change.')

    require('permissions:\n  contents: read' in text, 'Les permissions globales doivent rester contents: read.')
    require(text.count('contents: write') == 1, 'Une seule permission contents: write est autorisée, dans le job commit.')
    require('concurrency:\n  group: nova-seo-normalize-reference-documents\n  cancel-in-progress: false' in text, 'La sérialisation des écritures SEO doit rester active.')

    require(NORMALIZE_IF in normalize, 'Le job normalize doit vérifier dépôt et branche exacts.')
    require('permissions:\n      contents: read' in normalize, 'Le job normalize doit rester en lecture seule.')
    require('runs-on: ubuntu-24.04' in normalize, 'Le job normalize doit rester sur Ubuntu 24.04.')
    require('timeout-minutes: 10' in normalize, 'Le timeout normalize doit rester à 10 minutes.')
    require(f'uses: {CHECKOUT}' in normalize, 'Checkout normalize doit rester épinglé.')
    require('ref: ${{ github.sha }}' in normalize, 'Le job normalize doit lire exactement le commit déclencheur.')
    require('persist-credentials: false' in normalize, 'Le job normalize ne doit jamais persister les credentials Git.')
    require(f'uses: {SETUP_PYTHON}' in normalize, 'setup-python normalize doit rester épinglé.')
    require(f"python-version: '{PYTHON_VERSION}'" in normalize, f'Python doit rester figé à {PYTHON_VERSION}.')
    require('run: python3 scripts/normalize_nova_seo.py' in normalize, 'La normalisation historique doit rester exécutée en lecture seule.')
    require('git push' not in normalize, 'Aucun push Git n’est permis dans le job normalize.')
    require('contents: write' not in normalize, 'Le job normalize ne doit jamais obtenir contents: write.')

    for marker in (
        "mapfile -d '' -t changed_files < <(git diff --name-only -z)",
        'if ((${#changed_files[@]} > 24)); then',
        'projets/projet-nova/*.html) ;;',
        'test -f "$path"',
        'test ! -L "$path"',
        'git diff --check',
        'git diff --binary -- projets/projet-nova/*.html | base64 -w0',
        'if ((${#patch_b64} > 900000)); then',
        "echo 'changed=true' >> \"$GITHUB_OUTPUT\"",
        'echo "patch_b64=$patch_b64" >> "$GITHUB_OUTPUT"',
    ):
        require(marker in normalize, f'Frontière de génération du patch absente: {marker}')

    require('needs: normalize' in commit, 'Le job commit doit dépendre du job normalize.')
    require(COMMIT_IF in commit, 'Le job commit doit vérifier patch, dépôt et branche exacts.')
    require('permissions:\n      contents: write' in commit, 'Le job commit doit être le seul détenteur de contents: write.')
    require('runs-on: ubuntu-24.04' in commit, 'Le job commit doit rester sur Ubuntu 24.04.')
    require('timeout-minutes: 5' in commit, 'Le timeout commit doit rester à 5 minutes.')
    require(f'uses: {CHECKOUT}' in commit, 'Checkout commit doit rester épinglé.')
    require(f'ref: {TARGET_BRANCH}' in commit, 'Le checkout d’écriture doit viser uniquement la branche Nova dédiée.')
    require('persist-credentials: true' in commit, 'Le checkout d’écriture doit rendre explicite son unique exception de credentials persistés.')
    require('NOVA_SEO_PATCH_B64: ${{ needs.normalize.outputs.patch_b64 }}' in commit, 'Le job commit doit recevoir uniquement le patch du job read-only.')

    for forbidden in (
        'python ',
        'python3 ',
        'node ',
        'deno ',
        'bun ',
        'npm ',
        'npx ',
        'scripts/',
        './scripts/',
    ):
        require(forbidden not in commit, f'Le job avec token write ne doit exécuter aucun code du dépôt: {forbidden}')

    for marker in (
        "printf '%s' \"$NOVA_SEO_PATCH_B64\" | base64 --decode > /tmp/nova-seo.patch",
        'git apply --check /tmp/nova-seo.patch',
        'git apply /tmp/nova-seo.patch',
        "mapfile -d '' -t changed_files < <(git diff --name-only -z)",
        'test "${#changed_files[@]}" -gt 0',
        'test "${#changed_files[@]}" -le 24',
        'projets/projet-nova/*.html) ;;',
        'test -f "$path"',
        'test ! -L "$path"',
        'git diff --check',
        'git add -- projets/projet-nova/*.html',
        'git diff --cached --quiet',
        'git commit -m "Projet Nova A1 — normalise les métadonnées SEO [seo-autofix]"',
        f'git push origin HEAD:{TARGET_BRANCH}',
    ):
        require(marker in commit, f'Frontière d’écriture SEO absente: {marker}')

    require(commit.count('git push') == 1, 'Un seul push Git est autorisé dans le job commit.')
    require(commit.count('persist-credentials: true') == 1, 'Une seule persistance de credentials est autorisée dans le job commit.')
    require(text.count('persist-credentials: false') == 1, 'Le job read-only doit être l’unique checkout sans credentials persistés.')

    expected_actions = [CHECKOUT, SETUP_PYTHON, CHECKOUT]
    require(action_targets(text) == expected_actions, f'Actions autorisées inattendues: {action_targets(text)}')
    for target in action_targets(text):
        require(re.search(r'@[0-9a-f]{40}$', target) is not None, f'Action non immuable: {target}')

    forbidden_global = (
        'ubuntu-latest',
        '${{ secrets.',
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
        'continue-on-error: true',
        'set -x',
    )
    found = [marker for marker in forbidden_global if marker in active]
    require(not found, f'Surface distante ou contournement interdit: {found}')


def mutation_cases(text: str) -> tuple[tuple[str, str], ...]:
    return (
        ('pull request ajouté', text.replace('  push:\n', '  pull_request:\n    branches: [ main ]\n  push:\n', 1)),
        ('workflow dispatch ajouté', text.replace('permissions:\n', '  workflow_dispatch:\n\npermissions:\n', 1)),
        ('branche mobile', text.replace(f'branches: [ {TARGET_BRANCH} ]', 'branches: [ main ]', 1)),
        ('permissions globales write', text.replace('permissions:\n  contents: read', 'permissions:\n  contents: write', 1)),
        ('concurrency retirée', text.replace('concurrency:\n  group: nova-seo-normalize-reference-documents\n  cancel-in-progress: false\n\n', '', 1)),
        ('runner normalize mobile', text.replace('    runs-on: ubuntu-24.04', '    runs-on: ubuntu-latest', 1)),
        ('checkout normalize mutable', text.replace(CHECKOUT, 'actions/checkout@v6', 1)),
        ('ref normalize branche', text.replace('ref: ${{ github.sha }}', f'ref: {TARGET_BRANCH}', 1)),
        ('credentials normalize persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)),
        ('setup-python mutable', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)),
        ('Python non figé', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ('limite 24 retirée', text.replace('if ((${#changed_files[@]} > 24)); then', 'if false; then', 1)),
        ('symlink normalize non vérifié', text.replace('            test ! -L "$path"\n', '', 1)),
        ('taille patch retirée', text.replace('if ((${#patch_b64} > 900000)); then', 'if false; then', 1)),
        ('secret injecté', text.replace('    outputs:\n', '    env:\n      TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n    outputs:\n', 1)),
        ('push dans normalize', text.replace('      - name: Préparer un correctif HTML borné\n', f'      - run: git push origin HEAD:{TARGET_BRANCH}\n\n      - name: Préparer un correctif HTML borné\n', 1)),
        ('needs commit retiré', text.replace('    needs: normalize\n', '', 1)),
        ('condition changed retirée', text.replace("needs.normalize.outputs.changed == 'true' && ", '', 1)),
        ('permission commit read', text.replace('    permissions:\n      contents: write', '    permissions:\n      contents: read', 1)),
        ('runner commit mobile', text.replace('    runs-on: ubuntu-24.04\n    timeout-minutes: 5', '    runs-on: ubuntu-latest\n    timeout-minutes: 5', 1)),
        ('credentials commit retirés', text.replace('persist-credentials: true', 'persist-credentials: false', 1)),
        ('code dépôt exécuté en write', text.replace('      - name: Appliquer le correctif borné sans exécuter de code du dépôt\n', '      - run: python3 scripts/normalize_nova_seo.py\n\n      - name: Appliquer le correctif borné sans exécuter de code du dépôt\n', 1)),
        ('git apply check retiré', text.replace('          git apply --check /tmp/nova-seo.patch\n', '', 1)),
        ('symlink commit non vérifié', text.replace('            test ! -L "$path"\n', '', 1).replace('            test ! -L "$path"\n', '', 1)),
        ('push vers main', text.replace(f'git push origin HEAD:{TARGET_BRANCH}', 'git push origin HEAD:main', 1)),
        ('continue-on-error', text.replace('    timeout-minutes: 5\n', '    timeout-minutes: 5\n    continue-on-error: true\n', 1)),
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
    print(
        'OK Nova SEO: normalisation en lecture seule, patch HTML borné, '
        'écriture Git isolée sans exécution de code du dépôt et branche cible fixe.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
