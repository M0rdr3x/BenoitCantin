#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/get-document-url/index.ts'

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'JSON explicite': "contentType!=='application/json'",
    'lecteur borné partagé': "import { readBoundedRequestText } from '../_shared/bounded-request.mjs';",
    'limite appliquée pendant le flux': 'readBoundedRequestText(req,MAX_REQUEST_BYTES)',
    'longueur déclarée canonique': 'Number.isSafeInteger(Number(rawLength))',
    'racine JSON objet': 'Array.isArray(body)',
    'JSON sans valeur par défaut': 'JSON.parse(raw)',
    'refus du flux expiré': "error.message==='REQUEST_TIMEOUT'",
    'refus de dépassement': "error.message==='REQUEST_TOO_LARGE'",
    'UUID strict': 'const UUID_RE=',
    'document_id chaîne uniquement': "typeof parsed.body?.document_id==='string'",
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options':'nosniff'",
    'référent masqué': "'Referrer-Policy':'no-referrer'",
    'auth optionnelle': 'optionalUser(req)',
    'document approuvé': "doc.status!=='approved'",
    'projet actif': "doc.projects?.status!=='active'",
    'rang public conditionné à la visibilité': "let userRank=doc.projects?.visibility==='public'?ranks.public:0;",
    'niveau inconnu explicitement bloqué': "if(typeof doc.access_level!=='string'||!Object.hasOwn(ranks,doc.access_level)){",
    'rang calculé uniquement après la liste blanche': "const requiredRank=ranks[doc.access_level];",
    'RPC uniquement si rang insuffisant': "if(user&&userRank<requiredRank){",
    'rang membre ne retire pas le rang public': "userRank=Math.max(userRank,memberRank);",
    'refus sur rang final': "if(userRank<requiredRank){",
    'rang projet serveur': "service.rpc('project_access_rank'",
    'validation URL externe': 'externalUrlAllowed(url)',
    'URL de registre non normalisée avant validation': 'const url=String(doc.external_url);',
    'origine canonique des chemins locaux': "const OFFICIAL_ORIGIN='https://www.benoitcantin.com';",
    'origine locale non négociable': 'url.origin===OFFICIAL_ORIGIN',
    'refus des séparateurs encodés': '(?:2f|5c|0[0-9a-f]|1[0-9a-f]|7f)',
    'refus des identifiants intégrés': '!url.username&&!url.password',
    'protocole HTTPS externe explicite': "url.protocol==='https:'&&!!url.hostname",
    'lien signé 600 secondes': 'createSignedUrl(doc.storage_path,600)',
    'TTL réponse 600 secondes': 'expires_in:600',
    'log à code fixe': "console.error('[get-document-url]',{code:'GET_DOCUMENT_URL_FAILED'});",
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 512 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*512\s*;'),
    'UUID RFC4122 borné': re.compile(r'\^\[0-9a-f\]\{8\}-.+\$\/i'),
}

FORBIDDEN = {
    'JSON direct non borné': 'await req.json()',
    'texte direct non borné': 'await req.text()',
    'coercition arbitraire document_id': "String(parsed.body?.document_id",
    'objet erreur brut': 'console.error(e)',
    'objet error brut': 'console.error(error)',
    'message erreur brut journalisé': 'console.error(error.message)',
    'message erreur brut exposé': 'error:error.message',
    'stack erreur brute': 'error.stack',
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'get-document-url illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde get-document-url absent: {label}.')
    for label, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(source):
            errors.append(f'Garde get-document-url absent ou affaibli: {label}.')
    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde get-document-url violé: {label}.')

    read_pos = source.find('const parsed=await readLimitedJson(req)')
    lookup_pos = source.find(".from('documents')")
    if read_pos < 0 or lookup_pos < 0 or read_pos > lookup_pos:
        errors.append('La requête doit être validée avant toute lecture de documents via service role.')

    # Une liste blanche sans retour HTTP 403 immédiat laisserait des rangs
    # serveur très élevés (>= 999) autoriser les niveaux inconnus.
    guard_pos = source.find("if(typeof doc.access_level!=='string'||!Object.hasOwn(ranks,doc.access_level)){")
    refuse_pos = source.find(
        "return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);",
        guard_pos
    )
    rank_pos = source.find('const requiredRank=ranks[doc.access_level];')
    rpc_pos = source.find("service.rpc('project_access_rank'")
    if not (lookup_pos >= 0 and guard_pos > lookup_pos and
            refuse_pos > guard_pos and rank_pos > refuse_pos and
            rpc_pos > rank_pos):
        errors.append(
            'Le niveau inconnu doit renvoyer HTTP 403 avant calcul du rang et toute RPC.'
        )
    signed_pos = source.find('createSignedUrl(doc.storage_path,600)' )
    response_ttl_pos = source.find('expires_in:600', signed_pos)
    if signed_pos < 0 or response_ttl_pos < signed_pos:
        errors.append('Le lien privé doit rester signé 600 secondes et annoncer le même TTL.')

    return errors


