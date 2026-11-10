#!/usr/bin/env node
'use strict';
// Les véritables fonctions de récupération SINJIRA sont chargées dans une VM
// sans réseau, sans session réelle et sans mot de passe de production.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ROOT=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(ROOT,'assets/js/sinjira-recovery-v24-4-99.js'),'utf8');
const sql=fs.readFileSync(path.join(ROOT,'supabase/migrations/20260822011003_v24_4_99_recovery_and_lost_device_security.sql'),'utf8');
assert.match(source,/^import .* from .*;$/m,'Module de récupération réel introuvable');
assert.match(sql,/security_after_password_recovery\(p_device_key text default null\)/,
  'Le serveur doit accepter une clé d’appareil nulle pour tout révoquer');
assert.ok(sql.includes('(v_current is null or id<>v_current)'),
  'Le serveur doit révoquer tous les appareils si aucun appareil courant n’est reconnu');
const script=source.replace(/^import[^\n]*\n/gm,'')+
  '\nglobalThis.__recoveryTest={deviceKey,validDeviceKey};';
const KEY='sinjira.security.device_key.v1';
const UUID='123e4567-e89b-42d3-a456-426614174000';
const strongLegacy='sinjira-'+'b4'.repeat(24);
const weakLegacy='sinjira-'+'0'.repeat(48)+'-legacy';
let assertions=0;
function eq(a,b,label){assert.equal(a,b,label);assertions++}
function yes(a,label){assert.ok(a,label);assertions++}
function storage(value){return {getItem(key){eq(key,KEY,'Lire uniquement la clé d’appareil');return value},setItem(){throw Error('Ne jamais fabriquer de nouvelle identité')}}}
const denied={getItem(){throw Error('Accès refusé par le navigateur')}};

async function scenario(opts={}){
  const events={},calls=[],messages=[],timerCalls=[],navigation=[];
  const inputs=[{disabled:false},{disabled:false}];
  const form={
    addEventListener(name,callback){events[name]=callback},
    setAttribute(name,value){calls.push(['form',name,value])},
    querySelectorAll(){return inputs},
    checkValidity(){return true},
    reportValidity(){throw Error('Le formulaire simulé est valide')},
  };
  const status={},backend={};
  const client={
    auth:{
      mfa:{async getAuthenticatorAssuranceLevel(){
        return {data:opts.requireMfa?
          {nextLevel:'aal2',currentLevel:'aal1'}:
          {nextLevel:'aal1',currentLevel:'aal1'},error:null};
      }},
      async getUser(){return {data:{user:{id:'synthetic-user'}},error:null}},
      async updateUser({password}){
        eq(password,'only-a-test-password','Mot de passe synthétique');
        calls.push(['update']);
        return {error:opts.updateError?{message:'mock denied'}:null};
      },
      async signOut({scope}){
        calls.push(['signOut',scope]);
        if(scope==='global'&&opts.globalThrows)throw Error('mock signout outage');
        if(scope==='global')return {error:opts.globalError?{code:'MOCK_FAIL'}:null};
        return {error:opts.localError?{code:'MOCK_LOCAL_FAIL'}:null};
      },
    },
    async rpc(name,args){
      eq(name,'security_after_password_recovery','RPC sécurisé attendu');
      calls.push(['rpc',args.p_device_key]);
      if(opts.rpcThrows)throw Error('backend unavailable');
      return {data:{ok:opts.rpcOk!==false},error:opts.rpcError?{code:'MOCK_FAIL'}:null};
    }
  };
  const sandbox={
    console:{warn(){throw Error('La récupération ne doit pas journaliser une exception brute')},error(){throw Error('Journal brut interdit')}},
    getSupabase:()=>client,
    isSinjiraBackendConfigured:()=>true,
    setStatus(_target,message,type){messages.push({message,type})},
    localStorage:opts.localStorage??storage(null),
    sessionStorage:opts.sessionStorage??storage(null),
    crypto:{randomUUID(){throw Error('Le reset ne doit pas créer de device_key')}},
    location:{replace(next){navigation.push(next)}},
    document:{querySelector(selector){
      if(selector==='[data-reset-form]')return form;
      if(selector==='[data-account-status]')return status;
      if(selector==='[data-backend-state]')return backend;
      return null;
    }},
    FormData:class{get(name){
      return name==='password'?'only-a-test-password':
        name==='password_confirm'?'only-a-test-password':null;
    }},
    setTimeout(callback,ms){eq(ms,1200,'Redirection après confirmation');timerCalls.push(callback);callback()},
    Date,Uint8Array,Promise,
  };
  vm.runInNewContext(script,sandbox,{filename:'sinjira-recovery-v24-4-99.js',timeout:2000});
  await new Promise(resolve=>setImmediate(resolve));
  yes(typeof sandbox.__recoveryTest.deviceKey==='function','Clé réelle accessible aux tests');
  if(opts.requireMfa){
    eq(events.submit,undefined,'Aucun update avant second facteur');
    eq(navigation[0],'/compte/mfa.html?recovery=1&next=%2Fcompte%2Freinitialiser-mot-de-passe.html','MFA conservée');
    return {calls,messages,navigation,sandbox};
  }
  yes(typeof events.submit==='function','Soumission du vrai formulaire enregistrée');
  await events.submit({preventDefault(){}});
  return {calls,messages,navigation,sandbox};
}
const count=(calls,name)=>calls.filter(c=>c[0]===name).length;

