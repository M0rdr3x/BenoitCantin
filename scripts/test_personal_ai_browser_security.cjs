'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-personal-ai-v25.js'),'utf8');
const start=source.indexOf('const DEVICE_KEY_STORAGE=');
const end=source.indexOf('\ninit().catch(');
assert.ok(start>=0&&end>start);
const code=source.slice(start,end)+'\nglobalThis.gates={validSuccess,invokePersonalAi,clearWorkspace,randomDeviceKey,loadState,openWorkspace,getState:()=>state};';
const settings={enabled:true,display_name:'Synthetic',language_code:'fr-CA',runtime_status:'not_configured'};
const runtime={conversation_enabled:false,memory_enabled:false,source_retrieval_enabled:false,provider_configured:false};
const risk={risk_model_version:'v25.0',mandatory_step_up:true,requires_step_up:true,outcome:'allow',risk_score:20};
const good={ok:true,security:risk,state:{settings,runtime,source_permissions:[{source_type:'life_story',granted:true}]}};
function harness(){
  let response={data:good,error:null};
  const field={enabled:{checked:false},ai_display_name:{value:''},language_code:{value:''}};
  const form={reset(){field.ai_display_name.value='';},elements:{namedItem:key=>field[key]}};
  const workspace={hidden:true},checkbox={checked:false,dataset:{personalAiSource:'life_story'}},statusNode={};
  const sandbox={document:{querySelector:s=>s==='[data-personal-ai-settings-form]'?form:s==='[data-personal-ai-status]'?statusNode:null,
    querySelectorAll:s=>s==='[data-personal-ai-workspace]'?[workspace]:s==='[data-personal-ai-source]'?[checkbox]:[]},
    localStorage:{getItem:()=> 'synthetic-device-key-0001'},navigator:{},setStatus:(node,msg)=>node.message=msg,
    getSupabase:()=>({functions:{invoke:async()=>response}})};
  vm.runInNewContext(code,sandbox,{timeout:1000});
  return {g:sandbox.gates,set:r=>response=r,workspace,checkbox,field,statusNode};
}
async function main(){
  const h=harness(),g=h.g,body={action:'get_state'};
  assert.equal(g.validSuccess(good,body),true);
  const bad=[{...good,ok:'true'},{...good,security:null},{...good,security:{...risk,risk_score:'20'}},
    {...good,security:{...risk,risk_score:75}},{...good,security:{...risk,outcome:'challenge'}},
    {...good,security:{...risk,mandatory_step_up:false}},{...good,state:null},
    {...good,state:{...good.state,runtime:{...runtime,memory_enabled:true}}},
    {...good,state:{...good.state,source_permissions:[{source_type:'conscience',granted:true}]}},
    {...good,state:{...good.state,source_permissions:[{source_type:'life_story',granted:true},{source_type:'life_story',granted:false}]}}];
  for(const data of bad)assert.equal(g.validSuccess(data,body),false);
  for(const error of [undefined,false,0,'']){h.set({data:good,error});await assert.rejects(g.invokePersonalAi(body));}
  assert.equal(g.validSuccess({ok:true,security:risk,deleted:'true'},{action:'delete_personal_ai_data'}),false);
  assert.equal(g.validSuccess({ok:true,security:risk,settings},{action:'update_settings',enabled:false}),false);
  assert.equal(g.validSuccess({ok:true,security:risk,source_type:'life_story',granted:false,runtime_access_enabled:false},{action:'set_source_permission',source_type:'life_story',granted:true}),false);
  assert.throws(()=>g.randomDeviceKey(),/SECURITY_STATE_UNAVAILABLE/);
  h.set({data:good,error:null});await g.openWorkspace();
  assert.equal(h.workspace.hidden,false);assert.equal(h.checkbox.checked,true);assert.equal(h.field.ai_display_name.value,'Synthetic');
  h.set({data:{ok:false,code:'AUTH_REQUIRED'},error:null});await g.openWorkspace();
  assert.equal(h.workspace.hidden,true);assert.equal(h.checkbox.checked,false);assert.equal(h.field.ai_display_name.value,'');assert.equal(g.getState(),null);
  console.log('PASS: Mon IA browser strict success, secure entropy, private workspace cleared on refusal.');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
