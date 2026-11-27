'use strict';
// Tests des sources réellement exécutées : redirection post-login et contrôle MFA.
// Pas de réseau, pas de session et pas de données privées.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const ORIGIN='https://www.benoitcantin.com';
const AUTH=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-auth-route.js'),'utf8');
const SHARED=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-supabase.js'),'utf8');
const HOME='/compte/index.html';
let checks=0;
function eq(actual,expected,context){
  assert.equal(actual,expected,context);
  checks++;
}
function auth(href='/compte/connexion.html'){
  const url=new URL(href,ORIGIN);
  const location={origin:ORIGIN,href:url.href,search:url.search};
  const historyCalls=[];
  const history={
    state:null,
    replaceState(_state,_title,target){
      historyCalls.push(target);
      const updated=new URL(target,ORIGIN);
      location.href=updated.href;
      location.search=updated.search;
    }
  };
  const window={};
  const document={addEventListener(event,handler,capture){
    if(event==='submit')eq(capture,true,'La politique de mots de passe doit être en phase capture');
  },querySelector(){return null}};
  const ctx=vm.createContext({window,location,history,document,URL,URLSearchParams,Object});
  vm.runInContext(AUTH,ctx,{filename:'sinjira-auth-route.js',timeout:1000});
  return {route:window.SINJIRA_AUTH_ROUTE,location,historyCalls};
}
const SHARED_START=SHARED.indexOf('export function safeInternalDestination(');
const SHARED_END=SHARED.indexOf('\nexport async function requireUser(',SHARED_START);
assert.ok(SHARED_START>=0&&SHARED_END>SHARED_START,'Fonction partagée de contrôle de destination introuvable');
const sharedCode=SHARED.slice(SHARED_START,SHARED_END).replace('export function','function')+
  '\nglobalThis.checkDestination=safeInternalDestination;';
const sharedCtx=vm.createContext({URL,location:{origin:ORIGIN}});
vm.runInContext(sharedCode,sharedCtx,{filename:'sinjira-supabase.js',timeout:1000});
const sharedDestination=sharedCtx.checkDestination;

