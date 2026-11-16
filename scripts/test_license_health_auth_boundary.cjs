'use strict';
// Exécute le véritable gestionnaire Edge, avec dépendances Auth/RPC simulées.
// Aucun JWT, secret, compte ou serveur distant : toutes les données sont fictives.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {stripTypeScriptTypes} = require('node:module');
const {webcrypto} = require('node:crypto');
const {pathToFileURL} = require('node:url');

const ROOT=path.resolve(__dirname,'..');
const SOURCE=fs.readFileSync(
  path.join(ROOT,'supabase/functions/redeem-license-code/index.ts'),'utf8'
);
const IMPORTS=/^import [^\n]+;\r?\n/gm;
const stripped=SOURCE.replace(IMPORTS,'');
assert.equal((SOURCE.match(IMPORTS)||[]).length,3,
  'Les trois dépendances explicites du gestionnaire Edge doivent rester connues');
assert.ok(!/^import /m.test(stripped),'Import non simulé dans le test Edge');
const executable=stripTypeScriptTypes(stripped,{mode:'strip'});

async function run(body,role,options={}){
  const {readLimitedUtf8Body}=await import(pathToFileURL(
    path.join(ROOT,'supabase/functions/_shared/limited-body.mjs')).href);
  const calls={auth:0,admin:0,service:0,pepper:0,rpcs:[],logs:[]};
  let handler;
  const context={
    Deno:{
      serve:fn=>{handler=fn},
      env:{get:key=>{
        assert.equal(key,'SINJIRA_LICENSE_PEPPER');
        calls.pepper++;
        return options.noPepper?null:'only-synthetic-test-pepper';
      }}
    },
    corsHeaders:{'Access-Control-Allow-Origin':'https://www.benoitcantin.com'},
    requiredUser:async()=>{
      calls.auth++;
      if(role==='anonymous')throw new Error('AUTH_REQUIRED');
      return {id:'00000000-0000-4000-8000-000000000123'};
    },
    requiredAdmin:async()=>{
      calls.admin++;
      if(role==='user')throw new Error('ADMIN_REQUIRED');
      if(role==='admin-aal1')throw new Error('MFA_REQUIRED');
      if(role==='admin-no-factor')throw new Error('MFA_SETUP_REQUIRED');
      if(role==='admin-mfa-error')throw new Error('MFA_STATE_UNAVAILABLE');
      if(role!=='admin-aal2')throw new Error('UNEXPECTED_TEST_ROLE');
    },
    serviceClient:()=>{
      calls.service++;
      return {rpc:async(name,args)=>{
        calls.rpcs.push({name,args});
        if(name==='sinjira_license_health')return {
          data:{ok:true, tables:{activation_codes:true},version:'synthetic-only'},
          error:null
        };
        if(name==='redeem_sinjira_activation'){
          assert.equal(args.p_user_id,'00000000-0000-4000-8000-000000000123');
          assert.match(args.p_code_hash,/^[0-9a-f]{64}$/);
          return {data:[{product_slug:'synthetic-test-license'}],error:null};
        }
        throw new Error('RPC_UNKNOWN');
      }};
    },
    readLimitedUtf8Body,
    Response,Request,crypto:webcrypto,TextEncoder,Uint8Array,
    console:{error:(...args)=>calls.logs.push(args)}
  };
  vm.runInNewContext(executable,context,{
    filename:'redeem-license-code/index.ts',timeout:2500
  });
  assert.equal(typeof handler,'function');
  const request=new Request('https://edge.test/functions/v1/redeem-license-code',{
    method:options.method||'POST',
    headers:{'Content-Type':'application/json'},
    ...(options.method==='GET'||options.method==='OPTIONS'?{}:{body:JSON.stringify(body)})
  });
  const response=await handler(request);
  const result=await response.json().catch(()=>null);
  return {status:response.status,result,calls,headers:response.headers};
}
async function main(){
  let cases=0;
  for(const [role,expected,code] of [
    ['anonymous',401,undefined],
    ['user',403,'ADMIN_ACCESS_REQUIRED'],
    ['admin-aal1',403,'ADMIN_ACCESS_REQUIRED'],
    ['admin-no-factor',403,'ADMIN_ACCESS_REQUIRED'],
    ['admin-mfa-error',503,'MFA_STATE_UNAVAILABLE']
  ]){
    const x=await run({action:'health'},role);
    assert.equal(x.status,expected,role+': statut HTTP attendu');
    if(code)assert.equal(x.result.code,code,role+': code d'accès');
    assert.equal(x.calls.service,0,role+': le service ne doit pas être interrogé');
    assert.equal(x.calls.pepper,0,role+': aucun secret ne doit être lu');
    assert.deepEqual(x.calls.rpcs,[],role+': aucune RPC avant autorisation');
    assert.ok(!JSON.stringify(x.result).includes('activation_codes'),
      role+': détails du schéma visibles malgré le refus');
    assert.match(x.headers.get('cache-control'),/no-store/);
    assert.equal(x.headers.get('referrer-policy'),'no-referrer');
    for(const log of x.calls.logs){
      assert.ok(!JSON.stringify(log).includes('only-synthetic-test-pepper'));
    }
    cases++;
  }

  const allowed=await run({action:'health'},'admin-aal2');
  assert.equal(allowed.status,200);
  assert.equal(allowed.result.ok,true);
  assert.equal(allowed.calls.admin,1);
  assert.deepEqual(allowed.calls.rpcs.map(x=>x.name),['sinjira_license_health']);
  assert.equal(allowed.result.schema.tables.activation_codes,true);
  cases++;

  const redeem=await run({code:'TEST-CODE-123456789'},'user');
  assert.equal(redeem.status,200,'Activation de licence normale préservée');
  assert.equal(redeem.result.ok,true);
  assert.equal(redeem.calls.admin,0,'Ne pas imposer AAL2 à une activation ordinaire');
  assert.deepEqual(redeem.calls.rpcs.map(x=>x.name),
    ['sinjira_license_health','redeem_sinjira_activation']);
  cases++;

  const invalid=await run({code:'short'},'user');
  assert.equal(invalid.status,400);
  assert.equal(invalid.calls.admin,0);
  assert.ok(!invalid.calls.rpcs.some(x=>x.name==='redeem_sinjira_activation'));
  cases++;

  const big=await run({action:'health',padding:'x'.repeat(5000)},'admin-aal2');
  assert.equal(big.status,413,'Limiter le corps avant de consulter les privilèges');
  assert.equal(big.calls.admin,0);
  assert.equal(big.calls.service,0);
  cases++;

  const unavailable=await run({action:'health'},'admin-aal2',{noPepper:true});
  assert.equal(unavailable.status,503);
  assert.equal(unavailable.calls.service,0);
  cases++;

  for(const method of ['GET','OPTIONS']){
    const x=await run(null,'user',{method});
    assert.equal(x.status,method==='GET'?405:200);
    assert.equal(x.calls.auth,0);
    assert.equal(x.calls.service,0);
    cases++;
  }
  console.log('PASS: '+cases+
    ' parcours Edge réels (JWT, admin AAL2, MFA indisponible, activation, JSON borné, méthodes).');
}
main().catch(e=>{console.error('FAIL: vérification du diagnostic des licences',e);process.exitCode=1;});
