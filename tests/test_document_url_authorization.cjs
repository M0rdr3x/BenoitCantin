'use strict';
// Exécution locale de la véritable fonction Edge avec mocks service_role.
// Aucun appel réseau, aucune clé Supabase, aucun document réel.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

const source=fs.readFileSync(path.join(__dirname,
  '../supabase/functions/get-document-url/index.ts'),'utf8');
function buildHandler(mock){
  const boundedReaderSource=fs.readFileSync(path.join(__dirname,
    '../supabase/functions/_shared/bounded-request.mjs'),'utf8');
  assert.match(boundedReaderSource,/export async function readBoundedRequestText\(/);
  const boundedReader=boundedReaderSource.replace(
    'export async function readBoundedRequestText',
    'async function readBoundedRequestText');
  let transformed=source.replace(/^import[^\n]*\n/gm,'')
    .replace('const ranks:Record<string,number>','const ranks')
    .replace('const chunks:Uint8Array[]=[];','const chunks=[];')
    .replace('let raw:string;','let raw;')
    .replace('function privateJson(data:unknown,status=200)','function privateJson(data,status=200)')
    .replace('function externalUrlAllowed(value:string)','function externalUrlAllowed(value)')
    .replace('async function readLimitedJson(req:Request):Promise<{body?:any;response?:Response}>',
      'async function readLimitedJson(req)');
  assert.doesNotMatch(transformed,/\bimport\s+.*from/);
  let handler;
  const context={
    Response,Request,TextEncoder,TextDecoder,Uint8Array,URL,console,setTimeout,clearTimeout,
    corsHeaders:{'Access-Control-Allow-Origin':'*'},
    optionalUser:async(req)=>req.headers.get('Authorization')==='Bearer anonymous'
      ?null:{id:'test-member'},
    serviceClient:()=>mock,
    Deno:{serve(callback){handler=callback}}
  };
  vm.runInNewContext(boundedReader+'\n'+transformed,context,{filename:'get-document-url/index.ts'});
  assert.equal(typeof handler,'function');
  return handler;
}
const DOCUMENT_ID='11111111-1111-4111-8111-111111111111';
const doc={
  project_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',status:'approved',
  access_level:'tester',external_url:null,
  storage_bucket:'private-documents',storage_path:'test.pdf',
  projects:{id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',status:'active',visibility:'restricted'}
};
function fixture({owner=false,admin=false,rank=0,rankError=null,ownerError=null,
  adminError=null,document=doc}={}){
  const calls=[],stats={signed:0,rank:0};
  const service={
    from(table){
      assert.equal(table,'documents');
      return {select(){return {eq(){return {maybeSingle:async()=>({data:document,error:null})}}}}};
    },
    async rpc(name,args){
      calls.push(name);
      assert.equal(args.p_user_id,'test-member');
      if(name==='is_sinjira_owner')return {data:owner,error:ownerError};
      if(name==='is_sinjira_admin')return {data:admin,error:adminError};
      if(name==='project_access_rank'){stats.rank++;
        assert.equal(args.p_project_id,doc.project_id);
        return {data:rank,error:rankError};
      }
      throw Error('Unexpected RPC '+name);
    },
    storage:{from(name){assert.equal(name,'private-documents');
      return {createSignedUrl:async(path,ttl)=>{
        assert.equal(path,'test.pdf');assert.equal(ttl,600);stats.signed++;
        return {data:{signedUrl:'https://private.example/signed'},error:null};
      }};
    }}
  };
  return {service,calls,stats};
}
async function attempt(options={},bearer='member'){
  const f=fixture(options),handler=buildHandler(f.service);
  const req=new Request('https://functions.local/functions/v1/get-document-url',{
    method:'POST',headers:{'Content-Type':'application/json',
      Authorization:'Bearer '+bearer},
    body:JSON.stringify({document_id:DOCUMENT_ID})
  });
  const response=await handler(req);
  return {status:response.status,body:await response.json(),...f};
}

test('créateur confirmé par RPC: rang 100 même sans admin et sans licence projet',async()=>{
  const x=await attempt({owner:true,admin:false,rank:0});
  assert.equal(x.status,200);
  assert.equal(x.body.ok,true);
  assert.equal(x.body.protected,true);
  assert.equal(x.stats.signed,1);
  assert.equal(x.stats.rank,0);
  assert.deepEqual(x.calls,['is_sinjira_owner','is_sinjira_admin']);
});
test('administrateur confirmé: rang 100 et lien temporaire signé',async()=>{
  const x=await attempt({owner:false,admin:true,rank:0});
  assert.equal(x.status,200);assert.equal(x.stats.rank,0);
  assert.equal(x.stats.signed,1);
});
test('membre sans droit: 403 et aucun fichier signé',async()=>{
  const x=await attempt({owner:false,admin:false,rank:0});
  assert.equal(x.status,403);assert.equal(x.stats.signed,0);
  assert.equal(x.stats.rank,1);
});
test('membre autorisé par rang serveur: fichier signé',async()=>{
  const x=await attempt({owner:false,admin:false,rank:30});
  assert.equal(x.status,200);assert.equal(x.stats.signed,1);
});
test('droits indisponibles: 503 sans fuite ni lien signé',async()=>{
  const x=await attempt({owner:false,admin:false,rankError:{message:'offline'}});
  assert.equal(x.status,503);assert.equal(x.stats.signed,0);
  assert.doesNotMatch(JSON.stringify(x.body),/offline/);
});
test('RPC propriétaire échouée: aucun contournement si rang insuffisant',async()=>{
  const x=await attempt({owner:true,ownerError:{message:'offline'},admin:false,rank:0});
  assert.equal(x.status,403);assert.equal(x.stats.signed,0);
});
test('document non approuvé: aucun lien même pour propriétaire',async()=>{
  const x=await attempt({owner:true,document:{...doc,status:'draft'}});
  assert.equal(x.status,404);assert.equal(x.stats.signed,0);
});
test('anonyme sans rang : document privé refusé',async()=>{
  const x=await attempt({owner:false},'anonymous');
  assert.equal(x.status,403);assert.equal(x.stats.signed,0);
  assert.deepEqual(x.calls,[]);
});

// La connexion ne doit jamais supprimer le niveau d'accès public d'un
// projet public actif; les documents restreints restent protégés.
const publicDoc={
  ...doc,access_level:'public',
  projects:{...doc.projects,visibility:'public'}
};

test('document public approuvé: même accès pour visiteur anonyme et membre connecté',async()=>{
  for(const bearer of ['anonymous','member']){
    const x=await attempt({document:publicDoc,rank:0},bearer);
    assert.equal(x.status,200);
    assert.equal(x.body.protected,true);
    assert.equal(x.stats.signed,1);
    assert.equal(x.stats.rank,0);
    assert.deepEqual(x.calls,[]);
  }
});
test('document public: aucune panne RPC ne doit pénaliser un membre connecté',async()=>{
  const x=await attempt({document:publicDoc,rankError:{message:'offline'},
    ownerError:{message:'offline'},adminError:{message:'offline'}});
  assert.equal(x.status,200);
  assert.equal(x.stats.signed,1);
  assert.deepEqual(x.calls,[]);
});
test('document public dans projet restreint: aucun accès anonyme',async()=>{
  const restricted={...doc,access_level:'public'};
  const x=await attempt({document:restricted},'anonymous');
  assert.equal(x.status,403);
  assert.equal(x.stats.signed,0);
  assert.deepEqual(x.calls,[]);
});
test('document public dans projet restreint: accès seulement avec rang serveur',async()=>{
  const restricted={...doc,access_level:'public'};
  const denied=await attempt({document:restricted,rank:0});
  assert.equal(denied.status,403);
  assert.equal(denied.stats.signed,0);
  const allowed=await attempt({document:restricted,rank:1});
  assert.equal(allowed.status,200);
  assert.equal(allowed.stats.signed,1);
  assert.equal(allowed.stats.rank,1);
});
test('document privé dans projet public: accès réservé au rang exigé',async()=>{
  const privateDoc={...publicDoc,access_level:'tester'};
  const visitor=await attempt({document:privateDoc},'anonymous');
  assert.equal(visitor.status,403);
  assert.equal(visitor.stats.signed,0);
  const denied=await attempt({document:privateDoc,rank:0});
  assert.equal(denied.status,403);
  assert.equal(denied.stats.signed,0);
  const allowed=await attempt({document:privateDoc,rank:30});
  assert.equal(allowed.status,200);
  assert.equal(allowed.stats.signed,1);
});
test('document public non approuvé ou projet inactif: refus à tous',async()=>{
  for(const document of [
    {...publicDoc,status:'draft'},
    {...publicDoc,projects:{...publicDoc.projects,status:'inactive'}}
  ]){
    for(const bearer of ['anonymous','member']){
      const x=await attempt({document},bearer);
      assert.equal(x.status,404);
      assert.equal(x.stats.signed,0);
    }
  }
});

// Le registre peut référencer des documents publics externes HTTPS ou
// des chemins locaux. Un chemin avec une barre inverse peut changer l'hôte
// à l'ouverture : il ne doit jamais être renvoyé comme URL autorisée.
test('URL documentaire locale légitime: reste accessible au visiteur et membre',async()=>{
  const url='/projets/sinjira/documents/demo.pdf?lecture=1#debut';
  for(const bearer of ['anonymous','member']){
    const x=await attempt({document:{...publicDoc,external_url:url}},bearer);
    assert.equal(x.status,200);
    assert.equal(x.body.url,url);
    assert.equal(x.body.protected,false);
    assert.equal(x.stats.signed,0);
    assert.deepEqual(x.calls,[]);
  }
});
test('document externe HTTPS explicite: reste autorisé sans lien signé',async()=>{
  const url='https://example.org/documents/guide.pdf';
  const x=await attempt({document:{...publicDoc,external_url:url}},'anonymous');
  assert.equal(x.status,200);
  assert.equal(x.body.url,url);
  assert.equal(x.body.protected,false);
  assert.equal(x.stats.signed,0);
});
test('URL ambiguë ou contenant un identifiant: aucune URL publiée',async()=>{
  const invalid=[
    '/\\\\evil.example/private.pdf',
    '/\\\\/evil.example/private.pdf',
    '/docs/%5cevil.example/private.pdf',
    '/docs/%2fhidden.pdf',
    '//evil.example/private.pdf',
    'https://user:secret@example.org/private.pdf',
    'https:/example.org/private.pdf',
    'https:\\\\example.org/private.pdf',
    'http://example.org/private.pdf',
    'javascript:alert(1)',
    ' /docs/guide.pdf',
    '/docs/guide.pdf\\n',
  ];
  for(const url of invalid){
    const x=await attempt({document:{...publicDoc,external_url:url}},'member');
    assert.equal(x.status,500,'URL non refusée: '+JSON.stringify(url));
    assert.equal(x.body.ok,false);
    assert.equal(x.stats.signed,0);
    assert.deepEqual(x.calls,[]);
    assert.doesNotMatch(JSON.stringify(x.body),/secret|evil.example/i);
  }
});
test('une URL ambiguë ne contourne jamais les droits d’un document restreint',async()=>{
  const restricted={...doc,external_url:'/\\\\evil.example/private.pdf'};
  const x=await attempt({document:restricted,rank:0});
  assert.equal(x.status,403);
  assert.equal(x.stats.signed,0);
});

// Un niveau de document issu du registre ne doit jamais bénéficier des
// propriétés héritées d'un objet JavaScript (Object.prototype).
test('niveaux d’accès inconnus ou hérités: refus même au propriétaire',async()=>{
  const invalid=[
    'constructor','toString','__proto__','hasOwnProperty',
    'valueOf','isPrototypeOf','propertyIsEnumerable',
    'unknown','','PUBLIC',null,undefined,0,{},['public'],
  ];
  for(const level of invalid){
    const document={...publicDoc,access_level:level};
    for(const bearer of ['anonymous','member']){
      const x=await attempt({document,owner:true,admin:true,rank:100},bearer);
      assert.equal(x.status,403,
        'Niveau non autorisé: '+String(level)+' / '+bearer);
      assert.equal(x.stats.signed,0);
      assert.equal(x.body.ok,false);
      assert.deepEqual(x.calls,[],'Aucune RPC pour un niveau inconnu');
    }
  }
});
test('URL externe d’un document au niveau hérité: aucun lien divulgué',async()=>{
  for(const level of ['constructor','toString','__proto__']){
    const document={...publicDoc,access_level:level,
      external_url:'https://example.org/restricted.pdf'};
    const x=await attempt({document,owner:true,rank:100});
    assert.equal(x.status,403);
    assert.equal(x.body.url,undefined);
    assert.equal(x.stats.signed,0);
  }
});
test('niveau inconnu: rang serveur 999 ou supérieur ne doit jamais autoriser',async()=>{
  for(const level of ['unknown','constructor','__proto__']){
    for(const rank of [999,1000,999999,Number.MAX_SAFE_INTEGER]){
      const document={...publicDoc,access_level:level};
      const x=await attempt({document,rank,owner:false,admin:false});
      assert.equal(x.status,403,'Niveau '+level+', rang '+rank);
      assert.equal(x.body.ok,false);
      assert.equal(x.body.url,undefined);
      assert.equal(x.stats.signed,0);
      assert.deepEqual(x.calls,[],'Refus avant toute consultation de rôle ou rang');
    }
  }
});
test('niveau inconnu: ni erreur RPC ni URL externe ne changent le refus strict',async()=>{
  const x=await attempt({
    document:{...publicDoc,access_level:'invalid',
      external_url:'https://example.org/protected.pdf'},
    rank:1000,owner:true,admin:true,rankError:{message:'offline'}
  });
  assert.equal(x.status,403);
  assert.equal(x.body.url,undefined);
  assert.equal(x.stats.signed,0);
  assert.deepEqual(x.calls,[]);
});
test('niveaux explicites du registre: seuil de rang serveur respecté',async()=>{
  for(const [level,required] of [
    ['public',1],['account',10],['player',20],['tester',30],['admin',100]
  ]){
    const document={...doc,access_level:level};
    const denied=await attempt({document,rank:required-1});
    assert.equal(denied.status,403,'Refus attendu: '+level);
    assert.equal(denied.stats.signed,0);
    const granted=await attempt({document,rank:required});
    assert.equal(granted.status,200,'Accès confirmé: '+level);
    assert.equal(granted.stats.signed,1);
  }
});

test('requête volumineuse sans Content-Length: refuse avant signature',async()=>{
  const f=fixture(),handler=buildHandler(f.service);
  const response=await handler(new Request('https://functions.local/functions/v1/get-document-url',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({document_id:DOCUMENT_ID,padding:'x'.repeat(900)})
  }));
  assert.equal(response.status,413);assert.equal(f.stats.signed,0);
  assert.deepEqual(f.calls,[]);
  assert.equal(response.headers.get('cache-control'),'private, no-store, max-age=0');
});
test('Content-Length trop grand: refuse avant lecture et accès aux données',async()=>{
  const f=fixture(),handler=buildHandler(f.service);
  const response=await handler(new Request('https://functions.local/functions/v1/get-document-url',{
    method:'POST',headers:{'Content-Type':'application/json','Content-Length':'2048'},
    body:JSON.stringify({document_id:DOCUMENT_ID})
  }));
  assert.equal(response.status,413);assert.equal(f.stats.signed,0);
});
test('JSON ou UTF-8 invalide: 400 sans lien privé',async()=>{
  for(const body of ['{"document_id":',new Uint8Array([0xc3,0x28])]){
    const f=fixture(),handler=buildHandler(f.service);
    const response=await handler(new Request('https://functions.local/functions/v1/get-document-url',{
      method:'POST',headers:{'Content-Type':'application/json'},body
    }));
    assert.equal(response.status,400);assert.equal(f.stats.signed,0);
    assert.deepEqual(f.calls,[]);
  }
});
test('Content-Type trompeur: 415 avant toute requête SQL',async()=>{
  for(const type of ['text/plain','application/json-invalid']){
    const f=fixture(),handler=buildHandler(f.service);
    const response=await handler(new Request('https://functions.local/functions/v1/get-document-url',{
      method:'POST',headers:{'Content-Type':type},
      body:JSON.stringify({document_id:DOCUMENT_ID})
    }));
    assert.equal(response.status,415);assert.equal(f.stats.signed,0);
  }
});
