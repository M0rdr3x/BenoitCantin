#!/usr/bin/env node
"use strict";
/** Verrous Netlify : la prévisualisation de Projet Nova reste manuelle et
 * n'autorise pas de publication DNS/production ni de collecte politique.
 * Ce test local n'utilise aucun réseau, compte ou secret.
 */
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const names=[
  "deploy-netlify-staging.yml",
  "validate-netlify-preview.yml",
  "validate-netlify-pre-dns.yml"
];
const workflows=Object.fromEntries(names.map(name=>[
  name,fs.readFileSync(path.join(root,".github/workflows",name),"utf8")
]));
const allowedRef="github.ref == 'refs/heads/staging/nova-public-40-64-boussole-2026-10-26'";
const read=pathName=>fs.readFileSync(path.join(root,pathName),"utf8");

test("Trois portes Netlify à déclenchement uniquement manuel",()=>{
  for(const [name,source] of Object.entries(workflows)){
    const header=source.slice(0,source.indexOf("\npermissions:"));
    assert.match(header,/^on:\s*\n  workflow_dispatch:/m,name);
    assert.doesNotMatch(header,/^  (?:push|pull_request|schedule|repository_dispatch|workflow_run):/m,name);
    assert.match(source,/permissions:\s*\n  contents: read/,name);
  }
});

test("Le candidat Nova exact est autorisé, aucune autorisation globale de branche",()=>{
  for(const [name,source] of Object.entries(workflows)){
    assert.ok(source.includes(allowedRef),name);
    assert.ok(source.includes("startsWith(github.ref, 'refs/heads/a1/web-release-')"),name);
    assert.doesNotMatch(source,/github\.ref == 'refs\/heads\/main'/,name);
  }
});

test("Deux déploiements candidats exigent une confirmation et l'identité de SHA",()=>{
  const s=workflows["deploy-netlify-staging.yml"];
  for(const marker of [
    'STAGING_ONLY','expected_sha','expected_site_name',
    'NETLIFY_AUTH_TOKEN','NETLIFY_SITE_ID',
    '"$EXPECTED_SHA" != "$GITHUB_SHA"',
    'python3 scripts/build_netlify_public.py --check',
    '--dir _preview_site','--dir _site','--no-build',
    'Refuser le même deploy deux fois'
  ]) assert.ok(s.includes(marker),marker);
  assert.doesNotMatch(s,/\bnetlify-cli\b[^\n]*\s--prod(?:\s|$)/);
});

test("Gate pré-DNS : deux permalinks distincts du même site et du même SHA",()=>{
  const s=workflows["validate-netlify-pre-dns.yml"];
  for(const marker of [
    'preview_permalink','production_permalink',
    '"$PREVIEW_PERMALINK" = "$PRODUCTION_PERMALINK"',
    '--context preview --expected-sha "$GITHUB_SHA"',
    '--context production-candidate --same-netlify-site-as "$PREVIEW_PERMALINK" --expected-sha "$GITHUB_SHA"'
  ]) assert.ok(s.includes(marker),marker);
});

test("Révision HTTP autonome : contexte choisi et SHA attendu",()=>{
  const s=workflows["validate-netlify-preview.yml"];
  for(const marker of ['artifact_context','deploy_permalink','--context "$SMOKE_CONTEXT" --expected-sha "$GITHUB_SHA"']){
    assert.ok(s.includes(marker),marker);
  }
});

