'use strict';
/* Exécute les vraies fonctions de la bibliothèque sans comptes ni réseau. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

const file=path.join(__dirname,'../assets/js/sinjira-library-v24-4-61.js');
const original=fs.readFileSync(file,'utf8');
const sharedFileContent=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-supabase.js'),'utf8');
const routeStart='// BEGIN SINJIRA_LIBRARY_ROUTE';
const routeEnd='// END SINJIRA_LIBRARY_ROUTE';
assert.equal(sharedFileContent.split(routeStart).length,2);
assert.equal(sharedFileContent.split(routeEnd).length,2);
const routeCode=sharedFileContent.split(routeStart)[1].split(routeEnd)[0]
  .replaceAll('export function ','function ');
const routeEnvironment={URL,location:{origin:'https://www.benoitcantin.com'}};
vm.runInNewContext(routeCode+'\nglobalThis.validateRoute=safeLibraryRoute;',
  routeEnvironment,{filename:'sinjira-supabase.js/library-route'});
const safeLibraryRoute=routeEnvironment.validateRoute;
const coverStart='// BEGIN SINJIRA_LIBRARY_COVER';
const coverEnd='// END SINJIRA_LIBRARY_COVER';
assert.equal(sharedFileContent.split(coverStart).length,2);
assert.equal(sharedFileContent.split(coverEnd).length,2);
const coverCode=sharedFileContent.split(coverStart)[1].split(coverEnd)[0]
  .replaceAll('export function ','function ');
const coverEnvironment={safeLibraryRoute};
vm.runInNewContext(coverCode+'\nglobalThis.validateCover=safeLibraryCover;',
  coverEnvironment,{filename:'sinjira-supabase.js/library-cover'});
const safeLibraryCover=coverEnvironment.validateCover;
assert.match(original,/^import\s+\{getSupabase/);
assert.match(original,/\ninit\(\)\.catch\(/);
const code=original.replace(/^import[^\n]*\n/,'')
  .replace(/\ninit\(\)\.catch\([\s\S]*$/,'');
const elements=new Map();
const document={
  querySelector(selector){return elements.get(selector)||null;},
  querySelectorAll(){return [];}
};
const sandbox={
  document,
  escapeHtml(value){return String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');},
  projectStatusLabel(value){return String(value||'');},
  Date,URL,location:{origin:'https://www.benoitcantin.com'},
  safeLibraryRoute,
  safeLibraryCover,
  console,
};
vm.runInNewContext(code+'\nglobalThis.testAPI={activeProjectAccess,canOpenProject,safeProjectPlayPath,setCount,renderProjects,renderReads};',sandbox,{filename:file});
const api=sandbox.testAPI;
const publicProject={id:'pub',slug:'public',name:'Public',visibility:'public',status:'open',play_path:'/projets/sinjira/jeux/',allow_tester_requests:false};
const memberProject={id:'member',slug:'compte',name:'Compte',visibility:'account',status:'open'};
const privateProject={id:'priv',slug:'prive',name:'Privé',visibility:'restricted',status:'planned',play_path:'/projets/sinjira/jeux/',allow_tester_requests:true};
const fixedNow=Date.parse('2026-10-14T12:00:00Z');

test('compte gratuit: public et compte accessibles, projet privé verrouillé',()=>{
  const rights=api.activeProjectAccess([],fixedNow);
  assert.equal(api.canOpenProject(publicProject,rights,false,false),true);
  assert.equal(api.canOpenProject(memberProject,rights,false,false),true);
  assert.equal(api.canOpenProject(privateProject,rights,false,false),false);
  assert.equal(api.canOpenProject(privateProject,rights,true,false),true);
  assert.equal(api.canOpenProject(privateProject,rights,false,true),true);
});

test('droits actifs admis; expirations et dates malformées refusées',()=>{
  for(const expires_at of ['2026-10-15T00:00:00Z',null]){
    const rights=api.activeProjectAccess([{project_id:'priv',access_level:'tester',expires_at}],fixedNow);
    assert.equal(api.canOpenProject(privateProject,rights,false,false),true);
  }
  for(const expires_at of ['2026-10-14T11:59:59Z','2026-10-14T12:00:00Z','invalid']){
    const rights=api.activeProjectAccess([{project_id:'priv',access_level:'tester',expires_at}],fixedNow);
    assert.equal(api.canOpenProject(privateProject,rights,false,false),false);
  }
  for(const invalid of ['', 'revoked', 'admin', 'viewer']){
    assert.equal(api.canOpenProject(privateProject,api.activeProjectAccess([{project_id:'priv',access_level:invalid}],fixedNow),false,false),false);
  }
});

test('URL jouer: liens internes uniquement, pas javascript ou protocole relatif',()=>{
  assert.equal(api.safeProjectPlayPath('/projets/sinjira/jeux/'),'/projets/sinjira/jeux/');
  for(const bad of ['javascript:alert(1)','https://evil.test','//evil.test/path','/\\evil.test','/foo\nbar']){
    assert.equal(api.safeProjectPlayPath(bad),'',bad);
  }
});

test('couvertures: aucune image distante, technique ou exécutable dans le registre',()=>{
  const allowed=[
    '/assets/media/sinjira-emblem.webp',
    '/assets/media/sinjira-livre-1-cover-480.webp',
    '/assets/media/sinjira-fracture-du-reseau-mere-officiel.png',
    '/assets/media/sinjira-jeux-banniere-2026.webp'
  ];
  for(const value of allowed){
    assert.equal(safeLibraryCover(value),value);
  }
  const forbidden=[
    'https://tracker.example/visitor.jpg',
    '//tracker.example/image.webp',
    'http://www.benoitcantin.com/assets/media/sinjira-emblem.webp',
    'data:image/svg+xml,<svg/onload=alert(1)>',
    'javascript:alert(1)',
    '/assets/media/spy.svg',
    '/assets/media/README.md',
    '/supabase/config.toml',
    '/scripts/validate_site.py',
    '/assets/icons/icon.png',
    '/assets/media/../technical/image.webp',
    '/assets/media/%73injira-cover.webp',
    '/assets/media/sinjira-emblem.webp?visitor=123',
    '/assets/media/sinjira-emblem.webp#fragment',
    '/assets/media/cover.webp ',
    null,undefined,{},[],42
  ];
  for(const value of forbidden){
    assert.equal(safeLibraryCover(value),'/assets/media/sinjira-emblem.webp',
      'Image de registre non approuvée : '+String(value));
  }

  const box={innerHTML:''};
  elements.set('[data-project-library]',box);
  for(const candidate of forbidden){
    api.renderProjects([{...publicProject,cover_url:candidate}],[],[],[],false,false);
    assert.match(box.innerHTML,/src="\/assets\/media\/sinjira-emblem.webp"/);
    assert.doesNotMatch(box.innerHTML,/(?:tracker\.example|data:image|javascript:|\/supabase\/config)/);
  }
  api.renderProjects([{
    ...publicProject,slug:'fracture-du-reseau-mere',cover_url:'https://tracker.example/pixel.webp'
  }],[],[],[],false,false);
  assert.match(box.innerHTML,/src="\/assets\/media\/sinjira-fracture-du-reseau-mere-officiel.webp"/);
  api.renderProjects([{
    ...publicProject,slug:'fracture-du-reseau-mere',
    cover_url:'/assets/media/sinjira-fracture-du-reseau-mere-officiel.png'
  }],[],[],[],false,false);
  assert.match(box.innerHTML,/src="\/assets\/media\/sinjira-fracture-du-reseau-mere-officiel.png"/);
});

test('routes du registre: seules les destinations locales canoniques restent cliquables',()=>{
  for(const route of [
    '/projets/sinjira/jeux/',
    '/projets/sinjira/romans/lire-demo.html',
    '/projets/sinjira/romans/?lang=fr#contenu',
    '/compte/bibliotheque.html#livre-i',
  ]){
    assert.equal(safeLibraryRoute(route),route);
    assert.equal(api.safeProjectPlayPath(route),route);
  }
  const forbidden=[
    'javascript:alert(1)','data:text/html,<svg/onload=alert(1)>',
    'https://evil.example/roman.pdf','//evil.example/roman.pdf',
    '/\\evil.example/roman.pdf','/%2f%2fevil.example/roman.pdf',
    '/%5cevil.example/roman.pdf','/projets/%2e%2e/admin/',
    '/projets/sinjira/../admin/','/secret%00file',
    '/projets/sinjira/romans/ ',' /projets/sinjira/romans/',
    '/projets/sinjira/%zz','/projets/sinjira/jeux/\nnext',
    null,[],{toString:()=>'/projets/sinjira/romans/'},
  ];
  for(const value of forbidden){
    assert.equal(safeLibraryRoute(value),'','Destination inconnue interdite : '+String(value));
    assert.equal(api.safeProjectPlayPath(value),'','Jouer non canonique : '+String(value));
  }
});

test('routes du registre: 14 destinations techniques de la barrière Pages ne deviennent jamais des liens',()=>{
  const exposed=[
    '/supabase/config.toml',
    '/tests/e2e/test_public_site.py',
    '/mobile-native/App.tsx',
    '/scripts/validate_site.py',
    '/scripts/audit_pages_jekyll.py',
    '/.github/workflows/validate-site.yml',
    '/docs/README.md',
    '/_config.yml',
    '/assets/icons/README.md',
    '/projets/projet-nova/netlify.toml',
    '/projets/projet-nova/UPLOAD_GITHUB.md',
    '/projets/projet-nova/SECURITY.md',
    '/projets/sinjira/codex/livre-i-delivery-contract.json',
    '/scripts/build_netlify_public.py'
  ];
  assert.equal(exposed.length,14);
  const technical=[
    ...exposed,
    '/supabase/index.html','/scripts/guide.html','/tests/assets/index.html',
    '/docs/faq.html','/.github/workflows/index.html','/mobile-native/index.html',
    '/projets/sinjira/codex/index.html','/projets/sinjira/CODEX/draft.html',
    '/compte/private.sql','/projets/sinjira/romans/config.yml',
    '/projets/sinjira/jeux/app.tsx','/projets/sinjira/logiciels/source.py',
    '/assets/icons/README.md?raw=true#source'
  ];
  for(const candidate of technical){
    assert.equal(safeLibraryRoute(candidate),'','Fichier technique accessible : '+candidate);
    assert.equal(api.safeProjectPlayPath(candidate),'','Jouer ne doit jamais viser : '+candidate);
  }
  for(const ok of [
    '/projets/sinjira/romans/','/projets/sinjira/jeux/',
    '/projets/sinjira/logiciels/','/compte/projet.html?slug=jeu#contenu',
    '/projets/projet-nova/boussole-electorale.html',
    '/projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf'
  ]) assert.equal(safeLibraryRoute(ok),ok,'Route utilisateur légitime : '+ok);
});

test('routes de catalogue: l’encodage des lettres ne masque pas un chemin technique',()=>{
  const aliases=[
    '/%73upabase/functions/private.html',
    '/su%70abase/config.html','/%53UPABASE/index.html',
    '/%73cripts/audit.html','/scrip%74s/report.html',
    '/%74ests/reports/index.html','/%64ocs/private.html',
    '/.%67ithub/workflows/actions.html',
    '/%6dobile-native/app.html','/%6eode_modules/library.html',
    '/projets/sinjira/%63odex/private.html',
    '/projets/sinjira/cod%65x/internal.html',
    '/assets/media/%52EADME.html',
    '/projets/sinjira/%25encoded/index.html',
    '/projets/sinjira/romans/%20test.html'
  ];
  for(const route of aliases){
    assert.equal(safeLibraryRoute(route),'','Route encodée refusée: '+route);
    assert.equal(api.safeProjectPlayPath(route),'','Jeu ne doit pas afficher: '+route);
  }
  // Les requêtes et fragments encodés restent légitimes, seuls les
  // segments du chemin de destination doivent être canoniques.
  const useful=[
    '/projets/sinjira/romans/?recherche=La%20Cendre',
    '/compte/projet.html?slug=jeu%2Dtest#contenu',
    '/projets/sinjira/logiciels/#t%C3%A9l%C3%A9chargements'
  ];
  for(const route of useful)assert.equal(safeLibraryRoute(route),route);
});

test('progression des romans: données hors plage et pages incohérentes sont normalisées',()=>{
  const box={innerHTML:''};
  elements.set('[data-library-reads]',box);
  const base={sinjira_novels:{title:'La Cendre du Jugement',
    demo_path:'/projets/sinjira/romans/',public_path:'/projets/sinjira/romans/'}};
  const cases=[
    {progress_percent:'NaN',last_page:'not-a-page',progress:0,page:null},
    {progress_percent:'Infinity',last_page:-9,progress:0,page:null},
    {progress_percent:-35,last_page:0,progress:0,page:null},
    {progress_percent:250,last_page:Number.MAX_SAFE_INTEGER+1,progress:100,page:null},
    {progress_percent:32.6,last_page:120,progress:33,page:120},
    {progress_percent:99.9,last_page:'18',progress:100,page:18},
    {progress_percent:null,last_page:null,progress:0,page:null},
  ];
  for(const row of cases){
    api.renderReads([{...base,progress_percent:row.progress_percent,last_page:row.last_page}]);
    assert.match(box.innerHTML,new RegExp('Progression : '+row.progress+'%'));
    assert.match(box.innerHTML,new RegExp('style="width:'+row.progress+'%"'));
    assert.doesNotMatch(box.innerHTML,/NaN|Infinity|page -|page 0\b|page undefined/);
    if(row.page===null)assert.doesNotMatch(box.innerHTML,/ · page /);
    else assert.match(box.innerHTML,new RegExp(' · page '+row.page+'</p>'));
  }
});

test('lectures suivies: chemins démo/roman issus du registre ne peuvent pas rediriger hors SINJIRA',()=>{
  const box={innerHTML:''};
  elements.set('[data-library-reads]',box);
  const novel={title:'La Cendre du Jugement',description:'Essai',
    demo_path:'/projets/sinjira/romans/lire-demo.html',
    public_path:'/projets/sinjira/romans/'};
  api.renderReads([{sinjira_novels:novel,progress_percent:15}]);
  assert.match(box.innerHTML,/Lire la démo|Continuer la lecture/);
  assert.match(box.innerHTML,/href="\/projets\/sinjira\/romans\/lire-demo.html"/);

  for(const malicious of [
    'javascript:alert(1)','https://evil.example/sinjira',
    '//evil.example/reader','/%2f%2fevil.example/a',
    '/projets/%2e%2e/admin/', '/\\evil.example/a',
    '/supabase/config.toml','/scripts/audit_pages_jekyll.py',
    '/docs/README.md','/projets/sinjira/codex/secret.html',
    '/%73upabase/private.html','/projets/sinjira/%63odex/private.html',
  ]){
    api.renderReads([{sinjira_novels:{...novel,demo_path:malicious,public_path:malicious},
      progress_percent:12}]);
    assert.doesNotMatch(box.innerHTML,/Continuer la lecture/);
    assert.doesNotMatch(box.innerHTML,/>Lire la démo</);
    assert.match(box.innerHTML,/href="\/projets\/sinjira\/romans\/">Page du roman</);
    assert.doesNotMatch(box.innerHTML,/href="(?:javascript:|https:\/\/evil|\/\/evil|\/%2f)/i);
  }
});

test('rendu projets: aucun bouton Jouer ou Ouvrir sur un projet restreint',()=>{
  const box={innerHTML:''};
  elements.set('[data-project-library]',box);
  api.renderProjects([privateProject],[],[],[],false,false);
  assert.match(box.innerHTML,/Autorisation nécessaire pour ouvrir le projet/);
  assert.doesNotMatch(box.innerHTML,/Ouvrir l’espace/);
  assert.doesNotMatch(box.innerHTML,/>Jouer</);
  assert.match(box.innerHTML,/Demander accès testeur/);
  assert.match(box.innerHTML,/Documents sur autorisation/);

  const rights=[{project_id:'priv',access_level:'tester',expires_at:null}];
  api.renderProjects([privateProject],[],rights,[],false,false);
  assert.match(box.innerHTML,/Ouvrir l’espace/);
  assert.match(box.innerHTML,/>Jouer</);

  const hostile={...publicProject,play_path:'javascript:alert(1)'};
  api.renderProjects([hostile],[],[],[],false,false);
  assert.doesNotMatch(box.innerHTML,/href="javascript:/);
  assert.doesNotMatch(box.innerHTML,/>Jouer</);
  const technical={...publicProject,play_path:'/supabase/config.toml'};
  api.renderProjects([technical],[],[],[],false,false);
  assert.doesNotMatch(box.innerHTML,/>Jouer</);
  assert.doesNotMatch(box.innerHTML,/href="\/supabase\//);
});

test('compteur accessible: le libellé chargement disparaît après API',()=>{
  const attributes=new Map([['aria-label','En cours de vérification']]);
  const counter={
    textContent:'—',
    setAttribute(k,v){attributes.set(k,v);},
    removeAttribute(k){attributes.delete(k);}
  };
  elements.set('[data-library-entitlement-count]',counter);
  api.setCount('[data-library-entitlement-count]',3);
  assert.equal(counter.textContent,'3');
  assert.equal(attributes.has('aria-label'),false);
  api.setCount('[data-library-entitlement-count]','—');
  assert.equal(attributes.get('aria-label'),'Information momentanément indisponible');
});


// Vérifier également la page historique /compte/projet.html. Elle est
// chargée par un module différent de la bibliothèque v24.4.61.
const legacySource=fs.readFileSync(
  path.join(__dirname,'../assets/js/sinjira-library.js'),'utf8'
);
assert.match(legacySource,/rpc\('is_sinjira_owner'/);
assert.match(legacySource,/rpc\('is_sinjira_admin'/);
assert.doesNotMatch(legacySource,/isSinjiraOwner\(user\)/);
const autoInit=legacySource.lastIndexOf('\n(async()=>{');
assert.ok(autoInit>0,'Bootstrap legacy introuvable');
const legacyCode=legacySource.slice(0,autoInit)
  .replace(/^import[^\n]*\n/,'');
function legacyHarness(grants=[],roles={},extra={}){
  const docNodes=new Map();
  const getNode=(selector)=>{
    if(!docNodes.has(selector))docNodes.set(selector,{
      innerHTML:'',textContent:'',src:'',alt:'',
      querySelectorAll(){return [];}
    });
    return docNodes.get(selector);
  };
  const counters={documents:0,playtests:0};
  const project={
    id:'priv',slug:'test-prive',name:'Projet privé',
    status:'active',visibility:'restricted',
    description:'Aperçu du projet',
    public_path:'/projets/sinjira/jeux/',
    play_path:'/projets/sinjira/jeux/test/',
    allow_tester_requests:true
  };
  const response={data:project,error:null};
  const s={
    from(table){
      if(table==='projects')return {
        select(){return {eq(){return {maybeSingle:async()=>response}}}}
      };
      if(table==='project_access')return {
        select(){return {eq(){return Promise.resolve({
          data:grants,error:extra.accessError||null
        })}}}
      };
      if(table==='documents'){
        counters.documents++;
        return {select(){return {eq(){return {eq(){return {order:async()=>({data:[],error:null})}}}}}}};
      }
      if(table==='playtests'){
        counters.playtests++;
        return {select(){return {eq(){return {in(){return {order:async()=>({data:[],error:null})}}}}}}};
      }
      throw Error('Unexpected query '+table);
    }
  };
  const fakeDocument={
    body:{dataset:{libraryPage:'project'}},
    querySelector:getNode,
    querySelectorAll(){return []}
  };
  const env={
    document:fakeDocument,
    location:{search:'?slug=test-prive',href:''},
    getSupabase:()=>s,
    requireUser:async()=>({id:'mock-user'}),
    escapeHtml:v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;'),
    projectStatusLabel:v=>v,
    roleLabel:v=>v,
    safeLibraryRoute,
    safeLibraryCover,
    setStatus:()=>{},
    URLSearchParams,Date,console,
    prompt:()=>null,
    window:{open(){}}
  };
  vm.runInNewContext(legacyCode+
    '\nglobalThis.legacyAPI={verifiedProjectAccess,projectIsOpen,internalProjectPath,cover,project};'+
    '\nglobalThis.legacySet=(r)=>{user={id:"mock-user"};owner=!!r.owner;admin=!!r.admin};',
    env,{filename:'sinjira-library.js'});
  env.legacySet(roles);
  return {api:env.legacyAPI,project,counters,node:getNode};
}

test('legacy: couverture du détail projet toujours locale avec repli officiel',()=>{
  const ctx=legacyHarness();
  ctx.project.cover_url='https://tracker.example/reader-pixel.webp';
  assert.equal(ctx.api.cover(ctx.project),'/assets/media/sinjira-emblem.webp');
  ctx.project.cover_url='javascript:alert(1)';
  assert.equal(ctx.api.cover(ctx.project),'/assets/media/sinjira-emblem.webp');
  ctx.project.slug='reseau-mere-resistance';
  ctx.project.cover_url='/scripts/internal.webp';
  assert.equal(ctx.api.cover(ctx.project),
    '/assets/media/sinjira-reseau-mere-resistance-officiel.webp');
  ctx.project.cover_url='/assets/media/sinjira-reseau-mere-resistance-officiel.webp';
  assert.equal(ctx.api.cover(ctx.project),ctx.project.cover_url);
});

test('legacy: seuls player et tester non expirés débloquent un projet',()=>{
  const ctx=legacyHarness();
  const clock=Date.parse('2026-10-14T12:00:00Z');
  for(const level of ['revoked','admin','owner','']){
    const map=ctx.api.verifiedProjectAccess([{project_id:'priv',access_level:level}],clock);
    assert.equal(ctx.api.projectIsOpen(ctx.project,map,false,false),false,level);
  }
  for(const expires_at of ['invalid','2026-10-14T11:59:59Z']){
    const map=ctx.api.verifiedProjectAccess([{project_id:'priv',access_level:'tester',expires_at}],clock);
    assert.equal(ctx.api.projectIsOpen(ctx.project,map,false,false),false);
  }
  const map=ctx.api.verifiedProjectAccess([{project_id:'priv',access_level:'player',expires_at:null}],clock);
  assert.equal(ctx.api.projectIsOpen(ctx.project,map,false,false),true);
  assert.equal(ctx.api.projectIsOpen(ctx.project,new Map(),true,false),true);
  assert.equal(ctx.api.projectIsOpen(ctx.project,new Map(),false,true),true);
});

test('legacy: sans droit, page projet ne demande ni documents ni playtests privés',async()=>{
  const ctx=legacyHarness();
  await ctx.api.project();
  assert.equal(ctx.counters.documents,0);
  assert.equal(ctx.counters.playtests,0);
  assert.match(ctx.node('[data-project-role]').textContent,/Accès restreint/);
  assert.doesNotMatch(ctx.node('[data-project-actions]').innerHTML,/>Jouer</);
  assert.match(ctx.node('[data-project-documents]').innerHTML,/autorisation/);
  assert.match(ctx.node('[data-project-playtests]').innerHTML,/sans droit confirmé/);
});

test('legacy: droit valide ou rôle confirmé rend la page accessible',async()=>{
  for(const [grants,roles] of [
    [[{project_id:'priv',access_level:'player',expires_at:null}],{}],
    [[],{owner:true}],
    [[],{admin:true}]
  ]){
    const ctx=legacyHarness(grants,roles);
    await ctx.api.project();
    assert.equal(ctx.counters.documents,1);
    assert.equal(ctx.counters.playtests,1);
    assert.match(ctx.node('[data-project-actions]').innerHTML,/>Jouer</);
  }
});

test('legacy: API droits indisponible et chemins externes ne donnent aucun accès',async()=>{
  const ctx=legacyHarness([],{},{accessError:{message:'backend unavailable'}});
  await ctx.api.project();
  assert.equal(ctx.counters.documents,0);
  assert.doesNotMatch(ctx.node('[data-project-actions]').innerHTML,/>Jouer</);
  for(const bad of ['//evil.test','https://evil.test/','javascript:alert(1)',
    '/\\evil.test','/%2f%2fevil.test/private','/projets/%2e%2e/admin/',
    '/projets/sinjira/../admin/']){
    assert.equal(ctx.api.internalProjectPath(bad),'',bad);
  }
});

// Valider les vraies fonctions de fenêtre exportées par le module Supabase
// sans importer les dépendances réseau, ni ouvrir de compte de production.
const sharedSource=sharedFileContent;
const sharedStart='// BEGIN SINJIRA_DOCUMENT_WINDOW';
const sharedEnd='// END SINJIRA_DOCUMENT_WINDOW';
assert.equal(sharedSource.split(sharedStart).length,2,'Contrat de fenêtre unique requis');
assert.equal(sharedSource.split(sharedEnd).length,2,'Fin de contrat unique requise');
const sharedFunctions=sharedSource.split(sharedStart)[1].split(sharedEnd)[0]
  .replaceAll('export function ','function ');

function secureTabFixture(blocked=false){
  const visited=[],current=[],calls=[],tabs=[];
  const fakeLocation={origin:'https://www.benoitcantin.com',
    assign(value){current.push(value)}};
  const fakeWindow={open(url,target){
    calls.push([url,target]);
    if(blocked)return null;
    const tab={opener:{},closed:false,
      document:{title:'',body:{textContent:''}},
      location:{replace(value){visited.push(value)}},
      close(){this.closed=true}
    };
    tabs.push(tab);
    return tab;
  }};
  const ctx={window:fakeWindow,location:fakeLocation,URL};
  vm.runInNewContext(sharedFunctions+
    '\nglobalThis.documentsWindowAPI={prepareDocumentWindow,closeDocumentWindow,navigateDocumentWindow};',
    ctx,{filename:'sinjira-supabase.js/document-window'});
  return {api:ctx.documentsWindowAPI,visited,current,calls,tabs};
}

test('document: onglet réservé immédiatement, sans accès opener, puis lien HTTPS',()=>{
  const f=secureTabFixture();
  const tab=f.api.prepareDocumentWindow();
  assert.equal(f.calls.length,1);
  assert.equal(f.calls[0][0],'about:blank');
  assert.equal(f.calls[0][1],'_blank');
  assert.equal(tab.opener,null,'Le PDF ne doit pas piloter la bibliothèque');
  assert.match(tab.document.body.textContent,/Vérification des droits/);
  assert.equal(f.api.navigateDocumentWindow(tab,'https://private.example/signed?token=valid'),true);
  assert.deepEqual(f.visited,['https://private.example/signed?token=valid']);
  assert.deepEqual(f.current,[]);
  assert.equal(tab.closed,false);
});

test('document: pop-up bloquée = même onglet seulement après URL autorisée',()=>{
  const f=secureTabFixture(true);
  const tab=f.api.prepareDocumentWindow();
  assert.equal(tab,null);
  assert.equal(f.api.navigateDocumentWindow(tab,'/projets/sinjira/documents/demo.pdf'),true);
  assert.deepEqual(f.current,['/projets/sinjira/documents/demo.pdf']);
  assert.equal(f.calls.length,1);
});

test('document: destinations dangereuses interdites même si Edge répond ok',()=>{
  const forbidden=[
    'javascript:alert(1)','data:text/html,test','http://evil.example/file.pdf',
    '//evil.example/file.pdf','/\\evil.example/private.pdf',
    '/%2f%2fevil.example/private.pdf','/%5cevil.example/file.pdf',
    'https://user:pass@private.example/file.pdf','https://example.org/file.pdf ',
    ' https://example.org/file.pdf','https://example.org/\u0000bad'
  ];
  for(const url of forbidden){
    const f=secureTabFixture();
    const tab=f.api.prepareDocumentWindow();
    assert.equal(f.api.navigateDocumentWindow(tab,url),false,JSON.stringify(url));
    assert.equal(tab.closed,true,'Ne jamais garder la fenêtre sans droit');
    assert.deepEqual(f.current,[]);
    assert.deepEqual(f.visited,[]);
  }
});

test('document: fermeture d’onglet refusé et gestion fermeture idempotente',()=>{
  const f=secureTabFixture();
  const tab=f.api.prepareDocumentWindow();
  f.api.closeDocumentWindow(tab);
  f.api.closeDocumentWindow(tab);
  assert.equal(tab.closed,true);
  assert.deepEqual(f.visited,[]);
});

function deferredResult(){
  let resolve, reject;
  const promise=new Promise((yes,no)=>{resolve=yes;reject=no});
  return {promise,resolve,reject};
}
function securedLibraryFlow(which,blocked=false){
  const fixtures=secureTabFixture(blocked);
  const pending=deferredResult();
  const statusEvents=[];
  const env={
    document:{body:{dataset:{libraryPage:'tests'}},
      querySelector:()=>({}),querySelectorAll:()=>[]},
    getSupabase:()=>({functions:{invoke:(name,body)=>{
      statusEvents.push(['invoke',name,body]);
      return pending.promise;
    }}}),
    prepareDocumentWindow:()=>{
      statusEvents.push(['prepare']);
      return fixtures.api.prepareDocumentWindow();
    },
    closeDocumentWindow:fixtures.api.closeDocumentWindow,
    navigateDocumentWindow:fixtures.api.navigateDocumentWindow,
    setStatus:(_node,message,type)=>statusEvents.push(['status',message,type]),
    Date,URL,console,
  };
  if(which==='novel'){
    const trimmed=original.replace(/^import[^\n]*\n/,'')
      .replace(/\ninit\(\)\.catch\([\s\S]*$/,'');
    vm.runInNewContext(trimmed+'\nglobalThis.authorizedOpen=openFullNovel;',env);
  }else{
    vm.runInNewContext(legacyCode+'\nglobalThis.authorizedOpen=openDoc;',env);
  }
  return {call:env.authorizedOpen,pending,events:statusEvents,fixtures};
}

test('Livre I: réservation synchronique avant requête, puis lecture après contrôle Edge',async()=>{
  const ctx=securedLibraryFlow('novel');
  const button={disabled:false};
  const operation=ctx.call(button);
  assert.equal(button.disabled,true);
  assert.equal(ctx.fixtures.calls.length,1);
  assert.equal(ctx.events[0][0],'prepare','Pré-ouverture AVANT toute RPC asynchrone');
  assert.equal(ctx.events[2][1],'get-novel-file-url');
  assert.deepEqual(ctx.fixtures.visited,[]);
  ctx.pending.resolve({data:{ok:true,url:'https://private.example/novel.pdf'},error:null});
  await operation;
  assert.equal(button.disabled,false);
  assert.deepEqual(ctx.fixtures.visited,['https://private.example/novel.pdf']);
  assert.match(ctx.events.at(-1)[1],/10 minutes/);
});

test('Livre I: sans droit / fichier non prêt, fermer sans divulguer de lien',async()=>{
  for(const response of [
    {data:{ok:false,code:'FILE_NOT_READY',error:'En préparation'},error:null},
    {data:null,error:{message:'Non autorisé'}}
  ]){
    const ctx=securedLibraryFlow('novel');
    const button={disabled:false};
    const task=ctx.call(button);
    ctx.pending.resolve(response);
    await task;
    assert.equal(button.disabled,false);
    assert.equal(ctx.fixtures.tabs[0].closed,true);
    assert.deepEqual(ctx.fixtures.visited,[]);
    assert.deepEqual(ctx.fixtures.current,[]);
    assert.equal(ctx.events.at(-1)[0],'status');
  }
});

test('Livre I: fenêtre bloquée => lien signé navigue dans le même onglet',async()=>{
  const ctx=securedLibraryFlow('novel',true);
  const task=ctx.call({disabled:false});
  ctx.pending.resolve({data:{ok:true,url:'https://private.example/novel.pdf'},error:null});
  await task;
  assert.deepEqual(ctx.fixtures.current,['https://private.example/novel.pdf']);
});

test('Document de projet: clic ouvre onglet avant réponse puis refuse ou navigue',async()=>{
  const denied=securedLibraryFlow('document');
  const button={disabled:false};
  const task=denied.call('00000000-0000-4000-8000-000000000001',button);
  assert.equal(denied.fixtures.calls.length,1);
  assert.equal(button.disabled,true);
  assert.equal(denied.events[0][0],'prepare');
  denied.pending.resolve({data:{ok:false,error:'Accès refusé'},error:null});
  await task;
  assert.equal(denied.fixtures.tabs[0].closed,true);
  assert.equal(button.disabled,false);
  assert.deepEqual(denied.fixtures.visited,[]);

  const allowed=securedLibraryFlow('document');
  const next=allowed.call('00000000-0000-4000-8000-000000000002',{disabled:false});
  allowed.pending.resolve({data:{ok:true,url:'https://private.example/document.pdf',protected:true},error:null});
  await next;
  assert.deepEqual(allowed.fixtures.visited,['https://private.example/document.pdf']);
});

test('Échec réseau: ne laisse aucune fenêtre blanche et réactive le bouton',async()=>{
  for(const which of ['novel','document']){
    const ctx=securedLibraryFlow(which);
    const button={disabled:false};
    const promise=which==='novel'?ctx.call(button):ctx.call('valid-id',button);
    ctx.pending.reject(new Error('Connection lost'));
    await promise;
    assert.equal(button.disabled,false);
    assert.equal(ctx.fixtures.tabs[0].closed,true);
    assert.deepEqual(ctx.fixtures.visited,[]);
  }
});
