#!/usr/bin/env node
'use strict';
// Scénarios synthétiques : aucune connexion, aucun compte ou données réelles.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const test=require('node:test');
const vm=require('node:vm');

const SOURCE=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-security-center-v24-4-98.js'),'utf8');
const VALID_ID='12345678-1234-4234-8234-123456789abc';
const MALICIOUS_ID='" onmouseover="alert(1)"><svg onload="alert(2)">';
const htmlEscape=x=>String(x??'').replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;',
})[c]);

function slice(start,end){
  const a=SOURCE.indexOf(start),b=SOURCE.indexOf(end,a+start.length);
  assert.ok(a>=0&&b>a,'Fonction réelle absente: '+start);
  return SOURCE.slice(a,b);
}

const FUNCTIONS=[
  slice('function randomDeviceKey(){','function weakLegacyDeviceKey('),
  slice('function weakLegacyDeviceKey(','function deviceMetadata(){'),
  slice('function securityRecordId(','async function rpc('),
  slice('function renderDevices(','function renderSessions('),
  slice('function renderTravel(','function fillSettings('),
  slice('function friendlySecurityError(','async function boot(){'),
].join('\n');

function load(secureCrypto){
  const nodes={};
  const storage={local:new Map(),session:new Map()};
  const context=vm.createContext({
    crypto:secureCrypto,Uint8Array,Date,
    localStorage:{
      getItem(k){return storage.local.get(k)||null;},
      setItem(k,v){storage.local.set(k,v);},
    },
    sessionStorage:{
      getItem(k){return storage.session.get(k)||null;},
      setItem(k,v){storage.session.set(k,v);},
    },
    qs(selector){return nodes[selector]||null;},
    qsa(){return [];},
    escapeHtml:htmlEscape,
    formatDate(){return '2026-11-10';},
  });
  vm.runInContext(
    'const DEVICE_KEY_STORAGE="sinjira.security.device_key.v1";\n'+FUNCTIONS+
    '\n;globalThis.__test={randomDeviceKey,deviceKey,weakLegacyDeviceKey,securityRecordId,requiredSecurityRecordId,renderDevices,renderTravel,renderChallenges,friendlySecurityError};',
    context,{filename:'security-center-extract.js',timeout:2000},
  );
  return {...context.__test,nodes,storage};
}

test('absence de générateur cryptographique : ne jamais créer une clé prévisible',()=>{
  for(const crypto of [undefined,{}, {randomUUID:null}, {getRandomValues:null}]){
    const app=load(crypto);
    assert.throws(()=>app.randomDeviceKey(),/SECURE_RANDOM_REQUIRED/);
    assert.throws(()=>app.deviceKey(),/SECURE_RANDOM_REQUIRED/);
    assert.equal(app.storage.local.size,0);
    assert.equal(app.storage.session.size,0);
  }
});

test('rejet explicite des faux générateurs qui laissent 24 octets à zéro',()=>{
  const app=load({getRandomValues(){ /* ne touche pas au tampon */ }});
  assert.throws(()=>app.randomDeviceKey(),/SECURE_RANDOM_REQUIRED/);
  assert.equal(app.storage.local.size,0);
});

test('un UUID généré par Web Crypto reste accepté',()=>{
  let calls=0;
  const app=load({randomUUID(){calls++;return VALID_ID;}});
  assert.equal(app.deviceKey(),VALID_ID);
  assert.equal(app.deviceKey(),VALID_ID);
  assert.equal(calls,1,'la clé persistante n’est pas régénérée sans raison');
});

test('le repli Web Crypto fournit un secret aléatoire de 192 bits sans date',()=>{
  const app=load({getRandomValues(bytes){
    for(let i=0;i<bytes.length;i++)bytes[i]=i+1;
    return bytes;
  }});
  const key=app.randomDeviceKey();
  assert.match(key,/^sinjira-[0-9a-f]{48}$/);
  assert.equal(key,'sinjira-'+Array.from({length:24},(_,i)=>(i+1).toString(16).padStart(2,'0')).join(''));
});

test('une ancienne clé nulle et prévisible est régénérée dans localStorage',()=>{
  const old='sinjira-'+'0'.repeat(48)+'-abc123';
  const app=load({randomUUID(){return VALID_ID;}});
  app.storage.local.set('sinjira.security.device_key.v1',old);
  assert.equal(app.weakLegacyDeviceKey(old),true);
  assert.equal(app.deviceKey(),VALID_ID);
  assert.equal(app.storage.local.get('sinjira.security.device_key.v1'),VALID_ID);
});

