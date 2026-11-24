#!/usr/bin/env node
// Exécute la VRAIE fonction Edge de révocation avec un client Supabase simulé.
// Aucun compte, secret, réseau ou donnée de production n'est utilisé.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const source=readFileSync(resolve(ROOT,'supabase/functions/revoke-my-contributions/index.ts'),'utf8');
const start=source.indexOf('Deno.serve(async (req) => {');
assert.ok(start>=0,'Handler Edge réel introuvable');
const realHandler=source.slice(start);
const uuidDefinition=source.split('\n').find(line=>line.startsWith('const UUID_RE='));
assert.ok(uuidDefinition,'Validation UUID réelle introuvable');
const UUID_RE=new Function('return '+uuidDefinition.slice('const UUID_RE='.length).replace(/;$/, ''))();

const buildHandler=new Function(
  'Deno','requiredUser','readBoundedJson','serviceClient','privateJson','UUID_RE',
  realHandler+'\nreturn Deno.handler;'
);
const SESSION='11111111-1111-4111-8111-111111111111';
const USER='22222222-2222-4222-8222-222222222222';
function setup({authFails=false,sqlError=false}={}){
  const calls=[];
  const Deno={
    handler:null,
    serve(handler){this.handler=handler;}
  };
  const requiredUser=async()=>{
    calls.push(['auth']);
    if(authFails)throw new Error('AUTH_REQUIRED');
    return {id:USER};
  };
  const readBoundedJson=async(req)=>{
    calls.push(['body']);
    if(authFails)throw new Error('READ_BEFORE_AUTH');
    return JSON.parse(req.payload);
  };
  const serviceClient=()=>{
    calls.push(['service']);
    return {
      async rpc(name,args){
        calls.push(['rpc',name,args]);
        return {data:sqlError?null:3,error:sqlError?{code:'DB_UNAVAILABLE'}:null};
      }
    };
  };
  const privateJson=(data,status=200)=>new Response(JSON.stringify(data),{
    status,
    headers:{
      'Content-Type':'application/json; charset=utf-8',
      'Cache-Control':'private, no-store, max-age=0',
      'X-Content-Type-Options':'nosniff',
      'Referrer-Policy':'no-referrer'
    }
  });
  const handler=buildHandler(Deno,requiredUser,readBoundedJson,serviceClient,privateJson,UUID_RE);
  assert.equal(typeof handler,'function');
  return {handler,calls};
}
async function invoke(body,options={}){
  const {handler,calls}=setup(options);
  const req={method:'POST',payload:typeof body==='string'?body:JSON.stringify(body)};
  const response=await handler(req);
  const json=await response.json();
  assert.equal(response.headers.get('Cache-Control'),'private, no-store, max-age=0');
  return {status:response.status,json,calls};
}
const rpcCount=calls=>calls.filter(call=>call[0]==='rpc').length;
const noEffects=result=>{
  assert.equal(rpcCount(result.calls),0,'Une portée rejetée ne peut pas activer le RPC destructeur');
  assert.equal(result.calls.some(c=>c[0]==='service'),false,'Aucun client service_role nécessaire sur portée invalide');
};

test('révocation de toutes les contributions uniquement avec all:true sans session_id',async()=>{
  const result=await invoke({all:true});
  assert.equal(result.status,200);
  assert.deepEqual(result.json,{ok:true,removed:3,scope:'all'});
  assert.equal(rpcCount(result.calls),1);
  assert.deepEqual(result.calls.find(c=>c[0]==='rpc'),[
    'rpc','revoke_sinjira_contributions',{p_user_id:USER,p_session_id:null}
  ]);
  assert.deepEqual(result.calls.slice(0,2).map(c=>c[0]),['auth','body']);
});

