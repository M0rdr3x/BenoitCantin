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
  console.log('PASS: '+checks+' contrôles de redirections Auth/MFA, URLs encodées et next assaini.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
