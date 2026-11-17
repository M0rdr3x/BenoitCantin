#!/usr/bin/env node
'use strict';
// Exécute le VRAI module du Centre de sécurité dans une VM sans réseau.
// Les identifiants, messages SQL et erreurs sont exclusivement fictifs.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-security-v24-4-99.js'),'utf8');
const DEVICE_ID='123e4567-e89b-42d3-a456-426614174000';
const SECRET='pg_catalog auth.users email user@example.invalid jwt eyJ.test.secret';
let checks=0;
function eq(a,b,label){assert.equal(a,b,label);checks++;}
function yes(value,label){assert.ok(value,label);checks++;}
function redacted(text,label){
  for(const item of ['pg_catalog','auth.users','user@example.invalid','eyJ.test.secret']) {
    yes(!String(text).includes(item),label+' : pas de '+item);
  }
}
function createHarness({rpcResult={data:{ok:true,session_revocation_required:true},error:null},
                       signOutResult={error:null},id=DEVICE_ID,confirmResult=true,
                       rpcReject=null,signOutReject=null}={}){
  const statuses=[],warnings=[],rpcCalls=[],signOutCalls=[],timers=[];
  let click=null;
  const button={disabled:false,dataset:{deviceLost:id}};
  const status={textContent:''};
  const sandbox={
    getSupabase(){return {
      rpc(name,args) {
        rpcCalls.push({name,args});
        return rpcReject?Promise.reject(rpcReject):Promise.resolve(rpcResult);
      },
      auth:{signOut(options){
        signOutCalls.push(options);
        return signOutReject?Promise.reject(signOutReject):Promise.resolve(signOutResult);
      }}
    }},
    setStatus(element,text,type){eq(element,status,'Statut Ma sécurité');statuses.push({text,type});},
    document:{
      querySelector(query){
        if(query==='[data-security-center-status]')return status;
        return null;
      },
      addEventListener(name,callback) {
        if(name==='click')click=callback;
      }
    },
    MutationObserver:class {observe(){}},
    CSS:{escape:input=>String(input)},
    confirm(){return confirmResult;},
    setTimeout(callback,delay){timers.push({callback,delay});return 1;},
    location:{reload(){throw Error('Un test ne doit pas recharger la page')}},
    console:{warn(...args){warnings.push(args.join(' '));}}
  };
  const ctx=vm.createContext(sandbox);
  vm.runInContext(source.replace(/^import[^\n]*\n/gm,''),ctx,{timeout:2000,filename:'sinjira-security-v24-4-99.js'});
  yes(typeof click==='function','Handler clic réel installé');
  return {
    button,statuses,warnings,rpcCalls,signOutCalls,timers,
    async click(){await click({target:{closest(selector){eq(selector,'[data-device-lost]','Clic appareil perdu');return button;}}});},
    confirmResult
  };
}
async function main(){
  yes(source.includes('data?.session_revocation_required!==true'),'Contrat RPC de révocation Auth requis');
  yes(source.includes("signOutResult.error!==null"),'Erreur retournée par signOut vérifiée');
  yes(!source.includes("console.warn('[SINJIRA lost device]',error)"),'Objet backend non journalisé');
  yes(source.includes('if(button.disabled)return'),'Anti-double clic présent');

  const success=createHarness();
  await success.click();
  eq(success.rpcCalls.length,1,'Une RPC appareil perdu');
  eq(success.rpcCalls[0].name,'security_report_lost_device','RPC propriétaire existante');
  eq(success.rpcCalls[0].args.p_device_id,DEVICE_ID,'UUID inchangé');
  eq(success.signOutCalls.length,1,'Déconnexion Auth réellement demandée');
  eq(success.signOutCalls[0].scope,'others','Préserve session courante');
  eq(success.statuses.at(-1).type,'success','Succès après deux confirmations');
  yes(success.statuses.at(-1).text.includes('confirmée'),'Message exige preuve Auth');
  eq(success.timers.length,1,'Reload uniquement après succès');
  eq(success.button.disabled,true,'Pas de double déclaration en vol');

  for(const invalid of ['','not-a-uuid',DEVICE_ID+'<img>','0000000',SECRET]){
    const blocked=createHarness({id:invalid});
    await blocked.click();
    eq(blocked.rpcCalls.length,0,'ID non UUID rejeté avant RPC');
    eq(blocked.signOutCalls.length,0,'Aucune déconnexion sur ID invalide');
    eq(blocked.timers.length,0,'Pas de reload sur ID invalide');
  }
  const cancelled=createHarness({confirmResult:false});
  await cancelled.click();
  eq(cancelled.rpcCalls.length,0,'Annulation n’appelle aucune RPC');
  eq(cancelled.signOutCalls.length,0,'Annulation ne ferme aucune session');

  const cases=[
    ['RPC error', {data:null,error:{message:SECRET,code:'42501'}}],
    ['RPC false', {data:{ok:false,session_revocation_required:true},error:null}],
    ['RPC missing confirmation', {data:{ok:true},error:null}],
    ['RPC missing response', {data:null,error:null}],
    ['RPC omits session requirement', {data:{ok:true,session_revocation_required:false},error:null}]
  ];
  for(const [label,rpcResult] of cases){
    const h=createHarness({rpcResult});
    await h.click();
    eq(h.signOutCalls.length,0,label+': pas de signOut sans RPC confirmée');
    eq(h.timers.length,0,label+': pas de reload');
    eq(h.statuses.at(-1).type,'error',label+': échec explicite');
    yes(h.statuses.at(-1).text.includes('pas été confirmée'),label+': état non confirmé');
    eq(h.button.disabled,false,label+': réessai possible');
    redacted(h.statuses.at(-1).text,label+' statut');
    h.warnings.forEach(message=>redacted(message,label+' console'));
  }

  for(const badSignout of [{error:{message:SECRET}},{error:{message:'Bad Request',code:'401'}},null,{}, {error:undefined}]){
    const h=createHarness({signOutResult:badSignout});
    await h.click();
    eq(h.rpcCalls.length,1,'Appareil effectivement déclaré perdu');
    eq(h.signOutCalls.length,1,'Tentative de fermeture des sessions effectuée');
    eq(h.statuses.at(-1).type,'error','Jamais succès si signOut incomplet');
    yes(h.statuses.at(-1).text.includes('Cet appareil a été révoqué'),'État partiel explicite');
    yes(h.statuses.at(-1).text.includes('Déconnecter tous les appareils'),'Action corrective indiquée');
    eq(h.timers.length,0,'Aucun rechargement masquant une erreur de session');
    eq(h.button.disabled,false,'Bouton réactivé');
    redacted(h.statuses.at(-1).text,'État partiel');
    h.warnings.forEach(message=>redacted(message,'Journal après signOut'));
  }

  const thrownRpc=createHarness({rpcReject:new Error(SECRET)});
  await thrownRpc.click();
  eq(thrownRpc.signOutCalls.length,0,'RPC jetant une exception bloque Auth');
  eq(thrownRpc.statuses.at(-1).type,'error','Exception RPC pas succès');
  thrownRpc.warnings.forEach(message=>redacted(message,'RPC rejetée'));

  const thrownSignout=createHarness({signOutReject:new Error(SECRET)});
  await thrownSignout.click();
  yes(thrownSignout.statuses.at(-1).text.includes('Cet appareil a été révoqué'),
    'Exception Auth conserve la distinction révocation appareil / sessions');
  eq(thrownSignout.timers.length,0,'Exception Auth ne recharge pas');
  thrownSignout.warnings.forEach(message=>redacted(message,'Auth rejetée'));

  const mfa=createHarness({rpcResult:{error:{message:'AAL2_REQUIRED'}}});
  await mfa.click();
  yes(mfa.statuses.at(-1).text.includes('MFA requise'),'MFA requise conservée');
  eq(mfa.signOutCalls.length,0,'Aucune déconnexion sous MFA non satisfaite');

  // L'état occupé du bouton protège contre une réentrance immédiate.
  const occupied=createHarness();
  occupied.button.disabled=true;
  await occupied.click();
  eq(occupied.rpcCalls.length,0,'Bouton occupé : seconde requête refusée');
  const page=fs.readFileSync(path.join(ROOT,'compte/securite.html'),'utf8');
  yes(page.includes('sinjira-security-v24-4-99.js?v=24.4.100-lost-device'),
    'Ancien module mis hors cache');
  console.log('PASS: '+checks+' assertions réelles sur RPC appareil perdu, sessions Auth, diagnostic et états partiels.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
