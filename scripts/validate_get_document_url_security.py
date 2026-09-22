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
    'normalisation MIME exacte': ".split(';',1)[0].trim().toLowerCase()",
    'JSON exact': "contentType!=='application/json'",
    'lecture bornée par flux': 'req.body?.getReader()',
    'annulation au dépassement': 'reader.cancel()',
    'décodage UTF-8 strict': "new TextDecoder('utf-8',{fatal:true})",
    'objet JSON uniquement': 'function isRecord(value:unknown)',
    'une seule clé JSON': 'Object.keys(body).length!==1',
    'document_id typé dans le JSON': "typeof body.document_id!=='string'",
    'UUID strict': 'const UUID_RE=',
    'document_id chaîne uniquement': "typeof documentIdValue==='string'",
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options':'nosniff'",
    'référent masqué': "'Referrer-Policy':'no-referrer'",
    'auth optionnelle': 'optionalUser(req)',
    'document approuvé': "doc.status!=='approved'",
    'projet actif': "doc.projects?.status!=='active'",
    'product_slug projet chargé': 'child_access_status,product_slug)',
    'slug produit normalisé': "const productSlug=typeof doc.projects?.product_slug==='string'?doc.projects.product_slug.trim():'';",
    'projet payant fermé aux comptes child': '|| productSlug.length>0',
    'admin booléen exact': 'if(isAdmin===true)userRank=100;',
    'rang projet serveur': "service.rpc('project_access_rank'",
    'rang projet numérique': 'Number.isFinite(normalizedRank)',
    'rang projet non négatif': 'normalizedRank<0',
    'niveau inconnu refusé': 'if(userRank<(ranks[doc.access_level]||999))',
    'garde produit sous rang player': 'if(productSlug&&userRank<20)',
    'droit produit serveur': "service.rpc('has_sinjira_product'",
    'erreur droit produit fail-closed': 'if(productError)',
    'droit produit booléen exact': 'if(hasProduct!==true)',
    'storage path typé': "typeof doc.storage_path!=='string'",
    'validation URL externe': 'externalUrlAllowed(url)',
    'lien signé 600 secondes': 'createSignedUrl(doc.storage_path,600)',
    'TTL réponse 600 secondes': 'expires_in:600',
    'log ACL à code fixe': "console.error('[get-document-url]',{code:'INVALID_PROJECT_ACCESS_RANK'});",
    'log produit à code fixe': "console.error('[get-document-url]',{code:'PRODUCT_ACCESS_UNAVAILABLE'});",
    'log à code fixe': "console.error('[get-document-url]',{code:'GET_DOCUMENT_URL_FAILED'});",
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 512 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*512\s*;'),
    'UUID RFC4122 borné': re.compile(r'\^\[0-9a-f\]\{8\}-.+\$\/i'),
}

