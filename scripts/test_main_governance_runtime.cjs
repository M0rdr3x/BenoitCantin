#!/usr/bin/env node
'use strict';
// Exécuter LE VRAI corps JavaScript de actions/github-script sans réseau,
// autorisations GitHub, secrets ni changements de branches.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {AsyncFunction} = (()=>({
  AsyncFunction:Object.getPrototypeOf(async function(){}).constructor
}))();
const root=path.resolve(__dirname,'..');
const workflow=fs.readFileSync(path.join(root,'.github/workflows/main-governance.yml'),'utf8');
const lines=workflow.split(/\r?\n/);
const start=lines.findIndex(line=>line.trim()==='script: |');
assert.ok(start>=0,'Action github-script manquante dans le workflow réel');
const indent=lines[start].match(/^ */)[0].length;
const body=[];
for(const line of lines.slice(start+1)){
  const spaces=line.match(/^ */)[0].length;
  if(line.trim()&&spaces<=indent)break;
  body.push(line.slice(indent+2));
}
const script=body.join('\n');
assert.match(script,/repos\.listPullRequestsAssociatedWithCommit/,
  'Contrôle réel de provenance commit/PR absent');
assert.match(script,/pr\.merge_commit_sha === sha/,
  'Contrôle réel du SHA de fusion absent');
const runner=new AsyncFunction('github','context','core','process',script);
const sha='a'.repeat(40),otherSha='b'.repeat(40);
let assertions=0;
function equal(value,expected,why){assert.equal(value,expected,why);assertions++}
async function run({
  protectedMain=true,eventName='push',ref='refs/heads/main',
  associated=[{merged_at:'2026-11-09T00:00:00Z',base:{ref:'main'},merge_commit_sha:sha}]
}={}){
  const failed=[],infos=[],calls=[];
  const github={rest:{repos:{
    async listPullRequestsAssociatedWithCommit(args){
      calls.push(args);
      return {data:associated};
    }
  }}};
  const context={ref,eventName,sha,repo:{owner:'M0rdr3x',repo:'BenoitCantin'}};
  const core={
    setFailed(message){failed.push(String(message))},
    info(message){infos.push(String(message))},
    warning(message){failed.push('AVERTISSEMENT_NON_BLOQUANT: '+message)}
  };
  const proc={env:{GITHUB_REF_PROTECTED: protectedMain?'true':'false'}};
  await runner(github,context,core,proc);
  return {failed,infos,calls};
}
async function main(){
  const nominal=await run();
  equal(nominal.failed.length,0,'Protection + fusion exacte = succès');
  equal(nominal.calls.length,1,'Provenance du commit vérifiée');
  equal(nominal.calls[0].commit_sha,sha,'Provenance du SHA exact');
  equal(nominal.calls[0].owner,'M0rdr3x','Dépôt attendu');

  const onlyAssociated=await run({associated:[
    {merged_at:'2026-11-09',base:{ref:'main'},merge_commit_sha:otherSha}
  ]});
  equal(onlyAssociated.failed.length,1,'PR associée mais mauvais SHA refusée');
  assert.match(onlyAssociated.failed[0],/sans Pull Request/);
  assertions++;

  const unmerged=await run({associated:[
    {merged_at:null,base:{ref:'main'},merge_commit_sha:sha}
  ]});
  equal(unmerged.failed.length,1,'PR non fusionnée refusée');

  const wrongBase=await run({associated:[
    {merged_at:'2026-11-09',base:{ref:'develop'},merge_commit_sha:sha}
  ]});
  equal(wrongBase.failed.length,1,'PR fusionnée ailleurs refusée');

  const empty=await run({associated:[]});
  equal(empty.failed.length,1,'Push direct sans PR refusé');

  const weak=await run({protectedMain:false});
  equal(weak.failed.length,1,'Une main non protégée fait échouer la CI malgré la PR valide');
  assert.match(weak.failed[0],/pas protégée/);
  assertions++;

  const both=await run({protectedMain:false,associated:[]});
  equal(both.failed.length,2,'Les deux défauts sont rapportés sur le même push');

  const scheduled=await run({eventName:'schedule',associated:[]});
  equal(scheduled.failed.length,0,'Surveillance planifiée si main protégée');
  equal(scheduled.calls.length,0,'Surveillance planifiée ne demande pas de PR');

  const scheduledUnprotected=await run({eventName:'schedule',protectedMain:false,associated:[]});
  equal(scheduledUnprotected.failed.length,1,'Surveillance quotidienne met main non protégée en échec');
  equal(scheduledUnprotected.calls.length,0,'Pas de fausse recherche de PR en scheduled');

  const manual=await run({eventName:'workflow_dispatch',associated:[]});
  equal(manual.failed.length,0,'Diagnostic manuel accepté quand main protégée');

  const otherRef=await run({ref:'refs/heads/feature/unsafe',associated:[]});
  equal(otherRef.failed.length,1,'Exécution hors main refusée');
  equal(otherRef.calls.length,0,'Aucun appel de PR si hors main');
  console.log('PASS: '+assertions+' vérifications du VRAI script GitHub de gouvernance; SHA de fusion, protection et surveillance.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
