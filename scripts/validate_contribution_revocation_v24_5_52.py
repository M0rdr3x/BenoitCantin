#!/usr/bin/env python3
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
FN = ROOT / 'supabase/functions/revoke-my-contributions/index.ts'
DOC = ROOT / 'CONTRIBUTION_REVOCATION_HARDENING_V24_5_52.md'
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
        'MAX_REQUEST_BYTES=2048',
        'readBoundedJson',
        'TextEncoder',
        'JSON_REQUIRED',
        'REQUEST_TOO_LARGE',
        'INVALID_JSON',
        'UUID_RE',
        'body.all===true',
        'AMBIGUOUS_SCOPE',
        'SESSION_REQUIRED',
        'revokeAll ? null : sessionId',
        'p_user_id: user.id',
        'Cache-Control',
        'private, no-store',
        'X-Content-Type-Options',
        'nosniff',
        'Referrer-Policy',
        'no-referrer',
    )
    for marker in markers:
        if marker not in source:
            errors.append(f'Garde-fou V24.5.52 absent: {marker}')

    if 'await req.json()' in source:
        errors.append('Lecture JSON directe non bornée interdite.')
    if "body?.all ? null : (body?.session_id || null)" in source:
        errors.append('La portée globale implicite historique est interdite.')

    function_cfg = config.get('functions', {}).get('revoke-my-contributions', {})
    if function_cfg.get('verify_jwt') is not True:
        errors.append('revoke-my-contributions doit conserver verify_jwt=true.')

    if any('24_5_52' in p.name.lower() for p in MIGRATIONS.glob('*.sql')):
        errors.append('V24.5.52 est Edge-only et ne doit pas ajouter de migration Supabase.')

    for marker in (
        'version **2**',
        'verify_jwt=true',
        'aucune migration supabase',
        '174 migrations',
        'all: true',
        'un corps vide ne peut plus',
        '2 048 octets',
        'private, no-store',
        'service_role',
        'aucun paiement',
    ):
        if marker not in doc:
            errors.append(f'Document V24.5.52 incomplet: {marker}')

    if errors:
        print(f'ECHEC V24.5.52 révocation contributions: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK V24.5.52: révocation JWT, portée globale explicite, session UUID obligatoire sinon, POST JSON 2 KiB, réponses privées no-store, aucune migration ni service payant.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
