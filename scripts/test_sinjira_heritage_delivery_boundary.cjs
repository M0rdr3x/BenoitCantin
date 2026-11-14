#!/usr/bin/env node
'use strict';
// Exécute les fonctions réelles de la console Héritage numérique dans une VM.
// Les liens, identifiants et réponses Edge sont synthétiques et aucun réseau,
// jeton utilisateur, export PDF réel ou session Supabase n'est utilisé.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const file='assets/js/sinjira-admin-life-story-v24-5-2.js';
const original=read(file);
const cut=original.lastIndexOf('boot().catch(');
assert.ok(cut>0,'Initialisation du module introuvable');
const source=original.slice(0,cut).replace(/^import[^\n]*\n/gm,'')+
  '\nglobalThis.__heritage={safeAdminUuid,safePrivateDeliveryUrl,renderRequests,renderCase,renderCaseActions,renderVersions,renderCaseCleanup,renderDeliveryLinks,exportAction,loadCleanup,openCase,state};';
const id='123e4567-e89b-42d3-a456-426614174000';
const next='223e4567-e89b-42d3-a456-426614174000';
const malicious='"><img src=x onerror=alert(1)>';
const delivery='https://www.benoitcantin.com/histoire-de-vie/remise.html#'+'a'.repeat(64);
let assertions=0;
function eq(actual,expected,label){assert.equal(actual,expected,label);assertions++}
function yes(condition,label){assert.ok(condition,label);assertions++}
function lacks(content,term,label){yes(!content.includes(term),label)}
const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
})[c]);
function makeNode(){
  return {innerHTML:'',hidden:false,children:[],textContent:'',dataset:{},
    scrollIntoView(){},append(...elements){this.children.push(...elements)},
    setAttribute(key,value){this[key]=value},
    addEventListener(type,fn){this[type]=fn},
    select(){this.selected=true}
  };
}
const sel={
  '[data-legacy-admin-status]':makeNode(),
  '[data-legacy-request-list]':makeNode(),
  '[data-legacy-cleanup-list]':makeNode(),
  '[data-legacy-case-section]':makeNode(),
  '[data-legacy-case-summary]':makeNode(),
  '[data-legacy-case-actions]':makeNode(),
  '[data-legacy-contests]':makeNode(),
  '[data-legacy-versions]':makeNode(),
  '[data-legacy-case-cleanup]':makeNode(),
  '[data-legacy-delivery-once]':makeNode()
};
const listeners={};
const calls=[];
const mock={
  auth:{async getUser(){return {data:{user:{id}},error:null}},mfa:{
    async getAuthenticatorAssuranceLevel(){return {data:{currentLevel:'aal2'},error:null}}
  }},
  async rpc(name,args){
    calls.push({kind:'rpc',name,args});
    if(name==='admin_life_story_cleanup_due')return {data:[],error:null};
    if(name==='admin_life_story_case_detail')return {data:{
      case:{id,status:'ready_for_export'},contests:[],versions:[],exports:[],cleanup_tasks:[]
    },error:null};
    return {data:{},error:null};
  },
  functions:{
    async invoke(name,options){
      calls.push({kind:'edge',name,options});
      if(name!=='life-story-export')throw Error('Unexpected Edge action');
      return {data:{ok:true,links:[{recipient_label:'Test',download_url:delivery}]},error:null};
    }
  }
};
const sandbox=vm.createContext({
  URL,Date,Intl,Promise,
  document:{
    querySelector(selector){return sel[selector]||null},
    addEventListener(type,fn){listeners[type]=fn},
    createElement(){return makeNode()}
  },
  navigator:{clipboard:{async writeText() {throw Error('No clipboard access in test')}}},
  getSupabase:()=>mock,
  escapeHtml,
  friendlyBackendMessage:()=> 'Opération administrative refusée.',
  location:{replace(){throw Error('Navigation réelle interdite')}},
  confirm:()=>true,
  prompt:()=> '',
  console:{error(){throw Error('Unexpected raw logging')}}
});
vm.runInContext(source,sandbox,{filename:file,timeout:3000});
const h=sandbox.__heritage;
async function test(){
  eq(h.safeAdminUuid(id),id,'UUID normal conservé');
  for(const v of [malicious,'abc','javascript:alert(1)',null,1,undefined,id+'" onclick="x']){
    eq(h.safeAdminUuid(v),'','Référence malformée refusée');
  }
  eq(h.safePrivateDeliveryUrl(delivery),delivery,'Jeton privé hex 256 bits valide conservé');
  const unsafe=[
    '',null,123,{},'javascript:alert(1)','data:text/html,<svg onload=alert(1)>',
    'https://evil.invalid/histoire-de-vie/remise.html#'+'b'.repeat(64),
    'https://www.benoitcantin.com.evil.invalid/histoire-de-vie/remise.html#'+'b'.repeat(64),
    '//evil.invalid/histoire-de-vie/remise.html#'+'b'.repeat(64),
    'http://www.benoitcantin.com/histoire-de-vie/remise.html#'+'b'.repeat(64),
    'https://user:password@www.benoitcantin.com/histoire-de-vie/remise.html#'+'b'.repeat(64),
    'https://www.benoitcantin.com/histoire-de-vie/remise.html?token='+('a'.repeat(64)),
    'https://www.benoitcantin.com/histoire-de-vie/remise.html#short',
    'https://www.benoitcantin.com/histoire-de-vie/remise.html#'+'g'.repeat(64),
    'https://www.benoitcantin.com/histoire-de-vie/remise.html#'+'A'.repeat(64),
    'https://www.benoitcantin.com/histoire-de-vie/../remise.html#'+'a'.repeat(64),
    delivery+'\n',' '+delivery,delivery+' ',
    'https://www.benoitcantin.com/histoire-de-vie/remise.html#'+'a'.repeat(65),
    delivery.replace('https://www.benoitcantin.com','https://www.benoitcantin.com:444'),
    delivery.replace('/remise.html','/remise.html/'),
  ];
  for(const v of unsafe)eq(h.safePrivateDeliveryUrl(v),'','Lien frauduleux interdit : '+String(v).slice(0,85));
  const cleanLabel={recipient_label:'Destinataire fictif',recipient_email:null,expires_at:'2026-11-11T00:00:00Z',download_url:delivery};
  const accepted=h.renderDeliveryLinks([cleanLabel]);
  eq(accepted,true,'Lien authentique affiché');
  eq(sel['[data-legacy-delivery-once]'].children.length,1,'Une seule adresse de remise visible');
  const input=sel['[data-legacy-delivery-once]'].children[0].children[1];
  eq(input.value,delivery,'Le jeton n’est pas modifié avant copie');

  for(const bad of unsafe){
    const result=h.renderDeliveryLinks([{...cleanLabel,download_url:bad}]);
    eq(result,false,'Lien falsifié non affiché');
    eq(sel['[data-legacy-delivery-once]'].hidden,true,'Rendu privé masqué');
    eq(sel['[data-legacy-delivery-once]'].innerHTML,'','Anciens liens retirés de la page');
  }
  eq(h.renderDeliveryLinks([]),false,'Liste de remises vide refusée');
  eq(h.renderDeliveryLinks([cleanLabel,{...cleanLabel,download_url:'javascript:alert(1)'}]),false,
    'Un seul élément invalide bloque la liste complète');

  h.state.requests=[
    {id:malicious,subject_display_name:'Faux signalement',case_status:'pending'},
    {id:next,case_id:malicious,subject_display_name:'Faux dossier'},
    {id,subject_display_name:'Signalement légitime',case_status:'pending'}
  ];
  h.renderRequests();
  const html=sel['[data-legacy-request-list]'].innerHTML;
  yes(html.includes('data-verify-request="'+id+'"'),'Dossier légitime conservé');
  lacks(html,'Faux signalement','ID forgé écarté');
  lacks(html,'Faux dossier','ID case forgé écarté');
  lacks(html,'onerror=','Attribut HTML dangereux rejeté');

  h.renderCaseActions({id:malicious,status:'verified_hold'},true);
  lacks(sel['[data-legacy-case-actions]'].innerHTML,'data-confirm-case','Action de confirmation sans UUID impossible');
  h.renderCaseActions({id,status:'verified_hold'},true);
  yes(sel['[data-legacy-case-actions]'].innerHTML.includes('data-confirm-case="'+id+'"'),
    'Confirmation légitime reste disponible');

  h.renderVersions([
    {id:malicious,title:'Malicious',status:'ready',recipient_count:1,authorized_entry_count:1},
    {id,title:'Version familiale',status:'ready',recipient_count:1,authorized_entry_count:1}
  ],[],{id,status:'ready_for_export'});
  const versions=sel['[data-legacy-versions]'].innerHTML;
  lacks(versions,'Malicious','Version sans UUID rejetée');
  yes(versions.includes('data-prepare-export="'+id+'"'),'Export autorisé avec UUID valide');

  h.renderCaseCleanup([
    {id:malicious,task_type:'Fausse suppression',status:'pending',due_after:'2024-01-01'},
    {id,task_type:'Revue',status:'pending',due_after:'2024-01-01'}
  ]);
  const cleanup=sel['[data-legacy-case-cleanup]'].innerHTML;
  lacks(cleanup,'Fausse suppression','Tâche non UUID masquée');
  yes(cleanup.includes('data-cleanup-task="'+id+'"'),'Tâche légitime conservée');

  for(const [action,exportId] of [['delete_all',id],['generate',malicious],['purge','000']]){
    const n=calls.length;
    await assert.rejects(()=>h.exportAction(action,exportId));
    assertions++;
    eq(calls.length,n,'Action export invalide non envoyée');
  }
  const before=calls.filter(c=>c.kind==='edge').length;
  await h.exportAction('generate',id);
  eq(calls.filter(c=>c.kind==='edge').length,before+1,'Export PDF valide transmis une seule fois');
  eq(calls.filter(c=>c.kind==='edge').at(-1).options.body.export_id,id,'UUID export préservé');

  // Le clic administrateur réinspecte les identifiants et les statuts
  // de décisions même après une éventuelle altération du DOM.
  for(const dataset of [
    {confirmCase:malicious},{openCase:malicious},{verifyRequest:malicious},
    {exportAction:'delete_all',exportId:id},
    {exportAction:'generate',exportId:malicious},
    {resolveContest:'unknown'},
    {cleanupTask:id,cleanupStatus:'purge'}
  ]){
    const n=calls.length;
    await listeners.click({target:{closest(){return {dataset}}}});
    eq(calls.length,n,'Aucune RPC ne doit traiter une action HTML hostile');
  }
  const page=read('admin/sinjira/heritage.html');
  yes(page.includes('sinjira-admin-life-story-v24-5-2.js?v=24.5.2-secure-delivery'),
    'Page admin charge le nouveau module après publication');

  console.log('PASS: '+assertions+' gardes vérifiés sur la vraie console héritage: UUID, consentements, jetons de 256 bits et actions DOM.');
}
test().catch(error=>{console.error(error);process.exitCode=1});
