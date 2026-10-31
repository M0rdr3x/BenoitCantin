'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const source=fs.readFileSync(path.resolve(
  __dirname,'../supabase/functions/_shared/auth.ts'),'utf8');
const begin=source.indexOf('async function assertAdminMfa(');
const end=source.indexOf('\nasync function sensitiveStepUpEnabled(',begin);
assert.ok(begin>0 && end>begin,'Garde MFA admin réel introuvable');
const declaration=source.slice(begin,end);

function createCheck({admin=true,dbError=null,assurance={nextLevel:'aal2',currentLevel:'aal2'},aalError=null}={}) {
  // Isoler exactement la fonction TypeScript livrée : aucune requête distante.
  const script=declaration.replace(
    'context: Awaited<ReturnType<typeof authenticatedContext>>','context');
  const assuranceLevel=async()=>{if(aalError)throw aalError;return assurance;};
  const check=new Function('assuranceLevel','console',
    script+'\nreturn assertAdminMfa;')(assuranceLevel,{error(){}});
  const context={
    user:{id:'admin-test'},
    service:{rpc:async()=>({data:admin,error:dbError})}
  };
  return ()=>check(context);
}

test('admin : AAL2 vérifié autorise uniquement le contexte existant',async()=>{
  const result=await createCheck()();
  assert.equal(result.currentLevel,'aal2');
});
test('admin : AAL1 sans MFA inscrit est rejeté (ancienne faille)',async()=>{
  await assert.rejects(createCheck({
    assurance:{currentLevel:'aal1',nextLevel:'aal1'}
  })(),/MFA_REQUIRED/);
});
test('admin : facteur inscrit mais session AAL1 est rejetée',async()=>{
  await assert.rejects(createCheck({
    assurance:{currentLevel:'aal1',nextLevel:'aal2'}
  })(),/MFA_REQUIRED/);
});
test('admin : AAL2 incohérent, niveau suivant absent ou inconnu, rejeté',async()=>{
  for(const next of ['aal1',null,undefined,'unknown']) {
    await assert.rejects(createCheck({
      assurance:{currentLevel:'aal2',nextLevel:next}
    })(),/MFA_REQUIRED/);
  }
});
test('admin : authentification requise indépendamment de MFA',async()=>{
  await assert.rejects(createCheck({admin:false})(),/ADMIN_REQUIRED/);
  await assert.rejects(createCheck({dbError:new Error('offline')})(),/ADMIN_REQUIRED/);
});
test('admin : serveur MFA indisponible ou sans réponse refuse fermé',async()=>{
  await assert.rejects(createCheck({aalError:new Error('provider_detail_must_not_leak')})(),/MFA_STATE_UNAVAILABLE/);
  await assert.rejects(createCheck({assurance:null})(),/TypeError/);
});
test('les 7 endpoints admin restent dans le garde d’accès',()=>{
  const names=[
    'admin-analytics','admin-console','admin-license-codes',
    'admin-reports','admin-sinjira-v18','admin-social-v20','admin-users'
  ];
  for(const name of names)assert.ok(source.includes("'"+name+"'"),name);
  assert.match(source,/return \{ \.\.\.context, aal \}/);
  assert.match(source,/if \(aal\.nextLevel !== 'aal2' \|\| aal\.currentLevel !== 'aal2'\)/);
  assert.doesNotMatch(source,/aal\.nextLevel === 'aal2' && aal\.currentLevel !== 'aal2'/);
});

test('aucune erreur de fournisseur ou fragment de secret dans les logs serveur',()=>{
  assert.doesNotMatch(source,/console\.(?:warn|error)\([^;]*,\s*error\)/,
    'Ne jamais journaliser un objet Error venant du fournisseur');
  assert.match(source,/throw new Error\('MFA_STATE_UNAVAILABLE'\)/);
});