function safeTests(safe,label){
  for(const path of [
    '/', '/compte/index.html', '/app/', '/projets/sinjira/',
    '/compte/index.html?tab=1#notifications',
    '/projets/sinjira/romans/lire-demo.html?edition=demo&lang=fr',
    '/app/?value=%3Ctexte%3E#top'
  ])eq(safe(path),path,label+': lien interne valide rejeté: '+path);
  for(const path of [
    '',null,undefined,[],{},'https://evil.invalid/login',
    'https:%2f%2fevil.invalid/login','javascript:alert(1)','data:text/html,<h1>evil</h1>',
    '//evil.invalid/','///evil.invalid/','/\\evil.invalid/',
    '/%2fevil.invalid/','/%2Fevil.invalid/','/%2F%2Fevil.invalid/',
    '/%5cevil.invalid/','/%5Cevil.invalid/',
    '/app/%0aescape','/app/%0Dredirect','/app/%1fredirect','/app/%7Fredirect',
    '/app/../admin/','/app/%2e%2e/admin/','/app/%2E%2E/admin/',
    '/app/./','/app/%2e/',' /app/','/app/ ',
    '/app/\nline','/app/\ttab','/app/\rline',
    '/app/test\\path',
  ])eq(safe(path),HOME,label+': destination ambiguë acceptée: '+String(path));
}
async function assuranceTests(){
  const start=SHARED.indexOf('export function assertKnownAssuranceLevels(');
  const end=SHARED.indexOf('export function safeInternalDestination(',start);
  assert.ok(start>=0&&end>start);
  const validator=SHARED.slice(start,end).replace('export function','function');
  const gateStart=SHARED.indexOf('export async function requireUser(');
  const gateEnd=SHARED.indexOf('export function isSinjiraOwner(',gateStart);
  assert.ok(gateStart>=0&&gateEnd>gateStart);
  const gate=SHARED.slice(gateStart,gateEnd).replace('export async function','async function');
  const recovery=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-recovery-v24-4-99.js'),'utf8');
  const recoveryStart=recovery.indexOf('async function requireRecoveryAal2WhenAvailable(');
  const recoveryEnd=recovery.indexOf('async function boot(',recoveryStart);
  assert.ok(recoveryStart>=0&&recoveryEnd>recoveryStart);
  const recoveryGate=recovery.slice(recoveryStart,recoveryEnd);

  for(const data of [null,undefined,{}, {currentLevel:'aal1'}, {nextLevel:'aal2'},
    {currentLevel:null,nextLevel:'aal1'},{currentLevel:'aal1',nextLevel:null},
    {currentLevel:'aal3',nextLevel:'aal1'},{currentLevel:'aal1',nextLevel:'unknown'}]){
    const redirects=[];
    const client={auth:{mfa:{getAuthenticatorAssuranceLevel:async()=>({data,error:null})}}};
    const ctx={getCurrentUser:async()=>({id:'test-user'}),getSupabase:()=>client,s:client,
      safeInternalDestination:sharedDestination,location:{pathname:HOME,search:'',hash:'',replace:v=>redirects.push(v)},
      console:{warn(){}},setBusy(){},setStatus(){},status:null,RESET_PATH:'/compte/reinitialiser-mot-de-passe.html'};
    vm.runInNewContext(validator+gate+recoveryGate+'\nglobalThis.gate=requireUser;globalThis.recover=requireRecoveryAal2WhenAvailable;',ctx);
    let settled=false;
    ctx.gate().then(()=>{settled=true},()=>{settled=true});
    await new Promise(resolve=>setImmediate(resolve));
    eq(settled,false,'Le garde central ne doit pas autoriser un AAL indéterminé');
    eq(redirects.length,1,'Un AAL indéterminé doit conduire au contrôle MFA');
    eq(redirects[0].includes('state=aal-check'),true,'Contrôle MFA explicite');
    await assert.rejects(ctx.recover(),/MFA_STATE_UNAVAILABLE/);
    checks++;
  }
  for(const [currentLevel,nextLevel,expected] of [['aal1','aal1',true],['aal2','aal2',true],['aal2','aal1',true],['aal1','aal2',false]]){
    const redirects=[];
    const client={auth:{mfa:{getAuthenticatorAssuranceLevel:async()=>({data:{currentLevel,nextLevel},error:null})}}};
    const ctx={getCurrentUser:async()=>({id:'test-user'}),getSupabase:()=>client,s:client,
      safeInternalDestination:sharedDestination,location:{pathname:HOME,search:'',hash:'',replace:v=>redirects.push(v)},
      console:{warn(){}},setBusy(){},setStatus(){},status:null,RESET_PATH:'/compte/reinitialiser-mot-de-passe.html'};
    vm.runInNewContext(validator+gate+recoveryGate+'\nglobalThis.gate=requireUser;globalThis.recover=requireRecoveryAal2WhenAvailable;',ctx);
    if(expected)eq((await ctx.gate()).id,'test-user','AAL connu et autorisé');
    else {
      let settled=false;
      ctx.gate().then(()=>{settled=true},()=>{settled=true});
      await new Promise(resolve=>setImmediate(resolve));
      eq(settled,false,'Un facteur vérifié doit être demandé');
      eq(redirects.length,1,'Redirection MFA requise');
    }
    eq(await ctx.recover(),expected,'Politique AAL de récupération conservée');
  }
}
async function recoveryRevocationTests(){
  const recovery=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-recovery-v24-4-99.js'),'utf8');
  const start=recovery.indexOf('async function revokeRecoverySessions(');
  const end=recovery.indexOf('async function boot(',start);
  assert.ok(start>=0&&end>start,'Fonction de révocation absente');
  const rejected=Symbol('network failure');
  const cases=[
    [{error:null},undefined,'global',['global']],
    [{error:{message:'denied'}},{error:null},'local',['global','local']],
    [rejected,{error:null},'local',['global','local']],
    [undefined,{error:null},'local',['global','local']],
    [{},{error:null},'local',['global','local']],
    [{error:{message:'denied'}},{error:{message:'denied'}},'unconfirmed',['global','local']],
    [rejected,rejected,'unconfirmed',['global','local']],
    [undefined,undefined,'unconfirmed',['global','local']],
  ];
  for(const [globalResult,localResult,expected,scopes] of cases){
    const calls=[];
    const ctx={s:{auth:{signOut:async({scope})=>{
      calls.push(scope);
      const result=scope==='global'?globalResult:localResult;
      if(result===rejected)throw Error('offline');
      return result;
    }}}};
    vm.runInNewContext(recovery.slice(start,end)+'\nglobalThis.revoke=revokeRecoverySessions;',ctx);
    eq(await ctx.revoke(),expected,'Résultat de révocation exact');
    assert.deepEqual(calls,scopes);checks++;
  }
  assert.ok(recovery.includes("if(revoked!=='global')"),'Pas de succès global sans confirmation');
  assert.ok(recovery.includes('finally{submitting=false;setBusy(passwordUpdated)}'),'Pas de nouvelle soumission après changement');
  assert.ok(recovery.includes('if(submitting||passwordUpdated)return;'),'Verrou de soumission');
  checks+=3;
}

