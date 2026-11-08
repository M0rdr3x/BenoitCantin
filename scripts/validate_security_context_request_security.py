#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/security-context/index.ts'

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'authentification obligatoire': 'requiredUser(req)',
    'session issue du JWT validé': 'sessionIdFromVerifiedRequest(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'lecteur UTF-8 en flux': 'readLimitedUtf8Body(req, MAX_REQUEST_BYTES)',
    'résultat JSON strict': "JSON.parse(limited.raw || '{}')",
    'importation du lecteur partagé': "from '../_shared/limited-body.mjs'",
    'journal expurgé': "code: 'SECURITY_CONTEXT_FAILED'",
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options': 'nosniff'",
    'référent masqué': "'Referrer-Policy': 'no-referrer'",
    'géolocalisation explicite opt-in infrastructure': "Deno.env.get('SINJIRA_TRUST_GEO_HEADERS') !== 'true'",
    'pays approximatif seulement': "req.headers.get('cf-ipcountry')",
    'région approximative seulement': "req.headers.get('x-sinjira-region')",
    'RPC contexte session canonique': "service.rpc('service_security_evaluate_context_session'",
    'session imposée au RPC': 'p_session_id: sessionId',
    'réponse succès privée': 'return privateJson({\n      ok: true,',
    'contrat confidentialité IP': 'raw_ip_stored: false',
    'contrat confidentialité GPS': 'gps_used: false',
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 4096 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;'),
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'lecture HTTP brute non bornée': 'await req.text()',
    'journalisation brute de l’exception': "console.error('[security-context]', error)",
    'lecture JSON directe non bornée espacée': 'await req.json (',
    'lecture IP brute Cloudflare': 'cf-connecting-ip',
    'lecture IP brute proxy': 'x-forwarded-for',
    'lecture IP brute générique': 'x-real-ip',
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'Fonction security-context illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde security-context absent: {label}.')
    for label, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(source):
            errors.append(f'Garde security-context absent ou affaibli: {label}.')
    for label, marker in FORBIDDEN.items():
        if marker in source.lower():
            errors.append(f'Garde security-context violé: {label}.')

    parsed_pos = source.find('const parsed = await readLimitedJson(req)')
    auth_pos = source.find('const user = await requiredUser(req)')
    if parsed_pos >= 0 and auth_pos >= 0 and auth_pos > parsed_pos:
        errors.append('Le corps ne doit pas être lu avant la validation de l’utilisateur JWT.')

    if source.count('privateJson(') < 6:
        errors.append('Les réponses sensibles doivent rester uniformément privées et non cachables.')

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        path = Path(raw) / 'index.ts'
        safe = """
import { readLimitedUtf8Body } from '../_shared/limited-body.mjs';
const MAX_REQUEST_BYTES = 4096;
const PRIVATE_HEADERS = {
  'Cache-Control': 'private, no-store, max-age=0',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
};
function privateJson(data, status=200){return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS})}
async function readLimitedJson(req){
 const limited=await readLimitedUtf8Body(req, MAX_REQUEST_BYTES);
 if(!limited.ok) return {response:privateJson({},413)};
 const body=JSON.parse(limited.raw || '{}');
 return {body};
}
function sessionIdFromVerifiedRequest(req){return req}
function trustedGeo(req){
 if (Deno.env.get('SINJIRA_TRUST_GEO_HEADERS') !== 'true') return {country:null,region:null};
 const country=req.headers.get('cf-ipcountry');
 const region=req.headers.get('x-sinjira-region');
 return {country,region};
}
Deno.serve(async (req) => {
 if (req.method !== 'POST') return privateJson({},405);
 const user = await requiredUser(req);
 const sessionId = sessionIdFromVerifiedRequest(req);
 const parsed = await readLimitedJson(req);
 if (parsed.response) return parsed.response;
 if (!parsed.body) return privateJson({},400);
 const geo=trustedGeo(req);
 const service=serviceClient();
 const {data}=await service.rpc('service_security_evaluate_context_session',{p_session_id: sessionId});
 if(!data)return privateJson({},500);
 const privacy={raw_ip_stored: false,gps_used: false};
 return privateJson({
      ok: true,
      privacy,
      geo
 });
});
privateJson({});
privateJson({});
console.error('[security-context]', { code: 'SECURITY_CONTEXT_FAILED' });
"""
        path.write_text(safe, encoding='utf-8')
        clean = validate(path)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        path.write_text(safe.replace('readLimitedUtf8Body(req, MAX_REQUEST_BYTES)', 'req.text()'), encoding='utf-8')
        raw_read = validate(path)
        if not any('lecture HTTP brute' in item or 'lecteur UTF-8' in item for item in raw_read):
            raise AssertionError('La lecture complète non bornée doit être bloquée.')

        path.write_text(safe.replace("console.error('[security-context]', { code: 'SECURITY_CONTEXT_FAILED' });",
                                     "console.error('[security-context]', error);"), encoding='utf-8')
        raw_logs = validate(path)
        if not any('journalisation brute' in item or 'journal expurgé' in item for item in raw_logs):
            raise AssertionError('Un log d’exception brut doit être bloqué.')

        path.write_text(safe.replace('const parsed = await readLimitedJson(req);', 'const parsed = {body: await req.json()};'), encoding='utf-8')
        direct = validate(path)
        if not any('lecture JSON directe' in item for item in direct):
            raise AssertionError('La lecture JSON directe doit être bloquée.')

        path.write_text(safe.replace("'Cache-Control': 'private, no-store, max-age=0',", ''), encoding='utf-8')
        cache = validate(path)
        if not any('réponse privée' in item for item in cache):
            raise AssertionError('La suppression de no-store doit être bloquée.')

        path.write_text(safe.replace('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 40960;'), encoding='utf-8')
        body_size = validate(path)
        if not any('4096 octets' in item for item in body_size):
            raise AssertionError('Une limite de corps affaiblie doit être bloquée.')

        path.write_text(safe.replace("const country=req.headers.get('cf-ipcountry');", "const country=req.headers.get('cf-connecting-ip');"), encoding='utf-8')
        raw_ip = validate(path)
        if not any('IP brute' in item for item in raw_ip):
            raise AssertionError('La lecture d’une IP brute doit être bloquée.')

        path.write_text(safe.replace('const user = await requiredUser(req);\n const sessionId', 'const parsed = await readLimitedJson(req);\n const user = await requiredUser(req);\n const sessionId').replace(' const parsed = await readLimitedJson(req);\n if (parsed.response)', ' if (parsed.response)'), encoding='utf-8')
        auth_order = validate(path)
        if not any('avant la validation' in item for item in auth_order):
            raise AssertionError('La lecture du corps avant le JWT doit être bloquée.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide les bornes HTTP et la confidentialité de security-context.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test security-context.')
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC security-context: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK security-context: JWT avant corps, JSON 4 KiB, réponses no-store et aucune IP brute/GPS.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
