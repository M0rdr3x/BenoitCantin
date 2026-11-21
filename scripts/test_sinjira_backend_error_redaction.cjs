#!/usr/bin/env node
'use strict';
// Vérifie les vraies fonctions de rendu d'erreurs du module partagé SINJIRA.
// Scénarios synthétiques uniquement, sans comptes ni réseau.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const test=require('node:test');
const vm=require('node:vm');

const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-supabase.js'),'utf8');

function actualFunctions(){
  const start=source.indexOf('export function friendlyBackendMessage(');
  const end=source.indexOf('export function roleLabel(',start);
  assert.ok(start>=0&&end>start,'bloc réel des helpers de messages manquant');
  return source.slice(start,end).replaceAll('export function ','function ');
}

function renderer(){
  const logs=[];
  const ctx=vm.createContext({
    console:{warn(...args){logs.push(args.map(String).join(' '));}},
  });
  vm.runInContext(actualFunctions()+
    '\n;globalThis.api={friendlyBackendMessage,setStatus};',ctx,
    {filename:'sinjira-supabase-messages.js',timeout:1500});
  const node={
    hidden:true,textContent:null,dataset:{},attributes:{},
    setAttribute(key,value){this.attributes[key]=value;},
  };
  return {...ctx.api,node,logs};
}

test('une erreur inconnue ne révèle ni secret, ni SQL, ni diagnostic interne',()=>{
  const data=[
    "ERROR: relation private.users doesn't exist; query: SELECT * FROM auth.sessions",
    'access_token=eyJhbGciOiJIUzI1NiJ9.fake.signature',
    'password=secret-pass-123; email=private@example.test',
    'Unexpected backend error: user_uuid=43bbd6b3-50c3-49cd-903b-961fb51328e5',
    'Error: storage secret key sk_test_temporary',
    'private.schema_function: unhandled exception',
    'Internal error',
    '<img src=x onerror=alert(1)>',
  ];
  for(const message of data){
    const {setStatus,node,logs}=renderer();
    setStatus(node,message,'error');
    assert.ok(node.textContent,'un message de remplacement doit être présent');
    assert.ok(!node.textContent.includes(message),'détail brut rendu');
    assert.equal(node.textContent,'Une opération serveur n’a pas pu être terminée.');
    assert.equal(node.attributes.role,'alert');
    assert.equal(node.attributes['aria-live'],'assertive');
    assert.equal(logs.length,0,'le texte sensible ne doit pas rejoindre la console');
  }
});

test('les erreurs standard continuent à retourner des messages sûrs et utiles',()=>{
  const cases=[
    ['AUTH_REQUIRED','Connexion requise pour cette opération.'],
    ['AAL2_REQUIRED','Une authentification renforcée est requise pour cette opération sensible.'],
    ['JWT expired','Votre session a expiré. Reconnectez-vous puis réessayez.'],
    ['permission denied for relation private_admin','Votre compte n’a pas l’autorisation nécessaire pour cette opération.'],
    ['PGRST202 Could not find the function secret.function','Le serveur SINJIRA™ doit encore être synchronisé pour cette fonction.'],
    ['NetworkError loading user@example.test','Communication avec le serveur SINJIRA™ impossible pour le moment.'],
    ['INVALID_OR_EXPIRED_GUARDIAN_CODE','Le code d’autorisation parentale est invalide, expiré ou déjà utilisé.'],
  ];
  for(const [input,expected] of cases){
    const {setStatus,node,logs}=renderer();
    setStatus(node,input,'error');
    assert.equal(node.textContent,expected,input);
    assert.equal(logs.length,0,'aucune erreur reconnue loggée en clair');
  }
});

test('les confirmations normales et les messages informatifs ne sont pas remplacés',()=>{
  for(const type of ['success','info']){
    const {setStatus,node}=renderer();
    const message='Réservation enregistrée. Vous pouvez fermer cette page.';
    setStatus(node,message,type);
    assert.equal(node.textContent,message);
    assert.equal(node.attributes.role,'status');
    assert.equal(node.attributes['aria-live'],'polite');
    assert.equal(node.dataset.statusType,type);
    assert.equal(node.hidden,false);
  }
});

test('un noeud inexistant reste sans effet',()=>{
  const {setStatus,logs}=renderer();
  assert.equal(setStatus(null,'access_token=private','error'),undefined);
  assert.equal(logs.length,0);
});

test('friendlyBackendMessage utilise une valeur de remplacement sûre par défaut',()=>{
  const {friendlyBackendMessage}=renderer();
  assert.equal(friendlyBackendMessage('unrecognized SQL backend trace'),'Une opération serveur n’a pas pu être terminée.');
  assert.equal(friendlyBackendMessage(''), 'Une opération serveur n’a pas pu être terminée.');
});

test('les sorties de diagnostic Auth, MFA et admin n’impriment plus les erreurs brutes',()=>{
  assert.ok(!source.includes("console.warn('[SINJIRA backend]',raw)"));
  assert.ok(!source.includes("console.warn('[SINJIRA MFA gate]',error?.message||error)"));
  assert.ok(!source.includes("console.warn('[SINJIRA admin health loader]',err)"));
  assert.ok(!source.includes("friendlyBackendMessage(raw,raw||"));
  assert.ok(source.includes("const friendly=isError?friendlyBackendMessage(raw):raw;"));
});