async function recoveryIdentityTests(){
  const source=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-recovery-v24-4-99.js'),'utf8');
  const start=source.indexOf('async function recoveryIdentity(');
  const end=source.indexOf('async function boot(',start);
  assert.ok(start>=0&&end>start);
  const rejected=Symbol('network failure');
  for(const [result,expectedId,expected] of [
    [{error:null,data:{user:{id:'test-user'}}},undefined,'test-user'],
    [{error:null,data:{user:{id:'test-user'}}},'test-user','test-user'],
    [{error:null,data:{user:{id:'other-user'}}},'test-user',null],
    [{error:null,data:{user:{id:''}}},undefined,null],
    [{error:null,data:{user:{id:' '}}},undefined,null],
    [{error:null,data:{user:{id:42}}},undefined,null],
    [{error:null,data:{user:null}},undefined,null],
    [{error:{message:'denied'},data:{user:{id:'test-user'}}},'test-user',null],
    [{data:{user:{id:'test-user'}}},'test-user',null],
    [undefined,'test-user',null],
    [rejected,'test-user',null]
  ]){
    const ctx={s:{auth:{getUser:async()=>{if(result===rejected)throw Error('offline');return result}}}};
    vm.runInNewContext(source.slice(start,end)+'\nglobalThis.identity=recoveryIdentity;',ctx,{timeout:1000});
    eq(await ctx.identity(expectedId),expected,'Identité de récupération vérifiée et stable');
  }
  const submit=source.slice(source.indexOf("form.addEventListener('submit'"));
  assert.ok(source.includes('const recoveryUserId=await recoveryIdentity();'));
  assert.ok(submit.indexOf('if(!await recoveryIdentity(recoveryUserId))')>submit.indexOf('if(!await requireRecoveryAal2WhenAvailable())'));
  assert.ok(submit.indexOf('if(!await recoveryIdentity(recoveryUserId))')<submit.indexOf('s.auth.updateUser({password})'));
  assert.ok(!/console\.(?:warn|error)\([^\n]*,\s*error\b/.test(source),'Aucune exception brute dans les logs de récupération');
  checks+=4;
}

async function compromiseRevocationTests(){
  const source=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-security-center-v24-4-98.js'),'utf8');
  const start=source.indexOf('async function revokeCompromisedSessions(');
  const end=source.indexOf('async function boot(',start);
  assert.ok(start>=0&&end>start);
  const reject=Symbol('offline');
  const ok={error:null}, denied={error:{message:'denied'}};
  for(const [rpcResult,authResult,expected,attempt] of [
    [ok,ok,'confirmed',true],
    [ok,denied,'devices-only',true],
    [ok,undefined,'devices-only',true],
    [ok,{},'devices-only',true],
    [ok,reject,'devices-only',true],
    [denied,ok,'unconfirmed',false],
    [undefined,ok,'unconfirmed',false],
    [{},ok,'unconfirmed',false],
    [reject,ok,'unconfirmed',false]
  ]){
    const calls=[];
    const respond=result=>{if(result===reject)throw Error('offline');return result};
    const client={rpc:async(name,args)=>{calls.push(name);eq(args.p_current_device_key,'synthetic-device','Appareil courant');return respond(rpcResult)},
      auth:{signOut:async({scope})=>{calls.push(scope);return respond(authResult)}}};
    const ctx={};
    vm.runInNewContext(source.slice(start,end)+'\nglobalThis.revoke=revokeCompromisedSessions;',ctx,{timeout:1000});
    eq(await ctx.revoke(client,'synthetic-device'),expected,'Confirmation explicite des mesures d’urgence');
    assert.deepEqual(calls,attempt?['security_compromise_account','others']:['security_compromise_account']);checks++;
  }
  assert.ok(source.includes("if(result==='confirmed')"));
  assert.ok(source.includes("else if(result==='devices-only')"));
  assert.ok(source.includes('compromisePending||!confirmAction'));
  assert.ok(source.includes('finally{compromisePending=false;button.disabled=false}'));
  checks+=4;
}

async function lostDeviceRevocationTests(){
  const source=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-security-v24-4-99.js'),'utf8');
  const start=source.indexOf('async function reportLostDevice(');
  const end=source.indexOf('let lostDevicePending=',start);
  assert.ok(start>=0&&end>start);
  const reject=Symbol('offline'), ok={error:null}, denied={error:{message:'denied'}};
  const rpcOk={error:null,data:{ok:true,device_id:'synthetic-id',session_revocation_required:true}};
  for(const [rpcResult,authResult,expected,attempt] of [
    [rpcOk,ok,'confirmed',true],
    [rpcOk,denied,'device-only',true],
    [rpcOk,undefined,'device-only',true],
    [rpcOk,{},'device-only',true],
    [rpcOk,reject,'device-only',true],
    [{error:{message:'AAL2_REQUIRED'}},ok,'mfa-required',false],
    [ok,ok,'unconfirmed',false],
    [{error:null,data:{ok:false,device_id:'synthetic-id',session_revocation_required:true}},ok,'unconfirmed',false],
    [{error:null,data:{ok:true,device_id:'other-id',session_revocation_required:true}},ok,'unconfirmed',false],
    [{error:null,data:{ok:true,device_id:'synthetic-id',session_revocation_required:false}},ok,'unconfirmed',false],
    [{error:null,data:{ok:'true',device_id:'synthetic-id',session_revocation_required:true}},ok,'unconfirmed',false],
    [denied,ok,'unconfirmed',false],
    [undefined,ok,'unconfirmed',false],
    [{},ok,'unconfirmed',false],
    [reject,ok,'unconfirmed',false]
  ]){
    const calls=[];
    const respond=result=>{if(result===reject)throw Error('synthetic private detail');return result};
    const client={rpc:async(name,args)=>{calls.push(name);eq(args.p_device_id,'synthetic-id','Identifiant de l’appareil');return respond(rpcResult)},
      auth:{signOut:async({scope})=>{calls.push(scope);return respond(authResult)}}};
    const ctx={};
    vm.runInNewContext(source.slice(start,end)+'\nglobalThis.report=reportLostDevice;',ctx,{timeout:1000});
    eq(await ctx.report(client,'synthetic-id'),expected,'Résultat explicite de déclaration de perte');
    assert.deepEqual(calls,attempt?['security_report_lost_device','others']:['security_report_lost_device']);checks++;
  }
  assert.ok(source.includes("if(result==='confirmed')"));
  assert.ok(source.includes("if(result==='device-only')"));
  assert.ok(source.includes("lostDevicePending||button.disabled"));
  assert.ok(!/console\.(?:warn|error)\([^\n]*,\s*error\b/.test(source));
  checks+=4;
}

function recoveryCleanupContractTests(){
  const source=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-recovery-v24-4-99.js'),'utf8');
  const start=source.indexOf('function recoveryCleanupConfirmed(');
  const end=source.indexOf('async function recoveryIdentity(',start);
  assert.ok(start>=0&&end>start);
  const ctx={};
  vm.runInNewContext(source.slice(start,end)+'\nglobalThis.confirmed=recoveryCleanupConfirmed;',ctx,{timeout:1000});
  for(const [result,expected] of [
    [{error:null,data:{ok:true,current_device_trusted:false}},true],
    [{error:null},false],
    [{error:null,data:null},false],
    [{error:null,data:{ok:false,current_device_trusted:false}},false],
    [{error:null,data:{ok:true,current_device_trusted:true}},false],
    [{error:null,data:{ok:true}},false],
    [{error:null,data:{ok:'true',current_device_trusted:false}},false],
    [{error:{message:'denied'},data:{ok:true,current_device_trusted:false}},false],
    [undefined,false]
  ])eq(ctx.confirmed(result),expected,'Contrat de confirmation du nettoyage après récupération');
  assert.ok(source.includes('cleanupOk=recoveryCleanupConfirmed(result);'));
  checks++;
}

function securityCenterRenderingTests(){
  const source=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-security-center-v24-4-98.js'),'utf8');
  const shared=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-supabase.js'),'utf8');
  const escape=shared.split('\n').find(line=>line.startsWith('export function escapeHtml('));
  const start=source.indexOf('function validSecurityRecordId(');
  const end=source.indexOf('function fillSettings(',start);
  const pillStart=source.indexOf('function pill(');
  const pillEnd=source.indexOf('async function rpc(',pillStart);
  assert.ok(escape&&start>=0&&end>start&&pillStart>=0&&pillEnd>pillStart);
  const nodes=new Map();
  const ctx={qs:sel=>{if(!nodes.has(sel))nodes.set(sel,{innerHTML:''});return nodes.get(sel)},formatDate:()=> 'date'};
  vm.runInNewContext(escape.replace('export ','')+'\n'+source.slice(pillStart,pillEnd)+source.slice(start,end)+'\nglobalThis.render={validSecurityRecordId,renderDevices,renderTravel,renderChallenges};',ctx,{timeout:1000});
  const id='12345678-1234-4234-8234-123456789abc',other='87654321-4321-4321-8321-cba987654321';
  const bad=['',null,undefined,42,{},'invalid-id',id+' ',id+'\n','" data-untrusted="marker','<invalid>'];
  const {render}=ctx;
  eq(render.validSecurityRecordId(id),true,'UUID valide');
  for(const value of bad)eq(render.validSecurityRecordId(value),false,'Identifiant malformé refusé');
  for(const value of bad){
    render.renderDevices([{id:value,is_current:true,is_trusted:false}]);
    assert.ok(!nodes.get('[data-security-devices]').innerHTML.includes('data-device-trust='));
    render.renderTravel([{id:value,status:'active',destinations:[]}]);
    assert.ok(!nodes.get('[data-security-travel-list]').innerHTML.includes('data-travel-cancel='));
    render.renderChallenges([{id:value,request_device_id:other,status:'pending',expires_at:'2099-01-01'}],[{id,is_current:true,is_trusted:true}]);
    assert.ok(!nodes.get('[data-security-challenges]').innerHTML.includes('data-challenge-approve='));
    checks+=3;
  }
  render.renderDevices([{id,is_current:true,is_trusted:false}]);
  assert.ok(nodes.get('[data-security-devices]').innerHTML.includes('data-device-trust="'+id+'"'));
  render.renderTravel([{id,status:'active',destinations:[]}]);
  assert.ok(nodes.get('[data-security-travel-list]').innerHTML.includes('data-travel-cancel="'+id+'"'));
  const pending=[{id,request_device_id:other,status:'pending',expires_at:'2099-01-01'}];
  render.renderChallenges(pending,[{id,is_current:true,is_trusted:true}]);
  assert.ok(nodes.get('[data-security-challenges]').innerHTML.includes('data-challenge-approve="'+id+'"'));
  render.renderChallenges(pending,[{id,is_current:true,is_trusted:'true'}]);
  assert.ok(!nodes.get('[data-security-challenges]').innerHTML.includes('data-challenge-approve='));
  render.renderChallenges([{...pending[0],request_device_id:'invalid'}],[{id,is_current:true,is_trusted:true}]);
  assert.ok(!nodes.get('[data-security-challenges]').innerHTML.includes('data-challenge-approve='));
  checks+=5;
}

function deviceEntropyTests(){
  for(const file of ['sinjira-auth-pages.js','sinjira-recovery-v24-4-99.js','sinjira-security-center-v24-4-98.js']){
    const source=fs.readFileSync(path.join(ROOT,'assets/js',file),'utf8');
    const start=source.indexOf('function randomDeviceKey(){');
    const end=source.indexOf('\n}',start);
    assert.ok(start>=0&&end>start,file+': générateur absent');
    const body=source.slice(start,end+2);
    function generate(crypto){
      const ctx={crypto,Uint8Array,Array};
      vm.runInNewContext(body+'\nglobalThis.generate=randomDeviceKey;',ctx,{timeout:1000});
      return ctx.generate();
    }
    const uuid='12345678-1234-4234-8234-123456789abc';
    eq(generate({randomUUID:()=>uuid}),uuid,file+': UUID CSPRNG');
    let requested=0;
    const secureBytes=bytes=>{requested=bytes.length;bytes.fill(0xab);return bytes;};
    eq(generate({getRandomValues:secureBytes}),'sinjira-'+'ab'.repeat(24),file+': repli cryptographique');
    eq(requested,24,file+': 192 bits demandés');
    eq(generate({randomUUID(){throw Error('unavailable')},getRandomValues:secureBytes}),'sinjira-'+'ab'.repeat(24),file+': UUID indisponible');
    for(const crypto of [undefined,{}, {randomUUID(){throw Error('unavailable')}}]){
      assert.throws(()=>generate(crypto),/SECURITY_CRYPTO_UNAVAILABLE/);checks++;
    }
    assert.throws(()=>generate({getRandomValues(){throw Error('entropy failed')}}),/entropy failed/);checks++;
    assert.ok(!/Date\.now|Math\.random|\.getRandomValues\?\./.test(body),file+': aucun repli prévisible');checks++;
  }
}
async function loginDecisionTests(){
  const source=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-auth-pages.js'),'utf8');
  const start=source.indexOf('async function login(){');
  const end=source.indexOf('async function forgot(){',start);
  assert.ok(start>=0&&end>start);
  const login=source.slice(start,end);
  for(const outcome of ['allow','approved','block',undefined,null,'','denied','unexpected',42]){
    const redirects=[],signouts=[],messages=[];
    let submit;
    const form={addEventListener(_type,handler){submit=handler}};
    const client={auth:{signInWithPassword:async()=>({error:null}),signOut:async(options)=>{signouts.push(options.scope);return {error:null}}}};
    const ctx={document:{querySelector:()=>form},getCurrentUser:async()=>null,ready:()=>true,reportInvalid:()=>false,
      FormData:class {get(){return ''}},destination:()=>HOME,setBusy(){},clearPendingChallenge(){},
      securityDeviceMetadata:()=>({device_key:'synthetic-test-key'}),getSupabase:()=>client,
      evaluateLoginSecurity:async()=>({security:{outcome}}),setStatus:(_node,message)=>messages.push(message),
      status:null,location:{replace:value=>redirects.push(value)},console:{warn(){}}};
    vm.runInNewContext(login+'\nglobalThis.init=login;',ctx);
    await ctx.init();
    await submit({preventDefault(){}});
    if(outcome==='allow'||outcome==='approved'){
      eq(redirects.length,1,'Décision autorisée explicite');
      eq(signouts.length,0,'Session autorisée conservée');
    }else{
      eq(redirects.length,0,'Décision non autorisée: aucune redirection');
      eq(signouts.length,1,'Décision non autorisée: déconnexion tentée');
      eq(messages.length,1,'Décision non autorisée: avertissement visible');
    }
  }
  assert.ok(login.indexOf('const meta=securityDeviceMetadata();')<login.indexOf('auth.signInWithPassword('),'Génération avant ouverture de session');checks++;
}

async function main(){
  const client=auth();
  safeTests(client.route.safeLocalDestination,'Login');
  safeTests(sharedDestination,'MFA/shared');
  eq(client.route.safeLocalDestination('javascript:alert(1)',''),'',
    'Une valeur de repli vide doit rester vide');
  eq(client.route.safeLocalDestination('/app/',''),'/app/','Destination valide avec repli vide');

  const invalid=auth('/compte/connexion.html?next=javascript%3Aalert%281%29&mode=login#main');
  eq(invalid.location.search,'?mode=login','Un next malveillant doit être supprimé');
  eq(invalid.historyCalls.length,1,'Assainissement de next enregistré dans history');
  eq(invalid.route.next(),HOME,'Destination de secours après suppression');
  eq(invalid.location.href.endsWith('/compte/connexion.html?mode=login#main'),true,
    'Autres paramètres et fragment conservés');

  const encoded=auth('/compte/connexion.html?next=%2F%252F%252Fevil.invalid%2F');
  eq(encoded.location.search,'','Slash encodé dans next refusé et paramètre supprimé');
  eq(encoded.route.next(),HOME,'Aucune destination ambiguë persistante');

  const normalized=auth('/compte/connexion.html?next=%2Fcompte%2F..%2Fadmin%2F');
  eq(normalized.location.search,'','Traversée relative normalisée retirée de next');

  const valid=auth('/compte/connexion.html?next=%2Fapp%2F');
  eq(valid.location.search,'?next=%2Fapp%2F','Destination saine conservée');
  eq(valid.route.next(),'/app/','Destination saine réellement navigable');
  eq(valid.historyCalls.length,0,'Aucune écriture d’historique inutile');

  for(const query of [
    'next=%2Fapp%2F&next=%2Fcompte%2F',
    'next=%2Fapp%2F&next=%2Fapp%2F',
    'next=%2Fapp%2F&next=https%3A%2F%2Fevil.invalid',
    'next=https%3A%2F%2Fevil.invalid&next=%2Fapp%2F',
    'next=%2Fapp%2F&n%65xt=%2Fcompte%2F',
    'next=&next=%2Fapp%2F'
  ]){
    const duplicate=auth('/compte/connexion.html?'+query+'&mode=login#main');
    eq(duplicate.location.search,'?mode=login','Tous les next ambigus sont supprimés');
    eq(duplicate.route.next(),HOME,'Repli sûr après doublon');
    eq(duplicate.historyCalls.length,1,'Une seule correction d’historique');
  }
  // La lecture après initialisation doit aussi refuser les doublons.
  valid.location.search='?next=%2Fapp%2F&next=%2Fcompte%2F';
  eq(valid.route.next(),HOME,'Doublon introduit après initialisation refusé');

  // Exécuter les lignes réelles de sélection de destination du module MFA.
  const mfa=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-mfa-v24-4-66.js'),'utf8');
  const mfaLines=mfa.split('\n').filter(line=>/^(const params=|const nextValues=|const next=)/.test(line));
  assert.equal(mfaLines.length,3,'Sélecteur MFA canonique absent');
  for(const [search,expected] of [
    ['?next=%2Fapp%2F','/app/'],
    ['?next=%2Fapp%2F&next=%2Fcompte%2F',HOME],
    ['?next=%2Fapp%2F&n%65xt=%2Fapp%2F',HOME],
    ['?next=%2F%2Fevil.invalid',HOME],
    ['',HOME]
  ]){
    const ctx={URLSearchParams,location:{search},safeInternalDestination:sharedDestination};
    vm.runInNewContext(mfaLines.join('\n')+'\nglobalThis.result=next;',ctx,{timeout:1000});
    eq(ctx.result,expected,'Sélection MFA sans ambiguïté');
  }

  const blank=auth('/compte/connexion.html?next=');
  eq(blank.location.search,'','Destination next vide retirée');

  eq(sharedDestination('/compte/index.html?tab=1','/compte/bibliotheque.html'),
    '/compte/index.html?tab=1','Navigation locale commune reste valide');
  eq(sharedDestination('//evil.invalid/','/compte/bibliotheque.html'),
    '/compte/bibliotheque.html','Fallback MFA prédéfini conservé');
  await assuranceTests();
  await recoveryRevocationTests();
  await recoveryIdentityTests();
  await compromiseRevocationTests();
  await lostDeviceRevocationTests();
  recoveryCleanupContractTests();
  securityCenterRenderingTests();
  deviceEntropyTests();
  await loginDecisionTests();
  console.log('PASS: '+checks+' contrôles de redirections Auth/MFA, URLs encodées et next assaini.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
