#!/usr/bin/env node
'use strict';
// Tests des vraies fonctions JS Auth et Centre de sécurité, sans réseau ni compte.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

const ROOT=path.resolve(__dirname,'..');
const auth=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-auth-pages.js'),'utf8');
const center=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-security-center-v24-4-98.js'),'utf8');
const SECRET='session=eyJhbGciOiJIUzI1NiJ9.privatefake.sig; email=private@example.invalid; SELECT * FROM auth.sessions';
let checks=0;

function section(source,start,end){
  const first=source.indexOf(start);
  const last=source.indexOf(end,first+start.length);
  assert.ok(first>=0&&last>first,'Fonction de sécurité absente: '+start);
  return source.slice(first,last);
}
function checkSafe(value,label){
  assert.ok(!String(value).includes(SECRET),label+': diagnostic de session divulgué');
  assert.ok(!String(value).includes('private@example.invalid'),label+': courriel privé divulgué');
  assert.ok(!String(value).includes('auth.sessions'),label+': catalogue SQL divulgué');
  checks+=3;
}
function verifyStaticConsole(source,label){
  const calls=[...source.matchAll(/\bconsole\.(?:warn|error|log)\s*\(([^)]*)\)/g)];
  assert.ok(calls.length>0,label+': contrôle de console non exécuté');
  for(const match of calls){
    const args=match[1].trim();
    assert.match(args,/^'(?:[^'\\]|\\.)*'$|^"(?:[^"\\]|\\.)*"$/,label+': argument dynamique de console interdit: '+args.slice(0,70));
    checks++;
  }
}
verifyStaticConsole(auth,'Auth');
verifyStaticConsole(center,'Centre sécurité');

const safeCode=section(center,'function friendlySecurityError(error){','\nasync function boot(){');
const csp=vm.createContext({});
vm.runInContext(safeCode+'\nglobalThis.getSafeError=friendlySecurityError;',csp,{timeout:1500});
const safe=csp.getSafeError;
for(const value of [
  new Error(SECRET),new Error('Internal exception'),
  new Error('<img src=x onerror=alert(1)>'),
  new Error('token=fictional'),new Error('SQLSTATE: private.account'),
  {message:SECRET},Object.create(null),null,
]){
  const output=safe(value);
  assert.equal(output,'Le Centre de sécurité ne peut pas terminer cette opération. Réessayez ou reconnectez-vous.');
  checkSafe(output,'Erreur RPC inconnue');
}
for(const [input,expected] of [
  ['TRUST_CONFIRMATION_REQUIRED '+SECRET,'Cet appareil doit d’abord être autorisé depuis un autre appareil déjà fiable.'],
  ['CURRENT_DEVICE_REQUIRED '+SECRET,'Seul l’appareil que vous utilisez actuellement peut être marqué comme fiable.'],
  ['AAL2_REQUIRED '+SECRET,'Une vérification MFA récente est requise pour modifier la confiance des appareils.'],
  ['AUTH_SESSION_INVALID '+SECRET,'Votre session de sécurité n’est plus valide. Reconnectez-vous.'],
  ['SESSION_REVOKED '+SECRET,'Votre session de sécurité n’est plus valide. Reconnectez-vous.'],
  ['SECURE_RANDOM_UNAVAILABLE '+SECRET,'La protection cryptographique de ce navigateur est indisponible. Utilisez un navigateur à jour.'],
  ['Indiquez une période et au moins une destination approximative.','Indiquez une période et au moins une destination approximative.'],
]){
  const output=safe(new Error(input));
  assert.equal(output,expected);
  checkSafe(output,'Code d’erreur reconnu');
}

