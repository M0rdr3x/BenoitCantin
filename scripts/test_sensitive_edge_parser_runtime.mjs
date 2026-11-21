// Exécute les VRAIS parseurs TypeScript des fonctions AAL2 sous VM Node,
// avec le lecteur partagé en production, mais une horloge de test accélérée.
// Aucun compte réel, aucune session, aucun service externe.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import {readLimitedUtf8BodyWithDeadline} from '../supabase/functions/_shared/read-chunk-deadline.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const encoder=new TextEncoder();
const bytes=value=>encoder.encode(value);
const stream=chunks=>new ReadableStream({
  start(controller){for(const chunk of chunks)controller.enqueue(chunk);controller.close();}
});
function request(body,headers={'content-type':'application/json'},signal) {
  return new Request('https://example.invalid/sensitive-aal2',{
    method:'POST',duplex:'half',body,headers,...(signal?{signal}:{})
  });
}
const payload=({text='{"action":"get_state"}',type='application/json',length}={})=>{
  const headers={'content-type':type};
  if(length!==undefined)headers['content-length']=length;
  return request(stream([bytes(text)]),headers);
};
const error=async(run,req,code)=>assert.rejects(run(req),e=>e?.message===code);

function loadParser(slug,budgetBytes,budgetMs) {
  const edge=readFileSync(resolve(root,'supabase/functions',slug,'index.ts'),'utf8');
  const start=edge.indexOf('async function readBoundedJson(req: Request) {');
  const end=edge.indexOf('\nfunction safeText(value: unknown, max: number)',start);
  assert.ok(start>=0&&end>start,slug+': le parseur réel a changé sans adaptation du test');
  let code=edge.slice(start,end);
  code=code.replace('readBoundedJson(req: Request)','readBoundedJson(req)');
  code=code.replace('let parsed: unknown;','let parsed;');
  code=code.replaceAll(' as Record<string, unknown>','');
  assert.doesNotMatch(code,/await\s+reader\.(?:read|cancel)\s*\(/,
    slug+': lecteur sans délai ou annulation bloquante');
  assert.match(code,/readLimitedUtf8BodyWithDeadline/);
  assert.match(edge,new RegExp('MAX_REQUEST_READ_TIMEOUT_MS = '+budgetMs.toLocaleString('en-US').replaceAll(',','_')+';'));
  let uses=0;
  const safeReader=(req,limit,ms)=>{
    uses++;
    assert.equal(limit,budgetBytes,slug+': limite de transport modifiée');
    assert.equal(ms,budgetMs,slug+': échéance en production modifiée');
    return readLimitedUtf8BodyWithDeadline(req,limit,45);
  };
  const read=vm.runInNewContext(
    'const MAX_REQUEST_BYTES='+budgetBytes+';\n'+
    'const MAX_REQUEST_READ_TIMEOUT_MS='+budgetMs+';\n'+
    'const readLimitedUtf8BodyWithDeadline=safeReader;\n'+
    code+'\nreadBoundedJson',
    {safeReader},{timeout:3000}
  );
  return {read,uses:()=>uses};
}

for(const {slug,max,ms} of [
  {slug:'conscience-vault',max:1024*1024*6+64*1024,ms:20000},
  {slug:'personal-ai',max:16*1024,ms:4000}
]) {
  const {read,uses}=loadParser(slug,max,ms);
  const valid=await read(payload());
  assert.equal(valid.action,'get_state',slug+': JSON valide refusé');
  assert.equal((await read(payload({type:'application/json; charset=utf-8'}))).action,'get_state');
  await error(read,payload({type:'application/json-evil'}),'JSON_REQUIRED');
  await error(read,payload({type:'text/plain'}),'JSON_REQUIRED');
  await error(read,payload({length:String(max+1)}),'REQUEST_TOO_LARGE');
  await error(read,payload({length:'NaN'}),'REQUEST_TOO_LARGE');
  await error(read,payload({length:'01'}),'REQUEST_TOO_LARGE');
  await error(read,payload({text:'['}),'INVALID_JSON');
  await error(read,payload({text:'[]'}),'INVALID_JSON');
  await error(read,request(stream([new Uint8Array([0xc3])]),{'content-type':'application/json'}),'INVALID_JSON');
  await error(read,request(stream([new Uint8Array(max+1)]),{'content-type':'application/json','content-length':'1'}),'REQUEST_TOO_LARGE');

  let cancelled=0;
  const frozen=new ReadableStream({
    pull(){return new Promise(()=>{});},
    cancel(){cancelled++;return new Promise(()=>{});}
  });
  const began=performance.now();
  await error(read,request(frozen),'REQUEST_TIMEOUT');
  assert.ok(performance.now()-began<1000,slug+': annulation bloquante');
  assert.equal(cancelled,1,slug+': source gelée sans tentative d’annulation');

  const partial=new ReadableStream({
    start(controller){controller.enqueue(bytes('{"action":'));},
    pull(){return new Promise(()=>{});},
    cancel(){return new Promise(()=>{});}
  });
  await error(read,request(partial),'REQUEST_TIMEOUT');

  const stopped=new AbortController();stopped.abort();
  await error(read,request(stream([bytes('{}')]),{'content-type':'application/json'},stopped.signal),'REQUEST_TIMEOUT');

  assert.ok(uses()>=12,slug+': le parseur réel ne passe plus par la primitive sécurisée');
}
console.log('OK parseurs réels AAL2 : 2 implémentations, JSON strict, taille réelle, timeout global, cancel bloqué, UTF-8 et déconnexion.');
