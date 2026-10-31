'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=path.join(__dirname,'..');
const file=fs.readFileSync(path.join(root,'supabase/functions/send-game-report/index.ts'),'utf8');
const begin=file.indexOf('async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }> {');
const end=file.indexOf('\n}\n\nconst MAX_TEXT',begin);
assert.ok(begin>=0&&end>begin,'Le vrai lecteur Edge doit être identifiable');
const code=file.slice(begin,end+2)
 .replace('async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }> {',
          'async function readLimitedJson(req) {')
 .replace('let raw:string;','let raw;');
assert.doesNotMatch(code,/await req\.(?:json|text)\(/);
let active;
async function reader(){
 if(!active){
  const {readBoundedRequestText}=await import(pathToFileURL(path.join(root,'supabase/functions/_shared/bounded-request.mjs')).href);
  active=new Function('readBoundedRequestText','privateJson','MAX_REQUEST_BYTES','TextEncoder','Response','FUNCTION_VERSION',
    code+'\nreturn readLimitedJson;')(
    readBoundedRequestText,
    (body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Cache-Control':'private, no-store, max-age=0'}}),
    220000,TextEncoder,Response,'24.5.2');
 }
 return active;
}
function make(body,headers={'content-type':'application/json'}){
 return new Request('https://example.invalid/report',{method:'POST',headers,...(body===undefined?{}:{body})});
}
async function denied(input,status){
 const result=await (await reader())(input);
 assert.equal(result.response?.status,status);
 assert.equal(result.response?.headers.get('Cache-Control'),'private, no-store, max-age=0');
}
test('mode download et fiche JSON structurée restent admis avec charset',async()=>{
 const x=await (await reader())(make('{"mode":"download","sheet_data":{"nom_pseudo":"Test"}}',
 {'content-type':'application/json; charset=utf-8'}));
 assert.equal(x.body?.mode,'download');
 assert.equal(x.body?.sheet_data?.nom_pseudo,'Test');
});
test('MIME faux et en-tête manquant refusés sans PDF',async()=>{
 for(const kind of [null,'text/plain','application/jsonx','application/json-seq']){
  await denied(make('{}',kind===null?{}:{'content-type':kind}),415);
 }
});
test('JSON non objet, vide, tronqué et UTF8 invalide refusés',async()=>{
 for(const body of ['','[]','null','"quoted"','0','true','{'])
  await denied(make(body),400);
 await denied(make(undefined),400);
 await denied(make(Uint8Array.of(0xc3,0x28)),400);
});
test('Content-Length falsifié, décimal, négatif ou trop grand rejeté',async()=>{
 for(const value of ['0.0','+5','1e3','-1','220001','9007199254740992'])
  await denied(make('{}',{'content-type':'application/json','content-length':value}),413);
 await denied(make('x'.repeat(220001)),413);
});
test('flux à fragments non binaires rejeté',async()=>{
 const request={headers:new Headers({'content-type':'application/json'}),
 body:{getReader:()=>({read:async()=>({done:false,value:'raw-text'}),cancel:()=>Promise.resolve(),releaseLock:()=>{}})}};
 await denied(request,400);
});
test('flux excessivement fragmenté annulé et refusé avant génération',async()=>{
 let cancelled=false;
 const request={headers:new Headers({'content-type':'application/json'}),
 body:{getReader:()=>({read:async()=>({done:false,value:Uint8Array.of(32)}),
  cancel:()=>{cancelled=true;return Promise.resolve()},releaseLock:()=>{}})}};
 await denied(request,413);
 assert.equal(cancelled,true);
});
test('délai de lecture -> HTTP 408 no-store',async()=>{
 const timeout=new Function('readBoundedRequestText','privateJson','MAX_REQUEST_BYTES','TextEncoder','Response','FUNCTION_VERSION',
 code+'\nreturn readLimitedJson;')(
 async()=>{throw new Error('REQUEST_TIMEOUT')},
 (body,status)=>new Response(JSON.stringify(body),{status,headers:{'Cache-Control':'private, no-store, max-age=0'}}),
 220000,TextEncoder,Response,'24.5.2');
 const x=await timeout(make('{}'));
 assert.equal(x.response?.status,408);
});
test('mode et fiche invalide refusés avant création du PDF',()=>{
 const handler=file.slice(file.indexOf('    const body = parsed.body;'),file.indexOf('    const user = await optionalUser(req);'));
 assert.match(handler,/body\.mode !== 'download' && body\.mode !== 'email'/);
 assert.match(handler,/Array\.isArray\(body\.sheet_data\)/);
 assert.ok(handler.indexOf("Array.isArray(body.sheet_data)")>handler.indexOf("body.mode !== 'download'"));
});
