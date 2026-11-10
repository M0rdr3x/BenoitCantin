#!/usr/bin/env node
'use strict';
// Test de régression : charge les vrais modules de l'espace personnel dans
// des VM Node. Aucun réseau, aucune authentification ni donnée réelle.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..');
const read=file=>fs.readFileSync(path.join(root,file),'utf8');
const id='123e4567-e89b-42d3-a456-426614174000';
const version='223e4567-e89b-42d3-a456-426614174000';
const recipient='323e4567-e89b-42d3-a456-426614174000';
const bad='"><img src=x onerror=alert(1)>';
const code='a'.repeat(64);
let checks=0;
function eq(actual,expected,label){assert.equal(actual,expected,label);checks++}
function yes(value,label){assert.ok(value,label);checks++}
function lacks(html,value,label){yes(!html.includes(value),label)}
function domNode(){
  return {innerHTML:'',hidden:false,textContent:'',dataset:{},children:[],value:'',disabled:false,
    options:[],append(...nodes){this.children.push(...nodes)},
    addEventListener(name,fn){this[name]=fn},setAttribute(k,v){this[k]=v},
    reset(){this.wasReset=true},select(){this.selected=true},querySelector(){return domNode()}
  };
}
function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
})[c])}
class FakeFormData {
  constructor(form){this.values=form?.fields||{}}
  get(k){return this.values[k]??null}
}
async function main(){
  const boundary=await import(pathToFileURL(path.join(root,'assets/js/sinjira-life-story-owner-boundaries.mjs')).href);
  for(const good of [id,version,recipient])eq(boundary.isSafeLifeStoryId(good),true,'UUID légitime conservé');
  for(const forged of [bad,null,undefined,1,{},'','a'.repeat(64),id+'" data-entry-delete="'+version]){
    eq(boundary.isSafeLifeStoryId(forged),false,'UUID forgé ou non typé refusé');
  }
  eq(boundary.isSafeDeathReportCode(code),true,'Code de 32 octets hex accepté');
  for(const value of [null,'',bad,code.toUpperCase(),code.slice(0,62),code+'f','f'.repeat(63)+'g','0x'+code,3]){
    eq(boundary.isSafeDeathReportCode(value),false,'Code de signalement invalide refusé');
  }

  const privateNodes=new Map();
  for(const selector of [
    '[data-life-story-status]','[data-life-story-summary]',
    '[data-life-story-directive-state]','[data-life-story-entries]',
    '[data-life-story-versions]','[data-life-story-recipients]',
    '[data-life-story-preview-version]','[data-life-story-preview]'
  ])privateNodes.set(selector,domNode());
  const tableRows={
    life_story_legacy_settings:{delivery_enabled:false},
    life_story_entries:[
      {id,title:'Souvenir légitime',body:'Ce texte est privé',entry_type:'memory',
        approval_status:'approved',posthumous_disclosure:'selected_versions',knowledge_status:'declared_fact'},
      {id:bad,title:'Souvenir XSS',body:'<img src=x onerror=alert(1)>'}
    ],
    life_story_versions:[
      {id:version,name:'Famille',title:'Ma famille',status:'draft',audience:'family'},
      {id:bad,name:'Version XSS',title:'Version forgée',status:'ready',audience:'family'}
    ],
    life_story_version_entries:[
      {entry_id:id,version_id:version,sort_order:1},
      {entry_id:bad,version_id:version,sort_order:2}
    ],
    life_story_recipients:[
      {id:recipient,version_id:version,recipient_label:'Contact légitime',status:'active'},
      {id:bad,version_id:version,recipient_label:'Contact XSS',status:'active'}
    ]
  };
  const mutations=[];
  function clientTable(table){
    const builder={
      select(){return this},eq(){return this},
      order(){return Promise.resolve({data:tableRows[table],error:null})},
      maybeSingle(){return Promise.resolve({data:tableRows[table],error:null})},
      update(data){mutations.push({table,op:'update',data});return this},
      delete(){mutations.push({table,op:'delete'});return this},
      insert(data){mutations.push({table,op:'insert',data});return Promise.resolve({error:null})},
      then(success,failure){return Promise.resolve({error:null}).then(success,failure)}
    };
    return builder;
  }
  const doc={
    querySelector(sel){return privateNodes.get(sel)||null},
    querySelectorAll(){return []}
  };
  const sandbox=vm.createContext({
    document:doc,getSupabase:()=>({from:clientTable}),
    requireUser:async()=>({id}),setStatus(node,message,type){node.textContent=message;node.kind=type},
    formatDate:()=> 'date simulée',escapeHtml,
    isSafeLifeStoryId:boundary.isSafeLifeStoryId,
    FormData:FakeFormData,
    globalThis:{confirm:()=>true},
    console:{warn(){throw Error('Les erreurs privées ne doivent pas être journalisées')}},
    Date,Promise,Set,Map,Array
  });
  const source=read('assets/js/sinjira-life-story-v24-5-0.js');
  const cut=source.lastIndexOf('boot().catch(');
  yes(cut>0,'Point de démarrage identifié');
  vm.runInContext(source.slice(0,cut).replace(/^import[^\n]*\n/gm,'')+
    '\nglobalThis.__owner={loadState,state,authorizeEntry,privatizeEntry,deleteEntry,toggleVersion,saveVersion,addRecipient,deleteRecipient};',
    sandbox,{filename:'sinjira-life-story-v24-5-0.js',timeout:2000});
  const owner=sandbox.globalThis.__owner;
  owner.state.user={id};
  await owner.loadState();
  eq(owner.state.entries.length,1,'Rendu de souvenir avec ID malformé écarté');
  eq(owner.state.versions.length,1,'Rendu de version malformée écarté');
  eq(owner.state.mappings.length,1,'Relation entre éléments malformée écartée');
  eq(owner.state.recipients.length,1,'Rendu de destinataire malformé écarté');
  for(const [selector,maliciousTitle] of [
    ['[data-life-story-entries]','Souvenir XSS'],
    ['[data-life-story-versions]','Version XSS'],
    ['[data-life-story-recipients]','Contact XSS']
  ]){
    const html=privateNodes.get(selector).innerHTML;
    lacks(html,maliciousTitle,'Pas de données sans UUID dans le DOM '+selector);
    lacks(html,'<img src=x','Aucune injection dans le DOM '+selector);
    lacks(html,bad,'Aucune insertion brute des attributs '+selector);
  }
  const entriesHtml=privateNodes.get('[data-life-story-entries]').innerHTML;
  yes(entriesHtml.includes('data-entry-private="'+id+'"'),
    'Souvenir déjà autorisé : l’action de retrait vers le privé reste disponible' );
  const versionHtml=privateNodes.get('[data-life-story-versions]').innerHTML;
  yes(versionHtml.includes('data-version-form="'+version+'"'),'Formulaire d’une version légitime conservé');

  const before=mutations.length;
  for(const fn of [
    ()=>owner.authorizeEntry(bad),()=>owner.privatizeEntry(bad),
    ()=>owner.deleteEntry(bad),()=>owner.toggleVersion(bad,version,true),
    ()=>owner.toggleVersion(id,bad,true),()=>owner.deleteRecipient(bad),
    ()=>owner.saveVersion({dataset:{versionForm:bad}}),
    ()=>owner.addRecipient({fields:{version_id:bad,recipient_label:'X'}}),
  ]){
    await assert.rejects(fn);checks++;
    eq(mutations.length,before,'Action privée falsifiée non envoyée à Supabase');
  }
  await owner.toggleVersion(id,version,true);
  yes(mutations.some(x=>x.table==='life_story_version_entries'&&x.op==='insert'),
    'Ajout d’une version légitime conservé');

  // Une case cochée injectée dans le navigateur ne doit pas autoriser un
  // souvenir privé non approuvé à entrer dans une version posthume.
  owner.state.entries=[{id,approval_status:'draft',posthumous_disclosure:'never'}];
  const prior=mutations.length;
  await assert.rejects(()=>owner.toggleVersion(id,version,true));checks++;
  eq(mutations.length,prior,'Souvenir non autorisé ne peut être associé à une version');

  // Second module : codes privés et contestation d'un décès.
  const status=domNode(),panel=domNode(),contestForm=domNode(),codeList=domNode(),codeOnce=domNode();
  const els=new Map([
    ['[data-life-story-posthumous-status]',status],
    ['[data-life-story-posthumous-case]',panel],
    ['[data-life-story-contest-form]',contestForm],
    ['[data-life-story-report-codes]',domNode()],
    ['[data-report-code-list]',codeList],
    ['[data-report-code-once]',codeOnce]
  ]);
  let rpcCode={code,display_once:true};
  let currentCase={case_id:bad,status:'verified_hold',can_contest:true};
  let reportRows=[{id:bad,label:'Faux code',status:'active'},{id:recipient,label:'Code fiable',status:'active'}];
  const rpc=[];
  const shared={
    async rpc(name,args){
      rpc.push({name,args});
      if(name==='life_story_create_report_code')return {data:rpcCode,error:null};
      if(name==='life_story_my_posthumous_case')return {data:currentCase,error:null};
      if(name==='life_story_list_report_codes')return {data:reportRows,error:null};
      return {data:{},error:null};
    }
  };
  const s2=vm.createContext({
    document:{
      querySelector(sel){return els.get(sel)||null},
      createElement(){return domNode()}
    },
    getSupabase:()=>shared,
    requireUser:async()=>({id}),
    friendlyBackendMessage:(_message,fallback)=>fallback,
    isSafeLifeStoryId:boundary.isSafeLifeStoryId,
    isSafeDeathReportCode:boundary.isSafeDeathReportCode,
    FormData:FakeFormData,
    confirm:()=>true,
    navigator:{clipboard:{writeText:async()=>{}}},
    Promise,Date,Intl
  });
  const second=read('assets/js/sinjira-life-story-v24-5-2.js');
  const init=second.lastIndexOf('Promise.all([loadCase(), loadReportCodes()])');
  yes(init>0,'Initialisation du panneau posthume reconnue');
  vm.runInContext(second.slice(0,init).replace(/^import[^\n]*\n/gm,'')+
    '\nglobalThis.__codes={loadCase,loadReportCodes,createReportCode,revokeReportCode};',
    s2,{filename:'sinjira-life-story-v24-5-2.js',timeout:2000});
  const codes=s2.__codes;
  await codes.loadCase();
  eq(contestForm.hidden,true,'Case contestation avec ID forgé doit rester fermée');
  eq(contestForm.dataset.caseId,'','Case malformée absente du DOM');
  currentCase={case_id:version,status:'verified_hold',can_contest:true};
  await codes.loadCase();
  eq(contestForm.hidden,false,'Contestation légitime conservée');
  eq(contestForm.dataset.caseId,version,'Case UUID légitime conservée');

  await codes.loadReportCodes();
  eq(codeList.children.length,2,'Liste des codes visibles');
  yes(!codeList.children[0].children.some(x=>x.dataset?.revokeReportCode),
    'ID de code malformé sans bouton de révocation');
  yes(codeList.children[1].children.some(x=>x.dataset?.revokeReportCode===recipient),
    'Code légitime révocable');
  const invalidButton=domNode();
  invalidButton.dataset.revokeReportCode=bad;
  const countRevoke=rpc.filter(x=>x.name==='life_story_revoke_report_code').length;
  await codes.revokeReportCode({target:{closest(){return invalidButton}}});
  eq(rpc.filter(x=>x.name==='life_story_revoke_report_code').length,countRevoke,
    'Révocation malformée refusée avant RPC');
  const form=domNode();form.fields={label:'Proche de confiance'};
  const submitButton=domNode();
  form.querySelector=()=>submitButton;
  for(const forgedCode of [
    {code:'javascript:alert(1)',display_once:true},
    {code:'a'.repeat(63),display_once:true},
    {code,display_once:false}
  ]){
    rpcCode=forgedCode;
    const n=codeOnce.children.length;
    await codes.createReportCode({preventDefault(){},currentTarget:form});
    eq(codeOnce.children.length,n,'Code de signalement falsifié ne peut être affiché');
    eq(status.dataset.kind,'error','Erreur de code privé affichée');
  }
  rpcCode={code,display_once:true};
  await codes.createReportCode({preventDefault(){},currentTarget:form});
  eq(codeOnce.children.length,3,'Code valide affiché une seule fois');
  eq(codeOnce.children[1].value,code,'Jeton hexadécimal exact remis au propriétaire');
  const html=read('compte/histoire-de-vie.html');
  yes(html.includes('sinjira-life-story-v24-5-0.js?v=24.5.2-owner-security'),
    'Cache du module principal actualisé');
  yes(html.includes('sinjira-life-story-v24-5-2.js?v=24.5.2-owner-security'),
    'Cache de gestion des codes actualisé');
  yes(!source.includes("console.warn('[SINJIRA life story]',error)"),
    'Aucune exception Supabase privée en clair dans les logs');
  console.log('PASS: '+checks+' assertions couvrant les vrais modules Histoire de vie, les actions, les UUID et les codes privés de 256 bits.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
