import {getSupabase} from './sinjira-supabase.js';
import {liveCommandRpcSpec,liveTopic,normalizeLiveRoomId,parseLiveInput} from './sinjira-live-command-parser-v25.js';

const MESSAGE_COLUMNS='id,room_id,user_id,body,reply_to,created_at';
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function cleanMessageBody(value){
  const body=String(value||'').trim();
  if(!body||body.length>2000)throw new Error('SOCIAL_LIVE_MESSAGE_LENGTH');
  return body;
}

function cleanOptionalUuid(value,code='SOCIAL_LIVE_ID_INVALID'){
  if(value===null||value===undefined||value==='')return null;
  const id=String(value).trim().toLowerCase();
  if(!UUID_RE.test(id))throw new Error(code);
  return id;
}

async function enrichMessages(rows,supabase){
  const safeRows=Array.isArray(rows)?rows:[];
  const userIds=[...new Set(safeRows.map(row=>String(row?.user_id||'')).filter(id=>UUID_RE.test(id)))];
  const labels=new Map();
  if(userIds.length){
    const {data,error}=await supabase
      .from('social_profiles')
      .select('user_id,pseudo,display_name')
      .in('user_id',userIds);
    if(error)throw error;
    for(const profile of data||[]){
      labels.set(profile.user_id,String(profile.display_name||profile.pseudo||'Membre SINJIRA').trim()||'Membre SINJIRA');
    }
  }
  return safeRows.map(row=>{
    const {user_id,...message}=row;
    return {...message,author_label:labels.get(user_id)||'Membre SINJIRA'};
  });
}

export async function loadLiveMessages(roomId,{supabase=getSupabase(),limit=100}={}){
  const id=normalizeLiveRoomId(roomId);
  const capped=Math.max(1,Math.min(Number(limit)||100,100));
  const {data,error}=await supabase
    .from('social_live_messages')
    .select(MESSAGE_COLUMNS)
    .eq('room_id',id)
    .order('created_at',{ascending:false})
    .limit(capped);
  if(error)throw error;
  const enriched=await enrichMessages((data||[]).reverse(),supabase);
  return enriched;
}

export async function sendLiveMessage(roomId,body,{replyTo=null,supabase=getSupabase()}={}){
  const id=normalizeLiveRoomId(roomId);
  const safeBody=cleanMessageBody(body);
  const safeReply=cleanOptionalUuid(replyTo,'SOCIAL_LIVE_REPLY_INVALID');
  const payload={room_id:id,body:safeBody};
  if(safeReply)payload.reply_to=safeReply;
  const {data,error}=await supabase
    .from('social_live_messages')
    .insert(payload)
    .select(MESSAGE_COLUMNS)
    .single();
  if(error)throw error;
  const [message]=await enrichMessages([data],supabase);
  return message;
}

export async function executeLiveInput(value,{roomId=null,supabase=getSupabase()}={}){
  const parsed=parseLiveInput(value);
  if(parsed.kind==='empty')return {ok:true,empty:true};
  if(parsed.kind==='error')throw new Error(parsed.code);
  if(parsed.kind==='message'){
    if(!roomId)throw new Error('SOCIAL_LIVE_ROOM_REQUIRED');
    return {ok:true,kind:'message',message:await sendLiveMessage(roomId,parsed.body,{supabase})};
  }

  const spec=liveCommandRpcSpec(parsed);
  if(!spec)throw new Error('LIVE_COMMAND_UNKNOWN');
  const {data,error}=await supabase.rpc(spec.rpc,spec.args);
  if(error)throw error;
  return {ok:true,kind:parsed.kind,data:data||null};
}

function presenceCount(channel){
  const state=channel.presenceState()||{};
  return Object.values(state).reduce((total,entries)=>total+(Array.isArray(entries)?entries.length:0),0);
}

async function fetchRealtimeMessage(messageId,roomId,supabase){
  const id=cleanOptionalUuid(messageId,'SOCIAL_LIVE_MESSAGE_ID_INVALID');
  if(!id)return null;
  const {data,error}=await supabase
    .from('social_live_messages')
    .select(MESSAGE_COLUMNS)
    .eq('id',id)
    .eq('room_id',roomId)
    .maybeSingle();
  if(error)throw error;
  if(!data)return null;
  const [message]=await enrichMessages([data],supabase);
  return message||null;
}

export async function openLiveRealtimeSession({
  roomId,
  onMessage=()=>{},
  onPresence=()=>{},
  onStatus=()=>{},
  supabase=getSupabase(),
  subscribeTimeoutMs=10000
}={}){
  const id=normalizeLiveRoomId(roomId);
  const {data:sessionData,error:sessionError}=await supabase.auth.getSession();
  if(sessionError)throw sessionError;
  const accessToken=sessionData?.session?.access_token;
  if(!accessToken)throw new Error('AUTH_REQUIRED');
  await supabase.realtime.setAuth(accessToken);

  // Clé aléatoire éphémère de connexion, distincte de l'UUID du compte.
  const presenceKey=`session-${crypto.randomUUID()}`;
  const channel=supabase.channel(liveTopic(id),{
    config:{
      private:true,
      broadcast:{self:false,ack:false},
      presence:{key:presenceKey}
    }
  });

  channel.on('broadcast',{event:'message_created'},async ({payload})=>{
    try{
      if(String(payload?.room_id||'').toLowerCase()!==id)return;
      // Le Broadcast n'est jamais rendu directement : message_id est relu via RLS.
      const message=await fetchRealtimeMessage(payload?.message_id,id,supabase);
      if(message)onMessage(message);
    }catch(error){
      onStatus({state:'message_error',error});
    }
  });

  channel.on('presence',{event:'sync'},()=>{
    onPresence({count:presenceCount(channel)});
  });

  await new Promise((resolve,reject)=>{
    let settled=false;
    const finish=(fn,value)=>{
      if(settled)return;
      settled=true;
      clearTimeout(timer);
      fn(value);
    };
    const timer=setTimeout(()=>finish(reject,new Error('SOCIAL_LIVE_REALTIME_TIMEOUT')),Math.max(1000,Number(subscribeTimeoutMs)||10000));
    channel.subscribe(async status=>{
      onStatus({state:String(status||'').toLowerCase()});
      if(status==='SUBSCRIBED'){
        try{
          // Presence minimale : aucune identité, aucun profil, aucune localisation.
          await channel.track({online:true});
          finish(resolve);
        }catch(error){finish(reject,error)}
      }else if(status==='CHANNEL_ERROR'||status==='TIMED_OUT'||status==='CLOSED'){
        finish(reject,new Error(`SOCIAL_LIVE_REALTIME_${status}`));
      }
    });
  }).catch(async error=>{
    await supabase.removeChannel(channel).catch(()=>{});
    throw error;
  });

  const initialMessages=await loadLiveMessages(id,{supabase});
  onPresence({count:presenceCount(channel)});

  return {
    roomId:id,
    initialMessages,
    send:(body,options={})=>sendLiveMessage(id,body,{...options,supabase}),
    close:async()=>{
      try{await channel.untrack()}catch{}
      await supabase.removeChannel(channel);
    }
  };
}
