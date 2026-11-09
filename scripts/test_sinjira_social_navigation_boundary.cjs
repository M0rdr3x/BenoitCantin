#!/usr/bin/env node
'use strict';
// Tests des fonctions réellement chargées dans les parcours compte SINJIRA.
// Aucun réseau, aucun compte réel, aucune modification Supabase.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {pathToFileURL}=require('node:url');

const ROOT=path.resolve(__dirname,'..');
const ORIGIN='https://www.benoitcantin.com';
const HOME='/compte/communaute.html';
const SCOPES=['/compte/','/projets/sinjira/'];
const read=file=>fs.readFileSync(path.join(ROOT,file),'utf8');
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,char=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'
})[char]);
let assertions=0;
function equal(actual,expected,why){
  assert.equal(actual,expected,why);
  assertions++;
}
async function main(){
  // Le module ESM est directement importé (aucune duplication de la politique).
  const {safeSocialDestination}=await import(pathToFileURL(path.join(ROOT,'assets/js/sinjira-social-navigation-guard.mjs')).href);
  function accepted(value,expected=value){
    equal(safeSocialDestination(value,{origin:ORIGIN,scopes:SCOPES}),expected,
      'Lien légitime local refusé : '+value);
  }
  function rejected(value){
    equal(safeSocialDestination(value,{origin:ORIGIN,scopes:SCOPES}),'',
      'Lien externe, hors périmètre ou ambigu accepté : '+String(value));
  }

  [
    '/compte/communaute.html','/compte/messages.html','/compte/notifications.html',
    '/compte/securite.html?tab=devices#session','/compte/messages-reels.html?peer=ab%2Fcd',
    '/compte/index.html?next=%2Fcompte%2Fmessages.html',
    '/projets/sinjira/','/projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html'
  ].forEach(v=>accepted(v));
  [
    '',null,undefined,12,{},[], '/','/compte','/admin/sinjira/',
    '/projets/projet-nova/','https://evil.invalid/','http://evil.invalid/',
    'javascript:alert(1)','data:text/html,<svg/onload=alert(1)>',
    '//evil.invalid/','///evil.invalid/','/\\evil.invalid/',
    '/%2fevil.invalid/','/%5cevil.invalid/',
    '/compte/../../evil','/compte/%2e%2e/evil','/compte/%2E%2E/evil',
    '/compte/./messages.html','/compte/%2e/messages.html',
    '/compte/%2f%2fevil.invalid','/compte/%5cevil.invalid',
    '/compte/%0amessage','/compte/%0dmessage','/compte/%1fmessage',
    '/compte/%7fmessage','/compte/hello\\world',
    '/compte/\nmalicious','/compte/\rmalicious','/compte/\tmalicious',
    ' /compte/messages.html','/compte/messages.html ',
    '/'+ 'x'.repeat(2048)
  ].forEach(rejected);
  equal(safeSocialDestination('/compte/messages.html',{origin:'http://evil.invalid',scopes:SCOPES}),'',
    'Origine fournie non HTTPS');
  equal(safeSocialDestination('/compte/messages.html',{origin:ORIGIN,scopes:['//evil.invalid']}),'',
    'Périmètre non valide');
  accepted('/compte/messages.html?ref=1&part=2#post');

  // Évaluer le vrai client de notifications et inspecter les vrais attributs href.
  const notifySource=read('assets/js/sinjira-user-notifications-v24-4-63.js');
  const notifySandbox=vm.createContext({
    URL,
    safeSocialDestination,escapeHtml,
    formatDate(){return 'date locale'},
    getSupabase(){return {}},
    document:{querySelector(){return null}},
    location:{origin:ORIGIN},
    console
  });
  vm.runInContext(
    notifySource.replace(/^import[^\n]*\n/gm,'')+
       '\nglobalThis.__notificationFns={safeActionPath,notificationCard};',
    notifySandbox,{filename:'sinjira-user-notifications-v24-4-63.js',timeout:2000}
  );
  const {safeActionPath,notificationCard}=notifySandbox.__notificationFns;
  const sample={id:'00000000-0000-4000-8000-000000000001',notification_type:'access_request',
    title:'Accès confirmé',body:'La demande est acceptée.',created_at:'2026-11-09',read_at:null};
  for(const path of [
    '/compte/messages.html','/projets/sinjira/', '/compte/notifications.html?filter=all'
  ]){
    equal(safeActionPath(path),path,'Lien de notification légitime conservé');
    const html=notificationCard({...sample,action_path:path});
    assert.ok(html.includes('href="'+escapeHtml(path)+'"'),'Action de notification sûre affichée');
    assertions++;
  }
  for(const path of [
    '//evil.invalid/phishing','/compte/%2e%2e/admin/sinjira/',
    '/compte/%2f%2fevil.invalid/login','/projets/projet-nova/',
    'javascript:alert(1)','/compte/../../admin/sinjira/'
  ]){
    equal(safeActionPath(path),'','Action notification douteuse interdite');
    const html=notificationCard({...sample,action_path:path});
    assert.ok(!html.includes('data-notification-open='),
      'L’action d’une notification douteuse ne doit pas être rendue');
    assertions++;
  }
  const xss=notificationCard({...sample,title:'<img src=x onerror=alert(1)>',action_path:'//evil.invalid/'});
  assert.ok(!xss.includes('<img '),'Titre notification HTML non échappé');
  assertions++;

  // Parcours authentique du bouton « accepter les règles » avec Supabase simulé.
  async function rulesNext(destination){
    const listeners={};
    const button={disabled:false,textContent:"J’accepte",addEventListener(type,fn){listeners[type]=fn}};
    const location={origin:ORIGIN,search:'?next='+encodeURIComponent(destination),href:ORIGIN+'/compte/regles-communaute.html'};
    const db={
      select(){return this},eq(){return this},
      async maybeSingle(){return {data:null,error:null}},
      async upsert(){return {error:null}}
    };
    const sandbox=vm.createContext({
      URLSearchParams,location,
      safeSocialDestination,
      document:{querySelector(selector){
        if(selector==='[data-rules-status]')return {hidden:true};
        if(selector==='[data-accept-rules]')return button;
        return null;
      }},
      getSupabase(){return {from(){return db}}},
      requireUser:async()=>({id:'faux-utilisateur'}),
      RULES_VERSION:'test-rules',
      socialStatus(){},socialErrorStatus(){},
      setTimeout(fn){fn();},
      Date,console
    });
    const src=read('assets/js/sinjira-community-rules.js').replace(/^import[^\n]*\n/gm,'');
    vm.runInContext(src,sandbox,{filename:'sinjira-community-rules.js',timeout:2000});
    await new Promise(resolve=>setImmediate(resolve));
    assert.equal(typeof listeners.click,'function','Bouton de consentement non relié');
    assertions++;
    await listeners.click();
    equal(button.disabled,false,'Bouton réactivé après consentement');
    return location.href;
  }
  equal(await rulesNext('/compte/messages.html?view=threads'),
    '/compte/messages.html?view=threads','Retour local après consentement conservé');
  for(const value of [
    '//evil.invalid/phishing','///evil.invalid/','javascript:alert(1)',
    '/compte/../../admin/sinjira/','/compte/%2e%2e/admin/sinjira/',
    'https://evil.invalid','/projets/projet-nova/'
  ]){
    equal(await rulesNext(value),HOME,'Retour communautaire dangereux accepté : '+value);
  }
  console.log('PASS: '+assertions+' contrôles réels de redirection communautaire et de liens de notifications, avec variantes URL malveillantes.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
