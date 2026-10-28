'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=path.join(__dirname,'..');
const source=fs.readFileSync(path.join(root,'supabase/functions/get-document-url/index.ts'),'utf8');
const begin=source.indexOf('async function readLimitedJson(req:Request):Promise<{body?:any;response?:Response}>{');
const end=source.indexOf('\n}\n\nDeno.serve',begin);
assert.ok(begin>=0&&end>begin,'Lecteur de production get-document-url introuvable');
const code=source.slice(begin,end+2)
 .replace('async function readLimitedJson(req:Request):Promise<{body?:any;response?:Response}>{','async function readLimitedJson(req){')
 .replace('let raw:string;','let raw;');
assert.doesNotMatch(code,/await req\.(?:text|json)\(/);
let real;
async function parser(){
 if(!real){
  const {readBoundedRequestText}=await import(pathToFileURL(path.join(root,'supabase/functions/_shared/bounded-request.mjs')).href);
  real=new Function('readBoundedRequestText','privateJson','MAX_REQUEST_BYTES','Response',
  code+'\nreturn readLimitedJson;')(readBoundedRequestText,
  (body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Cache-Control':'private, no-store, max-age=0'}}),512,Response);
 }
 return real;
}
function make(body,headers={'content-type':'application/json'}){
 return new Request('https://example.invalid/functions/v1/get-document-url',{
  method:'POST',headers,...(body===undefined?{}:{body})
 });
}
async function reject(req,code){
 const out=await (await parser())(req);
 assert.equal(out.response?.status,code);
 assert.equal(out.response?.headers.get('Cache-Control'),'private, no-store, max-age=0');
}
test('UUID légitime dans un objet JSON reste accepté',async()=>{
 const out=await (await parser())(make('{"document_id":"11111111-1111-4111-8111-111111111111"}',
 {'content-type':'application/json; charset=UTF-8'}));
 assert.equal(out.response,undefined);
 assert.equal(out.body.document_id,'11111111-1111-4111-8111-111111111111');
});
test('corps JSON vides, tableaux, primitives et malformés rejetés',async()=>{
 for(const v of ['',undefined,'[]','null','123','true','"abc"','{'])
  await reject(make(v),400);
});
test('MIME absent ou faux refusé',async()=>{
 for(const ct of [null,'text/plain','application/jsonx','application/json-seq']){
  await reject(make('{}',ct===null?{}:{'content-type':ct}),415);
 }
});
test('Content-Length falsifié, non entier ou dépassant 512 refusé',async()=>{
 for(const v of ['-1','+12','3.0','1e2','513','9007199254740992']){
  await reject(make('{}',{'content-type':'application/json','content-length':v}),413);
 }
 await reject(make('x'.repeat(513)),413);
});
test('octets UTF-8 invalides et segments non binaires refusés',async()=>{
 await reject(make(Uint8Array.of(0xc3,0x28)),400);
 const bad={headers:new Headers({'content-type':'application/json'}),
  body:{getReader:()=>({read:async()=>({done:false,value:'text-not-bytes'}),
   cancel:()=>Promise.resolve(),releaseLock:()=>{}})}};
 await reject(bad,400);
});
test('plus de 4096 fragments refusés avant les droits',async()=>{
 let cancelled=false;
 const bad={headers:new Headers({'content-type':'application/json'}),
  body:{getReader:()=>({read:async()=>({done:false,value:Uint8Array.of(32)}),
   cancel:()=>{cancelled=true;return Promise.resolve()},releaseLock:()=>{}})}};
 await reject(bad,413);assert.equal(cancelled,true);
});
test('délai de lecture 408 non cachable',async()=>{
 const timeout=new Function('readBoundedRequestText','privateJson','MAX_REQUEST_BYTES','Response',
  code+'\nreturn readLimitedJson;')(
  async()=>{throw new Error('REQUEST_TIMEOUT')},
  (body,status)=>new Response(JSON.stringify(body),{status,headers:{'Cache-Control':'private, no-store, max-age=0'}}),
  512,Response);
 const response=await timeout(make('{}'));
 assert.equal(response.response?.status,408);
});
