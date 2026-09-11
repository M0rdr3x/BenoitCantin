#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-reports/index.ts'

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'admin explicite': 'requiredAdmin(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma': 'no-cache'",
    'nosniff': "'X-Content-Type-Options': 'nosniff'",
    'no-referrer': "'Referrer-Policy': 'no-referrer'",
    'courriel admin existant préservé': 'email: emails.get(r.owner_user_id)',
    'limite historique rapports préservée': '.limit(2000)',
    'erreur MFA fermée': "error?.message === 'MFA_STATE_UNAVAILABLE'",
    'réponse privée rapports': 'return privateJson({\n        ok:true,\n        reports,',
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'helper JSON générique cacheable': 'return json(',
    'import helper JSON générique': "import { corsHeaders, json }",
    'auth admin indirecte par requiredUser': 'requiredUser(req)',
}

LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;')


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-reports illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde admin-reports absent: {label}.')
    if not LIMIT_RE.search(source):
        errors.append('Garde admin-reports absent ou affaibli: requête exactement bornée à 4096 octets.')
    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde admin-reports violé: {label}.')

    auth_pos = source.find('const { service } = await requiredAdmin(req)')
    body_pos = source.find('const body = await readLimitedJson(req)')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre admin/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le corps ne doit pas être lu avant la validation admin/JWT/AAL2.')

    if source.count('privateJson(') < 10:
        errors.append('Les réponses administratives doivent rester uniformément privées et non cachables.')
    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'json direct': real.replace('const body = await readLimitedJson(req);', 'const body = await req.json();', 1),
        'no-store retiré': real.replace("'Cache-Control': 'private, no-store, max-age=0',", '', 1),
        'limite affaiblie': real.replace('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 40960;', 1),
        'admin explicite retiré': real.replace('const { service } = await requiredAdmin(req);', 'const user = await requiredUser(req); const service = serviceClient();', 1),
        'ordre inversé': real.replace(
            'const { service } = await requiredAdmin(req);\n    const body = await readLimitedJson(req);',
            'const body = await readLimitedJson(req);\n    const { service } = await requiredAdmin(req);',
            1,
        ),
        'réponse cacheable': real.replace('return privateJson({\n        ok:true,\n        reports,', 'return json({\n        ok:true,\n        reports,', 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test admin-reports: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la confidentialité et les bornes HTTP de admin-reports.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC admin-reports: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK admin-reports: admin/JWT/AAL2 avant corps, JSON 4 KiB et réponses privées no-store.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
