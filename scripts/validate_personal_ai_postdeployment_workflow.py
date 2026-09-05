#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-personal-ai-production-readiness.yml'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ECHEC workflow postproduction Mon IA: {message}')


def main() -> int:
    require(WORKFLOW.is_file(), 'workflow absent')
    text = WORKFLOW.read_text('utf-8')
    active = '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))

    trigger_block = text.split('on:\n', 1)[1].split('\npermissions:', 1)[0]
    trigger_keys = {
        match.group(1)
        for line in trigger_block.splitlines()[1:]
        if (match := re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line))
    }
    require(trigger_keys == {'workflow_dispatch'}, 'le contrôle doit rester manuel uniquement')

    for marker in (
        'VERIFY-SINJIRA-V25-PERSONAL-AI',
        'environment: production',
        'SUPABASE_PROJECT_REF: gpvivleexywljowcqkru',
        '20260905133130', 'sinjira_v25_employment_foundation',
        '20260905145448', 'sinjira_v25_personal_ai_foundation',
        '20260905145502', 'sinjira_v25_personal_ai_rls_hardening',
        '20260905150553', 'sinjira_v25_personal_ai_audit_user_index',
        'python3 scripts/validate_personal_ai_production_readiness.py',
        'Exécuter les 36 assertions Mon IA',
        '/database/migrations',
    ):
        require(marker in text, f'marqueur obligatoire absent: {marker}')

    for forbidden in (
        '--request POST',
        'supabase db push',
        'supabase functions deploy',
        'supabase migration repair',
        '--include-all',
        'continue-on-error: true',
        'set -x',
    ):
        require(forbidden not in active, f'primitive d écriture/contournement interdite: {forbidden}')

    require(active.count('/database/migrations') == 1, 'une seule lecture de l historique distant est attendue')
    require('Authorization: Bearer $SUPABASE_ACCESS_TOKEN' in text, 'authentification de la lecture distante absente')
    require("positions != list(range(positions[0],positions[0]+len(positions)))" in text, 'contrôle de continuité des migrations absent')

    print('OK workflow postproduction Mon IA: manuel, lecture seule, migrations réelles verrouillées et 36 pgTAP.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
