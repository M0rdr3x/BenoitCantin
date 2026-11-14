'use strict';
/* Exécute les fonctions du vrai Centre de sécurité SINJIRA sans API, cookies ou utilisateurs. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

const js=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-security-center-v24-4-98.js'),'utf8');
assert.match(js,/^import .* from .*;\s*$/m);
assert.match(js,/\nboot\(\);\s*$/);
const script=js.replace(/^import .*;\s*$/gm,'').replace(/\nboot\(\);\s*$/,'')+
  '\nglobalThis.__tests={randomDeviceKey,validDeviceKey,deviceKey,safeSecurityId,renderDevices,renderTravel,renderChallenges,registerContext,friendlySecurityError};';

function memory(initial={}){
  const cache=new Map(Object.entries(initial));
  return {cache,getItem:key=>cache.get(key)??null,setItem:(key,value)=>cache.set(key,String(value))};
}
const KEY='sinjira.security.device_key.v1';
const deviceID='123e4567-e89b-12d3-a456-426614174000';
const otherID='23be4567-e89b-12d3-a456-426614174000';
const nodes={};
function put(selector){nodes[selector]={innerHTML:'',textContent:''};return nodes[selector]}
const sandbox={
  console,Date,Uint8Array,
  localStorage:memory(),sessionStorage:memory(),
  navigator:{userAgent:'Test navigateur',platform:'Test OS'},
  document:{querySelector:selector=>nodes[selector]||null,
    querySelectorAll:()=>[]},
  escapeHtml:value=>String(value??'').replace(/[&<>"']/g,
    ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])),
  formatDate:value=>String(value??''),
  getSupabase:()=>{throw Error('La CI ne doit jamais accéder à Supabase')},
  requireUser:()=>{throw Error('Boot interdit dans les tests')},
  setStatus:()=>{},
};
vm.runInNewContext(script,sandbox,{timeout:3000});
const api=sandbox.__tests;
let assertions=0;
function check(value){assert.ok(value);assertions++}
function equal(x,y){assert.equal(x,y);assertions++}
function throws(fn,code){assert.throws(fn,{message:code});assertions++}
function renderer(selector,fn,...args){const out=put(selector);fn(...args);return out.innerHTML}

// La génération échoue explicitement sans crypto.
delete sandbox.crypto;
throws(()=>api.randomDeviceKey(),'SECURE_RANDOM_REQUIRED');
throws(()=>api.deviceKey(),'SECURE_RANDOM_REQUIRED');
equal(api.friendlySecurityError(new Error('SECURE_RANDOM_REQUIRED')).includes('navigateur'),true);

// Un UUID crypto valide est permis.
sandbox.crypto={randomUUID:()=>deviceID};
equal(api.randomDeviceKey(),deviceID);
check(api.validDeviceKey(deviceID));
check(!api.validDeviceKey('00000000-0000-0000-0000-000000000000'));

// Fallback cryptographique : 192 bits aléatoires, sans horodatage en guise d'entropie.
sandbox.crypto={getRandomValues:buf=>{buf.fill(0);buf[0]=0xb4;buf[23]=0x8f;return buf}};
const generated=api.randomDeviceKey();
check(/^sinjira-[a-f0-9]{48}$/.test(generated));
check(api.validDeviceKey(generated));
check(!api.validDeviceKey('sinjira-'+'0'.repeat(48)+'-historic'));
check(!api.validDeviceKey('sinjira-'+'0'.repeat(48)));
check(!api.validDeviceKey('sinjira-'+('a'.repeat(129))));
sandbox.crypto={getRandomValues:()=>{}};
throws(()=>api.randomDeviceKey(),'SECURE_RANDOM_REQUIRED');

// Les identifiants historiques prévisibles sont renouvelés, pas réutilisés.
sandbox.crypto={randomUUID:()=>deviceID};
sandbox.localStorage=memory({[KEY]:'sinjira-'+'0'.repeat(48)+'-old'});
equal(api.deviceKey(),deviceID);
equal(sandbox.localStorage.cache.get(KEY),deviceID);
sandbox.crypto=undefined;
equal(api.deviceKey(),deviceID); // valeur forte déjà persistée

// SessionStorage est accepté seulement si LocalStorage ne marche pas.
sandbox.crypto={randomUUID:()=>otherID};
sandbox.localStorage={getItem:()=>{throw Error('blocked')},setItem:()=>{throw Error('blocked')}};
sandbox.sessionStorage=memory();
equal(api.deviceKey(),otherID);
equal(sandbox.sessionStorage.cache.get(KEY),otherID);
sandbox.sessionStorage={getItem:()=>{throw Error('blocked')},setItem:()=>{throw Error('blocked')}};
throws(()=>api.deviceKey(),'DEVICE_STORAGE_REQUIRED');
check(api.friendlySecurityError(new Error('DEVICE_STORAGE_REQUIRED')).includes('stockage'));

// Les identifiants qui deviennent attributs HTML doivent être des UUID stricts.
for(const bad of [
  'x" autofocus onfocus="alert(1)',
  '"><img src=x onerror=alert(1)>',
  'not-a-uuid', deviceID+'"><svg>',
  'javascript:alert(1)', null,undefined,1,'',
]){
  equal(api.safeSecurityId(bad),'');
}
equal(api.safeSecurityId(deviceID),deviceID);

const malicious='x" onmouseover="alert(1)';
const device={
  id:malicious,is_current:true,is_trusted:true,is_primary:false,revoked_at:null,
  display_name:'<img src=x onerror=alert(1)>',platform:'Test',device_type:'browser'
};
let html=renderer('[data-security-devices]',api.renderDevices,[device]);
check(!html.includes('data-device-trust='));
check(!html.includes('data-device-primary='));
check(!html.includes('data-device-untrust='));
check(!html.includes('data-device-revoke='));
check(!html.includes('data-device-id="'+malicious+'"'));
check(!html.includes('<img src=x onerror=alert(1)>'));
check(html.includes('&lt;img'));
device.id=deviceID;
html=renderer('[data-security-devices]',api.renderDevices,[device]);
check(html.includes('data-device-primary="'+deviceID+'"'));
check(html.includes('data-device-untrust="'+deviceID+'"'));

const travel={id:malicious,status:'active',destinations:['Québec'],starts_at:'',ends_at:''};
html=renderer('[data-security-travel-list]',api.renderTravel,[travel]);
check(!html.includes('data-travel-cancel='));
travel.id=deviceID;
html=renderer('[data-security-travel-list]',api.renderTravel,[travel]);
check(html.includes('data-travel-cancel="'+deviceID+'"'));

const pending={
  id:malicious,status:'pending',request_device_id:otherID,
  expires_at:'2099-01-01T00:00:00Z',
  display_code:'<svg/onload=alert(1)>'
};
const trusted={id:deviceID,is_current:true,is_trusted:true,revoked_at:null};
html=renderer('[data-security-challenges]',api.renderChallenges,[pending],[trusted]);
check(!html.includes('data-challenge-approve='));
check(!html.includes('data-challenge-deny='));
check(!html.includes('<svg'));
check(html.includes('&lt;svg'));
pending.id=otherID;
html=renderer('[data-security-challenges]',api.renderChallenges,[pending],[trusted]);
check(html.includes('data-challenge-approve="'+otherID+'"'));
check(html.includes('data-challenge-deny="'+otherID+'"'));
trusted.id=malicious;
html=renderer('[data-security-challenges]',api.renderChallenges,[pending],[trusted]);
check(!html.includes('data-challenge-approve='));

// Les erreurs de génération crypto sont interceptées par boot et affichées.
check(/async function boot\(\)\{\s*try\{\s*const meta=deviceMetadata\(\)/.test(js));
check(js.includes("if(Object.hasOwn(target.dataset,key)&&!safeSecurityId(target.dataset[key]))"));

// La fonction Edge de contexte ne peut jamais être réputée opérationnelle si
// sa réponse ne fournit pas explicitement ok=true et l'objet security.
check(js.includes("if(data?.ok!==true||!data?.security)throw new Error('SECURITY_CONTEXT_UNAVAILABLE')"));
check(js.includes("if(contextResult.context)status('Centre de sécurité prêt.','success')"));
check(js.includes("else status('Centre de sécurité chargé, mais la vérification contextuelle est indisponible."));

async function checkContextBehavior(){
  let edge={data:{ok:true,security:{outcome:'allow'}},error:null};
  let rpcCalls=0, edgeCalls=0;
  sandbox.getSupabase=()=>({
    rpc: async(name,args)=>{
      check(name==='security_register_device');
      check(typeof args.p_device_key==='string');
      rpcCalls++;
      return {data:{id:deviceID},error:null};
    },
    functions:{
      invoke:async(name,opts)=>{
        equal(name,'security-context');
        check(opts.body.action==='security_center');
        edgeCalls++;
        return edge;
      }
    }
  });
  const meta={device_key:deviceID,display_name:'Test',platform:'Test',device_type:'browser'};
  const healthy=await api.registerContext(meta);
  equal(healthy.context.security.outcome,'allow');
  edge={data:{ok:false,error:'blocked'},error:null};
  const rejected=await api.registerContext(meta);
  equal(rejected.context,null);
  edge={data:{ok:true},error:null};
  const missing=await api.registerContext(meta);
  equal(missing.context,null);
  edge={data:null,error:new Error('Edge unavailable')};
  const outage=await api.registerContext(meta);
  equal(outage.context,null);
  equal(rpcCalls,4);
  equal(edgeCalls,4);
}
checkContextBehavior().then(()=>{
  console.log('PASS: '+assertions+' assertions contre les clés prévisibles, les actions HTML et les états de sécurité dégradés.');
}).catch(error=>{console.error(error);process.exitCode=1;});
