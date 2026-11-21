#!/usr/bin/env node
'use strict';
// Tester le vrai parseur Edge en VM Node, sans réseau ni identifiants réels.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
(async()=>{
  const source=fs.readFileSync(path.resolve(__dirname,
    '../supabase/functions/fracture-engine-gateway/index.ts'),'utf8');
  assert.match(source,/const MAX_BODY_BYTES=32_000;/);
  assert.match(source,/const MAX_BODY_READ_TIMEOUT_MS=4_000;/);
  assert.match(source,/if\(contentType!=='application\/json'\)/);
  assert.doesNotMatch(source,/contentType\.startsWith\('application\/json'\)/);
  assert.ok(source.indexOf('await client.auth.getUser(token)') <
            source.indexOf('const parsed=await readLimitedJson(req);'),
            'JWT exigé avant lecture du corps');
  for(const marker of ['fracture_engine_get_state_safe','ALLOWED_ACTIONS',
    "'Cache-Control':'private, no-store, max-age=0'",
    "console.error('[fracture-engine-gateway]',{code:'FRACTURE_GATEWAY_REQUEST_REJECTED'});"])
    assert.ok(source.includes(marker),'Garde absent : '+marker);

  const begin=source.indexOf('async function readLimitedJson(req:Request):Promise<{body?:JsonRecord;response?:Response}>{');
  const end=source.indexOf('\nDeno.serve(async(req)=>{',begin);
  assert.ok(begin>=0&&end>begin,'Parseur de production introuvable');
  const block=source.slice(begin,end)
    .replace('readLimitedJson(req:Request):Promise<{body?:JsonRecord;response?:Response}>','readLimitedJson(req)')
    .replace('let parsed:unknown;','let parsed;')
    .replace('parsed as JsonRecord','parsed');
  assert.doesNotMatch(block,/await\s+reader\.(?:read|cancel)\s*\(/);
  assert.doesNotMatch(block,/await\s+req\.(?:text|json)\s*\(/);
  assert.match(block,/readLimitedUtf8BodyWithDeadline/);

  const {readLimitedUtf8BodyWithDeadline}=await import('../supabase/functions/_shared/read-chunk-deadline.mjs');
  let count=0;
  const guarded=(req,max,ms)=>{
    count++;
    assert.equal(max,32000,'Limite octets modifiée');
    assert.equal(ms,4000,'Délai de production modifié');
    // Raccourcir seulement le délai du test. Mécanisme de production identique.
    return readLimitedUtf8BodyWithDeadline(req,max,45);
  };
  const privateJson=(obj,status=200)=>new Response(JSON.stringify(obj),
    {status,headers:{'Cache-Control':'private, no-store'}});
  const read=vm.runInNewContext(
    "const MAX_BODY_BYTES=32000;const MAX_BODY_READ_TIMEOUT_MS=4000;" +
    "const GATEWAY_VERSION='24.4.15';const readLimitedUtf8BodyWithDeadline=guarded;\n" +
    block+'\nreadLimitedJson',{guarded,privateJson},{timeout:3000});

  const encoder=new TextEncoder();
  const b=value=>encoder.encode(value);
  const stream=parts=>new ReadableStream({
    start(c){for(const v of parts)c.enqueue(v);c.close();}
  });
  const make=(body,{mime='application/json',length,signal}={})=>{
    const headers=new Headers({'content-type':mime});
    if(length!==undefined)headers.set('content-length',length);
    return new Request('https://example.invalid/fracture-engine-gateway',{
      method:'POST',duplex:'half',body,headers,...(signal?{signal}:{})
    });
  };
  const full=(raw,opts)=>make(stream([b(raw)]),opts);
  const refusal=async(req,status)=>{
    const result=await read(req);
    assert.equal(result.response?.status,status,'HTTP '+status+' attendu');
    assert.equal(result.response.headers.get('Cache-Control'),'private, no-store');
  };
  const valid=await read(make(stream([b('{"action":'),b('"fracture_engine_start"}')])));
  assert.equal(valid.body.action,'fracture_engine_start');
  const charset=await read(full('{"action":"fracture_engine_start"}',
    {mime:'application/json; charset=utf-8'}));
  assert.equal(charset.body.action,'fracture_engine_start');

  await refusal(full('{}',{mime:'application/json-evil'}),415);
  await refusal(full('{}',{mime:'application/jsonx'}),415);
  await refusal(full('{}',{mime:'text/plain'}),415);
  await refusal(full('{}',{length:'NaN'}),413);
  await refusal(full('{}',{length:'01'}),413);
  await refusal(full('{}',{length:'32001'}),413);
  await refusal(full('invalid json'),400);
  await refusal(full('[]'),400);
  await refusal(make(stream([new Uint8Array([0xc3])])),400);
  await refusal(make(stream([new Uint8Array(32001)]),{length:'1'}),413);

  let cancellations=0;
  const frozen=new ReadableStream({
    pull(){return new Promise(()=>{});},
    cancel(){cancellations++;return new Promise(()=>{});}
  });
  const began=performance.now();
  await refusal(make(frozen),408);
  assert.ok(performance.now()-began<1000,'Annulation non résolue ne doit pas bloquer HTTP 408');
  assert.equal(cancellations,1,'Annulation non bloquante attendue');

  const partial=new ReadableStream({
    start(c){c.enqueue(b('{"action":'));},
    pull(){return new Promise(()=>{});},
    cancel(){return new Promise(()=>{});}
  });
  await refusal(make(partial),408);

  const controller=new AbortController();controller.abort();
  await refusal(make(stream([b('{}')]),{signal:controller.signal}),408);
  assert.ok(count>=8,'Le vrai parseur ne teste plus assez la primitive de production');
  console.log('OK Fracture : JWT avant corps, JSON strict, 32 Ko / 4 s absolues, cancel non bloquant, UTF-8 et statut 408.');
})().catch(e=>{console.error(e);process.exitCode=1;});
