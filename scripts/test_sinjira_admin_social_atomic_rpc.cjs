#!/usr/bin/env node
'use strict';
// Exerce les VRAIES fonctions de l'Edge de modération dans une VM Node,
// avec RPC Supabase purement simulées et aucun secret ni compte réel.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(root,'supabase/functions/admin-social-v20/index.ts'),'utf8');
const start=src.indexOf('function policyAndStatement(');
const end=src.indexOf('Deno.serve(async(req)=>{',start);
assert.ok(start>=0&&end>start,'Fonctions serveur de modération atomique absentes');
let code=src.slice(start,end);
code=code.replace(/:any\b/g,'').replace(/:string\b/g,'').replace(/:never\b/g,'')
 .replace("action:'resolve_report'|'hide_content'|'suspend_social'","action")
 .replace("action:'hide_content'|'suspend_social'","action");
const context=vm.createContext({String,Number,Set,Error,Array,Promise});
vm.runInContext(code+'\nglobalThis.__atomic={atomicModeration,createDecision,appealOverview,listAppeals,reviewAppeal};',
  context,{filename:'admin-social-v20/index.ts',timeout:3000});
const f=context.__atomic;
const admin='aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa';
const report='dddddddd-dddd-4ddd-dddd-dddddddddddd';
const appeal='ffffffff-ffff-4fff-ffff-ffffffffffff';
const decision='eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee';
const calls=[];
let responseMode='success';
const service={
  async rpc(name,args){
    calls.push({name,args});
    if(responseMode==='private-error')
      return {data:null,error:{message:'PRIVATE_SQL_STACK_AND_JWT'}};
    if(responseMode==='known-error')
      return {data:null,error:{message:'REPORT_NOT_OPEN'}};
    if(responseMode==='invalid-body')
      return {data:{ok:false,decision_id:decision},error:null};
    if(name==='sinjira_admin_moderate_atomic'){
      if(args.p_action==='resolve_report')
        return {data:{ok:true,resolved:true,report_id:args.p_report_id},error:null};
      return {data:{ok:true,decision_id:decision,until_at:'2026-11-17T03:00:00Z'},error:null};
    }
    if(name==='sinjira_admin_review_appeal_atomic'){
      return {data:{ok:true,decision_id:decision,appeal_id:appeal,
        outcome:args.p_outcome},error:null};
    }
    if(name==='sinjira_admin_appeals_overview')
      return {data:{pending_count:2,appeals:[{id:appeal,decision:{id:decision}}]},error:null};
    throw Error('RPC inattendue : '+name);
  },
  from(){throw Error('Accès direct aux tables interdit pour la modération')}
};
let count=0;
function eq(actual,expected,why){assert.equal(actual,expected,why);count++}
function yes(actual,why){assert.ok(actual,why);count++}
async function rejected(run,message,why){
  await assert.rejects(run,e=>{
    eq(e?.message,message,why);
    return true;
  });count++;
}
async function main(){
  yes(src.includes('const {user,service:s}=await requiredAdmin(req)'),
    'JWT administrateur et AAL2 avant RPC');
  yes(src.indexOf('const {user,service:s}=await requiredAdmin(req)')<
    src.indexOf('const b=await readLimitedJson(req)'),'auth avant lecture');
  yes(!src.includes(".schema('private').from("),
    'aucun CRUD direct sur tables privées dans l’Edge');
  yes(!src.includes(".from('social_suspensions').upsert("),
    'aucune écriture directe de suspension non atomique');
  yes(!src.includes(".from('social_reports').update("),
    'aucune clôture de signalement directe non atomique');
  for(const name of [
    'sinjira_admin_moderate_atomic',
    'sinjira_admin_review_appeal_atomic',
    'sinjira_admin_appeals_overview'
  ])yes(src.includes("s.rpc('"+name+"'"),'RPC publique attendue : '+name);

  const r={id:report,status:'open',network:'real',target_type:'post',reason:'threats',snapshot:{}};
  let result=await f.createDecision(service,admin,r,{
    policy_rule:'Sécurité communautaire',
    statement_of_reasons:'Mesure motivée par une révision humaine et réversible.'
  },'suspend_social');
  eq(result.id,decision,'décision serveur réelle renvoyée');
  eq(calls.at(-1).name,'sinjira_admin_moderate_atomic','sanction par la RPC atomique');
  eq(calls.at(-1).args.p_admin_id,admin,'identité admin issue du JWT');
  eq(calls.at(-1).args.p_report_id,report,'identifiant de signalement exact');
  eq(calls.at(-1).args.p_action,'suspend_social','action de suspension attendue');
  eq(calls.at(-1).args.p_days,7,'sept jours par défaut');
  eq(calls.at(-1).args.p_urgency,'standard','urgence standard conservée');
  eq(result.ends_at,'2026-11-17T03:00:00Z','date renvoyée par SQL');

  let before=calls.length;
  await rejected(()=>f.createDecision(service,admin,{...r,status:'resolved'}, {},'suspend_social'),
    'REPORT_NOT_OPEN','rapport clos refusé avant tout appel SQL');
  eq(calls.length,before,'aucune RPC pour un rapport fermé');

  await rejected(()=>f.createDecision(service,admin,{
    ...r,snapshot:{source:'dating'}
  },{},'hide_content'),'CONTENT_TARGET_NOT_REVERSIBLE',
  'aucun masquage non réversible de Rencontres');
  eq(calls.length,before,'aucune RPC en réseau privé Rencontres');

  for(const days of [0,-7,1.5,366,'7',null,Infinity]){
    await rejected(()=>f.createDecision(service,admin,r,{days},'suspend_social'),
      'INVALID_SUSPENSION_DURATION','durée non numérique entière et bornée : '+days);
    eq(calls.length,before,'aucune requête de sanction sur durée invalide');
  }
  for(const urgency of ['super-admin','HIGH',null,2]){
    await rejected(()=>f.createDecision(service,admin,r,{urgency},'suspend_social'),
      'INVALID_MODERATION_INPUT','niveau urgence altéré refusé');
    eq(calls.length,before,'aucune requête avec urgence hors contrat');
  }

  await f.createDecision(service,admin,r,{
    policy_rule:'Règle de sécurité',
    statement_of_reasons:'Contenu masqué après examen humain documenté.'
  },'hide_content');
  eq(calls.at(-1).args.p_action,'hide_content','masquage réversible atomique');
  eq(calls.at(-1).args.p_days,null,'pas de durée de suspension sur le masquage');

  const resolve=await f.atomicModeration(service,admin,report,'resolve_report');
  eq(resolve.resolved,true,'rapport clos via la même transaction SQL');
  eq(calls.at(-1).args.p_policy_rule,null,'pas de règle artificielle pour résolution');
  eq(calls.at(-1).args.p_statement,null,'pas de notification en résolution simple');

  const overview=await f.appealOverview(service,admin);
  eq(overview.pending_count,2,'nombre de dossiers privés exact');
  eq(overview.appeals.length,1,'lecture des appels sur RPC plutôt que CRUD');
  eq(calls.at(-1).name,'sinjira_admin_appeals_overview','liste via rôle serveur uniquement');
  eq(calls.at(-1).args.p_admin_id,admin,'filtre admin serveur sur liste');
  const list=await f.listAppeals(service,admin);
  eq(list.length,1,'retour JSON conservé pour console');

  before=calls.length;
  await rejected(()=>f.reviewAppeal(service,admin,{
    appeal_id:appeal,outcome:'delete_all',review_reason:'texte motivé suffisamment long'
  }),'INVALID_APPEAL_OUTCOME','décision d’appel arbitraire refusée');
  eq(calls.length,before,'aucune RPC sur décision d’appel arbitraire');
  await rejected(()=>f.reviewAppeal(service,admin,{
    appeal_id:appeal,outcome:'reversed',review_reason:'court'
  }),'APPEAL_REVIEW_REASON_LENGTH','motif trop court refusé');
  eq(calls.length,before,'aucune RPC avec motif trop court');

  const reviewed=await f.reviewAppeal(service,admin,{
    appeal_id:appeal,outcome:'reversed',
    review_reason:'Révision humaine fondée sur des documents vérifiés.'
  });
  eq(reviewed.outcome,'reversed','révision atomique renversée');
  eq(calls.at(-1).name,'sinjira_admin_review_appeal_atomic','revue via RPC dédiée');
  eq(calls.at(-1).args.p_appeal_id,appeal,'lien exact au dossier appel');
  eq(calls.at(-1).args.p_admin_id,admin,'admin transmis au RPC');

  responseMode='private-error';
  before=calls.length;
  await rejected(()=>f.atomicModeration(service,admin,report,'resolve_report'),
    'ATOMIC_MODERATION_FAILED','pile SQL et identité interne masquées');
  eq(calls.length,before+1,'échec SQL signalé une fois');
  await rejected(()=>f.appealOverview(service,admin),
    'ATOMIC_MODERATION_FAILED','erreur SQL privée de la liste masquée');
  responseMode='known-error';
  await rejected(()=>f.atomicModeration(service,admin,report,'resolve_report'),
    'REPORT_NOT_OPEN','erreur métier connue explicitement autorisée');
  responseMode='invalid-body';
  await rejected(()=>f.atomicModeration(service,admin,report,'resolve_report'),
    'ATOMIC_MODERATION_FAILED','réponse SQL malformée refusée');
  responseMode='success';

  console.log('PASS : '+count+' assertions sur les vraies fonctions Edge, 3 RPC service-only et refus de CRUD privé.');
}
main().catch(e=>{console.error(e);process.exitCode=1});
