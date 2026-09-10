#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-personal-ai-functional-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_SUPABASE = 'supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
SELF_TEST = 'python3 scripts/validate_personal_ai_functional_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_personal_ai_functional_workflow_security.py'
HISTORICAL = (
    'python3 scripts/validate_personal_ai_v25.py',
    'python3 scripts/validate_sensitive_aal2_smoke.py',
    'python3 scripts/validate_personal_ai_functional_smoke.py',
    'python3 scripts/validate_production_schema_manifest.py',
    'supabase start',
    'supabase test db supabase/tests/personal_ai_v25.test.sql --local',
    'supabase stop --no-backup || true',
)
TRIGGER_PATHS = (
    "      - 'scripts/smoke_personal_ai_functional_local.py'",
    "      - 'scripts/validate_personal_ai_functional_smoke.py'",
    "      - 'scripts/smoke_sensitive_aal2_local.py'",
    "      - 'scripts/validate_sensitive_aal2_smoke.py'",
    "      - 'scripts/validate_personal_ai_v25.py'",
    "      - 'scripts/validate_production_schema_manifest.py'",
    "      - 'scripts/validate_personal_ai_functional_workflow_security.py'",
    "      - 'supabase/tests/personal_ai_v25.test.sql'",
    "      - 'supabase/functions/personal-ai/**'",
    "      - 'supabase/functions/_shared/auth.ts'",
    "      - 'supabase/functions/_shared/cors.ts'",
    "      - 'supabase/migrations/**personal_ai**.sql'",
    "      - 'supabase/migrations/**security**.sql'",
    "      - 'supabase/config.toml'",
    "      - '.github/workflows/sinjira-personal-ai-functional-v25.yml'",
)
FUNCTIONAL_BLOCK = '''        run: |
          set -euo pipefail
          status_env="$(supabase status -o env)"
          API_URL="$(sed -n 's/^API_URL="\\(.*\\)"$/\\1/p' <<< "$status_env" | head -n1)"
          ANON_KEY="$(sed -n 's/^ANON_KEY="\\(.*\\)"$/\\1/p' <<< "$status_env" | head -n1)"
          test -n "$API_URL"
          test -n "$ANON_KEY"
          SINJIRA_LOCAL_API_URL="$API_URL" \\
          SINJIRA_LOCAL_ANON_KEY="$ANON_KEY" \\
            python3 scripts/smoke_personal_ai_functional_local.py
'''


def fail(message: str) -> None:
    raise ValueError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def exact_single_line_runs(text: str) -> list[str]:
    commands: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('run: ') and stripped != 'run: |':
            commands.append(stripped.removeprefix('run: '))
    return commands


