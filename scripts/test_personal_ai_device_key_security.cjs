#!/usr/bin/env node
'use strict';
// Exécute le VRAI module Mon IA dans une VM sans réseau, Supabase réel,
// stockage réel, compte, identifiant ou secret de production.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-personal-ai-v25.js'),'utf8');
const VALID_UUID='123e4567-e89b-42d3-a456-426614174000';
const ZERO_UUID='00000000-0000-0000-0000-000000000000';
const BAD_ZERO='sinjira-'+'0'.repeat(48)+'-abc123';
const DEVICE_KEY='sinjira.security.device_key.v1';
const SECRET='private SQL auth.users token eyJ123.jwt contact@example.invalid';
let checks=0;
function eq(actual,expected,why){assert.equal(actual,expected,why);checks++}
function yes(value,why){assert.ok(value,why);checks++}
function noSecret(value,why){
  for(const token of ['auth.users','eyJ123.jwt','contact@example.invalid']){
    yes(!String(value).includes(token),why+' '+token);
  }
}
function store(preloaded='',options={}){
  const map=new Map();
  if(preloaded!==undefined)map.set(DEVICE_KEY,preloaded);
  return {
    map,
    getItem(k){if(options.denyRead)throw Error('Storage unavailable');return map.get(k)??null;},
    setItem(k,v){if(options.denyWrite)throw Error('Storage unavailable');if(!options.ignoreWrite)map.set(k,String(v));}
  };
}
const goodBytes={
  getRandomValues(bytes){
    for(let i=0;i<bytes.length;i++)bytes[i]=(i+1)&255;
    return bytes;
  }
};
function fixture({crypto,local=store(null),session=store(null),backend}={}){
  let calls=0,requestBody=null;
  const context=vm.createContext({
    crypto,
    localStorage:local,
    sessionStorage:session,
    navigator:{userAgent:'Firefox browser',platform:'Unit Test'},
    document:{querySelector(){return null;},querySelectorAll(){return []}},
    window:{confirm(){return true;}},
    getSupabase:()=>({
      functions:{
        async invoke(name,args){
          calls++;
          eq(name,'personal-ai','Fonction Edge reste Mon IA');
          requestBody=args?.body;
          return backend||{data:{ok:true,state:{}},error:null};
        }
      }
    }),
    setStatus(){},
    Date,Promise,Map,Set,Uint8Array
  });
  const original=source.replace(/^import[^\n]*\n/gm,'');
  const entry=original.lastIndexOf('\ninit().catch(');
  yes(entry>0,'Module réel avec point de démarrage reconnu');
  vm.runInContext(original.slice(0,entry)+
    '\nglobalThis.__test={isStrongDeviceKey,randomDeviceKey,deviceKey,deviceMetadata,invokePersonalAi,friendlyError};',
    context,{filename:'sinjira-personal-ai-v25.js',timeout:2000});
  return {api:context.__test,local,session,get calls(){return calls},get requestBody(){return requestBody}};
}
async function rejectsCode(promiseOrFn,code,why){
  try{
    if(typeof promiseOrFn==='function')await promiseOrFn();
    else await promiseOrFn;
  }catch(error){
    eq(error.code,code,why);
    return;
  }
  assert.fail(why+': une identité non fiable a été acceptée');
}
async function main(){
  const good=fixture({crypto:goodBytes});
  yes(good.api.isStrongDeviceKey(VALID_UUID),'UUIDv4 valide reconnu');
  const legacy='sinjira-'+'a'.repeat(48)+'-lmnopq';
  yes(good.api.isStrongDeviceKey(legacy),'Ancienne clé CSPRNG à suffixe conservée');
  for(const v of [
    null,undefined,'',1,'X'.repeat(32),'1234567890123456',
    ZERO_UUID,BAD_ZERO,'sinjira-'+'0'.repeat(48),
    'sinjira-'+'g'.repeat(48),'123e4567-e89b-12d3-a456-426614174000',
    VALID_UUID+'?next=//invalid.example','<img src=x onerror=alert(1)>'
  ])eq(good.api.isStrongDeviceKey(v),false,'Clé falsifiée ou faible refusée: '+String(v).slice(0,25));

  const generated=good.api.randomDeviceKey();
  yes(generated.startsWith('sinjira-'),'Clé de 192 bits générée avec Web Crypto');
  eq(generated.length,56,'24 octets : préfixe de 8 caractères et 48 hex');
  yes(good.api.isStrongDeviceKey(generated),'Clé aléatoire forte conforme');

  const uuid=fixture({crypto:{randomUUID:()=>VALID_UUID}});
  eq(uuid.api.randomDeviceKey(),VALID_UUID,'crypto.randomUUID conforme accepté');

  const weakStore=store(BAD_ZERO);
  const migrated=fixture({crypto:goodBytes,local:weakStore});
  const rotated=migrated.api.deviceKey();
  yes(migrated.api.isStrongDeviceKey(rotated),'Ancienne clé de zéros remplacée');
  eq(weakStore.getItem(DEVICE_KEY),rotated,'Nouvelle clé persistée');
  eq(migrated.api.deviceKey(),rotated,'Clé réutilisée lors des prochaines requêtes');

  const noCrypto=fixture({crypto:undefined,local:store(null),session:store(null)});
  await rejectsCode(()=>noCrypto.api.deviceKey(),'DEVICE_KEY_UNAVAILABLE','Pas de repli sans Web Crypto');
  await rejectsCode(noCrypto.api.invokePersonalAi({action:'get_state'}),'DEVICE_KEY_UNAVAILABLE',
    'Aucun RPC lorsque le navigateur ne peut générer de clé fiable');
  eq(noCrypto.calls,0,'Aucune requête Supabase sans identité fiable');

  const zero=fixture({crypto:{getRandomValues:arr=>arr.fill(0)}});
  await rejectsCode(()=>zero.api.randomDeviceKey(),'DEVICE_KEY_UNAVAILABLE',
    'Octets non initialisés/entièrement nuls refusés');
  eq(zero.calls,0,'Zéro RPC sur clé entièrement nulle');

  const storageFail=fixture({
    crypto:goodBytes,
    local:store(null,{denyWrite:true}),
    session:store(null,{denyWrite:true})
  });
  await rejectsCode(()=>storageFail.api.deviceKey(),'DEVICE_KEY_UNAVAILABLE',
    'Aucune identité éphémère lorsque les deux stockages sont inaccessibles');
  eq(storageFail.calls,0,'Aucun RPC sur stockage impossible');

  const sessionStore=store(null);
  const fallback=fixture({crypto:goodBytes,local:store(null,{denyRead:true}),session:sessionStore});
  const sessionKey=fallback.api.deviceKey();
  yes(fallback.api.isStrongDeviceKey(sessionKey),'Stockage session comme repli stable');
  eq(sessionStore.getItem(DEVICE_KEY),sessionKey,'Clé persistée en session');

  const existing=fixture({crypto:undefined,local:store(VALID_UUID)});
  eq(existing.api.deviceKey(),VALID_UUID,'Clé persistée forte utilisable sans nouveau tirage');

  const valid=fixture({crypto:goodBytes,backend:{data:{ok:true,state:{}},error:null}});
  const result=await valid.api.invokePersonalAi({action:'get_state'});
  eq(result.ok,true,'Requête légitime conservée');
  eq(valid.calls,1,'Une requête Edge légitime');
  yes(valid.api.isStrongDeviceKey(valid.requestBody.device_key),'RPC reçoit uniquement la clé validée');
  eq(valid.requestBody.action,'get_state','Action attendue conservée');

  const malicious=fixture({crypto:goodBytes,backend:{
    data:{ok:false,code:'UNEXPECTED_SQL',error:SECRET},
    error:null
  }});
  let backendError;
  try{await malicious.api.invokePersonalAi({action:'get_state'})}catch(e){backendError=e}
  yes(backendError,'Erreur Edge refusée');
  noSecret(backendError.message,'Exception cliente');
  const message=malicious.api.friendlyError(backendError);
  noSecret(message,'UI erreur Edge inconnue');
  eq(message,'L’opération Mon IA n’a pas pu être terminée. Aucun accès privé supplémentaire n’a été accordé.',
    'Erreur inconnue redigée');

  const typed=fixture({crypto:goodBytes});
  const missing=typed.api.friendlyError({code:'DEVICE_KEY_UNAVAILABLE',message:SECRET});
  noSecret(missing,'UI Web Crypto manquant');
  yes(missing.includes('identifiant d’appareil fiable'),'Aide à résoudre Web Crypto/Storage indisponible');

  const challengeMalicious=typed.api.friendlyError({
    code:'SECURITY_CHALLENGE_REQUIRED',security:{display_code:SECRET}
  });
  noSecret(challengeMalicious,'Code de confirmation falsifié');
  yes(!challengeMalicious.includes('Code de confirmation :'),
    'Ne pas afficher de code serveur au format inattendu');
  const challengeValid=typed.api.friendlyError({
    code:'SECURITY_CHALLENGE_REQUIRED',security:{display_code:'ab123456'}
  });
  yes(challengeValid.includes('AB123456'),'Code de confirmation alphanumérique légitime conservé');
  const mfa=typed.api.friendlyError({code:'MFA_REQUIRED',message:SECRET});
  noSecret(mfa,'Réponse MFA');

  const html=fs.readFileSync(path.join(__dirname,'../compte/mon-ia.html'),'utf8');
  yes(html.includes('sinjira-personal-ai-v25.js?v=25.0-device-security'),
    'La page invalide le cache de l’ancien module faible');
  yes(!source.includes('globalThis.crypto?.getRandomValues?.(bytes)'),
    'Aucun appel Web Crypto optionnel laissant des octets nuls');
  yes(!source.includes('catch{return randomDeviceKey()}'),
    'Aucun repli éphémère lors du refus de Storage');
  yes(!source.includes("return String(error?.message"),
    'Aucune exception Edge retournée brute aux utilisateurs');

  console.log('PASS: '+checks+' assertions sur vrais modules Mon IA, CSPRNG, stockage, RPC et confidentialité.');
}
main().catch(e=>{console.error(e);process.exitCode=1});
