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
function main(){
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

  const blank=auth('/compte/connexion.html?next=');
  eq(blank.location.search,'','Destination next vide retirée');

  eq(sharedDestination('/compte/index.html?tab=1','/compte/bibliotheque.html'),
    '/compte/index.html?tab=1','Navigation locale commune reste valide');
  eq(sharedDestination('//evil.invalid/','/compte/bibliotheque.html'),
    '/compte/bibliotheque.html','Fallback MFA prédéfini conservé');
  console.log('PASS: '+checks+' contrôles de redirections Auth/MFA, URLs encodées et next assaini.');
}
main();
