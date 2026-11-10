#!/usr/bin/env node
'use strict';
// Charge et exécute la VRAIE fonction Edge createDecision en isolant uniquement
// les annotations de type TS de sa signature. Aucun service Supabase réel.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const edge=fs.readFileSync(path.join(root,'supabase/functions/admin-social-v20/index.ts'),'utf8');
const start=edge.indexOf('async function createDecision(');
const end=edge.indexOf('\nasync function listAppeals(',start);
assert.ok(start>=0&&end>start,'Fonction Edge createDecision attendue');
let implementation=edge.slice(start,end);
const signature="async function createDecision(s:any,adminId:string,r:any,b:any,action:'hide_content'|'suspend_social'){";
assert.ok(implementation.startsWith(signature),'Signature Edge réelle modifiée');
implementation=implementation.replace(signature,'async function createDecision(s,adminId,r,b,action){')
  .replace('const row:any=', 'const row=');
assert.ok(!implementation.includes('const row:any'),'Annotations TS non éliminées');
let checks=0;
function eq(a,b,reason){assert.equal(a,b,reason);checks++}
function truthy(v,reason){assert.ok(v,reason);checks++}
const uuid='123e4567-e89b-42d3-a456-426614174000';
const author='223e4567-e89b-42d3-a456-426614174000';
function context({
  reportStatus='open',subject=author,action='suspend_social',
  days=7,closed=true,decisionError=null,suspensionError=null,reportError=null
}={}){
  const history=[];
  const client={
    schema(name){eq(name,'private','Décision de modération en schéma privé');return this;},
    from(name){
      return {
        insert(payload){
          history.push({op:'insert',table:name,payload});
          return {select(fields){
            eq(fields,'id,ends_at','La décision retourne seulement identifiant et date');
            return {async single(){return {data:{id:uuid,ends_at:payload.ends_at},error:decisionError}}}
          }};
        },
        upsert:async(payload)=>{history.push({op:'upsert',table:name,payload});return {error:suspensionError}},
        update(payload){
          history.push({op:'update',table:name,payload,filters:[]});
          const record=history[history.length-1];
          return {
            eq(k,v){record.filters.push([k,v]);return this},
            select(columns){eq(columns,'id','Uniquement la référence de rapport retournée');return this},
            async maybeSingle(){return {data:closed?{id:uuid}:null,error:reportError}}
          };
        }
      };
    }
  };
  const targetTables={real:{post:['social_real_posts','user_id']}};
  const ctx=vm.createContext({
    reportTargetUser:async()=>{history.push({op:'canonical_subject'});return subject},
    targetSnapshot:async()=>{history.push({op:'target_snapshot'});return {id:uuid}},
    policyAndStatement:()=>({rule:'Règles de sécurité',statement:'Décision humaine réversible et documentée.'}),
    targetTables,
    notifyDecision:async()=>{history.push({op:'notify'})},
    Date,Error,Number
  });
  vm.runInContext(implementation+'\nglobalThis.testCreateDecision=createDecision;',ctx,{timeout:2000});
  const r={id:uuid,status:reportStatus,network:'real',target_type:'post',target_id:uuid,
    reason:'threats',created_at:'2026-11-09',snapshot:{}};
  const body={days};
  return {perform:()=>ctx.testCreateDecision(client,author,r,body,action),
    history,r,body,subject};
}
const count=(history,op)=>history.filter(x=>x.op===op).length;
async function rejected(run,code,label){
  let caught;
  try{await run.perform()}catch(e){caught=e};
  truthy(caught,label+' doit être refusé');
  eq(String(caught.message),code,label+' code attendu');
  eq(count(run.history,'insert'),0,label+' ne doit jamais créer de sanction');
  eq(count(run.history,'upsert'),0,label+' ne doit jamais créer de suspension');
  eq(count(run.history,'notify'),0,label+' ne doit pas notifier');
}
async function main(){
  await rejected(context({reportStatus:'resolved'}),'REPORT_NOT_OPEN','Rapport déjà résolu');
  await rejected(context({reportStatus:'archived'}),'REPORT_NOT_OPEN','Rapport archivé');
  await rejected(context({subject:null}),'TARGET_USER_NOT_FOUND','Cible supprimée');
  await rejected(context({subject:undefined}),'TARGET_USER_NOT_FOUND','Cible introuvable');
  for(const days of [0,-1,1.5,366,'7',null,NaN,Infinity,-Infinity]){
    await rejected(context({days}),'INVALID_SUSPENSION_DURATION',
      'Durée de suspension invalide '+String(days));
  }
  const notReversible=context({action:'hide_content'});
  notReversible.r.target_type='profile';
  await rejected(notReversible,'CONTENT_TARGET_NOT_REVERSIBLE','Contenu non masquable');

  const normal=context({days:7});
  const result=await normal.perform();
  eq(result.id,uuid,'La sanction légitime produit une décision');
  eq(count(normal.history,'insert'),1,'Insertion unique');
  eq(count(normal.history,'upsert'),1,'Suspension unique');
  eq(count(normal.history,'update'),1,'Signalement clos');
  eq(count(normal.history,'notify'),1,'Notification d’une sanction valide');
  const firstInsert=normal.history.findIndex(x=>x.op==='insert');
  const canonical=normal.history.findIndex(x=>x.op==='canonical_subject');
  truthy(canonical>=0&&canonical<firstInsert,'Identité validée AVANT écriture');
  const close=normal.history.find(x=>x.op==='update');
  truthy(close.filters.some(x=>x[0]==='status'&&x[1]==='open'),
    'Clôture conditionnelle sur un rapport encore ouvert');

  const defaultDays=context({});
  delete defaultDays.body.days;
  await defaultDays.perform();
  eq(count(defaultDays.history,'insert'),1,'Sept jours par défaut conservés');
  const hide=context({action:'hide_content'});
  await hide.perform();
  eq(count(hide.history,'insert'),1,'Masquage de contenu connu conservé');
  eq(count(hide.history,'upsert'),0,'Masquage ne suspend aucun compte');

  const closed=context({closed:false});
  let error;
  try{await closed.perform()}catch(e){error=e}
  eq(error?.message,'REPORT_NOT_OPEN','Échec de fermeture détecté et non présenté comme succès');
  eq(count(closed.history,'notify'),0,'Aucune notification en cas de fermeture non confirmée');

  const sourceMarkers=[
    "const reference=a==='review_appeal'?b.appeal_id:b.report_id",
    "throw new Error('INVALID_MODERATION_REFERENCE')",
    ".eq('id',b.report_id).eq('status','open').maybeSingle()",
    "if(!r)throw new Error('REPORT_NOT_OPEN')",
    "if(!closed)throw new Error('REPORT_NOT_OPEN')",
    "code:'INVALID_MODERATION_INPUT'",
    "code:'REPORT_NOT_OPEN'",
    "code:'TARGET_USER_NOT_FOUND'"
  ];
  for(const needle of sourceMarkers)truthy(edge.includes(needle),'Garde serveur absent: '+needle);
  truthy(!edge.includes("Math.max(1,Math.min(Number(b.days||7),365))"),
    'Ancienne correction silencieuse de durée non désirée');

  console.log('PASS: '+checks+' assertions sur la fonction Edge réelle : aucune décision avant identité vérifiée, durées contrôlées et état de rapport.');
  console.log('NOTE: absence de transaction SQL atomique ; une concurrence pendant des écritures multi-tables reste à traiter séparément.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
