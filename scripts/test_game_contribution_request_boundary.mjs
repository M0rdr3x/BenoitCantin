// Tests locaux de sécurité de la contribution SINJIRA : aucun compte ni réseau.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readLimitedUtf8BodyWithDeadline } from '../supabase/functions/_shared/read-chunk-deadline.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const edge=readFileSync(resolve(root,'supabase/functions/submit-game-contribution/index.ts'),'utf8');
const requireGuard=(marker)=>assert.ok(edge.includes(marker),'Garde contribution absent : '+marker);
for(const marker of [
  'MAX_REQUEST_BYTES=2048',
  'MAX_REQUEST_READ_TIMEOUT_MS=4_000',
  "contentType!=='application/json'",
  'readLimitedUtf8BodyWithDeadline(req,MAX_REQUEST_BYTES,MAX_REQUEST_READ_TIMEOUT_MS)',
  "limited.reason==='REQUEST_TIMEOUT'",
  "code:'REQUEST_TIMEOUT'},408)",
  "console.error('[submit-game-contribution]',{code:'GAME_CONTRIBUTION_FAILED'});",
  "const user=await requiredUser(req);",
  "const body=await readBoundedJson(req);",
  ".eq('user_id',user.id)",
]) requireGuard(marker);
assert.ok(edge.indexOf('const user=await requiredUser(req);') <
  edge.indexOf('const body=await readBoundedJson(req);'),
  'Un compte doit être authentifié avant la lecture du corps');
for(const marker of [
  "console.error('[submit-game-contribution]',e)",
  'console.error(e)',
  'await req.json()',
  'await req.text()',
  "readLimitedUtf8Body(req,MAX_REQUEST_BYTES)",
]) assert.ok(!edge.includes(marker),'Régression de confidentialité ou de délai : '+marker);

const encoder=new TextEncoder();
const request=(body,headers={})=>new Request('https://example.invalid/submit-game-contribution',{
  method:'POST',duplex:'half',headers,body
});
const stream=(fragments)=>new ReadableStream({
  start(controller){for(const value of fragments)controller.enqueue(value);controller.close();}
});
const good=request(stream([encoder.encode('{"a":'),encoder.encode('1}')]));
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(good,2048,200),
  {ok:true,raw:'{"a":1}'});
const oversized=request(stream([new Uint8Array(2049)]));
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(oversized,2048,200),
  {ok:false,reason:'REQUEST_TOO_LARGE'});
const misleading=request(stream([encoder.encode('{}')]),{'content-length':'NaN'});
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(misleading,2048,200),
  {ok:false,reason:'REQUEST_TOO_LARGE'});
const invalidUtf8=request(stream([new Uint8Array([0xC3])]));
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(invalidUtf8,2048,200),
  {ok:false,reason:'INVALID_BODY'});

let attempts=0;
const frozen=request(new ReadableStream({
  pull(){return new Promise(()=>{});},
  cancel(){attempts++;return new Promise(()=>{});}
}));
const started=performance.now();
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(frozen,2048,40),
  {ok:false,reason:'REQUEST_TIMEOUT'});
assert.ok(performance.now()-started<1000,'Le délai ne doit pas attendre cancel()');
assert.equal(attempts,1,'Le flux interrompu doit déclencher une annulation consultative');

const aborted=new AbortController();
aborted.abort();
const disconnected=new Request('https://example.invalid/disconnected',{
  method:'POST',signal:aborted.signal
});
assert.deepEqual(await readLimitedUtf8BodyWithDeadline(disconnected,2048,200),
  {ok:false,reason:'REQUEST_TIMEOUT'});

console.log('OK contribution : lecture sûre 2 KiB/4 s, flux gelé et annulation non bloquante, aucun log brut ni réseau.');
