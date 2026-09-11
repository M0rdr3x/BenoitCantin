import { corsHeaders } from '../_shared/cors.ts';
import { requiredAdmin } from '../_shared/auth.ts';

const MAX_REQUEST_BYTES=32768;
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
  'JSON_REQUIRED','REQUEST_TOO_LARGE','INVALID_JSON',
  'PLAYTEST_ACCESS_GRANT_FAILED','PLAYTEST_REVIEW_ROLLBACK_FAILED'
]);

function privateJson(data:unknown,status=200){
  return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS});
}

function adminConsoleLogCode(error:unknown){
  const code=error instanceof Error?error.message:'';
  return SAFE_LOG_CODES.has(code)?code:'ADMIN_CONSOLE_BACKEND_FAILED';
}

async function readBoundedJson(req:Request){
  const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(contentType!=='application/json')throw new Error('JSON_REQUIRED');
  const declaredRaw=req.headers.get('content-length');
  if(declaredRaw){
    const declared=Number(declaredRaw);
    if(!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  }
  const raw=await req.text();
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  let body:unknown;
  try{body=JSON.parse(raw)}catch{throw new Error('INVALID_JSON')}
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body as Record<string,any>;
}

function safeName(v:string){
  return String(v||'document').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()
    .replace(/[^a-z0-9._-]+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,120)||'document';
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.',code:'METHOD_NOT_ALLOWED'},405);
  try{
    const {user,service}=await requiredAdmin(req);
    const body=await readBoundedJson(req),action=String(body?.action||'');

    if(action==='dashboard'){
      const [users,projects,documents,requests,playtests,contributions]=await Promise.all([
        service.auth.admin.listUsers({page:1,perPage:1000}),
        service.from('projects').select('id',{count:'exact',head:true}),
        service.from('documents').select('id',{count:'exact',head:true}).eq('status','approved'),
        service.from('access_requests').select('id',{count:'exact',head:true}).eq('status','pending'),
        service.from('playtests').select('id',{count:'exact',head:true}).in('status',['open','active']),
        service.from('internal_gameplay_contributions').select('id',{count:'exact',head:true})
      ]);
      return privateJson({ok:true,dashboard:{
        users:users.data?.users?.length||0,projects:projects.count||0,approved_documents:documents.count||0,
        pending_requests:requests.count||0,open_playtests:playtests.count||0,contributions:contributions.count||0
      }});
    }

    if(action==='list_projects'){
      const {data,error}=await service.from('projects').select('*').order('sort_order');
      if(error)throw error;return privateJson({ok:true,projects:data||[]});
    }

    if(action==='save_project'){
      const p=body.project||{},payload:any={
        slug:String(p.slug||'').trim(),name:String(p.name||'').trim(),type:p.type||'game',
        status:p.status||'development',visibility:p.visibility||'account',
        description:String(p.description||'').slice(0,5000),cover_url:p.cover_url||null,
        public_path:p.public_path||null,play_path:p.play_path||null,
        allow_tester_requests:p.allow_tester_requests!==false,sort_order:Number(p.sort_order||100)
      };
      if(p.id)payload.id=p.id;
      if(!payload.slug||!payload.name)return privateJson({ok:false,error:'Nom et slug requis.'},400);
      const {data,error}=await service.from('projects').upsert(payload).select('*').single();
      if(error)throw error;return privateJson({ok:true,project:data});
    }

    if(action==='list_documents'){
      const {data,error}=await service.from('documents').select('*,projects(name,slug)').order('created_at',{ascending:false});
      if(error)throw error;return privateJson({ok:true,documents:data||[]});
    }

    if(action==='prepare_document_upload'){
      const x=body.document||{},original=safeName(x.filename||'document.pdf');
      const ext=original.includes('.')?original.split('.').pop():'bin';
      const path=`${x.project_slug||'sinjira'}/${crypto.randomUUID()}/${safeName(x.title||'document')}.${ext}`;
      const bucket='sinjira-private-documents';
      const {data:upload,error:uploadError}=await service.storage.from(bucket).createSignedUploadUrl(path);
      if(uploadError||!upload?.token)throw uploadError||new Error('Token upload absent');
      const {data:row,error:rowError}=await service.from('documents').insert({
        project_id:x.project_id,title:String(x.title||'').trim(),description:String(x.description||'').slice(0,5000),
        document_type:x.document_type||'document',version:x.version||'1.0',status:'draft',
        access_level:x.access_level||'account',storage_bucket:bucket,storage_path:path,
        mime_type:x.mime_type||'application/octet-stream',file_size_bytes:Number(x.file_size_bytes||0)||null,
        sort_order:Number(x.sort_order||100),created_by:user.id
      }).select('*').single();
      if(rowError){await service.storage.from(bucket).remove([path]);throw rowError}
      return privateJson({ok:true,document:row,upload:{path,token:upload.token,bucket}});
    }

    if(action==='finalize_document'||action==='set_document_status'){
      const documentId=body.document_id,desired=action==='finalize_document'
        ?(['review','approved'].includes(body.status)?body.status:'review')
        :body.status;
      if(!['draft','review','approved','archived'].includes(desired))return privateJson({ok:false,error:'Statut invalide.'},400);
      const update:any={status:desired};
      if(desired==='approved'){update.approved_by=user.id;update.approved_at=new Date().toISOString()}
      const {data,error}=await service.from('documents').update(update).eq('id',documentId).select('*').single();
      if(error)throw error;return privateJson({ok:true,document:data});
    }

    if(action==='list_access_requests'){
      const {data,error}=await service.from('access_requests').select('*,projects(name,slug)').order('created_at',{ascending:false});
      if(error)throw error;
      const ids=[...new Set((data||[]).map((x:any)=>x.user_id))],users:any[]=[];
      for(const id of ids){const {data:u}=await service.auth.admin.getUserById(id);if(u?.user)users.push({id,email:u.user.email})}
      return privateJson({ok:true,requests:data||[],users});
    }

    if(action==='review_access_request'){
      const {data:r,error:rerr}=await service.from('access_requests').select('*').eq('id',body.request_id).single();
      if(rerr)throw rerr;const decision=body.decision==='approved'?'approved':'refused';
      if(decision==='approved'){
        const {error}=await service.from('project_access').upsert({
          user_id:r.user_id,project_id:r.project_id,access_level:r.requested_level,granted_by:user.id,source:'request'
        },{onConflict:'user_id,project_id'});if(error)throw error;
      }
      const {error}=await service.from('access_requests').update({
        status:decision,reviewed_by:user.id,reviewed_at:new Date().toISOString(),review_note:String(body.review_note||'').slice(0,1500)
      }).eq('id',r.id);if(error)throw error;return privateJson({ok:true});
    }

    if(action==='list_users'){
      const {data:authData,error:authError}=await service.auth.admin.listUsers({page:1,perPage:1000});if(authError)throw authError;
      const [{data:profiles},{data:access}]=await Promise.all([
        service.from('profiles').select('*'),service.from('project_access').select('*,projects(name,slug)')
      ]);
      const pmap=new Map((profiles||[]).map((p:any)=>[p.user_id,p]));
      const adminIds=new Set((await service.from('internal_admin_users').select('user_id')).data?.map((a:any)=>a.user_id)||[]);
      return privateJson({ok:true,users:(authData.users||[]).map((u:any)=>({
        id:u.id,email:u.email,created_at:u.created_at,last_sign_in_at:u.last_sign_in_at,
        pseudo:pmap.get(u.id)?.pseudo||'',display_name:pmap.get(u.id)?.display_name||'',avatar_path:pmap.get(u.id)?.avatar_path||null,
        is_admin:adminIds.has(u.id),
        access:(access||[]).filter((a:any)=>a.user_id===u.id)
      }))});
    }

    if(action==='grant_access'){
      const {error}=await service.from('project_access').upsert({
        user_id:body.user_id,project_id:body.project_id,access_level:body.access_level==='tester'?'tester':'player',
        granted_by:user.id,source:'manual'
      },{onConflict:'user_id,project_id'});
      if(error)throw error;return privateJson({ok:true});
    }

    if(action==='revoke_access'){
      const {error}=await service.from('project_access').delete().eq('user_id',body.user_id).eq('project_id',body.project_id);
      if(error)throw error;return privateJson({ok:true});
    }

    if(action==='list_playtests'){
      const {data,error}=await service.from('playtests').select('*,projects(name,slug),playtest_participants(*)').order('created_at',{ascending:false});
      if(error)throw error;return privateJson({ok:true,playtests:data||[]});
    }

    if(action==='save_playtest'){
      const p=body.playtest||{},payload:any={
        project_id:p.project_id,title:String(p.title||'').trim(),description:String(p.description||'').slice(0,5000),
        status:p.status||'draft',required_access:p.required_access||'tester',
        starts_at:p.starts_at||null,ends_at:p.ends_at||null,max_participants:Number(p.max_participants||0)||null,created_by:user.id
      };
      if(p.id)payload.id=p.id;
      const {data,error}=await service.from('playtests').upsert(payload).select('*').single();
      if(error)throw error;return privateJson({ok:true,playtest:data});
    }

    if(action==='review_playtest_participant'){
      const state=['approved','refused','completed'].includes(body.status)?body.status:'refused';
      const {data:row,error:findError}=await service.from('playtest_participants').select('*,playtests(project_id)')
        .eq('playtest_id',body.playtest_id).eq('user_id',body.user_id).single();if(findError)throw findError;
      const previousReview={status:row.status,reviewed_by:row.reviewed_by??null,reviewed_at:row.reviewed_at??null};
      const {error}=await service.from('playtest_participants').update({
        status:state,reviewed_by:user.id,reviewed_at:new Date().toISOString()
      }).eq('playtest_id',body.playtest_id).eq('user_id',body.user_id);if(error)throw error;
      if(state==='approved'){
        const {error:grantError}=await service.from('project_access').upsert({
          user_id:body.user_id,project_id:row.playtests.project_id,access_level:'tester',granted_by:user.id,source:'playtest'
        },{onConflict:'user_id,project_id'});
        if(grantError){
          const {error:rollbackError}=await service.from('playtest_participants').update(previousReview)
            .eq('playtest_id',body.playtest_id).eq('user_id',body.user_id);
          if(rollbackError)throw new Error('PLAYTEST_REVIEW_ROLLBACK_FAILED');
          throw new Error('PLAYTEST_ACCESS_GRANT_FAILED');
        }
      }
      return privateJson({ok:true});
    }

    if(action==='list_extensions'){
      const [{data:extensions,error},{data:rows=[]}]=await Promise.all([
        service.from('extensions').select('*,projects(name,slug)').order('created_at',{ascending:false}),
        service.from('internal_gameplay_contributions').select('game_slug,feedback,created_at').order('created_at',{ascending:false}).limit(2000)
      ]);
      if(error)throw error;
      const signals=rows.map((r:any)=>({
        game_slug:r.game_slug,idea:String(r.feedback?.extension_idea||'').trim(),
        favorite:String(r.feedback?.favorite_mechanic||'').trim(),unclear:String(r.feedback?.unclear_text||'').trim(),created_at:r.created_at
      })).filter((x:any)=>x.idea||x.favorite||x.unclear);
      return privateJson({ok:true,extensions:extensions||[],signals});
    }

    if(action==='save_extension'){
      const e=body.extension||{},payload:any={
        project_id:e.project_id,title:String(e.title||'').trim(),description:String(e.description||'').slice(0,10000),
        status:e.status||'idea',is_public:Boolean(e.is_public),created_by:user.id
      };
      if(e.id)payload.id=e.id;
      const {data,error}=await service.from('extensions').upsert(payload).select('*').single();
      if(error)throw error;return privateJson({ok:true,extension:data});
    }

    if(action==='analytics'){
      const {data:rows=[],error}=await service.from('internal_gameplay_contributions')
        .select('game_slug,metrics,feedback,created_at').order('created_at',{ascending:false}).limit(10000);
      if(error)throw error;const byGame:any={};
      for(const r of rows){
        const k=r.game_slug||'inconnu',m=r.metrics||{},f=r.feedback||{};
        byGame[k]||={count:0,players:0,pc:0,duration:0,dc:0,ratings:0,rc:0,difficulty:{}};
        const g=byGame[k];g.count++;
        if(Number(m.player_count)>0){g.players+=Number(m.player_count);g.pc++}
        if(Number(m.duration_minutes)>0){g.duration+=Number(m.duration_minutes);g.dc++}
        if(Number(f.rating)>0){g.ratings+=Number(f.rating);g.rc++}
        if(f.difficulty)g.difficulty[f.difficulty]=(g.difficulty[f.difficulty]||0)+1;
      }
      for(const g of Object.values(byGame) as any[]){
        g.average_players=g.pc?Math.round(g.players/g.pc*10)/10:null;
        g.average_duration=g.dc?Math.round(g.duration/g.dc):null;
        g.average_rating=g.rc?Math.round(g.ratings/g.rc*10)/10:null;
        delete g.players;delete g.pc;delete g.duration;delete g.dc;delete g.ratings;delete g.rc;
      }
      return privateJson({ok:true,analytics:byGame});
    }

    return privateJson({ok:false,error:'Action inconnue.',code:'UNKNOWN_ACTION'},400);
  }catch(e){
    console.error('[admin-console]',adminConsoleLogCode(e));
    if(e?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(e?.message==='ADMIN_REQUIRED')return privateJson({ok:false,error:'Accès administrateur refusé.',code:'ADMIN_REQUIRED'},403);
    if(e?.message==='MFA_REQUIRED')return privateJson({ok:false,error:'MFA_REQUIRED',code:'MFA_REQUIRED'},403);
    if(e?.message==='MFA_STATE_UNAVAILABLE')return privateJson({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(e?.message==='JSON_REQUIRED')return privateJson({ok:false,error:'Corps JSON requis.',code:'JSON_REQUIRED'},415);
    if(e?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE'},413);
    if(e?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON'},400);
    if(e?.message==='PLAYTEST_ACCESS_GRANT_FAILED')return privateJson({ok:false,error:'L’accès testeur n’a pas pu être accordé; la décision du participant a été restaurée.',code:'PLAYTEST_ACCESS_GRANT_FAILED'},503);
    if(e?.message==='PLAYTEST_REVIEW_ROLLBACK_FAILED')return privateJson({ok:false,error:'Échec de cohérence lors de la révision du participant.',code:'PLAYTEST_REVIEW_ROLLBACK_FAILED'},500);
    return privateJson({ok:false,error:'Erreur administration SINJIRA.',code:'ADMIN_CONSOLE_FAILED'},500);
  }
});
