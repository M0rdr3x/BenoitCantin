import {getSupabase} from './sinjira-social-common.js?v=24.4.42';

export async function unreadCounts(table,userId,keyField){
  const {data,error}=await getSupabase()
    .from(table)
    .select(keyField)
    .eq('recipient_user_id',userId)
    .is('read_at',null);
  if(error)throw error;
  const counts=new Map();
  for(const row of Array.isArray(data)?data:[]){
    const key=row?.[keyField];
    if(!key)continue;
    counts.set(key,(counts.get(key)||0)+1);
  }
  return counts;
}

export async function unreadTotal(table,userId){
  const {count,error}=await getSupabase()
    .from(table)
    .select('id',{count:'exact',head:true})
    .eq('recipient_user_id',userId)
    .is('read_at',null);
  if(error)throw error;
  return Number(count||0);
}

export async function markConversationRead(table,userId,filters={}){
  let query=getSupabase()
    .from(table)
    .update({read_at:new Date().toISOString()})
    .eq('recipient_user_id',userId)
    .is('read_at',null);
  for(const [column,value] of Object.entries(filters)){
    if(value!==undefined&&value!==null&&value!=='')query=query.eq(column,value);
  }
  const {error}=await query;
  if(error)throw error;
}
