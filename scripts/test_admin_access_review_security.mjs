#!/usr/bin/env node
import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {
  validProjectAccessReviewDecision,
  isReviewableProjectAccessRequest,
} from '../supabase/functions/_shared/project-access-review-guard.mjs';

const USER='123e4567-e89b-42d3-a456-426614174000';
const PROJECT='123e4567-e89b-42d3-a456-426614174001';
const REQUEST='123e4567-e89b-42d3-a456-426614174002';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const admin=readFileSync(resolve(root,'supabase/functions/admin-console/index.ts'),'utf8');
const start=admin.indexOf("    if(action==='review_access_request'){");
const end=admin.indexOf("    if(action==='list_users'){",start);
assert.ok(start>=0 && end>start,'Real review route must remain available');
const snippet=admin.slice(start,end);
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
// Compile and execute the actual review branch, without importing Deno or Supabase.
const review=new AsyncFunction(
  'action','body','service','user','privateJson','UUID_RE',
  'validProjectAccessReviewDecision','isReviewableProjectAccessRequest',
  snippet+"return {status:599,body:{error:'REVIEW_ACTION_NOT_REACHED'}};"
);
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
function request(status='pending',level='tester'){
  return {id:REQUEST,user_id:USER,project_id:PROJECT,requested_level:level,status,reviewed_by:null,reviewed_at:null,review_note:null};
}
function fake(record,opts={}){
  const events=[];
  let readCount=0;
  const database={row:record};
  const service={
    from(table){
      if(table==='project_access'){
        return {
          async upsert(payload,options){
            events.push({op:'grant',payload,options});
            return {error:opts.grantError?{code:'FAILED'}:null};
          }
        };
      }
      assert.equal(table,'access_requests','unexpected privileged table');
      const query={
        filters:{},
        action:'read',
        payload:null,
        select(){return this;},
        eq(key,value){this.filters[key]=value;return this;},
        update(value){this.action='update';this.payload=value;return this;},
        async maybeSingle(){return this.execute();},
        async execute(){
          if(this.action==='read'){
            readCount++;
            events.push({op:'read',filters:this.filters});
            return {data:database.row ? {...database.row}:null,error:opts.readError?{code:'READ_FAILED'}:null};
          }
          const before=database.row;
          if(opts.cancelBeforeUpdate && this.payload.status==='approved') database.row.status='cancelled';
          if(this.payload.status==='pending' && opts.rollbackError) return {data:null,error:{code:'ROLLBACK_FAILED'}};
          if(opts.transitionError && this.payload.status!=='pending')return {data:null,error:{code:'UPDATE_FAILED'}};
          const eligible=before && Object.entries(this.filters).every(([key,value])=>database.row[key]===value);
          events.push({op:this.payload.status==='pending'?'rollback':'transition',filters:this.filters,success:Boolean(eligible)});
          if(eligible) Object.assign(database.row,this.payload);
          return {data:eligible?{id:database.row.id}:null,error:null};
        },
        then(ok,fail){return this.execute().then(ok,fail);}
      };
      return query;
    }
  };
  return {service,events,database,getReadCount:()=>readCount};
}
async function run(record,body={request_id:REQUEST,decision:'approved'},opts={}){
  const h=fake(record,opts);
  const reply=await review('review_access_request',body,h.service,{id:USER},
    (body,status=200)=>({status,body}),UUID_RE,
    validProjectAccessReviewDecision,isReviewableProjectAccessRequest);
  return {reply,...h};
}

test('le helper accepte uniquement player/tester avec identité SQL UUID et état pending',()=>{
  for(const level of ['player','tester'])assert.equal(isReviewableProjectAccessRequest(request('pending',level)),true);
  for(const status of ['approved','refused','cancelled','completed',null,'PENDING']){
    assert.equal(isReviewableProjectAccessRequest(request(status)),false,String(status));
  }
  for(const level of ['admin','owner','account','',null,undefined]){
    assert.equal(isReviewableProjectAccessRequest(request('pending',level)),false,String(level));
  }
  for(const field of ['id','user_id','project_id']){
    assert.equal(isReviewableProjectAccessRequest({...request(),[field]:'../../../foreign'}),false,field);
  }
});

