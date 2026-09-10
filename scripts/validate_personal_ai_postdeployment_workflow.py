#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-personal-ai-production-readiness.yml'
PRODUCTION_URL = 'https://api.supabase.com/v1/projects/gpvivleexywljowcqkru/database/migrations'
TOKEN_REF = 'SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ECHEC workflow postproduction Mon IA: {message}')


def step_blocks(text: str) -> dict[str, str]:
    matches = list(re.finditer(r'(?m)^      - name: (.+)$', text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks[match.group(1).strip()] = text[match.start():end]
    return blocks


def main() -> int:
    require(WORKFLOW.is_file(), 'workflow absent')
    text = WORKFLOW.read_text('utf-8')
    active = '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))

    trigger_block = text.split('on:\n', 1)[1].split('\npermissions:', 1)[0]
    trigger_keys = {
        match.group(1)
        for line in trigger_block.splitlines()
        if (match := re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line))
    }
    require(trigger_keys == {'workflow_dispatch'}, 'le contrôle doit rester manuel uniquement')

    for marker in (
        'VERIFY-SINJIRA-V25-PERSONAL-AI',
        'environment: production',
        'test "$GITHUB_REF" = "refs/heads/main"',
        'permissions:\n  contents: read',
        '20260905133130', 'sinjira_v25_employment_foundation',
        '20260905145448', 'sinjira_v25_personal_ai_foundation',
        '20260905145502', 'sinjira_v25_personal_ai_rls_hardening',
        '20260905150553', 'sinjira_v25_personal_ai_audit_user_index',
        'python3 scripts/validate_personal_ai_production_readiness.py',
        'Exécuter les 36 assertions Mon IA',
        "curl --proto '=https' --fail-with-body --silent --show-error --request GET",
        f'--url "{PRODUCTION_URL}"',
        'Authorization: Bearer $SUPABASE_ACCESS_TOKEN',
        'Vérifier l\'historique distant sans secret',
    ):
        require(marker in text, f'marqueur obligatoire absent: {marker}')

    for forbidden in (
        'SUPABASE_PROJECT_REF:',
        'SUPABASE_MANAGEMENT_API:',
        '--request POST', '--request PUT', '--request PATCH', '--request DELETE',
        'curl -X POST', 'curl -X PUT', 'curl -X PATCH', 'curl -X DELETE',
        '--location', '--proxy', '--connect-to', '--resolve', '--upload-file', '--data ', '--data=', '--data-binary', '--form ',
        'supabase db push',
        'supabase functions deploy',
        'supabase secrets set',
        'supabase migration repair',
        '--include-all',
        '--linked',
        '--no-verify-jwt',
        'continue-on-error: true',
        'set -x',
        'gh api',
        'git push',
    ):
        require(forbidden not in active, f'primitive d écriture/contournement interdite: {forbidden}')

    require(active.count(PRODUCTION_URL) == 1, 'une seule URL production Supabase littérale est attendue')
    require(len(re.findall(r'(?m)^\s*curl\b', active)) == 1, 'un seul appel curl distant est autorisé')

    secret_lines = [line for line in text.splitlines() if '${{ secrets.' in line]
    require(secret_lines == [f'          {TOKEN_REF}'], 'le token Supabase doit être l unique secret et rester borné à une seule étape')

    blocks = step_blocks(text)
    download = blocks.get("Télécharger l'historique distant en lecture seule", '')
    require(download, 'étape de téléchargement bornée absente')
    require(TOKEN_REF in download, 'le token doit être injecté uniquement dans l étape GET')
    require(PRODUCTION_URL in download, 'le GET doit cibler l URL Supabase exacte')
    require("--proto '=https'" in download and '--request GET' in download, 'le GET doit imposer HTTPS et la méthode GET')

    parser = blocks.get("Vérifier l'historique distant sans secret", '')
    require(parser, 'étape de parsing sans secret absente')
    require('SUPABASE_ACCESS_TOKEN' not in parser and '${{ secrets.' not in parser, 'le parsing ne doit recevoir aucun secret')
    require('MIGRATION_HISTORY="$RUNNER_TEMP/personal-ai-production-migrations.json"' in parser, 'le parsing doit consommer le fichier temporaire borné')
    require("positions != list(range(positions[0],positions[0]+len(positions)))" in parser, 'contrôle de continuité des migrations absent')

    print('OK workflow postproduction Mon IA: manuel, main-only, GET HTTPS Supabase exact, secret borné à une étape, parsing sans secret et 36 pgTAP.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
