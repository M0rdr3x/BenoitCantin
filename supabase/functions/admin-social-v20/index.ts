import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';

async function ctx(req:Request){
  const user=await requiredUser(req),s=serviceClient();
  const {data,error}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});
  if(error||!data)throw new Error('ADMIN_REQUIRED');
  return {user,s};
}
async function audit(s:any,userId:string,action:string,r:any,metadata:Record<string,unknown>={}){
  try{await s.from('admin_audit_log').insert({admin_user_id:userId,action,entity_type:'social_report',entity_id:String(r?.id||''),summary:`${r?.network||'social'}:${r?.target_type||'target'}`,metadata:{network:r?.network||null,target_type:r?.target_type||null,target_id:r?.target_id||null,...metadata}})}
  catch(e){console.warn('[SINJIRA social audit]',e)}
}
async function authoritativeTargetUser(s:any,r:any){
  if(!r?.id)return null;
  // V24.4.11 conserve une correspondance serveur privée pour que le modérateur puisse
  // encore suspendre l'auteur après suppression du contenu, sans jamais faire confiance
  // au snapshot lisible par le déclarant.
  const {data:stored,error:storedError}=await s.from('social_report_targets').select('target_user_id').eq('report_id',r.id).maybeSingle();
  if(!storedError&&stored?.target_user_id)return stored.target_user_id;
  const network=String(r?.network||''),type=String(r?.target_type||''),id=r?.target_id;if(!id)return null;
  let table='',column='user_id';
  if(network==='real'){
    if(type==='post')table='social_real_posts';
    else if(type==='comment')table='social_real_comments';
    else if(type==='message'){table='social_real_messages';column='sender_user_id'}
    else if(type==='profile'){const {data}=await s.from('social_profiles').select('user_id').eq('user_id',id).maybeSingle();return data?.user_id||null}
  }else if(network==='character'){
    if(type==='post')table='social_character_posts';
    else if(type==='comment')table='social_character_comments';
    else if(type==='message'){table='social_character_messages';column='sender_user_id'}
    else if(type==='profile'){const {data}=await s.from('character_social_profiles').select('user_id').eq('character_id',id).maybeSingle();return data?.user_id||null}
  }
  if(!table)return null;
  const {data}=await s.from(table).select(column).eq('id',id).maybeSingle();return data?.[column]||null;
}
function suspensionDays(value:unknown){const n=Number(value);if(!Number.isFinite(n)||!Number.isInteger(n))throw new Error('INVALID_SUSPENSION_DAYS');return Math.max(1,Math.min(n,365))}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,s}=await ctx(req),b=await req.json().catch(()=>({})),a=String(b.action||'');
    if(a==='dashboard'){
      const [{count:open},{count:susp}]=await Promise.all([s.from('social_reports').select('id',{count:'exact',head:true}).eq('status','open'),s.from('social_suspensions').select('user_id',{count:'exact',head:true}).or(`until_at.is.null,until_at.gt.${new Date().toISOString()}`)]);
      return json({ok:true,dashboard:{open_reports:open||0,active_suspensions:susp||0}});
    }
    if(a==='list_reports'){
      const {data,error}=await s.from('social_reports').select('*').eq('status','open').order('created_at',{ascending:false}).limit(300);if(error)throw error;return json({ok:true,reports:data||[]});
    }
    if(a==='resolve_report'){
      const {data:r,error:readError}=await s.from('social_reports').select('*').eq('id',b.report_id).single();if(readError)throw readError;
      const {error}=await s.from('social_reports').update({status:'resolved',reviewed_at:new Date().toISOString(),reviewed_by:user.id}).eq('id',r.id);if(error)throw error;
      await audit(s,user.id,'resolve_social_report',r);return json({ok:true});
    }
    if(a==='remove_reported_content'){
      const {data:r,error}=await s.from('social_reports').select('*').eq('id',b.report_id).single();if(error)throw error;
      const map:any={real:{post:'social_real_posts',comment:'social_real_comments',message:'social_real_messages'},character:{post:'social_character_posts',comment:'social_character_comments',message:'social_character_messages'}};
      const table=map?.[r.network]?.[r.target_type];if(!table)throw new Error('UNSUPPORTED_MODERATION_TARGET');
      const {error:deleteError}=await s.from(table).delete().eq('id',r.target_id);if(deleteError)throw deleteError;
      const {error:resolveError}=await s.from('social_reports').update({status:'resolved',reviewed_at:new Date().toISOString(),reviewed_by:user.id}).eq('id',r.id);if(resolveError)throw resolveError;
      await audit(s,user.id,'remove_reported_content',r);return json({ok:true});
    }
    if(a==='suspend_reported_user'){
      const {data:r,error}=await s.from('social_reports').select('*').eq('id',b.report_id).single();if(error)throw error;
      const uid=await authoritativeTargetUser(s,r);if(!uid)throw new Error('TARGET_USER_NOT_FOUND');if(uid===user.id)throw new Error('CANNOT_SUSPEND_SELF');
      const days=suspensionDays(b.days??7),until=new Date(Date.now()+days*86400000).toISOString();
      const {error:suspensionError}=await s.from('social_suspensions').upsert({user_id:uid,reason:`Signalement ${r.id}: ${String(r.reason||'').slice(0,500)}`,until_at:until,created_by:user.id},{onConflict:'user_id'});if(suspensionError)throw suspensionError;
      await audit(s,user.id,'suspend_reported_user',r,{suspended_user_id:uid,days,until_at:until});return json({ok:true,until_at:until});
    }
    return json({ok:false,error:'Action inconnue.'},400);
  }catch(e){
    console.error('[SINJIRA social admin]',e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(e?.message==='ADMIN_REQUIRED')return json({ok:false,error:'Administration refusée.'},403);
    if(e?.message==='TARGET_USER_NOT_FOUND')return json({ok:false,error:'Le compte visé par ce signalement n’existe plus ou ne correspond pas à la cible.'},409);
    if(e?.message==='INVALID_SUSPENSION_DAYS')return json({ok:false,error:'La durée de suspension doit être un nombre entier entre 1 et 365 jours.'},400);
    if(e?.message==='CANNOT_SUSPEND_SELF')return json({ok:false,error:'Un administrateur ne peut pas se suspendre lui-même depuis un signalement.'},409);
    if(e?.message==='UNSUPPORTED_MODERATION_TARGET')return json({ok:false,error:'Ce type de contenu doit être modéré depuis sa fiche dédiée.'},409);
    return json({ok:false,error:'Erreur de modération sociale.'},500);
  }
});
