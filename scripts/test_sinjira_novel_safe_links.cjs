#!/usr/bin/env node
'use strict';
// Teste le module de validation réellement importé et le HTML rendu par les
// deux clients de lecture (actuel + historique), sans accès Supabase réel.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {pathToFileURL}=require('node:url');
const ROOT=path.resolve(__dirname,'..');
const SITE='https://www.benoitcantin.com';
const read=file=>fs.readFileSync(path.join(ROOT,file),'utf8');
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,char=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'
})[char]);
let checks=0;
function equal(actual,expected,label){assert.equal(actual,expected,label);checks++;}
function has(haystack,needle,label){assert.ok(haystack.includes(needle),label);checks++;}
function lacks(haystack,needle,label){assert.ok(!haystack.includes(needle),label);checks++;}

async function main(){
  const {safeNovelHref}=await import(pathToFileURL(path.join(ROOT,'assets/js/sinjira-novel-href.mjs')).href);
  const allowed=[
    '/projets/sinjira/','/projets/sinjira/romans/',
    '/projets/sinjira/romans/lire-demo.html?language=fr#page=4',
    '/compte/liseuse.html?edition=demo','/compte/mes-lectures.html?tab=recent',
    '/compte/mon-personnage.html?part=2&part=3'
  ];
  for(const url of allowed)equal(safeNovelHref(url,SITE),url,'Lien interne légitime refusé: '+url);
  const rejected=[
    '',null,undefined,{},[],42,'https://www.benoitcantin.com/compte/liseuse.html',
    'https://evil.invalid/','http://evil.invalid/','javascript:alert(1)',
    'data:text/html,<svg/onload=alert(1)>','blob:https://evil.invalid/id',
    '//evil.invalid/','///evil.invalid/','/\\evil.invalid/',
    '/compte/../admin/sinjira/','/compte/%2e%2e/admin/sinjira/',
    '/compte/%2E/mes-lectures.html','/compte/./mes-lectures.html',
    '/compte/%2f%2fevil.invalid/','/compte/%5cevil.invalid/',
    '/compte/%252f%252fevil.invalid/','/compte/%0aheader',
    '/compte/%1fheader','/compte/%7fheader',
    '/admin/sinjira/','/projets/projet-nova/',
    '/compte/\nscript','/compte/\tscript','/compte/\rscript',
    ' /compte/mes-lectures.html','/compte/mes-lectures.html ',
    '/compte/a\\b','/'+'x'.repeat(2048)
  ];
  for(const url of rejected)equal(safeNovelHref(url,SITE),'','Chemin dangereux accepté: '+String(url));
  equal(safeNovelHref('/compte/liseuse.html','http://evil.invalid'),'','Origine non HTTPS acceptée');
  equal(safeNovelHref('/compte/liseuse.html','https://user:pass@example.org'),'','Identifiants dans l’origine acceptés');

  function boot(file,{table,novels,book=[]}){
    const box={innerHTML:'',querySelectorAll(){return []}};
    const service={
      from(name){
        return {
          select(){return this},
          in(){return this},
          order(){return Promise.resolve({data:name===table?novels:[]})},
          eq(){return Promise.resolve({data:name==='sinjira_reader_library'||name==='reader_library'?book:[]})},
        };
      }
    };
    const ctx=vm.createContext({
      URL,Map,Date,Promise,
      safeNovelHref,escapeHtml,console,
      location:{origin:SITE,search:''},
      document:{
        body:{dataset:{v18Page:file==='assets/js/sinjira-reads-v24-4-61.js'?'reads-v24-4-61':'none'}},
        querySelector(selector){return selector==='[data-reader-library]'?box:
          selector==='[data-v18-status]'?{hidden:true}:null},
      },
      getSupabase(){return service},
      requireUser:async()=>({id:'synthetic-uuid'}),
      setStatus(){},
      formatDate(){return 'date simulée'},
    });
    const source=read(file).replace(/^import[^\n]*\n/gm,'');
    vm.runInContext(source,ctx,{filename:file,timeout:2000});
    return {box,ctx,source};
  }

  const novel={
    id:'11111111-1111-4111-8111-111111111111',
    slug:'roman-test',
    title:'Roman de test',
    description:'Données de test',
    volume_label:'Tome I',
    status:'published',
    public_path:'//evil.invalid/phishing',
    demo_path:'javascript:alert(1)'
  };
  const current=boot('assets/js/sinjira-reads-v24-4-61.js',{
    table:'sinjira_novels',novels:[novel]
  });
  await vm.runInContext('load()',current.ctx,{timeout:2000});
  lacks(current.box.innerHTML,'javascript:','V24: protocole script présent dans le HTML');
  lacks(current.box.innerHTML,'evil.invalid','V24: hôte externe présent dans le HTML');
  lacks(current.box.innerHTML,'>Lire la démo</a>','V24: bouton de démo dangereux visible');
  has(current.box.innerHTML,'href="/projets/sinjira/romans/"','V24: repli de page roman absent');

  novel.demo_path='/projets/sinjira/romans/lire-demo.html';
  novel.public_path='/projets/sinjira/romans/';
  await vm.runInContext('load()',current.ctx,{timeout:2000});
  has(current.box.innerHTML,'href="/projets/sinjira/romans/lire-demo.html"','V24: démo saine absente');
  has(current.box.innerHTML,'href="/projets/sinjira/romans/"','V24: page publique saine absente');
  novel.slug='la-cendre-du-jugement';
  novel.demo_path='javascript:alert(1)';
  await vm.runInContext('load()',current.ctx,{timeout:2000});
  has(current.box.innerHTML,'href="/compte/liseuse.html?edition=demo"',
    'V24: navigation canonique du Livre I doit rester disponible');
  lacks(current.box.innerHTML,'javascript:','V24: lien du Livre I contient protocole exécutable');

  novel.slug='roman-test';
  novel.id='"><img src=x onerror=alert(1)>';
  novel.demo_path='/compte/liseuse.html?edition=demo';
  await vm.runInContext('load()',current.ctx,{timeout:2000});
  lacks(current.box.innerHTML,'<img src=x','V24: identifiant inattendu non échappé dans les attributs');
  has(current.box.innerHTML,'&quot;&gt;&lt;img','V24: identifiant échappé');
  novel.id='11111111-1111-4111-8111-111111111111';

  const previous=boot('assets/js/sinjira-account-v18.js',{
    table:'novels',novels:[novel]
  });
  novel.demo_path='javascript:alert(1)';
  novel.public_path='//evil.invalid/login';
  await vm.runInContext('reads({id:"synthetic-uuid"})',previous.ctx,{timeout:2000});
  lacks(previous.box.innerHTML,'javascript:','V18: script dans la liste de romans');
  lacks(previous.box.innerHTML,'evil.invalid','V18: URL externe dans la liste de romans');
  has(previous.box.innerHTML,'href="/projets/sinjira/romans/"','V18: destination locale de repli');
  lacks(previous.box.innerHTML,'>Lire la démo</a>','V18: bouton malveillant présent');

  novel.demo_path='/projets/sinjira/romans/lire-demo.html';
  novel.public_path='/projets/sinjira/romans/';
  await vm.runInContext('reads({id:"synthetic-uuid"})',previous.ctx,{timeout:2000});
  has(previous.box.innerHTML,'href="/projets/sinjira/romans/lire-demo.html"',
    'V18: la démo légitime doit être affichée');

  const readsHtml=read('compte/mes-lectures.html'),romansHtml=read('compte/bibliotheque-romans.html');
  has(readsHtml,'sinjira-reads-v24-4-61.js?v=24.4.94','Cache V24 lectures non rafraîchi');
  has(romansHtml,'sinjira-reads-v24-4-61.js?v=26.11.09.1','Cache catalogue romans non rafraîchi');
  has(readsHtml,'sinjira-account-v18.js?v=24.4.94','Cache de l’ancien lecteur non rafraîchi');
  lacks(current.source,'escapeHtml(novel.demo_path)','V24: ancien lien non validé');
  lacks(previous.source,'escapeHtml(n.demo_path)','V18: ancien lien non validé');
  console.log('PASS: '+checks+' vérifications des liens des romans, rendus actifs et historiques, et cache des navigateurs.');
}
main().catch(err=>{console.error(err);process.exitCode=1;});
