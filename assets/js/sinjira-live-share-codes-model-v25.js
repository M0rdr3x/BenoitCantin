const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SLUG_RE=/^[a-z0-9][a-z0-9-]{2,47}$/;
const SHARE_CODE_RE=/^[a-f0-9]{64}$/;
const CODE_STATUSES=new Set(['active','used','revoked','expired']);

function safeUuid(value){
  const id=String(value||'').trim().toLowerCase();
  return UUID_RE.test(id)?id:null;
}

export function normalizeLiveShareCode(value){
  const code=String(value||'').trim().toLowerCase();
  return SHARE_CODE_RE.test(code)?code:null;
}

export function normalizeLiveShareCodeCreate(payload){
  const raw=payload&&typeof payload==='object'?payload:{};
  const codeId=safeUuid(raw.code_id);
  const code=normalizeLiveShareCode(raw.code);
  if(!codeId||!code||raw.display_once!==true)return null;
  return {
    codeId,
    code,
    displayOnce:true,
    expiresAt:String(raw.expires_at||'')
  };
}

export function normalizeLiveShareCodes(payload){
  const raw=Array.isArray(payload?.codes)?payload.codes:[];
  const seen=new Set();
  const codes=[];
  for(const row of raw){
    const codeId=safeUuid(row?.code_id);
    const roomId=safeUuid(row?.room_id);
    const roomSlug=String(row?.room_slug||'').trim().toLowerCase();
    const roomName=String(row?.room_name||'').trim().slice(0,80);
    const status=CODE_STATUSES.has(String(row?.status||'').toLowerCase())?String(row.status).toLowerCase():'expired';
    if(!codeId||!roomId||!SLUG_RE.test(roomSlug)||!roomName||seen.has(codeId))continue;
    seen.add(codeId);
    codes.push({
      codeId,
      roomId,
      roomSlug,
      roomName,
      status,
      createdAt:String(row?.created_at||''),
      expiresAt:String(row?.expires_at||''),
      closedAt:String(row?.closed_at||'')
    });
    if(codes.length>=50)break;
  }
  return codes;
}

export function normalizeLiveShareCodeRedeem(payload){
  const raw=payload&&typeof payload==='object'?payload:{};
  const roomId=safeUuid(raw.room_id);
  const roomSlug=String(raw.room_slug||'').trim().toLowerCase();
  const status=raw.status==='already_member'?'already_member':raw.status==='joined'?'joined':null;
  if(!roomId||!SLUG_RE.test(roomSlug)||!status)return null;
  return {roomId,roomSlug,status};
}
