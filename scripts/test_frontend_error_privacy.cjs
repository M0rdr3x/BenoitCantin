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
async function legacyComments(){
  // La page « Mes commentaires » utilisait alert(error.message) sur UPDATE
  // et DELETE, et affichait le diagnostic serveur lors du chargement initial.
  const source=read('assets/js/sinjira-account-v18.js');
  check(!source.includes('alert(error.message)'),'Le compte legacy ne montre plus une erreur SQL brute');
  check(!source.includes("st(e?.message||"),'Le chargement legacy ne renvoie pas les diagnostics serveur');
  const status={textContent:'',dataset:{},hidden:true};
  const displayed={innerHTML:'',querySelectorAll(name){
    return name==='[data-edit-comment]'?[editButton]
      :name==='[data-delete-comment]'?[deleteButton]:[];
  }};
  const makeButton=()=>({listeners:{},addEventListener(name,callback){this.listeners[name]=callback},
    closest(){return {dataset:{commentId:'comment-1'}}}});
  const editButton=makeButton(),deleteButton=makeButton();
  const row={id:'comment-1',body:'Texte existant',status:'pending',
    contains_spoilers:false,created_at:'2026-11-14',novels:{title:'Roman test'}};
  const alerts=[];
  let operation='error',mutationCalls=0;
  function mutation(){
    let n=0;
    return {eq(){
      n++;
      if(n<2)return this;
      mutationCalls++;
      if(operation==='throw')return Promise.reject(new Error(secret));
      return Promise.resolve({error:operation==='error'?{message:secret,code:'PGRST500'}:null});
    }};
  }
  const db={from(name){
    equal(name,'novel_comments','Table de commentaires self-only');
    return {
      select(){return this},
      eq(){return this},
      order(){return Promise.resolve({data:[row],error:null})},
      update(){return mutation()},
      delete(){return mutation()}
    };
  }};
  const context=vm.createContext({
    document:{body:{dataset:{v18Page:'comments'}},querySelector(sel){
      if(sel==='[data-v18-status]')return status;
      if(sel==='[data-my-comments]')return displayed;
      return null;
    }},
    getSupabase:()=>db,
    requireUser:async()=>({id:'user-1'}),
    escapeHtml:s=>String(s??''),formatDate:()=> 'Date',
    prompt:()=> 'Texte mis à jour suffisamment long',
    confirm:()=>true,
    alert:message=>alerts.push(message),
    console:{warn(){throw Error('Journal privé refusé')},error(){throw Error('Journal privé refusé')}}
  });
  const script=importedSource(source),cut=script.lastIndexOf('\n(async()=>');
  check(cut>0,'Point de lancement legacy reconnu');
  vm.runInContext(script.slice(0,cut)+'\nglobalThis.__legacy={comments,st};',context,
    {filename:'sinjira-account-v18.js',timeout:2000});
  const api=context.__legacy;
  api.st(secret,'error');
  equal(status.textContent,'Impossible de charger cette rubrique pour le moment.',
    'Échec initial standardisé');
  noSecret(status.textContent,'Échec initial legacy');
  api.st('Opération réussie.','success');
  equal(status.textContent,'Opération réussie.','Statut non-error préservé');
  await api.comments({id:'user-1'});
  check(typeof editButton.listeners.click==='function','Handler édition réel enregistré');
  check(typeof deleteButton.listeners.click==='function','Handler suppression réel enregistré');

  for(const type of ['edit','delete']){
    for(const mode of ['error','throw','success']){
      operation=mode;
      const before=alerts.length;
      const button=type==='edit'?editButton:deleteButton;
      await button.listeners.click();
      if(mode==='success'){
        equal(alerts.length,before,'Opération réussie sans fausse erreur: '+type);
      }else{
        equal(alerts.length,before+1,'Échec signalé: '+type+'/'+mode);
        equal(alerts.at(-1),type==='edit'
          ?'Impossible de modifier ce commentaire pour le moment.'
          :'Impossible de supprimer ce commentaire pour le moment.',
          'Diagnostic sans fuite: '+type+'/'+mode);
        noSecret(alerts.at(-1),'Alerte SQL legacy '+type+'/'+mode);
      }
    }
  }
  equal(mutationCalls,6,'Les six écritures backend sont effectivement simulées');
  const page=read('compte/mes-commentaires.html');
  check(page.includes('sinjira-account-v18.js?v=24.1-error-privacy'),
    'Cache invalidé sur la page Mes commentaires');
}
async function main(){
  await reader();
  social();
  await legacyComments();
  console.log('PASS: '+checks+' assertions de confidentialité sur vrais modules lecteur/social/commentaires legacy.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