async function main(){
  const strong=await scenario({localStorage:storage(UUID)});
  eq(strong.calls.find(c=>c[0]==='rpc')[1],UUID,'Conserver une identité déjà sûre');
  eq(count(strong.calls,'update'),1,'Mot de passe actualisé');
  eq(strong.calls.some(c=>c[0]==='signOut'&&c[1]==='global'),true,
    'Déconnexion globale imposée');
  eq(strong.messages.at(-1).type,'success','Succès annoncé après RPC et logout');
  eq(strong.navigation[0],'/compte/connexion.html?reset=1','Retour après révocation confirmée');

  const legacy=await scenario({localStorage:storage(strongLegacy)});
  eq(legacy.calls.find(c=>c[0]==='rpc')[1],strongLegacy,'Identifiant historique de 192 bits maintenu');

  const forged=await scenario({localStorage:storage(weakLegacy)});
  eq(forged.calls.find(c=>c[0]==='rpc')[1],null,'Une clé prévisible doit révoquer tous les appareils');

  const weakUuid=await scenario({localStorage:storage('00000000-0000-0000-0000-000000000000')});
  eq(weakUuid.calls.find(c=>c[0]==='rpc')[1],null,'UUID nul ne doit pas préserver la confiance');

  const missing=await scenario({localStorage:storage(null),sessionStorage:storage(null)});
  eq(missing.calls.find(c=>c[0]==='rpc')[1],null,'Sans identité courante : révoquer tout');
  eq(missing.messages.at(-1).type,'success','Révocation globale sans appareil courant');

  const fallback=await scenario({localStorage:denied,sessionStorage:storage(UUID)});
  eq(fallback.calls.find(c=>c[0]==='rpc')[1],UUID,'SessionStorage sûr utilisé si LocalStorage indisponible');

  const noStorage=await scenario({localStorage:denied,sessionStorage:denied});
  eq(noStorage.calls.find(c=>c[0]==='rpc')[1],null,'Aucun stockage : révocation de tous les appareils');
  eq(noStorage.calls.some(c=>c[0]==='signOut'&&c[1]==='global'),true,'Toujours se déconnecter sans stockage');

  const failedRpc=await scenario({localStorage:storage(UUID),rpcError:true});
  eq(failedRpc.calls.some(c=>c[0]==='signOut'&&c[1]==='global'),true,'RPC en erreur ne bloque pas déconnexion');
  eq(failedRpc.messages.at(-1).type,'info','Pas de faux succès de révocation');
  yes(failedRpc.messages.at(-1).message.includes('n’a pas été confirmée'),
    'Présenter explicitement l’incertitude de la révocation');

  const thrownRpc=await scenario({rpcThrows:true});
  eq(count(thrownRpc.calls,'signOut'),1,'Exception RPC ne bloque pas la déconnexion globale');

  const refusedRpc=await scenario({rpcOk:false});
  eq(refusedRpc.messages.at(-1).type,'info','Réponse ok=false ne doit pas annoncer révocation réussie');

  const logoutFail=await scenario({globalError:true});
  eq(logoutFail.calls.some(c=>c[0]==='signOut'&&c[1]==='local'),true,'Tentative de clôture locale');
  eq(logoutFail.messages.at(-1).type,'error','Échec global ne doit pas être présenté comme succès');
  eq(logoutFail.navigation.length,0,'Pas de redirection automatique sur échec global');
  yes(logoutFail.messages.at(-1).message.includes('déconnexion globale n’a pas été confirmée'),
    'Avertir précisément sur la non-révocation des sessions');

  const logoutThrow=await scenario({globalThrows:true});
  eq(logoutThrow.calls.some(c=>c[0]==='signOut'&&c[1]==='local'),true,
    'Exception globale : déconnexion locale tentée');
  eq(logoutThrow.messages.at(-1).type,'error','Exception globale doit rester visible');

  const updateFail=await scenario({updateError:true});
  eq(count(updateFail.calls,'rpc'),0,'Pas de révocation avant succès de changement');
  eq(count(updateFail.calls,'signOut'),0,'Pas de déconnexion après échec de changement');

  const mfa=await scenario({requireMfa:true});
  eq(count(mfa.calls,'update'),0,'MFA non validée bloque le changement');
  eq(count(mfa.calls,'rpc'),0,'MFA non validée bloque la révocation');

  yes(!source.includes('randomDeviceKey'),'Générateur d’appareil prévisible retiré');
  yes(!source.includes('getRandomValues?.('),'Aucun secours cryptographique facultatif');
  yes(!source.includes("console.warn('[SINJIRA secure recovery]',error)"),
    'Erreur Auth brute non journalisée');
  yes(source.includes('data?.ok===true'),'Résultat RPC confirmé explicitement');
  yes(source.includes("signOut({scope:'global'})"),'Désactivation globale maintenue');
  console.log('PASS: '+assertions+' assertions contre les clés prévisibles, le faux succès de révocation, les exceptions RPC et les erreurs de déconnexion.');
}
main().catch(err=>{console.error(err);process.exitCode=1});
