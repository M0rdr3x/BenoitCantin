#!/usr/bin/env node
'use strict';
// Exécute le vrai module MFA navigateur, sans Supabase externe, compte ou JWT.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ROOT = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(ROOT,'assets/js/sinjira-mfa-v24-4-66.js'),'utf8');
const script = source.replace(/^import[^\r\n]*\r?\n/m,'');
const CHALLENGE='123e4567-e89b-42d3-a456-426614174000';
const DEVICE='123e4567-e89b-42d3-a456-426614174001';
const SECRET='pg_catalog auth.sessions JWT eyJ.invalid.email customer@example.invalid';
let count=0;
function eq(actual,wanted,what){assert.equal(actual,wanted,what);count++}
function yes(actual,what){assert.ok(actual,what);count++}
function redacted(value,label){
  for(const fragment of ['pg_catalog','auth.sessions','eyJ.invalid.email','customer@example.invalid']){
    yes(!String(value).includes(fragment),label+': '+fragment);
  }
}
function element(){
  return {listeners:{},disabled:false,hidden:true,value:'',
    addEventListener(name,cb){this.listeners[name]=cb},
    querySelector(name){return name==='[type="submit"]'?this.submitButton:null},
    replaceChildren(){this.children=[];this.value=''},
    append(option){this.children.push(option);if(this.children.length===1)this.value=option.value}
  };
}
function makeStorage(initial={}){
  const state=new Map(Object.entries(initial));
  return {
    getItem(name){return state.get(name)||null},
    setItem(name,value){state.set(name,value)},
    removeItem(name){state.delete(name)},
    state
  };
}
async function settle(){await new Promise(resolve=>setImmediate(resolve))}
async function start({security=false,mode='success',key=DEVICE,challenge=CHALLENGE,
  aalBefore='aal1',factors=[{id:'factor-a',status:'verified',friendly_name:'Personnel'}],
  signOutResult={error:null},rpcResult={data:{ok:true},error:null},getUserResult,
  verifyGate=null}={}){
  const form=element(),factorSelect=element(),status=element(),signOut=element();
  form.submitButton=element();
  const navigation=[],statuses=[],logs=[],verifications=[],rpcCalls=[],signOutCalls=[];
  const localStorage=makeStorage({'sinjira.security.device_key.v1':key});
  const sessionStorage=makeStorage({
    'sinjira.security.pending_challenge.v1':challenge,
    'sinjira.security.pending_destination.v1':'/compte/securite.html'
  });
  let aal=aalBefore;
  const auth={
    async getUser(){return getUserResult??{data:{user:{id:'test-user'}},error:null}},
    mfa:{
      async getAuthenticatorAssuranceLevel(){
        if(mode==='aal-error' && aal==='aal2')return {error:{message:SECRET},data:null};
        return {data:{currentLevel:aal},error:null}
      },
      async listFactors(){return {data:{totp:factors},error:null}},
      async challengeAndVerify(params){
        verifications.push(params);
        if(verifyGate)await verifyGate;
        if(mode==='verify-throws')throw new Error(SECRET);
        if(mode==='verify-error')return {error:{message:SECRET}};
        if(mode==='empty-success')return {data:{},error:null};
        if(mode!=='aal1-after-verify')aal='aal2';
        return {data:{access_token:'FAKE_NOT_REAL'},error:null};
      }
    },
    async signOut(options){
      signOutCalls.push(options);
      if(signOutResult instanceof Error)throw signOutResult;
      return signOutResult
    }
  };
  const s={
    auth,
    async rpc(name,args){
      rpcCalls.push({name,args});
      if(mode==='rpc-throws')throw new Error(SECRET);
      return rpcResult
    }
  };
  const elements=new Map([
    ['[data-mfa-challenge-form]',form],
    ['[data-mfa-factor]',factorSelect],
    ['[data-mfa-status]',status],
    ['[data-mfa-signout]',signOut]
  ]);
  const context={
    URLSearchParams,
    location:{search:security?'?security=1&next=%2Fcompte%2Fsecurite.html':'?next=%2Fcompte%2Findex.html',
      replace(value){navigation.push(String(value))}},
    document:{
      querySelector(selector){return elements.get(selector)||null},
      createElement(tag){eq(tag,'option','Options MFA DOM uniquement');return {value:'',textContent:''}}
    },
    localStorage,sessionStorage,
    getSupabase(){return s},
    safeInternalDestination(value,fallback){
      return typeof value==='string'&&value.startsWith('/')&&!value.startsWith('//')?value:fallback
    },
    setStatus(node,message,type){eq(node,status,'Statut dans la zone MFA');statuses.push({message,type})},
    FormData:class {
      constructor(node){eq(node,form,'Code vérification issu du formulaire') }
      get(name){eq(name,'code','Champ TOTP uniquement');return '123456'}
    },
    console:{warn(...args){logs.push(args.join(' '))}}
  };
  vm.runInNewContext(script,context,{timeout:3000,filename:'sinjira-mfa-v24-4-66.js'});
  await settle();
  return {form,factorSelect,status,signOut,navigation,statuses,logs,verifications,
    rpcCalls,signOutCalls,localStorage,sessionStorage,
    async submit(){
      yes(typeof form.listeners.submit==='function','Handler submit MFA');
      return form.listeners.submit({preventDefault(){}})
    },
    async logout(){
      yes(typeof signOut.listeners.click==='function','Handler déconnexion');
      return signOut.listeners.click()
    }
  };
}
async function main(){
  yes(source.includes('if(verifying||navigationBlocked||submit?.disabled)return'),
    'Protection contre double challenge obligatoire');
  yes(source.includes('verifiedSession?.access_token'),
    'Le token de session renouvelé est exigé');
  yes(source.includes("aal?.currentLevel!=='aal2'"),
    'AAL2 explicitement confirmé');
  yes(!/console\.(?:warn|error)\([^)]*,\s*error\)/.test(source),
    'Ne jamais journaliser un objet Auth/Postgres brut');

  const standard=await start();
  const form=standard.form;
  eq(form.hidden,false,'Formulaire présent pour session AAL1');
  eq(standard.factorSelect.children.length,1,'Un facteur TOTP sûr construit');
  await standard.submit();
  eq(standard.verifications.length,1,'Un seul challenge');
  eq(standard.navigation.length,1,'Navigation après vérification AAL2');
  eq(standard.navigation[0],'/compte/index.html','Navigation locale seulement');

  for(const [mode,reason] of [
    ['verify-error','Code refusé'],['verify-throws','Rejet de promesse'],
    ['empty-success','Réponse sans jeton'],['aal1-after-verify','Niveau MFA non élevé'],
    ['aal-error','Niveau MFA indisponible']
  ]){
    const h=await start({mode});
    await h.submit();
    eq(h.navigation.length,0,reason+': aucune navigation');
    eq(h.verifications.length,1,reason+': une vérification maximum');
    eq(h.form.submitButton.disabled,false,reason+': retry possible');
    eq(h.statuses.at(-1).type,'error',reason+': erreur explicite');
    redacted(h.statuses.at(-1).message,reason+' statut');
    h.logs.forEach(x=>redacted(x,reason+' journal'));
  }

  let releaseVerify;
  const gate=new Promise(resolve=>{releaseVerify=resolve});
  const race=await start({verifyGate:gate});
  const first=race.submit();
  eq(race.form.submitButton.disabled,true,'Bouton désactivé avant réponse asynchrone');
  await race.submit();
  eq(race.verifications.length,1,'Double soumission évitée sur requête en vol');
  releaseVerify();
  await first;
  eq(race.navigation.length,1,'Un seul retour après réussite');

  const secured=await start({security:true});
  await secured.submit();
  eq(secured.rpcCalls.length,1,'Résolution de la connexion inhabituelle');
  eq(secured.rpcCalls[0].name,'security_resolve_connection_challenge_mfa','RPC existante');
  eq(secured.rpcCalls[0].args.p_challenge_id,CHALLENGE,'Challenge canonique');
  eq(secured.rpcCalls[0].args.p_device_key,DEVICE,'Clé cryptographique validée');
  eq(secured.navigation[0],'/compte/securite.html','Retour local après RPC et MFA');
  eq(secured.sessionStorage.getItem('sinjira.security.pending_challenge.v1'),null,
    'Défi en attente effacé après résolution');

  for(const badKey of ['', '1'.repeat(20), 'sinjira-'+'0'.repeat(48), 'fake-'+SECRET]){
    const h=await start({security:true,key:badKey});
    await h.submit();
    eq(h.navigation.length,0,'Clé faible: pas de navigation');
    eq(h.rpcCalls.length,0,'Clé faible: aucune RPC sensible');
    eq(h.signOutCalls.length,1,'Clé faible: déconnexion locale demandée');
    eq(h.signOutCalls[0].scope,'local','Déconnexion ciblée');
    eq(h.statuses.at(-1).type,'error','Session suspecte non autorisée');
    h.logs.forEach(x=>redacted(x,'Journal clé faible'));
  }

  const badChallenge=await start({security:true,challenge:'not-uuid'});
  await badChallenge.submit();
  eq(badChallenge.rpcCalls.length,0,'Challenge malformé refusé');
  eq(badChallenge.navigation.length,0,'Challenge malformé non autorisé');

  for(const mode of ['rpc-throws','success']){
    const h=await start({security:true,mode,
      rpcResult:mode==='success'?{error:{message:SECRET}}:{data:null,error:null}});
    await h.submit();
    eq(h.navigation.length,0,'Échec RPC: aucune redirection');
    eq(h.signOutCalls.length,1,'Échec RPC: demande déconnexion locale');
    eq(h.statuses.at(-1).type,'error','Connexion inhabituelle refusée');
    h.logs.forEach(x=>redacted(x,'Journal erreur RPC'));
  }

  const cannotLogout=await start({security:true,key:'0'.repeat(30),
    signOutResult:{error:{message:SECRET}}});
  await cannotLogout.submit();
  eq(cannotLogout.navigation.length,0,'Échec logout n’autorise pas le compte');
  yes(cannotLogout.statuses.at(-1).message.includes('n’a pas pu être confirmée'),
    'Échec logout ne déclare pas la session fermée');
  redacted(cannotLogout.statuses.at(-1).message,'Échec logout');
  const signedOut=await start();
  await signedOut.logout();
  eq(signedOut.signOutCalls.length,1,'Déconnexion volontaire effectuée');
  eq(signedOut.signOutCalls[0].scope,'local','Déconnexion volontaire locale');
  eq(signedOut.navigation[0],'/compte/connexion.html','Redirection seulement après réponse Auth');

  const logoutError=await start({signOutResult:{error:{message:SECRET}}});
  await logoutError.logout();
  eq(logoutError.navigation.length,0,'Échec de déconnexion bloquant');
  eq(logoutError.signOut.disabled,false,'Réessai logout possible');
  yes(logoutError.statuses.at(-1).message.includes('n’a pas pu être confirmée'),
    'Interface honnête si logout refusé');
  logoutError.logs.forEach(x=>redacted(x,'Erreur logout'));

  const noFactors=await start({security:true,factors:[]});
  eq(noFactors.form.hidden,true,'Absence de facteur : défi masqué');
  eq(noFactors.signOutCalls.length,1,'Absence de facteur : tentative déconnexion');
  eq(noFactors.navigation.length,0,'Absence de facteur : pas de redirection');

  const unauthorized=await start({getUserResult:{data:{user:null},error:{message:SECRET}}});
  eq(unauthorized.navigation.length,1,'Utilisateur non connecté renvoyé au login');
  yes(unauthorized.navigation[0].startsWith('/compte/connexion.html?next='),
    'Redirection locale connexion');

  let releaseRace;
  const pending=new Promise(resolve=>{releaseRace=resolve});
  const during=await start({verifyGate:pending});
  const verify=during.submit();
  await during.logout();
  eq(during.navigation.length,1,'Un logout concurrent ne laisse qu’une destination');
  eq(during.navigation[0],'/compte/connexion.html','Le logout prime sur le challenge');
  releaseRace();
  await verify;
  eq(during.navigation.length,1,'Réponse MFA tardive ne réautorise pas la session');

  const page=fs.readFileSync(path.join(ROOT,'compte/mfa.html'),'utf8');
  yes(page.includes('sinjira-mfa-v24-4-66.js?v=24.4.100'),
    'Version de module MFA rechargée');
  console.log('PASS: '+count+' assertions MFA sur login, AAL2, session Auth, anti-race et confidentialité.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
