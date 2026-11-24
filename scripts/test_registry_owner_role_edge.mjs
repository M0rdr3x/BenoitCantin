#!/usr/bin/env node
// Exercices de la véritable porte d'autorisation Edge (pas une copie de sa logique).
// Aucun utilisateur réel, aucune requête réseau, aucune écriture Supabase.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = readFileSync(resolve(root, 'supabase/functions/submit-character-questionnaire/index.ts'), 'utf8');
const start = source.indexOf('    let owner=false;');
const end = source.indexOf('    if(owner&&update_existing&&(existingSubmission||existingCharacter)){', start);
assert.ok(start >= 0 && end > start, 'La décision serveur réelle doit rester isolable');
const gateSource = source.slice(start, end);
assert.match(gateSource, /service\.rpc\('is_sinjira_owner',\{p_user_id:user\.id\}\)/);
assert.match(gateSource, /owner=ownerRole===true;/);
assert.doesNotMatch(gateSource, /owner\s*=\s*String\(user\??\.email/);

// Extraire le bloc JavaScript réel : il ne contient aucun TypeScript ni import.
const check = vm.runInNewContext(
  '(async function roleGate(user,service,update_existing,privateJson){\n'
  + gateSource
  + '\nreturn {kind:"allowed", privileged:owner, hasExisting:!!(existingSubmission||existingCharacter)};\n})',
  {}, {timeout:1500, filename:'questionnaire-owner-gate.js'}
);
const uid = '10000000-0000-4000-8000-000000000001';

async function scenario({
  email='changed-owner@example.invalid',
  update=true,
  submission={id:'20000000-0000-4000-8000-000000000001'},
  character=null,
  role=true,
  roleError=null,
  stateError=null,
}={}) {
  const calls = { rpc:[], reads:[] };
  const rows = { profiles: {data:{pseudo:'synthetic'},error:null},
    character_submissions:{data:submission,error:stateError},
    characters:{data:character,error:null} };
  const service={
    from(table) {
      assert.ok(Object.hasOwn(rows,table), 'Only the three expected account tables');
      calls.reads.push(table);
      return {
        select(){return this;},
        eq(field,value){assert.equal(field,'user_id');assert.equal(value,uid);return this;},
        order(){return this;},
        limit(){return this;},
        async maybeSingle(){return rows[table];}
      };
    },
    async rpc(name,args){
      calls.rpc.push({name,args});
      assert.equal(name,'is_sinjira_owner');
      assert.equal(args.p_user_id,uid, 'Trust only the verified JWT user id');
      return {data:role,error:roleError};
    }
  };
  let outcome;
  try{
    outcome=await check({id:uid,email},service,update,(body,status)=>({kind:'rejected',status,body}));
  }catch(error){
    outcome={kind:'exception',code:error.message};
  }
  return {outcome,calls};
}
const tests=[
  [{role:true},'allowed',null,1],
  [{role:true,email:'new-address@example.invalid'},'allowed',null,1],
  [{role:false,email:'changed-owner@example.invalid'},'rejected',409,1],
  [{role:false,email:'old-owner@example.invalid'},'rejected',409,1],
  [{role:'true'},'exception','OWNER_ROLE_UNAVAILABLE',1],
  [{role:1},'exception','OWNER_ROLE_UNAVAILABLE',1],
  [{role:null},'exception','OWNER_ROLE_UNAVAILABLE',1],
  [{role:{owner:true}},'exception','OWNER_ROLE_UNAVAILABLE',1],
  [{role:true,roleError:new Error('RPC unavailable')},'exception','OWNER_ROLE_UNAVAILABLE',1],
  [{update:false,role:true},'rejected',409,0],
  [{update:true,submission:null,character:null,role:true},'allowed',null,0],
  [{update:false,submission:null,character:null,role:false},'allowed',null,0],
  [{stateError:new Error('RLS error')},'exception','CHARACTER_STATE_LOOKUP_FAILED',0],
  [{submission:null,character:{id:'30000000-0000-4000-8000-000000000001'},role:false},'rejected',409,1]
];
for(const [options,kind,detail,rpcCount] of tests){
  const {outcome,calls}=await scenario(options);
  assert.equal(outcome.kind,kind,JSON.stringify(options, (k,v)=>k==='roleError'||k==='stateError'?'fixture-error':v));
  if(kind==='rejected'){
    assert.equal(outcome.status,detail);
    assert.equal(outcome.body.code,'ONE_CHARACTER_PER_ACCOUNT');
  }else if(kind==='exception'){
    assert.equal(outcome.code,detail);
  }else if(rpcCount===1){
    assert.equal(outcome.privileged,true);
  }
  assert.equal(calls.rpc.length,rpcCount,'RPC must be conditional on explicit update and existing dossier');
  assert.deepEqual(calls.reads.slice().sort(),['character_submissions','characters','profiles'].sort());
}
console.log('PASS Registre: 14 scénarios réels de contrôle owner, rôle strict, échec fermé, état privé et compte authentifié.');
