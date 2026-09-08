const LIVE_SLUG_RE=/^[a-z0-9][a-z0-9-]{2,47}$/;
const ROOM_UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function normalizeLiveRoomId(value){
  const id=String(value||'').trim().toLowerCase();
  if(!ROOM_UUID_RE.test(id))throw new Error('SOCIAL_LIVE_ROOM_ID_INVALID');
  return id;
}

export function liveTopic(roomId){
  return `sinjira-live:${normalizeLiveRoomId(roomId)}`;
}

export function parseLiveInput(value){
  const raw=String(value||'').trim();
  if(!raw)return {kind:'empty'};
  if(!raw.startsWith('/'))return {kind:'message',body:raw};

  const match=raw.match(/^\/([a-z]+)(?:\s+(.+))?$/i);
  if(!match)return {kind:'error',code:'LIVE_COMMAND_INVALID'};
  const command=match[1].toLowerCase();
  const args=String(match[2]||'').trim();

  if(command==='join'){
    const slug=args.toLowerCase();
    if(!LIVE_SLUG_RE.test(slug))return {kind:'error',code:'LIVE_COMMAND_JOIN_USAGE'};
    return {kind:'join',slug};
  }
  if(command==='rooms'){
    if(args)return {kind:'error',code:'LIVE_COMMAND_ROOMS_USAGE'};
    return {kind:'rooms'};
  }
  if(command==='me'){
    if(args)return {kind:'error',code:'LIVE_COMMAND_ME_USAGE'};
    return {kind:'me'};
  }
  return {kind:'error',code:'LIVE_COMMAND_UNKNOWN',command};
}

export function liveCommandRpcSpec(parsed){
  switch(parsed?.kind){
    case 'join':
      return {rpc:'social_live_join_public_room',args:{p_slug:parsed.slug}};
    case 'rooms':
      return {rpc:'social_live_list_rooms',args:{p_limit:50}};
    case 'me':
      return {rpc:'social_live_me',args:{}};
    default:
      return null;
  }
}