test('une ancienne clé nulle est aussi régénérée dans sessionStorage',()=>{
  const old='sinjira-'+'0'.repeat(48)+'-abc123';
  const app=load({randomUUID(){return VALID_ID;}});
  app.storage.session.set('sinjira.security.device_key.v1',old);
  // Dans le navigateur, localStorage peut être inaccessible sans tuer la session.
  // Ici on simule cette branche avec une erreur lors du premier accès.
  const code=FUNCTIONS;
  const context=vm.createContext({
    crypto:{randomUUID(){return VALID_ID;}},Uint8Array,
    localStorage:{getItem(){throw new Error('unavailable');}},
    sessionStorage:{getItem(){return old;},setItem(k,v){app.storage.session.set(k,v);}},
  });
  vm.runInContext('const DEVICE_KEY_STORAGE="sinjira.security.device_key.v1";\n'+
    slice('function randomDeviceKey(){','function deviceMetadata(){')+
    '\n;globalThis.go=deviceKey;',context);
  assert.equal(context.go(),VALID_ID);
  assert.equal(app.storage.session.get('sinjira.security.device_key.v1'),VALID_ID);
});

test('les identifiants des commandes sensibles sont limités à des UUID',()=>{
  const app=load({randomUUID(){return VALID_ID;}});
  assert.equal(app.securityRecordId(VALID_ID),VALID_ID);
  for(const value of [
    MALICIOUS_ID,'../../admin','',null,{},42,
    VALID_ID+'?admin=true','{'+VALID_ID+'}',
    '0123','AAAAAAAA-AAAA-AAAA-AAAA-AAAA',
  ]){
    assert.equal(app.securityRecordId(value),null,String(value));
    assert.throws(()=>app.requiredSecurityRecordId(value),/SECURITY_RECORD_ID_INVALID/);
  }
});

test('les enregistrements d’appareils falsifiés ne génèrent aucun bouton',()=>{
  const app=load({randomUUID(){return VALID_ID;}});
  const node={innerHTML:''};app.nodes['[data-security-devices]']=node;
  app.renderDevices([
    {id:MALICIOUS_ID,display_name:'<svg onload=alert(1)>',is_current:true,is_trusted:true},
    {id:VALID_ID,display_name:'<img src=x onerror=alert(2)>',is_current:true,is_trusted:false},
  ]);
  assert.equal((node.innerHTML.match(/data-device-id=/g)||[]).length,1);
  assert.ok(node.innerHTML.includes('data-device-id="'+VALID_ID+'"'));
  assert.ok(node.innerHTML.includes('data-device-trust="'+VALID_ID+'"'));
  assert.ok(node.innerHTML.includes('&lt;img src=x onerror=alert(2)&gt;'));
  assert.ok(!node.innerHTML.includes(MALICIOUS_ID));
  assert.ok(!node.innerHTML.includes('<svg'));
});

test('un voyage invalide reste sans commande annulable',()=>{
  const app=load({randomUUID(){return VALID_ID;}});
  const node={innerHTML:''};app.nodes['[data-security-travel-list]']=node;
  app.renderTravel([
    {id:MALICIOUS_ID,status:'active',destinations:['CA']},
    {id:VALID_ID,status:'active',destinations:['FR']},
  ]);
  assert.equal((node.innerHTML.match(/data-travel-cancel=/g)||[]).length,1);
  assert.ok(node.innerHTML.includes('data-travel-cancel="'+VALID_ID+'"'));
  assert.ok(!node.innerHTML.includes(MALICIOUS_ID));
});

test('un challenge invalide ne peut afficher Autoriser ou Refuser',()=>{
  const app=load({randomUUID(){return VALID_ID;}});
  const node={innerHTML:''};app.nodes['[data-security-challenges]']=node;
  const devices=[{id:VALID_ID,is_current:true,is_trusted:true,revoked_at:null}];
  app.renderChallenges([{
    id:MALICIOUS_ID,status:'pending',expires_at:'2099-01-01T00:00:00Z',
    request_device_id:'dddddddd-1111-4111-8111-000000000000',display_code:'123456',
  }],devices);
  assert.ok(!node.innerHTML.includes('data-challenge-approve'));
  assert.ok(!node.innerHTML.includes('data-challenge-deny'));
  assert.ok(!node.innerHTML.includes(MALICIOUS_ID));
  app.renderChallenges([{
    id:'11111111-2222-4333-8444-555555555555',status:'pending',expires_at:'2099-01-01T00:00:00Z',
    request_device_id:'dddddddd-1111-4111-8111-000000000000',display_code:'123456',
  }],devices);
  assert.ok(node.innerHTML.includes('data-challenge-approve="11111111-2222-4333-8444-555555555555"'));
  assert.ok(node.innerHTML.includes('data-challenge-deny="11111111-2222-4333-8444-555555555555"'));
});

test('les 7 mutations de confiance exigent un UUID avant appel RPC',()=>{
  const actions=[
    'deviceTrust','devicePrimary','deviceUntrust','deviceRevoke',
    'travelCancel','challengeApprove','challengeDeny',
  ];
  for(const action of actions){
    assert.ok(SOURCE.includes('requiredSecurityRecordId(target.dataset.'+action+')'),
      'validation absente pour '+action);
  }
  assert.ok(!SOURCE.includes('getRandomValues?.(bytes)'), 'repli faible interdit');
});
