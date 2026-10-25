'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const ROOT=path.resolve(__dirname,'../supabase/functions');
const FUNCTIONS=[
  'admin-analytics','admin-console','admin-license-codes','admin-reports',
  'admin-sinjira-v18','admin-social-v20','admin-users','conscience-vault',
  'delete-player-account','fracture-engine-gateway','get-document-url',
  'get-novel-file-url','get-private-book-url','life-story-delivery',
  'life-story-export','nova-consultation40-submit','nova-survey-submit',
  'personal-ai','redeem-license-code','revoke-my-contributions',
  'security-context','send-game-report','send-player-sheet',
  'submit-character-questionnaire','submit-fracture-endgame',
  'submit-game-contribution'
];
function unsafeLogs(source){
  // Ne jamais enregistrer un objet Error Supabase/Storage/fournisseur brut.
  return [...source.matchAll(/console\.(?:error|warn|log|info|debug)\s*\(([^;\n]{0,1400})\)/g)]
    .map(m=>m[0])
    .filter(statement=>/,\s*(?:error|e|err)\s*\)/.test(statement)||
      /,\s*\{\s*(?:error|e|err)\s*\}\s*\)/.test(statement));
}
test('toutes les Edge Functions actuelles et futures expurgent leurs erreurs',()=>{
  assert.equal(new Set(FUNCTIONS).size,26,'Inventaire des 26 routes de référence');
  const discovered=fs.readdirSync(ROOT,{withFileTypes:true})
    .filter(dir=>dir.isDirectory() && fs.existsSync(path.join(ROOT,dir.name,'index.ts')))
    .map(dir=>dir.name).sort();
  assert.ok(discovered.length>=FUNCTIONS.length,'Routes Edge manquantes');
  for(const fn of FUNCTIONS)assert.ok(discovered.includes(fn),fn+': route disparue');
  // Parcourir la liste réelle permet de couvrir automatiquement une 27e fonction.
  for(const fn of discovered){
    const src=fs.readFileSync(path.join(ROOT,fn,'index.ts'),'utf8');
    assert.deepEqual(unsafeLogs(src),[],fn+': journaux de fournisseur non expurgés');
  }
  const sharedDir=path.join(ROOT,'_shared');
  for(const entry of fs.readdirSync(sharedDir)){
    if(!entry.endsWith('.ts') && !entry.endsWith('.mjs'))continue;
    const src=fs.readFileSync(path.join(sharedDir,entry),'utf8');
    assert.deepEqual(unsafeLogs(src),[],'_shared/'+entry+': erreur brute journalisée');
  }
});
test('le garde détecte les fuites artificielles et ignore les codes fixes',()=>{
  for(const bad of [
    "console.error('[delete]', error);",
    "console.warn('[redeem]',e);",
    "console.log('oops', {error});"
  ])assert.notEqual(unsafeLogs(bad).length,0,bad);
  assert.deepEqual(unsafeLogs("console.error('[delete]','DELETE_FAILED');"),[]);
});
test('les routes critiques restent expressément expurgées',()=>{
  for(const [fn,labels] of [
    ['delete-player-account',['STORAGE_DELETE_FAILED','AUTH_DELETE_FAILED','DELETE_FAILED']],
    ['redeem-license-code',['LICENSE_REDEEM_FAILED','LICENSE_UNEXPECTED_ERROR']],
    ['revoke-my-contributions',['REVOCATION_RPC_FAILED','REVOCATION_FAILED']],
    ['security-context',['SECURITY_CONTEXT_FAILED']],
    ['submit-game-contribution',['SUBMISSION_FAILED']]
  ]){
    const src=fs.readFileSync(path.join(ROOT,fn,'index.ts'),'utf8');
    for(const label of labels)assert.ok(src.includes(label),fn+': '+label);
  }
});
