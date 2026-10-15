'use strict';
// Exécution isolée de la vraie Edge Function get-novel-file-url sans Supabase réel.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

const source=fs.readFileSync(path.join(__dirname,
  '../supabase/functions/get-novel-file-url/index.ts'),'utf8');
const SLUG='sinjira-livre-01-la-cendre-du-jugement';
const novel={id:'novel-01',slug:SLUG,title:'La Cendre du Jugement',
  status:'published',product_id:'product-01',file_ready:true,
  private_storage_bucket:'private-books',private_storage_path:'novel-01.pdf',
  page_count:400,file_version:'1',file_sha256:'testhash',file_size_bytes:12345};

function fixture(options={}){
  const state={signed:0,entitlementLookups:0,productLookups:0,queries:[],roles:[],errors:[]};
  const service={
    from(table){
      const filters=[];
      const chain={
        select(){return chain;},
        eq(key,value){filters.push([key,value]);return chain;},
        async maybeSingle(){
          state.queries.push({table,filters});
          if(table==='sinjira_novels'){
            assert.deepEqual(filters,[['slug',options.slugLookup||SLUG]]);
            return {data:options.novel===undefined?novel:options.novel,error:options.novelError||null};
          }
          if(table==='user_entitlements'){
            state.entitlementLookups++;
            assert.ok(filters.some(([k,v])=>k==='user_id'&&v==='member-01'));
            assert.ok(filters.some(([k,v])=>k==='product_id'&&v==='product-01'));
            return {data:options.entitlement?{product_id:'product-01'}:null,
              error:options.entitlementError||null};
          }
          if(table==='products'){
            state.productLookups++;
            return {data:options.productActive===false?{active:false}:{active:true},
              error:options.productError||null};
          }
          throw Error('Unexpected table '+table);
        }
      };
      return chain;
    },
    async rpc(name,params){
      state.roles.push(name);
      assert.equal(params.p_user_id,'member-01');
      if(name==='is_sinjira_owner')
        return {data:options.owner===undefined?false:options.owner,
          error:options.ownerError||null};
      if(name==='is_sinjira_admin')
        return {data:options.admin===undefined?false:options.admin,
          error:options.adminError||null};
      throw Error('Unexpected role RPC '+name);
    },
    storage:{from(bucket){
      assert.equal(bucket,'private-books');
      return {async createSignedUrl(filename,ttl,settings){
        assert.equal(filename,'novel-01.pdf');
        assert.equal(ttl,600);
        assert.equal(settings.download,SLUG+'.pdf');
        state.signed++;
        return {data:{signedUrl:'https://private.example/signed'},
          error:null};
      }};
    }}
  };
  const stripped=source.replace(/^import[^\n]*\n/gm,'')
    .replace('function json(data:unknown,status=200)','function json(data,status=200)')
    .replace('const chunks:Uint8Array[]=[];','const chunks=[];');
  let handler;
  const environment={
    Deno:{serve(fn){handler=fn}},
    Response,Request,TextDecoder,Uint8Array,Number,URL,console:{
      error(...args){state.errors.push(args)}
    },
    corsHeaders:{'Access-Control-Allow-Origin':'https://www.benoitcantin.com'},
    requiredUser:async(req)=>{
      if(req.headers.get('Authorization')!=='Bearer member')
        throw new Error('AUTH_REQUIRED');
      return {id:'member-01'};
    },
    serviceClient:()=>service
  };
  vm.runInNewContext(stripped,environment,{filename:'get-novel-file-url/index.ts'});
  assert.equal(typeof handler,'function');
  return {handler,state};
}

async function invoke(options={},request={}){
  const f=fixture(options);
  const body=request.body===undefined?JSON.stringify({slug:SLUG}):request.body;
  const req=new Request('https://functions.local/functions/v1/get-novel-file-url',{
    method:'POST',headers:{
      Authorization:'Bearer '+(request.bearer||'member'),
      'Content-Type':request.mime||'application/json'
    },body
  });
  const response=await f.handler(req);
  return {status:response.status,body:await response.json(),
    headers:response.headers,...f};
}

