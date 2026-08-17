#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / 'supabase' / 'migrations'
EXPECTED_FILE = MIGRATIONS / '20260817003529_fracture_seat_identity_isolation_v24_4_25.sql'
HARDENING_VERSION = '24.4.25'


def latest_function_block(files, name):
    rx = re.compile(
        rf'create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',
        re.I | re.S,
    )
    for path in reversed(files):
        matches = list(rx.finditer(path.read_text('utf-8', errors='ignore')))
        if matches:
            return path, matches[-1].group(0)
    return None, ''


def main() -> int:
    errors = []
    files = sorted(MIGRATIONS.glob('*.sql'))

    if not EXPECTED_FILE.exists():
        errors.append(f'Migration canonique absente: {EXPECTED_FILE.name}')

    sanitizer_file, sanitizer = latest_function_block(files, 'fracture_engine_sanitize_state')
    if not sanitizer_file:
        errors.append('fracture_engine_sanitize_state introuvable.')
    else:
        low = sanitizer.lower()
        seats_start = low.find("if jsonb_typeof(v_state->'seats') = 'array' then")
        reports_start = low.find("if jsonb_typeof(v_state->'reports') = 'array' then")
        if seats_start < 0 or reports_start < 0 or reports_start <= seats_start:
            errors.append(f'Bloc sièges impossible à isoler dans {sanitizer_file.name}.')
        else:
            seats = re.sub(r'\s+', '', low[seats_start:reports_start])
            if 'whenv_finishedthen' not in seats:
                errors.append('Le sanitizer ne distingue plus explicitement la révélation finale.')
            if "elseitem-array['identity','hand','cards','picks','private','secret','suspect']::text[]" not in seats:
                errors.append('Avant la fin, le sanitizer ne retire plus identity de chaque siège.')
            if 'v_my_seat' in seats:
                errors.append('Le bloc sièges réintroduit une exception par siège; aucune identité de siège ne doit sortir avant la fin.')

        compact = re.sub(r'\s+', '', low)
        if "v_finishedboolean:=coalesce(p_state->>'phase','')='finished'" not in compact:
            errors.append('La condition de fin officielle n’est plus utilisée pour la révélation des identités.')
        if "v_state:=v_state-array['identities','all_identities','secret_identities','identity_map']::text[]" not in compact:
            errors.append('Les collections globales d’identités ne sont plus supprimées avant la fin.')

    health_file, health = latest_function_block(files, 'fracture_engine_privacy_health')
    if not health_file:
        errors.append('fracture_engine_privacy_health introuvable.')
    else:
        compact_health = re.sub(r'\s+', '', health.lower())
        if f"'hardening_version','{HARDENING_VERSION}'" not in compact_health:
            errors.append(f'Le health check confidentialité n’annonce pas le durcissement {HARDENING_VERSION}.')
        if "'seat_identity_isolation',true" not in compact_health:
            errors.append('Le health check ne confirme plus seat_identity_isolation=true.')
        if "'privacy_version','24.4.15'" not in compact_health:
            errors.append('Le contrat de base privacy_version 24.4.15 a été modifié de façon incompatible.')

    migration = EXPECTED_FILE.read_text('utf-8', errors='ignore') if EXPECTED_FILE.exists() else ''
    for marker in [
        "'hardening_version','24.4.25'",
        "'seat_identity_isolation',true",
        "grant execute on function public.fracture_engine_sanitize_state(jsonb) to authenticated;",
        "revoke all on function public.fracture_engine_sanitize_state(jsonb) from public, anon;",
    ]:
        if marker not in migration.lower():
            errors.append(f'Migration V24.4.25 incomplète: {marker}')

    if errors:
        print(f'ECHEC isolation identités Fracture: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK isolation identités Fracture V24.4.25: aucune identité dans seats avant la fin, my_identity reste le canal privé, révélation complète seulement après finished.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
