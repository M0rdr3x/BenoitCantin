#!/usr/bin/env python3
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
FN = ROOT / 'supabase/functions/delete-player-account/index.ts'
DOC = ROOT / 'DELETE_ACCOUNT_HTTP_HARDENING_V24_5_51.md'
CONFIG = ROOT / 'supabase/config.toml'
MIGRATIONS = ROOT / 'supabase/migrations'


def main() -> int:
    errors = []
    for path in (FN, DOC, CONFIG):
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors:
            print('- ' + error)
        return 1

    source = FN.read_text('utf-8', errors='ignore')
    doc = DOC.read_text('utf-8', errors='ignore').lower()
    config = tomllib.loads(CONFIG.read_text('utf-8'))

    markers = (
        "req.method !== 'POST'",
        'MAX_REQUEST_BYTES=1024',
        'readBoundedJson',
        'TextEncoder',
        'JSON_REQUIRED',
        'REQUEST_TOO_LARGE',
        'INVALID_JSON',
        "CONFIRM_PHRASE='SUPPRIMER MON COMPTE'",
        'privacy_service_can_delete_user',
        'OWNER_OR_ADMIN_DELETE_BLOCKED',
        'MFA_REQUIRED',
        'Cache-Control',
        'private, no-store',
        'Pragma',
        'no-cache',
        'X-Content-Type-Options',
        'nosniff',
        'Referrer-Policy',
        'no-referrer',
        'SAFE_FAILURE_CODES',
        "SAFE_FAILURE_CODES.has(error.message)?error.message:'DELETE_FAILED'",
    )
    for marker in markers:
        if marker not in source:
            errors.append(f'Garde-fou V24.5.51 absent: {marker}')

    if 'await req.json()' in source:
        errors.append('Lecture JSON directe non bornée interdite.')

    console_lines = [line.strip() for line in source.splitlines() if 'console.' in line]
    expected_console_lines = [
        "console.error('[delete-player-account]',{code:'AUTH_DELETE_FAILED'});",
        "console.error('[delete-player-account]',{code:failureCode(error)});",
    ]
    if console_lines != expected_console_lines:
        errors.append('Les logs de suppression doivent rester limités aux codes bornés approuvés, sans objet d’erreur brut.')

    raw_log_markers = (
        "console.error('[delete-player-account]',error)",
        'console.error(`[SINJIRA delete] storage ${bucket}`,error)',
        "console.error('[SINJIRA delete] auth delete',error)",
    )
    for marker in raw_log_markers:
        if marker in source:
            errors.append(f'Log d’erreur brut interdit dans delete-player-account: {marker}')

    function_cfg = config.get('functions', {}).get('delete-player-account', {})
    if function_cfg.get('verify_jwt') is not True:
        errors.append('delete-player-account doit conserver verify_jwt=true.')

    if any('24_5_51' in p.name.lower() for p in MIGRATIONS.glob('*.sql')):
        errors.append('V24.5.51 est Edge-only et ne doit pas ajouter de migration Supabase.')

    for marker in (
        'version **4**',
        'verify_jwt=true',
        'aucune migration supabase',
        '174 migrations',
        '1 024 octets',
        'private, no-store',
        'conservation légale',
        'aal2',
        'aucun paiement',
    ):
        if marker not in doc:
            errors.append(f'Document V24.5.51 incomplet: {marker}')

    forbidden = ('stripe', 'paypal', 'twilio', 'api.resend.com', 'shippo', 'easypost')
    for token in forbidden:
        if token in source.lower():
            errors.append(f'Intégration externe interdite dans V24.5.51: {token}')

    if errors:
        print(f'ECHEC V24.5.51 suppression de compte: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK V24.5.51: suppression de compte JWT, POST JSON borné à 1 KiB, réponses privées no-store, conservation légale/MFA/confirmation conservées, logs bornés, aucune migration ni service payant.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
