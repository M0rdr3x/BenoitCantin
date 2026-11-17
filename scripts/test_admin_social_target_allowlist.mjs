#!/usr/bin/env node
// Tests des VRAIES fonctions de sélection SQL et de décision admin-social-v20.
// Toutes les données et fonctions Supabase sont simulées : aucun secret ni réseau.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const source=readFileSync(resolve(root,'supabase/functions/admin-social-v20/index.ts'),'utf8');

function extract(startToken,endToken){
  const start=source.indexOf(startToken),end=source.indexOf(endToken,start);
  assert.ok(start>=0&&end>start,'Bloc source réel introuvable: '+startToken);
  return source.slice(start,end);
}
let targets=extract('const targetTables:any=', 'async function canonicalUser(');
for(const [oldValue,newValue] of [
  ['const targetTables:any=','const targetTables='],
  ['function moderationTargetTable(network:unknown,targetType:unknown):[string,string]|null',
   'function moderationTargetTable(network,targetType)'],
  ['pair as [string,string]', 'pair']
]){
  assert.equal(targets.split(oldValue).length-1,1,'Annotation du bloc cible modifiée: '+oldValue);
  targets=targets.replace(oldValue,newValue);
}
let snapshot=extract('async function targetSnapshot(','function policyAndStatement(');
const oldSnapshot='async function targetSnapshot(s:any,r:any)';
assert.equal(snapshot.split(oldSnapshot).length-1,1);
snapshot=snapshot.replace(oldSnapshot,'async function targetSnapshot(s,r)');

let decision=extract('async function createDecision(', 'async function listAppeals(');
for(const [oldValue,newValue] of [
  ["async function createDecision(s:any,adminId:string,r:any,b:any,action:'hide_content'|'suspend_social')",
   'async function createDecision(s,adminId,r,b,action)'],
  ['const row:any=', 'const row=']
]){
  assert.equal(decision.split(oldValue).length-1,1,'Annotation du bloc décision modifiée: '+oldValue);
  decision=decision.replace(oldValue,newValue);
}
function runtime({subject='subject-123',onSubject=()=>{}}={}){
  const notifications=[];
  const real=new Function(
    'reportTargetUser','policyAndStatement','notifyDecision',
    targets+'\n'+snapshot+'\n'+decision+'\nreturn {moderationTargetTable,targetSnapshot,createDecision};'
  )(
    async()=>{onSubject();return subject;},
    ()=>({rule:'Règles communautaires',statement:'Décision humaine validée par le modérateur'}),
    async(_service,id,decisionId)=>{notifications.push({id,decisionId});}
  );
  return {...real,notifications};
}
const valid={
  real:{
    post:['social_real_posts','user_id'],
    comment:['social_real_comments','user_id'],
    message:['social_real_messages','sender_user_id'],
  },
  character:{
    post:['social_character_posts','user_id'],
    comment:['social_character_comments','user_id'],
    message:['social_character_messages','sender_user_id'],
  }
};
const unsafe=['__proto__','constructor','prototype','toString','valueOf',
  'hasOwnProperty','isPrototypeOf','__defineGetter__','__lookupSetter__',
  'Post','message/other','',null,undefined,0,{},[]];

function mockedStorage(){
  const calls=[];
  const service={
    from(table){
      calls.push(['from',table]);
      if(table==='social_reports'){
        return {
          update(update){calls.push(['update-report',update]);return this;},
          async eq(key,value){calls.push(['update-report-where',key,value]);return {error:null};},
        };
      }
      return {
        select(cols){calls.push(['select',cols]);return this;},
        eq(key,value){calls.push(['eq',key,value]);return this;},
        async maybeSingle(){calls.push(['lookup']);return {data:{sample:true},error:null};},
      };
    },
    schema(schema){
      calls.push(['schema',schema]);
      assert.equal(schema,'private');
      return {
        from(table){
          assert.equal(table,'moderation_decisions');
          return {
            insert(row){
              calls.push(['insert',row]);
              return {
                select(){
                  return {
                    async single(){return {data:{id:'decision-1',ends_at:null},error:null};}
                  };
                },
              };
            }
          };
        },
      };
    }
  };
  return {service,calls};
}

test('six combinaisons réseau/type réelles sont liées aux tables SQL attendues',()=>{
  const {moderationTargetTable}=runtime();
  for(const [network,types] of Object.entries(valid)){
    for(const [type,pair] of Object.entries(types)){
      assert.deepEqual(moderationTargetTable(network,type),pair,network+'/'+type);
    }
  }
});

