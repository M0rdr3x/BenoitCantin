'use strict';
// Vérifie le VRAI module Registre sans requête réseau ni donnée personnelle.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const input=fs.readFileSync(path.join(__dirname,'..','assets/js/sinjira-character-registry.js'),'utf8');
const re=/^import\s+\{[^;\n]+\}\s+from\s+['"][^'"\n]+['"];?\s*$/gm;
assert.equal([...input.matchAll(re)].length,1,'Import du Registre attendu');
const program=input.replace(re,'')+'\nglobalThis.__setReady=()=>{registryReady=true;currentUser={id:"00000000-0000-4000-8000-000000000001",email:"essai@example.invalid"};};';
let assertions=0;
function eq(a,b,why){assert.equal(a,b,why);assertions++}
function yes(v,why){assert.ok(v,why);assertions++}
class MockFile {constructor(){this.size=300;this.type='image/png'}}
async function scenario(result,{uploadFails=false,aal='aal2',userState='same',rpcState='allowed'}={}){
  const photo=new MockFile();
  const calls={uploads:[],removes:[],invokes:[],clears:0,aalChecks:0,rpcChecks:0,redirects:[]};
  let sessionAvailable=false;
  const state={textContent:'',dataset:{},links:[],scrollIntoView(){},insertAdjacentElement(_,v){this.links.push(v)}};
  const button={disabled:false},events={};
  const form={
    addEventListener(t,callback){events[t]=callback},
    querySelector(q){
      if(q==='button[type="submit"]')return button;
      if(q==='input[type="file"][name="photo"]')return {files:[photo]};
      return null;
    },
    querySelectorAll(){return []},
    checkValidity(){return true},
    reportValidity(){throw Error('unexpected invalid form')}
  };
  const supabase={
    auth:{mfa:{async getAuthenticatorAssuranceLevel(){
      calls.aalChecks++;
      if(aal==='error')return {data:null,error:{message:'security state unavailable'}};
      return {data:{nextLevel:aal==='unenrolled'?'aal1':'aal2',currentLevel:aal==='aal2'?'aal2':'aal1'},error:null};
    }}},
    async rpc(name,params){
      eq(name,'security_sensitive_access_status','Sensitive Registry scope');
      eq(params.p_scope,'registry','Only Registry scope checked');
      calls.rpcChecks++;
      if(rpcState==='error')return {data:null,error:{message:'MFA state unavailable'}};
      return {data:rpcState==='allowed'?{allowed:true}:{allowed:false},error:null};
    },
    storage:{from(bucket){
      eq(bucket,'sinjira-character-sources','Private source bucket');
      return {async upload(key,chosen,opts){
        eq(chosen,photo,'Photo is from this submit');
        eq(opts.upsert,false,'No overwrite');
        calls.uploads.push(key);
        return {error:uploadFails?{message:'simulated failure'}:null};
      },async remove(keys){calls.removes.push(keys);return {error:null}}}
    }},
    functions:{async invoke(endpoint,request){
      eq(endpoint,'submit-character-questionnaire','Only expected Edge endpoint');
      yes(request.body.manual_only,'No generation');
      calls.invokes.push(request);
      return result;
    }}
  };
  const context={
    document:{
      querySelector(q){return ({
        '[data-character-form]':form,
        '[data-character-submit-status]':state,
        '[data-registry-login-actions]':{hidden:true}
      })[q]||null},
      createElement(t){eq(t,'a','Only a link to current dossier');return {dataset:{}}}
    },
    getSupabase:()=>supabase,
    getCurrentUser:async()=>{
      if(!sessionAvailable || userState==='expired')return null;
      return {id:userState==='different'?'00000000-0000-4000-8000-000000000099':'00000000-0000-4000-8000-000000000001',email:'essai@example.invalid'};
    },
    isSinjiraOwner:()=>false,
    FormData:class {
      constructor(element){eq(element,form,'Real Registry form')}
      *entries(){yield ['personality_notes','données entièrement fictives'];yield ['photo',photo]}
    },
    File:MockFile,
    crypto:{randomUUID:()=> '00000000-0000-4000-8000-000000000002'},
    localStorage:{removeItem(k){eq(k,'registre-consciences-draft-v1','Clear only on success');calls.clears++}},
    console:{warn(){},info(){}},
    location:{pathname:'/projets/sinjira/registre/',search:'',hash:'',replace(url){calls.redirects.push(url)}},
    CSS:{escape:v=>v},HTMLInputElement:class {},Event:class {}
  };
  vm.runInNewContext(program,context,{timeout:2500,filename:'sinjira-character-registry.js'});
  await Promise.resolve();await Promise.resolve();
  context.__setReady();
  sessionAvailable=true;
  eq(typeof events.submit,'function','Real submit handler');
  let prevented=false;
  await events.submit({preventDefault(){prevented=true}});
  yes(prevented,'No native HTML POST');
  return {calls,state,button,events};
}
async function main(){
  const duplicate=await scenario({data:null,error:{context:{status:409,async json(){
    return {code:'ONE_CHARACTER_PER_ACCOUNT'};
  }}}});
  eq(duplicate.calls.invokes.length,1,'409 only one invoke');
  eq(duplicate.calls.uploads.length,1,'409 photo uploaded before rejection');
  eq(duplicate.calls.removes.length,1,'Known rejection deletes only new orphan');
  eq(duplicate.button.disabled,true,'Known duplicate locks form');
  yes(duplicate.state.textContent.includes('possède déjà une demande'),'Explain duplicate');
  eq(duplicate.state.links[0]?.href,'/compte/mon-personnage.html','Provide existing dossier link');
  eq(duplicate.calls.clears,0,'Preserve draft on duplicate');
  await duplicate.events.submit({preventDefault(){}});
  eq(duplicate.calls.invokes.length,1,'Second submit remains blocked');

  const uncertain=[
    ['network',new Error('transport unavailable')],
    ['wrong409',{context:{status:409,async json(){return {code:'OTHER'}}}}],
    ['malformed409',{context:{status:409,async json(){throw Error('invalid json')}}}],
    ['http500',{context:{status:500,async json(){return {code:'ONE_CHARACTER_PER_ACCOUNT'}}}}]
  ];
  for(const [name,error] of uncertain){
    const x=await scenario({data:null,error});
    eq(x.calls.invokes.length,1,name+': single invoke');
    eq(x.calls.removes.length,0,name+': never delete photo on uncertain outcome');
    eq(x.button.disabled,true,name+': block potentially repeated POST');
    yes(x.state.textContent.includes('incertaine'),name+': explain uncertain status');
    eq(x.state.links[0]?.href,'/compte/mon-personnage.html',name+': verification link');
    eq(x.calls.clears,0,name+': preserve draft');
  }

  const good=await scenario({data:{
    ok:true,persisted:true,submission_id:'00000000-0000-4000-8000-000000000003',
    admin_notification_created:true
  },error:null});
  eq(good.calls.aalChecks,1,'AAL2 rechecked at actual submit time');
  eq(good.calls.rpcChecks,1,'Server-sensitive access rechecked before photo');
  eq(good.calls.invokes.length,1,'Saved exactly once');
  eq(good.calls.removes.length,0,'Never delete persisted photo');
  eq(good.calls.clears,1,'Clear draft only after persistence confirmed');
  eq(good.state.dataset.statusType,'success','Success label only after persistence');
  eq(good.button.disabled,true,'No repeat after success');

  const noPersistence=await scenario({data:{ok:true,persisted:false},error:null});
  eq(noPersistence.calls.removes.length,0,'No cleanup after inconclusive response');
  eq(noPersistence.button.disabled,true,'No duplicate when persistence is unknown');

  const noSession=await scenario({data:null,error:null},{userState:'expired'});
  eq(noSession.calls.uploads.length,0,'Expired session: never upload photo');
  eq(noSession.calls.invokes.length,0,'Expired session: never submit dossier');
  eq(noSession.calls.aalChecks,0,'Expired session: do not check MFA as another user');
  eq(noSession.button.disabled,true,'Expired session: form blocked');
  eq(noSession.calls.clears,0,'Expired session: draft preserved');

  const changedUser=await scenario({data:null,error:null},{userState:'different'});
  eq(changedUser.calls.uploads.length,0,'Changed account: no photo upload');
  eq(changedUser.calls.invokes.length,0,'Changed account: no Registry POST');
  eq(changedUser.button.disabled,true,'Changed account: form blocked');

  const downgraded=await scenario({data:null,error:null},{aal:'aal1'});
  eq(downgraded.calls.uploads.length,0,'AAL1 after page load: no photo upload');
  eq(downgraded.calls.invokes.length,0,'AAL1 after page load: no POST');
  eq(downgraded.button.disabled,true,'AAL1 after page load: form locked');
  yes(downgraded.calls.redirects[0]?.startsWith('/compte/mfa.html?next='),'AAL1: controlled MFA redirect');
  eq(downgraded.calls.clears,0,'AAL1: draft retained');

  const noFactor=await scenario({data:null,error:null},{aal:'unenrolled'});
  eq(noFactor.calls.uploads.length,0,'No TOTP factor: no photo upload');
  eq(noFactor.calls.invokes.length,0,'No TOTP factor: no POST');
  eq(noFactor.button.disabled,true,'No TOTP factor: form locked');

  const aalFailed=await scenario({data:null,error:null},{aal:'error'});
  eq(aalFailed.calls.uploads.length,0,'MFA unavailable: no photo upload');
  eq(aalFailed.calls.invokes.length,0,'MFA unavailable: no POST');
  eq(aalFailed.button.disabled,true,'MFA unavailable: form locked');

  const rpcFailed=await scenario({data:null,error:null},{rpcState:'error'});
  eq(rpcFailed.calls.aalChecks,1,'RPC outage: AAL2 was examined');
  eq(rpcFailed.calls.uploads.length,0,'RPC outage: no photo upload');
  eq(rpcFailed.calls.invokes.length,0,'RPC outage: no POST');
  eq(rpcFailed.button.disabled,true,'RPC outage: form locked');

  const rpcDenied=await scenario({data:null,error:null},{rpcState:'denied'});
  eq(rpcDenied.calls.uploads.length,0,'Sensitive access denied: no photo upload');
  eq(rpcDenied.calls.invokes.length,0,'Sensitive access denied: no POST');

  const uploadError=await scenario({data:null,error:null},{uploadFails:true});
  eq(uploadError.calls.invokes.length,0,'No Edge call when upload failed');
  eq(uploadError.button.disabled,false,'Retry safe before Edge invocation');
  eq(uploadError.calls.clears,0,'Never lose draft on upload failure');
  console.log('PASS Registre SINJIRA : '+assertions+' assertions, aucune donnée ni requête réelle');
}
main().catch(e=>{console.error(e);process.exitCode=1});