FORBIDDEN = {
    'JSON direct non borné': 'await req.json()',
    'texte intégral avant borne': 'await req.text()',
    'MIME JSON par préfixe': "startsWith('application/json')",
    'coercition arbitraire document_id': "String(parsed.body?.document_id",
    'admin truthy permissif': 'if(isAdmin)userRank=100',
    'rang RPC coercé sans validation': 'Number(accessRank||0)',
    'log ACL avec identifiant utilisateur': "code:'INVALID_PROJECT_ACCESS_RANK',",
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

    rank_validation_pos = source.find('Number.isFinite(normalizedRank)')
    rank_assignment_pos = source.find('userRank=normalizedRank')
    if rank_validation_pos < 0 or rank_assignment_pos < 0 or rank_validation_pos > rank_assignment_pos:
        errors.append('Le rang projet doit être validé avant son utilisation dans la décision ACL.')

    product_gate_pos = source.find('if(productSlug&&userRank<20)')
    external_url_pos = source.find('if(doc.external_url)')
    if product_gate_pos < 0 or external_url_pos < 0 or product_gate_pos > external_url_pos:
        errors.append('Le droit produit doit être vérifié avant toute livraison de document externe ou privé.')

    signed_pos = source.find('createSignedUrl(doc.storage_path,600)')
    response_ttl_pos = source.find('expires_in:600', signed_pos)
    if signed_pos < 0 or response_ttl_pos < signed_pos:
        errors.append('Le lien privé doit rester signé 600 secondes et annoncer le même TTL.')

    return errors


def self_test() -> None:
    safe = """
const MAX_REQUEST_BYTES=512;
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ranks={public:1,account:10,player:20,tester:30,admin:100};
const PRIVATE_JSON_HEADERS={
 'Cache-Control':'private, no-store, max-age=0',
 'X-Content-Type-Options':'nosniff',
 'Referrer-Policy':'no-referrer'
};
function privateJson(data,status=200){return new Response(JSON.stringify(data),{status,headers:PRIVATE_JSON_HEADERS});}
function externalUrlAllowed(url){return true;}
function isRecord(value:unknown){return !!value&&typeof value==='object'&&!Array.isArray(value);}
async function readLimitedJson(req){
 const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
 if(contentType!=='application/json') return {response:privateJson({},415)};
 const reader=req.body?.getReader();
 if(!reader)return {response:privateJson({},400)};
 const chunks=[]; let total=0;
 while(true){
  const {done,value}=await reader.read(); if(done)break; if(!value)continue;
  total+=value.byteLength;
  if(total>MAX_REQUEST_BYTES){try{await reader.cancel()}catch{} return {response:privateJson({},413)}}
  chunks.push(value);
 }
 const bytes=new Uint8Array(total); let offset=0;
 for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength}
 const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 let body:unknown; try{body=JSON.parse(raw)}catch{return {response:privateJson({},400)}}
 if(!isRecord(body)||Object.keys(body).length!==1||typeof body.document_id!=='string')return {response:privateJson({},400)};
 return {body};
}
Deno.serve(async(req)=>{
 if(req.method!=='POST')return privateJson({},405);
 try{
  const parsed=await readLimitedJson(req);
  const documentIdValue=parsed.body?.document_id;
  const document_id=typeof documentIdValue==='string'?documentIdValue.trim():'';
  if(!UUID_RE.test(document_id))return privateJson({},400);
  const service=serviceClient(),user=await optionalUser(req);
  const {data:doc}=await service.from('documents').select('project_id,status,access_level,child_access_status,storage_bucket,storage_path,projects(status,child_access_status,product_slug)').eq('id',document_id).maybeSingle();
  if(doc.status!=='approved'||doc.projects?.status!=='active')return privateJson({},404);
  const productSlug=typeof doc.projects?.product_slug==='string'?doc.projects.product_slug.trim():'';
  const ageBand='adult';
  if(ageBand==='child'&&(doc.child_access_status!=='approved_11_12'||doc.projects?.child_access_status!=='approved_11_12'|| productSlug.length>0))return privateJson({},403);
  let userRank=0;
  if(user){
   const {data:isAdmin}=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
   if(isAdmin===true)userRank=100;
   else{
    const {data:accessRank}=await service.rpc('project_access_rank',{p_project_id:doc.project_id,p_user_id:user.id});
    const normalizedRank=Number(accessRank??0);
    if(!Number.isFinite(normalizedRank)||normalizedRank<0){console.error('[get-document-url]',{code:'INVALID_PROJECT_ACCESS_RANK'});return privateJson({},403)}
    userRank=normalizedRank;
   }
  }
  if(userRank<(ranks[doc.access_level]||999))return privateJson({},403);
  if(productSlug&&userRank<20){
   if(!user)return privateJson({},403);
   const {data:hasProduct,error:productError}=await service.rpc('has_sinjira_product',{p_product_slug:productSlug,p_user_id:user.id});
   if(productError){console.error('[get-document-url]',{code:'PRODUCT_ACCESS_UNAVAILABLE'});return privateJson({},503)}
   if(hasProduct!==true)return privateJson({},403);
  }
  if(doc.external_url){
   const url='https://example.test'; if(!externalUrlAllowed(url))return privateJson({},500);
  }
  if(!doc.storage_bucket||typeof doc.storage_path!=='string'||!doc.storage_path)return privateJson({},500);
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
            'MIME JSON par préfixe': safe.replace("if(contentType!=='application/json')", "if(!contentType.startsWith('application/json'))"),
            'req.text intégral': safe.replace(' const reader=req.body?.getReader();', ' const raw=await req.text();'),
            'req.json direct': safe.replace(' const reader=req.body?.getReader();', ' const body=await req.json();'),
            'annulation retirée': safe.replace('try{await reader.cancel()}catch{} ', ''),
            'clé JSON inattendue acceptée': safe.replace('Object.keys(body).length!==1||', ''),
            'coercition document_id': safe.replace("typeof documentIdValue==='string'?documentIdValue.trim():''", "String(parsed.body?.document_id||'').trim()"),
            'admin truthy permissif': safe.replace('if(isAdmin===true)userRank=100;', 'if(isAdmin)userRank=100;'),
            'rang non fini accepté': safe.replace('!Number.isFinite(normalizedRank)||', ''),
            'fallback niveau inconnu retiré': safe.replace('(ranks[doc.access_level]||999)', 'ranks[doc.access_level]'),
            'product_slug non chargé': safe.replace(',product_slug)', ')'),
            'garde child produit retirée': safe.replace('|| productSlug.length>0', ''),
            'rang player produit affaibli': safe.replace('if(productSlug&&userRank<20)', 'if(productSlug&&userRank<10)'),
            'RPC droit produit retiré': safe.replace("service.rpc('has_sinjira_product'", "service.rpc('product_access_missing'"),
            'erreur droit produit ignorée': safe.replace('if(productError){', 'if(false){'),
            'droit produit truthy permissif': safe.replace('if(hasProduct!==true)', 'if(!hasProduct)'),
            'storage path non typé': safe.replace("typeof doc.storage_path!=='string'||", ''),
            'log ACL avec identifiant': safe.replace("{code:'INVALID_PROJECT_ACCESS_RANK'}", "{code:'INVALID_PROJECT_ACCESS_RANK',userId:user.id}"),
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
    parser = argparse.ArgumentParser(description='Valide la frontière publique et les décisions ACL de get-document-url.')
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
    print('OK get-document-url: requête bornée, ACL + droit produit fail-closed, contenu 11–12 payant fermé, réponses no-store et lien signé 600 s.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