async function contextError(){
  const logs=[];
  const code=section(center,'async function registerContext(meta){','\nfunction renderOverview(');
  const sandbox={
    rpc:async()=>({ok:true}),
    getSupabase:()=>({functions:{invoke:async()=>({data:null,error:new Error(SECRET)})}}),
    console:{warn(...args){logs.push(args);}},
  };
  vm.runInNewContext(code+'\nglobalThis.runRegisterContext=registerContext;',sandbox,{timeout:1500});
  const response=await sandbox.runRegisterContext({
    device_key:'device-example',display_name:'Test',device_type:'browser',platform:'Test'
  });
  assert.equal(response.context,null,'Échec du contexte doit rester une erreur');
  assert.equal(logs.length,1);
  for(const args of logs)for(const item of args)checkSafe(item,'Journal security-context');
}
function makeForm(){
  let listener;
  const form={
    addEventListener(name,fn){if(name==='submit')listener=fn;},
    querySelector(){return {disabled:false};},
    querySelectorAll(){return [];},
    setAttribute(){},reset(){},
  };
  return {form,submit:async()=>{assert.equal(typeof listener,'function','Gestionnaire submit absent');await listener({preventDefault(){}});}};
}
async function authScenario(name,scenario){
  const logs=[],shown=[],redirects=[];
  const form=makeForm();
  const authApi={
    getUser:async()=>({data:{user:{id:'fictional'}},error:null}),
    signInWithPassword:async()=>{throw new Error(SECRET);},
    resetPasswordForEmail:async()=>{
      if(scenario==='throw')throw new Error(SECRET);
      return {error:new Error(SECRET)};
    },
    updateUser:async()=>{throw new Error(SECRET);},
  };
  const context={
    document:{querySelector:()=>form.form},
    getCurrentUser:async()=>null,
    destination:()=>'/compte/index.html',
    ready:()=>true,reportInvalid:()=>false,
    setBusy:()=>{},clearPendingChallenge:()=>{},
    FormData:class{get(key){return key==='email'?'sample@example.invalid':'a-valid-fictional-password-1234';}},
    getSupabase:()=>({auth:authApi}),
    status:{},
    setStatus(_node,message){shown.push(message);},
    SINJIRA_CONFIG:{siteUrl:'https://www.benoitcantin.com'},
    location:{replace(value){redirects.push(value);}},
    console:{warn(...args){logs.push(args);}},
  };
  const next=name==='login'?'\nasync function forgot()':
    name==='forgot'?'\nasync function reset()':'\nready();\ntry{';
  const block=section(auth,'async function '+name+'(){',next);
  vm.runInNewContext(block+'\nglobalThis.runAuthFlow='+name+';',context,{timeout:1500});
  await context.runAuthFlow();
  await form.submit();
  assert.equal(redirects.length,0,name+': redirection inattendue après erreur');
  assert.ok(logs.length>=1,name+': aucune observation de la branche d’erreur');
  assert.ok(shown.length>=1,name+': absence de message utilisateur');
  for(const args of logs)for(const item of args)checkSafe(item,name+' : journal navigateur');
  for(const message of shown)checkSafe(message,name+' : message utilisateur');
}
async function storageError(){
  const logs=[];
  const block=section(auth,'function storePendingChallenge(challengeId,next){','\nfunction clearPendingChallenge(){');
  const context={
    PENDING_CHALLENGE_STORAGE:'challenge',PENDING_DESTINATION_STORAGE:'destination',
    sessionStorage:{setItem(){throw new Error(SECRET);}},
    console:{warn(...args){logs.push(args);}},
  };
  vm.runInNewContext(block+'\nglobalThis.testStore=storePendingChallenge;',context,{timeout:1500});
  context.testStore('fictional-challenge','/compte/');
  assert.equal(logs.length,1);
  for(const args of logs)for(const item of args)checkSafe(item,'Journal stockage session');
}
async function bootError(){
  const logs=[],shown=[];
  const block=section(center,'async function boot(){','\nboot();');
  const context={
    deviceMetadata:()=>({device_key:'fictional'}),
    requireUser:async()=>{throw new Error(SECRET);},
    status:msg=>shown.push(msg),
    console:{error(...args){logs.push(args);}},
    friendlySecurityError:safe,
  };
  vm.runInNewContext(block+'\nglobalThis.testBoot=boot;',context,{timeout:1500});
  await context.testBoot();
  assert.equal(logs.length,1);
  for(const args of logs)for(const item of args)checkSafe(item,'Journal erreur Centre de sécurité');
  assert.equal(shown.at(-1),'Le Centre de sécurité ne peut pas terminer cette opération. Réessayez ou reconnectez-vous.');
}

