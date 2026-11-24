import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { createPdfAdmissionGate } from '../supabase/functions/_shared/pdf-admission.mjs';
import { consumeReportBudget } from '../supabase/functions/_shared/report-pdf-budget.mjs';

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
  let serve, reads = 0, budgetCalls = 0, budgetResult = 'allowed';
  let user = null;
  const budgetClasses = [];
  const headers = {'Cache-Control':'private, no-store, max-age=0','Content-Type':'application/json; charset=utf-8'};
  const privateJson = (value,status=200)=>new Response(JSON.stringify(value),{status,headers});
  vm.runInNewContext(handler, {
    Deno:{serve(fn){serve=fn;}},
    Response, JSON, Date, String,
    corsHeaders:{}, PRIVATE_JSON_HEADERS:headers,
    FUNCTION_VERSION:'fixture', PAID_EXTERNAL_SERVICES_ENABLED:false,
    acquirePdfSlot:createPdfAdmissionGate(2),
    readLimitedJson:async req=>{reads++; return {body:req.body};},
    optionalUser:async()=>user,
    serviceClient:()=>({}),
    consumeReportBudget:async (_service, authenticated)=>{budgetCalls++;budgetClasses.push(authenticated);return budgetResult;},
    recordDelivery:async()=>{},
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
  assert.equal(budgetCalls,4,'local saturation and disabled email do not consume shared budget');
  budgetResult = 'limited';
  const limited = await serve({...req,body:{mode:'download',authenticated:true}});
  assert.equal(limited.status,429);
  assert.equal((await limited.json()).code,'REPORT_QUOTA_EXCEEDED');
  assert.equal(limited.headers.get('Retry-After'),'60');
  assert.equal(budgetClasses.at(-1),false,'client body cannot select the account pool');
  budgetResult = 'unavailable';
  assert.equal((await serve(req)).status,503);
  user={id:'synthetic-account'};
  assert.equal((await serve(req)).status,503);
  assert.equal(budgetClasses.at(-1),true,'verified user alone chooses account pool');
  assert.equal(jobs.length,4,'denied or unavailable quota never generates PDF');
  budgetResult='allowed';
  const recovered=serve(req); await tick();
  assert.equal(jobs.length,5,'quota refusal released the local slot');
  jobs[4].resolve(new Uint8Array([1]));
  assert.equal((await recovered).status,200);
});

test('shared quota helper accepts only strict boolean results and fails closed', async () => {
  for (const [result,expected] of [
    [{data:true,error:null},'allowed'],
    [{data:false,error:null},'limited'],
    [{data:'true',error:null},'unavailable'],
    [{data:true,error:{code:'synthetic'}},'unavailable'],
    [null,'unavailable']
  ]) {
    const calls=[];
    const service={rpc(name,args){calls.push({name,args});return {abortSignal(signal){assert.ok(signal instanceof AbortSignal);return Promise.resolve(result);}};}};
    assert.equal(await consumeReportBudget(service,false,25),expected);
    assert.deepEqual(calls,[{name:'consume_report_pdf_budget',args:{p_authenticated:false}}]);
  }
  assert.equal(await consumeReportBudget({rpc(){throw Error('synthetic');}},true,25),'unavailable');
  assert.equal(await consumeReportBudget({rpc(){return {abortSignal(){return new Promise(()=>{});}};}},true,25),'unavailable');
  assert.equal(await consumeReportBudget({},'true',25),'unavailable');
});
