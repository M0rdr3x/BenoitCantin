import {corsHeaders} from '../_shared/cors.ts';
import {requiredAdmin} from '../_shared/auth.ts';

const MAX_REQUEST_BYTES=8192;
const PRIVATE_HEADERS={
  ...corsHeaders,
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  'Pragma':'no-cache',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer'
};
const SAFE_LOG_CODES=new Set([
  'AUTH_REQUIRED','ADMIN_REQUIRED','MFA_REQUIRED','MFA_STATE_UNAVAILABLE',
  'REQUEST_TOO_LARGE','INVALID_JSON','UNSUPPORTED_MEDIA_TYPE',
  'CONTENT_TARGET_NOT_REVERSIBLE','TARGET_USER_NOT_FOUND',
  'DATING_REPORT_HAS_NO_REMOVABLE_PUBLIC_CONTENT','INVALID_APPEAL_OUTCOME',
  'APPEAL_REVIEW_REASON_LENGTH'
]);

function privateJson(data:unknown,status=200){
  return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS});
}

function requireJsonContentType(req:Request){
  const contentType=(req.headers.get('content-type')||'').toLowerCase();
  if(!contentType.startsWith('application/json'))throw new Error('UNSUPPORTED_MEDIA_TYPE');
}

function moderationLogCode(error:unknown){
  const code=error instanceof Error?error.message:'';
  return SAFE_LOG_CODES.has(code)?code:'MODERATION_BACKEND_FAILED';
}

