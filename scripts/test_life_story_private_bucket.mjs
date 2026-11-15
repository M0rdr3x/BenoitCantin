#!/usr/bin/env node
// Vérification du vrai garde Histoire de vie : aucun secret/réseau/fichier réel.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import {
  LIFE_STORY_PRIVATE_BUCKET,
  isVerifiedPrivateLifeStoryBucket,
  hasVerifiedPrivateLifeStoryBucket,
} from '../supabase/functions/_shared/private-life-story-bucket.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const bucket=LIFE_STORY_PRIVATE_BUCKET;
const fake=(data,error=null)=>({getBucket:async(name)=>{
  assert.equal(name,bucket); return {data,error};
}});

test('accepte uniquement un bucket confirmé privé et identifié exactement',async()=>{
  assert.equal(bucket,'sinjira-life-story-exports');
  assert.equal(isVerifiedPrivateLifeStoryBucket({id:bucket,public:false}),true);
  assert.equal(await hasVerifiedPrivateLifeStoryBucket(fake({id:bucket,public:false})),true);
});
test('refuse le bucket public même lorsque le service le possède',async()=>{
  assert.equal(await hasVerifiedPrivateLifeStoryBucket(fake({id:bucket,public:true})),false);
});
test('refuse la réponse sans indicateur public ou avec mauvaise valeur',async()=>{
  for(const flag of [undefined,null,0,'false','private']){
    assert.equal(await hasVerifiedPrivateLifeStoryBucket(fake({id:bucket,public:flag})),false);
  }
});
test('refuse les IDs substitués, même marqués privés',async()=>{
  for(const id of ['another-bucket','SINJIRA-LIFE-STORY-EXPORTS',null,undefined]){
    assert.equal(await hasVerifiedPrivateLifeStoryBucket(fake({id,public:false})),false);
  }
});
test('refuse les métadonnées absentes, primitives ou tableaux',async()=>{
  for(const value of [null,undefined,false,'private',[],{},[ {id:bucket,public:false} ]]){
    assert.equal(await hasVerifiedPrivateLifeStoryBucket(fake(value)),false);
  }
});
test('refuse les erreurs du service Storage sans divulguer les détails',async()=>{
  assert.equal(await hasVerifiedPrivateLifeStoryBucket(fake({id:bucket,public:false},new Error('secret'))),false);
  assert.equal(await hasVerifiedPrivateLifeStoryBucket(fake(null,{message:'not allowed'})),false);
});
test('refuse lorsque getBucket rejette la promesse',async()=>{
  assert.equal(await hasVerifiedPrivateLifeStoryBucket({getBucket:async()=>{throw Error('private');}}),false);
});
test('refuse si l’API de métadonnées est absente',async()=>{
  for(const storage of [null,undefined,{}, {getBucket:null}]){
    assert.equal(await hasVerifiedPrivateLifeStoryBucket(storage),false);
  }
});
test('la création et la distribution ne peuvent précéder la vérification du bucket',()=>{
  const exportSource=readFileSync(resolve(root,'supabase/functions/life-story-export/index.ts'),'utf8');
  const first=exportSource.indexOf("if (action === 'generate') {");
  const second=exportSource.indexOf("if (action === 'create_delivery_links') {");
  const third=exportSource.indexOf("if (action === 'revoke') {");
  const generateGuard=exportSource.indexOf('await hasVerifiedPrivateLifeStoryBucket(service.storage)',first);
  const linkGuard=exportSource.indexOf('await hasVerifiedPrivateLifeStoryBucket(service.storage)',second);
  const upload=exportSource.indexOf('service.storage.from(BUCKET).upload(',first);
  const deleteTokens=exportSource.indexOf("from('life_story_delivery_links').delete()",second);
  const errorCheck=exportSource.indexOf("if (revokeExistingError) throw new Error('LIFE_STORY_LINK_ROTATION_FAILED');",second);
  const tokenCreate=exportSource.indexOf('crypto.getRandomValues(new Uint8Array(32))',second);
  assert.ok(first<generateGuard && generateGuard<upload && upload<second);
  assert.ok(second<linkGuard && linkGuard<deleteTokens && deleteTokens<errorCheck && errorCheck<tokenCreate && tokenCreate<third);
  assert.equal(exportSource.match(/await hasVerifiedPrivateLifeStoryBucket\(service\.storage\)/g)?.length,2);
});
test('la remise valide les métadonnées après jeton/référence et avant la lecture PDF',()=>{
  const deliverySource=readFileSync(resolve(root,'supabase/functions/life-story-delivery/index.ts'),'utf8');
  const token=deliverySource.indexOf(".eq('token_hash', hash)");
  const record=deliverySource.indexOf("record.storage_bucket !== 'sinjira-life-story-exports'");
  const guard=deliverySource.indexOf('await hasVerifiedPrivateLifeStoryBucket(service.storage)');
  const read=deliverySource.indexOf('await readPrivateLifeStoryPdf(');
  assert.ok(token>=0&&token<record&&record<guard&&guard<read);
  assert.ok(deliverySource.includes('if (!(await hasVerifiedPrivateLifeStoryBucket(service.storage))) return errorResponse(req, 410);'));
  assert.equal(deliverySource.match(/await hasVerifiedPrivateLifeStoryBucket\(service\.storage\)/g)?.length,1);
});
