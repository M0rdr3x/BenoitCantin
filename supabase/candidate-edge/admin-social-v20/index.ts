// CANDIDAT DE REVUE UNIQUEMENT — NON DEPLOYE.
// Source: après migration approuvée, recopier dans supabase/functions/admin-social-v20/index.ts
// avec les imports de déploiement et les validations de contrat restaurés.
import { readLimitedUtf8Body } from '../../functions/_shared/limited-body.mjs';
import {corsHeaders} from '../../functions/_shared/cors.ts';
import {requiredAdmin} from '../../functions/_shared/auth.ts';

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
  'AUTH_REQUIRED','ADMIN_REQUIRED','MFA_REQUIRED','MFA_SETUP_REQUIRED','MFA_STATE_UNAVAILABLE',
  'REQUEST_TOO_LARGE','INVALID_JSON','UNSUPPORTED_MEDIA_TYPE',
  'CONTENT_TARGET_NOT_REVERSIBLE','TARGET_USER_NOT_FOUND',
  'DATING_REPORT_HAS_NO_REMOVABLE_PUBLIC_CONTENT','INVALID_APPEAL_OUTCOME',
  'APPEAL_REVIEW_REASON_LENGTH', 'INVALID_MODERATION_REFERENCE',
  'REPORT_NOT_OPEN', 'TARGET_USER_NOT_FOUND', 'INVALID_SUSPENSION_DURATION',
  'ATOMIC_MODERATION_FAILED', 'INVALID_MODERATION_INPUT',
  'APPEAL_NOT_PENDING', 'DECISION_NOT_ACTIVE', 'SUSPENSION_ALREADY_ACTIVE'
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
  const limited=await readLimitedUtf8Body(req,MAX_REQUEST_BYTES);
  if(!limited.ok)throw new Error('REQUEST_TOO_LARGE');
  const raw=limited.raw;
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  let body:any;
  try{body=JSON.parse(raw||'{}');}
  catch{throw new Error('INVALID_JSON');}
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body;
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

// Les erreurs de PostgREST ne sont ni retournées ni journalisées en clair.
// Seuls des codes métier fixes et non sensibles sont conservés.
const ATOMIC_SQL_CODES=new Set([
  'REPORT_NOT_OPEN','TARGET_USER_NOT_FOUND','CONTENT_TARGET_NOT_REVERSIBLE',
  'INVALID_SUSPENSION_DURATION','INVALID_MODERATION_INPUT',
  'APPEAL_NOT_PENDING','DECISION_NOT_ACTIVE','ADMIN_REQUIRED',
  'SUSPENSION_ALREADY_ACTIVE','INVALID_APPEAL_REVIEW'
]);
function atomicFailure(error:any):never{
  const code=typeof error?.message==='string'&&ATOMIC_SQL_CODES.has(error.message)
    ?error.message:'ATOMIC_MODERATION_FAILED';
  throw new Error(code);
}
async function atomicModeration(
  s:any,adminId:string,reportId:string,
  action:'resolve_report'|'hide_content'|'suspend_social',
  payload:any={}
){
  // Le service Role n'est accessible qu'après requiredAdmin(req) et AAL2.
  // On utilise le wrapper PUBLIC limité à service_role, pas le schéma privé.
  const {data,error}=await s.rpc('sinjira_admin_moderate_atomic',{
    p_admin_id:adminId,p_report_id:reportId,p_action:action,
    p_policy_rule:payload.rule??null,
    p_statement:payload.statement??null,
    p_urgency:payload.urgency??'standard',p_days:payload.days??null
  });
  if(error)atomicFailure(error);
  if(data?.ok!==true ||
    (action==='resolve_report' ? data.resolved!==true :
      typeof data.decision_id!=='string'))
    throw new Error('ATOMIC_MODERATION_FAILED');
  return data;
}
async function createDecision(
  s:any,adminId:string,r:any,b:any,action:'hide_content'|'suspend_social'
){
  if(!r||r.status!=='open')throw new Error('REPORT_NOT_OPEN');
  if(action==='hide_content'&&
    (r.snapshot?.source==='dating'||
     !['real','character'].includes(r.network)||
     !['post','comment','message'].includes(r.target_type)))
    throw new Error('CONTENT_TARGET_NOT_REVERSIBLE');
  const {rule,statement}=policyAndStatement(r,b,action);
  const urgency=b.urgency===undefined?'standard':b.urgency;
  if(!['standard','urgent_harm','illegal_content'].includes(urgency))
    throw new Error('INVALID_MODERATION_INPUT');
  const days=action==='suspend_social'?(b.days===undefined?7:b.days):null;
  if(action==='suspend_social'&&
    (typeof days!=='number'||!Number.isInteger(days)||days<1||days>365))
    throw new Error('INVALID_SUSPENSION_DURATION');
  const result=await atomicModeration(s,adminId,r.id,action,{
    rule,statement,urgency,days
  });
  return {id:result.decision_id,ends_at:result.until_at??null};
}

