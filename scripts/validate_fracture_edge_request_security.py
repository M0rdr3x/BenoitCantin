#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / 'supabase/functions/fracture-engine-gateway/index.ts'
ENDGAME = ROOT / 'supabase/functions/submit-fracture-endgame/index.ts'


def compact(value: str) -> str:
    return re.sub(r'\s+', '', value)


def read(path: Path) -> str:
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def validate_sources(gateway: str, endgame: str) -> list[str]:
    errors: list[str] = []
    gateway_flat = compact(gateway)
    endgame_flat = compact(endgame)

    gateway_required = {
        'limite gateway 32 000 octets': 'constMAX_BODY_BYTES=32_000;',
        'MIME gateway normalisé': ".split(';',1)[0].trim().toLowerCase()",
        'MIME gateway JSON exact': "contentType!=='application/json'",
        'Content-Length gateway numérique strict': r'if(!/^\d+$/.test(normalizedLength))',
        'Content-Length gateway entier sûr': 'if(!Number.isSafeInteger(declaredLength))',
        'lecture gateway par flux': 'req.body?.getReader()',
        'annulation gateway au dépassement': 'reader.cancel()',
        'borne gateway pendant le flux': 'if(total>MAX_BODY_BYTES)',
        'UTF-8 gateway strict': "newTextDecoder('utf-8',{fatal:true})",
        'JWT gateway vérifié': 'client.auth.getUser(token)',
        'actions gateway allowlistées': 'ALLOWED_ACTIONS',
        'état gateway assaini': "client.rpc('fracture_engine_get_state_safe'",
        'réponse gateway privée': "'Cache-Control':'private,no-store,max-age=0'",
    }
    endgame_required = {
        'limite endgame 4 096 octets': 'constMAX_REQUEST_BYTES=4096;',
        'MIME endgame normalisé': ".split(';',1)[0].trim().toLowerCase()",
        'MIME endgame JSON exact': "contentType!=='application/json'",
        'Content-Length endgame numérique strict': r'if(!/^\d+$/.test(normalizedLength))',
        'Content-Length endgame entier sûr': 'if(!Number.isSafeInteger(declaredLength))',
        'lecture endgame par flux': 'req.body?.getReader()',
        'annulation endgame au dépassement': 'reader.cancel()',
        'borne endgame pendant le flux': 'if(total>MAX_REQUEST_BYTES)',
        'UTF-8 endgame strict': "newTextDecoder('utf-8',{fatal:true})",
        'utilisateur endgame obligatoire': 'constuser=awaitrequiredUser(req);',
        'corps endgame à clé unique': 'Object.keys(body).length!==1',
        'party_code endgame typé': "typeofbody.party_code!=='string'",
        'propriétaire endgame requis': 'party.owner_user_id!==user.id',
        'RPC endgame serveur': "service.rpc('service_submit_fracture_endgame'",
        'services payants endgame désactivés': 'constPAID_EXTERNAL_SERVICES_ENABLED=false;',
        'réponse endgame privée': "'Cache-Control':'private,no-store,max-age=0'",
    }

    for label, marker in gateway_required.items():
        if marker not in gateway_flat:
            errors.append(f'Gateway Fracture: garde absent ou affaibli — {label}.')
    for label, marker in endgame_required.items():
        if marker not in endgame_flat:
            errors.append(f'Endgame Fracture: garde absent ou affaibli — {label}.')

    for label, source in (('Gateway Fracture', gateway_flat), ('Endgame Fracture', endgame_flat)):
        if 'awaitreq.text()' in source:
            errors.append(f'{label}: req.text() non borné interdit.')
        if 'awaitreq.json()' in source:
            errors.append(f'{label}: req.json() non borné interdit.')
        if "startswith('application/json')" in source.lower():
            errors.append(f'{label}: validation MIME par préfixe interdite.')

    gateway_auth = gateway_flat.find('client.auth.getUser(token)')
    gateway_read = gateway_flat.find('constparsed=awaitreadLimitedJson(req)')
    if gateway_auth < 0 or gateway_read < 0 or gateway_auth > gateway_read:
        errors.append('Gateway Fracture: le JWT doit être vérifié avant toute lecture du corps applicatif.')

    endgame_auth = endgame_flat.find('constuser=awaitrequiredUser(req);')
    endgame_read = endgame_flat.find('constparsedRequest=awaitreadLimitedJson(req);')
    if endgame_auth < 0 or endgame_read < 0 or endgame_auth > endgame_read:
        errors.append('Endgame Fracture: requiredUser(req) doit précéder toute lecture du corps applicatif.')

    return errors


