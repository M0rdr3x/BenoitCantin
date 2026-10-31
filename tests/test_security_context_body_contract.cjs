'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=path.join(__dirname,'..');
const code=fs.readFileSync(path.join(root,'supabase/functions/security-context/index.ts'),'utf8');
const marker='async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }> {';
const i=code.indexOf(marker),j=code.indexOf('\n}\n\nfunction safeText',i);
assert.ok(i>=0&&j>i,'Lecteur de production non identifiable');
const readerCode=code.slice(i,j+2).replace(marker,'async function readLimitedJson(req) {')
  .replace('let raw: string;','let raw;');
assert.doesNotMatch(readerCode,/await req\.(?:json|text)\(/);
assert.match(code,/const user = await requiredUser\(req\);[\s\S]*const sessionId = sessionIdFromVerifiedRequest\(req\);[\s\S]*const parsed = await readLimitedJson\(req\);/);
let fn;
async function parser(){
  if(!fn){
    const {readBoundedRequestText}=await import(pathToFileURL(
      path.join(root,'supabase/functions/_shared/bounded-request.mjs')).href);
    fn=new Function('readBoundedRequestText','privateJson','MAX_REQUEST_BYTES','TextEncoder','Response',
      readerCode+'\nreturn readLimitedJson;')(
      readBoundedRequestText,
      (data,status=200)=>new Response(JSON.stringify(data),{
        status,headers:{'Content-Type':'application/json','Cache-Control':'private, no-store, max-age=0'}
      }),4096,TextEncoder,Response);
  }
  return fn;
}
function req(body,headers={'content-type':'application/json'}){
  return new Request('https://example.invalid/functions/v1/security-context',{
    method:'POST',headers,...(body===undefined?{}:{body})
  });
}
async function expectStatus(request,status){
  const parsed=await (await parser())(request);
  assert.equal(parsed.response?.status,status);
  assert.equal(parsed.response?.headers.get('cache-control'),'private, no-store, max-age=0');
}
test('objet JSON strict et MIME JSON avec charset',async()=>{
  const a=await (await parser())(req('{"device_key":"0123456789abcdef"}',{'content-type':'application/json; charset=utf-8'}));
  assert.deepEqual(a.body,{device_key:'0123456789abcdef'});
});
test('racines tableaux/primitives, JSON vide et syntaxe invalide refusés',async()=>{
  for(const body of ['[]','null','false','123','"x"','','{'])await expectStatus(req(body),400);
  await expectStatus(req(undefined),400);
});
test('content-type manquant, non JSON ou séquence rejetés',async()=>{
  for(const value of [null,'text/plain','application/json-seq','application/x-www-form-urlencoded']){
    await expectStatus(req('{}',value===null?{}:{'content-type':value}),415);
  }
});
test('en-têtes Content-Length non canoniques et dépassement rejetés',async()=>{
  for(const value of ['4.0','+4','1e2','-1','4097','9007199254740992']){
    await expectStatus(req('{}',{'content-type':'application/json','content-length':value}),413);
  }
  await expectStatus(req('a'.repeat(4097)),413);
});
test('UTF-8 non valide ou trames non binaires rejetés',async()=>{
  await expectStatus(req(Uint8Array.of(0xc3,0x28)),400);
  const fake={headers:new Headers({'content-type':'application/json'}),
    body:{getReader:()=>({read:async()=>({done:false,value:'not-bytes'}),
      cancel:()=>Promise.resolve(),releaseLock:()=>{}})}};
  await expectStatus(fake,400);
});
test('abus de micro-fragments provoque 413 et annulation',async()=>{
  let cancelled=false;
  const fake={headers:new Headers({'content-type':'application/json'}),
    body:{getReader:()=>({read:async()=>({done:false,value:Uint8Array.of(32)}),
      cancel:()=>{cancelled=true;return Promise.resolve()},releaseLock:()=>{}})}};
  await expectStatus(fake,413);
  assert.equal(cancelled,true);
});
test('expiration convertie en 408, jamais en 500',async()=>{
  const timeoutFn=new Function('readBoundedRequestText','privateJson','MAX_REQUEST_BYTES','TextEncoder','Response',
    readerCode+'\nreturn readLimitedJson;')(
    async()=>{throw new Error('REQUEST_TIMEOUT')},
    (data,status)=>new Response(JSON.stringify(data),{status,headers:{'Cache-Control':'private, no-store, max-age=0'}}),
    4096,TextEncoder,Response);
  const result=await timeoutFn(req('{}'));
  assert.equal(result.response?.status,408);
});
