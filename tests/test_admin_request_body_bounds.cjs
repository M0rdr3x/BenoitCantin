'use strict';
// Tests locaux : aucune connexion, aucun compte et aucune requête Supabase.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');

const ROOT=path.resolve(__dirname,'..');
const readerPromise=import(pathToFileURL(path.join(
  ROOT,'supabase/functions/_shared/bounded-request.mjs')).href);
function request(chunks,declared=null,onCancel=()=>{}) {
  let position=0;
  const headers=new Headers();
  if(declared!==null)headers.set('content-length',declared);
  return {
    headers,body:new ReadableStream({
      pull(controller) {
        if(position>=chunks.length) controller.close();
        else controller.enqueue(chunks[position++]);
      },
      cancel(){onCancel();}
    })
  };
}
const bytes=value=>new TextEncoder().encode(value);

test('le corps JSON sous la limite est reconstruit sans perte Unicode',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  const data='{"nom":"Élève","ok":true}';
  const raw=bytes(data);
  const req=request([raw.slice(0,7),raw.slice(7,11),raw.slice(11)],String(raw.length));
  assert.equal(await readBoundedRequestText(req,4096),data);
});
test('borne exacte acceptée et dépassement interrompu au milieu du flux',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  const cap=4096;
  assert.equal((await readBoundedRequestText(request([bytes('a'.repeat(cap))]),cap)).length,cap);
  let cancelled=0;
  await assert.rejects(
    readBoundedRequestText(
      request([bytes('a'.repeat(4090)),bytes('b'.repeat(20)),
               bytes('c'.repeat(200))],null,()=>cancelled++),cap),
    /REQUEST_TOO_LARGE/);
  assert.equal(cancelled,1,'La connexion doit être annulée au dépassement');
});
test('le Content-Length absent ne supprime pas la limite',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  await assert.rejects(
    readBoundedRequestText(request([bytes('x'.repeat(4097))]),4096),
    /REQUEST_TOO_LARGE/);
});
test('en-têtes négatifs, ambigus et surdimensionnés rejetés AVANT lecture',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  for(const header of ['-1','4097','3, 4','not-a-size','9e6']) {
    let called=false;
    const req={headers:new Headers({'content-length':header}),
      body:{getReader(){called=true;throw Error('MUST_NOT_READ');}}};
    await assert.rejects(readBoundedRequestText(req,4096),/REQUEST_TOO_LARGE/);
    assert.equal(called,false,'La lecture ne doit pas commencer: '+header);
  }
});
test('octets UTF-8 invalides et fragments non octet sont refusés',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  await assert.rejects(
    readBoundedRequestText(request([Uint8Array.of(0xc3,0x28)]),4096),
    /INVALID_JSON/);
  await assert.rejects(
    readBoundedRequestText(request([new Int16Array([1])]),4096),
    /INVALID_JSON/);
});
test('limites invalides refusées; corps absent autorisé comme objet vide',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  assert.equal(await readBoundedRequestText({headers:new Headers(),body:null},4096),'');
  await assert.rejects(
    readBoundedRequestText(request([bytes('{}')]),0),/REQUEST_TOO_LARGE/);
  await assert.rejects(
    readBoundedRequestText(request([bytes('{}')]),Infinity),/REQUEST_TOO_LARGE/);
});
test('les six fonctions admin utilisent la borne AVANT req.text()',()=>{
  const functions=[
    'admin-analytics','admin-console','admin-license-codes',
    'admin-reports','admin-sinjira-v18','admin-social-v20'
  ];
  for(const name of functions) {
    const source=fs.readFileSync(path.join(
      ROOT,'supabase/functions',name,'index.ts'),'utf8');
    assert.match(source,/import \{ readBoundedRequestText \} from '\.\.\/_shared\/bounded-request\.mjs'/,
      name+': dépendance sécurisée requise');
    assert.match(source,/await readBoundedRequestText\(req, MAX_REQUEST_BYTES\)/,
      name+': limite serveur requise');
    assert.doesNotMatch(source,/await req\.(?:text|json|arrayBuffer)\(\)/,
      name+': pas de lecture sans contrôle de taille');
    assert.match(source,/await requiredAdmin\(req\)/,name+': MFA admin indispensable');
  }
});
