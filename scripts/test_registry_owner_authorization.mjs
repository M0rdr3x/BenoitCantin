#!/usr/bin/env node
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import test from 'node:test';
import {isVerifiedRegistryOwner} from '../supabase/functions/_shared/registry-owner-authorization.mjs';

const USER_ID='123e4567-e89b-42d3-a456-426614174000';
const OTHER_ID='123e4567-e89b-42d3-a456-426614174001';
function mockOwner(data,error=null){
  const calls=[];
  return {
    calls,
    service:{
      async rpc(name,args){
        calls.push({name,args});
        return {data,error};
      }
    }
  };
}

test('accorde l’exception uniquement si le rôle SQL retourne le booléen true',async()=>{
  const {service,calls}=mockOwner(true);
  assert.equal(await isVerifiedRegistryOwner(service,USER_ID),true);
  assert.deepEqual(calls,[{name:'is_sinjira_owner',args:{p_user_id:USER_ID}}]);
});

test('refuse un compte non propriétaire avec un résultat SQL false',async()=>{
  const {service,calls}=mockOwner(false);
  assert.equal(await isVerifiedRegistryOwner(service,OTHER_ID),false);
  assert.equal(calls[0].args.p_user_id,OTHER_ID);
});

test('refuse les réponses non booléennes et indisponibles',async()=>{
  for(const value of [undefined,null,0,1,'true','false',{},[],{owner:true}]){
    const {service}=mockOwner(value);
    await assert.rejects(()=>isVerifiedRegistryOwner(service,USER_ID),{message:'REGISTRY_OWNER_CHECK_FAILED'});
  }
});

test('une erreur renvoyée par PostgREST ne devient jamais une autorisation',async()=>{
  const {service}=mockOwner(true,{message:'backend secret error',code:'PGRST116'});
  await assert.rejects(()=>isVerifiedRegistryOwner(service,USER_ID),{message:'REGISTRY_OWNER_CHECK_FAILED'});
});

test('une exception réseau est réduite à une erreur fixe et privée',async()=>{
  const service={async rpc(){throw new Error('sensitive backend details');}};
  await assert.rejects(()=>isVerifiedRegistryOwner(service,USER_ID),{message:'REGISTRY_OWNER_CHECK_FAILED'});
});

test('refuse une absence de service RPC ou de méthode',async()=>{
  for(const service of [null,undefined,{}, {rpc:'yes'}]){
    await assert.rejects(()=>isVerifiedRegistryOwner(service,USER_ID),{message:'REGISTRY_OWNER_CHECK_FAILED'});
  }
});

test('rejette les identifiants invalides avant tout appel SQL',async()=>{
  const {service,calls}=mockOwner(true);
  for(const uid of ['',null,undefined,{},'not-a-uuid','123e4567-e89b-62d3-a456-426614174000','123e4567-e89b-42d3-a456-426614174000; DROP TABLE x']){
    await assert.rejects(()=>isVerifiedRegistryOwner(service,uid),{message:'REGISTRY_OWNER_CHECK_FAILED'});
  }
  assert.equal(calls.length,0);
});

test('la route réelle dérive l’identité du JWT validé AAL2, et jamais du courriel',()=>{
  const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
  const code=readFileSync(resolve(root,'supabase/functions/submit-character-questionnaire/index.ts'),'utf8');
  const aal=code.indexOf('const {user}=await requiredVaultUser(req);');
  const request=code.indexOf('const body=await readBoundedJson(req);');
  const owner=code.indexOf('const owner=update_existing?await isVerifiedRegistryOwner(service,user.id):false;');
  const state=code.indexOf("if(submissionResult.error||characterResult.error)throw new Error('CHARACTER_STATE_LOOKUP_FAILED');");
  const allow=code.indexOf('if(owner&&update_existing&&(existingSubmission||existingCharacter)){');
  assert.ok(aal>=0&&request>aal&&owner>request&&state>owner&&allow>state);
  assert.ok(code.includes("import {isVerifiedRegistryOwner} from '../_shared/registry-owner-authorization.mjs';"));
  assert.ok(!/const\s+owner\s*=\s*String\s*\(\s*user\??\.email/.test(code),'Do not infer the privileged role from the user email');
  assert.ok(code.includes("if(e?.message==='REGISTRY_OWNER_CHECK_FAILED')return privateJson("));
  assert.ok(code.includes("code:'ONE_CHARACTER_PER_ACCOUNT'"));
});

test('le module ne lit pas des claims modifiables ni de courriels',()=>{
  const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
  const code=readFileSync(resolve(root,'supabase/functions/_shared/registry-owner-authorization.mjs'),'utf8');
  assert.ok(code.includes("service.rpc('is_sinjira_owner',{p_user_id:verifiedUserId})"));
  assert.ok(!/user_metadata|app_metadata|\.email\b|@gmail\.com|localStorage/i.test(code));
  assert.ok(code.includes('data !== true && data !== false'));
});
