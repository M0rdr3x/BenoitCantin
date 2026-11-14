#!/usr/bin/env node
'use strict';
// Régression du véritable bridge WebView : Supabase, SecureStore et réseau
// sont remplacés par des doublures. Aucun compte ni jeton réel.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(ROOT, 'assets/js/sinjira-security-push-bridge-v24-4-98.js'), 'utf8');
const UUID = '123e4567-e89b-42d3-a456-426614174000';
const LEGACY = 'sinjira-' + 'ab'.repeat(24) + '-mnxy9';
const TOKEN = 'ExponentPushToken[' + 'A'.repeat(22) + ']';
const SHORT_TOKEN = 'ExpoPushToken[' + 'B'.repeat(22) + ']';
const SECRET = 'SQL auth.users; email=user@example.invalid; JWT eyJ.private-credential';
const KEY = 'sinjira.security.device_key.v1';
const TOKEN_KEY = 'sinjira.security.push_token.v1';
const ENABLED = 'sinjira.security.push_enabled.v1';
const PLATFORM = 'sinjira.security.push_platform.v1';
let checks = 0;
function equal(actual, expected, label) {
  assert.equal(actual, expected, label);
  checks += 1;
}
function yes(test, label) {
  assert.ok(test, label);
  checks += 1;
}
function noSensitive(text, label) {
  for(const part of ['auth.users', 'user@example.invalid', 'eyJ.private-credential']){
    yes(!String(text).includes(part), label + ' : pas de ' + part);
  }
}

function harness({key=UUID, token=TOKEN, enabled='1', platform='ios', user={id:'user-test'}, rpcImpl, storageFails=false}={}){
  const values = new Map([[KEY, key], [TOKEN_KEY, token], [ENABLED, enabled], [PLATFORM, platform]]);
  const calls = [];
  const warnings = [];
  const handlers = new Map();
  let sessionLookups = 0;
  const storage = {
    getItem(name) {
      if (storageFails) throw new Error(SECRET);
      return values.get(name) ?? null;
    },
    setItem(name, value) {values.set(name, value);},
    removeItem(name) {values.delete(name);}
  };
  const sandbox = vm.createContext({
    localStorage: storage,
    window: {addEventListener(name, fn){handlers.set(name, fn);}},
    console: {warn(...parts){warnings.push(parts.join(' '));}},
    async getCurrentUser(){sessionLookups += 1; if(user instanceof Error)throw user; return user;},
    getSupabase(){return {async rpc(name, args){
      calls.push({name, args});
      if(rpcImpl) return rpcImpl(name, args, calls.length);
      return {data:{ok:true}, error:null};
    }}}
  });
  const body = source.replace(/^import[^\n]*\n/gm, '');
  vm.runInContext(body + '\nglobalThis.__bridge={isStrongDeviceKey,isExpoPushToken,schedulePushSync};',
    sandbox, {filename:'sinjira-security-push-bridge-v24-4-98.js', timeout:2000});
  return {
    api:sandbox.__bridge, values, calls, warnings,
    dispatch(){const handler=handlers.get('sinjira:push-changed');yes(typeof handler==='function','Listener natif');handler();},
    get sessionLookups(){return sessionLookups;}
  };
}
const flush=async()=>new Promise(resolve=>setImmediate(resolve));

