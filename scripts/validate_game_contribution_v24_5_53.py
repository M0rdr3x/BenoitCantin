#!/usr/bin/env python3
from pathlib import Path
import argparse
import tomllib

ROOT = Path(__file__).resolve().parents[1]
FN = ROOT / 'supabase/functions/submit-game-contribution/index.ts'
DOC = ROOT / 'GAME_CONTRIBUTION_HARDENING_V24_5_53.md'
CONFIG = ROOT / 'supabase/config.toml'
MIGRATIONS = ROOT / 'supabase/migrations'


def validate_request_privacy(source: str) -> list[str]:
    """Regression guard for the real authenticated HTTP request boundary."""
    required = {
        'délai 4 secondes': 'MAX_REQUEST_READ_TIMEOUT_MS=4_000;',
        'lecteur partagé à échéance absolue': "from '../_shared/read-chunk-deadline.mjs';",
        'appel du lecteur sécurisé': 'readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,MAX_REQUEST_READ_TIMEOUT_MS)',
        'délai de lecture signalé': "limited.reason==='REQUEST_TIMEOUT'",
        'HTTP 408 explicite': "code:'REQUEST_TIMEOUT'},408)",
        'rejet des octets excédentaires': "limited.reason==='REQUEST_TOO_LARGE'",
        'authentification': "const user=await requiredUser(req);",
        'corps JSON typé': "contentType!=='application/json'",
        'log fixe, sans exception': "console.error('[submit-game-contribution]',{code:'GAME_CONTRIBUTION_FAILED'});",
    }
    errors = [f'Contributions : garde absent : {label}'
              for label, marker in required.items() if marker not in source]
    forbidden = (
        'await req.text()', 'await req.json()',
        'await readLimitedUtf8Body(req,MAX_REQUEST_BYTES)',
        "console.error('[submit-game-contribution]',e)",
        'console.error(e)', 'console.warn(e)',
        "console.error('[submit-game-contribution]',error)",
    )
    for marker in forbidden:
        if marker in source:
            errors.append(f'Contributions : accès ou journal dangereux : {marker}')
    auth_at = source.find("const user=await requiredUser(req);")
    read_at = source.find("const body=await readBoundedJson(req);")
    if auth_at < 0 or read_at <= auth_at:
        errors.append("Contributions : authentification obligatoire avant lecture de l'entrée.")
    return errors


def self_test() -> None:
    clean = FN.read_text('utf-8', errors='strict')
    problems = validate_request_privacy(clean)
    if problems:
        raise AssertionError("Le code actuel doit passer : " + " | ".join(problems))
    mutations = {
        'délai retiré': clean.replace('MAX_REQUEST_READ_TIMEOUT_MS=4_000;', '', 1),
        'ancien lecteur sans échéance': clean.replace(
            'readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,MAX_REQUEST_READ_TIMEOUT_MS)',
            'readLimitedUtf8Body(req,MAX_REQUEST_BYTES)', 1),
        'délai masqué en 413': clean.replace(
            "code:'REQUEST_TIMEOUT'},408)", "code:'REQUEST_TIMEOUT'},413)", 1),
        'erreur brute journalisée': clean.replace(
            "console.error('[submit-game-contribution]',{code:'GAME_CONTRIBUTION_FAILED'});",
            "console.error('[submit-game-contribution]',e);", 1),
        'authentification après le corps': clean.replace(
            "const user=await requiredUser(req);\n    const body=await readBoundedJson(req);",
            "const body=await readBoundedJson(req);\n    const user=await requiredUser(req);", 1),
        'lecture non bornée': clean.replace(
            'readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,MAX_REQUEST_READ_TIMEOUT_MS)',
            'await req.json()', 1),
        'corps MIME non vérifié': clean.replace(
            "contentType!=='application/json'", "false", 1),
    }
    for label, broken in mutations.items():
        if broken == clean:
            raise AssertionError(f'Mutation incorrecte : {label}')
        if not validate_request_privacy(broken):
            raise AssertionError(f'Mutation non détectée : {label}')
    print(f'OK: {len(mutations)} régressions de sécurité rejetées sans accéder aux comptes réels.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = []
    for path in (FN, DOC, CONFIG):
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors:
            print('- ' + error)
        return 1

    source = FN.read_text('utf-8', errors='ignore')
    errors.extend(validate_request_privacy(source))
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
