#!/usr/bin/env node
'use strict';
// Régression de confidentialité : exécuter les vrais modules web avec des RPC fictives.
// Aucun réseau, utilisateur réel, secret ou dépendance NPM requis.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const read=name=>fs.readFileSync(path.join(ROOT,name),'utf8');
let checks=0;
function check(condition,message){assert.ok(condition,message);checks++}
function equal(a,b,message){assert.equal(a,b,message);checks++}
const secret='private SQL auth.users id 123e4567-e89b-42d3-a456-426614174000 email person@example.invalid jwt eyJ.secret';
function noSecret(message,label){
  check(!String(message).includes('auth.users'),label+' SQL');
  check(!String(message).includes('person@example.invalid'),label+' courriel');
  check(!String(message).includes('eyJ.secret'),label+' jeton');
}
function importedSource(source){
  // Ce sont deux modules simples : imports statiques uniquement, sans dépendances
  // chargées dans le banc d'essai. Les fonctions exécutées restent identiques.
  return source.replace(/^import[^\n]*\n/gm,'')
    .replace(/^export\s*\{[^\n]*\};?\s*$/gm,'')
    .replace(/^export\s+/gm,'');
}
async function reader(){
  const source=read('assets/js/sinjira-reader.js');
  check(!source.includes("setStatus(error.message,'error')"),'Pas de sortie brute sur erreur INSERT');
  check(!source.includes("setStatus(e?.message"),'Pas de sortie brute sur l\x27erreur globale');
  const status={textContent:'',dataset:{},hidden:true};
  const list={innerHTML:'',querySelectorAll(){return []}};
  const account={innerHTML:''};
  const fields={body:'Un commentaire de test',contains_spoilers:'no'};
  const form={hidden:true,handlers:{},resets:0,
    addEventListener(name,handler){this.handlers[name]=handler},
    reset(){this.resets++}};
  const nodes=new Map([
    ['[data-reader-status]',status],['[data-novel-comments]',list],
    ['[data-comment-account]',account],['[data-comment-form]',form]
  ]);
  let mode='error',inserts=0;
  function from(table){
    return {
      select(){return this},eq(){return this},order(){return this},
      limit(){return Promise.resolve({data:[],error:null})},
      maybeSingle(){
        if(table==='novels')return Promise.resolve({data:{id:'novel-test'},error:null});
        if(table==='profiles')return Promise.resolve({data:{pseudo:'Lecteur de test'},error:null});
        return Promise.resolve({data:null,error:null});
      },
      upsert(){return Promise.resolve({error:null})},
      async insert(){
        inserts++;
        if(mode==='throw')throw Error(secret);
        return {error:mode==='error'?{message:secret,code:'UNKNOWN'}:null};
      }
    };
  }
  const sandbox={
    document:{body:{dataset:{readerPage:'novel',novelSlug:'roman-test'}},querySelector(key){return nodes.get(key)||null}},
    getSupabase:()=>({from}),getCurrentUser:async()=>({id:'user-test',email:'test@example.invalid'}),
    escapeHtml:value=>String(value??''),formatDate:()=> 'Date',
    FormData:class {get(name){return fields[name]??null}},
    Date,Set,Map,Number,String,Promise,
    console:{error(){throw Error('Log de données privées interdit')}},
  };
  const context=vm.createContext(sandbox);
  const script=importedSource(source);
  const cut=script.lastIndexOf('\n(async()=>');
  check(cut>0,'Point de lancement lecteur trouvé');
  vm.runInContext(script.slice(0,cut)+'\nglobalThis.__reader={comments,setStatus};',context,
    {filename:'sinjira-reader.js',timeout:2000});
  const api=context.__reader;
  api.setStatus(secret,'error');
  noSecret(status.textContent,'Erreur arbitraire remplacée');
  equal(status.textContent,'Le lecteur est temporairement indisponible. Réessayez plus tard.',
    'Refus par défaut du diagnostic brut');
  api.setStatus('Le commentaire est trop court.','error');
  equal(status.textContent,'Le commentaire est trop court.','Erreur locale connue conservée');
  api.setStatus('Commentaire envoyé. Il apparaîtra après approbation.','success');
  equal(status.textContent,'Commentaire envoyé. Il apparaîtra après approbation.','Confirmation inchangée');

  await api.comments();
  check(typeof form.handlers.submit==='function','Handler du vrai formulaire installé');
  for(const failure of ['error','throw']){
    mode=failure;
    await form.handlers.submit({preventDefault(){}});
    equal(status.textContent,'Impossible de publier le commentaire pour le moment.',
      'Erreur serveur '+failure+' non divulguée');
    noSecret(status.textContent,'Publication refusée '+failure);
  }
  mode='success';
  await form.handlers.submit({preventDefault(){}});
  equal(status.textContent,'Commentaire envoyé. Il apparaîtra après approbation.',
    'Publication réussie toujours affichée');
  equal(form.resets,1,'Formulaire réinitialisé seulement après confirmation');
  equal(inserts,3,'Trois insertions fictives correctement exercées');
}
function social(){
  const source=read('assets/js/sinjira-social-common.js');
  check(!source.includes("console.error('[SINJIRA social]',error)"),
    'Aucun logging brut Supabase social');
  const context=vm.createContext({
    getSupabase:()=>({}),requireUser:async()=>({}),escapeHtml:s=>s,formatDate:s=>s,
    SINJIRA_CONFIG:{},location:{pathname:'/compte/communaute.html',search:''},
    console:{error(){throw Error('Exposition privée console.error')},warn(){throw Error('Exposition privée console.warn')}},
    Set,Map,Array,String,
  });
  vm.runInContext(importedSource(source)+
    '\nglobalThis.__social={socialErrorStatus,socialErrorMessage};',context,
    {filename:'sinjira-social-common.js',timeout:2000});
  const node={textContent:'',dataset:{},hidden:true};
  context.__social.socialErrorStatus(node,{code:'UNKNOWN',message:secret},
    'Action impossible. Réessayez plus tard.');
  equal(node.textContent,'Votre session doit être renouvelée. Reconnectez-vous au Compte SINJIRA™.',
    'Erreur contenant JWT normalisée en message de reconnexion sûr');
  noSecret(node.textContent,'Message social non divulgué');
  equal(node.dataset.statusType,'error','Statut de sécurité conservé');
  context.__social.socialErrorStatus(node,{code:'42501',message:secret},
    'Action impossible. Réessayez plus tard.');
  check(node.textContent.includes('pas autorisée'),
    'Message sûr pour refus de permission conservé');
  noSecret(node.textContent,'Refus RLS non divulgué');
  context.__social.socialErrorStatus(null,{message:secret},
    'Action impossible. Réessayez plus tard.');
}
async function main(){
  await reader();
  social();
  console.log('PASS: '+checks+' assertions de confidentialité sur vrais modules lecteur/social.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
