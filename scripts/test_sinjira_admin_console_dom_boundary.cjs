#!/usr/bin/env node
'use strict';
// Tests des fonctions réellement exécutées dans la console propriétaire
// SINJIRA : les réponses Edge sont synthétiques, sans réseau, clé ni compte.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const read=path=>fs.readFileSync(require('node:path').join(ROOT,path),'utf8');
const raw=read('assets/js/sinjira-admin-console-core.js');
const marker='(async()=>{try{await requireSinjiraAdmin();';
const end=raw.lastIndexOf(marker);
assert.ok(end>0,'Initialisation de la console non reconnue');
const script=raw.slice(0,end).replace(/^import[^\n]*\n/gm,'')+
  '\nglobalThis.__admin={safeAdminId,loadProjects,loadDocs,loadRequests,loadUsers,loadPlaytests,analytics};';
const uuid='123e4567-e89b-42d3-a456-426614174000';
const other='223e4567-e89b-42d3-a456-426614174000';
const evil='"><img src=x onerror=alert(1)>';
let checks=0,requests=[];
function eq(got,want,label){assert.equal(got,want,label);checks++;}
function yes(value,label){assert.ok(value,label);checks++;}
function absent(html,needle,label){yes(!html.includes(needle),label);}
const escapeHtml=v=>String(v??'').replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
})[c]);

