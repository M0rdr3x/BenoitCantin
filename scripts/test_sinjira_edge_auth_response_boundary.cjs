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
  extract('assertVaultMfa','assertPersonalAiMfa')+
  source.slice(source.indexOf('async function assertPersonalAiMfa('),source.indexOf('\nexport async function optionalUser('))
    .replace('context: Awaited<ReturnType<typeof authenticatedContext>>','context')+
  '\nglobalThis.gates={authenticatedContext,assuranceLevel,assertAdminMfa,assertSensitiveMfa,assertVaultMfa,assertPersonalAiMfa};';
const validAal={currentLevel:'aal2',nextLevel:'aal2'};
function harness({admin=true,aal=validAal,user={id:'test-user'},authError=null,adminError=null,aalError=null,aalReject=false,authReject=false,adminReject=false,settingsReject=false,clientReject=false,omitAuthError=false,omitAdminError=false,omitAalError=false,settings={data:null,error:null}}={}){
  let assuranceCalls=0,settingsCalls=0;
  const service={rpc:async()=>{if(adminReject)throw new Error('synthetic private RPC detail');return {data:admin,...(omitAdminError?{}:{error:adminError})}},
    from(table){settingsCalls++;assert.equal(table,'security_user_settings');return {
      select(columns){assert.equal(columns,'user_id,sensitive_step_up');return {
        eq(column,value){assert.equal(column,'user_id');assert.equal(value,'test-user');return {
          maybeSingle:async()=>{if(settingsReject)throw new Error('synthetic private query detail');return settings}
        };}
      };}
    };},
    auth:{getUser:async()=>{if(authReject)throw new Error('synthetic private Auth detail');return {data:user===null?null:{user},...(omitAuthError?{}:{error:authError})}},
      mfa:{getAuthenticatorAssuranceLevel:async()=>{assuranceCalls++;if(aalReject)throw new Error('synthetic provider detail');return {data:aal,...(omitAalError?{}:{error:aalError})}}}}};
  const sandbox={serviceClient:()=>{if(clientReject)throw new Error('synthetic private configuration detail');return service},bearerToken:()=> 'synthetic-token',console:{error(){}}};
  vm.runInNewContext(code,sandbox,{timeout:1000});
  return {gates:sandbox.gates,context:{user:{id:'test-user'},service,token:'synthetic-token'},calls:()=>assuranceCalls,settingsCalls:()=>settingsCalls};
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
  // Une exception du fournisseur ne doit jamais franchir la frontière Auth.
  for(const gate of ['assuranceLevel','assertAdminMfa','assertSensitiveMfa','assertVaultMfa','assertPersonalAiMfa']){
    const h=harness({aalReject:true});
    await assert.rejects(h.gates[gate](h.context),{message:'MFA_STATE_UNAVAILABLE'});
    assert.equal(h.calls(),1);
  }
  // Les deux espaces privés restent soumis au MFA même avec une préférence désactivée.
  for(const gate of ['assertVaultMfa','assertPersonalAiMfa']){
    for(const [aal,expected] of [
      [null,'MFA_STATE_UNAVAILABLE'],
      [{currentLevel:'aal1',nextLevel:'aal1'},'MFA_SETUP_REQUIRED'],
      [{currentLevel:'aal1',nextLevel:'aal2'},'MFA_REQUIRED'],
      [{currentLevel:'aal2',nextLevel:'aal1'},'MFA_SETUP_REQUIRED']
    ]){
      const h=harness({aal,settings:{data:{...own,sensitive_step_up:false},error:null}});
      await assert.rejects(h.gates[gate](h.context),{message:expected});
      assert.equal(h.calls(),1);
      assert.equal(h.settingsCalls(),0);
    }
    const h=harness({settings:{data:{...own,sensitive_step_up:false},error:null}});
    assert.equal((await h.gates[gate](h.context)).currentLevel,'aal2');
    assert.equal(h.calls(),1);
    assert.equal(h.settingsCalls(),0);
  }
  // Les exceptions de configuration, transport et requête ne doivent pas sortir
  // de la frontière Auth, ni permettre une décision positive par défaut.
  for(const opts of [{authReject:true},{clientReject:true},{authError:{message:'synthetic private detail'}}]){
    const h=harness(opts);
    await assert.rejects(h.gates.authenticatedContext({}),{message:'AUTH_REQUIRED'});
    assert.equal(h.calls(),0);
  }
  const rejectedAdmin=harness({adminReject:true});
  await assert.rejects(rejectedAdmin.gates.assertAdminMfa(rejectedAdmin.context),{message:'ADMIN_REQUIRED'});
  assert.equal(rejectedAdmin.calls(),0);
  const rejectedSettings=harness({settingsReject:true});
  await assert.rejects(rejectedSettings.gates.assertSensitiveMfa(rejectedSettings.context),{message:'SECURITY_STATE_UNAVAILABLE'});
  assert.equal(rejectedSettings.calls(),0);
  assert.equal(rejectedSettings.settingsCalls(),1);
  // Seul error:null constitue le résultat explicite de succès du SDK.
  for(const invalid of [false,0,'']){
    const auth=harness({authError:invalid});
    await assert.rejects(auth.gates.authenticatedContext({}),{message:'AUTH_REQUIRED'});
    const admin=harness({adminError:invalid});
    await assert.rejects(admin.gates.assertAdminMfa(admin.context),{message:'ADMIN_REQUIRED'});
    assert.equal(admin.calls(),0);
    const mfa=harness({aalError:invalid});
    await assert.rejects(mfa.gates.assuranceLevel(mfa.context),{message:'MFA_STATE_UNAVAILABLE'});
    const pref=harness({settings:{data:{...own,sensitive_step_up:false},error:invalid}});
    await assert.rejects(pref.gates.assertSensitiveMfa(pref.context),{message:'SECURITY_STATE_UNAVAILABLE'});
    assert.equal(pref.calls(),0);
  }
  for(const [opts,gate,expected] of [
    [{omitAuthError:true},'authenticatedContext','AUTH_REQUIRED'],
    [{omitAdminError:true},'assertAdminMfa','ADMIN_REQUIRED'],
    [{omitAalError:true},'assuranceLevel','MFA_STATE_UNAVAILABLE'],
    [{settings:{data:{...own,sensitive_step_up:false}}},'assertSensitiveMfa','SECURITY_STATE_UNAVAILABLE'],
    [{user:{id:' '}},'authenticatedContext','AUTH_REQUIRED'],
    [{user:{id:' test-user '}},'authenticatedContext','AUTH_REQUIRED'],
    [{aal:Object.assign([],{currentLevel:'aal2',nextLevel:'aal2'})},'assuranceLevel','MFA_STATE_UNAVAILABLE']
  ]){
    const h=harness(opts);
    await assert.rejects(h.gates[gate](h.context),{message:expected});
  }
  console.log('PASS: Auth, Admin, AAL, préférence MFA, frontières privées et contrats SDK stricts.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
