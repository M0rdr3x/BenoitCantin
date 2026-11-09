#!/usr/bin/env node
'use strict';
// Régressions de liens HTML depuis les métadonnées de projets/romans Supabase.
// Aucune requête réseau, aucun compte et aucune donnée réelle.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const ORIGIN='https://www.benoitcantin.com';
const FILES=[
  'assets/js/sinjira-library.js',
  'assets/js/sinjira-library-v24-4-61.js',
  'assets/js/sinjira-library-hub-v26.js',
];
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
})[c]);
const read=file=>fs.readFileSync(path.join(ROOT,file),'utf8');
function boot(file,override={}){
  const source=read(file);
  const containers={
    '[data-project-library]':{innerHTML:''},
    '[data-library-reads]':{innerHTML:''},
    '[data-library-account-games]':{innerHTML:'',querySelectorAll(){return []}},
    '[data-library-status]':{textContent:''},
  };
  const ctx=vm.createContext({
    URL,Map,Set,Date,Promise,
    location:{origin:ORIGIN},
    document:{
      body:{dataset:{libraryPage:'none'}},
      querySelector(selector){return containers[selector]||null},
      querySelectorAll(){return []},
    },
    escapeHtml,
    getSupabase(){throw new Error('No backend allowed in unit test')},
    requireUser(){return Promise.reject(new Error('Connexion requise'))},
    projectStatusLabel(value){return value||'actif'},
    setStatus(){},
    console,
    ...override,
  });
  // Les imports ESM ne sont pas nécessaires pour vérifier la fonction réelle
  // et les interpolations du template client dans une VM isolée.
  const withoutImport=source.replace(/^import [^\n]+\n/m,'');
  vm.runInContext(withoutImport,ctx,{filename:file,timeout:2000});
  return {ctx,source,containers,href:vm.runInContext('safeLibraryHref',ctx)};
}
function guardCases(href,label){
  for(const good of [
    '/', '/projets/sinjira/', '/projets/sinjira/romans/lire-demo.html',
    '/compte/projet.html?slug=roman-1', '/compte/liseuse.html?edition=demo',
    '/projets/sinjira/#livres'
  ]){
    assert.equal(href(good),good,label+': lien local normal refusé : '+good);
  }
  for(const bad of [
    '',null,undefined,[],{},'https://www.benoitcantin.com/projets/sinjira/',
    'https://evil.invalid/','http://evil.invalid/','javascript:alert(1)',
    'data:text/html,<svg/onload=alert(1)>','//evil.invalid/',
    '///evil.invalid/','/\\evil.invalid/','/compte/../admin/',
    '/compte/%2e%2e/admin/','/compte/%2E/admin/','/compte/a/%2e%2e/admin/',
    '/foo\nbar','/foo\rbar','/foo\tbar','/foo\u007fbar',
    ' /projets/sinjira/','/projets/sinjira/ ', '/evil" onclick="alert(1)'
  ]){
    assert.equal(href(bad),'',label+': destination non sûre acceptée : '+String(bad));
  }
}
async function main(){
  const environments=FILES.map(boot);
  for(let i=0;i<environments.length;i++)guardCases(environments[i].href,FILES[i]);

  const legacy=environments[0].source;
  for(const required of [
    'const playHref=safeLibraryHref(p.play_path);',
    'const publicHref=safeLibraryHref(p.public_path),playHref=safeLibraryHref(p.play_path);',
    'href="${escapeHtml(playHref)}"','href="${escapeHtml(publicHref)}"',
  ])assert.ok(legacy.includes(required),'Legacy library: garde absente : '+required);
  assert.ok(!legacy.includes('href="${escapeHtml(p.play_path)}"'));
  assert.ok(!legacy.includes('href="${escapeHtml(p.public_path)}"'));

  const v24=environments[1],v24text=v24.source;
  for(const required of [
    'const playHref=safeLibraryHref(project.play_path);',
    'const demoHref=safeLibraryHref(novel.demo_path),publicHref=safeLibraryHref(novel.public_path)',
    'href="${escapeHtml(playHref)}"','href="${escapeHtml(demoHref)}"',
    'href="${escapeHtml(publicHref)}"',
  ])assert.ok(v24text.includes(required),'V24 library: garde absente : '+required);
  assert.ok(!v24text.includes('href="${escapeHtml(project.play_path)}"'));
  assert.ok(!v24text.includes('href="${escapeHtml(novel.demo_path)}"'));
  v24.ctx.project={
    id:'11111111-1111-4111-8111-111111111111',slug:'fracture-du-reseau-mere',
    name:'Test',description:'Local',status:'active',visibility:'public',
    play_path:'javascript:alert(1)',allow_tester_requests:false,
  };
  vm.runInContext('renderProjects([project],[],[],[],false,false)',v24.ctx);
  const projects=v24.containers['[data-project-library]'];
  assert.ok(!projects.innerHTML.includes('javascript:'));
  assert.ok(!projects.innerHTML.includes('>Jouer</a>'));
  v24.ctx.project.play_path='/projets/sinjira/jeux/';
  vm.runInContext('renderProjects([project],[],[],[],false,false)',v24.ctx);
  assert.ok(projects.innerHTML.includes('href="/projets/sinjira/jeux/"'));

  v24.ctx.book={sinjira_novels:{
    title:'Roman',description:'Demo',demo_path:'javascript:alert(1)',
    public_path:'//evil.invalid/',
  },progress_percent:5,last_page:1};
  vm.runInContext('renderReads([book])',v24.ctx);
  const reading=v24.containers['[data-library-reads]'].innerHTML;
  assert.ok(!reading.includes('javascript:')&&!reading.includes('//evil.invalid'));
  assert.ok(reading.includes('href="/projets/sinjira/romans/"'));

  const hub=environments[2].source;
  for(const required of [
    'safeLibraryHref(project.public_path)',
    'safeLibraryHref(project.play_path)',
    'href="\'+escapeHtml(path)+\'"',
    'href="\'+escapeHtml(play)+\'"',
  ])assert.ok(hub.includes(required),'V26 hub: garde absente : '+required);
  assert.ok(!hub.includes('const safeLink='));
  console.log('PASS: 3 bibliothèques SINJIRA, liens internes, injection de protocoles et rendus V24 protégés.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