async function readLimitedJson(req:Request){
  const rawLength=req.headers.get('content-length');
  if(rawLength){
    const declared=Number(rawLength);
    if(!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  }
  const raw=await req.text();
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  let body:any;
  try{body=JSON.parse(raw||'{}');}
  catch{throw new Error('INVALID_JSON');}
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body;
}

const targetTables:any={
  real:{post:['social_real_posts','user_id'],comment:['social_real_comments','user_id'],message:['social_real_messages','sender_user_id']},
  character:{post:['social_character_posts','user_id'],comment:['social_character_comments','user_id'],message:['social_character_messages','sender_user_id']}
};

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

async function targetSnapshot(s:any,r:any){
  const pair=targetTables?.[r.network]?.[r.target_type];
  if(!pair)return null;
  const {data,error}=await s.from(pair[0]).select('*').eq('id',r.target_id).maybeSingle();
  if(error)throw error;
  return data||null;
}

function policyAndStatement(r:any,b:any,action:string){
  const rule=String(b.policy_rule||`Règles communautaires SINJIRA™ — ${r.reason||'sécurité communautaire'}`).trim().slice(0,240);
  let statement=String(b.statement_of_reasons||'').trim();
  if(statement.length<20){
    statement=action==='hide_content'
      ? `Après examen humain du signalement, ce contenu est masqué pour le motif « ${r.reason||'sécurité communautaire'} ». La mesure est réversible et peut faire l’objet d’un appel interne gratuit.`
      : `Après examen humain du signalement, l’accès social est temporairement suspendu pour le motif « ${r.reason||'sécurité communautaire'} ». La mesure peut faire l’objet d’un appel interne gratuit.`;
  }
  return {rule,statement:statement.slice(0,4000)};
}

async function notifyDecision(s:any,userId:string|null,decisionId:string,title:string,body:string){
  if(!userId)return;
  const {error}=await s.from('user_notifications').insert({
    user_id:userId,notification_type:'moderation_decision',title,body,
    related_entity_type:'moderation_decision',related_entity_id:decisionId,
    action_path:'/compte/moderation.html'
  });
  if(error)console.error('[SINJIRA moderation notification]','NOTIFICATION_WRITE_FAILED');
}

async function createDecision(s:any,adminId:string,r:any,b:any,action:'hide_content'|'suspend_social'){
  const subject=await reportTargetUser(s,r);
  if(action==='hide_content'&&!targetTables?.[r.network]?.[r.target_type])throw new Error('CONTENT_TARGET_NOT_REVERSIBLE');
  const evidence={report_snapshot:r.snapshot||{},target_snapshot:await targetSnapshot(s,r),report_reason:r.reason,report_created_at:r.created_at};
  const {rule,statement}=policyAndStatement(r,b,action);
  const urgency=['standard','urgent_harm','illegal_content'].includes(String(b.urgency))?String(b.urgency):'standard';
  const row:any={subject_user_id:subject,report_id:r.id,network:r.snapshot?.source==='dating'?'dating':r.network,target_type:r.snapshot?.source==='dating'?'account':r.target_type,target_id:r.target_id,action,status:'active',policy_rule:rule,statement_of_reasons:statement,evidence_snapshot:evidence,urgency,decision_source:'human_admin',decided_by:adminId};
  if(action==='suspend_social'){
    const days=Math.max(1,Math.min(Number(b.days||7),365));
    row.ends_at=new Date(Date.now()+days*86400000).toISOString();
  }
  const {data:decision,error}=await s.schema('private').from('moderation_decisions').insert(row).select('id,ends_at').single();
  if(error)throw error;
  if(action==='suspend_social'){
    if(!subject)throw new Error('TARGET_USER_NOT_FOUND');
    const {error:suspensionError}=await s.from('social_suspensions').upsert({user_id:subject,reason:statement,until_at:decision.ends_at,created_by:adminId,moderation_decision_id:decision.id},{onConflict:'user_id'});
    if(suspensionError)throw suspensionError;
  }
  const {error:reportError}=await s.from('social_reports').update({status:'resolved',reviewed_at:new Date().toISOString(),reviewed_by:adminId}).eq('id',r.id);
  if(reportError)throw reportError;
  await notifyDecision(s,subject,decision.id,action==='hide_content'?'Décision de modération — contenu masqué':'Décision de modération — suspension sociale',statement);
  return decision;
}

async function listAppeals(s:any){
  const {data:appeals,error}=await s.schema('private').from('moderation_appeals').select('*').eq('status','pending').order('submitted_at',{ascending:true}).limit(300);
  if(error)throw error;
  const rows=appeals||[];
  const ids=[...new Set(rows.map((x:any)=>x.decision_id).filter(Boolean))];
  let decisions:any[]=[];
  if(ids.length){
    const res=await s.schema('private').from('moderation_decisions').select('id,subject_user_id,network,target_type,target_id,action,status,policy_rule,statement_of_reasons,urgency,starts_at,ends_at,appeal_deadline,decided_at').in('id',ids);
    if(res.error)throw res.error;
    decisions=res.data||[];
  }
  const byId=new Map(decisions.map((d:any)=>[d.id,d]));
  return rows.map((a:any)=>({...a,decision:byId.get(a.decision_id)||null}));
}

async function reviewAppeal(s:any,adminId:string,b:any){
  const outcome=String(b.outcome||'');
  const reason=String(b.review_reason||'').trim();
  if(!['upheld','reversed'].includes(outcome))throw new Error('INVALID_APPEAL_OUTCOME');
  if(reason.length<20||reason.length>4000)throw new Error('APPEAL_REVIEW_REASON_LENGTH');
  const {data:appeal,error}=await s.schema('private').from('moderation_appeals').select('*').eq('id',b.appeal_id).eq('status','pending').single();
  if(error)throw error;
  const {data:decision,error:decisionError}=await s.schema('private').from('moderation_decisions').select('*').eq('id',appeal.decision_id).single();
  if(decisionError)throw decisionError;
  const now=new Date().toISOString();
  if(outcome==='reversed'){
    const {error:reverseError}=await s.schema('private').from('moderation_decisions').update({status:'reversed',reversed_at:now,reversed_by:adminId,reversal_reason:reason,updated_at:now}).eq('id',decision.id);
    if(reverseError)throw reverseError;
    if(decision.action==='suspend_social'){
      const {error:suspensionError}=await s.from('social_suspensions').delete().eq('moderation_decision_id',decision.id);
      if(suspensionError)throw suspensionError;
    }
  }
  const {error:appealError}=await s.schema('private').from('moderation_appeals').update({status:outcome,reviewed_by:adminId,reviewed_at:now,review_reason:reason,updated_at:now}).eq('id',appeal.id);
  if(appealError)throw appealError;
  if(appeal.appellant_user_id){
    const title=outcome==='reversed'?'Appel accepté — décision renversée':'Appel examiné — décision maintenue';
    await notifyDecision(s,appeal.appellant_user_id,decision.id,title,reason);
  }
  return {ok:true,outcome,decision_id:decision.id};
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,service:s}=await requiredAdmin(req);
    requireJsonContentType(req);
    const b=await readLimitedJson(req);
    const a=typeof b.action==='string'?b.action.trim().slice(0,64):'';
    if(a==='dashboard'){
      const [{count:open},{count:susp},{count:appeals}]=await Promise.all([
        s.from('social_reports').select('id',{count:'exact',head:true}).eq('status','open'),
        s.from('social_suspensions').select('user_id',{count:'exact',head:true}).or(`until_at.is.null,until_at.gt.${new Date().toISOString()}`),
        s.schema('private').from('moderation_appeals').select('id',{count:'exact',head:true}).eq('status','pending')
      ]);
      return privateJson({ok:true,dashboard:{open_reports:open||0,active_suspensions:susp||0,pending_appeals:appeals||0}});
    }
    if(a==='list_reports'){
      const {data,error}=await s.from('social_reports').select('*').eq('status','open').order('created_at',{ascending:false}).limit(300);
      if(error)throw error;
      return privateJson({ok:true,reports:data||[]});
    }
    if(a==='list_appeals')return privateJson({ok:true,appeals:await listAppeals(s)});
    if(a==='resolve_report'){
      const {error}=await s.from('social_reports').update({status:'resolved',reviewed_at:new Date().toISOString(),reviewed_by:user.id}).eq('id',b.report_id);
      if(error)throw error;
      return privateJson({ok:true});
    }
    if(a==='restrict_reported_content'||a==='remove_reported_content'){
      const {data:r,error}=await s.from('social_reports').select('*').eq('id',b.report_id).single();
      if(error)throw error;
      if(r.snapshot?.source==='dating')throw new Error('DATING_REPORT_HAS_NO_REMOVABLE_PUBLIC_CONTENT');
      const decision=await createDecision(s,user.id,r,b,'hide_content');
      return privateJson({ok:true,decision_id:decision.id,reversible:true});
    }
    if(a==='suspend_reported_user'){
      const {data:r,error}=await s.from('social_reports').select('*').eq('id',b.report_id).single();
      if(error)throw error;
      const decision=await createDecision(s,user.id,r,b,'suspend_social');
      return privateJson({ok:true,decision_id:decision.id,until_at:decision.ends_at,reversible:true});
    }
    if(a==='review_appeal')return privateJson(await reviewAppeal(s,user.id,b));
    return privateJson({ok:false,error:'Action inconnue.'},400);
  }catch(e){
    console.error('[admin-social-v20]',moderationLogCode(e));
    if(e?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(e?.message==='ADMIN_REQUIRED')return privateJson({ok:false,error:'Administration refusée.',code:'ADMIN_REQUIRED'},403);
    if(e?.message==='MFA_REQUIRED')return privateJson({ok:false,error:'MFA_REQUIRED',code:'MFA_REQUIRED'},403);
    if(e?.message==='MFA_STATE_UNAVAILABLE')return privateJson({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(e?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE'},413);
    if(e?.message==='UNSUPPORTED_MEDIA_TYPE')return privateJson({ok:false,error:'Content-Type application/json requis.',code:'UNSUPPORTED_MEDIA_TYPE'},415);
    if(e?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON'},400);
    return privateJson({ok:false,error:'Erreur de modération sociale.',code:'MODERATION_FAILED'},500);
  }
});
