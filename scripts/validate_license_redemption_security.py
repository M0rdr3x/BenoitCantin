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
    'diagnostic admin AAL2': "if(body?.action==='health')await requiredAdmin(req);",
    'refus admin explicite': "code:'ADMIN_ACCESS_REQUIRED'",
    'MFA indisponible sans erreur privée': "code:'MFA_STATE_UNAVAILABLE'", 
    'lecture JSON bornée': 'readLimitedJson(req)',
    'lecture bornée en flux': 'readLimitedUtf8Body(req,MAX_REQUEST_BYTES)',
    'lecteur partagé': 'limited-body.mjs',
    'journaux d’erreurs expurgés': "code:'LICENSE_REDEEM_FAILED'",
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
    'lecture HTTP entière non bornée': 'await req.text()',
    "journalisation d'erreur brute": "console.error('[redeem-license-code]',error)",
    "journalisation d'exception brute": "console.error('[redeem-license-code]',e)",
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
        health_pos = source.find("if(body?.action==='health')await requiredAdmin(req);")
        health_result = source.find("if(body?.action==='health'){", health_pos)
        schema_pos = source.find('const health=await licenseHealth(s)')
        if auth_pos < 0 or health_pos < auth_pos or health_result < health_pos:
            errors.append("Le diagnostic health doit exiger un JWT et le rôle admin AAL2 AVANT la réponse.")
        if schema_pos >= 0 and health_pos >= schema_pos:
            errors.append("Le diagnostic health doit contrôler l'admin avant la lecture du schéma.")
    else:
        errors.append("Le diagnostic de licence health doit être administrateur et AAL2.")

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        path = Path(raw) / 'index.ts'
        safe = """
import { readLimitedUtf8Body } from '../_shared/limited-body.mjs';
const MAX_REQUEST_BYTES=4096;
const MIN_CODE_LENGTH=12;
const MAX_CODE_LENGTH=80;
const PRIVATE_HEADERS={'Cache-Control':'private, no-store, max-age=0','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'};
async function readLimitedJson(req){const limited=await readLimitedUtf8Body(req,MAX_REQUEST_BYTES);const body=JSON.parse(limited.raw||'{}');return {body}}
Deno.serve(async req=>{
 if(req.method!=='POST')return null;
 const user=await requiredUser(req);
 const parsed=await readLimitedJson(req);
 const body=parsed.body||{};
 if(body?.action==='health')await requiredAdmin(req);
 const pepper=Deno.env.get('SINJIRA_LICENSE_PEPPER');
 const s=serviceClient();
 const health=await licenseHealth(s);
 if(body?.action==='health'){return null;}
 return s.rpc('redeem_sinjira_activation',{p_code_hash:'x',p_user_id:user.id});
});
console.error('[redeem-license-code]',{code:'LICENSE_REDEEM_FAILED'});
const errorCode={code:'ADMIN_ACCESS_REQUIRED',mfa:'MFA_STATE_UNAVAILABLE'};
"""
        path.write_text(safe, encoding='utf-8')
        clean = validate(path)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        path.write_text(safe.replace("if(body?.action==='health')await requiredAdmin(req);", "if(body?.action==='health')await requiredUser(req);"), encoding='utf-8')
        without_admin = validate(path)
        if not any('admin AAL2' in item or 'rôle admin' in item for item in without_admin):
            raise AssertionError('La substitution du rôle admin par un simple JWT doit être rejetée.')

        path.write_text(safe.replace('readLimitedUtf8Body(req,MAX_REQUEST_BYTES)', 'req.text()'), encoding='utf-8')
        raw_body = validate(path)
        if not any('lecture HTTP entière' in item or 'lecture bornée en flux' in item for item in raw_body):
            raise AssertionError('Un corps lu en entier doit être rejeté.')

        path.write_text(safe.replace("console.error('[redeem-license-code]',{code:'LICENSE_REDEEM_FAILED'});",
                                     "console.error('[redeem-license-code]',error);"), encoding='utf-8')
        raw_log = validate(path)
        if not any('journalisation' in item or 'journaux d’erreurs' in item for item in raw_log):
            raise AssertionError('Un log brut de fournisseur doit être rejeté.')

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
