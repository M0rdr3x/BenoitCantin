#!/usr/bin/env node
'use strict';
// Le code JS de modération réellement déployable est exécuté dans une VM,
// avec des réponses Edge synthétiques et aucune session ou donnée réelle.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(ROOT,p),'utf8');
const original=read('assets/js/sinjira-admin-social-v20.js');
const boot=original.indexOf('\n(async()=>{try{await load();}');
assert.ok(boot>0,'Point de démarrage de modération absent');
const source=original.slice(0,boot).replace(/^import[^\n]*\n/gm,'')+
  '\nglobalThis.__moderation={load,reportCard,appealCard,validDecisionPayload,safeModerationId};';
const reportId='123e4567-e89b-42d3-a456-426614174000';
const datingId='223e4567-e89b-42d3-a456-426614174000';
const appealId='323e4567-e89b-42d3-a456-426614174000';
const malicious='"><img src=x onerror=alert(1)>';
let checks=0;
function eq(actual,expected,why){assert.equal(actual,expected,why);checks++}
function yes(value,why){assert.ok(value,why);checks++}
function notIn(text,value,why){yes(!text.includes(value),why)}
const escapeHtml=x=>String(x??'').replace(/[&<>"']/g,v=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
})[v]);
class FakeCard {
  constructor(id,kind,html){
    this.dataset={[kind]:id};
    this.html=html;
    this.inputs={
      '[data-policy-rule]':{value:'Règles de sécurité de la communauté'},
      '[data-statement]':{value:'Cette décision réversible a été vérifiée par un administrateur humain.'},
      '[data-urgency]':{value:'standard'},
      '[data-review-reason]':{value:'Une révision humaine motivée et complète.'}
    };
    this.buttons={};
    for(const name of ['resolve','restrict','suspend','uphold','reverse']){
      if(html.includes('data-'+name))this.buttons['[data-'+name+']']={onclick:null};
    }
  }
  querySelector(selector){return this.buttons[selector]||this.inputs[selector]||null}
}
class FakeList {
  constructor(){this.value='';this.cards=[]}
  get innerHTML(){return this.value}
  set innerHTML(s){
    this.value=String(s);
    this.cards=[];
    const rx=/<article\b[^>]*\bdata-(report|appeal)="([^"]*)"[^>]*>[\s\S]*?<\/article>/g;
    for(const match of this.value.matchAll(rx))this.cards.push(new FakeCard(match[2],match[1],match[0]));
  }
  querySelectorAll(selector){
    if(selector==='[data-report]')return this.cards.filter(c=>c.dataset.report!==undefined);
    if(selector==='[data-appeal]')return this.cards.filter(c=>c.dataset.appeal!==undefined);
    return [];
  }
  find(id){return this.cards.find(c=>c.dataset.report===id||c.dataset.appeal===id)}
}
const reportList=new FakeList(),appealList=new FakeList();
const reportCount={textContent:''},suspendCount={textContent:''},appealCount={textContent:''};
const panel={querySelector(selector){
  if(selector==='[data-social-appeal-count]')return appealCount;
  if(selector==='[data-social-appeal-list]')return appealList;
  if(selector==='.admin-stat-grid')return null;
  return null;
}};
const document={querySelector(selector){
  return ({
    '[data-admin-panel="social-moderation"] article':panel,
    '[data-social-report-count]':reportCount,
    '[data-social-suspension-count]':suspendCount,
    '[data-social-report-list]':reportList
  })[selector]||null;
}};
const reports=[
  {id:malicious,network:'real',reason:'hate',created_at:'2026-11-09'},
  {id:reportId,network:'real',reason:'threats',created_at:'2026-11-09',snapshot:{}},
  {id:datingId,network:'dating',reason:'harassment',created_at:'2026-11-09',
    snapshot:{source:'dating',messages:[],message_counts:{reporter:2,other:3}}}
];
const appeals=[
  {id:malicious,appeal_text:'Faux appel',submitted_at:'2026-11-09'},
  {id:appealId,appeal_text:'Arguments du membre',submitted_at:'2026-11-09',
    decision:{action:'suspend_social',policy_rule:'Règles',statement_of_reasons:'Motif initial'}}
];
const calls=[],alerts=[];
let nextFailure=false;
const supabase={functions:{async invoke(_name,{body}){
  calls.push(body);
  if(nextFailure){nextFailure=false;return {data:null,error:{message:'SESSION_SECRET_PRIVATE'}}}
  if(body.action==='dashboard')return {data:{ok:true,dashboard:{
    open_reports:3,active_suspensions:1,pending_appeals:2
  }},error:null};
  if(body.action==='list_reports')return {data:{ok:true,reports},error:null};
  if(body.action==='list_appeals')return {data:{ok:true,appeals},error:null};
  return {data:{ok:true},error:null};
}}};
const context=vm.createContext({
  getSupabase(){return supabase},escapeHtml,
  document,confirm(){return true},
  alert(message){alerts.push(String(message))},
  console:{error(){throw Error('Aucune erreur privée ne doit être journalisée')}},
  Date,Promise,Number,String,Array,Set,Map
});
vm.runInContext(source,context,{filename:'sinjira-admin-social-v20.js',timeout:2000});
const api=context.__moderation;
const countAction=name=>calls.filter(x=>x.action===name).length;
async function test(){
  eq(api.safeModerationId(reportId),reportId,'UUID valide autorisé');
  for(const x of [malicious,null,undefined,12,{},'javascript:alert(1)',reportId+' onclick="x']){
    eq(api.safeModerationId(x),'','Identifiant hostile rejeté');
  }
  await api.load();
  eq(reportList.cards.length,2,'Signalement avec ID malformé non rendu');
  eq(appealList.cards.length,1,'Appel avec ID malformé non rendu');
  notIn(reportList.innerHTML,'<img','Aucun fragment malveillant dans les signalements');
  notIn(appealList.innerHTML,'Faux appel','Appel malformé non rendu');
  yes(reportList.find(datingId).querySelector('[data-restrict]')===null,
    'Aucun masquage de contenu offert pour signalement Rencontres');
  yes(reportList.find(reportId).querySelector('[data-restrict]')!==null,
    'Option de masquage public conservée');

  const card=reportList.find(reportId);
  const originalCardId=card.dataset.report;
  card.dataset.report=datingId;
  const before=countAction('resolve_report');
  await card.querySelector('[data-resolve]').onclick();
  eq(countAction('resolve_report'),before,'Modification post-rendu de data-report rejetée');
  card.dataset.report=originalCardId;

  const restrict=card.querySelector('[data-restrict]');
  const statement=card.inputs['[data-statement]'];
  const policy=card.inputs['[data-policy-rule]'];
  const urgency=card.inputs['[data-urgency]'];
  for(const [property,value] of [
    [statement,'court'],
    [statement,'x'.repeat(4001)],
    [policy,'x'.repeat(241)],
    [policy,''],
    [urgency,'super-admin']
  ]){
    const previous=property.value;
    property.value=value;
    const prior=countAction('restrict_reported_content');
    await restrict.onclick();
    eq(countAction('restrict_reported_content'),prior,'Motif ou urgence invalide accepté');
    property.value=previous;
  }
  await restrict.onclick();
  eq(countAction('restrict_reported_content'),1,'Masquage humain valide transmis');
  const payload=calls.filter(x=>x.action==='restrict_reported_content')[0];
  eq(payload.report_id,reportId,'Masquage lié au signalement chargé');
  eq(payload.urgency,'standard','Urgence explicitement autorisée');

  const suspend=reportList.find(reportId).querySelector('[data-suspend]');
  await suspend.onclick();
  eq(countAction('suspend_reported_user'),1,'Suspension valide conservée');
  eq(calls.find(x=>x.action==='suspend_reported_user').days,7,'Suspension limitée à 7 jours');

  const resolve=reportList.find(reportId).querySelector('[data-resolve]');
  await resolve.onclick();
  eq(countAction('resolve_report'),1,'Résolution légitime conservée');

  let appeal=appealList.find(appealId);
  const reason=appeal.inputs['[data-review-reason]'];
  for(const value of ['court','x'.repeat(4001)]){
    reason.value=value;
    const n=countAction('review_appeal');
    await appeal.querySelector('[data-reverse]').onclick();
    eq(countAction('review_appeal'),n,'Révision hors limites rejetée');
  }
  reason.value='La révision suit une analyse humaine complète.';
  appeal.dataset.appeal=reportId;
  await appeal.querySelector('[data-uphold]').onclick();
  eq(countAction('review_appeal'),0,'Altération de data-appeal refusée');
  appeal.dataset.appeal=appealId;
  await appeal.querySelector('[data-reverse]').onclick();
  eq(countAction('review_appeal'),1,'Révision humaine valide conservée');
  eq(calls.find(x=>x.action==='review_appeal').outcome,'reversed',
    'Décision de révision attendue');

  nextFailure=true;
  const current=reportList.find(reportId);
  const beforeError=alerts.length;
  // Forcer un échec Edge sur une décision administrative réelle.
  await current.querySelector('[data-resolve]').onclick();
  eq(alerts.length,beforeError+1,'Échec RPC annoncé sans fuite brute');
  notIn(alerts.at(-1),'SESSION_SECRET_PRIVATE','Message privé non exposé');

  const page=read('admin/sinjira/index.html');
  yes(page.includes('sinjira-admin-social-v20.js?v=20.1-security'),
    'Version sécurisée de modération réellement importée par la page');
  notIn(original,"console.error('[SINJIRA admin moderation]',e)",
    'Échec de chargement privé ne doit plus être journalisé tel quel');
  console.log('PASS: '+checks+' assertions des vraies fonctions de modération, appels, sanctions et résistances DOM.');
}
test().catch(e=>{console.error(e);process.exitCode=1});
