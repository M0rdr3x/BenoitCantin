'use strict';
// Contrat SQL hors ligne. Ne se connecte jamais à Supabase et ne modifie rien.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'sql/sinjira_character_sources_insert_requires_aal2.sql'),'utf8');
let assertions=0;
const ok=(v,message)=>{assert.ok(v,message);assertions++};
const no=(v,message)=>{assert.ok(!v,message);assertions++};
ok(/\bBEGIN;\s*/.test(source) && /\bCOMMIT;\s*$/.test(source),'Atomic SQL transaction');
ok(/CREATE\s+POLICY\s+sinjira_character_sources_insert_requires_aal2\s+ON\s+storage\.objects\s+AS\s+RESTRICTIVE\s+FOR\s+INSERT\s+TO\s+authenticated\s+WITH\s+CHECK\s*\(/i.test(source),'Restrictive INSERT only');
ok(/bucket_id\s*<>\s*'sinjira-character-sources'\s+OR\s*\(\(\s*SELECT\s+auth\.jwt\(\)\s*->>\s*'aal'\s*\)\s*=\s*'aal2'\s*\)/i.test(source),'JWT AAL2 for only Registry source uploads');
ok(/char_source_insert_own/.test(source),'Existing owner folder INSERT rule required');
ok(/n\.nspname='storage'/.test(source) && /c\.relrowsecurity=true/.test(source),'Storage RLS must be enabled');
ok(/id='sinjira-character-sources'\s+AND\s+public=false/.test(source),'Bucket required to be private');
ok(/policyname='sinjira_character_sources_insert_requires_aal2'/.test(source),'Existing policy requires review; no silent skip');
no(/\bDROP\s+POLICY\b/i.test(source),'Never drop an owner policy');
no(/\bALTER\s+TABLE[^;]*DISABLE\s+ROW\s+LEVEL\s+SECURITY\b/i.test(source),'Never disable RLS');
no(/\bGRANT\s+/i.test(source),'Never grant extra permissions');
no(/\bservice_role\b/i.test(source),'No service-role key/permissions');
no(/\buser_metadata\b|\braw_user_meta_data\b/i.test(source),'Never authorize with editable user metadata');
no(/\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\b/i.test(source),'No privileged security-definer helper');
no(/\bUPDATE\s+storage\.objects\b|\bDELETE\s+FROM\s+storage\.objects\b/i.test(source),'No Storage metadata mutation');

// Pure simulation of the intended restrictive condition only.
// Owner-prefix RLS remains an independent necessary condition.
function restrictiveInsert(bucket,aal){return bucket!=='sinjira-character-sources'||aal==='aal2'}
const cases=[
  ['sinjira-character-sources','aal2',true],
  ['sinjira-character-sources','aal1',false],
  ['sinjira-character-sources',null,false],
  ['sinjira-character-sources','',false],
  ['sinjira-character-sources','invalid',false],
  ['sinjira-avatars','aal1',true],
  ['sinjira-character-submissions','aal1',true]
];
for(const [bucket,aal,expected] of cases){
  assert.equal(restrictiveInsert(bucket,aal),expected,bucket+' / '+aal);
  assertions++;
}
console.log('PASS SINJIRA RLS photo AAL2: '+assertions+' assertions statiques / simulation booléenne, sans base de données.');
