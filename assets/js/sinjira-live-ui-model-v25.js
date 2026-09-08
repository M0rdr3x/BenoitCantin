const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SLUG_RE=/^[a-z0-9][a-z0-9-]{2,47}$/;

function boundedInt(value,max=9999){
  const n=Number(value);
  if(!Number.isFinite(n)||n<0)return 0;
  return Math.min(Math.trunc(n),max);
}

export function normalizeLiveMe(payload){
  const raw=payload&&typeof payload==='object'?payload:{};
  const label=String(raw.profile_label||'Membre SINJIRA').trim().slice(0,120)||'Membre SINJIRA';
  return {
    profileLabel:label,
    ownedRooms:boundedInt(raw.owned_rooms),
    joinedRooms:boundedInt(raw.joined_rooms)
  };
}

export function normalizeLiveRooms(payload){
  const raw=Array.isArray(payload?.rooms)?payload.rooms:[];
  const seen=new Set();
  const rooms=[];
  for(const row of raw){
    const roomId=String(row?.room_id||'').trim().toLowerCase();
    const slug=String(row?.slug||'').trim().toLowerCase();
    const name=String(row?.name||'').trim().slice(0,80);
    const visibility=row?.visibility==='private'?'private':'public';
    if(!UUID_RE.test(roomId)||!SLUG_RE.test(slug)||!name||seen.has(roomId))continue;
    seen.add(roomId);
    rooms.push({
      roomId,
      slug,
      name,
      description:String(row?.description||'').trim().slice(0,500),
      visibility,
      owned:row?.owned===true,
      joined:row?.joined===true
    });
    if(rooms.length>=100)break;
  }
  return rooms;
}

export function livePresenceLabel(value){
  const count=boundedInt(value,999);
  if(count===0)return 'Personne en ligne dans ce salon';
  if(count===1)return '1 présence active';
  return `${count} présences actives`;
}

export function liveRoomAccessLabel(room){
  if(!room)return 'Aucun salon sélectionné';
  if(room.visibility==='private')return room.joined?'Salon privé · membre':'Salon privé · invitation requise';
  if(room.owned)return 'Salon public · vous êtes propriétaire';
  if(room.joined)return 'Salon public · rejoint';
  return 'Salon public · rejoindre pour écrire';
}

export function liveCommandHelp(){
  return '/join <salon> · /rooms · /me';
}

export function liveUiErrorMessage(error){
  const raw=String(error?.message||error||'').toUpperCase();
  if(raw.includes('LIVE_COMMAND_JOIN_USAGE'))return 'Utilisez /join suivi du nom court du salon.';
  if(raw.includes('LIVE_COMMAND_ROOMS_USAGE'))return 'La commande /rooms ne prend aucun argument.';
  if(raw.includes('LIVE_COMMAND_ME_USAGE'))return 'La commande /me ne prend aucun argument.';
  if(raw.includes('LIVE_COMMAND_UNKNOWN'))return 'Commande inconnue. Commandes disponibles : /join, /rooms et /me.';
  if(raw.includes('SOCIAL_LIVE_ROOM_REQUIRED'))return 'Choisissez d’abord un salon.';
  if(raw.includes('SOCIAL_LIVE_ROOM_UNAVAILABLE'))return 'Ce salon n’est pas disponible depuis votre compte.';
  if(raw.includes('SOCIAL_LIVE_JOIN_RATE_LIMIT'))return 'Trop de salons ont été rejoints récemment. Réessayez plus tard.';
  if(raw.includes('SOCIAL_LIVE_RATE_LIMIT'))return 'Vous envoyez des messages trop rapidement. Réessayez dans quelques instants.';
  if(raw.includes('SOCIAL_LIVE_DUPLICATE_MESSAGE'))return 'Ce message vient déjà d’être envoyé.';
  if(raw.includes('SOCIAL_LIVE_MEMBERSHIP_REQUIRED'))return 'Vous devez être membre du salon pour écrire.';
  if(raw.includes('SOCIAL_LIVE_REALTIME_TIMEOUT'))return 'La connexion En direct prend trop de temps. Réessayez.';
  if(raw.includes('AUTH_REQUIRED'))return 'Votre session doit être renouvelée avant d’utiliser En direct.';
  return null;
}
