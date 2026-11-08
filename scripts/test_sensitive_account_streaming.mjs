import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readLimitedUtf8Body } from '../supabase/functions/_shared/limited-body.mjs';

// Lecture locale, sans utilisateur, JWT, requête distante ni modification.
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const cases=[
  {slug:'delete-player-account',max:1024,logger:'DELETE_FAILED'},
  {slug:'revoke-my-contributions',max:2048,logger:'REVOCATION_FAILED'},
  {slug:'redeem-license-code',max:4096,logger:'LICENSE_UNEXPECTED_ERROR'}
];
const encoder=new TextEncoder();
function request(chunks,headers={}){
  return new Request('https://example.invalid/functions/v1/security-test',{
    method:'POST',duplex:'half',headers,
    body:new ReadableStream({start(c){for(const item of chunks)c.enqueue(item);c.close();}})
  });
}
for(const {slug,max,logger} of cases){
  const source=readFileSync(resolve(root,'supabase/functions',slug,'index.ts'),'utf8');
  assert.match(source,/import \{ readLimitedUtf8Body \} from '\.\.\/_shared\/limited-body\.mjs'/,
    slug+': lecteur partagé obligatoire');
  assert.ok(source.includes('readLimitedUtf8Body(req,MAX_REQUEST_BYTES)'),slug+': limite en flux absente');
  assert.ok(source.includes('MAX_REQUEST_BYTES='+max),slug+': limite historique altérée');
  assert.doesNotMatch(source,/\bawait\s+req\.(?:text|json)\s*\(/,
    slug+': lecture intégrale interdite');
  assert.ok(source.includes("code:'"+logger+"'"),slug+': code de log constant absent');
  assert.doesNotMatch(source,/console\.error\([^\n]*(?:,\s*error|,\s*e)\s*\)/,
    slug+': erreur fournisseur brute interdite');

  const small=request([encoder.encode('{"ok":true}')]);
  assert.deepEqual(await readLimitedUtf8Body(small,max),{ok:true,raw:'{"ok":true}'});
  const boundary=request([new Uint8Array(max)]);
  assert.equal((await readLimitedUtf8Body(boundary,max)).ok,true);
  const tooLong=request([new Uint8Array(max),new Uint8Array([1])]);
  assert.deepEqual(await readLimitedUtf8Body(tooLong,max),{ok:false});
  const fakeLength=request([new Uint8Array(max+1)],{'content-length':'1'});
  assert.deepEqual(await readLimitedUtf8Body(fakeLength,max),{ok:false});
  const invalidLength=request([encoder.encode('a')],{'content-length':'NaN'});
  assert.deepEqual(await readLimitedUtf8Body(invalidLength,max),{ok:false});
  const invalidUtf=request([new Uint8Array([0xc3])]);
  assert.deepEqual(await readLimitedUtf8Body(invalidUtf,max),{ok:false});
}
const novel=readFileSync(resolve(root,'supabase/functions/get-novel-file-url/index.ts'),'utf8');
assert.match(novel,/console\.error\('\[get-novel-file-url\]',\{code:'NOVEL_ACCESS_FAILED'\}\)/);
assert.doesNotMatch(novel,/console\.error\(error\)/);
console.log('OK sécurité compte : suppression 1 KiB, révocation 2 KiB, licences 4 KiB et liens romans avec logs expurgés. Aucun appel réseau.');