def validate_text(text: str) -> None:
    active = active_text(text)
    require('pull_request:\n    branches: [main]' in text, 'Les PR Mon IA doivent rester ciblées vers main.')
    require('push:\n    branches: [main]' in text, 'Le push main doit rester couvert tant que #135 n’est pas prouvé.')
    require('workflow_dispatch:' in text, 'Le déclenchement manuel historique doit rester disponible.')
    for path in TRIGGER_PATHS:
        require(text.count(path) == 2, f'Le chemin doit couvrir PR et push: {path.strip()}')

    require('permissions:\n  contents: read' in text, 'Le token GitHub doit rester en lecture seule.')
    require('runs-on: ubuntu-24.04' in text, 'Le runner doit rester figé sur Ubuntu 24.04.')
    require('ubuntu-latest' not in active, 'ubuntu-latest est interdit.')
    require('timeout-minutes: 20' in text, 'Le timeout de 20 minutes doit rester présent.')

    uses = [line.strip().split('uses:', 1)[1].strip().split()[0] for line in active.splitlines() if line.strip().startswith('uses: ')]
    require(uses == [CHECKOUT, SETUP_PYTHON, SETUP_SUPABASE], f'Actions inattendues ou ordre modifié: {uses}')
    for action in uses:
        require(re.search(r'@[0-9a-f]{40}$', action) is not None, f'Action non immuable: {action}')

    require('persist-credentials: false' in text, 'Les credentials Git ne doivent pas être persistés.')
    require("python-version: '3.12.14'" in text, 'Python doit rester figé à 3.12.14.')
    require('          version: 2.111.0' in text, 'Supabase CLI doit rester figé à 2.111.0.')
    require(exact_single_line_runs(text) == [SELF_TEST, SELF_CHECK, *HISTORICAL], 'Les commandes simples ou leur ordre ont changé hors contrat.')

    require(text.count('        shell: bash') == 1, 'Le smoke fonctionnel doit rester dans un shell bash explicite unique.')
    require(text.count(FUNCTIONAL_BLOCK) == 1, 'Le bloc fonctionnel local Mon IA doit rester exact et unique.')
    require(text.count('        if: always()') == 1, 'Le nettoyage Supabase local doit rester protégé par if: always().')
    require('supabase db start' not in active, 'Le smoke fonctionnel exige la pile Supabase locale complète, pas db start seul.')

    pg_index = text.index('supabase test db supabase/tests/personal_ai_v25.test.sql --local')
    smoke_index = text.index('python3 scripts/smoke_personal_ai_functional_local.py')
    require(pg_index < smoke_index, 'pgTAP doit réussir avant le smoke HTTP AAL2.')

    forbidden = (
        '${{ secrets.', 'contents: write', 'persist-credentials: true', 'environment: production',
        'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD', 'SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_ROLE_KEY',
        'supabase link', 'supabase db push', 'supabase functions deploy', 'supabase secrets set',
        'supabase migration repair', '--linked', '--no-verify-jwt', 'curl ', 'wget ', 'gh api', 'git push',
        'continue-on-error: true', 'set -x',
    )
    found = [marker for marker in forbidden if marker in active]
    require(not found, f'Écriture, secret, accès Supabase distant ou contournement interdit: {found}')


