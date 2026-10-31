'use strict';
// Regression des fonctions reelles, sans appel Supabase et sans donnees utilisateur.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const auth = fs.readFileSync(path.join(root, 'assets/js/sinjira-auth-pages.js'), 'utf8');
const center = fs.readFileSync(path.join(root, 'assets/js/sinjira-security-center-v24-4-98.js'), 'utf8');
let checks = 0;

function section(source, begin, end) {
  const i = source.indexOf(begin);
  const j = source.indexOf(end, i + begin.length);
  assert.ok(i >= 0 && j > i, 'Section de securite introuvable: ' + begin);
  return source.slice(i, j);
}
function storage(seed) {
  const state = new Map(seed || []);
  return {
    getItem: key => state.get(key) || null,
    setItem: (key, value) => state.set(key, String(value)),
    removeItem: key => state.delete(key),
  };
}
function runKeyTests(source, keyFnName, nextName) {
  const code = section(source, 'function randomDeviceKey(){', '\nfunction '+nextName+'(){');
  const sandbox = {Uint8Array, Date, localStorage:storage(), sessionStorage:storage()};
  vm.runInNewContext(code + '\nglobalThis.keys = {randomDeviceKey, unusableDeviceKey, '+keyFnName+'};', sandbox, {timeout:2000});
  const tests = sandbox.keys;
  const exampleUuid='e765f89d-bca1-4e11-9ef7-cc9511a4af11';

  assert.throws(() => tests.randomDeviceKey(), /SECURE_RANDOM_UNAVAILABLE/);
  checks++;
  sandbox.crypto = {getRandomValues: arr => arr};
  assert.throws(() => tests.randomDeviceKey(), /SECURE_RANDOM_UNAVAILABLE/);
  checks++;
  sandbox.crypto = {getRandomValues: arr => {for(let i=0;i<arr.length;i++)arr[i]=i+1;return arr;}};
  assert.match(tests.randomDeviceKey(), /^sinjira-[0-9a-f]{48}-[0-9a-z]+$/);
  checks++;
  sandbox.crypto = {randomUUID: () => exampleUuid};
  assert.equal(tests.randomDeviceKey(), exampleUuid);
  checks++;
  assert.equal(tests.unusableDeviceKey('sinjira-'+'0'.repeat(48)+'-m0'), true);
  checks++;
  assert.equal(tests.unusableDeviceKey(exampleUuid), false);
  checks++;
  assert.equal(tests.unusableDeviceKey('tiny'), true);
  checks++;
  sandbox.localStorage.setItem('sinjira.security.device_key.v1','sinjira-'+'0'.repeat(48)+'-legacy');
  assert.equal(tests[keyFnName](),exampleUuid,'Cle previsible historique non remplacee.');
  checks++;
  assert.equal(sandbox.localStorage.getItem('sinjira.security.device_key.v1'),exampleUuid);
  checks++;
  assert.equal(tests[keyFnName](),exampleUuid,'Cle forte persistante modifiee sans raison.');
  checks++;
  sandbox.localStorage=storage();
  sandbox.sessionStorage=storage();
  delete sandbox.crypto;
  assert.throws(() => tests[keyFnName](), /SECURE_RANDOM_UNAVAILABLE/,
    'Une nouvelle cle ne doit jamais etre fabriquee sans crypto');
  checks++;
}

runKeyTests(auth, 'securityDeviceKey', 'securityDeviceMetadata');
runKeyTests(center, 'deviceKey', 'deviceMetadata');

const loginSource = section(auth, 'async function login(){', '\nasync function forgot(){');

