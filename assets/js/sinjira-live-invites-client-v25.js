import {getSupabase} from './sinjira-supabase.js';
import {
  normalizeLiveInviteCreate,
  normalizeLiveInviteResponse,
  normalizeLiveInvites
} from './sinjira-live-invites-model-v25.js';

const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function requiredUuid(value,code){
  const id=String(value||'').trim().toLowerCase();
  if(!UUID_RE.test(id))throw new Error(code);
  return id;
}

export async function createLiveInvite(roomId,inviteeUserId,{supabase=getSupabase()}={}){
  const room=requiredUuid(roomId,'SOCIAL_LIVE_ROOM_ID_INVALID');
  const invitee=requiredUuid(inviteeUserId,'SOCIAL_LIVE_INVITEE_ID_INVALID');
  const {data,error}=await supabase.rpc('social_live_invite_create',{
    p_room_id:room,
    p_invitee_user_id:invitee
  });
  if(error)throw error;
  const normalized=normalizeLiveInviteCreate(data);
  if(!normalized)throw new Error('SOCIAL_LIVE_INVITE_RESPONSE_INVALID');
  return normalized;
}

export async function listMyLiveInvites({limit=20,supabase=getSupabase()}={}){
  const capped=Math.max(1,Math.min(Number(limit)||20,50));
  const {data,error}=await supabase.rpc('social_live_my_invites',{p_limit:capped});
  if(error)throw error;
  return normalizeLiveInvites(data);
}

export async function respondToLiveInvite(inviteId,accept,{supabase=getSupabase()}={}){
  const id=requiredUuid(inviteId,'SOCIAL_LIVE_INVITE_ID_INVALID');
  if(typeof accept!=='boolean')throw new Error('SOCIAL_LIVE_INVITE_DECISION_INVALID');
  const {data,error}=await supabase.rpc('social_live_invite_respond',{
    p_invite_id:id,
    p_accept:accept
  });
  if(error)throw error;
  const normalized=normalizeLiveInviteResponse(data);
  if(!normalized)throw new Error('SOCIAL_LIVE_INVITE_RESPONSE_INVALID');
  return normalized;
}

export async function revokeLiveInvite(inviteId,{supabase=getSupabase()}={}){
  const id=requiredUuid(inviteId,'SOCIAL_LIVE_INVITE_ID_INVALID');
  const {data,error}=await supabase.rpc('social_live_invite_revoke',{p_invite_id:id});
  if(error)throw error;
  return data===true;
}
