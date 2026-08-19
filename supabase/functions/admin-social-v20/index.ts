import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';

async function ctx(req:Request){
  const user=await requiredUser(req),s=serviceClient();
  const {data}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});
  if(!data)throw new Error('ADMIN_REQUIRED');
  return {user,s};
}

async function canonicalUser(s:any,table:string,idColumn:string,userColumn:string,id:string){
  const {data,error}=await s.from(table).select(userColumn).eq(idColumn,id).maybeSingle();
  if(error)throw error;
  return data?.[userColumn]||null;
}

async function reportTargetUser(s:any,r:any){
  const snap=r.snapshot||{};
  if(snap.source==='dating'){
    const profileId=String(snap.dating_profile_id||r.target_id||'');
    if(!profileId)return null;
    return canonicalUser(s,'dating_profiles','id','user_id',profileId);
  }
  if(r.network==='real'){
    if(r.target_type==='post')return canonicalUser(s,'social_real_posts','id','user_id',r.target_id);
    if(r.target_type==='comment')return canonicalUser(s,'social_real_comments','id','user_id',r.target_id);
    if(r.target_type==='message')return canonicalUser(s,'social_real_messages','id','sender_user_id',r.target_id);
    if(r.target_type==='profile')return canonicalUser(s,'social_profiles','user_id','user_id',r.target_id);
  }
  if(r.network==='character'){
    if(r.target_type==='post')return canonicalUser(s,'social_character_posts','id','user_id',r.target_id);
    if(r.target_type==='comment')return canonicalUser(s,'social_character_comments','id','user_id',r.target_id);
    if(r.target_type==='message')return canonicalUser(s,'social_character_messages','id','sender_user_id',r.target_id);
    if(r.target_type==='profile')return canonicalUser(s,'character_social_profiles','character_id','user_id',r.target_id);
  }
  return null;
}

async function suspendDatingForUser(s:any,userId:string){
  const {data:profile,error}=await s.from('dating_profiles').select('id').eq('user_id',userId).maybeSingle();
  if(error)throw error;
  if(!profile?.id)return;
  const {error:pauseError}=await s.from('dating_profiles').update({enabled:false}).eq('id',profile.id);
  if(pauseError)throw pauseError;
  const {error:closeError}=await s.from('dating_connections').update({status:'closed',closed_at:new Date().toISOString(),a_photo_consent:false,b_photo_consent:false}).in('status',['pending','accepted']).or(`profile_a_id.eq.${profile.id},profile_b_id.eq.${profile.id}`);
  if(closeError)throw closeError;
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,s}=await ctx(req),b=await req.json(),a=String(b.action||'');
    if(a==='dashboard'){
      const [{count:open},{count:susp}]=await Promise.all([
        s.from('social_reports').select('id',{count:'exact',head:true}).eq('status','open'),
        s.from('social_suspensions').select('user_id',{count:'exact',head:true}).or(`until_at.is.null,until_at.gt.${new Date().toISOString()}`)
      ]);
      return json({ok:true,dashboard:{open_reports:open||0,active_suspensions:susp||0}});
    }
    if(a==='list_reports'){
      const {data,error}=await s.from('social_reports').select('*').eq('status','open').order('created_at',{ascending:false}).limit(300);
      if(error)throw error;
      return json({ok:true,reports:data||[]});
    }
    if(a==='resolve_report'){
      const {error}=await s.from('social_reports').update({status:'resolved',reviewed_at:new Date().toISOString(),reviewed_by:user.id}).eq('id',b.report_id);
      if(error)throw error;
      return json({ok:true});
    }
    if(a==='remove_reported_content'){
      const {data:r,error}=await s.from('social_reports').select('*').eq('id',b.report_id).single();
      if(error)throw error;
      if(r.snapshot?.source==='dating')throw new Error('DATING_REPORT_HAS_NO_REMOVABLE_PUBLIC_CONTENT');
      const map:any={real:{post:'social_real_posts',comment:'social_real_comments',message:'social_real_messages'},character:{post:'social_character_posts',comment:'social_character_comments',message:'social_character_messages'}};
      const table=map?.[r.network]?.[r.target_type];
      if(table){const {error:e}=await s.from(table).delete().eq('id',r.target_id);if(e)throw e;}
      await s.from('social_reports').update({status:'resolved',reviewed_at:new Date().toISOString(),reviewed_by:user.id}).eq('id',r.id);
      return json({ok:true});
    }
    if(a==='suspend_reported_user'){
      const {data:r,error}=await s.from('social_reports').select('*').eq('id',b.report_id).single();
      if(error)throw error;
      const uid=await reportTargetUser(s,r);
      if(!uid)throw new Error('TARGET_USER_NOT_FOUND');
      const days=Math.max(1,Math.min(Number(b.days||7),365));
      const until=new Date(Date.now()+days*86400000).toISOString();
      const {error:e}=await s.from('social_suspensions').upsert({user_id:uid,reason:`Signalement ${r.id}: ${r.reason}`,until_at:until,created_by:user.id},{onConflict:'user_id'});
      if(e)throw e;
      await suspendDatingForUser(s,uid);
      return json({ok:true,until_at:until});
    }
    return json({ok:false,error:'Action inconnue.'},400);
  }catch(e){
    console.error(e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(e?.message==='ADMIN_REQUIRED')return json({ok:false,error:'Administration refusée.'},403);
    return json({ok:false,error:e?.message||'Erreur de modération sociale.'},500);
  }
});