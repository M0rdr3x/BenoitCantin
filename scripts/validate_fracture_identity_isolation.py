#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / 'supabase' / 'migrations'
IDENTITY_MIGRATION = MIGRATIONS / '20260817003529_fracture_seat_identity_isolation_v24_4_25.sql'
DIRECT_RETURN_MIGRATION = MIGRATIONS / '20260817004027_fracture_direct_rpc_safe_return_v24_4_26.sql'
HARDENING_VERSION = '24.4.26'


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

    for expected in (IDENTITY_MIGRATION, DIRECT_RETURN_MIGRATION):
        if not expected.exists():
            errors.append(f'Migration canonique absente: {expected.name}')

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

    get_state_file, get_state = latest_function_block(files, 'fracture_engine_get_state')
    if not get_state_file:
        errors.append('fracture_engine_get_state introuvable.')
    else:
        compact_get_state = re.sub(r'\s+', '', get_state.lower())
        if 'returnpublic.fracture_engine_sanitize_state(base);' not in compact_get_state:
            errors.append('fracture_engine_get_state ne passe plus son résultat final par le sanitizer canonique.')
        if 'public._fracture_engine_get_state_raw(p_party_code)' not in get_state:
            errors.append('fracture_engine_get_state n’utilise plus le helper brut interne attendu.')
        if "elser-'suspect'end" not in compact_get_state:
            errors.append('fracture_engine_get_state ne masque plus les soupçons des autres joueurs avant sanitization.')

    # Les RPC d’action peuvent rester appelables par authenticated uniquement si
    # leur résultat repasse systématiquement par fracture_engine_get_state(),
    # désormais lui-même assaini. Le gateway reste l’interface canonique du site.
    for name in (
        'fracture_engine_start',
        'fracture_engine_submit_keep',
        'fracture_engine_pick',
        'fracture_engine_submit_report',
        'fracture_engine_submit_accusation',
    ):
        action_file, action = latest_function_block(files, name)
        if not action_file:
            errors.append(f'{name} introuvable.')
            continue
        compact_action = re.sub(r'\s+', '', action.lower())
        if 'returnpublic.fracture_engine_get_state(p_party_code);' not in compact_action:
            errors.append(f'{name} ne retourne plus le contrat d’état assaini commun.')
        if 'auth.uid()' not in action.lower():
            errors.append(f'{name} ne vérifie plus l’identité JWT via auth.uid().')

    health_file, health = latest_function_block(files, 'fracture_engine_privacy_health')
    if not health_file:
        errors.append('fracture_engine_privacy_health introuvable.')
    else:
        compact_health = re.sub(r'\s+', '', health.lower())
        if f"'hardening_version','{HARDENING_VERSION}'" not in compact_health:
            errors.append(f'Le health check confidentialité n’annonce pas le durcissement {HARDENING_VERSION}.')
        for marker in (
            "'seat_identity_isolation',true",
            "'direct_action_safe_return',true",
            "'privacy_version','24.4.15'",
        ):
            if marker not in compact_health:
                errors.append(f'Le health check confidentialité a perdu le marqueur: {marker}')

    identity_sql = IDENTITY_MIGRATION.read_text('utf-8', errors='ignore').lower() if IDENTITY_MIGRATION.exists() else ''
    for marker in (
        "'hardening_version','24.4.25'",
        "'seat_identity_isolation',true",
        "grant execute on function public.fracture_engine_sanitize_state(jsonb) to authenticated;",
        "revoke all on function public.fracture_engine_sanitize_state(jsonb) from public, anon;",
    ):
        if marker not in identity_sql:
            errors.append(f'Migration V24.4.25 incomplète: {marker}')

    direct_sql = DIRECT_RETURN_MIGRATION.read_text('utf-8', errors='ignore').lower() if DIRECT_RETURN_MIGRATION.exists() else ''
    for marker in (
        "return public.fracture_engine_sanitize_state(base);",
        "'hardening_version','24.4.26'",
        "'direct_action_safe_return',true",
    ):
        if marker not in direct_sql:
            errors.append(f'Migration V24.4.26 incomplète: {marker}')

    if errors:
        print(f'ECHEC confidentialité Fracture: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK confidentialité Fracture V24.4.26: aucune identité dans seats avant la fin et tous les retours directs des RPC d’action repassent par le sanitizer canonique.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
