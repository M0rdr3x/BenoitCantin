import {getSupabase} from './sinjira-supabase.js';
import {
  normalizeLiveShareCode,
  normalizeLiveShareCodeCreate,
  normalizeLiveShareCodeRedeem,
  normalizeLiveShareCodes
} from './sinjira-live-share-codes-model-v25.js';

const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function requiredUuid(value,code){
  const id=String(value||'').trim().toLowerCase();
  if(!UUID_RE.test(id))throw new Error(code);
  return id;
}

export async function createLiveShareCode(roomId,{supabase=getSupabase()}={}){
  const id=requiredUuid(roomId,'SOCIAL_LIVE_ROOM_ID_INVALID');
  const {data,error}=await supabase.rpc('social_live_share_code_create',{p_room_id:id});
  if(error)throw error;
  const normalized=normalizeLiveShareCodeCreate(data);
  if(!normalized)throw new Error('SOCIAL_LIVE_SHARE_CODE_RESPONSE_INVALID');
  return normalized;
}

export async function listLiveShareCodes({roomId=null,limit=20,supabase=getSupabase()}={}){
  const id=roomId===null||roomId===undefined||roomId===''?null:requiredUuid(roomId,'SOCIAL_LIVE_ROOM_ID_INVALID');
  const capped=Math.max(1,Math.min(Number(limit)||20,50));
  const {data,error}=await supabase.rpc('social_live_share_code_list',{
    p_room_id:id,
    p_limit:capped
  });
  if(error)throw error;
  return normalizeLiveShareCodes(data);
}

export async function revokeLiveShareCode(codeId,{supabase=getSupabase()}={}){
  const id=requiredUuid(codeId,'SOCIAL_LIVE_SHARE_CODE_ID_INVALID');
  const {data,error}=await supabase.rpc('social_live_share_code_revoke',{p_code_id:id});
  if(error)throw error;
  return data===true;
}

export async function redeemLiveShareCode(value,{supabase=getSupabase()}={}){
  const code=normalizeLiveShareCode(value);
  if(!code)throw new Error('SOCIAL_LIVE_SHARE_CODE_UNAVAILABLE');
  const {data,error}=await supabase.rpc('social_live_share_code_redeem',{p_code:code});
  if(error)throw error;
  const normalized=normalizeLiveShareCodeRedeem(data);
  if(!normalized)throw new Error('SOCIAL_LIVE_SHARE_CODE_RESPONSE_INVALID');
  return normalized;
}
