import { getCurrentUser, getSupabase } from './sinjira-supabase.js';

const DEVICE_KEY='sinjira.security.device_key.v1';
const PUSH_TOKEN='sinjira.security.push_token.v1';
const PUSH_ENABLED='sinjira.security.push_enabled.v1';
const PUSH_PLATFORM='sinjira.security.push_platform.v1';

async function syncPushEndpoint(){
  try{
    const user=await getCurrentUser();
    if(!user)return;
    const deviceKey=localStorage.getItem(DEVICE_KEY)||'';
    if(deviceKey.length<16)return;
    const enabled=localStorage.getItem(PUSH_ENABLED);
    const token=localStorage.getItem(PUSH_TOKEN)||'';
    if(enabled==='1'&&token.length>=20){
      const {error}=await getSupabase().rpc('security_register_push_endpoint',{
        p_device_key:deviceKey,p_expo_push_token:token,p_platform:(localStorage.getItem(PUSH_PLATFORM)||'').slice(0,40)
      });
      if(error)throw error;
    }else if(enabled==='0'){
      const {error}=await getSupabase().rpc('security_disable_push_for_device',{p_device_key:deviceKey});
      if(error)throw error;
    }
  }catch(error){
    console.warn('[SINJIRA push bridge]',error?.message||error);
  }
}

window.addEventListener('sinjira:push-changed',()=>void syncPushEndpoint());
void syncPushEndpoint();