async function main(){
  yes(source.includes("rpc('security_register_push_endpoint'"),'RPC d’enregistrement self-only conservé');
  yes(source.includes("rpc('security_disable_push_for_device'"),'RPC de retrait conservé');
  yes(!source.includes("error?.message||error"),'Aucun diagnostic Postgres brut en console');
  const good=harness();
  yes(good.api.isStrongDeviceKey(UUID),'UUIDv4 natif valide');
  yes(good.api.isStrongDeviceKey(LEGACY),'Clé historique 192 bits valide');
  for (const key of [
    null, '', '1'.repeat(16), '0'.repeat(64), 'sinjira-'+'0'.repeat(48)+'-a1',
    'sinjira-'+'0'.repeat(48), 'invalid','--',
    '123e4567-e89b-12d3-a456-426614174000',
    '123e4567-e89b-42d3-c456-426614174000',
    'sinjira-'+'xyz'.repeat(16),UUID+SECRET
  ]) equal(good.api.isStrongDeviceKey(key), false, 'Clé faible ou malformée rejetée');

  yes(good.api.isExpoPushToken(TOKEN),'Jeton Expo legacy valide');
  yes(good.api.isExpoPushToken(SHORT_TOKEN),'Jeton Expo modern valide');
  for(const token of [
    '', null,'x'.repeat(40),'Bearer eyJ.myjwt',SECRET,
    'ExpoPushToken['+'!'.repeat(30)+']',
    'ExponentPushToken[truncated',
    'ExponentPushToken[' + 'A'.repeat(301) + ']',
    'ExpoPushToken[' + 'A'.repeat(15) + ']\nX-Test: injected'
  ]) equal(good.api.isExpoPushToken(token),false,'Jeton Expo invalide rejeté');

  await flush();
  equal(good.calls.length,1,'Une seule inscription sur démarrage');
  equal(good.calls[0].name,'security_register_push_endpoint','RPC inscription correct');
  equal(good.calls[0].args.p_device_key,UUID,'Identité transmise inchangée');
  equal(good.calls[0].args.p_expo_push_token,TOKEN,'Jeton approuvé inchangé');
  equal(good.calls[0].args.p_platform,'ios','Plateforme conforme inchangée');
  equal(good.sessionLookups,1,'Une session utilisateur vérifiée');

  const historical=harness({key:LEGACY,token:SHORT_TOKEN,platform:'android'});
  await flush();
  equal(historical.calls.length,1,'Clé 192 bits historique conserve les alertes');
  equal(historical.calls[0].args.p_platform,'android','Android conserve son format');

  for(const key of ['', '1'.repeat(18), 'sinjira-'+'0'.repeat(48)]){
    const blocked=harness({key,token:TOKEN});
    await flush();
    equal(blocked.calls.length,0,'Aucun RPC sur clé faible : '+key.slice(0,15));
  }
  for(const token of [SECRET,'x'.repeat(50),'ExpoPushToken[secret]']){
    const blocked=harness({token});
    await flush();
    equal(blocked.calls.length,0,'Aucun enregistrement sur jeton arbitraire');
  }
  const unauth=harness({user:null});
  await flush();
  equal(unauth.calls.length,0,'Aucun RPC sans utilisateur authentifié');
  const deniedStorage=harness({storageFails:true});
  await flush();
  equal(deniedStorage.calls.length,0,'Aucun RPC quand localStorage est interdit');
  equal(deniedStorage.warnings.length,1,'Erreur Storage signalée sans exception brute');
  noSensitive(deniedStorage.warnings[0],'Message Storage');

  const disabled=harness({enabled:'0',token:SECRET,platform:'ios\nSQL'});
  await flush();
  equal(disabled.calls.length,1,'La révocation fonctionne sans jeton valide');
  equal(disabled.calls[0].name,'security_disable_push_for_device','RPC de désactivation');
  equal(disabled.calls[0].args.p_device_key,UUID,'Révocation pour cet appareil');
  const strangeState=harness({enabled:'garbage'});
  await flush();
  equal(strangeState.calls.length,0,'Préférence non reconnue : refuser toute action');

  const sanitised=harness({platform:'ios\n' + SECRET});
  await flush();
  yes(!sanitised.calls[0].args.p_platform.includes('\n'),'Métadonnée plateforme sans CRLF');
  equal(sanitised.calls[0].args.p_platform.length<=40,true,'Métadonnée plateforme bornée');

  const sqlError=harness({rpcImpl:async()=>({error:{message:SECRET,code:'42501'}})});
  await flush();
  equal(sqlError.warnings.length,1,'RPC refusée signalée sans détails');
  noSensitive(sqlError.warnings[0],'Message RPC');
  const thrown=harness({user:new Error(SECRET)});
  await flush();
  equal(thrown.warnings.length,1,'Exception auth signalée sans détails');
  noSensitive(thrown.warnings[0],'Exception auth');

  // Un événement de désactivation pendant une inscription en vol ne doit
  // PAS démarrer une RPC concurrente susceptible de finir dans le mauvais ordre.
  let registrationStarted;
  const started=new Promise(resolve=>registrationStarted=resolve);
  let release;
  const gate=new Promise(resolve=>release=resolve);
  const rapid=harness({rpcImpl:async(name)=>{
    if(name==='security_register_push_endpoint'){
      registrationStarted();
      await gate;
    }
    return {data:{ok:true},error:null};
  }});
  await started;
  rapid.values.set(ENABLED,'0');
  rapid.values.delete(TOKEN_KEY);
  rapid.dispatch();
  rapid.dispatch();
  await flush();
  equal(rapid.calls.length,1,'Aucune désactivation en parallèle pendant inscription en cours');
  release();
  await flush();
  await flush();
  equal(rapid.calls.length,2,'Un seul retrait final après inscriptions successives');
  equal(rapid.calls[1].name,'security_disable_push_for_device','Retrait du consentement exécuté en dernier');

  const native=fs.readFileSync(path.join(ROOT,'mobile-native/App.tsx'),'utf8');
  yes(native.includes("sinjira-security-push-bridge-v24-4-98.js?v=24.4.100-security"),
    'Les nouveaux builds mobiles invalident le cache de l’ancien bridge');

  console.log('PASS: '+checks+' assertions sur la passerelle push réelle, tokens, identité et opt-out concurrent.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
