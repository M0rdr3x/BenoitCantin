#!/usr/bin/env node
'use strict';
// Exécuter le vrai parseur HTTP du contexte sécurité avec des sources fictives.
// Aucune session, donnée personnelle, clé, requête réseau ou RPC Supabase.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

(async () => {
  const edge = fs.readFileSync(path.resolve(__dirname,
    '../supabase/functions/security-context/index.ts'), 'utf8');
  const begin = edge.indexOf('async function readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }> {');
  const end = edge.indexOf('\nfunction safeText(value: unknown, max: number)', begin);
  assert.ok(begin >= 0 && end > begin, 'Parseur réel security-context introuvable');
  let parser = edge.slice(begin, end)
    .replace('readLimitedJson(req: Request): Promise<{ body?: any; response?: Response }>', 'readLimitedJson(req)')
    .replace('const body: unknown =', 'const body =');
  assert.doesNotMatch(parser, /await\s+(?:req\.(?:text|json)|reader\.(?:read|cancel))\s*\(/);

  assert.ok(edge.indexOf('const user = await requiredUser(req);') <
    edge.indexOf('const parsed = await readLimitedJson(req);'),
    'Authentification JWT doit précéder lecture du corps');
  assert.match(edge, /console\.error\('\[security-context\]', \{ code: 'SECURITY_CONTEXT_FAILED' \}\)/);
  assert.doesNotMatch(edge, /console\.error\('\[security-context\]', error\)/);
  assert.match(edge, /const MAX_REQUEST_BYTES = 4096;/);
  assert.match(edge, /const MAX_REQUEST_READ_TIMEOUT_MS = 4_000;/);

  const { readLimitedUtf8BodyWithDeadline } = await import(
    '../supabase/functions/_shared/read-chunk-deadline.mjs');
  let calls = 0;
  const guarded = (req, limit, timeout) => {
    calls++;
    assert.equal(limit, 4096, 'plafond d’octets actuel conservé');
    assert.equal(timeout, 4000, 'délai de production absolu conservé');
    // Délai accéléré pour l’essai du blocage, véritable lecteur partagé inchangé.
    return readLimitedUtf8BodyWithDeadline(req, limit, 40);
  };
  const privateJson = (value, status=200) =>
    new Response(JSON.stringify(value), { status, headers:{'Cache-Control':'private, no-store'} });
  const read = vm.runInNewContext(
    'const MAX_REQUEST_BYTES=4096;const MAX_REQUEST_READ_TIMEOUT_MS=4000;\n' +
    'const readLimitedUtf8BodyWithDeadline=guarded;\n' + parser +
    '\nreadLimitedJson', { guarded, privateJson }, { timeout:3000 });

  const bytes=s=>new TextEncoder().encode(s);
  const chunks=list=>new ReadableStream({
    start(c){for(const item of list)c.enqueue(item);c.close();}
  });
  const make=(body, { mime='application/json', declared, signal }={})=>{
    const headers=new Headers({'content-type':mime});
    if(declared!==undefined)headers.set('content-length',declared);
    return new Request('https://example.invalid/security-context',{
      method:'POST', duplex:'half', headers, body, ...(signal?{signal}:{})
    });
  };
  const full=(text,opts)=>make(chunks([bytes(text)]),opts);
  const refusal=async(req,status)=>{
    const value=await read(req);
    assert.equal(value.response?.status,status,'HTTP attendu : '+status);
    assert.equal(value.response.headers.get('Cache-Control'),'private, no-store');
    return value;
  };

  const ok=await read(full('{"device_key":"aaaaaaaaaaaaaaaa","action":"session"}'));
  assert.equal(ok.body.device_key,'aaaaaaaaaaaaaaaa');
  assert.equal((await read(full('{}',{mime:'application/json; charset=utf-8'}))).body instanceof Object, true);
  await refusal(full('{}',{mime:'application/json-evil'}),415);
  await refusal(full('{}',{mime:'text/plain'}),415);
  await refusal(full('{}',{declared:'NaN'}),413);
  await refusal(full('{}',{declared:'4097'}),413);
  await refusal(full('{}',{declared:'01'}),413);
  await refusal(full('not a json'),400);
  await refusal(full('[]'),400);
  await refusal(full(''),400);
  await refusal(make(chunks([new Uint8Array([0xc3])])),400);
  await refusal(make(chunks([new Uint8Array(4097)]),{declared:'1'}),413);

  let cancelCount=0;
  const stuck=new ReadableStream({
    pull(){return new Promise(()=>{});},
    cancel(){cancelCount++;return new Promise(()=>{});}
  });
  const start=performance.now();
  await refusal(make(stuck),408);
  assert.ok(performance.now()-start<1000,'cancel() bloqué ne doit pas retarder 408');
  assert.equal(cancelCount,1,'une annulation consultative est tentée');

  const partial=new ReadableStream({
    start(c){c.enqueue(bytes('{"device_key":'));},
    pull(){return new Promise(()=>{});},
    cancel(){return new Promise(()=>{});}
  });
  await refusal(make(partial),408);

  const aborted=new AbortController();
  aborted.abort();
  await refusal(make(chunks([bytes('{}')]),{signal:aborted.signal}),408);
  assert.ok(calls >= 14,'Le vrai parseur doit appeler le lecteur partagé.');
  console.log('OK security-context : JWT avant corps, JSON strict, 4 KiB, délai absolu, cancel bloqué, UTF-8, erreurs privées et logs expurgés.');
})().catch(error=>{console.error(error);process.exitCode=1;});