def self_test() -> None:
    safe = """
import { readBoundedRequestText } from '../_shared/bounded-request.mjs';
const MAX_REQUEST_BYTES=512;
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const PRIVATE_JSON_HEADERS={
 'Cache-Control':'private, no-store, max-age=0',
 'X-Content-Type-Options':'nosniff',
 'Referrer-Policy':'no-referrer'
};
function privateJson(data,status=200){return new Response(JSON.stringify(data),{status,headers:PRIVATE_JSON_HEADERS});}
const OFFICIAL_ORIGIN='https://www.benoitcantin.com';
function externalUrlAllowed(value){
  if(!value||value.trim()!==value)return false;
  if(value.startsWith('/')&&!value.startsWith('//')){
    if(/%(?:2f|5c|0[0-9a-f]|1[0-9a-f]|7f)/i.test(value))return false;
    const url=new URL(value,OFFICIAL_ORIGIN);
    return url.origin===OFFICIAL_ORIGIN&&!url.username&&!url.password;
  }
  const url=new URL(value);
  return url.protocol==='https:'&&!!url.hostname&&!url.username&&!url.password;
}
async function readLimitedJson(req){
  const contentType=(req.headers.get('content-type')||'').toLowerCase();
  if(contentType!=='application/json')return {response:privateJson({},415)};
  const rawLength=req.headers.get('content-length');
  if(rawLength!==null&&!Number.isSafeInteger(Number(rawLength)))return {response:privateJson({},413)};
  let raw;
  try{raw=await readBoundedRequestText(req,MAX_REQUEST_BYTES);}
  catch(error){
    if(error instanceof Error && error.message==='REQUEST_TIMEOUT')return {response:privateJson({},408)};
    if(error instanceof Error && error.message==='REQUEST_TOO_LARGE')return {response:privateJson({},413)};
    return {response:privateJson({},400)};
  }
  const body=JSON.parse(raw);
  if(!body||typeof body!=='object'||Array.isArray(body))return {response:privateJson({},400)};
  return {body};
}
Deno.serve(async(req)=>{
 if(req.method!=='POST')return privateJson({},405);
 try{
  const parsed=await readLimitedJson(req);
  const document_id=typeof parsed.body?.document_id==='string'?parsed.body.document_id.trim():'';
  if(!UUID_RE.test(document_id))return privateJson({},400);
  const service=serviceClient(),user=await optionalUser(req);
  const {data:doc}=await service.from('documents').select('status,projects(status)').eq('id',document_id).maybeSingle();
  if(doc.status!=='approved'||doc.projects?.status!=='active')return privateJson({},404);
  if(typeof doc.access_level!=='string'||!Object.hasOwn(ranks,doc.access_level)){
    return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);
  }
  const requiredRank=ranks[doc.access_level];
  let userRank=doc.projects?.visibility==='public'?ranks.public:0;
  if(user&&userRank<requiredRank){
    await service.rpc('project_access_rank',{p_project_id:doc.project_id,p_user_id:user?.id});
    const memberRank=10;
    userRank=Math.max(userRank,memberRank);
  }
  if(userRank<requiredRank){return privateJson({},403);}
  const url=String(doc.external_url); if(!externalUrlAllowed(url))return privateJson({},500);
  const signed=await service.storage.from('x').createSignedUrl(doc.storage_path,600);
  return privateJson({ok:true,url:signed.signedUrl,expires_in:600});
 }catch{
  console.error('[get-document-url]',{code:'GET_DOCUMENT_URL_FAILED'});
  return privateJson({},500);
 }
});
"""
    with TemporaryDirectory() as raw:
        path = Path(raw) / 'index.ts'
        path.write_text(safe, encoding='utf-8')
        clean = validate(path)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        mutations = {
            'limite augmentée': safe.replace('MAX_REQUEST_BYTES=512;', 'MAX_REQUEST_BYTES=8192;'),
            'type JSON retiré': safe.replace("if(contentType!=='application/json')return {response:privateJson({},415)};", ''),
            'longueur forgée acceptée': safe.replace("Number.isSafeInteger(Number(rawLength))", "true"),
            'racine tableau acceptée': safe.replace("Array.isArray(body)", "false"),
            'JSON vide réintroduit': safe.replace("JSON.parse(raw)", "JSON.parse(raw||'{}')"),
            'req.json direct': safe.replace('raw=await readBoundedRequestText(req,MAX_REQUEST_BYTES);', 'raw=await req.json();'),
            'req.text direct': safe.replace('raw=await readBoundedRequestText(req,MAX_REQUEST_BYTES);', 'raw=await req.text();'),
            'contrôle de taille retiré': safe.replace("error.message==='REQUEST_TOO_LARGE'", 'false'),
            'lecteur partagé retiré': safe.replace('raw=await readBoundedRequestText(req,MAX_REQUEST_BYTES);', "raw='{}';"),
            'expiration neutralisée': safe.replace("error.message==='REQUEST_TIMEOUT'", 'false'),
            'coercition document_id': safe.replace("typeof parsed.body?.document_id==='string'?parsed.body.document_id.trim():''", "String(parsed.body?.document_id||'').trim()"),
            'no-store retiré': safe.replace(" 'Cache-Control':'private, no-store, max-age=0',\n", ''),
            'TTL signé augmenté': safe.replace('createSignedUrl(doc.storage_path,600)', 'createSignedUrl(doc.storage_path,3600)'),
            'log brut': safe.replace("}catch{\n  console.error('[get-document-url]',{code:'GET_DOCUMENT_URL_FAILED'});", "}catch(error){\n  console.error(error);"),
            'origine locale retirée': safe.replace('url.origin===OFFICIAL_ORIGIN', 'true'),
            'séparateurs encodés acceptés': safe.replace(
                'if(/%(?:2f|5c|0[0-9a-f]|1[0-9a-f]|7f)/i.test(value))return false;',
                'if(false)return false;'),
            'identifiants intégrés acceptés': safe.replace(
                '!url.username&&!url.password', 'true'),
            'HTTPS externe relâché': safe.replace(
                "url.protocol==='https:'&&!!url.hostname", '!!url.hostname'),
            'URL nettoyée avant validation': safe.replace(
                'const url=String(doc.external_url);',
                'const url=String(doc.external_url).trim();'),
            'niveau hérité autorisé': safe.replace(
                "!Object.hasOwn(ranks,doc.access_level)", 'false'),
            'type du niveau non vérifié': safe.replace(
                "typeof doc.access_level!=='string'||", ''),
            'garde niveau désactivée': safe.replace(
                "if(typeof doc.access_level!=='string'||!Object.hasOwn(ranks,doc.access_level)){",
                "if(false){"),
            'refus strict déplacé après RPC': safe.replace(
                "  if(typeof doc.access_level!=='string'||!Object.hasOwn(ranks,doc.access_level)){\n"
                "    return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);\n"
                "  }\n  const requiredRank=ranks[doc.access_level];",
                "  const requiredRank=ranks[doc.access_level];\n"
                "  if(typeof doc.access_level!=='string'||!Object.hasOwn(ranks,doc.access_level)){\n"
                "    return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);\n"
                "  }"),
            'refus explicite 403 neutralisé': safe.replace(
                "    return privateJson({ok:false,error:'Votre compte ne possède pas le niveau d’accès requis.'},403);",
                "    return privateJson({ok:true},200);"),
            'rang public retiré': safe.replace(
                "let userRank=doc.projects?.visibility==='public'?ranks.public:0;",
                "let userRank=0;"),
            'RPC exigé même pour public': safe.replace(
                "if(user&&userRank<requiredRank){", "if(user){"),
            'rang public écrasé par projet': safe.replace(
                "userRank=Math.max(userRank,memberRank);", "userRank=memberRank;"),
        }
        for label, mutated in mutations.items():
            if mutated == safe:
                raise AssertionError(f'Mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Régression non détectée: {label}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière publique de get-document-url.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test get-document-url security.')
        return 0
    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC get-document-url: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK get-document-url: POST JSON borné à 512 octets avec timeout et limite de fragments, UUID typé, refus no-store et liens signés 600 s.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
