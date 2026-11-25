'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../supabase/functions/_shared/auth.ts'),'utf8');
function extract(name,next){
  const start=source.indexOf('async function '+name+'(');
  const end=source.indexOf('\nasync function '+next+'(',start);
  assert.ok(start>=0&&end>start,name+' introuvable');
  return source.slice(start,end)
    .replace('req: Request','req')
    .replace('context: Awaited<ReturnType<typeof authenticatedContext>>','context');
}
const code=extract('authenticatedContext','assuranceLevel')+
  extract('assuranceLevel','assertAdminMfa')+
  extract('assertAdminMfa','sensitiveStepUpEnabled')+
  extract('sensitiveStepUpEnabled','assertSensitiveMfa')+
  extract('assertSensitiveMfa','assertVaultMfa')+
  '\nglobalThis.gates={authenticatedContext,assuranceLevel,assertAdminMfa,assertSensitiveMfa};';
const validAal={currentLevel:'aal2',nextLevel:'aal2'};
function harness({admin=true,aal=validAal,user={id:'test-user'},authError=null,adminError=null,aalError=null,settings={data:null,error:null},responses={}}={}){
  let assuranceCalls=0;
  const response=(name,fallback)=>Object.hasOwn(responses,name)?responses[name]:fallback;
  const service={rpc:async()=>response('admin',{data:admin,error:adminError}),
    from(table){assert.equal(table,'security_user_settings');return {
      select(columns){assert.equal(columns,'user_id,sensitive_step_up');return {
        eq(column,value){assert.equal(column,'user_id');assert.equal(value,'test-user');return {
          maybeSingle:async()=>settings
        };}
      };}
    };},
    auth:{getUser:async()=>response('auth',{data:user===null?null:{user},error:authError}),
      mfa:{getAuthenticatorAssuranceLevel:async()=>{assuranceCalls++;return response('aal',{data:aal,error:aalError})}}}};
  const sandbox={serviceClient:()=>service,bearerToken:()=> 'synthetic-token',console:{error(){}}};
  vm.runInNewContext(code,sandbox,{timeout:1000});
  return {gates:sandbox.gates,context:{user:{id:'test-user'},service,token:'synthetic-token'},calls:()=>assuranceCalls};
}
async function main(){
  for(const admin of [false,null,0,1,'false','true',[],{},[true]]){
    const h=harness({admin});
    await assert.rejects(h.gates.assertAdminMfa(h.context),/ADMIN_REQUIRED/);
    assert.equal(h.calls(),0);
  }
  const adminError=harness({adminError:{message:'unavailable'}});
  await assert.rejects(adminError.gates.assertAdminMfa(adminError.context),/ADMIN_REQUIRED/);
  for(const aal of [null,{}, {currentLevel:'aal2'}, {nextLevel:'aal2'},
    {currentLevel:'aal3',nextLevel:'aal2'}, {currentLevel:'aal2',nextLevel:null}]){
    const h=harness({aal});
    await assert.rejects(h.gates.assertAdminMfa(h.context),/MFA_STATE_UNAVAILABLE/);
  }
  const error=harness({aalError:{message:'unavailable'}});
  await assert.rejects(error.gates.assertAdminMfa(error.context),/MFA_STATE_UNAVAILABLE/);
  for(const [aal,expected] of [
    [{currentLevel:'aal1',nextLevel:'aal1'},'MFA_SETUP_REQUIRED'],
    [{currentLevel:'aal1',nextLevel:'aal2'},'MFA_REQUIRED']
  ]){
    const h=harness({aal});
    await assert.rejects(h.gates.assertAdminMfa(h.context),new RegExp(expected));
  }
  const allowed=harness();
  assert.equal((await allowed.gates.assertAdminMfa(allowed.context)).currentLevel,'aal2');
  for(const user of [null,{}, {id:''},{id:1}]){
    const h=harness({user});
    await assert.rejects(h.gates.authenticatedContext({}),/AUTH_REQUIRED/);
  }
  assert.equal((await allowed.gates.authenticatedContext({})).user.id,'test-user');
  // Aucun résultat ambigu ne peut désactiver le MFA facultatif.
  const own={user_id:'test-user'};
  for(const data of [undefined, false, [], {}, {sensitive_step_up:false},
    {user_id:'other-user',sensitive_step_up:false},
    {...own,sensitive_step_up:'false'}, {...own,sensitive_step_up:0},
    {...own,sensitive_step_up:null}, {...own}]){
    const h=harness({settings:{data,error:null}});
    await assert.rejects(h.gates.assertSensitiveMfa(h.context),/SECURITY_STATE_UNAVAILABLE/);
    assert.equal(h.calls(),0);
  }
  const outage=harness({settings:{data:{...own,sensitive_step_up:false},error:{message:'unavailable'}}});
  await assert.rejects(outage.gates.assertSensitiveMfa(outage.context),/SECURITY_STATE_UNAVAILABLE/);
  assert.equal(outage.calls(),0);
  for(const data of [null,{...own,sensitive_step_up:true}]){
    const h=harness({settings:{data,error:null},aal:{currentLevel:'aal1',nextLevel:'aal2'}});
    await assert.rejects(h.gates.assertSensitiveMfa(h.context),/MFA_REQUIRED/);
    assert.equal(h.calls(),1);
    const allowed=harness({settings:{data,error:null}});
    assert.equal((await allowed.gates.assertSensitiveMfa(allowed.context)).currentLevel,'aal2');
    assert.equal(allowed.calls(),1);
  }
  const optedOut=harness({settings:{data:{...own,sensitive_step_up:false},error:null}});
  assert.equal(await optedOut.gates.assertSensitiveMfa(optedOut.context),null);
  assert.equal(optedOut.calls(),0);
  // Une réponse du SDK doit confirmer explicitement l'absence d'erreur.
  const goodUser={id:'test-user'};
  const invalidAuth=[null,undefined,{}, {data:{user:goodUser}},
    {data:{user:goodUser},error:false},{data:{user:goodUser},error:0},
    {data:{user:{id:' '}},error:null},{data:{user:{id:' test-user'}},error:null},
    {data:{user:Object.assign([],{id:'test-user'})},error:null},
    {data:Object.assign([],{user:goodUser}),error:null}];
  for(const auth of invalidAuth){
    const h=harness({responses:{auth}});
    await assert.rejects(h.gates.authenticatedContext({}),/AUTH_REQUIRED/);
  }
  const invalidAdmin=[null,undefined,{}, {data:true},{data:true,error:false},{data:true,error:0}];
  for(const admin of invalidAdmin){
    const h=harness({responses:{admin}});
    await assert.rejects(h.gates.assertAdminMfa(h.context),/ADMIN_REQUIRED/);
    assert.equal(h.calls(),0);
  }
  const invalidAal=[null,undefined,{}, {data:validAal},{data:validAal,error:false},
    {data:validAal,error:0},{data:{currentLevel:'aal2',nextLevel:'aal1'},error:null},
    {data:Object.assign([] ,validAal),error:null}];
  for(const aal of invalidAal){
    const h=harness({responses:{aal}});
    await assert.rejects(h.gates.assuranceLevel(h.context),/MFA_STATE_UNAVAILABLE/);
  }
  for(const settings of [{data:{...own,sensitive_step_up:false}},
    {data:{...own,sensitive_step_up:false},error:false},
    {data:{...own,sensitive_step_up:false},error:0}]){
    const h=harness({settings});
    await assert.rejects(h.gates.assertSensitiveMfa(h.context),/SECURITY_STATE_UNAVAILABLE/);
    assert.equal(h.calls(),0);
  }
  console.log('PASS: 41 scénarios existants et 27 nouveaux refus Auth/Admin/AAL/préférences.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
