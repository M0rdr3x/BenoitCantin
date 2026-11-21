// Validation locale du lecteur partagé sur les Edge AAL2 sensibles.
// Aucune donnée de compte ni requête externe : flux de test entièrement fictifs.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readLimitedUtf8BodyWithDeadline } from '../supabase/functions/_shared/read-chunk-deadline.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const encoder=new TextEncoder();

for (const route of [
  {slug:'conscience-vault',timeout:'20_000',auth:'requiredVaultUser'},
  {slug:'personal-ai',timeout:'4_000',auth:'requiredPersonalAiUser'}
]) {
  const source=readFileSync(resolve(root,'supabase/functions',route.slug,'index.ts'),'utf8');
  const required=[
    "import { readLimitedUtf8BodyWithDeadline } from '../_shared/read-chunk-deadline.mjs';",
    'const MAX_REQUEST_READ_TIMEOUT_MS = '+route.timeout+';',
    'req, MAX_REQUEST_BYTES, MAX_REQUEST_READ_TIMEOUT_MS',
    "limited.reason === 'REQUEST_TIMEOUT'",
    "limited.reason === 'REQUEST_TOO_LARGE'",
    "throw new Error('INVALID_JSON')",
    'await '+route.auth+'(req)',
    'await readBoundedJson(req)',
    "'Cache-Control': 'private, no-store, max-age=0'"
  ];
  for(const marker of required){
    assert.ok(source.includes(marker),route.slug+': garde absente '+marker);
  }
  assert.ok(source.indexOf('await '+route.auth+'(req)') <
            source.indexOf('await readBoundedJson(req)'),
    route.slug+': la MFA doit précéder le traitement du corps');
  for(const forbidden of [
    'req.body.getReader()', 'await reader.read()', 'await reader.cancel(',
    'await req.text()', 'await req.json()'
  ]) assert.ok(!source.includes(forbidden),route.slug+': régression '+forbidden);
}

const request=(chunks,headers={})=>new Request('https://example.invalid/aal2',{
  method:'POST',duplex:'half',headers,
  body:new ReadableStream({start(controller){
    for (const chunk of chunks)controller.enqueue(chunk);
    controller.close();
  }})
});
const valid=request([encoder.encode('{"action":'),encoder.encode('"get_state"}')]);
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(valid,1024,300),
  {ok:true,raw:'{"action":"get_state"}'});

const misleading=request([encoder.encode('{}')],{'content-length':'garbage'});
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(misleading,1024,300),
  {ok:false,reason:'REQUEST_TOO_LARGE'});
const tooBig=request([new Uint8Array(1025)],{'content-length':'1'});
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(tooBig,1024,300),
  {ok:false,reason:'REQUEST_TOO_LARGE'});
const malformed=request([new Uint8Array([0xc3])]);
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(malformed,1024,300),
  {ok:false,reason:'INVALID_BODY'});

let cancels=0;
const frozen=new Request('https://example.invalid/aal2',{
  method:'POST',duplex:'half',
  body:new ReadableStream({
    pull(){return new Promise(()=>{});},
    cancel(){cancels++;return new Promise(()=>{});}
  })
});
const before=performance.now();
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(frozen,1024,45),
  {ok:false,reason:'REQUEST_TIMEOUT'});
assert.ok(performance.now()-before<1000,'Une annulation bloquée ne doit pas empêcher le refus');
assert.equal(cancels,1,'L’annulation doit être tentée même en cas de flux bloqué');

const controller=new AbortController();
controller.abort();
const disconnected=new Request('https://example.invalid/aal2',{
  method:'POST',signal:controller.signal
});
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(disconnected,1024,300),
  {ok:false,reason:'REQUEST_TIMEOUT'});

console.log('OK AAL2 sensible : limites en octets, deadline absolue, annulation non bloquante, UTF-8 strict, MFA avant corps.');