test('les propriétés de prototype et tous les types non répertoriés sont refusés',()=>{
  const {moderationTargetTable}=runtime();
  for(const item of unsafe){
    for(const field of ['post','comment','message',...unsafe.slice(0,6)]){
      assert.equal(moderationTargetTable(item,field),null,
        'réseau inattendu '+String(item)+'/'+field);
    }
    for(const network of ['real','character']){
      assert.equal(moderationTargetTable(network,item),null,
        'type inattendu '+network+'/'+String(item));
    }
  }
  assert.equal(Object.prototype.sample,undefined);
  assert.equal(Object.prototype.count,undefined);
});

test('snapshot SQL réel : uniquement les tables autorisées sont interrogées',async()=>{
  const {moderationTargetTable,targetSnapshot}=runtime();
  for(const [network,types] of Object.entries(valid)){
    for(const [type,pair] of Object.entries(types)){
      const {service,calls}=mockedStorage();
      const result=await targetSnapshot(service,{network,target_type:type,target_id:'id-1'});
      assert.deepEqual(result,{sample:true});
      assert.deepEqual(calls[0],['from',pair[0]]);
      assert.equal(calls.find(x=>x[0]==='select')[1],'*');
    }
  }
  for(const item of unsafe){
    for(const report of [
      {network:item,target_type:'post',target_id:'id-1'},
      {network:'real',target_type:item,target_id:'id-1'},
    ]){
      const {service,calls}=mockedStorage();
      assert.equal(await targetSnapshot(service,report),null);
      assert.equal(calls.length,0,'aucune requête SQL sur cible non répertoriée');
    }
  }
});

test('une modération de contenu invalide est bloquée avant toute lecture ou écriture',async()=>{
  const {createDecision}=runtime({onSubject:()=>{throw new Error('IDENTITY_LOOKUP_SHOULD_NOT_RUN');}});
  for(const item of unsafe){
    for(const report of [
      {network:item,target_type:'post'},
      {network:'real',target_type:item},
    ]){
      const {service,calls}=mockedStorage();
      await assert.rejects(
        () =>createDecision(service,'admin-1',
          {...report,id:'report-1',target_id:'content-1',snapshot:{},reason:'test'},
          {},'hide_content'),
        error=>error?.message==='CONTENT_TARGET_NOT_REVERSIBLE'
      );
      assert.equal(calls.length,0,'aucun effet de bord avant refus');
    }
  }
});

test('une suspension sans identité canonique ne crée pas de décision SQL orpheline',async()=>{
  const {createDecision}=runtime({subject:null});
  const {service,calls}=mockedStorage();
  await assert.rejects(
    ()=>createDecision(service,'admin-1',{
      id:'report-1',network:'real',target_type:'post',target_id:'content-1',
      snapshot:{},reason:'test',created_at:'2026-11-16T00:00:00Z',
    },{days:7},'suspend_social'),
    error=>error?.message==='TARGET_USER_NOT_FOUND'
  );
  assert.deepEqual(calls,[],'la suspension échoue avant toute écriture SQL');
});

test('une décision réversible légitime conserve ses écritures et notification',async()=>{
  const rt=runtime();
  const {service,calls}=mockedStorage();
  const decision=await rt.createDecision(service,'admin-1',{
    id:'report-1',network:'real',target_type:'post',target_id:'content-1',
    snapshot:{},reason:'test',created_at:'2026-11-16T00:00:00Z',
  },{},'hide_content');
  assert.deepEqual(decision,{id:'decision-1',ends_at:null});
  assert.ok(calls.some(x=>x[0]==='from'&&x[1]==='social_real_posts'));
  assert.ok(calls.some(x=>x[0]==='insert'&&x[1].decision_source==='human_admin'));
  assert.ok(calls.some(x=>x[0]==='update-report'));
  assert.equal(rt.notifications.length,1);
});

test('une suspension légitime conserve la décision et la sanction',async()=>{
  const rt=runtime();
  const {service:base,calls}=mockedStorage();
  const service={...base,from(name){
    if(name==='social_suspensions'){
      return {upsert(row){calls.push(['upsert-suspension',row]);return Promise.resolve({error:null});}};
    }
    return base.from(name);
  }};
  const decision=await rt.createDecision(service,'admin-1',{
    id:'report-1',network:'character',target_type:'post',target_id:'content-1',
    snapshot:{},reason:'test',created_at:'2026-11-16T00:00:00Z',
  },{days:7},'suspend_social');
  assert.equal(decision.id,'decision-1');
  assert.ok(calls.some(x=>x[0]==='upsert-suspension'&&x[1].user_id==='subject-123'));
  assert.equal(rt.notifications.length,1);
});
