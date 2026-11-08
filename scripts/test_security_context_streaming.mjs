import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readLimitedUtf8Body } from '../supabase/functions/_shared/limited-body.mjs';

// Test hors ligne du vrai lecteur en flux utilisé par security-context.
// Aucun JWT, aucune RPC, aucune donnée de session ou d'utilisateur.
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const src=readFileSync(resolve(root,'supabase/functions/security-context/index.ts'),'utf8');
assert.match(src,/import \{ readLimitedUtf8Body \} from '\.\.\/_shared\/limited-body\.mjs'/);
assert.match(src,/readLimitedUtf8Body\(req, MAX_REQUEST_BYTES\)/);
assert.match(src,/const MAX_REQUEST_BYTES = 4096;/);
assert.doesNotMatch(src,/\bawait\s+req\.(?:text|json)\s*\(/);
assert.match(src,/console\.error\('\[security-context\]', \{ code: 'SECURITY_CONTEXT_FAILED' \} \)/);
assert.doesNotMatch(src,/console\.(?:error|log|warn)\('\[security-context\]',\s*error\s*\)/);
const auth=src.indexOf('const user = await requiredUser(req)');
const parse=src.indexOf('const parsed = await readLimitedJson(req)');
assert.ok(auth>=0 && parse>auth,'Authentifier le JWT avant de lire un corps non fiable');

const encoder=new TextEncoder();
function bodyRequest(chunks,extraHeaders={}){
  return new Request('https://example.invalid/functions/v1/security-context',{
    method:'POST',duplex:'half',
    headers:extraHeaders,
    body:new ReadableStream({start(c){for(const ch of chunks)c.enqueue(ch);c.close();}})
  });
}

const ok=bodyRequest([encoder.encode('{"device_key":"abc"}')]);
assert.deepEqual(await readLimitedUtf8Body(ok,4096),{ok:true,raw:'{"device_key":"abc"}'});
const boundary=bodyRequest([new Uint8Array(4000),new Uint8Array(96)]);
assert.equal((await readLimitedUtf8Body(boundary,4096)).ok,true,'4096 octets admis');
const overflow=bodyRequest([new Uint8Array(4000),new Uint8Array(97)]);
assert.deepEqual(await readLimitedUtf8Body(overflow,4096),{ok:false},
  'Dépasser 4096 octets même sans Content-Length doit être refusé');
const lied=bodyRequest([new Uint8Array(4097)],{'content-length':'1'});
assert.deepEqual(await readLimitedUtf8Body(lied,4096),{ok:false},
  'Content-Length faible ne contourne pas la limite');
const tooBig=bodyRequest([encoder.encode('a')],{'content-length':'4097'});
assert.deepEqual(await readLimitedUtf8Body(tooBig,4096),{ok:false},
  'Content-Length trop grand est bloqué avant lecture');
const invalid=bodyRequest([new Uint8Array([0xc3])]);
assert.deepEqual(await readLimitedUtf8Body(invalid,4096),{ok:false},
  'UTF-8 invalide refusé');
console.log('OK security-context: streaming 4KiB, en-tête trompeur, UTF-8 fatal, JWT avant lecture et logs expurgés.');
