#!/usr/bin/env node
// Contrat anti-XSS : tester les véritables rendus des bibliothèques SINJIRA.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const legacy=readFileSync(resolve(root,'assets/js/sinjira-library.js'),'utf8');
const modern=readFileSync(resolve(root,'assets/js/sinjira-library-v24-4-61.js'),'utf8');
const shared=readFileSync(resolve(root,'assets/js/sinjira-supabase.js'),'utf8');
const origin='https://www.benoitcantin.com';

function esc(value='') {
  return String(value).replaceAll('&','&amp;').replaceAll('<','&lt;')
    .replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
}
const head=shared.indexOf('export function safeInternalDestination(');
const tail=shared.indexOf('export async function requireUser(',head);
assert.ok(head>=0 && tail>head,'la destination locale doit être définie');
const safeInternalDestination=vm.runInNewContext(
  shared.slice(head,tail).replace(/^export /,'')+'\nsafeInternalDestination',
  {URL,location:{origin}}, {timeout:3000}
);

function fakeDom() {
  const map=new Map();
  const node=key=>{
    if(!map.has(key))map.set(key,{
      innerHTML:'',textContent:'',value:'',style:{},dataset:{},
      querySelectorAll(){return []},
      addEventListener(){},
      setAttribute(){}
    });
    return map.get(key);
  };
  return {map,node,document:{body:{dataset:{libraryPage:''}},querySelector:node,querySelectorAll(){return []}}};
}
const invalidProject={
  id:'00000000-0000-4000-8000-000000000001',slug:'unprojet',name:'Projet <script>',
  status:'active',description:'Édition privée',
  play_path:'javascript:alert(1)',public_path:'//evil.example/landing',
  cover_url:'https://tracker.example/collect.png',visibility:'public',allow_tester_requests:false
};
const validProject={
  id:'00000000-0000-4000-8000-000000000002',slug:'fracture-du-reseau-mere',
  name:'Projet sécurisé',status:'active',description:'Jeu',
  play_path:'/projets/sinjira/jeux/fracture-du-reseau-mere/',
  public_path:'/projets/sinjira/',cover_url:'/assets/media/cover.webp',
  visibility:'public',allow_tester_requests:false
};
const novInvalid={
  id:'00000000-0000-4000-8000-000000000003',
  title:'Roman <img src=x onerror=alert(9)>',description:'Suivi',
  demo_path:'data:text/html,alert(1)',public_path:'https://evil.example/novel'
};
const novValid={
  id:'00000000-0000-4000-8000-000000000004',
  title:'Roman valide',description:'Lecture',
  demo_path:'/projets/sinjira/romans/lire-demo.html',
  public_path:'/projets/sinjira/romans/'
};

