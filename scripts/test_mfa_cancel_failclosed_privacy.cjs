#!/usr/bin/env node
'use strict';
// Exécuter le vrai module du Centre de sécurité, avec Auth Supabase factice.
// Aucun compte, réseau, secret TOTP ou jeton réel.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(ROOT,'assets/js/v24-security.js'),'utf8');
const script=source.replace(/^import\s+\{[^\n]+\}\s+from\s+'[^']+';\s*$/m,'');
const SECRET='SQL auth.users, email user@example.invalid, jwt eyJ.private.fake';
let checks=0;
function eq(actual,expected,label){assert.equal(actual,expected,label);checks++}
function yes(actual,label){assert.ok(actual,label);checks++}
function noPrivate(text,label) {
  for(const fragment of ['auth.users','user@example.invalid','eyJ.private.fake']){
    yes(!String(text).includes(fragment),label+' : '+fragment);
  }
}
function element(){
  const listeners={};
  return {
    listeners,hidden:true,disabled:false,textContent:'',innerHTML:'',
    src:'',alt:'',resetCalled:false,attributes:{},
    addEventListener(name,handler){listeners[name]=handler;},
    querySelector(name){return name==='[type="submit"]'?this.submitButton||null:null;},
    querySelectorAll(){return []},
    removeAttribute(attr){if(attr==='src')this.src='';},
    reset(){this.resetCalled=true;}
  };
}
async function harness(mode='success'){
  const enroll=element(),cancel=element(),setup=element(),qr=element(),secret=element(),
    form=element(),factorBox=element(),mfaBox=element(),session=element(),status=element();
  form.submitButton=element();
  const nodes=new Map([
    ['[data-mfa-enroll]',enroll],['[data-mfa-cancel]',cancel],
    ['[data-mfa-enroll-form]',form],['[data-mfa-setup]',setup],
    ['[data-mfa-qr]',qr],['[data-mfa-secret]',secret],
    ['[data-mfa-factors]',factorBox],['[data-v24-security-mfa]',mfaBox],
    ['[data-v24-security-session]',session],['[data-v24-security-status]',status]
  ]);
  const warnings=[],statuses=[],lifecycle=new Map();
  let unenrollCalls=0,listCalls=0,removeSucceeded=false;
  let holdResolve=null;
  let allowUnenroll;
  const inFlight=new Promise(resolve=>{allowUnenroll=resolve});
  const mfa={
    async listFactors(){
      listCalls++;
      if(mode==='refresh-error'&&removeSucceeded)throw Error(SECRET);
      return {data:{totp:[]},error:null};
    },
    async getAuthenticatorAssuranceLevel(){return {data:{currentLevel:'aal1'},error:null}},
    async enroll(){return {data:{id:'TEST_FACTOR',totp:{
      qr_code:'data:image/png;base64,TEST_QR_NOT_REAL',secret:'FAKE_TOTP_TEST_SECRET'}},error:null}},
    async unenroll({factorId}){
      unenrollCalls++;
      eq(factorId,'TEST_FACTOR','Unenroll limité au facteur en attente');
      if(mode==='delayed'){holdResolve?.();await inFlight;}
      if(mode==='throw')throw Error(SECRET);
      if(mode==='error')return {error:{message:SECRET,code:'42501'}};
      if(mode==='undefined-error')return {error:undefined};
      if(mode==='empty')return null;
      removeSucceeded=true;
      return {data:{id:factorId},error:null};
    }
  };
  const supabase={auth:{
    mfa,
    async getSession(){return {data:{session:{fake:true}},error:null}},
    async signOut(){return {error:null}}
  }};
  const ctx={
    document:{querySelector(selector){return nodes.get(selector)||null;}},
    addEventListener(name,listener){lifecycle.set(name,listener)},
    console:{warn(...message){warnings.push(message.join(' '))}},
    getSupabase:()=>supabase,
    requireUser:async()=>({email:'user@example.invalid',email_confirmed_at:true}),
    escapeHtml:value=>String(value).replace(/</g,'&lt;'),
    setStatus(node,message,type){statuses.push({message,type});eq(node,status,'Statut MFA ciblé')},
    confirm:()=>false,
    location:{replace(){throw Error('Aucune redirection attendue')}},
  };
  await vm.runInNewContext('(async()=>{\n'+script+'\n})()',ctx,{timeout:3000,filename:'v24-security.js'});
  yes(typeof enroll.listeners.click==='function','Handler enroll existant');
  yes(typeof cancel.listeners.click==='function','Handler d’annulation réel');
  yes(typeof lifecycle.get('pagehide')==='function','Nettoyage TOTP lors de la navigation');
  await enroll.listeners.click();
  eq(setup.hidden,false,'TOTP visible après enroll');
  eq(secret.textContent,'FAKE_TOTP_TEST_SECRET','Secret de test présenté à utilisateur');
  return {
    enroll,cancel,form,setup,qr,secret,warnings,statuses,lifecycle,
    async clickCancel(){return cancel.listeners.click()},
    get unenrollCalls(){return unenrollCalls},
    get listCalls(){return listCalls},
    get removeSucceeded(){return removeSucceeded},
    release(){allowUnenroll()}
  };
}
async function main(){
  yes(!/console\.warn\([^)]*,\s*error\)/.test(source),'Aucun log brut d’exception Supabase');
  yes(source.includes("response.error!==null"),'Unenroll sans confirmation explicite refusé');
  const success=await harness('success');
  await success.clickCancel();
  eq(success.unenrollCalls,1,'Un seul RPC de suppression');
  eq(success.setup.hidden,true,'TOTP masqué après confirmation Auth');
  eq(success.secret.textContent,'—','Secret effacé après annulation');
  eq(success.qr.src,'','QR effacé après annulation');
  eq(success.form.resetCalled,true,'Code d’activation effacé');
  eq(success.cancel.disabled,false,'Bouton réactivé');
  eq(success.statuses.at(-1).message,'Activation TOTP annulée.','Succès confirmé seulement après Auth');
  eq(success.statuses.at(-1).type,'info','Confirmation modérée');
  eq(success.warnings.length,0,'Pas de log en succès');
  const before=success.unenrollCalls;
  await success.clickCancel();
  eq(success.unenrollCalls,before,'Un second clic sans facteur n’appelle pas Auth');

  for(const mode of ['error','throw','undefined-error','empty']){
    const h=await harness(mode);
    await h.clickCancel();
    eq(h.unenrollCalls,1,mode+': une tentative Auth');
    eq(h.removeSucceeded,false,mode+': pas de preuve de retrait');
    eq(h.setup.hidden,false,mode+': formulaire TOTP conservé');
    eq(h.secret.textContent,'FAKE_TOTP_TEST_SECRET',mode+': contenu conservé pour nouvelle tentative');
    eq(h.qr.src,'data:image/png;base64,TEST_QR_NOT_REAL',mode+': QR conservé pour nouvelle tentative');
    eq(h.cancel.disabled,false,mode+': bouton déverrouillé');
    eq(h.statuses.at(-1).type,'error',mode+': niveau erreur');
    yes(h.statuses.at(-1).message.includes('non confirmée'),mode+': statut prudent');
    noPrivate(h.statuses.at(-1).message,mode+' statut');
    eq(h.warnings.length,1,mode+': log générique uniquement');
    noPrivate(h.warnings[0],mode+' journal');
  }

  const refreshed=await harness('refresh-error');
  await refreshed.clickCancel();
  eq(refreshed.removeSucceeded,true,'Facteur supprimé malgré échec de mise à jour des listes');
  eq(refreshed.setup.hidden,true,'Secret effacé après succès Auth');
  eq(refreshed.statuses.at(-1).type,'info','Impossible de charger la liste ne révoque pas le succès');
  yes(refreshed.statuses.at(-1).message.includes('impossible d’actualiser'), 'État de refresh partiel explicite');
  noPrivate(refreshed.statuses.at(-1).message,'Refus de refresh');

  const delayed=await harness('delayed');
  let signalled; const entered=new Promise(resolve=>signalled=resolve);
  // Une tentative d’annulation en vol bloque déjà le second clic synchroniquement.
  const request=delayed.clickCancel();
  eq(delayed.cancel.disabled,true,'Bouton verrouillé avant la requête réseau');
  await delayed.clickCancel();
  eq(delayed.unenrollCalls,1,'Double clic ne lance pas deux désinscriptions');
  delayed.release();
  await request;
  eq(delayed.unenrollCalls,1,'Un seul appel au final');
  eq(delayed.setup.hidden,true,'Annulation confirmée finalement visible');

  const verifying=await harness('success');
  verifying.form.submitButton.disabled=true;
  await verifying.clickCancel();
  eq(verifying.unenrollCalls,0,'Interdit unenroll pendant challengeAndVerify');
  eq(verifying.setup.hidden,false,'Secret conservé pendant la vérification');
  verifying.form.submitButton.disabled=false;
  await verifying.clickCancel();
  eq(verifying.unenrollCalls,1,'Annulation possible une fois vérification terminée');

  const pagehide=await harness('success');
  pagehide.lifecycle.get('pagehide')();
  eq(pagehide.secret.textContent,'—','Secret TOTP effacé dès pagehide');
  eq(pagehide.qr.src,'','Image TOTP nettoyée dès pagehide');
  eq(pagehide.setup.hidden,true,'Panel dissimulé pagehide');
  eq(pagehide.unenrollCalls,0,'Aucun appel réseau non fiable à la fermeture');

  const page=fs.readFileSync(path.join(ROOT,'compte/securite.html'),'utf8');
  yes(page.includes('v24-security.js?v=24.4.100'),'Cache-buster MFA revu');
  yes(!page.includes('v24-security.js?v=24.4.70'),'Ancien JS MFA non servi');
  console.log('PASS: '+checks+' assertions MFA réelles : annulation fail-closed, nettoyage et confidentialité.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
