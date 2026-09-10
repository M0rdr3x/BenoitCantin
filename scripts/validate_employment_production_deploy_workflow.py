#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-employment-production.yml'
PRODUCTION_URL = 'https://api.supabase.com/v1/projects/gpvivleexywljowcqkru/database/migrations'
TOKEN_REF = 'SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def top_level_block(text: str, start: str, end: str) -> str:
    start_pos = text.find(start)
    if start_pos < 0:
        raise AssertionError(f'Bloc absent: {start.strip()}')
    end_pos = text.find(end, start_pos + len(start))
    if end_pos < 0:
        raise AssertionError(f'Fin de bloc absente: {end.strip()}')
    return text[start_pos:end_pos]


def trigger_keys(block: str) -> set[str]:
    keys: set[str] = set()
    for line in block.splitlines()[1:]:
        match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line)
        if match:
            keys.add(match.group(1))
    return keys


def step_blocks(text: str) -> dict[str, str]:
    matches = list(re.finditer(r'(?m)^      - name: (.+)$', text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks[match.group(1).strip()] = text[match.start():end]
    return blocks


def main() -> int:
    require(WORKFLOW.is_file(), f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')
    workflow = WORKFLOW.read_text('utf-8', errors='strict')
    active = '\n'.join(line for line in workflow.splitlines() if not line.strip().startswith('#'))
    triggers = top_level_block(workflow, 'on:\n', '\npermissions:')

    require(
        trigger_keys(triggers) == {'workflow_dispatch'},
        'La vérification Emploi production doit rester strictement manuelle.',
    )

    required = (
        'name: SINJIRA V25 — Vérification production Emploi',
        'VERIFY-SINJIRA-V25-EMPLOYMENT',
        'permissions:\n  contents: read',
        'environment: production',
        'test "$GITHUB_REF" = "refs/heads/main"',
        'EXPECTED_REMOTE_BASELINE: "20260905131659"',
        'EXPECTED_REMOTE_BASELINE_NAME: sinjira_v25_conscience_vault_audit_session_index',
        'EXPECTED_EMPLOYMENT_VERSION: "20260905133130"',
        'EXPECTED_EMPLOYMENT_NAME: sinjira_v25_employment_foundation',
        'ref: main',
        'persist-credentials: false',
        "curl --proto '=https' --fail-with-body --silent --show-error --request GET",
        f'--url "{PRODUCTION_URL}"',
        'Authorization: Bearer $SUPABASE_ACCESS_TOKEN',
        "Vérifier l'historique Emploi sans secret",
        'MIGRATION_HISTORY="$RUNNER_TEMP/employment-production-migrations.json"',
        'if observed != employment:',
        'if len(matches) != 1:',
        'Aucune migration, aucune Edge Function et aucun secret',
        'Emploi reste séparé du Registre personnel',
    )
    for marker in required:
        require(marker in workflow, f'contrat post-déploiement Emploi: marqueur absent: {marker}')

    forbidden = (
        'SUPABASE_PROJECT_REF',
        'SUPABASE_MANAGEMENT_API',
        'DEPLOY-SINJIRA-V25-EMPLOYMENT',
        'SUPABASE_DB_PASSWORD',
        '--request POST', '--request PUT', '--request PATCH', '--request DELETE',
        'curl -X POST', 'curl -X PUT', 'curl -X PATCH', 'curl -X DELETE',
        '--location', '--proxy', '--connect-to', '--resolve', '--upload-file',
        '--data ', '--data=', '--data-binary', '--form ',
        'supabase link',
        'supabase db push',
        'supabase functions deploy',
        'supabase secrets set',
        'supabase migration repair',
        '--include-all',
        '--linked',
        '--no-verify-jwt',
        'continue-on-error:',
        'set -x',
        'gh api',
        'git push',
    )
    for marker in forbidden:
        require(marker not in active, f'la vérification Emploi doit rester en lecture seule: {marker}')

    require(active.count(PRODUCTION_URL) == 1, 'Une seule URL production Supabase littérale est autorisée.')
    require(len(re.findall(r'(?m)^\s*curl\b', active)) == 1, 'Le workflow Emploi doit effectuer un seul appel curl distant.')

    secret_lines = [line for line in workflow.splitlines() if '${{ secrets.' in line]
    require(
        secret_lines == [f'          {TOKEN_REF}'],
        'SUPABASE_ACCESS_TOKEN doit être l unique secret et rester borné à une seule env d étape.',
    )

    blocks = step_blocks(workflow)
    download = blocks.get("Télécharger l'historique Emploi en lecture seule", '')
    require(download, 'Étape de téléchargement Emploi bornée absente.')
    require(TOKEN_REF in download, 'Le token doit être injecté uniquement dans l étape GET.')
    require(PRODUCTION_URL in download, 'Le GET doit cibler l URL Supabase exacte.')
    require("--proto '=https'" in download and '--request GET' in download, 'Le GET doit imposer HTTPS et la méthode GET.')

    parser = blocks.get("Vérifier l'historique Emploi sans secret", '')
    require(parser, 'Étape de parsing Emploi sans secret absente.')
    require(
        'SUPABASE_ACCESS_TOKEN' not in parser and '${{ secrets.' not in parser,
        'Le parsing de l historique Emploi ne doit recevoir aucun secret.',
    )
    require(
        'MIGRATION_HISTORY="$RUNNER_TEMP/employment-production-migrations.json"' in parser,
        'Le parsing doit consommer uniquement le fichier temporaire produit par le GET borné.',
    )

    contracts = active.find('Vérifier les contrats Emploi')
    download_pos = active.find("Télécharger l'historique Emploi en lecture seule")
    parser_pos = active.find("Vérifier l'historique Emploi sans secret")
    summary = active.find('Résumé lecture seule')
    require(
        min(contracts, download_pos, parser_pos, summary) >= 0 and contracts < download_pos < parser_pos < summary,
        'Ordre attendu: contrats locaux, GET distant, parsing sans secret, résumé lecture seule.',
    )

    print(
        'OK production Emploi V25: vérification manuelle, GET HTTPS Supabase exact, '
        'secret borné à une étape, parsing séparé sans secret et version distante figée.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
