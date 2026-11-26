import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {consumeLicenseAttempt} from '../supabase/functions/_shared/license-attempt-budget.mjs';
const account='123e4567-e89b-42d3-a456-426614174000';
test('strict quota result, server user, timeout and provider failure',async()=>{
  for(const [result,expected] of [[{data:true,error:null},'allowed'],[{data:false,error:null},'limited'],[{data:'true'},'unavailable'],[{data:true,error:{}},'unavailable'],[null,'unavailable']]){
    const s={rpc(name,args){assert.equal(name,'consume_license_attempt_budget');assert.deepEqual(args,{p_user_id:account});return {abortSignal(signal){assert.ok(signal instanceof AbortSignal);return Promise.resolve(result);}};}};
    assert.equal(await consumeLicenseAttempt(s,account,30),expected);
  }
  assert.equal(await consumeLicenseAttempt({rpc(){throw Error('fixture');}},account,30),'unavailable');
  assert.equal(await consumeLicenseAttempt({rpc(){return {abortSignal(){return new Promise(()=>{});}};}},account,30),'unavailable');
  assert.equal(await consumeLicenseAttempt({},'not-uuid',30),'unavailable');
});
test('actual handler denies quota before hash and activation, never trusts client identity',async()=>{
  const src=readFileSync(new URL('../supabase/functions/redeem-license-code/index.ts',import.meta.url),'utf8');
  let serve,allowed='limited',auth=true,hashed=0,redeemed=0,healthCalls=0,attempts=0;
  const PRIVATE_HEADERS={'Cache-Control':'private, no-store, max-age=0','Content-Type':'application/json'};
  const s={rpc:async(name,args)=>{assert.equal(name,'redeem_sinjira_activation');assert.equal(args.p_user_id,account);redeemed++;return {data:[{product_slug:'test'}],error:null};}};
  vm.runInNewContext(src.slice(src.indexOf('Deno.serve(async req=>{')),{
    Deno:{serve(fn){serve=fn;},env:{get(){return 'fixture-only';}}},Response,JSON,String,
    VERSION:'fixture',MIN_CODE_LENGTH:12,MAX_CODE_LENGTH:80,PRIVATE_HEADERS,corsHeaders:{},
    privateJson:(body,status=200)=>new Response(JSON.stringify(body),{status,headers:PRIVATE_HEADERS}),
    requiredUser:async()=>{if(!auth)throw Error('AUTH_REQUIRED');return {id:account};},
    readLimitedJson:async req=>({body:req.body}),serviceClient:()=>s,
    licenseHealth:async()=>{healthCalls++;return {ok:true,data:{internal:'fixture'}};},
    consumeLicenseAttempt:async(_s,id)=>{assert.equal(id,account);attempts++;return allowed;},
    digest:async()=>{hashed++;return 'fixture-hash';},console:{error(){}}
  },{timeout:1000});
  const req={method:'POST',body:{code:'SYNTHETIC-TEST-CODE',user_id:'third-party'}};
  auth=false;assert.equal((await serve(req)).status,401);auth=true;
  assert.equal(attempts,0);
  const health=await serve({method:'POST',body:{action:'health'}});
  assert.deepEqual(await health.json(),{ok:true,service:'redeem-license-code',version:'fixture'});
  assert.equal(attempts,0);
  assert.equal((await serve({method:'POST',body:{code:{value:'arbitrary'}}})).status,400);
  const busy=await serve(req);assert.equal(busy.status,429);assert.equal(busy.headers.get('Retry-After'),'600');
  assert.equal((await busy.json()).code,'LICENSE_ATTEMPT_LIMIT');
  allowed='unavailable';assert.equal((await serve(req)).status,503);
  assert.equal(hashed,0);assert.equal(redeemed,0);
  allowed='allowed';assert.equal((await serve(req)).status,200);
  assert.equal(hashed,1);assert.equal(redeemed,1);assert.equal(attempts,3);
});