function fakeButton(data,card){
  return {dataset:{...data},listener:null,
    addEventListener(name,fn){if(name==='click')this.listener=fn},
    closest(selector){eq(selector,'.admin-user-card','Conteneur de l’utilisateur courant');return card}
  };
}
function box(){
  return {innerHTML:'',buttons:{},
    querySelectorAll(sel){return this.buttons[sel]||[]},
    querySelector(){throw Error('Ne jamais interroger la liste entière avec un sélecteur interpolé')}
  };
}
const targets={
  '[data-admin-status]':{textContent:'',dataset:{},hidden:false},
  '[data-admin-project-list]':box(),
  '[data-admin-document-list]':box(),
  '[data-admin-request-list]':box(),
  '[data-admin-user-list]':box(),
  '[data-admin-playtest-list]':box(),
  '[data-admin-analytics]':box()
};
const response={
  list_projects:{projects:[{id:evil,name:'Projet forgé',slug:'fake'},{
    id:uuid,name:'Projet légitime',slug:'roman',status:'active',visibility:'account'}]},
  list_documents:{documents:[{id:evil,title:'Faux document',status:'review'},{
    id:uuid,title:'Document légitime',status:'review',version:1}]},
  list_access_requests:{requests:[{id:evil,message:'Fausse demande',status:'pending'},{
    id:uuid,user_id:other,message:'Demande légitime',status:'pending',requested_level:'tester'}],users:[{id:other,email:'lecteur@example.invalid'}]},
  list_users:{users:[{id:evil,pseudo:'Compte forgé',access:[]},{
    id:other,pseudo:'<svg/onload=alert(1)>',email:'compte@example.invalid',access:[]}]},
  list_playtests:{playtests:[{id:evil,title:'Faux playtest',status:'open',playtest_participants:[]},{
    id:uuid,title:'Playtest légitime',status:'open',playtest_participants:[
      {user_id:evil,status:'applied'},{user_id:other,status:'applied'}]}]},
  analytics:{analytics:{'Fracture':{
    count:'<svg/onload=alert(1)>',
    average_players:'<img src=x onerror=alert(1)>',
    average_duration:'</dd><script>alert(1)</script>',
    average_rating:'<iframe srcdoc=evil>'
  }}},
  grant_access:{},
  set_document_status:{},
  review_access_request:{},
  review_playtest_participant:{},
  dashboard:{dashboard:{}},
  reports_dashboard:{dashboard:{}},
};
const sandbox=vm.createContext({
  document:{
    querySelector(sel){return targets[sel]||null},
    querySelectorAll(sel){return sel==='[data-project-select]'?[]:[]}
  },
  getSupabase(){return {
    storage:{from(){return {getPublicUrl(){return {data:{publicUrl:'/assets/media/sinjira-emblem.webp'}}}}}},
    functions:{async invoke(endpoint,{body}){
      const action=body?.action;
      requests.push({endpoint,body});
      const key=endpoint==='admin-reports'?'reports_'+action:action;
      const data=response[key];
      if(!data)throw Error('Action de test absente: '+key);
      return {data:{ok:true,...data},error:null};
    }}
  }},
  escapeHtml,console,Map,Array,Date,Promise,
  setStatus(_node,message,type){targets['[data-admin-status]'].textContent=message;
    targets['[data-admin-status]'].dataset.statusType=type}
});
vm.runInContext(script,sandbox,{filename:'sinjira-admin-console-core.js',timeout:2000});
const api=sandbox.__admin;
for(const value of [uuid,other])eq(api.safeAdminId(value),value,'UUID PostgreSQL valide');
for(const value of [evil,'not-uuid',null,undefined,12,uuid+'" onclick="x','javascript:alert(1)']){
  eq(api.safeAdminId(value),'','Identifiant non typé rejeté: '+String(value));
}
async function check(){
  await api.loadProjects();
  const projects=targets['[data-admin-project-list]'].innerHTML;
  absent(projects,'Projet forgé','Projet avec identifiant forgé masqué');
  absent(projects,'onerror=','Projet forgé ne devient pas HTML');
  yes(projects.includes('data-edit-project="'+uuid+'"'),'UUID projet préservé');

  await api.loadDocs();
  const doc=targets['[data-admin-document-list]'].innerHTML;
  absent(doc,'Faux document','Document avec ID illégal masqué');
  yes(doc.includes('data-doc="'+uuid+'"'),'Action document légitime conservée');

  await api.loadRequests();
  const access=targets['[data-admin-request-list]'].innerHTML;
  absent(access,'Fausse demande','Demande invalide masquée');
  yes(access.includes('data-request="'+uuid+'"'),'Action demande légitime conservée');

  await api.loadUsers();
  const users=targets['[data-admin-user-list]'].innerHTML;
  absent(users,'Compte forgé','Faux utilisateur absent');
  absent(users,'<svg/','Pseudo dangereux non interprété');
  yes(users.includes('&lt;svg/onload=alert(1)&gt;'),'Pseudo échappé');
  yes(users.includes('data-grant="'+other+'"'),'Action compte légitime conservée');

  await api.loadPlaytests();
  const pt=targets['[data-admin-playtest-list]'].innerHTML;
  absent(pt,'Faux playtest','Playtest avec identifiant forgé masqué');
  absent(pt,evil,'Action participant malformée absente');
  yes(pt.includes('data-pt="'+uuid+'" data-user="'+other+'"'),'Action playtest valide');

  await api.analytics();
  const stats=targets['[data-admin-analytics]'].innerHTML;
  for(const item of ['<svg','<img','<script','<iframe'])
    absent(stats,item,'Valeur statistique non échappée : '+item);
  yes(stats.includes('&lt;svg/onload=alert(1)&gt;'),'Statistique hostile échappée');
  yes(stats.includes('&lt;/dd&gt;&lt;script&gt;'),'Durée statistique hostile échappée');

  const userbox=targets['[data-admin-user-list]'];
  const card={
    querySelector(sel){
      if(sel==='[data-user-project]')return {value:uuid};
      if(sel==='[data-user-level]')return {value:'tester'};
      throw Error('Sélecteur non autorisé: '+sel);
    }
  };
  const button=fakeButton({grant:other},card);
  userbox.buttons['[data-grant]']=[button];
  await api.loadUsers();
  yes(typeof button.listener==='function','Événement octroi réel installé');
  const before=requests.length;
  await button.listener();
  eq(requests.length>before,true,'Octroi légitime passe vers Edge');
  const grants=requests.filter(r=>r.body.action==='grant_access');
  eq(grants.length,1,'Un seul octroi sous contrôle UUID');
  eq(grants[0].body.user_id,other,'Compte courant depuis le bouton');
  eq(grants[0].body.project_id,uuid,'Projet depuis la carte locale');
  eq(grants[0].body.access_level,'tester','Rôle issu du sélecteur local');

  const invalidButton=fakeButton({grant:evil},card);
  userbox.buttons['[data-grant]']=[invalidButton];
  await api.loadUsers();
  const previous=requests.filter(r=>r.body.action==='grant_access').length;
  await invalidButton.listener();
  eq(requests.filter(r=>r.body.action==='grant_access').length,previous,
    'Action ajoutée par DOM hostile refusée');

  const invalidRoleCard={querySelector(sel){
    return {value:sel==='[data-user-project]'?uuid:'administrator'};
  }};
  const invalidRoleButton=fakeButton({grant:other},invalidRoleCard);
  userbox.buttons['[data-grant]']=[invalidRoleButton];
  await api.loadUsers();
  await invalidRoleButton.listener();
  eq(requests.filter(r=>r.body.action==='grant_access').length,previous,
    'Élévation de rôle par altération du DOM interdite');

  // Les autres actions ne doivent pas accepter les décisions de statut
  // forgées après leur rendu, même si leur UUID reste correct.
  for(const [selector,render,dataset,action] of [
    ['[data-admin-document-list]',api.loadDocs,{doc:uuid,state:'delete-all'},'set_document_status'],
    ['[data-admin-request-list]',api.loadRequests,{request:uuid,decision:'grant-admin'},'review_access_request'],
    ['[data-admin-playtest-list]',api.loadPlaytests,{pt:uuid,user:other,state:'owner'},'review_playtest_participant']
  ]){
    const fake=fakeButton(dataset,card);
    const list=targets[selector];
    const key=action==='set_document_status'?'[data-doc]':action==='review_access_request'?'[data-request]':'[data-pt]';
    list.buttons[key]=[fake];
    await render();
    yes(typeof fake.listener==='function','Listener de sécurité '+action);
    const initial=requests.filter(r=>r.body.action===action).length;
    await fake.listener();
    eq(requests.filter(r=>r.body.action===action).length,initial,
      'Décision administrative non prévue rejetée : '+action);
    list.buttons[key]=[];
  }
  const wrapper=read('assets/js/sinjira-admin-console.js');
  const html=read('admin/sinjira/index.html');
  yes(wrapper.includes("sinjira-admin-console-core.js?v=26.11.09-security"),
    'Import du module protégé avec cache rafraîchi');
  yes(html.includes('sinjira-admin-console.js?v=4.1-security'),
    'Entrée administration actualisée');
  console.log('PASS: '+checks+' assertions de sécurité pour les identifiants, actions administratives, DOM et statistiques.');
}
check().catch(err=>{console.error(err);process.exitCode=1});
