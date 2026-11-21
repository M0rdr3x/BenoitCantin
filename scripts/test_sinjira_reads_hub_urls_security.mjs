#!/usr/bin/env node
// Tests des vraies fonctions de rendu — aucun appel réseau ni secret.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const read=path=>readFileSync(resolve(ROOT,path),'utf8');
const reads=read('assets/js/sinjira-reads-v24-4-61.js');
const hub=read('assets/js/sinjira-library-hub-v26.js');
const shared=read('assets/js/sinjira-supabase.js');
const origin='https://www.benoitcantin.com';
const from=shared.indexOf('export function safeInternalDestination(');
const to=shared.indexOf('export async function requireUser(',from);
assert.ok(from>=0&&to>from);
const safeInternalDestination=vm.runInNewContext(
  shared.slice(from,to).replace(/^export /,'')+'\nsafeInternalDestination',
  {URL,location:{origin}},{timeout:3000}
);
const escapeHtml=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;')
  .replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');

function harness(source,entry,fixtures) {
  const elements=new Map();
  const element=name=>{
    if(!elements.has(name))elements.set(name,{
      innerHTML:'',textContent:'',dataset:{},disabled:false,style:{},
      querySelectorAll:()=>[],addEventListener(){}
    });
    return elements.get(name);
  };
  const document={
    body:{dataset:{v18Page:'reads-v24-4-61'}},
    querySelector:element,querySelectorAll:()=>[]
  };
  const query=table=>{
    const chain={
      select(){return this},in(){return this},eq(){return this},order(){return this},
      then(ok,bad){return Promise.resolve({data:fixtures[table]??[],error:null}).then(ok,bad);}
    };
    return chain;
  };
  const client={from:query,rpc:async()=>({data:false,error:null})};
  const ctx=vm.createContext({
    document,location:{origin},URL,URLSearchParams,
    getSupabase:()=>client,requireUser:async()=>({id:'fixture-user'}),
    safeInternalDestination,escapeHtml,setStatus(){},
    console:{error(){},warn(){}},prompt:()=>'',confirm:()=>false
  });
  const stripped=source.replace(/^import [^\n]+\n/,'');
  assert.notEqual(stripped,source,'test doit exécuter le fichier source réel');
  const tail=entry==='load'?/\nload\(\)\.catch\(error=>\{[\s\S]*$/:/\ninit\(\)\.catch\(error=>\{[\s\S]*$/;
  const executable=stripped.replace(tail,'');
  assert.notEqual(executable,stripped,'invocation automatique du module doit être isolée');
  vm.runInContext(executable+'\nglobalThis.__run = '+entry+';',ctx,{timeout:3500});
  return {run:()=>ctx.__run(),html:selector=>element(selector).innerHTML};
}
const maliciousNovel={
  id:'evil" data-exploit="yes',slug:'roman-test',
  title:'Titre <script>alert(1)</script>',subtitle:'Titre public',
  description:'Description publique',status:'published',
  demo_path:'javascript:alert(1)',public_path:'javascript:alert(2)',
};
const validNovel={
  id:'00000000-0000-4000-8000-000000000001',slug:'roman-valide',
  title:'Roman valide',description:'Édition',status:'published',
  demo_path:'/projets/sinjira/romans/lire-demo.html',
  public_path:'/projets/sinjira/romans/'
};
const expectedNovel={
  id:'00000000-0000-4000-8000-000000000002',slug:'la-cendre-du-jugement',
  title:'La Cendre',status:'published',
  demo_path:'/projets/sinjira/romans/lire-demo.html',
  public_path:'/projets/sinjira/romans/'
};
const maliciousProject={
  id:'00000000-0000-4000-8000-000000000003',slug:'reseau-mere-resistance',
  name:'Projet <svg onload=alert(1)>',
  description:'Projet sécurisé',public_path:'javascript:alert(3)',
  play_path:'data:text/html,alert(4)',allow_tester_requests:false
};
const validProject={
  id:'00000000-0000-4000-8000-000000000004',slug:'reseau-mere-resistance',
  name:'Jeu valide',description:'Projet jouable',
  public_path:'/projets/sinjira/jeux/reseau-mere-resistance/?edition=v2',
  play_path:'/projets/sinjira/jeux/reseau-mere-resistance/',
  allow_tester_requests:false
};
const fixtureReads={
  sinjira_novels:[maliciousNovel,validNovel,expectedNovel],
  sinjira_reader_library:[]
};
const fixtureHub={
  projects:[maliciousProject,validProject],
  project_access:[],access_requests:[]
};
function hrefs(html){
  return [...html.matchAll(/href="([^"]*)"/g)].map(m=>m[1]);
}
function requireSafeAnchors(html){
  const links=hrefs(html);
  assert.ok(links.length>0,'des liens internes doivent rester utilisables');
  for(const href of links){
    assert.ok(href.startsWith('/')&&!href.startsWith('//'),'lien non local: '+href);
    assert.doesNotMatch(href,/^(?:javascript|data|https?):/i);
  }
  assert.doesNotMatch(html,/href="(?:javascript|data|https?):/i);
  assert.doesNotMatch(html,/<script\b|<svg\b[^>]*onload=/i);
}

test('contrat commun : refuse les destinations ambiguës et conserve les chemins internes',()=>{
  for(const value of ['javascript:alert(1)','data:text/html,a','https://evil.example/a',
    '//evil.example/a','/%2f%2fevil','/dir/../index.html','/x\\evil',' /projets/sinjira/']){
    assert.equal(safeInternalDestination(value,''),'','interdiction '+value);
  }
  assert.equal(safeInternalDestination('/projets/sinjira/romans/?edition=v2',''),
    '/projets/sinjira/romans/?edition=v2');
});

test('vrai catalogue Mes lectures : bloque les démos et pages malveillantes',async()=>{
  const app=harness(reads,'load',fixtureReads);
  await app.run();
  const html=app.html('[data-reader-library]');
  requireSafeAnchors(html);
  assert.match(html,/href="\/projets\/sinjira\/romans\/lire-demo.html"/);
  assert.match(html,/href="\/projets\/sinjira\/romans\/"/);
  assert.match(html,/href="\/compte\/liseuse.html\?edition=demo"/);
  assert.match(html,/&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
  assert.match(html,/data-v2461-novel="evil&amp;quot; data-exploit="|data-v2461-novel="evil&quot; data-exploit=&quot;yes"/);
});

test('vrai hub : refuse la navigation externe et conserve les requêtes internes',async()=>{
  const app=harness(hub,'init',fixtureHub);
  await app.run();
  const html=app.html('[data-library-account-games]');
  requireSafeAnchors(html);
  assert.match(html,/href="\/projets\/sinjira\/jeux\/"/);
  assert.match(html,/href="\/projets\/sinjira\/jeux\/reseau-mere-resistance\/\?edition=v2"/);
  assert.match(html,/href="\/projets\/sinjira\/jeux\/reseau-mere-resistance\/"/);
  assert.match(html,/&lt;svg onload=alert\(1\)&gt;/);
});

test('mutation : un lien public brut est détecté comme régression XSS',async()=>{
  const snippet="const publicHref=safeInternalDestination(novel.public_path,'/projets/sinjira/romans/');";
  assert.ok(reads.includes(snippet));
  const mutated=reads.replace(snippet,'const publicHref=novel.public_path;');
  const app=harness(mutated,'load',fixtureReads);
  await app.run();
  assert.match(app.html('[data-reader-library]'),/href="javascript:alert\(2\)"/);
});

test('mutation : régression du garde-fou dans le hub détectée',async()=>{
  const snippet="const path=safeInternalDestination(project.public_path,'/projets/sinjira/jeux/');";
  assert.ok(hub.includes(snippet));
  const mutated=hub.replace(snippet,'const path=project.public_path;');
  const app=harness(mutated,'init',fixtureHub);
  await app.run();
  assert.match(app.html('[data-library-account-games]'),/href="javascript:alert\(3\)"/);
});