function testHtmlAttributeInjection(){
  // Les valeurs de RPC traversent un rendu innerHTML. Test sur les vraies
  // fonctions, avec la vraie fonction escapeHtml du module partagé.
  const common=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-supabase.js'),'utf8');
  const actualEscape=section(common,'export function escapeHtml(','\nexport function formatDate(').replace('export function','function');
  const injectedId='id" autofocus onfocus="alert(1)';
  const blocks=[
    section(center,'function renderDevices(devices){','\nfunction renderSessions('),
    section(center,'function renderTravel(rows){','\nfunction renderChallenges('),
    section(center,'function renderChallenges(rows,devices){','\nfunction fillSettings('),
  ].join('\n');
  const node={innerHTML:''};
  const sandbox={
    qs:()=>node, Date,
    pill:()=>'<span>État</span>',
    empty:()=>'<p>Vide</p>',
    formatDate:()=>'date',
  };
  vm.runInNewContext(actualEscape+'\n'+blocks+
    '\nglobalThis.renderers={renderDevices,renderTravel,renderChallenges,escapeHtml};',
    sandbox,{timeout:1500});
  const {renderDevices,renderTravel,renderChallenges,escapeHtml}=sandbox.renderers;
  const expected=escapeHtml(injectedId);
  assert.ok(expected.includes('&quot;'),'Garde d’échappement des guillemets indisponible');

  const data={
    id:injectedId,
    display_name:'Appareil de test',
    last_seen_at:'2026-11-20T00:00:00Z',
    device_type:'browser',platform:'test',revoked_at:null,
    is_primary:false,
  };
  renderDevices([
    {...data,is_current:true,is_trusted:false},
    {...data,is_current:false,is_trusted:true},
  ]);
  for(const attr of ['data-device-id','data-device-trust','data-device-primary',
                     'data-device-untrust','data-device-revoke']){
    assert.ok(node.innerHTML.includes(attr+'="'+expected+'"'),
      'ID non échappé dans l’attribut '+attr);
    assert.ok(!node.innerHTML.includes(attr+'="'+injectedId+'"'),
      'Injection de guillemet dans '+attr);
    checks+=2;
  }
  renderTravel([{
    id:injectedId,status:'active',destinations:['Test'],
    starts_at:'2026-11-20',ends_at:'2026-11-21',delete_after:'2026-11-22',
  }]);
  assert.ok(node.innerHTML.includes('data-travel-cancel="'+expected+'"'),
    'ID de voyage non échappé');
  checks++;

  renderChallenges([{
    id:injectedId,status:'pending',expires_at:'2099-01-01T00:00:00Z',
    request_device_id:'other',display_code:'TEST-CODE',
  }],[{id:'device-current',is_current:true,is_trusted:true,revoked_at:null}]);
  for(const attr of ['data-challenge-approve','data-challenge-deny']){
    assert.ok(node.innerHTML.includes(attr+'="'+expected+'"'),
      'ID de challenge non échappé pour '+attr);
    assert.ok(!node.innerHTML.includes(attr+'="'+injectedId+'"'));
    checks+=2;
  }
  assert.ok(!node.innerHTML.includes('onfocus="alert(1)"'),
    'Attribut événementiel injecté dans un bouton de confirmation');
  checks++;
}

(async()=>{
  testHtmlAttributeInjection();
  await contextError();
  await authScenario('login','throw');
  await authScenario('forgot','return');
  await authScenario('forgot','throw');
  await authScenario('reset','throw');
  await storageError();
  await bootError();
  console.log('PASS: '+checks+' vérifications des erreurs Auth/RPC, messages privés et journaux sans réseau.');
})().catch(error=>{console.error(error);process.exitCode=1;});