test('révocation par session avec ou sans all:false et nettoyage des espaces',async()=>{
  for(const body of [
    {session_id:SESSION},
    {all:false,session_id:SESSION},
    {session_id:' '+SESSION+'  ',all:false}
  ]){
    const result=await invoke(body);
    assert.equal(result.status,200);
    assert.equal(result.json.scope,'session');
    assert.deepEqual(result.calls.find(c=>c[0]==='rpc')?.[2],
      {p_user_id:USER,p_session_id:SESSION});
  }
});

test('une suppression globale avec session_id, même vide ou mal typé, est refusée',async()=>{
  for(const session_id of [null,undefined,'','   ',0,false,true,[],{},SESSION,'not-uuid']){
    const payload=JSON.stringify({all:true,session_id});
    // JSON.stringify omet undefined : la requête produite n'a alors aucune clé
    // session_id ; les cas effectivement présents sont ceux à refuser.
    if(session_id===undefined)continue;
    const result=await invoke(payload);
    assert.equal(result.status,400,payload);
    assert.equal(result.json.code,'AMBIGUOUS_SCOPE',payload);
    noEffects(result);
  }
});

test('les paramètres supplémentaires et les propriétés prototypales ne sont jamais ignorés',async()=>{
  for(const payload of [
    '{"all":true,"session":"'+SESSION+'"}',
    '{"all":true,"confirm":true}',
    '{"all":true,"user_id":"'+USER+'"}',
    '{"all":true,"__proto__":{"session_id":"'+SESSION+'"}}',
    '{"session_id":"'+SESSION+'","reason":"ignored"}',
    '{"all":false,"session_id":"'+SESSION+'","extra":null}',
    '{"all":true,"constructor":"value"}'
  ]){
    const result=await invoke(payload);
    assert.equal(result.status,400,payload);
    assert.equal(result.json.code,'INVALID_SCOPE',payload);
    noEffects(result);
  }
  assert.equal(Object.prototype.session_id,undefined);
});

test('all de type incorrect ne déclenche jamais une révocation de masse',async()=>{
  for(const value of ['true',1,0,null,{},[],'false']){
    const result=await invoke({all:value});
    assert.equal(result.status,400);
    assert.equal(result.json.code,'INVALID_SCOPE');
    noEffects(result);
  }
});

test('scope vide, false seul ou session invalide : requête refusée avant service_role',async()=>{
  for(const body of [{},{all:false},{session_id:''},{session_id:' '},
    {session_id:'other'},{all:false,session_id:42},{all:false,session_id:null}]){
    const result=await invoke(body);
    assert.equal(result.status,400);
    assert.equal(result.json.code,'SESSION_REQUIRED');
    noEffects(result);
  }
});

test('JWT absent : aucune lecture du corps ni invocation RPC',async()=>{
  const result=await invoke({all:true},{authFails:true});
  assert.equal(result.status,401);
  assert.equal(result.json.code,'AUTH_REQUIRED');
  assert.deepEqual(result.calls.map(c=>c[0]),['auth']);
});

test('une erreur SQL ne devient jamais un faux succès',async()=>{
  const result=await invoke({all:true},{sqlError:true});
  assert.equal(result.status,500);
  assert.equal(result.json.code,'REVOCATION_FAILED');
  assert.equal(rpcCount(result.calls),1);
});

test('le contrat réel reste POST, JWT, RPC compte courant, réponses privées',()=>{
  assert.ok(realHandler.includes("req.method !== 'POST'"));
  assert.ok(realHandler.includes('await requiredUser(req)'));
  assert.ok(realHandler.includes('await readBoundedJson(req)'));
  assert.ok(realHandler.includes('body.all===true'));
  assert.ok(realHandler.includes('Object.prototype.hasOwnProperty.call(body,'));
  assert.ok(realHandler.includes('if(revokeAll && hasSessionId)'));
  assert.ok(realHandler.includes('p_user_id: user.id'));
  assert.ok(realHandler.includes('p_session_id: revokeAll ? null : sessionId'));
});