async function loginScenario({evaluation,signInError=false,aal='aal1',logoutError=false}={}) {
  const actions = [];
  let callback = null;
  const form = {
    addEventListener: (_name,cb) => {callback=cb;},
    querySelector: () => ({disabled:false}),
    setAttribute: () => {},
  };
  const supabase = {
    auth:{
      signInWithPassword:async()=>({error:signInError?new Error('test'):null}),
      signOut:async()=>{actions.push('signout');return logoutError?{error:new Error('logout blocked')}:{error:null};},
      mfa:{getAuthenticatorAssuranceLevel:async()=>({data:{nextLevel:aal},error:null})}
    }
  };
  const sandbox = {
    document:{querySelector:()=>form},
    getCurrentUser:async()=>null,
    destination:()=>'/compte/index.html',
    reportInvalid:()=>false,
    ready:()=>true,
    FormData:function(){return {get:key=>key==='email'?'test@example.org':'fictional-password'};},
    setBusy:()=>{},
    clearPendingChallenge:()=>{},
    getSupabase:()=>supabase,
    evaluateLoginSecurity:async()=> {
      if(evaluation instanceof Error)throw evaluation;
      return {meta:{},security:evaluation};
    },
    setStatus:(_node,_msg,kind)=>actions.push('status:'+kind),
    storePendingChallenge:()=>actions.push('pending'),
    status:{},
    location:{replace:url=>actions.push('redirect:'+url)},
    console:{warn:()=>{}},
  };
  vm.runInNewContext(loginSource+'\nglobalThis.realLogin=login;',sandbox,{timeout:2000});
  await sandbox.realLogin();
  assert.equal(typeof callback,'function','Le parcours de login a change.');
  await callback({preventDefault(){}});
  return actions;
}

(async()=>{
  for(const failure of [
    new Error('SECURITY_CONTEXT_UNAVAILABLE'),
    new Error('SECURE_RANDOM_UNAVAILABLE'),
    new Error('HTTP 503'),
  ]){
    const actions=await loginScenario({evaluation:failure});
    assert.ok(actions.includes('signout'),'Panne security-context non deconnectee.');
    assert.ok(actions.includes('status:error'),'Panne security-context non signalee.');
    assert.ok(!actions.some(a=>a.startsWith('redirect:')),'Panne security-context redirigee.');
    checks+=3;
  }
  for(const outcome of [undefined,{}, {outcome:'approved'}, {outcome:'disabled'}, {outcome:''}]){
    const actions=await loginScenario({evaluation:outcome});
    assert.ok(actions.includes('signout'),'Reponse securite inconnue non deconnectee.');
    assert.ok(!actions.some(a=>a.startsWith('redirect:')),'Reponse inconnue autorisee.');
    checks+=2;
  }
  const safe=await loginScenario({evaluation:{outcome:'allow'}});
  assert.ok(safe.includes('redirect:/compte/index.html'));
  assert.ok(!safe.includes('signout'));
  checks+=2;
  const deny=await loginScenario({evaluation:{outcome:'block'}});
  assert.ok(deny.includes('signout'));
  assert.ok(!deny.some(a=>a.startsWith('redirect:')));
  checks+=2;
  const missing=await loginScenario({evaluation:{outcome:'challenge'}});
  assert.ok(missing.includes('signout'));
  assert.ok(!missing.some(a=>a.startsWith('redirect:')));
  checks+=2;
  const challenge=await loginScenario({evaluation:{outcome:'challenge',challenge_id:'fictional-id'},aal:'aal2'});
  assert.ok(challenge.includes('pending'));
  assert.ok(challenge.some(a=>a.startsWith('redirect:/compte/mfa.html?security=1&next=')));
  checks+=2;
  const weak=await loginScenario({evaluation:{outcome:'challenge',challenge_id:'fictional-id'},aal:'aal1'});
  assert.ok(weak.includes('signout'));
  assert.ok(!weak.some(a=>a.startsWith('redirect:')));
  checks+=2;
  const error=await loginScenario({signInError:true});
  assert.ok(!error.some(a=>a.startsWith('redirect:')));
  checks++;
  const failLogout=await loginScenario({evaluation:new Error('HTTP 503'),logoutError:true});
  assert.ok(!failLogout.some(a=>a.startsWith('redirect:')),'Ne pas avancer si la fermeture de session renvoie une erreur.');
  checks++;
  console.log('PASS: '+checks+' assertions du parcours de connexion fail-closed et des identifiants cryptographiques.');
})().catch(error=>{console.error(error);process.exitCode=1;});