function assertSafeMarkup(html) {
  const hrefs=[...html.matchAll(/href="([^"]*)"/g)].map(m=>m[1]);
  assert.ok(hrefs.length>0,'au moins un lien légitime doit rester affiché');
  for(const href of hrefs) {
    assert.ok(href.startsWith('/')&&!href.startsWith('//'),'destination locale obligatoire : '+href);
    assert.doesNotMatch(href,/javascript:|data:|https?:/i);
  }
  assert.doesNotMatch(html, /<script\b|<img\b[^>]*onerror=/i);
  assert.doesNotMatch(html, /tracker\.example|evil\.example|javascript:|data:text\/html/);
}
function loadSource(source,dom,{db=null,entry='legacy'}={}) {
  let executable=source.replace(/^import [^\n]+\n/gm,'');
  assert.notEqual(executable,source,'le test doit charger un fichier ES module réel');
  if(entry==='legacy') {
    executable=executable.replace(/\(async\(\)=>\{user=await requireUser\(\);[\s\S]*$/,'');
  } else {
    executable=executable.replace(/init\(\)\.catch\(error=>\{[\s\S]*$/,'');
  }
  const query=(table)=>{
    const obj={
      select(){return obj},eq(){return obj},in(){return obj},order(){return obj},
      maybeSingle:async()=>({data:table==='projects'?invalidProject:null,error:null}),
      then(ok,fail){return Promise.resolve({data:db?.[table]??[],error:null}).then(ok,fail)}
    };return obj;
  };
  const context=vm.createContext({
    document:dom.document,location:{origin,search:'?slug=unprojet',href:''},
    URL,URLSearchParams,Date,Map,Set,Math,Number,Promise,
    getSupabase:()=>({from:query}),escapeHtml:esc,safeInternalDestination,
    requireUser:async()=>({id:'fixture'}),setStatus(){},roleLabel:v=>v,
    projectStatusLabel:v=>v,isSinjiraOwner:()=>false,
    console:{warn(){},error(){}}
  });
  vm.runInContext(executable+'\nglobalThis.__api = { renderProjects: typeof renderProjects === "function" ? renderProjects : null, renderReads: typeof renderReads === "function" ? renderReads : null, library: typeof library === "function" ? library : null, project: typeof project === "function" ? project : null, cover, setFixtureUser(value){ if(typeof user !== "undefined") user=value; } };',context,{timeout:5000});
  return context.__api;
}

test('le filtre réutilisé refuse les destinations et médias externes',()=>{
  for(const bad of ['javascript:alert(1)','data:text/html,boom','//example.org/',
    'https://example.org/','/%2f%2fevil','/dir/../x','/a\\b',' /valid']){
    assert.equal(safeInternalDestination(bad,''),'','refus de '+bad);
  }
  assert.equal(safeInternalDestination('/projets/sinjira/jeux/',''),'/projets/sinjira/jeux/');
});

test('bibliothèque historique : rendu réel des cartes et couvertures sans injections',async()=>{
  const dom=fakeDom();
  const api=loadSource(legacy,dom,{db:{projects:[invalidProject,validProject],
    documents:[],access_requests:[],project_access:[]}});
  api.setFixtureUser({id:'fixture'});
  await api.library();
  const html=dom.node('[data-project-library]').innerHTML;
  assertSafeMarkup(html);
  assert.match(html,/href="\/projets\/sinjira\/jeux\/fracture-du-reseau-mere\/"/);
  assert.match(html,/&lt;script&gt;/);
  assert.match(html,/src="\/assets\/media\/sinjira-emblem.webp"/);
  assert.match(html,/src="\/assets\/media\/cover.webp"/);
});

test('fiche projet historique : liens publics et de jeu malveillants exclus',async()=>{
  const dom=fakeDom();
  const api=loadSource(legacy,dom,{db:{project_access:[],documents:[],playtests:[]}});
  api.setFixtureUser({id:'fixture'});
  await api.project();
  const html=dom.node('[data-project-actions]').innerHTML;
  assert.equal(html,'','aucun lien arbitraire ne peut être affiché');
  assert.equal(dom.node('[data-project-cover]').src,'/assets/media/sinjira-emblem.webp');
});

test('bibliothèque actuelle : projets, couvertures et démos des romans filtrés',()=>{
  const dom=fakeDom();
  const api=loadSource(modern,dom,{entry:'modern'});
  api.renderProjects([invalidProject,validProject],[],[],[],false,false);
  const projects=dom.node('[data-project-library]').innerHTML;
  assertSafeMarkup(projects);
  assert.match(projects,/href="\/projets\/sinjira\/jeux\/fracture-du-reseau-mere\/"/);
  assert.match(projects,/src="\/assets\/media\/sinjira-emblem.webp"/);
  api.renderReads([
    {novel:novInvalid,progress_percent:0},
    {novel:novValid,progress_percent:0},
  ].map(x=>({sinjira_novels:x.novel,progress_percent:x.progress_percent})));
  const reads=dom.node('[data-library-reads]').innerHTML;
  assertSafeMarkup(reads);
  assert.match(reads,/href="\/projets\/sinjira\/romans\/lire-demo.html"/);
  assert.match(reads,/&lt;img src=x onerror=alert\(9\)&gt;/);
});

test('mutation négative : retirer le validateur réintroduit un lien dangereux',async()=>{
  const signature="const playHref=safeInternalDestination(p.play_path,'');";
  assert.ok(legacy.includes(signature));
  const mutated=legacy.replace(signature,'const playHref=p.play_path;');
  assert.notEqual(mutated,legacy);
  const dom=fakeDom();
  const api=loadSource(mutated,dom,{db:{projects:[invalidProject],documents:[],access_requests:[],project_access:[]}});
  api.setFixtureUser({id:'fixture'});
  await api.library();
  assert.match(dom.node('[data-project-library]').innerHTML,/href="javascript:alert\(1\)"/);
});
