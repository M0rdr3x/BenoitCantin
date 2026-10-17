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
  let transformed=source.replace(/^import[^\n]*\n/gm,'')
    .replace('const ranks:Record<string,number>','const ranks')
    .replace('const chunks:Uint8Array[]=[];','const chunks=[];')
    .replace('function privateJson(data:unknown,status=200)','function privateJson(data,status=200)')
    .replace('function externalUrlAllowed(value:string)','function externalUrlAllowed(value)')
    .replace('async function readLimitedJson(req:Request):Promise<{body?:any;response?:Response}>',
      'async function readLimitedJson(req)');
  assert.doesNotMatch(transformed,/\bimport\s+.*from/);
  let handler;
  const context={
    Response,Request,TextEncoder,TextDecoder,URL,console,
    corsHeaders:{'Access-Control-Allow-Origin':'*'},
    optionalUser:async(req)=>req.headers.get('Authorization')==='Bearer anonymous'
      ?null:{id:'test-member'},
    serviceClient:()=>mock,
    Deno:{serve(callback){handler=callback}}
  };
  vm.runInNewContext(transformed,context,{filename:'get-document-url/index.ts'});
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