def mutation_cases(text: str) -> tuple[tuple[str, str], ...]:
    cleanup_anchor = '      - name: Arrêter Supabase local\n'
    return (
        ('runner mutable', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)),
        ('checkout mutable', text.replace(CHECKOUT, 'actions/checkout@v6', 1)),
        ('setup-python mutable', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)),
        ('setup-supabase mutable', text.replace(SETUP_SUPABASE, 'supabase/setup-cli@v2', 1)),
        ('Python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ('Supabase CLI large', text.replace('          version: 2.111.0', '          version: 2', 1)),
        ('credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)),
        ('permissions write', text.replace('contents: read', 'contents: write', 1)),
        ('timeout retiré', text.replace('    timeout-minutes: 20\n', '', 1)),
        ('secret injecté', text.replace('    steps:\n', '    env:\n      LEAK: "${{ secrets.SUPABASE_ACCESS_TOKEN }}"\n    steps:\n', 1)),
        ('production injectée', text.replace('    timeout-minutes: 20\n', '    timeout-minutes: 20\n    environment: production\n', 1)),
        ('push main retiré', text.replace('  push:\n    branches: [main]\n', '  push:\n    branches: [ai-functional]\n', 1)),
        ('workflow dispatch retiré', text.replace('  workflow_dispatch:\n', '', 1)),
        ('chemin smoke retiré', text.replace("      - 'scripts/smoke_personal_ai_functional_local.py'\n", '', 1)),
        ('chemin garde fonctionnel retiré', text.replace("      - 'scripts/validate_personal_ai_functional_smoke.py'\n", '', 1)),
        ('chemin helper AAL2 retiré', text.replace("      - 'scripts/smoke_sensitive_aal2_local.py'\n", '', 1)),
        ('chemin garde AAL2 retiré', text.replace("      - 'scripts/validate_sensitive_aal2_smoke.py'\n", '', 1)),
        ('chemin garde CI retiré', text.replace("      - 'scripts/validate_personal_ai_functional_workflow_security.py'\n", '', 1)),
        ('chemin pgTAP retiré', text.replace("      - 'supabase/tests/personal_ai_v25.test.sql'\n", '', 1)),
        ('chemin Edge retiré', text.replace("      - 'supabase/functions/personal-ai/**'\n", '', 1)),
        ('chemin auth retiré', text.replace("      - 'supabase/functions/_shared/auth.ts'\n", '', 1)),
        ('chemin cors retiré', text.replace("      - 'supabase/functions/_shared/cors.ts'\n", '', 1)),
        ('chemin migration IA retiré', text.replace("      - 'supabase/migrations/**personal_ai**.sql'\n", '', 1)),
        ('chemin migration sécurité retiré', text.replace("      - 'supabase/migrations/**security**.sql'\n", '', 1)),
        ('chemin config retiré', text.replace("      - 'supabase/config.toml'\n", '', 1)),
        ('chemin workflow retiré', text.replace("      - '.github/workflows/sinjira-personal-ai-functional-v25.yml'\n", '', 1)),
        ('auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '', 1)),
        ('contrat retiré', text.replace(f'        run: {SELF_CHECK}\n', '', 1)),
        *tuple((f'preuve simple retirée {index + 1}', text.replace(f'        run: {command}\n', '', 1)) for index, command in enumerate(HISTORICAL)),
        ('shell bash retiré', text.replace('        shell: bash\n', '', 1)),
        ('pipefail retiré', text.replace('          set -euo pipefail\n', '          set -eu\n', 1)),
        ('origine status locale retirée', text.replace('supabase status -o env', 'printenv', 1)),
        ('extraction API modifiée', text.replace('          API_URL="$(sed -n', '          API_URL="$(printf', 1)),
        ('extraction anon modifiée', text.replace('          ANON_KEY="$(sed -n', '          ANON_KEY="$(printf', 1)),
        ('preuve API non vide retirée', text.replace('          test -n "$API_URL"\n', '', 1)),
        ('preuve anon non vide retirée', text.replace('          test -n "$ANON_KEY"\n', '', 1)),
        ('variable API locale renommée', text.replace('SINJIRA_LOCAL_API_URL', 'SINJIRA_API_URL', 1)),
        ('variable anon locale renommée', text.replace('SINJIRA_LOCAL_ANON_KEY', 'SINJIRA_ANON_KEY', 1)),
        ('smoke HTTP retiré', text.replace('            python3 scripts/smoke_personal_ai_functional_local.py\n', '', 1)),
        ('cleanup always retiré', text.replace('        if: always()\n', '', 1)),
        ('pile complète réduite', text.replace('        run: supabase start\n', '        run: supabase db start\n', 1)),
        ('test distant', text.replace('--local', '--linked', 1)),
        ('db push ajouté', text.replace(cleanup_anchor, '      - run: supabase db push --linked\n\n' + cleanup_anchor, 1)),
        ('link ajouté', text.replace(cleanup_anchor, '      - run: supabase link --project-ref fake\n\n' + cleanup_anchor, 1)),
        ('deploy fonction ajouté', text.replace(cleanup_anchor, '      - run: supabase functions deploy personal-ai\n\n' + cleanup_anchor, 1)),
        ('secret distant ajouté', text.replace(cleanup_anchor, '      - run: supabase secrets set X=Y\n\n' + cleanup_anchor, 1)),
        ('migration repair ajouté', text.replace(cleanup_anchor, '      - run: supabase migration repair 20260101000000 --status applied\n\n' + cleanup_anchor, 1)),
        ('push Git ajouté', text.replace(cleanup_anchor, '      - run: git push origin HEAD:main\n\n' + cleanup_anchor, 1)),
        ('curl ajouté', text.replace(cleanup_anchor, '      - run: curl https://example.invalid\n\n' + cleanup_anchor, 1)),
        ('continue-on-error ajouté', text.replace('    timeout-minutes: 20\n', '    timeout-minutes: 20\n    continue-on-error: true\n', 1)),
        ('set -x ajouté', text.replace('          set -euo pipefail\n', '          set -euo pipefail\n          set -x\n', 1)),
        ('JWT bypass ajouté', text.replace(cleanup_anchor, '      - run: supabase functions serve personal-ai --no-verify-jwt\n\n' + cleanup_anchor, 1)),
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
    print('OK CI fonctionnelle Mon IA: runtimes/actions immuables, Supabase local complet, AAL2/pgTAP avant smoke HTTP et aucune écriture distante.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
