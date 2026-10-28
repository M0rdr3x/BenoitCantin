'use strict';
// Aucun jeton, fichier ou compte réel : extraction du parseur de production.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=path.join(__dirname,'..');
const production=fs.readFileSync(path.join(root,'supabase/functions/life-story-delivery/index.ts'),'utf8');
const start=production.indexOf('async function readDeliveryToken(req: Request): Promise<{ token?: string; response?: Response }> {');
const end=production.indexOf('\n}\n\nDeno.serve(',start);
assert.ok(start>=0&&end>start,'Le parseur de remise doit provenir du vrai code Edge');
const parsedSource=production.slice(start,end+2).replace(
  'async function readDeliveryToken(req: Request): Promise<{ token?: string; response?: Response }> {',
  'async function readDeliveryToken(req) {').replace('let rawBody:string;','let rawBody;')
  .replace('let payload:unknown;','let payload;')
  .replace('const body=payload as Record<string,unknown>;','const body=payload;');
assert.doesNotMatch(parsedSource,/await req\.(?:text|json)\(/,'Lecteur non borné interdit');
let current;
async function parser(){
  if(!current){
    const {readBoundedRequestText}=await import(pathToFileURL(path.join(root,'supabase/functions/_shared/bounded-request.mjs')).href);
    const errorResponse=(req,status=404)=>new Response('Indisponible',{status,headers:{
      'Cache-Control':'private, no-store, max-age=0'}});
    current=new Function('readBoundedRequestText','MAX_REQUEST_BYTES','errorResponse',
      'Response','Number','Object',parsedSource+'\nreturn readDeliveryToken;')(
        readBoundedRequestText,256,errorResponse,Response,Number,Object);
  }
  return current;
}
function request(body,headers={'content-type':'application/json'}){
  return new Request('https://example.invalid/functions/v1/life-story-delivery',{
    method:'POST',headers,...(body===undefined?{}:{body})
  });
}
const good=JSON.stringify({token:'a'.repeat(64)});
async function denied(req,status){
  const r=await (await parser())(req);
  assert.equal(r.response?.status,status);
  assert.equal(r.response?.headers.get('Cache-Control'),'private, no-store, max-age=0');
}
test('jeton 256 bits hex minuscule: accepté sans accès base',async()=>{
  const r=await (await parser())(request(good,{'content-type':'application/json; charset=utf-8'}));
  assert.equal(r.token,'a'.repeat(64));
  assert.equal(r.response,undefined);
});
test('MIME faux ou non JSON strict rejeté',async()=>{
  for(const t of [null,'application/jsonx','application/json-seq','text/plain']){
    await denied(request(good,t===null?{}:{'content-type':t}),415);
  }
});
test('longueurs forgées, non canoniques et corps > 256 rejetés',async()=>{
  for(const v of ['2.0','+2','1e3','-1','257','9007199254740992']){
    await denied(request(good,{'content-type':'application/json','content-length':v}),413);
  }
  await denied(request('x'.repeat(257)),413);
});
test('JSON vide, tableau, primitive et clés excédentaires rejetés',async()=>{
  for(const raw of ['', '[]','null','"str"','5','true','{',
    JSON.stringify({token:'a'.repeat(64),extra:'x'})]){
    await denied(request(raw),400);
  }
  await denied(request(undefined),400);
});
test('jeton invalide: 404 générique sans lecture service role',async()=>{
  for(const raw of ['abc','A'.repeat(64),'g'.repeat(64),'a'.repeat(63)]){
    await denied(request(JSON.stringify({token:raw})),404);
  }
});
test('UTF-8 invalide et fragments non binaires rejetés',async()=>{
  await denied(request(Uint8Array.of(0xc3,0x28)),400);
  const bad={headers:new Headers({'content-type':'application/json'}),
    body:{getReader:()=>({read:async()=>({done:false,value:'not-a-byte-array'}),
      cancel:()=>Promise.resolve(),releaseLock:()=>{}})}};
  await denied(bad,400);
});
test('flux de micro-fragments annulé à la limite',async()=>{
  let cancelled=false;
  const fake={headers:new Headers({'content-type':'application/json'}),
    body:{getReader:()=>({read:async()=>({done:false,value:Uint8Array.of(32)}),
      cancel:()=>{cancelled=true;return Promise.resolve()},releaseLock:()=>{}})}};
  await denied(fake,413);
  assert.equal(cancelled,true);
});
test('délai absolu du reader devient HTTP 408 non cachable',async()=>{
  const fn=new Function('readBoundedRequestText','MAX_REQUEST_BYTES','errorResponse',
    'Response','Number','Object',parsedSource+'\nreturn readDeliveryToken;')(
    async()=>{throw new Error('REQUEST_TIMEOUT')},256,
    (req,status=404)=>new Response('Indisponible',{status,headers:{
      'Cache-Control':'private, no-store, max-age=0'}}),Response,Number,Object);
  const r=await fn(request(good));
  assert.equal(r.response?.status,408);
});
test('autorisation de remise après parsing et avant lecture Storage',()=>{
  const parserCall=production.indexOf('const parsed=await readDeliveryToken(req);');
  const tokenHash=production.indexOf('const hash = await sha256Hex(token);');
  const blobDownload=production.indexOf(".download(record.storage_path)");
  const atomicCounter=production.indexOf("service.rpc('service_life_story_register_download'");
  assert.ok(parserCall>0&&parserCall<tokenHash&&tokenHash<blobDownload&&blobDownload<atomicCounter);
});
