'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.join(__dirname,'..');
const routeCode=fs.readFileSync(path.join(root,'assets/js/sinjira-auth-route.js'),'utf8');
const shared=fs.readFileSync(path.join(root,'assets/js/sinjira-supabase.js'),'utf8');
const marker='export function safeInternalDestination(';
const start=shared.indexOf(marker);
const stop=shared.indexOf('\nexport async function requireUser(',start);
assert.ok(start>=0&&stop>start,'Contrôle des redirections partagé absent');
const localCode=shared.slice(start,stop).replace('export function ','function ');
function sharedFunction(){
  return vm.runInNewContext(localCode+'\nsafeInternalDestination;',{
    URL,location:{origin:'https://www.benoitcantin.com'}
  });
}
function routeFunction(rawNext=null){
  const origin='https://www.benoitcantin.com';
  const search=rawNext===null?'':('?next='+encodeURIComponent(rawNext));
  const window={};
  const replaced=[];
  const ctx={URL,URLSearchParams,
    location:{origin,href:origin+'/compte/connexion.html'+search,search},
    window,
    history:{state:{},replaceState:(_state,_title,url)=>replaced.push(url)},
    document:{addEventListener:()=>{}}
  };
  vm.runInNewContext(routeCode,ctx);
  return {safe:window.SINJIRA_AUTH_ROUTE.safeLocalDestination,
    next:window.SINJIRA_AUTH_ROUTE.next,replaced};
}
const fallback='/compte/index.html';
test('redirections métier légitimes et paramètres encodés acceptés',()=>{
  for(const dest of [
    '/compte/index.html','/compte/securite.html',
    '/projets/sinjira/romans/lire-demo.html',
    '/compte/bibliotheque.html?livre=1%2F2#mes-livres',
    '/projets/sinjira/jeux/',
  ]){
    assert.equal(sharedFunction()(dest),dest);
    assert.equal(routeFunction().safe(dest),dest);
    assert.equal(routeFunction(dest).next(),dest);
  }
});
const bad=[
  'https://evil.example/after','//evil.example/after','/\\evil.example',
  '/supabase/config.toml','/supabase/functions/personal-ai/index.ts',
  '/.github/workflows/sinjira-secret-guard.yml',
  '/docs/SUPABASE_PRODUCTION_RUNBOOK.md','/mobile-native/App.tsx',
  '/scripts/validate_site.py','/tests/e2e/test_public_site.py',
  '/projets/sinjira/codex/livre-i-delivery-contract.json',
  '/assets/icons/README.md','/projets/projet-nova/netlify.toml',
  '/projets/projet-nova/SECURITY.md','/.well-known/sinjira-pages-release.json',
  '/%73upabase/config.toml','/su%70abase/config.toml','/%2F%2Fevil.example',
  '/projets/sinjira/../supabase/config.toml','/compte/%2e%2e/supabase/config.toml',
  '/compte/../../docs/runbook.html','/compte/./../scripts/internal.html',
  '/admin/config.sql','/compte/suspicious.tsx','/compte/backup.env',
  '/compte/private.lock','/assets/js/site.js','/assets/css/file.css?x=1',
  '/compte/index.html ',' /compte/index.html','/compte/connexion.html\nadmin',
  '/compte/invalid%zz','/%00secret',
];
test('toutes les redirections internes ambiguës et techniques sont refusées',()=>{
  for(const value of bad){
    assert.equal(sharedFunction()(value),fallback,'shared: '+value);
    assert.equal(routeFunction().safe(value),fallback,'auth-route: '+value);
    assert.equal(routeFunction(value).next(),fallback,'auth next: '+value);
  }
});
test('lien next dangereux effacé de l’URL de connexion',()=>{
  const x=routeFunction('/supabase/config.toml');
  assert.ok(x.replaced.some(url=>!url.includes('next=')),'next technique conservé');
});
test('fallback vide préservé pour retirer une destination suspecte',()=>{
  assert.equal(routeFunction().safe('/scripts/private.py',''),'');
  assert.equal(routeFunction().safe('', ''),'');
});
