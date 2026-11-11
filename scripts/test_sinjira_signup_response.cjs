'use strict';
// Exécute le VRAI module d'inscription avec DOM/Auth simulés : zéro réseau.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'..','assets/js/v24-signup.js'),'utf8');
const importRe=/^import\s+\{[^;\n]+\}\s+from\s+['"][^'"\n]+['"];?\s*$/gm;
assert.equal([...source.matchAll(importRe)].length,1,'Frontière import Auth modifiée');
const script=source.replace(importRe,'');
let n=0;
const eq=(got,want,why)=>{assert.equal(got,want,why);n++};
const yes=(got,why)=>{assert.ok(got,why);n++};
async function run(reply,{backend=true,questionnaire=false}={}){
  const call={signups:[],status:[],redirects:[],resets:0};
  const answers={
    display_name:'Utilisateur fictif',email:'test@example.invalid',
    password:'mot-de-passe-test-long-2026',
    password_confirm:'mot-de-passe-test-long-2026',
    birth_date:'1990-02-15',gender:'Homme',residence_country:'Canada',
    wants_character_questionnaire:questionnaire?'yes':'no',
    formspree_receipt_opt_in:'no',initial_contributor_opt_in:'no'
  };
  const events={},submit={disabled:true};
  const birth={value:answers.birth_date,addEventListener(){}};
  const guardian={value:'',setAttribute(){}},wrap={hidden:true};
  const controls={
    '[data-signup-birth-date]':birth,'[data-guardian-code-wrap]':wrap,
    '[data-guardian-code]':guardian,'[type="submit"]':submit
  };
  const form={
    querySelector(sel){return controls[sel]||null},
    addEventListener(k,cb){events[k]=cb},
    checkValidity(){return true},
    reportValidity(){throw Error('Unexpected invalid form')},
    setAttribute(){},
    reset(){call.resets++}
  };
  const status={},dom={
    '[data-signup-form]':form,'[data-account-status]':status,
    '[data-backend-state]':{}
  };
  const ctx={
    document:{querySelector(s){return dom[s]||null}},
    window:{SINJIRA_AUTH_ROUTE:{next:()=>'/compte/index.html'}},
    location:{assign(x){call.redirects.push(x)}},
    FormData:class{constructor(f){eq(f,form,'Valid form')}get(k){return answers[k]??null}},
    getSupabase(){return {auth:{async signUp(x){call.signups.push(x);return reply}}}},
    SINJIRA_CONFIG:{siteUrl:'https://www.benoitcantin.com'},
    isSinjiraBackendConfigured(){return backend},
    setStatus(target,message,kind){eq(target,status,'Status target');call.status.push({message,kind})},
    console:{warn(){}}
  };
  vm.runInNewContext(script,ctx,{filename:'v24-signup.js',timeout:2000});
  yes(typeof events.submit==='function','Real signup handler installed');
  let prevented=false;
  await events.submit({preventDefault(){prevented=true}});
  yes(prevented,'Native form submit prevented');
  return {call,submit};
}
async function main(){
  for(const reply of [
    {data:null,error:null},{data:{},error:null},
    {data:{user:null,session:null},error:null},
    {data:{user:{},session:null},error:null},
    {data:{user:{id:''},session:null},error:null},
    {data:{user:null,session:{access_token:'fake'}},error:null}
  ]){
    const x=await run(reply);
    eq(x.call.signups.length,1,'Auth called once');
    eq(x.call.resets,0,'Form retained on ambiguous signup result');
    eq(x.call.redirects.length,0,'No redirect without user');
    eq(x.call.status.at(-1)?.kind,'error','No false success');
    yes(x.call.status.at(-1)?.message.includes('n’a pas confirmé la création'),
      'Neutral message about uncertain account creation');
    eq(x.submit.disabled,false,'Can retry');
  }
  const created=await run({data:{user:{id:'00000000-0000-4000-8000-000000000001'},session:null},error:null});
  eq(created.call.status.at(-1)?.kind,'success','Acknowledged signup request is non-error');
  yes(created.call.status.at(-1)?.message.includes('Si elle peut être traitée'),
    'Signup request acknowledged without promising a created account');
  yes(!created.call.status.at(-1)?.message.includes('Compte créé'),
    'Supabase obfuscated user cannot trigger a false account-created claim');
  eq(created.call.resets,1,'Form cleared only when user acknowledged');
  eq(created.call.redirects.length,0,'No redirect before session');
  const immediate=await run({data:{user:{id:'00000000-0000-4000-8000-000000000001'},session:{access_token:'fake'}},error:null});
  eq(immediate.call.redirects[0],'/compte/index.html','User plus session redirects');
  const registry=await run({data:{user:{id:'00000000-0000-4000-8000-000000000001'},session:{access_token:'fake'}},error:null},{questionnaire:true});
  eq(registry.call.redirects[0],'/projets/sinjira/registre/','Intended registry redirect');
  const registryWithoutSession=await run({data:{user:{id:'00000000-0000-4000-8000-000000000001',identities:[]},session:null},error:null},{questionnaire:true});
  eq(registryWithoutSession.call.status.at(-1)?.kind,'success',
    'A potentially obfuscated user is not treated as an error by SDK');
  yes(registryWithoutSession.call.status.at(-1)?.message.includes('Si elle peut être traitée'),
    'Potentially obfuscated user receives neutral acknowledgement');
  yes(!registryWithoutSession.call.status.at(-1)?.message.includes('Compte créé'),
    'Registry request does not assert a nonexistent new account');
  eq(registryWithoutSession.call.redirects.length,0,
    'No navigation to protected registry without session');
  const apiError=await run({data:null,error:{message:'error-inert'}});
  eq(apiError.call.status.at(-1)?.kind,'error','Explicit error still fails');
  eq(apiError.call.resets,0,'Explicit error preserves form');
  const off=await run({data:null,error:null},{backend:false});
  eq(off.call.signups.length,0,'No API request when unavailable');
  eq(off.call.status.at(-1)?.kind,'error','Unavailable service explained');
  console.log('PASS inscription SINJIRA : '+n+' assertions sur le vrai module, sans réseau.');
}
main().catch(e=>{console.error(e);process.exitCode=1});