def self_test() -> None:
    gateway = """
const GATEWAY_VERSION='24.4.15';
const MAX_BODY_BYTES=32_000;
const PRIVATE_HEADERS={'Cache-Control':'private, no-store, max-age=0'};
const ALLOWED_ACTIONS=new Set(['fracture_engine_start']);
async function readLimitedJson(req){
 const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
 if(contentType!=='application/json') return {};
 const rawLength=req.headers.get('content-length');
 if(rawLength!==null){
  const normalizedLength=rawLength.trim();
  if(!/^\d+$/.test(normalizedLength)) return {};
  const declaredLength=Number(normalizedLength);
  if(!Number.isSafeInteger(declaredLength)) return {};
  if(declaredLength>MAX_BODY_BYTES) return {};
 }
 const reader=req.body?.getReader(); let total=0;
 while(true){const {done,value}=await reader.read();if(done)break;if(!value)continue;total+=value.byteLength;if(total>MAX_BODY_BYTES){await reader.cancel();return {}}}
 const bytes=new Uint8Array(total); const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 return {body:JSON.parse(raw||'{}')};
}
async function handler(req){
 const token='x'; const client={auth:{getUser:async()=>({})},rpc:async()=>({})};
 await client.auth.getUser(token);
 const parsed=await readLimitedJson(req);
 await client.rpc('fracture_engine_get_state_safe',{});
 return parsed;
}
"""
    endgame = """
const MAX_REQUEST_BYTES=4096;
const PAID_EXTERNAL_SERVICES_ENABLED=false;
const PRIVATE_HEADERS={'Cache-Control':'private, no-store, max-age=0'};
async function readLimitedJson(req){
 const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
 if(contentType!=='application/json') return {};
 const rawLength=req.headers.get('content-length');
 if(rawLength!==null){
  const normalizedLength=rawLength.trim();
  if(!/^\d+$/.test(normalizedLength)) return {};
  const declaredLength=Number(normalizedLength);
  if(!Number.isSafeInteger(declaredLength)) return {};
  if(declaredLength>MAX_REQUEST_BYTES) return {};
 }
 const reader=req.body?.getReader(); let total=0;
 while(true){const {done,value}=await reader.read();if(done)break;if(!value)continue;total+=value.byteLength;if(total>MAX_REQUEST_BYTES){await reader.cancel();return {}}}
 const bytes=new Uint8Array(total); const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 return {body:JSON.parse(raw||'{}')};
}
async function handler(req){
 const user=await requiredUser(req);
 const parsedRequest=await readLimitedJson(req);
 const body=parsedRequest.body||{};
 if(Object.keys(body).length!==1||typeof body.party_code!=='string')return {};
 const party={owner_user_id:user.id}; if(party.owner_user_id!==user.id)return {};
 await service.rpc('service_submit_fracture_endgame',{});
 return parsedRequest;
}
"""
    clean = validate_sources(gateway, endgame)
    if clean:
        raise AssertionError('Le cas sain Fracture doit passer: ' + ' | '.join(clean))

    mutations = {
        'gateway MIME préfixe': (gateway.replace("contentType!=='application/json'", "!contentType.startsWith('application/json')"), endgame),
        'gateway req.text': (gateway.replace('const reader=req.body?.getReader();', 'const raw=await req.text();'), endgame),
        'gateway cancel retiré': (gateway.replace('await reader.cancel();', ''), endgame),
        'gateway UTF-8 permissif': (gateway.replace("new TextDecoder('utf-8',{fatal:true})", "new TextDecoder('utf-8')"), endgame),
        'gateway Content-Length fail-open': (gateway.replace("if(!/^\\d+$/.test(normalizedLength)) return {};", "if(Number.isFinite(declaredLength)&&declaredLength>MAX_BODY_BYTES)return {};"), endgame),
        'endgame MIME préfixe': (gateway, endgame.replace("contentType!=='application/json'", "!contentType.startsWith('application/json')")),
        'endgame req.text': (gateway, endgame.replace('const reader=req.body?.getReader();', 'const raw=await req.text();')),
        'endgame cancel retiré': (gateway, endgame.replace('await reader.cancel();', '')),
        'endgame UTF-8 permissif': (gateway, endgame.replace("new TextDecoder('utf-8',{fatal:true})", "new TextDecoder('utf-8')")),
        'endgame auth déplacée': (gateway, endgame.replace('const user=await requiredUser(req);\n const parsedRequest=await readLimitedJson(req);', 'const parsedRequest=await readLimitedJson(req);\n const user=await requiredUser(req);')),
    }
    for label, (mut_gateway, mut_endgame) in mutations.items():
        if mut_gateway == gateway and mut_endgame == endgame:
            raise AssertionError(f'Mutation sans effet: {label}')
        if not validate_sources(mut_gateway, mut_endgame):
            raise AssertionError(f'Régression non détectée: {label}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide les frontières HTTP des Edge Functions Fracture.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test sécurité requêtes Edge Fracture.')
        return 0

    if not GATEWAY.exists() or not ENDGAME.exists():
        missing = [str(p.relative_to(ROOT)) for p in (GATEWAY, ENDGAME) if not p.exists()]
        print('ECHEC sécurité requêtes Edge Fracture: fichier(s) absent(s): ' + ', '.join(missing))
        return 1

    errors = validate_sources(read(GATEWAY), read(ENDGAME))
    if errors:
        print(f'ECHEC sécurité requêtes Edge Fracture: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK Edge Fracture: JWT avant corps, JSON exact, Content-Length fail-closed, corps bornés en streaming, UTF-8 strict, propriétaire endgame et services payants verrouillés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
