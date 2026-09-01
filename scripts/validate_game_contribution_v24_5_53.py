#!/usr/bin/env python3
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
FN = ROOT / 'supabase/functions/submit-game-contribution/index.ts'
DOC = ROOT / 'GAME_CONTRIBUTION_HARDENING_V24_5_53.md'
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
        "req.method!=='POST'",
        'MAX_REQUEST_BYTES=2048',
        'readBoundedJson',
        'TextEncoder',
        'JSON_REQUIRED',
        'REQUEST_TOO_LARGE',
        'INVALID_JSON',
        'UUID_RE',
        'INVALID_SESSION',
        'p_user_id:user.id',
        "select('id,game_slug,play_mode,human_player_count,effective_player_count,player_count,duration_minutes')",
        'submitted:true',
        'Cache-Control',
        'private, no-store',
        'X-Content-Type-Options',
        'nosniff',
        'Referrer-Policy',
        'no-referrer',
    )
    for marker in markers:
        if marker not in source:
            errors.append(f'Garde-fou V24.5.53 absent: {marker}')

    if 'await req.json()' in source:
        errors.append('Lecture JSON directe non bornée interdite.')
    if 'contribution_id' in source:
        errors.append('UUID interne contribution_id interdit dans la réponse/client.')
    if ".select('*')" in source:
        errors.append("select('*') interdit dans submit-game-contribution.")

    function_cfg = config.get('functions', {}).get('submit-game-contribution', {})
    if function_cfg.get('verify_jwt') is not True:
        errors.append('submit-game-contribution doit conserver verify_jwt=true.')

    if any('24_5_53' in p.name.lower() for p in MIGRATIONS.glob('*.sql')):
        errors.append('V24.5.53 est Edge-only et ne doit pas ajouter de migration Supabase.')

    for marker in (
        'version **4**',
        'verify_jwt=true',
        'aucune migration supabase',
        '174 migrations',
        'uuid n’est plus retourné',
        '2 048 octets',
        'select(\'*\')',
        'private, no-store',
        'aucun paiement',
    ):
        if marker not in doc:
            errors.append(f'Document V24.5.53 incomplet: {marker}')

    if errors:
        print(f'ECHEC V24.5.53 contribution jeu: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK V24.5.53: contribution JWT, JSON 2 KiB, session UUID/ownership, SQL minimisé, UUID interne non exposé, réponses no-store, aucune migration ni service payant.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
