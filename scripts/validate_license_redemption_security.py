#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/redeem-license-code/index.ts'

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'authentification obligatoire': 'requiredUser(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'mesure UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'secret serveur du code': "Deno.env.get('SINJIRA_LICENSE_PEPPER')",
    'client serveur': 'serviceClient()',
    'RPC canonique': "s.rpc('redeem_sinjira_activation'",
    'identité imposée par le serveur': 'p_user_id:user.id',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options':'nosniff'",
    'référent masqué': "'Referrer-Policy':'no-referrer'",
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 4096 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;'),
    'longueur minimale du code exactement à 12': re.compile(r'\bMIN_CODE_LENGTH\s*=\s*12\s*;'),
    'longueur maximale du code exactement à 80': re.compile(r'\bMAX_CODE_LENGTH\s*=\s*80\s*;'),
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'lecture JSON directe non bornée espacée': 'await req.json (',
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'Fonction redeem-license-code illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde licence absent: {label}.')
    for label, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(source):
            errors.append(f'Garde licence absent ou affaibli: {label}.')
    for label, marker in FORBIDDEN.items():
        if marker in source:
            errors.append(f'Garde licence violé: {label}.')

    if "body?.action==='health'" in source:
        auth_pos = source.find('requiredUser(req)')
        health_pos = source.find("body?.action==='health'")
        if auth_pos < 0 or auth_pos > health_pos:
            errors.append("L'action health ne doit pas contourner l'authentification.")

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        path = Path(raw) / 'index.ts'
        safe = """
const MAX_REQUEST_BYTES=4096;
const MIN_CODE_LENGTH=12;
const MAX_CODE_LENGTH=80;
const PRIVATE_HEADERS={'Cache-Control':'private, no-store, max-age=0','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'};
async function readLimitedJson(req){const raw=await req.text();new TextEncoder().encode(raw).byteLength;return {body:{}}}
Deno.serve(async req=>{
 if(req.method!=='POST')return null;
 const user=await requiredUser(req);
 const parsed=await readLimitedJson(req);
 const pepper=Deno.env.get('SINJIRA_LICENSE_PEPPER');
 const s=serviceClient();
 if(parsed.body?.action==='health')return null;
 return s.rpc('redeem_sinjira_activation',{p_code_hash:'x',p_user_id:user.id});
});
"""
        path.write_text(safe, encoding='utf-8')
        clean = validate(path)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        path.write_text(safe.replace('const parsed=await readLimitedJson(req);', 'const parsed={body:await req.json()};'), encoding='utf-8')
        direct = validate(path)
        if not any('lecture JSON directe' in item for item in direct):
            raise AssertionError('La lecture JSON directe doit être bloquée.')

        path.write_text(safe.replace("'Cache-Control':'private, no-store, max-age=0',", ''), encoding='utf-8')
        cache = validate(path)
        if not any('réponse privée' in item for item in cache):
            raise AssertionError('La suppression de no-store doit être bloquée.')

        path.write_text(safe.replace('MAX_CODE_LENGTH=80;', 'MAX_CODE_LENGTH=8000;'), encoding='utf-8')
        length = validate(path)
        if not any('longueur maximale' in item for item in length):
            raise AssertionError('Une longueur maximale affaiblie doit être bloquée.')

        path.write_text(safe.replace('MAX_REQUEST_BYTES=4096;', 'MAX_REQUEST_BYTES=40960;'), encoding='utf-8')
        body_size = validate(path)
        if not any('4096 octets' in item for item in body_size):
            raise AssertionError('Une limite de corps affaiblie doit être bloquée.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la sécurité de redeem-license-code.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test activation licence.')
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC activation licence: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK activation licence: JWT, JSON 4 KiB, code 12–80, RPC service-only et réponses privées bornées.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
