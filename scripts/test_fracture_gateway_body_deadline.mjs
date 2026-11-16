import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { readLimitedUtf8BodyWithDeadline } from '../supabase/functions/_shared/read-chunk-deadline.mjs';

const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const fakeRequest=(reader,signal=new AbortController().signal,contentLength=null)=>({
  headers:new Headers(contentLength===null?{}:{'content-length':contentLength}),
  signal,
  body:{getReader:()=>reader}
});

test('Fracture: JSON intact avant le délai avec accents UTF-8',async()=>{
  const raw='{"action":"fracture_engine_start","args":{"p_party_code":"FRM-ABC123"},"note":"Québec"}';
  const req=new Request('https://edge.test',{
    method:'POST',body:raw,headers:{'Content-Type':'application/json'}
  });
  const actual=await readLimitedUtf8BodyWithDeadline(req,32_000,800);
  assert.deepEqual(actual,{ok:true,raw});
});

test('Fracture: stream bloqué retourne REQUEST_TIMEOUT sans attendre une annulation bloquée',async()=>{
  let cancelled=0;
  let released=0;
  const reader={
    read:()=>new Promise(()=>{}),
    cancel:()=>{cancelled++;return new Promise(()=>{});},
    releaseLock:()=>{released++;}
  };
  const started=performance.now();
  const actual=await readLimitedUtf8BodyWithDeadline(fakeRequest(reader),32_000,45);
  assert.deepEqual(actual,{ok:false,reason:'REQUEST_TIMEOUT'});
  assert.equal(cancelled,1);
  assert.equal(released,1);
  assert.ok(performance.now()-started<500,'Le refus ne doit pas dépendre du producteur HTTP');
});

test('Fracture: plusieurs petits fragments ne renouvellent pas le délai',async()=>{
  let count=0,cancelled=0;
  const reader={
    read:async()=>{await sleep(45);count++;return {done:false,value:Uint8Array.of(123)};},
    cancel:async()=>{cancelled++;},
    releaseLock:()=>{}
  };
  const actual=await readLimitedUtf8BodyWithDeadline(fakeRequest(reader),32_000,70);
  assert.deepEqual(actual,{ok:false,reason:'REQUEST_TIMEOUT'});
  assert.ok(count<=2,'Délai global plutôt que minuterie renouvelée');
  assert.equal(cancelled,1);
});

test('Fracture: la requête interrompue est refusée avant lecture',async()=>{
  const abort=new AbortController();abort.abort();
  let reads=0;
  const reader={
    read:()=>{reads++;return Promise.resolve({done:true});},
    cancel:async()=>{},releaseLock:()=>{}
  };
  const result=await readLimitedUtf8BodyWithDeadline(fakeRequest(reader,abort.signal),32_000,200);
  assert.deepEqual(result,{ok:false,reason:'REQUEST_TIMEOUT'});
  assert.equal(reads,0);
});

test('Fracture: Content-Length faux est rejeté avant la lecture',async()=>{
  for(const declaration of ['-1','0005','NaN','Infinity','32_000','9007199254740992','32001']){
    let reads=0;
    const reader={
      read:()=>{reads++;return Promise.resolve({done:true});},
      releaseLock:()=>{}
    };
    const result=await readLimitedUtf8BodyWithDeadline(
      fakeRequest(reader,new AbortController().signal,declaration),32_000,200
    );
    assert.equal(result.ok,false,declaration);
    assert.equal(reads,0,'Aucune lecture à cause du Content-Length '+declaration);
  }
});

test('Fracture: octets réellement reçus contrôlés sans confiance envers Content-Length',async()=>{
  let cancelled=0,released=0;
  let reads=0;
  const reader={
    read:async()=>({done:false,value:reads++===0?new Uint8Array(32_000):Uint8Array.of(1)}),
    cancel:async()=>{cancelled++;},
    releaseLock:()=>{released++;}
  };
  const result=await readLimitedUtf8BodyWithDeadline(fakeRequest(reader),32_000,800);
  assert.deepEqual(result,{ok:false,reason:'REQUEST_TOO_LARGE'});
  assert.equal(cancelled,1);
  assert.equal(released,1);
});

test('Fracture: UTF-8 invalide et flux brisé refusés sans refléter les données',async()=>{
  const invalid=new Request('https://edge.test',{
    method:'POST',body:Uint8Array.of(0xc3,0x28),duplex:'half'
  });
  assert.deepEqual(await readLimitedUtf8BodyWithDeadline(invalid,32_000,400),
    {ok:false,reason:'INVALID_BODY'});
  const boom={
    read:()=>Promise.reject(new Error('PRIVATE_SQL_SERVICE_DIAGNOSTICS')),
    cancel:async()=>{},releaseLock:()=>{}
  };
  const result=await readLimitedUtf8BodyWithDeadline(fakeRequest(boom),32_000,400);
  assert.deepEqual(result,{ok:false,reason:'INVALID_BODY'});
  assert.ok(!JSON.stringify(result).includes('PRIVATE_SQL_SERVICE_DIAGNOSTICS'));
});

test('Fracture: le gestionnaire conserve JWT avant lecture et retourne 408 sans RPC',()=>{
  const script=readFileSync(
    new URL('../supabase/functions/fracture-engine-gateway/index.ts',import.meta.url),'utf8'
  );
  assert.match(script,/BODY_READ_TIMEOUT_MS=8_000/);
  assert.match(script,/readLimitedUtf8BodyWithDeadline\(req,MAX_BODY_BYTES,BODY_READ_TIMEOUT_MS\)/);
  assert.match(script,/limited\.reason==='REQUEST_TIMEOUT'/);
  assert.match(script,/code:'REQUEST_TIMEOUT',gateway_version:GATEWAY_VERSION},408/);
  assert.ok(script.indexOf('client.auth.getUser(token)')<script.indexOf('await readLimitedJson(req)'));
  assert.match(script,/client\.rpc\('fracture_engine_get_state_safe'/);
  assert.match(script,/MAX_BODY_BYTES=32_000/);
});
