'use strict';
// Tests locaux : aucune connexion, aucun compte et aucune requête Supabase.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');

const ROOT=path.resolve(__dirname,'..');
const readerPromise=import(pathToFileURL(path.join(
  ROOT,'supabase/functions/_shared/bounded-request.mjs')).href);
function request(chunks,declared=null,onCancel=()=>{}) {
  let position=0;
  const headers=new Headers();
  if(declared!==null)headers.set('content-length',declared);
  return {
    headers,body:new ReadableStream({
      pull(controller) {
        if(position>=chunks.length) controller.close();
        else controller.enqueue(chunks[position++]);
      },
      cancel(){onCancel();}
    })
  };
}
const bytes=value=>new TextEncoder().encode(value);

test('le corps JSON sous la limite est reconstruit sans perte Unicode',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  const data='{"nom":"Élève","ok":true}';
  const raw=bytes(data);
  const req=request([raw.slice(0,7),raw.slice(7,11),raw.slice(11)],String(raw.length));
  assert.equal(await readBoundedRequestText(req,4096),data);
});
test('borne exacte acceptée et dépassement interrompu au milieu du flux',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  const cap=4096;
  assert.equal((await readBoundedRequestText(request([bytes('a'.repeat(cap))]),cap)).length,cap);
  let cancelled=0;
  await assert.rejects(
    readBoundedRequestText(
      request([bytes('a'.repeat(4090)),bytes('b'.repeat(20)),
               bytes('c'.repeat(200))],null,()=>cancelled++),cap),
    /REQUEST_TOO_LARGE/);
  assert.equal(cancelled,1,'La connexion doit être annulée au dépassement');
});
test('le Content-Length absent ne supprime pas la limite',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  await assert.rejects(
    readBoundedRequestText(request([bytes('x'.repeat(4097))]),4096),
    /REQUEST_TOO_LARGE/);
});
test('en-têtes négatifs, ambigus et surdimensionnés rejetés AVANT lecture',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  for(const header of ['-1','4097','3, 4','not-a-size','9e6']) {
    let called=false;
    const req={headers:new Headers({'content-length':header}),
      body:{getReader(){called=true;throw Error('MUST_NOT_READ');}}};
    await assert.rejects(readBoundedRequestText(req,4096),/REQUEST_TOO_LARGE/);
    assert.equal(called,false,'La lecture ne doit pas commencer: '+header);
  }
});
test('octets UTF-8 invalides et fragments non octet sont refusés',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  await assert.rejects(
    readBoundedRequestText(request([Uint8Array.of(0xc3,0x28)]),4096),
    /INVALID_JSON/);
  await assert.rejects(
    readBoundedRequestText(request([new Int16Array([1])]),4096),
    /INVALID_JSON/);
});
test('limites invalides refusées; corps absent autorisé comme objet vide',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  assert.equal(await readBoundedRequestText({headers:new Headers(),body:null},4096),'');
  await assert.rejects(
    readBoundedRequestText(request([bytes('{}')]),0),/REQUEST_TOO_LARGE/);
  await assert.rejects(
    readBoundedRequestText(request([bytes('{}')]),Infinity),/REQUEST_TOO_LARGE/);
});
test('les six fonctions admin utilisent la borne AVANT req.text()',()=>{
  const functions=[
    'admin-analytics','admin-console','admin-license-codes',
    'admin-reports','admin-sinjira-v18','admin-social-v20'
  ];
  for(const name of functions) {
    const source=fs.readFileSync(path.join(
      ROOT,'supabase/functions',name,'index.ts'),'utf8');
    assert.match(source,/import \{ readBoundedRequestText \} from '\.\.\/_shared\/bounded-request\.mjs'/,
      name+': dépendance sécurisée requise');
    assert.match(source,/await readBoundedRequestText\(req, MAX_REQUEST_BYTES\)/,
      name+': limite serveur requise');
    assert.doesNotMatch(source,/await req\.(?:text|json|arrayBuffer)\(\)/,
      name+': pas de lecture sans contrôle de taille');
    assert.match(source,/await requiredAdmin\(req\)/,name+': MFA admin indispensable');
  }
});

