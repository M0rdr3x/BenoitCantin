const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function normalizeUuid(value){
  const normalized=String(value||'').trim().toLowerCase();
  return UUID_RE.test(normalized)?normalized:'';
}

export function normalizeCommunityLiveInviteContext({viewerUserId,targetUserId,targetLabel='Membre SINJIRA™'}={}){
  const viewerId=normalizeUuid(viewerUserId);
  const targetId=normalizeUuid(targetUserId);
  if(!viewerId||!targetId)throw new Error('SOCIAL_LIVE_COMMUNITY_CONTEXT_UNAVAILABLE');
  if(viewerId===targetId)throw new Error('SOCIAL_LIVE_COMMUNITY_SELF_INVITE_FORBIDDEN');
  const label=String(targetLabel||'')
    .replace(/\s+/g,' ')
    .trim()
    .slice(0,80)||'Membre SINJIRA™';
  return Object.freeze({targetUserId:targetId,targetLabel:label});
}

export async function mountCommunityLiveInvite(root,context,{supabase,onSent=()=>{}}={}){
  if(!(root instanceof Element))throw new Error('SOCIAL_LIVE_COMMUNITY_ROOT_REQUIRED');
  const safeContext=normalizeCommunityLiveInviteContext(context);
  const {createLiveInviteTargetUi}=await import('./sinjira-live-invites-ui-v25.js');
  const options={
    targetUserId:safeContext.targetUserId,
    targetLabel:safeContext.targetLabel,
    onSent
  };
  if(supabase)options.supabase=supabase;
  return createLiveInviteTargetUi(root,options);
}
