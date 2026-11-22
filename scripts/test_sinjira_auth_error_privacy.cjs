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
const securityPage=fs.readFileSync(path.join(ROOT,'compte/securite.html'),'utf8');
assert.ok(
  securityPage.includes('sinjira-security-center-v24-4-98.js?v=24.5.2-compromise'),
  'Le module d’urgence doit être téléchargé avec sa nouvelle version de cache'
);
assert.ok(
  !securityPage.includes('sinjira-security-center-v24-4-98.js?v=24.5.1'),
  'Ancien module d’urgence encore accessible via le cache HTML'
);
checks+=2;

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


async function compromisedAccountScenario(name,opts={}){
  // Exécuter le VRAI gestionnaire du centre de sécurité avec des objets RPC
  // et Auth factices : aucune session, API ou requête réseau réelle.
  let listener=null,rpcCalls=0,authCalls=0,refreshCalls=0;
  const shown=[],sent=[];
  const button={
    disabled:false,
    addEventListener(type,fn){
      assert.equal(type,'click');
      listener=fn;
    },
  };
  const rpcOk={ok:true,revoked_devices:2,current_device_id:'fake'};
  const client={
    auth:{
      async signOut(args){
        authCalls++;
        sent.push(args);
        if(opts.authThrows)throw new Error(SECRET);
        return Object.hasOwn(opts,'authResult')?opts.authResult:{error:null};
      },
    },
  };
  const context={
    qs(selector){
      assert.equal(selector,'[data-security-compromised]');
      return button;
    },
    confirmAction:()=>opts.confirm!==false,
    meta:{device_key:'fake-device-key'},
    contextResult:{context:{geo_mode:'off'}},
    async rpc(name,args){
      rpcCalls++;
      assert.equal(name,'security_compromise_account');
      assert.equal(args.p_current_device_key,'fake-device-key');
      if(opts.rpcThrows)throw new Error(SECRET);
      return Object.hasOwn(opts,'rpcResult')?opts.rpcResult:rpcOk;
    },
    getSupabase:()=>client,
    async loadState(){
      refreshCalls++;
      if(opts.refreshThrows)throw new Error(SECRET);
      return {ready:true};
    },
    status(message,type='info'){shown.push({message,type});},
    friendlySecurityError:safe,
    state:null,
  };
  const handler=section(
    center,
    "    qs('[data-security-compromised]')?.addEventListener('click',async event=>{",
    "\n\n    document.addEventListener('click',async e=>{"
  );
  vm.runInNewContext(handler,context,{timeout:1500});
  assert.equal(typeof listener,'function',name+': gestionnaire d’urgence absent');
  await listener({currentTarget:button});
  for(const entry of shown)checkSafe(entry.message,name+': message utilisateur');
  const successes=shown.filter(item=>item.type==='success');
  if(opts.confirm===false){
    assert.equal(rpcCalls,0,name+': aucun appel après refus');
    assert.equal(authCalls,0,name+': aucun Auth après refus');
    assert.equal(shown.length,0,name+': aucun message de succès après refus');
    assert.equal(button.disabled,false);
  }else if(opts.rpcFailure){
    assert.equal(rpcCalls,1,name+': une RPC d’urgence');
    assert.equal(authCalls,0,name+': aucune révocation Auth si la RPC n’est pas confirmée');
    assert.equal(refreshCalls,0,name+': aucun refresh après RPC non confirmée');
    assert.equal(successes.length,0,name+': fausse confirmation de sécurité');
    assert.ok(shown.some(item=>item.type==='error'),name+': erreur non affichée');
    assert.equal(button.disabled,false,name+': utilisateur peut réessayer');
  }else if(opts.authFailure){
    assert.equal(rpcCalls,1);
    assert.equal(authCalls,1);
    assert.equal(sent[0].scope,'others');
    assert.equal(refreshCalls,0,name+': ne pas actualiser après signOut non confirmé');
    assert.equal(successes.length,0,name+': fausse fermeture de sessions');
    assert.ok(shown.some(item=>item.type==='error'
      &&item.message.includes('n’a pas pu être confirmée')),
      name+': révocation partielle doit être annoncée');
    assert.equal(button.disabled,false);
  }else if(opts.refreshThrows){
    assert.equal(rpcCalls,1);
    assert.equal(authCalls,1);
    assert.equal(refreshCalls,1);
    assert.ok(successes.length>=1,name+': les mesures Auth sont confirmées');
    assert.ok(shown.at(-1).message.includes('affichage n’a pas pu être actualisé'),
      name+': ne pas confondre panne d’affichage et échec Auth');
    assert.equal(button.disabled,true);
  }else{
    assert.equal(rpcCalls,1);
    assert.equal(authCalls,1);
    assert.equal(sent[0].scope,'others');
    assert.equal(refreshCalls,1);
    assert.equal(successes.length,1,name+': confirmation unique');
    assert.ok(successes[0].message.includes('expiration'),
      name+': mention indispensable des JWT déjà émis');
    assert.equal(button.disabled,true,name+': éviter une nouvelle révocation');
  }
  checks+=8;
}