test('propriétaire confirmé : téléchargement autorisé sans licence fictive',async()=>{
  const x=await invoke({owner:true});
  assert.equal(x.status,200);assert.equal(x.state.signed,1);
  assert.equal(x.state.entitlementLookups,0);
  assert.equal(x.body.protected,true);
  assert.equal(x.body.expires_in,600);
});

test('administrateur confirmé : téléchargement sans licence attribuée',async()=>{
  const x=await invoke({admin:true});
  assert.equal(x.status,200);assert.equal(x.state.signed,1);
  assert.equal(x.state.entitlementLookups,0);
});

test('membre possédant le produit actif : téléchargement autorisé',async()=>{
  const x=await invoke({entitlement:true});
  assert.equal(x.status,200);assert.equal(x.state.signed,1);
  assert.equal(x.state.productLookups,1);
});

test('absence de droit ou produit inactif : refus sans signature',async()=>{
  for(const options of [{},{entitlement:true,productActive:false}]){
    const x=await invoke(options);
    assert.equal(x.status,403);assert.equal(x.state.signed,0);
  }
});

test('état du rôle ou de la licence indisponible : 503, jamais zéro droit',async()=>{
  for(const options of [
    {ownerError:{message:'private owner error'}},
    {entitlementError:{message:'private entitlement error'}},
    {entitlement:true,productError:{message:'private product error'}}
  ]){
    const x=await invoke(options);
    assert.equal(x.status,503);assert.equal(x.state.signed,0);
    assert.doesNotMatch(JSON.stringify(x.body),/private/);
  }
});

test('licence vérifiée malgré panne RPC propriétaire : droit réel conservé',async()=>{
  const x=await invoke({ownerError:{message:'offline'},entitlement:true});
  assert.equal(x.status,200);assert.equal(x.state.signed,1);
});

test('rôle renvoyé comme chaîne truthy : jamais propriétaire',async()=>{
  const x=await invoke({owner:'false',admin:'false'});
  assert.equal(x.status,403);assert.equal(x.state.signed,0);
});

test('roman non publié ou fichier non prêt : aucune URL signée',async()=>{
  const draft=await invoke({owner:true,novel:{...novel,status:'draft'}});
  assert.equal(draft.status,404);assert.equal(draft.state.signed,0);
  const pending=await invoke({owner:true,novel:{...novel,file_ready:false}});
  assert.equal(pending.status,409);assert.equal(pending.state.signed,0);
  assert.equal(pending.body.code,'FILE_NOT_READY');
});

test('anonyme : 401 et aucune consultation Supabase',async()=>{
  const x=await invoke({}, {bearer:'anonymous'});
  assert.equal(x.status,401);assert.equal(x.state.signed,0);
  assert.equal(x.state.queries.length,0);
});

test('JSON volumineux, syntaxe et UTF-8 malformés : rejet avant SQL',async()=>{
  const data=[
    [JSON.stringify({slug:SLUG,padding:'x'.repeat(2400)}),413],
    ['{"slug":',400],
    [new Uint8Array([0xc3,0x28]),400]
  ];
  for(const [body,status] of data){
    const x=await invoke({}, {body});
    assert.equal(x.status,status);assert.equal(x.state.queries.length,0);
    assert.equal(x.headers.get('cache-control'),'private, no-store, max-age=0');
  }
});

test('paramètre slug de type inattendu ou chemin invalide : 400',async()=>{
  for(const input of [42,{toString:'dangerous'},'../admin','']){
    const x=await invoke({}, {body:JSON.stringify({slug:input})});
    assert.equal(x.status,400);assert.equal(x.state.queries.length,0);
  }
});

test('mauvais Content-Type : refus 415 sans requête privée',async()=>{
  for(const mime of ['text/plain','application/json-invalide']){
    const x=await invoke({}, {mime});
    assert.equal(x.status,415);assert.equal(x.state.queries.length,0);
  }
});

test('erreur serveur inattendue : code fixe, sans journaliser les secrets',async()=>{
  const x=await invoke({novelError:{message:'sensitive SQL detail'}});
  // L'erreur applicative de lookup est volontairement regroupée en 404.
  assert.equal(x.status,404);assert.equal(x.state.signed,0);
  assert.doesNotMatch(JSON.stringify(x.state.errors),/sensitive/);
});
