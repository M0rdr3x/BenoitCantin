'use strict';
// Aucun réseau / secret : la requête READ-ONLY doit reproduire exactement
// le prévol des propriétaires du SQL RLS approuvé dans GitHub.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const sqlDir=path.join(__dirname,'sql');
const migration=fs.readFileSync(path.join(sqlDir,'sinjira_character_sources_insert_requires_aal2.sql'),'utf8');
const query=fs.readFileSync(path.join(sqlDir,'sinjira_character_photo_aal2_preflight_read_only.sql'),'utf8');
const base=(file,open,close,label)=>{
  const start=file.indexOf(open);
  assert.ok(start>=0,label+' : marqueur de début absent');
  const end=file.indexOf(close,start+open.length);
  assert.ok(end>start,label+' : marqueur de fin absent');
  return file.slice(start+open.length,end).replace(/\s+/g,'');
};
const startM='      VALUES\n';
const endM='    ) AS expected(policy_name,policy_cmd,owner_predicate)';
const startQ='  VALUES\n';
const endQ=')\n,';
function check(text){
  assert.match(text,/^-- SINJIRA™ — prévol Storage AAL2 strictement READ-ONLY\./);
  const commentsRemoved=text.replace(/--[^\n]*\n/g,'');
  assert.match(commentsRemoved,/^\s*WITH expected\s*\(/i);
  assert.match(commentsRemoved,/\bSELECT owner_rules_valid,private_buckets,storage_rls_active,/);
  assert.ok(!/\b(?:CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|CALL|DO)\s/i.test(commentsRemoved),'Aucun SQL DDL, CALL ou DO');
  assert.ok(!/\b(?:INSERT\s+INTO|DELETE\s+FROM|UPDATE\s+[a-z_][\w.]*)\b/i.test(commentsRemoved),'Aucune écriture SQL');
  const migrationOwners=base(migration,startM,endM,'owner contract migration');
  // SQL preflight ends its VALUES rows with a parenthesis that closes the CTE.
  const preflightOwners=base(text,startQ,'\n),\nowner_rules AS (', 'owner query');
  assert.equal(preflightOwners,migrationOwners,'Les 7 expressions propriétaire doivent être identiques à la migration source');
  const owners=(migrationOwners.match(/\('(?:char_source_|sinjira character photo own )/g)||[]).length;
  assert.equal(owners,7,'Les 7 politiques propriétaires requises');
  for(const marker of [
    "p.roles=ARRAY['authenticated'::name]",
    "p.permissive='PERMISSIVE'",
    "p.cmd=e.cmd",
    "regexp_replace(p.qual,'[[:space:]]','','g')",
    "regexp_replace(p.with_check,'[[:space:]]','','g')",
    "regexp_replace(e.predicate,'[[:space:]]','','g')",
    "owner_rules_valid=7 AND private_buckets=2",
    "storage_rls_active AND existing_new_policies=0",
    "'READY_FOR_REVIEW' ELSE 'BLOCKED'",
    "'sinjira-character-sources','sinjira-character-submissions'",
    "public=false",
    "c.relrowsecurity",
    "FROM storage.objects"
  ])assert.ok(text.includes(marker),'Garde de prévol absent : '+marker);
  const migrationPolicies=[...migration.matchAll(/CREATE POLICY (sinjira_character_\w+_aal2)/g)].map(m=>m[1]).sort();
  const queryPolicies=[...text.matchAll(/'(sinjira_character_\w+_aal2)'/g)].map(m=>m[1]).sort();
  assert.equal(migrationPolicies.length,4,'Quatre politiques AAL2 dans la migration');
  assert.deepEqual(queryPolicies,migrationPolicies,'Même inventaire exact des politiques AAL2');
}
check(query);
const changes=[
  ['déblocage sans propriétaire',query.replace('owner_rules_valid=7 AND private_buckets=2','owner_rules_valid>=0 AND private_buckets=2')],
  ['suppression du contrôle RLS',query.replace('storage_rls_active AND existing_new_policies=0','true AND existing_new_policies=0')],
  ['suppression du contrôle des politiques préexistantes',query.replace('storage_rls_active AND existing_new_policies=0','storage_rls_active AND true')],
  ['acceptation de bucket public',query.replace('AND public=false','AND public=true')],
  ['altération du contrôle utilisateur',query.replace('(auth.uid())::text','(auth.role())::text')],
  ['ignorance de WITH CHECK',query.replace("regexp_replace(p.with_check,'[[:space:]]','','g')","regexp_replace(p.qual,'[[:space:]]','','g')")],
  ['autoriser autre rôle',query.replace("p.roles=ARRAY['authenticated'::name]","'authenticated'=ANY(p.roles)")],
  ['soustraction d’une politique',query.replace("'sinjira_character_photos_delete_requires_aal2'\n","'other_policy'\n")],
  ['autoriser DDL',query.replace('FROM status;','FROM status;\nDROP TABLE storage.objects;')]
];
for(const [label,mutated] of changes){
  assert.notEqual(mutated,query,'La mutation doit modifier le contrat : '+label);
  assert.throws(()=>check(mutated),assert.AssertionError,'Le garde doit rejeter : '+label);
}
console.log('PASS preflight SINJIRA photos AAL2 : requête SELECT seule, 7 propriétaires, 4 politiques, 9 régressions refusées.');
