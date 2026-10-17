'use strict';
/* Exécute les vraies fonctions de la bibliothèque sans comptes ni réseau. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

const file=path.join(__dirname,'../assets/js/sinjira-library-v24-4-61.js');
const original=fs.readFileSync(file,'utf8');
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
  Date,
  console,
};
vm.runInNewContext(code+'\nglobalThis.testAPI={activeProjectAccess,canOpenProject,safeProjectPlayPath,setCount,renderProjects};',sandbox,{filename:file});
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
    setStatus:()=>{},
    URLSearchParams,Date,console,
    prompt:()=>null,
    window:{open(){}}
  };
  vm.runInNewContext(legacyCode+
    '\nglobalThis.legacyAPI={verifiedProjectAccess,projectIsOpen,internalProjectPath,project};'+
    '\nglobalThis.legacySet=(r)=>{user={id:"mock-user"};owner=!!r.owner;admin=!!r.admin};',
    env,{filename:'sinjira-library.js'});
  env.legacySet(roles);
  return {api:env.legacyAPI,project,counters,node:getNode};
}

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
  for(const bad of ['//evil.test','https://evil.test/','javascript:alert(1)','/\\evil.test']){
    assert.equal(ctx.api.internalProjectPath(bad),'',bad);
  }
});
