const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SLUG_RE=/^[a-z0-9][a-z0-9-]{2,47}$/;

function safeUuid(value){
  const id=String(value||'').trim().toLowerCase();
  return UUID_RE.test(id)?id:null;
}

function safeText(value,max){
  return String(value||'').trim().slice(0,max);
}

export function normalizeLiveInviteCreate(payload){
  const raw=payload&&typeof payload==='object'?payload:{};
  const inviteId=safeUuid(raw.invite_id);
  const roomId=safeUuid(raw.room_id);
  const expiresAt=safeText(raw.expires_at,64);
  if(raw.ok!==true||!inviteId||!roomId||!expiresAt)return null;
  return {inviteId,roomId,expiresAt};
}

export function normalizeLiveInvites(payload){
  if(!payload||typeof payload!=='object'||payload.ok!==true)return [];
  const raw=Array.isArray(payload.invites)?payload.invites:[];
  const seen=new Set();
  const invites=[];
  for(const row of raw){
    const inviteId=safeUuid(row?.invite_id);
    const roomId=safeUuid(row?.room_id);
    const roomSlug=safeText(row?.room_slug,48).toLowerCase();
    const roomName=safeText(row?.room_name,80);
    const inviterLabel=safeText(row?.inviter_label,80)||'Membre SINJIRA™';
    const createdAt=safeText(row?.created_at,64);
    const expiresAt=safeText(row?.expires_at,64);
    if(!inviteId||!roomId||!SLUG_RE.test(roomSlug)||!roomName||!createdAt||!expiresAt||seen.has(inviteId))continue;
    seen.add(inviteId);
    invites.push({inviteId,roomId,roomSlug,roomName,inviterLabel,createdAt,expiresAt});
    if(invites.length>=50)break;
  }
  return invites;
}

export function normalizeLiveInviteResponse(payload){
  const raw=payload&&typeof payload==='object'?payload:{};
  const status=String(raw.status||'').toLowerCase();
  if(status==='accepted'&&raw.ok===true){
    const roomId=safeUuid(raw.room_id);
    return roomId?{status:'accepted',roomId}:null;
  }
  if(status==='declined'&&raw.ok===true)return {status:'declined'};
  if(status==='expired'&&raw.ok===false)return {status:'expired'};
  if(status==='unavailable'&&raw.ok===false)return {status:'unavailable'};
  return null;
}