async function compromisedDoubleClick(){
  let listener,resolveRpc,rpcCalls=0,authCalls=0;
  const button={disabled:false,addEventListener(_type,fn){listener=fn;}};
  const handler=section(
    center,
    "    qs('[data-security-compromised]')?.addEventListener('click',async event=>{",
    "\n\n    document.addEventListener('click',async e=>{"
  );
  const rpcPromise=new Promise(resolve=>{resolveRpc=resolve;});
  const context={
    qs:()=>button,
    meta:{device_key:'fake'},
    contextResult:{context:null},
    confirmAction:()=>true,
    rpc:async()=>{rpcCalls++;return rpcPromise;},
    getSupabase:()=>({auth:{signOut:async()=>{authCalls++;return {error:null};}}}),
    loadState:async()=>({}),
    status(){},
    friendlySecurityError:safe,
    state:null,
  };
  vm.runInNewContext(handler,context,{timeout:1500});
  const first=listener({currentTarget:button});
  const second=listener({currentTarget:button});
  assert.equal(rpcCalls,1,'Double clic : une seule RPC de sécurité');
  assert.equal(button.disabled,true,'Double clic : verrou actif avant appel réseau');
  resolveRpc({ok:true,revoked_devices:1});
  await Promise.all([first,second]);
  assert.equal(authCalls,1,'Double clic : une seule révocation Auth');
  checks+=3;
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
  await compromisedAccountScenario('Confirmation refusée',{confirm:false});
  for(const [name,value] of [
    ['RPC nulle',null],
    ['RPC vide',{}],
    ['RPC échec',{ok:false,revoked_devices:1}],
    ['RPC sans compte',{ok:true}],
    ['RPC sans nombre',{ok:true,revoked_devices:'2'}],
    ['RPC négative',{ok:true,revoked_devices:-1}],
    ['RPC décimale',{ok:true,revoked_devices:1.5}],
  ])await compromisedAccountScenario(name,{rpcResult:value,rpcFailure:true});
  await compromisedAccountScenario('RPC exception',{rpcThrows:true,rpcFailure:true});
  for(const [name,value] of [
    ['signOut null',null],
    ['signOut undefined',undefined],
    ['signOut vide',{}],
    ['signOut erreur indéfinie',{error:undefined}],
    ['signOut erreur privée',{error:new Error(SECRET)}],
  ])await compromisedAccountScenario(name,{authResult:value,authFailure:true});
  await compromisedAccountScenario('signOut exception',{authThrows:true,authFailure:true});
  await compromisedAccountScenario('signOut confirmé');
  await compromisedAccountScenario('Échec actualisation',{refreshThrows:true});
  await compromisedDoubleClick();
  console.log('PASS: '+checks+' vérifications des erreurs Auth/RPC, révocation d’urgence, messages privés et journaux sans réseau.');
})().catch(error=>{console.error(error);process.exitCode=1;});
