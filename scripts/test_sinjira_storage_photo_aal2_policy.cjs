'use strict';
// Contrat SQL hors ligne : aucune connexion ni opération Supabase.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'sql/sinjira_character_sources_insert_requires_aal2.sql'),'utf8');
let assertions=0;
const ok=(v,msg)=>{assert.ok(v,msg);assertions++};
const no=(v,msg)=>{assert.ok(!v,msg);assertions++};
const buckets=['sinjira-character-sources','sinjira-character-submissions'];
const policies=[
  ['INSERT','sinjira_character_sources_insert_requires_aal2',['WITH CHECK']],
  ['SELECT','sinjira_character_photos_select_requires_aal2',['USING']],
  ['UPDATE','sinjira_character_photos_update_requires_aal2',['USING','WITH CHECK']],
  ['DELETE','sinjira_character_photos_delete_requires_aal2',['USING']]
];
ok(/\bBEGIN;\s*/.test(source)&&/\bCOMMIT;\s*$/.test(source),'Transaction atomique');
ok(/c\.relrowsecurity=true/.test(source),'RLS Storage activée impérative');
ok(/public=false\)\s*<>\s*2/.test(source),'Deux compartiments privés requis');
ok(/'authenticated'=ANY\(p\.roles\)/.test(source),'Owner policies limited to authenticated');
ok(/p\.permissive='PERMISSIVE'/.test(source),'Owner policies must remain permissive');
ok(/'%auth\.uid\(\)%'/.test(source),'Owner policies must check user ID');
ok(/'sinjira character photo own update'/.test(source),'Owner UPDATE policy in legacy bucket required');
ok(/'char_source_insert_own'/.test(source),'Existing source owner INSERT policy required');
ok(/'sinjira character photo own delete'/.test(source),'Legacy owner DELETE policy required');
const clean=source.replace(/--[^\n]*/g,'');
const created=[...clean.matchAll(/CREATE POLICY ([a-z_]+)\s+ON storage\.objects AS RESTRICTIVE FOR (SELECT|INSERT|UPDATE|DELETE) TO authenticated\s+([\s\S]*?);/g)];
ok(created.length===4,'Exactly four restrictive policies; one per operation');
for(const [verb,name,clauses] of policies){
  const match=created.filter(m=>m[1]===name&&m[2]===verb);
  ok(match.length===1,verb+': policy name and operation');
  const condition=match[0][3];
  for(const keyword of clauses)ok(new RegExp('\\b'+keyword.replace(' ','\\s+')+'\\b').test(condition),verb+' requires '+keyword);
  ok(!/\bINSERT\b|\bDELETE FROM\b|\bGRANT\b/i.test(condition),'No other operations in '+verb+' condition');
  ok(condition.includes("bucket_id NOT IN ('sinjira-character-sources','sinjira-character-submissions')"),
    verb+' must protect both Registry photo buckets');
  ok(condition.includes("auth.jwt()->>'aal'"),verb+' must read signed JWT AAL claim');
  ok(condition.includes("'aal2'"),verb+' must require AAL2');
  if(verb==='UPDATE'){
    const copies=condition.match(/bucket_id NOT IN/g)||[];
    ok(copies.length===2,'UPDATE protects both old and new row identities');
  }
}
for(const bucket of buckets)ok(source.includes("id IN ('sinjira-character-sources','sinjira-character-submissions')"),
  'Preflight includes '+bucket);
no(/\bDROP\s+POLICY\b/i.test(clean),'Never drop existing owner rules');
no(/\bALTER\s+TABLE[^;]*DISABLE\s+ROW\s+LEVEL\s+SECURITY\b/i.test(clean),'Never disable RLS');
no(/\bGRANT\s+/i.test(clean),'Never grant permissions');
no(/\bservice_role\s*=|\bservice_role\b.+WITH CHECK/i.test(clean),'No service-role access override');
no(/\buser_metadata\b|\braw_user_meta_data\b/i.test(source),'No user-editable authorization claims');
no(/\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\b/i.test(source),'No privileged helper functions');
no(/\bUPDATE\s+storage\.objects\b|\bDELETE\s+FROM\s+storage\.objects\b/i.test(source),'No manual Storage changes');

// Simulation de la seule condition RESTRICTIVE. Les RLS propriétaires
// existantes et l'absence d'une permissive UPDATE sur sources peuvent refuser
// même si cette simulation retourne true.
function extraGate(bucket,aal){
  return !buckets.includes(bucket)||aal==='aal2';
}
for(const verb of ['SELECT','INSERT','UPDATE','DELETE']){
  for(const bucket of buckets){
    for(const [aal,allowed] of [['aal2',true],['aal1',false],[null,false],['',false],['unknown',false]]){
      assert.equal(extraGate(bucket,aal),allowed,verb+'/'+bucket+'/'+aal);
      assertions++;
    }
  }
  for(const b of ['sinjira-avatars','another-private-bucket']){
    assert.equal(extraGate(b,'aal1'),true,verb+'/'+b+': outside scope');
    assertions++;
  }
}
console.log('PASS SINJIRA Storage : '+assertions+' validations SQL et booléennes, sans base de données.');