test('les 12 routes privées supplémentaires lisent le corps en flux borné',()=>{
  const sensitive=[
    'delete-player-account','fracture-engine-gateway',
    'life-story-delivery','life-story-export','redeem-license-code',
    'revoke-my-contributions','security-context','send-game-report',
    'send-player-sheet','submit-character-questionnaire',
    'submit-fracture-endgame','submit-game-contribution'
  ];
  for(const name of sensitive) {
    const source=fs.readFileSync(path.join(
      ROOT,'supabase/functions',name,'index.ts'),'utf8');
    assert.match(source,/import \{ readBoundedRequestText \} from '\.\.\/_shared\/bounded-request\.mjs'/,
      name+': lecteur commun absent');
    const cap=name==='fracture-engine-gateway'?'MAX_BODY_BYTES':'MAX_REQUEST_BYTES';
    assert.ok(source.includes('await readBoundedRequestText(req, '+cap+')'),
      name+': limite de corps non appliquée');
    assert.doesNotMatch(source,/await req\.(?:text|json|arrayBuffer)\(\)/,
      name+': lecture HTTP brute non bornée');
  }
});
test('la limite existante de 2 Mio pour le questionnaire sensible reste supportée',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  const cap=2*1024*1024;
  const body=bytes('x'.repeat(cap));
  assert.equal((await readBoundedRequestText(request([body]),cap)).length,cap);
  await assert.rejects(readBoundedRequestText(request([body,bytes('z')]),cap),
    /REQUEST_TOO_LARGE/);
});

test('plus de 4096 fragments minuscules sont rejetés sans dépasser les octets',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  let cancelled=0;
  // Garder le producteur ouvert après le 4097e segment: ReadableStream
  // peut précharger et fermer un flux de 4099 éléments avant le cancel().
  const many=Array.from({length:5000},()=>Uint8Array.of(65));
  await assert.rejects(
    readBoundedRequestText(request(many,null,()=>cancelled++),2*1024*1024),
    /REQUEST_TOO_LARGE/);
  assert.equal(cancelled,1,'Annulation immédiate au-delà du nombre de fragments');
});
test('4096 fragments légitimes restent autorisés à la taille prévue',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  const chunks=Array.from({length:4096},()=>Uint8Array.of(65));
  const text=await readBoundedRequestText(request(chunks),2*1024*1024);
  assert.equal(text.length,4096);
});

test('une lecture HTTP suspendue expire et annule le flux',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  let cancelled=0;
  const req={
    headers:new Headers(),
    body:new ReadableStream({
      start(controller){controller.enqueue(bytes('{"incomplet":'));},
      cancel(){cancelled++;}
    })
  };
  const start=Date.now();
  await assert.rejects(readBoundedRequestText(req,4096,25),/REQUEST_TIMEOUT/);
  assert.equal(cancelled,1,'La requête bloquée doit être annulée');
  assert.ok(Date.now()-start<1500,'Le timeout ne doit pas bloquer le worker');
});
test('le délai de lecture est global, pas relancé par les fragments',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  let cancelled=0;
  let count=0;
  const req={
    headers:new Headers(),
    body:new ReadableStream({
      async pull(controller){
        await new Promise(resolve=>setTimeout(resolve,12));
        controller.enqueue(Uint8Array.of(65));
        count++;
      },
      cancel(){cancelled++;}
    })
  };
  const start=Date.now();
  await assert.rejects(readBoundedRequestText(req,4096,65),/REQUEST_TIMEOUT/);
  assert.ok(count>0 && count<40,'Le flux a dû progresser puis expirer');
  assert.ok(Date.now()-start<1500,'La lecture au compte-gouttes ne doit pas durer');
  assert.equal(cancelled,1);
});
test('un délai invalide échoue sans démarrer la lecture',async()=>{
  const {readBoundedRequestText}=await readerPromise;
  for(const ms of [0,-1,30001,Infinity,1.5]){
    let readerStarted=false;
    const req={headers:new Headers(),body:{getReader(){readerStarted=true;}}};
    await assert.rejects(readBoundedRequestText(req,4096,ms),/REQUEST_TIMEOUT/);
    assert.equal(readerStarted,false);
  }
});
