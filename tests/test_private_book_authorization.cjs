'use strict';
// Contrat réel de get-private-book-url exécuté en VM, sans réseau ni secrets.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const code=fs.readFileSync(
  path.join(__dirname,'../supabase/functions/get-private-book-url/index.ts'),'utf8'
).replace(/^import[^\n]*\n/gm,'')
 .replace('function privateJson(data:unknown,status=200)','function privateJson(data,status=200)');
const ITEM='sinjira-livre-01-la-cendre-du-jugement';
function build(options={}){
  const counts={products:0,entitlements:0,rpcs:[],signed:0,errors:[]};
  const client={
    rpc:async(name,payload)=>{
      counts.rpcs.push(name);
      assert.equal(payload.p_user_id,'member');
      if(name==='is_sinjira_owner')
        return {data:options.owner||false,error:options.ownerError||null};
      if(name==='is_sinjira_admin')
        return {data:options.admin||false,error:options.adminError||null};
      throw Error('Unexpected RPC '+name);
    },
    from(table){
      const filters=[];
      const self={
        select(){return self;},
        eq(field,val){filters.push([field,val]);return self;},
        async maybeSingle(){
          if(table==='products'){
            counts.products++;
            assert.ok(filters.some(([k,v])=>k==='slug'&&v===ITEM));
            assert.ok(filters.some(([k,v])=>k==='active'&&v===true));
            return {data:options.active===false?null:{id:'product',slug:ITEM,active:true},
              error:options.productError||null};
          }
          if(table==='user_entitlements'){
            counts.entitlements++;
            assert.ok(filters.some(([k,v])=>k==='user_id'&&v==='member'));
            assert.ok(filters.some(([k,v])=>k==='product_id'&&v==='product'));
            return {data:options.entitlement?{product_id:'product'}:null,
              error:options.entitlementError||null};
          }
          throw Error('Unexpected table '+table);
        }
      };
      return self;
    },
    storage:{from(bucket){
      assert.equal(bucket,'private-book');
      return {async createSignedUrl(path,ttl,download){
        counts.signed++;
        assert.equal(path,'livre-01.pdf');
        assert.equal(ttl,300);
        assert.equal(download.download,'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf');
        return {data:{signedUrl:'https://private.example/signed'},error:null};
      }};
    }}
  };
  const env={
    Deno:{
      env:{get(name){
        const data={
          SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED:options.enabled===false?'false':'true',
          SINJIRA_LIVRE_I_PRIVATE_BUCKET:'private-book',
          SINJIRA_LIVRE_I_PRIVATE_PATH:'livre-01.pdf'
        };
        return data[name]||'';
      }},
      serve(callback){env.callback=callback;}
    },
    Response,Request,URL,console:{error(...args){counts.errors.push(args)}},
    corsHeaders:{'Access-Control-Allow-Origin':'https://www.benoitcantin.com'},
    requiredUser:async req=>{
      if(req.headers.get('Authorization')!=='Bearer member')throw Error('AUTH_REQUIRED');
      return {id:'member'};
    },
    serviceClient:()=>client
  };
  vm.runInNewContext(code,env,{filename:'get-private-book-url/index.ts'});
  assert.equal(typeof env.callback,'function');
  return {handler:env.callback,counts};
}
async function invoke(options={},auth='member'){
  const {handler,counts}=build(options);
  const result=await handler(new Request('https://functions.local/functions/v1/get-private-book-url',{
    method:'POST',headers:{Authorization:'Bearer '+auth}
  }));
  return {status:result.status,body:await result.json(),headers:result.headers,counts};
}
test('propriétaire RPC confirmé: livre signé sans licence artificielle',async()=>{
  const x=await invoke({owner:true,active:false});
  assert.equal(x.status,200);assert.equal(x.counts.signed,1);
  assert.equal(x.counts.products,0);assert.equal(x.counts.entitlements,0);
  assert.equal(x.body.expires_in,300);assert.equal(x.body.protected,true);
});
test('administrateur RPC confirmé: accès distinct de l achat',async()=>{
  const x=await invoke({admin:true});
  assert.equal(x.status,200);assert.equal(x.counts.signed,1);
  assert.equal(x.counts.entitlements,0);
});
test('licence membre avec produit actif: accès signé',async()=>{
  const x=await invoke({entitlement:true});
  assert.equal(x.status,200);assert.equal(x.counts.products,1);
  assert.equal(x.counts.entitlements,1);assert.equal(x.counts.signed,1);
});
test('membre gratuit ou produit inactif: refus sans URL signée',async()=>{
  for(const opts of [{},{active:false,entitlement:true}]){
    const x=await invoke(opts);
    assert.equal(x.counts.signed,0);
    assert.equal(x.status,opts.active===false?503:403);
  }
});
test('réponse RPC truthy non booléenne: aucun privilège',async()=>{
  const x=await invoke({owner:'false',admin:'false'});
  assert.equal(x.status,403);assert.equal(x.counts.signed,0);
});
test('panne de rôle ou entitlement: résultat indisponible, pas faux refus',async()=>{
  for(const opts of [
    {ownerError:{message:'private role error'}},
    {entitlementError:{message:'private entitlement error'}},
    {productError:{message:'private product error'}}
  ]){
    const x=await invoke(opts);
    assert.equal(x.status,503);assert.equal(x.counts.signed,0);
    assert.doesNotMatch(JSON.stringify(x.body),/private .* error/);
  }
});
test('la licence reste valide même si RPC propriétaire est temporairement indisponible',async()=>{
  const x=await invoke({entitlement:true,ownerError:{message:'offline'}});
  assert.equal(x.status,200);assert.equal(x.counts.signed,1);
});
test('fonction désactivée: refus même pour propriétaire',async()=>{
  const x=await invoke({owner:true,enabled:false});
  assert.equal(x.status,503);assert.equal(x.counts.signed,0);
  assert.equal(x.counts.rpcs.length,0);
});
test('anonyme: pas de révélation du stockage et aucun appel serveur',async()=>{
  const x=await invoke({owner:true},'anonymous');
  assert.equal(x.status,401);assert.equal(x.counts.signed,0);
  assert.equal(x.counts.rpcs.length,0);
});
test('réponses toujours no-store et sans détail sensible',async()=>{
  for(const opts of [{owner:true},{}]){
    const x=await invoke(opts);
    assert.equal(x.headers.get('cache-control'),'private, no-store, max-age=0');
    assert.equal(x.headers.get('x-content-type-options'),'nosniff');
    assert.equal(x.headers.get('referrer-policy'),'no-referrer');
  }
});
