#!/usr/bin/env node
// Exécute les vrais blocs d'administration sans Supabase ni données réelles.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { isCanonicalRegistrySourcePhotoPath as validPhoto } from '../supabase/functions/_shared/registry-photo-ownership.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const edge=readFileSync(resolve(ROOT,'supabase/functions/admin-sinjira-v18/index.ts'),'utf8');
const questionnaire=readFileSync(resolve(ROOT,'supabase/functions/submit-character-questionnaire/index.ts'),'utf8');
const userA='11111111-1111-4111-8111-111111111111';
const userB='22222222-2222-4222-8222-222222222222';
const objectId='33333333-3333-4333-8333-333333333333';
const photoA=userA+'/'+objectId+'.webp';
const photoB=userB+'/'+objectId+'.webp';

function extract(source,from,until){
  const i=source.indexOf(from),j=source.indexOf(until,i);
  assert.ok(i>=0&&j>i,'Bloc réel introuvable: '+from);
  return source.slice(i,j);
}
let uploader=extract(questionnaire,'function isCanonicalRegistryPhotoPath(', '\n// Une violation UNIQUE');
const signature='function isCanonicalRegistryPhotoPath(raw:unknown,userId:string):boolean';
assert.equal(uploader.split(signature).length-1,1);
uploader=uploader.replace(signature,'function isCanonicalRegistryPhotoPath(raw,userId)');
const uploadValid=new Function(uploader+'\nreturn isCanonicalRegistryPhotoPath;')();

const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const listSource=extract(edge,"if(a==='list_submissions'){","if(a==='create_manual_character'){");
const purgeSource=extract(edge,"if(a==='purge_submission_source'){","if(a==='list_characters'){");
const listHandler=new AsyncFunction('s','privateJson','isCanonicalRegistrySourcePhotoPath',
  "const a='list_submissions';\n"+listSource+"\nthrow new Error('NO_RESPONSE');");
const purgeHandler=new AsyncFunction('s','b','user','audit','privateJson','isCanonicalRegistrySourcePhotoPath',
  "const a='purge_submission_source';\n"+purgeSource+"\nthrow new Error('NO_RESPONSE');");
const privateJson=(data,status=200)=>new Response(JSON.stringify(data),
  {status,headers:{'Content-Type':'application/json','Cache-Control':'private, no-store, max-age=0'}});

function fakeService(records=[],record=null,storageError=false){
  const calls=[];
  return {calls,service:{
    storage:{from(bucket){
      assert.equal(bucket,'sinjira-character-sources');
      return {
        async createSignedUrl(path,seconds){
          calls.push(['sign',path,seconds]);
          return {data:{signedUrl:'https://example.invalid/signed'}};
        },
        async remove(paths){
          calls.push(['remove',paths]);
          return {error:storageError?{code:'FAULT'}:null};
        }
      };
    }},
    from(table){
      assert.equal(table,'character_submissions');
      return {
        select(fields){calls.push(['select',fields]);return this;},
        order(){return Promise.resolve({data:records,error:null});},
        eq(column,id){calls.push(['eq',column,id]);return this;},
        single(){return Promise.resolve({data:record,error:null});},
        update(fields){
          calls.push(['update',fields]);
          return {eq(column,id){
            calls.push(['updateWhere',column,id]);
            return Promise.resolve({error:null});
          }};
        },
      };
    }
  }};
}
const invalid=[
  photoB,userA+'/../'+objectId+'.webp',userA+'//'+objectId+'.webp',
  userA+'/'+objectId+'.pdf',userA+'/'+objectId+'.WEBP',
  userA+'/'+objectId+'%2ewebp',userA+'/'+objectId+'.webp?x=1',
  userA+'/'+objectId+'.webp/next','/'+photoA,'https://example.org/'+photoA,
  null,5,{},['x'], '', userA+'/'.concat('x'.repeat(120),'.jpg')
];

test('garde et validateur upload acceptent uniquement les photos du propriétaire',()=>{
  for(const ext of ['jpg','png','webp','avif','gif']){
    const path=userA+'/'+objectId+'.'+ext;
    assert.equal(validPhoto(path,userA),true);
    assert.equal(uploadValid(path,userA),true);
    assert.equal(validPhoto(path,userB),false);
  }
  for(const path of invalid){
    assert.equal(validPhoto(path,userA),false,'garde admin: '+JSON.stringify(path));
    assert.equal(uploadValid(path,userA),false,'garde upload: '+JSON.stringify(path));
  }
  assert.equal(validPhoto(photoA,'invalid-id'),false);
});