const civicPages=[
  "consultation-40.html",
  "sondage.html",
  "boussole-electorale.html",
  "resultats-sondages.html"
];
function checkCivicPrivacyHeaders(config, page) {
  const url="/projets/projet-nova/"+page;
  const rules=config.split(/^\[\[headers\]\]\s*$/m).slice(1)
    .filter(block=>new RegExp('^\\s*for\\s*=\\s*"'+url.replace(/[.*+?^${}()|[\]\\]/g,"\\test("Build autorisé isolé et collecte Nova toujours fermée",()=>{")+'"\\s*
  const netlify=read("netlify.toml");
  assert.match(netlify,/^\s*publish\s*=\s*"_site"\s*$/m);
  assert.match(netlify,/^\s*command\s*=\s*"python3 scripts\/build_netlify_public\.py"\s*$/m);
  assert.doesNotMatch(netlify,/^\s*publish\s*=\s*"\."\s*$/m);
  const nova="projets/projet-nova/assets/";
  for(const file of ["consultation-40.js","sondage.js"]){
    const client=read(nova+file);
    assert.match(client,/const COLLECTION_OPEN = false;/,file);
    assert.match(client,/const LIVE_OPINION_CONSENT_GRANTED = false;/,file);
  }
  assert.match(read(nova+"resultats-sondages.js"),/const PUBLIC_AGGREGATES_ENABLED = false;/);
});
,"m").test(block));
  assert.equal(rules.length,1,"Règle Netlify unique requise pour "+url);
  assert.match(rules[0],/^\s*Cache-Control\s*=\s*"private, no-store, max-age=0"\s*$/m,url);
  assert.match(rules[0],/^\s*Referrer-Policy\s*=\s*"no-referrer"\s*$/m,url);
}

test("En-têtes stricts des quatre pages civiques Nova",()=>{
  const netlify=read("netlify.toml");
  for(const page of civicPages) checkCivicPrivacyHeaders(netlify,page);
});

test("Mutation négative : un cache public ou une fuite Referer est refusé",()=>{
  const netlify=read("netlify.toml");
  for(const page of civicPages){
    const url="/projets/projet-nova/"+page;
    const before='for = "'+url+'"';
    assert.ok(netlify.includes(before),page);
    const mutatedNoRule=netlify.replace(before,'for = "/missing-civic-page"');
    assert.throws(()=>checkCivicPrivacyHeaders(mutatedNoRule,page),page);
  }
  const wrongCache=netlify.replace('for = "/projets/projet-nova/sondage.html"\n  [headers.values]\n    Cache-Control = "private, no-store, max-age=0"',
    'for = "/projets/projet-nova/sondage.html"\n  [headers.values]\n    Cache-Control = "public, max-age=3600"');
  assert.notEqual(wrongCache,netlify);
  assert.throws(()=>checkCivicPrivacyHeaders(wrongCache,"sondage.html"));
  const wrongReferrer=netlify.replace('for = "/projets/projet-nova/sondage.html"\n  [headers.values]\n    Cache-Control = "private, no-store, max-age=0"\n    Referrer-Policy = "no-referrer"',
    'for = "/projets/projet-nova/sondage.html"\n  [headers.values]\n    Cache-Control = "private, no-store, max-age=0"\n    Referrer-Policy = "unsafe-url"');
  assert.notEqual(wrongReferrer,netlify);
  assert.throws(()=>checkCivicPrivacyHeaders(wrongReferrer,"sondage.html"));
});

test("Build autorisé isolé et collecte Nova toujours fermée",()=>{
  const netlify=read("netlify.toml");
  assert.match(netlify,/^\s*publish\s*=\s*"_site"\s*$/m);
  assert.match(netlify,/^\s*command\s*=\s*"python3 scripts\/build_netlify_public\.py"\s*$/m);
  assert.doesNotMatch(netlify,/^\s*publish\s*=\s*"\."\s*$/m);
  const nova="projets/projet-nova/assets/";
  for(const file of ["consultation-40.js","sondage.js"]){
    const client=read(nova+file);
    assert.match(client,/const COLLECTION_OPEN = false;/,file);
    assert.match(client,/const LIVE_OPINION_CONSENT_GRANTED = false;/,file);
  }
  assert.match(read(nova+"resultats-sondages.js"),/const PUBLIC_AGGREGATES_ENABLED = false;/);
});