async function appealOverview(s:any,adminId:string){
  const {data,error}=await s.rpc('sinjira_admin_appeals_overview',{
    p_admin_id:adminId,p_limit:300
  });
  if(error)atomicFailure(error);
  if(!data||!Number.isSafeInteger(data.pending_count)||
     data.pending_count<0||!Array.isArray(data.appeals))
    throw new Error('ATOMIC_MODERATION_FAILED');
  return data;
}
async function listAppeals(s:any,adminId:string){
  return (await appealOverview(s,adminId)).appeals;
}

async function reviewAppeal(s:any,adminId:string,b:any){
  const outcome=String(b.outcome||'');
  const reason=String(b.review_reason||'').trim();
  if(!['upheld','reversed'].includes(outcome))throw new Error('INVALID_APPEAL_OUTCOME');
  if(reason.length<20||reason.length>4000)throw new Error('APPEAL_REVIEW_REASON_LENGTH');
  const {data,error}=await s.rpc('sinjira_admin_review_appeal_atomic',{
    p_admin_id:adminId,p_appeal_id:b.appeal_id,
    p_outcome:outcome,p_review_reason:reason
  });
  if(error)atomicFailure(error);
  if(data?.ok!==true||data.outcome!==outcome||
    typeof data.decision_id!=='string'||typeof data.appeal_id!=='string')
    throw new Error('ATOMIC_MODERATION_FAILED');
  return data;
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,service:s}=await requiredAdmin(req);
    requireJsonContentType(req);
    const b=await readLimitedJson(req);
    const a=typeof b.action==='string'?b.action.trim().slice(0,64):'';
    // Obligatoire aussi pour clients alternatifs et requêtes sans UI.
    if(['resolve_report','restrict_reported_content','remove_reported_content',
      'suspend_reported_user','review_appeal'].includes(a)){
      const reference=a==='review_appeal'?b.appeal_id:b.report_id;
      if(typeof reference!=='string'||!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(reference))
        throw new Error('INVALID_MODERATION_REFERENCE');
    }
    if(a==='dashboard'){
      const [{count:open,error:openError},{count:susp,error:suspError},appeals]=await Promise.all([
        s.from('social_reports').select('id',{count:'exact',head:true}).eq('status','open'),
        s.from('social_suspensions').select('user_id',{count:'exact',head:true}).or(`until_at.is.null,until_at.gt.${new Date().toISOString()}`),
        appealOverview(s,user.id)
      ]);
      if(openError||suspError)throw new Error('ATOMIC_MODERATION_FAILED');
      return privateJson({ok:true,dashboard:{
        open_reports:open||0,active_suspensions:susp||0,
        pending_appeals:appeals.pending_count
      }});
    }
    if(a==='list_reports'){
      const {data,error}=await s.from('social_reports').select('*').eq('status','open').order('created_at',{ascending:false}).limit(300);
      if(error)throw error;
      return privateJson({ok:true,reports:data||[]});
    }
    if(a==='list_appeals')return privateJson({ok:true,appeals:await listAppeals(s,user.id)});
    if(a==='resolve_report'){
      await atomicModeration(s,user.id,b.report_id,'resolve_report');
      return privateJson({ok:true});
    }
    if(a==='restrict_reported_content'||a==='remove_reported_content'){
      const {data:r,error}=await s.from('social_reports').select('*').eq('id',b.report_id).eq('status','open').maybeSingle();
      if(error)throw error;
      if(!r)throw new Error('REPORT_NOT_OPEN');
      if(r.snapshot?.source==='dating')throw new Error('DATING_REPORT_HAS_NO_REMOVABLE_PUBLIC_CONTENT');
      const decision=await createDecision(s,user.id,r,b,'hide_content');
      return privateJson({ok:true,decision_id:decision.id,reversible:true});
    }
    if(a==='suspend_reported_user'){
      const {data:r,error}=await s.from('social_reports').select('*').eq('id',b.report_id).eq('status','open').maybeSingle();
      if(error)throw error;
      if(!r)throw new Error('REPORT_NOT_OPEN');
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
    if(e?.message==='MFA_SETUP_REQUIRED')return privateJson({ok:false,error:'Activez un facteur TOTP dans Ma sécurité avant d’utiliser l’administration.',code:'MFA_SETUP_REQUIRED',setup_url:'/compte/securite.html'},403);
    if(e?.message==='MFA_STATE_UNAVAILABLE')return privateJson({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(e?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE'},413);
    if(e?.message==='UNSUPPORTED_MEDIA_TYPE')return privateJson({ok:false,error:'Content-Type application/json requis.',code:'UNSUPPORTED_MEDIA_TYPE'},415);
    if(e?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON'},400);
    if(e?.message==='INVALID_MODERATION_REFERENCE'||e?.message==='INVALID_SUSPENSION_DURATION')
      return privateJson({ok:false,error:'Paramètres de modération invalides.',code:'INVALID_MODERATION_INPUT'},400);
    if(e?.message==='REPORT_NOT_OPEN')
      return privateJson({ok:false,error:'Ce signalement n’est plus ouvert.',code:'REPORT_NOT_OPEN'},409);
    if(e?.message==='TARGET_USER_NOT_FOUND')
      return privateJson({ok:false,error:'La cible de cette mesure est introuvable.',code:'TARGET_USER_NOT_FOUND'},409);
    return privateJson({ok:false,error:'Erreur de modération sociale.',code:'MODERATION_FAILED'},500);
  }
});
