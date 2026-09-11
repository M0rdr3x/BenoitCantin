#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-console/index.ts'
LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*32_?768\s*;')

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'admin explicite': 'requiredAdmin(req)',
    'lecture JSON bornée': 'readBoundedJson(req)',
    'contrôle Content-Length': "req.headers.get('content-length')",
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'nosniff': "'X-Content-Type-Options':'nosniff'",
    'no-referrer': "'Referrer-Policy':'no-referrer'",
    'upload signé privé': 'createSignedUploadUrl(path)',
    'jeton upload conservé': 'upload:{path,token:upload.token,bucket}',
    'liste utilisateurs conservée': "action==='list_users'",
    'demandes accès conservées': "action==='list_access_requests'",
    'octroi accès conservé': "action==='grant_access'",
    'révocation accès conservée': "action==='revoke_access'",
    'description extension 10k conservée': "description:String(e.description||'').slice(0,10000)",
    'MFA explicite': "e?.message==='MFA_REQUIRED'",
    'état MFA fermé': "e?.message==='MFA_STATE_UNAVAILABLE'",
    'requête trop grande': "e?.message==='REQUEST_TOO_LARGE'",
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'helper JSON générique cacheable': 'return json(',
    'import helper JSON générique': "corsHeaders, json",
    'auth admin indirecte': 'requiredUser(req)',
    'service client recréé': 'serviceClient()',
}


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-console illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde admin-console absent: {label}.')
    if not LIMIT_RE.search(source):
        errors.append('Garde admin-console absent ou affaibli: requête exactement bornée à 32768 octets.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde admin-console violé: {label}.')

    auth_pos = source.find('const {user,service}=await requiredAdmin(req)')
    body_pos = source.find('const body=await readBoundedJson(req)')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre admin/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le corps ne doit pas être lu avant la validation admin/JWT/AAL2.')

    upload_response = 'return privateJson({ok:true,document:row,upload:{path,token:upload.token,bucket}});'
    if upload_response not in source:
        errors.append('Le jeton d’upload signé doit rester dans une réponse privée/no-store explicite.')

    if source.count('privateJson(') < 20:
        errors.append('Les réponses de la console admin doivent rester uniformément privées et non cachables.')

    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'json direct': real.replace('const body=await readBoundedJson(req)', 'const body=await req.json()', 1),
        'no-store retiré': real.replace("'Cache-Control':'private, no-store, max-age=0',", '', 1),
        'limite affaiblie': real.replace('MAX_REQUEST_BYTES=32768;', 'MAX_REQUEST_BYTES=327680;', 1),
        'admin explicite retiré': real.replace('const {user,service}=await requiredAdmin(req);', 'const user=await requiredUser(req),service=serviceClient();', 1),
        'ordre inversé': real.replace(
            'const {user,service}=await requiredAdmin(req);\n    const body=await readBoundedJson(req)',
            'const body=await readBoundedJson(req);\n    const {user,service}=await requiredAdmin(req)',
            1,
        ),
        'upload non privé': real.replace(
            'return privateJson({ok:true,document:row,upload:{path,token:upload.token,bucket}});',
            'return new Response(JSON.stringify({ok:true,document:row,upload:{path,token:upload.token,bucket}}));',
            1,
        ),
        'révocation accès retirée': real.replace("if(action==='revoke_access')", "if(action==='revoke_access_disabled')", 1),
        'borne description extension augmentée': real.replace("slice(0,10000)", "slice(0,100000)", 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test admin-console: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide les bornes HTTP et la confidentialité de admin-console.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC sécurité admin-console: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK admin-console: admin/JWT/AAL2 avant corps, JSON 32 KiB, réponses no-store et jeton upload signé privé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
