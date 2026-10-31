'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const code=fs.readFileSync(path.join(__dirname,'..','assets/js/sinjira-auth-pages.js'),'utf8');
const start=code.indexOf('async function login(){');
const end=code.indexOf('\nasync function forgot(){',start);
assert.ok(start>=0&&end>start,'Fonction login non trouvée');
const loginFunction=code.slice(start,end);
assert.match(loginFunction,/let authenticated=false;/);
assert.match(loginFunction,/authenticated=true;/);
assert.match(loginFunction,/if\(authenticated\)\{[\s\S]*auth\.signOut\(\{scope:'local'\}\)/);
assert.doesNotMatch(loginFunction,/console\.warn\('\[SINJIRA auth login\]',err\)/);

async function scenario({outcome='challenge',mfaThrows=true,signInThrows=false}={}){
  const actions=[];
  let handler;
  const form={addEventListener:(type,fn)=>{assert.equal(type,'submit');handler=fn;}};
  const client={auth:{
    signInWithPassword:async()=>{
      actions.push('password');
      if(signInThrows)throw new Error('AUTH_NETWORK_DOWN');
      return {error:null};
    },
    signOut:async({scope})=>{actions.push('signOut:'+scope);return {error:null};},
    mfa:{getAuthenticatorAssuranceLevel:async()=>{
      actions.push('mfa');
      if(mfaThrows)throw new Error('MFA_NETWORK_DOWN');
      return {data:{nextLevel:'aal1'},error:null};
    }}
  }};
  const page={document:{querySelector:()=>form},getCurrentUser:async()=>null,
    destination:()=>'/compte/index.html',reportInvalid:()=>false,ready:()=>true,
    status:{},FormData:class{get(key){return key==='email'?'test@example.invalid':'not-a-real-password';}},
    setBusy:(_form,busy)=>actions.push('busy:'+busy),
    clearPendingChallenge:()=>actions.push('clearChallenge'),
    getSupabase:()=>client,
    evaluateLoginSecurity:async()=>({security:{outcome,challenge_id:'11111111-1111-4111-8111-111111111111'}}),
    setStatus:(_el,_message,_type)=>actions.push('errorShown'),
    storePendingChallenge:()=>actions.push('storeChallenge'),
    location:{replace:()=>{actions.push('navigated');}},
    console:{warn:()=>actions.push('logRedacted')},
    };
  const login=vm.runInNewContext('(function(){'+loginFunction+'\nreturn login;})()',page);
  await login();
  assert.equal(typeof handler,'function');
  await handler({preventDefault:()=>{}});
  return actions;
}
test('erreur inattendue du service MFA : session locale effacée, aucune navigation',async()=>{
  const events=await scenario();
  assert.ok(events.includes('password'));
  assert.ok(events.includes('mfa'));
  assert.equal(events.filter(x=>x==='signOut:local').length,1);
  assert.ok(events.includes('errorShown'));
  assert.ok(events.includes('logRedacted'));
  assert.ok(!events.includes('navigated'));
  assert.ok(!events.includes('storeChallenge'));
});
test('MFA négatif sans exception : session locale effacée',async()=>{
  const events=await scenario({mfaThrows:false});
  assert.equal(events.filter(x=>x==='signOut:local').length,1);
  assert.ok(!events.includes('navigated'));
});
test('échec avant connexion : pas de clôture d’une autre session',async()=>{
  const events=await scenario({signInThrows:true});
  assert.ok(!events.includes('signOut:local'));
  assert.ok(!events.includes('navigated'));
});
