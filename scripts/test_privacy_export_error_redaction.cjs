#!/usr/bin/env node
'use strict';
// Teste les vraies fonctions client dans un contexte Node isolé.
// Aucun compte, réseau, base Supabase ni secret de production.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(root,'assets/js/v24-data-control.js'),'utf8');
const secret='SQL auth.users; email=test-person@example.invalid; Bearer eyJ.mock-PRIVATE-SECRET';
let checks=0;
function equal(a,b,label){assert.equal(a,b,label);checks++}
function yes(condition,label){assert.ok(condition,label);checks++}
function noSecret(value,label){
  const text=String(value);
  for(const marker of ['auth.users','test-person@example.invalid','eyJ.mock-PRIVATE-SECRET']){
    yes(!text.includes(marker),label+' sans '+marker);
  }
}

async function main(){
  const eventHandlers=new Map();
  const exportButton={disabled:false,textContent:'Télécharger mes données',
    addEventListener(name,fn){eventHandlers.set('export:'+name,fn)}};
  const deleteButton={disabled:false,textContent:'Supprimer mon compte',
    addEventListener(name,fn){eventHandlers.set('delete:'+name,fn)}};
  const status={textContent:'',dataset:{},hidden:true};
  const recorded={blobs:[],links:[],messages:[],warnings:[],signOut:0,requests:[]};
  let backendMode='unrecognized';
  const fakeQuery=table=>({
    select(){return this},eq(){return this},or(){return this},
    async range(){
      if(table==='privacy_settings'){
        if(backendMode==='permission')return {data:[],error:{code:'42501',message:secret}};
        return {data:[],error:{code:'CUSTOM_SQL_FAILURE',message:secret}};
      }
      if(table==='profiles')return {data:[{user_id:'fake-user-id',pseudo:'Test'}],error:null};
      return {data:[],error:null};
    }
  });
  const s={
    from:fakeQuery,
    async rpc(name){
      equal(name,'privacy_export_my_extended_data','RPC complémentaire correct');
      return {data:null,error:{code:'CUSTOM_SQL_FAILURE',message:secret}};
    },
    functions:{async invoke(name,args){
      equal(name,'delete-player-account','Fonction suppression attendue');
      yes(args?.body?.confirm==='SUPPRIMER MON COMPTE','Confirmation serveur préservée');
      if(backendMode==='rejected')return {data:{ok:false,error:secret,code:'NOT_RECOGNIZED'},error:null};
      if(backendMode==='throw')throw new Error(secret);
      return {data:null,error:{message:secret,code:'DB_DIAGNOSTIC'}};
    }},
    auth:{async signOut(){recorded.signOut++}}
  };
  const fakeURL={
    createObjectURL(blob){recorded.blobs.push(blob);return 'blob:synthetic'},
    revokeObjectURL(value){equal(value,'blob:synthetic','URL temporaire révoquée')}
  };
  const document={
    querySelector(sel){
      if(sel==='[data-account-status]')return status;
      if(sel==='[data-export-data]')return exportButton;
      if(sel==='[data-delete-account]')return deleteButton;
      return null;
    },
    createElement(name){
      equal(name,'a','Lien de téléchargement fabriqué');
      const link={href:'',download:'',click(){recorded.links.push({href:this.href,download:this.download})}};
      return link;
    }
  };
  const sandbox=vm.createContext({
    document,
    getSupabase:()=>s,
    requireUser:async()=>({id:'fake-user-id',email:'fake-user@example.invalid'}),
    setStatus(node,message,type){recorded.messages.push({message,type});node.textContent=message;node.dataset.type=type;node.hidden=false},
    URL:fakeURL,Blob,Date,Promise,
    setTimeout(fn){fn()},
    prompt:()=> 'SUPPRIMER MON COMPTE',
    confirm:()=>true,
    location:{href:'',replace(){}},
    console:{warn(){throw Error('Fuite console.warn');},error(){throw Error('Fuite console.error');}}
  });
  yes(source.includes("function safeError(error)"),'Contrat de classification des erreurs présent');
  yes(!source.includes("console.warn('[SINJIRA delete account]',error)"),'Aucun diagnostic privé en console');
  yes(!source.includes("setStatus(status,data?.error"),'Aucune erreur brute lors de suppression');

  const body=source.replace(/^import[^\n]*\n/gm,'');
  const wrapper='(async()=>{\n'+body+'\n' +
    'globalThis.__privacy={safeError,fetchAll,exportData,deleteAccount};})()';
  await vm.runInContext(wrapper,sandbox,{filename:'v24-data-control.js',timeout:5000});
  const api=sandbox.__privacy;
  yes(typeof api.safeError==='function','Code réel chargé dans la VM');
  const unknown=api.safeError({code:'SENSITIVE_QUERY',message:secret});
  equal(unknown,'Cette section n’a pas pu être récupérée.','Erreur inconnue bloquée');
  noSecret(unknown,'Classification inconnue');
  equal(api.safeError({code:'42501',message:secret}),
    'Accès à cette section refusé.','Refus RLS localisé');
  equal(api.safeError({code:'PGRST301',message:secret}),
    'Session expirée ou non autorisée.','JWT expiré localisé');
  equal(api.safeError({code:'EXPORT_TOO_LARGE',message:secret}),
    'Cette section dépasse la limite de l’export du navigateur.','Limite export localisée');

  yes(typeof eventHandlers.get('export:click')==='function','Vrai handler export connecté');
  await eventHandlers.get('export:click')();
  equal(recorded.blobs.length,1,'Un seul export créé');
  equal(recorded.links.length,1,'Un seul téléchargement simulé');
  const payload=JSON.parse(await recorded.blobs[0].text());
  equal(payload.complete,false,'Export partiel clairement identifié');
  equal(payload.sections.profile[0].pseudo,'Test','Données utilisateur disponibles conservées');
  const errorEntries=payload.errors;
  equal(errorEntries.length,2,'Les deux sections refusées sont signalées');
  yes(errorEntries.some(e=>e.section==='privacy_settings'),'Section privée en erreur identifiée');
  yes(errorEntries.some(e=>e.section==='extended_private'),'Complément privé en erreur identifié');
  for(const entry of errorEntries){
    equal(entry.error,'Cette section n’a pas pu être récupérée.','Message export constant');
    noSecret(JSON.stringify(entry),'Aucun diagnostic serveur enregistré dans export');
  }
  equal(exportButton.disabled,false,'Export réactivé après traitement');
  yes(recorded.messages.at(-1).message.includes('Export partiel'),'Avertissement export partiel conservé');

  for(const mode of ['rejected','throw','error']){
    backendMode=mode;
    recorded.messages.length=0;
    await eventHandlers.get('delete:click')();
    equal(recorded.signOut,0,'Aucune déconnexion annoncée sur refus backend');
    yes(recorded.messages.length>=1,'Refus suppression signalé '+mode);
    const last=recorded.messages.at(-1);
    equal(last.type,'error','Suppression '+mode+' signalée comme erreur');
    noSecret(last.message,'Aucune fuite dans message suppression '+mode);
    yes(last.message.includes('Suppression impossible'),'Erreur sûre suppression '+mode);
    equal(deleteButton.disabled,false,'Bouton réactivé sur refus '+mode);
  }

  // Les données backend ne doivent pas contaminer un fichier via des
  // exceptions transitoires non classées, même après un échec RPC.
  backendMode='permission';
  await eventHandlers.get('export:click')();
  const partial=JSON.parse(await recorded.blobs.at(-1).text());
  const permission=partial.errors.find(e=>e.section==='privacy_settings');
  equal(permission.error,'Accès à cette section refusé.','Erreur SQL 42501 traduite sans détails');
  noSecret(JSON.stringify(partial.errors),'Pas de fuite SQL lors de refus RLS');
  console.log('PASS: '+checks+' assertions de confidentialité réelles : export et suppression de compte.');
}
main().catch(e=>{console.error(e);process.exitCode=1});
