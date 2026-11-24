import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { createPdfAdmissionGate } from '../supabase/functions/_shared/pdf-admission.mjs';

test('gate is bounded, independent and releases only once', () => {
  for (const n of [0, -1, 1.5, 9, Infinity, '2']) assert.throws(() => createPdfAdmissionGate(n));
  const acquire = createPdfAdmissionGate(2), another = createPdfAdmissionGate(1);
  const a = acquire(), b = acquire();
  assert.equal(acquire(), null);
  assert.equal(typeof another(), 'function');
  a(); a();
  const c = acquire();
  assert.equal(typeof c, 'function');
  assert.equal(acquire(), null);
  b(); c();
  assert.equal(typeof acquire(), 'function');
});

test('real report handler denies saturation, keeps download public and releases on success/error', async () => {
  const source = readFileSync(new URL('../supabase/functions/send-game-report/index.ts', import.meta.url), 'utf8');
  const handler = source.slice(source.indexOf('Deno.serve(async (req) => {'));
  assert.ok(handler.startsWith('Deno.serve('));
  const jobs = [];
  let serve, reads = 0;
  const headers = {'Cache-Control':'private, no-store, max-age=0','Content-Type':'application/json; charset=utf-8'};
  const privateJson = (value,status=200)=>new Response(JSON.stringify(value),{status,headers});
  vm.runInNewContext(handler, {
    Deno:{serve(fn){serve=fn;}},
    Response, JSON, Date, String,
    corsHeaders:{}, PRIVATE_JSON_HEADERS:headers,
    FUNCTION_VERSION:'fixture', PAID_EXTERNAL_SERVICES_ENABLED:false,
    acquirePdfSlot:createPdfAdmissionGate(2),
    readLimitedJson:async req=>{reads++; return {body:req.body};},
    optionalUser:async()=>null,
    sanitizeSheet:x=>x,
    buildPdf:()=>new Promise((resolve,reject)=>jobs.push({resolve,reject})),
    toBase64:()=> 'synthetic',
    privateJson,
    console:{error(){},warn(){}},
  }, {timeout:1000});
  assert.equal(typeof serve,'function');
  const req={method:'POST',body:{mode:'download',sheet_data:{}}};
  const tick=()=>new Promise(resolve=>setImmediate(resolve));
  const a=serve(req), b=serve(req);
  await tick();
  assert.equal(jobs.length,2);
  const busy=await serve(req);
  assert.equal(busy.status,503);
  assert.equal(busy.headers.get('Retry-After'),'3');
  assert.match(busy.headers.get('Cache-Control'),/no-store/);
  assert.equal((await busy.json()).code,'REPORT_BUSY');
  assert.equal(jobs.length,2,'no additional expensive job');
  const disabled=await serve({method:'POST',body:{mode:'email'}});
  assert.equal(disabled.status,503);
  assert.equal((await disabled.json()).code,'PAID_EXTERNAL_SERVICE_DISABLED');
  assert.equal(jobs.length,2);
  jobs[0].resolve(new Uint8Array([1]));
  assert.equal((await a).status,200);
  const c=serve(req);
  await tick();
  assert.equal(jobs.length,3,'success released the slot');
  jobs[1].reject(new Error('synthetic failure'));
  assert.equal((await b).status,500);
  const d=serve(req);
  await tick();
  assert.equal(jobs.length,4,'error released the slot');
  jobs[2].resolve(new Uint8Array([1])); jobs[3].resolve(new Uint8Array([1]));
  assert.equal((await c).status,200);
  assert.equal((await d).status,200);
  assert.equal(reads,6);
});