test('refuse les décisions inconnues, sans aucune requête ni modification',async()=>{
  for(const decision of ['pending','cancelled','admin','APPROVED','',null,{},true]){
    assert.equal(validProjectAccessReviewDecision(decision),false);
    const h=await run(request(),{request_id:REQUEST,decision});
    assert.equal(h.reply.status,400);
    assert.equal(h.events.length,0);
  }
});

test('approuve une demande pending en comparant le statut SQL avant le grant',async()=>{
  const h=await run(request());
  assert.equal(h.reply.status,200);
  assert.equal(h.database.row.status,'approved');
  assert.deepEqual(h.events.map(x=>x.op),['read','transition','grant']);
  assert.deepEqual(h.events[1].filters,{id:REQUEST,status:'pending'});
  assert.deepEqual(h.events[2].payload,{
    user_id:USER,project_id:PROJECT,access_level:'tester',granted_by:USER,source:'request'
  });
});

test('refuser une demande pending ne crée aucun accès',async()=>{
  const h=await run(request(),{request_id:REQUEST,decision:'refused'});
  assert.equal(h.reply.status,200);
  assert.equal(h.database.row.status,'refused');
  assert.deepEqual(h.events.map(x=>x.op),['read','transition']);
});

test('n approuve jamais les demandes annulées, refusées ni déjà approuvées',async()=>{
  for(const status of ['approved','refused','cancelled']){
    const h=await run(request(status));
    assert.equal(h.reply.status,409,status);
    assert.deepEqual(h.events.map(x=>x.op),['read'],status);
    assert.equal(h.database.row.status,status);
  }
});

test('ne redonne aucun droit à une demande annulée entre lecture et update',async()=>{
  const h=await run(request(),{request_id:REQUEST,decision:'approved'},{cancelBeforeUpdate:true});
  assert.equal(h.reply.status,409);
  assert.deepEqual(h.events.map(x=>x.op),['read','transition']);
  assert.equal(h.database.row.status,'cancelled');
  assert.equal(h.events[1].success,false);
});

test('refuse une demande dont le niveau SQL a été falsifié',async()=>{
  const h=await run(request('pending','admin'));
  assert.equal(h.reply.status,409);
  assert.deepEqual(h.events.map(x=>x.op),['read']);
});

test('un échec du grant tente un rollback, sans succès annoncé au client',async()=>{
  const h=fake(request(),{grantError:true});
  await assert.rejects(()=>review('review_access_request',{request_id:REQUEST,decision:'approved'},
    h.service,{id:USER},(body,status=200)=>({status,body}),UUID_RE,
    validProjectAccessReviewDecision,isReviewableProjectAccessRequest),
  {message:'ACCESS_REVIEW_GRANT_FAILED'});
  assert.deepEqual(h.events.map(x=>x.op),['read','transition','grant','rollback']);
  assert.equal(h.database.row.status,'pending');
});

test('une erreur SQL de transition est refusée avant tout grant',async()=>{
  const h=fake(request(),{transitionError:true});
  await assert.rejects(()=>review('review_access_request',{request_id:REQUEST,decision:'approved'},
    h.service,{id:USER},(body,status=200)=>({status,body}),UUID_RE,
    validProjectAccessReviewDecision,isReviewableProjectAccessRequest),
  {message:'ACCESS_REVIEW_TRANSITION_FAILED'});
  assert.equal(h.events.some(e=>e.op==='grant'),false);
});

test('le code source conserve AAL2, no-store et jamais de privilège fourni par le client',()=>{
  assert.ok(admin.includes('const {user,service}=await requiredAdmin(req);'));
  assert.ok(admin.includes("'Cache-Control':'private, no-store, max-age=0'"));
  assert.ok(snippet.indexOf(".eq('status','pending').select('id').maybeSingle()")<snippet.indexOf("service.from('project_access').upsert({"));
  assert.ok(snippet.includes('access_level:r.requested_level'));
  assert.ok(!snippet.includes('access_level:body.'));
  assert.ok(!snippet.includes('user_id:body.'));
});
