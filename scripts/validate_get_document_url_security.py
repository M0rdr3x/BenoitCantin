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
    'JSON explicite': "contentType.startsWith('application/json')",
    'lecture bornée par texte': 'const raw=await req.text();',
    'mesure UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'UUID strict': 'const UUID_RE=',
    'document_id chaîne uniquement': "typeof parsed.body?.document_id==='string'",
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options':'nosniff'",
    'référent masqué': "'Referrer-Policy':'no-referrer'",
    'auth optionnelle': 'optionalUser(req)',
    'document approuvé': "doc.status!=='approved'",
    'projet actif': "doc.projects?.status!=='active'",
    'rang projet serveur': "service.rpc('project_access_rank'",
    'validation URL externe': 'externalUrlAllowed(url)',
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
    'coercition arbitraire document_id': "String(parsed.body?.document_id",
    'objet erreur brut': 'console.error(e)',
    'objet error brut': 'console.error(error)',
    'message erreur brut': 'error.message',
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

    signed_pos = source.find('createSignedUrl(doc.storage_path,600)')
    response_ttl_pos = source.find('expires_in:600', signed_pos)
    if signed_pos < 0 or response_ttl_pos < signed_pos:
        errors.append('Le lien privé doit rester signé 600 secondes et annoncer le même TTL.')

    return errors


def self_test() -> None:
    safe = """
const MAX_REQUEST_BYTES=512;
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const PRIVATE_JSON_HEADERS={
 'Cache-Control':'private, no-store, max-age=0',
 'X-Content-Type-Options':'nosniff',
 'Referrer-Policy':'no-referrer'
};
function privateJson(data,status=200){return new Response(JSON.stringify(data),{status,headers:PRIVATE_JSON_HEADERS});}
function externalUrlAllowed(url){return true;}
async function readLimitedJson(req){
 const contentType=(req.headers.get('content-type')||'').toLowerCase();
 if(!contentType.startsWith('application/json')) return {response:privateJson({},415)};
 const raw=await req.text();
 if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES)return {response:privateJson({},413)};
 return {body:JSON.parse(raw||'{}')};
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
  await service.rpc('project_access_rank',{p_project_id:doc.project_id,p_user_id:user?.id});
  const url='https://example.test'; if(!externalUrlAllowed(url))return privateJson({},500);
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
            'type JSON retiré': safe.replace("if(!contentType.startsWith('application/json')) return {response:privateJson({},415)};", ''),
            'req.json direct': safe.replace('const raw=await req.text();', 'const body=await req.json();'),
            'coercition document_id': safe.replace("typeof parsed.body?.document_id==='string'?parsed.body.document_id.trim():''", "String(parsed.body?.document_id||'').trim()"),
            'no-store retiré': safe.replace(" 'Cache-Control':'private, no-store, max-age=0',\n", ''),
            'TTL signé augmenté': safe.replace('createSignedUrl(doc.storage_path,600)', 'createSignedUrl(doc.storage_path,3600)'),
            'log brut': safe.replace("}catch{\n  console.error('[get-document-url]',{code:'GET_DOCUMENT_URL_FAILED'});", "}catch(error){\n  console.error(error);"),
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
    print('OK get-document-url: POST JSON 512 octets, UUID typé, réponses no-store, accès serveur conservé, lien signé 600 s et logs sanitizés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