test('la liste signe les seules photos appartenant au compte de chaque dossier',async()=>{
  const rows=[
    {id:'a',user_id:userA,photo_path:photoA},
    {id:'b',user_id:userA,photo_path:photoB},
    {id:'c',user_id:userB,photo_path:photoB},
    {id:'d',user_id:userA,photo_path:null},
  ];
  const {service,calls}=fakeService(rows);
  const res=await listHandler(service,privateJson,validPhoto);
  assert.equal(res.status,200);
  assert.equal(res.headers.get('Cache-Control'),'private, no-store, max-age=0');
  const p=await res.json();
  assert.deepEqual(p.submissions.map(x=>Boolean(x.photo_url)),[true,false,true,false]);
  assert.deepEqual(calls.filter(c=>c[0]==='sign'),[['sign',photoA,600],['sign',photoB,600]]);
});

test('aucune URL signée pour un chemin incohérent ou ancien',async()=>{
  const rows=invalid.map((photo_path,i)=>({id:String(i),user_id:userA,photo_path}));
  const {service,calls}=fakeService(rows);
  const p=await (await listHandler(service,privateJson,validPhoto)).json();
  assert.ok(p.submissions.every(x=>x.photo_url===null));
  assert.equal(calls.filter(c=>c[0]==='sign').length,0);
});

async function attempt(record,confirmed=true,storageError=false){
  const {service,calls}=fakeService([],record,storageError);
  const audits=[];
  const promise=purgeHandler(service,
    {author_confirmed_source_purge:confirmed,submission_id:'record-1'},
    {id:'admin-id'},async(...args)=>audits.push(args),privateJson,validPhoto);
  return {promise,calls,audits};
}

test('aucune suppression ni audit sur chemin d’un autre compte ou non canonique',async()=>{
  for(const path of invalid.filter(Boolean)){
    const {promise,calls,audits}=await attempt({user_id:userA,photo_path:path,source_purged_at:null});
    await assert.rejects(promise,e=>e?.message==='SOURCE_PURGE_PATH_INVALID');
    assert.equal(calls.some(x=>x[0]==='remove'||x[0]==='update'),false);
    assert.equal(audits.length,0);
  }
});

test('la purge légitime enlève Storage avant nettoyage des données privées',async()=>{
  const {promise,calls,audits}=await attempt({user_id:userA,photo_path:photoA,source_purged_at:null});
  const res=await promise;
  assert.equal((await res.json()).ok,true);
  const i=calls.findIndex(x=>x[0]==='remove'),j=calls.findIndex(x=>x[0]==='update');
  assert.ok(i>=0&&j>i);
  assert.deepEqual(calls[i],['remove',[photoA]]);
  assert.equal(calls[j][1].source_payload,null);
  assert.equal(calls[j][1].photo_path,null);
  assert.ok(typeof calls[j][1].source_purged_at==='string');
  assert.equal(audits.length,1);
});

test('absence de photo autorisée seulement pour le nettoyage du payload',async()=>{
  const {promise,calls}=await attempt({user_id:userA,photo_path:null,source_purged_at:null});
  assert.equal((await (await promise).json()).ok,true);
  assert.equal(calls.some(x=>x[0]==='remove'),false);
  assert.equal(calls.some(x=>x[0]==='update'),true);
});

test('confirmation absente, purge antérieure et échec Storage bloquent le flux',async()=>{
  const record={user_id:userA,photo_path:photoA,source_purged_at:null};
  const noConsent=await attempt(record,false);
  await assert.rejects(noConsent.promise,e=>e?.message==='SOURCE_PURGE_CONFIRMATION_REQUIRED');
  assert.equal(noConsent.calls.length,0);
  const already=await attempt({...record,source_purged_at:'2026-11-15T01:00:00Z'});
  await assert.rejects(already.promise,e=>e?.message==='SOURCE_PURGED');
  assert.equal(already.calls.some(x=>x[0]==='remove'),false);
  const failed=await attempt(record,true,true);
  await assert.rejects(failed.promise,e=>e?.message==='SOURCE_PURGE_STORAGE_FAILED');
  assert.equal(failed.calls.some(x=>x[0]==='update'),false);
});
