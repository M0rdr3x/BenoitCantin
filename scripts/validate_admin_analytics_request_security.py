#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-analytics/index.ts'
LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;')
ROW_LIMIT_RE = re.compile(r'\.limit\(\s*10000\s*\)')
GAME_SLUG_MARKER = "const GAME_SLUG_RE = /^[a-z0-9][a-z0-9_-]{0,79}$/;"

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'admin/JWT/AAL2 explicite': 'requiredAdmin(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'contrôle Content-Length': "req.headers.get('content-length')",
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'slug jeu validé': GAME_SLUG_MARKER,
    'slug défaut conservé': "DEFAULT_GAME_SLUG = 'fracture-du-reseau-mere'",
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma': 'no-cache'",
    'nosniff': "'X-Content-Type-Options': 'nosniff'",
    'no-referrer': "'Referrer-Policy': 'no-referrer'",
    'données minimisées': ".select('metrics,feedback')",
    'MFA explicite': "error?.message === 'MFA_REQUIRED'",
    'état MFA fermé': "error?.message === 'MFA_STATE_UNAVAILABLE'",
    'requête trop grande': "error?.message === 'REQUEST_TOO_LARGE'",
    'slug invalide': "error?.message === 'INVALID_GAME_SLUG'",
    'agrégat contributions': 'total_contributions: rows.length',
    'agrégat joueurs': 'average_player_count:',
    'agrégat durée': 'average_duration_minutes:',
    'agrégat note': 'average_rating:',
    'top cartes': 'top_cards: topCards',
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'helper JSON générique cacheable': 'return json(',
    'import helper JSON générique': 'corsHeaders, json',
    'auth utilisateur simple': 'requiredUser(req)',
    'service client recréé': 'serviceClient()',
    'contrôle admin manuel': "from('internal_admin_users')",
    'created_at lu sans usage analytique': ".select('metrics,feedback,created_at')",
    'lignes brutes renvoyées': 'analytics: { rows',
}


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-analytics illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde admin-analytics absent: {label}.')

    if not LIMIT_RE.search(source):
        errors.append('Garde admin-analytics absent ou affaibli: requête exactement bornée à 4096 octets.')
    if not ROW_LIMIT_RE.search(source):
        errors.append('La lecture analytique doit rester bornée à 10000 contributions maximum.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde admin-analytics violé: {label}.')

    auth_pos = source.find('const { service } = await requiredAdmin(req);')
    body_pos = source.find('const body = await readLimitedJson(req);')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre admin/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le corps ne doit pas être lu avant la validation admin/JWT/AAL2.')

    if source.count('return new Response(') != 2:
        errors.append('Une réponse métier contourne privateJson; seuls privateJson et OPTIONS peuvent utiliser directement new Response.')

    analytics_return = 'return privateJson({\n      ok: true,\n      analytics: {'
    if analytics_return not in source:
        errors.append('La réponse analytique doit rester explicitement privée/no-store.')

    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'json direct': real.replace('const body = await readLimitedJson(req);', 'const body = await req.json();', 1),
        'no-store retiré': real.replace("'Cache-Control': 'private, no-store, max-age=0',", '', 1),
        'limite requête augmentée': real.replace('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 65536;', 1),
        'admin explicite retiré': real.replace(
            'const { service } = await requiredAdmin(req);',
            'const user = await requiredUser(req);\n    const service = serviceClient();',
            1,
        ),
        'ordre inversé': real.replace(
            'const { service } = await requiredAdmin(req);\n    const body = await readLimitedJson(req);',
            'const body = await readLimitedJson(req);\n    const { service } = await requiredAdmin(req);',
            1,
        ),
        'POST retiré': real.replace("if (req.method !== 'POST')", 'if (false)', 1),
        'slug non borné': real.replace(GAME_SLUG_MARKER, 'const GAME_SLUG_RE = /^.*$/;', 1),
        'donnée inutile réintroduite': real.replace(".select('metrics,feedback')", ".select('metrics,feedback,created_at')", 1),
        'limite lignes augmentée': real.replace('.limit(10000)', '.limit(100000)', 1),
        'réponse analytique cacheable': real.replace('return privateJson({\n      ok: true,\n      analytics: {', 'return new Response(JSON.stringify({\n      ok: true,\n      analytics: {', 1),
        'MFA retiré': real.replace("error?.message === 'MFA_REQUIRED'", "error?.message === 'MFA_BYPASSED'", 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test admin-analytics: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la confidentialité et les bornes HTTP de admin-analytics.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC sécurité admin-analytics: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK admin-analytics: admin/JWT/AAL2 avant corps, JSON 4 KiB, slug borné, réponses no-store et données analytiques minimisées.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
