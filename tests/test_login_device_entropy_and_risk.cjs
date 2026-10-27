'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.join(__dirname,'..');
function read(rel){return fs.readFileSync(path.join(root,rel),'utf8');}
const auth=read('assets/js/sinjira-auth-pages.js');
const center=read('assets/js/sinjira-security-center-v24-4-98.js');

function randomGenerator(src){
  const start=src.indexOf('function randomDeviceKey(){');
  assert.ok(start>=0,'Générateur de clé d’appareil absent');
  const end=src.indexOf('\n}',start);
  assert.ok(end>start,'Fonction randomDeviceKey non vérifiable');
  const code=src.slice(start,end+2);
  assert.doesNotMatch(code,/Date\.now\(|Math\.random\(/,'Entropie horloge/PRNG interdite');
  assert.match(code,/getRandomValues/);
  assert.match(code,/SECURE_RANDOM_UNAVAILABLE/);
  return new Function('globalThis','Uint8Array',code+'\nreturn randomDeviceKey;');
}
for(const [label,src] of [['connexion',auth],['centre de sécurité',center]]){
  test(label+': UUID CSPRNG ou 192 bits réels, sinon erreur fermée',()=>{
    const make=randomGenerator(src);
    assert.equal(make({crypto:{randomUUID:()=>'secure-uuid'}} ,Uint8Array)(),'secure-uuid');
    const fallback=make({crypto:{getRandomValues:a=>a.fill(0xa5)}},Uint8Array)();
    assert.equal(fallback,'sinjira-'+'a5'.repeat(24));
    assert.throws(()=>make({crypto:{}},Uint8Array)(),/SECURE_RANDOM_UNAVAILABLE/);
    assert.throws(()=>make({},Uint8Array)(),/SECURE_RANDOM_UNAVAILABLE/);
  });
}

function loginShieldIsFailClosed(source){
  const start=source.indexOf('}catch(securityError){');
  if(start<0)return false;
  const end=source.indexOf('\n      const outcome=',start);
  if(end<0)return false;
  const failureBranch=source.slice(start,end);
  return failureBranch.includes("auth.signOut({scope:'local'})") &&
    failureBranch.includes('setStatus(status,') &&
    !failureBranch.includes('location.replace(') &&
    failureBranch.includes('return;');
}
test('connexion: panne du contexte interdit une session utilisable',()=>{
  assert.ok(loginShieldIsFailClosed(auth),'Le risque doit échouer fermé');
  const weakened=auth.replace("await getSupabase().auth.signOut({scope:'local'}).catch(()=>{});",
     'location.replace(next);');
  assert.notEqual(weakened,auth,'Mutation anti-régression invalide');
  assert.equal(loginShieldIsFailClosed(weakened),false,
    'Un retour à la connexion fail-open doit être refusé');
});
