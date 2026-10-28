'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'..','assets/js/sinjira-mfa-v24-4-66.js'),'utf8');
function extract(startMarker,endMarker){
  const start=source.indexOf(startMarker),end=source.indexOf(endMarker,start+startMarker.length);
  assert.ok(start>=0&&end>start,'Bloc MFA de production introuvable');
  return source.slice(start,end);
}
const helper=extract('async function failMfaUnavailable() {','\nasync function init(){');
test('panne MFA : session locale fermée, défi effacé et formulaire masqué',async()=>{
  const events=[],form={hidden:false};
  const failure=vm.runInNewContext('(function(){'+helper+'\nreturn failMfaUnavailable;})()',{
    s:{auth:{signOut:async({scope})=>{events.push('signOut:'+scope);return {error:null};}}},
    clearPendingSecurityChallenge:()=>events.push('cleared'),
    form,status:{},setStatus:(_status,message,kind)=>events.push(kind+':'+message)
  });
  await failure();
  assert.deepEqual(Array.from(events.slice(0,2)),['cleared','signOut:local']);
  assert.equal(form.hidden,true);
  assert.ok(events.some(x=>x.startsWith('error:')));
});
test('exception MFA de l’initialisation : passer par le nettoyage sécurisé',async()=>{
  const tail=source.slice(source.lastIndexOf('init().catch('));
  assert.match(tail,/init\(\)\.catch\(async \(\)=>\{/);
  const events=[];
  await vm.runInNewContext('(async()=>{'+tail.replace(/^init\(\)\.catch\(/,'await init().catch(')+'\n})()',{
    init:async()=>{throw new Error('MFA_INIT_FAILED');},
    console:{warn:(_tag,message)=>events.push(message)},
    failMfaUnavailable:async()=>events.push('cleaned')
  });
  assert.ok(events.includes('MFA_INIT_FAILED'));
  assert.ok(events.includes('cleaned'));
});
test('exception TOTP : nettoyage, pas de navigation',async()=>{
  const handler=extract("  form.addEventListener('submit',async event=>{", '\n  });\n}');
  const events=[],button={disabled:false};
  let onSubmit;
  const form={querySelector:()=>button,addEventListener:(_evt,fn)=>{onSubmit=fn;}};
  const page={
    form,FormData:class{get(){return '123456';}},
    factorSelect:{value:'factor-1'},status:{},setStatus:()=>events.push('errorShown'),
    s:{auth:{mfa:{challengeAndVerify:async()=>{throw new Error('TOTP_NETWORK_DOWN');}}}},
    failMfaUnavailable:async()=>events.push('cleaned'),
    securityFlow:true,location:{replace:()=>events.push('navigated')}
  };
  vm.runInNewContext(handler,page);
  assert.equal(typeof onSubmit,'function');
  await onSubmit({preventDefault:()=>{}});
  assert.ok(events.includes('cleaned'));
  assert.ok(!events.includes('navigated'));
});
test('erreur de code TOTP ordinaire : permettre une nouvelle saisie',async()=>{
  const handler=extract("  form.addEventListener('submit',async event=>{", '\n  });\n}');
  let cb;const events=[],button={disabled:false};
  const sandbox={
    form:{querySelector:()=>button,addEventListener:(_type,fn)=>{cb=fn;}},
    FormData:class{get(){return '987654';}},factorSelect:{value:'totp'},status:{},
    setStatus:()=>events.push('invalidCode'),
    s:{auth:{mfa:{challengeAndVerify:async()=>({error:new Error('INVALID_CODE')})}}},
    failMfaUnavailable:async()=>events.push('cleanup'),
    securityFlow:true
  };
  vm.runInNewContext(handler,sandbox);
  await cb({preventDefault:()=>{}});
  assert.equal(button.disabled,false);
  assert.deepEqual(events,['invalidCode']);
});
