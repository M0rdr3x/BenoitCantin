#!/usr/bin/env node
'use strict';
// Exercices en VM du vrai parcours "Compte compromis" (sans authentification,
// secrets, API SQL ni comptes réels).
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-security-center-v24-4-98.js'),'utf8');
const start=source.indexOf('function friendlySecurityError(');
const end=source.lastIndexOf('\nboot();');
assert.ok(start>0&&end>start,'La fonction de sécurité et son boot réel doivent exister');
const actual=source.slice(start,end)+'\nglobalThis.__security={boot,friendlySecurityError};\n';
const SECRET='SQL auth.sessions contact@example.invalid JWT eyJ.not-real.private';
let assertions=0;
function equal(a,b,label){assert.equal(a,b,label);assertions++}
function check(value,label){assert.ok(value,label);assertions++}
function privateFree(text,label){for(const fragment of ['auth.sessions','contact@example.invalid','eyJ.not-real.private']){
  check(!String(text).includes(fragment),label+' sans '+fragment);
}}
const DEVICE='12345678-1234-4234-8234-123456789abc';
async function harness({rpcResult={ok:true,revoked_devices:2},rpcError=null,
 signOut={error:null},signOutError=null,reloadError=null,cryptoError=null,confirmation=true,delayRpc=null}={}){
  const btn={disabled:false,handlers:{},addEventListener(event,callback){this.handlers[event]=callback}};
  const statuses=[],logs=[],rpcCalls=[],signOutCalls=[],stateCalls=[];
  let documentClick=null,authCtx=0;
  const context=vm.createContext({
    deviceMetadata(){if(cryptoError)throw cryptoError;return {device_key:DEVICE}},
    async requireUser(){return {id:'fake-user'}},
    status(message,type='info'){statuses.push({message,type})},
    async registerContext(){return {registered:{},context:null}},
    async loadState(){
      stateCalls.push(true);
      if(reloadError && stateCalls.length>1)throw reloadError;
      return {devices:[]};
    },
    qs(selector){return selector==='[data-security-compromised]'?btn:null},
    confirmAction(){return confirmation},
    document:{addEventListener(event,callback){if(event==='click')documentClick=callback}},
    getSupabase(){return {auth:{async signOut(options){
      signOutCalls.push(options);
      if(signOutError)throw signOutError;
      return signOut;
    }}}},
    async rpc(name,args){
      rpcCalls.push({name,args});
      if(delayRpc)await delayRpc;
      if(rpcError)throw rpcError;
      return rpcResult;
    },
    requiredSecurityRecordId(value){return value},
    console:{warn(...args){logs.push(args.join(' '))}},
  });
  vm.runInContext(actual,context,{timeout:2500,filename:'sinjira-security-center-v24-4-98.js'});
  await context.__security.boot();
  check(typeof btn.handlers.click==='function','Gestionnaire réel Compte compromis enregistré');
  return {btn,statuses,logs,rpcCalls,signOutCalls,stateCalls,
    handlers:{get documentClick(){return documentClick}},
    friendlySecurityError:context.__security.friendlySecurityError,
    click(){return btn.handlers.click()},
  };
}
async function main(){
  check(!source.includes("console.warn('[SINJIRA security-context]',error?.message||error)"),
      'Aucun log brut de service security-context');
  check(!source.includes("console.error('[SINJIRA security center]',error)"),
      'Aucune erreur brute d’initialisation en console');
  check(!source.includes('return message;'),'Aucun diagnostic SQL arbitraire reflété dans le DOM');
  const h=await harness();
  await h.click();
  equal(h.rpcCalls.length,1,'Une seule RPC urgence');
  equal(h.rpcCalls[0].name,'security_compromise_account','La RPC du compte compromis est conservée');
  equal(h.rpcCalls[0].args.p_current_device_key,DEVICE,'Clé courante conservée');
  equal(h.signOutCalls.length,1,'Fermeture autres sessions invoquée');
  equal(h.signOutCalls[0].scope,'others','Déconnexion des autres appareils ciblée');
  equal(h.statuses.at(-1).type,'success','Succès après deux confirmations');
  check(h.statuses.at(-1).message.includes('confirmées'),'Message de succès précis');
  equal(h.btn.disabled,false,'Action réactivée');
  equal(h.stateCalls.length,2,'Vue actualisée après application');

  for(const result of [null,{}, {ok:false}, {revoked_devices:0}]){
    const blocked=await harness({rpcResult:result});
    await blocked.click();
    equal(blocked.signOutCalls.length,0,'Jamais signOut si RPC non confirmée');
    equal(blocked.statuses.at(-1).type,'error','Échec RPC déclaré');
    equal(blocked.stateCalls.length,1,'Pas de relecture comme si RPC réussie');
    equal(blocked.btn.disabled,false,'Réessai possible');
    privateFree(blocked.statuses.at(-1).message,'Échec RPC');
  }

  for(const signed of [null,{}, {error:undefined},{error:{message:SECRET}}]){
    const partial=await harness({signOut:signed});
    await partial.click();
    equal(partial.signOutCalls.length,1,'La fermeture des sessions tentée');
    equal(partial.statuses.at(-1).type,'error','Aucun succès si fermeture non prouvée');
    check(partial.statuses.at(-1).message.includes('pas été confirmée'),'État partiel explicite');
    check(partial.statuses.at(-1).message.includes('Déconnecter tous les appareils'),'Action corrective indiquée');
    equal(partial.stateCalls.length,2,'Vue relue après RPC réussie malgré échec Auth');
    privateFree(partial.statuses.at(-1).message,'Statut de fermeture partielle');
    partial.logs.forEach(log=>privateFree(log,'Console fermeture partielle'));
  }

  const authThrown=await harness({signOutError:new Error(SECRET)});
  await authThrown.click();
  equal(authThrown.statuses.at(-1).type,'error','Exception Auth -> échec');
  check(authThrown.statuses.at(-1).message.includes('pas été confirmée'),'Exception Auth -> statut prudent');
  privateFree(authThrown.statuses.at(-1).message,'Statut Auth rejeté');

  const rpcThrown=await harness({rpcError:new Error(SECRET)});
  await rpcThrown.click();
  equal(rpcThrown.signOutCalls.length,0,'Exception RPC -> aucune fermeture supposée');
  equal(rpcThrown.statuses.at(-1).type,'error','Exception RPC -> état non confirmé');
  privateFree(rpcThrown.statuses.at(-1).message,'Statut SQL rejeté');
  rpcThrown.logs.forEach(log=>privateFree(log,'Journal SQL'));

  const refreshed=await harness({reloadError:new Error(SECRET)});
  await refreshed.click();
  equal(refreshed.signOutCalls.length,1,'La fermeture Auth reste confirmée avant refresh');
  equal(refreshed.statuses.at(-1).type,'error','Échec de rafraîchissement visible');
  check(refreshed.statuses.at(-1).message.includes('Protection d’urgence confirmée'),
    'Refresh échoué distinct de la révocation');
  privateFree(refreshed.statuses.at(-1).message,'Statut refresh');

  const partialRefresh=await harness({signOut:{error:{message:SECRET}},reloadError:new Error(SECRET)});
  await partialRefresh.click();
  equal(partialRefresh.statuses.at(-1).type,'error','Refresh et Auth non confirmés -> échec');
  check(partialRefresh.statuses.at(-1).message.includes('fermeture des sessions non confirmée'),
    'État partiel préservé malgré erreur de rafraîchissement');
  privateFree(partialRefresh.statuses.at(-1).message,'Statut partial refresh');

  const cancelled=await harness({confirmation:false});
  await cancelled.click();
  equal(cancelled.rpcCalls.length,0,'Annulation ne révoque rien');
  equal(cancelled.signOutCalls.length,0,'Annulation ne touche pas aux sessions');

  const compromised=await harness({cryptoError:new Error(SECRET)});
  equal(compromised.rpcCalls.length,0,'WebCrypto absent -> aucune opération privée');
  equal(compromised.statuses.at(-1).type,'error','Crypto inaccessible -> message neutre');
  privateFree(compromised.statuses.at(-1).message,'Crypto erreur');
  compromised.logs.forEach(log=>privateFree(log,'Journal Crypto'));

  const err=h.friendlySecurityError({message:SECRET});
  privateFree(err,'Diagnostic inconnu masqué');
  check(err.includes('Centre de sécurité'),'Erreur sans diagnostic reconnu');

  let release;
  const pending=new Promise(resolve=>{release=resolve});
  const racing=await harness({delayRpc:pending});
  const first=racing.click();
  equal(racing.btn.disabled,true,'Action verrouillée avant fin RPC');
  await racing.click();
  equal(racing.rpcCalls.length,1,'Double clic ne produit pas de RPC concurrente');
  release();
  await first;
  equal(racing.signOutCalls.length,1,'Une seule fermeture des sessions');

  const html=fs.readFileSync(path.join(__dirname,'../compte/securite.html'),'utf8');
  check(html.includes('sinjira-security-center-v24-4-98.js?v=24.5.2'),
    'Cache bust du Centre de sécurité appliqué');
  console.log('PASS: '+assertions+' assertions Compte compromis : RPC, Auth, erreurs privées, consentement et concurrence');
}
main().catch(error=>{console.error(error);process.exitCode=1});
