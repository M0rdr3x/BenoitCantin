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
  '\nglobalThis.gates={authenticatedContext,assuranceLevel,assertAdminMfa};';
const validAal={currentLevel:'aal2',nextLevel:'aal2'};
function harness({admin=true,aal=validAal,user={id:'test-user'},authError=null,adminError=null,aalError=null}={}){
  let assuranceCalls=0;
  const service={rpc:async()=>({data:admin,error:adminError}),
    auth:{getUser:async()=>({data:user===null?null:{user},error:authError}),
      mfa:{getAuthenticatorAssuranceLevel:async()=>{assuranceCalls++;return {data:aal,error:aalError}}}}};
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
  console.log('PASS: 25 scénarios serveur Auth, Admin et AAL.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
