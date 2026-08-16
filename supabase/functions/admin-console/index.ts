import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

const PROJECT_TYPES=new Set(['game','experience','tool','other']);
const PROJECT_STATUSES=new Set(['draft','development','testing','active','archived']);
const PROJECT_VISIBILITIES=new Set(['public','account','restricted']);
const ACCESS_LEVELS=new Set(['player','tester']);
const DOCUMENT_STATUSES=new Set(['draft','review','approved','archived']);
const DOCUMENT_ACCESS=new Set(['public','account','player','tester','admin']);
const PLAYTEST_STATUSES=new Set(['draft','open','active','closed','archived']);
const PLAYTEST_ACCESS=new Set(['account','player','tester']);
const PARTICIPANT_REVIEW_STATUSES=new Set(['approved','refused','completed']);
const EXTENSION_STATUSES=new Set(['idea','research','design','testing','approved','released','archived']);
const MIME_EXT:Record<string,string>={
  'application/pdf':'pdf','application/zip':'zip','image/png':'png','image/jpeg':'jpg','image/webp':'webp','text/plain':'txt'
};
const MAX_PRIVATE_DOCUMENT_BYTES=50*1024*1024;

async function adminContext(req:Request){
  const user=await requiredUser(req),service=serviceClient();
  const {data,error}=await service.rpc('is_sinjira_admin',{p_user_id:user.id});
  if(error||!data)throw new Error('ADMIN_REQUIRED');
  return {user,service};
}
function text(v:unknown,max=5000){return String(v??'').trim().slice(0,max)}
function slug(v:unknown){const s=text(v,80).toLowerCase();if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(s))throw new Error('INVALID_SLUG');return s}
function uuid(v:unknown){const s=String(v||'').trim();if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(s))throw new Error('INVALID_UUID');return s}
function int(v:unknown,min:number,max:number,fallback:number|null=null){const n=Number(v);if(!Number.isFinite(n)||!Number.isInteger(n))return fallback;if(n<min||n>max)throw new Error('INVALID_NUMBER');return n}
function enumValue(v:unknown,allowed:Set<string>,fallback?:string){const s=String(v||fallback||'');if(!allowed.has(s))throw new Error('INVALID_ENUM');return s}
function safeName(v:unknown){return text(v,120).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9._-]+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,100)||'document'}
function localPath(v:unknown){const s=text(v,500);if(!s)return null;if(!s.startsWith('/')||s.startsWith('//')||/[\u0000-\u001f\\]/.test(s))throw new Error('INVALID_PATH');return s}
function safeMediaUrl(v:unknown){const s=text(v,500);if(!s)return null;if(s.startsWith('/')&&!s.startsWith('//')&&!/[\u0000-\u001f\\]/.test(s))return s;try{const u=new URL(s);if(u.protocol==='https:')return u.toString()}catch{}throw new Error('INVALID_URL')}
function isoDate(v:unknown){const s=text(v,80);if(!s)return null;const d=new Date(s);if(Number.isNaN(d.getTime()))throw new Error('INVALID_DATE');return d.toISOString()}
async function audit(service:any,userId:string,action:string,entityType:string,entityId:unknown,summary:string,metadata:Record<string,unknown>={}){
  const {error}=await service.from('admin_audit_log').insert({admin_user_id:userId,action,entity_type:entityType,entity_id:String(entityId||''),summary:text(summary,500),metadata});
  if(error)console.warn('[SINJIRA admin audit]',action,error.message);
}
async function projectExists(service:any,id:string){const {data,error}=await service.from('projects').select('id,slug,name').eq('id',id).maybeSingle();if(error)throw error;if(!data)throw new Error('PROJECT_NOT_FOUND');return data}
async function storageObjectExists(service:any,bucket:string,path:string){
  const parts=path.split('/').filter(Boolean),name=parts.pop();if(!name)return false;const folder=parts.join('/');
  const {data,error}=await service.storage.from(bucket).list(folder,{limit:100,search:name});
  if(error)throw new Error('STORAGE_CHECK_FAILED');
  return (data||[]).some((x:any)=>x.name===name);
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,service}=await adminContext(req);
    const body=await req.json().catch(()=>({})),action=String(body?.action||'');

    if(action==='dashboard'){
      const [users,projects,documents,requests,playtests,contributions]=await Promise.all([
        service.auth.admin.listUsers({page:1,perPage:1000}),
        service.from('projects').select('id',{count:'exact',head:true}),
        service.from('documents').select('id',{count:'exact',head:true}).eq('status','approved'),
        service.from('access_requests').select('id',{count:'exact',head:true}).eq('status','pending'),
        service.from('playtests').select('id',{count:'exact',head:true}).in('status',['open','active']),
        service.from('internal_gameplay_contributions').select('id',{count:'exact',head:true})
      ]);
      const error=users.error||projects.error||documents.error||requests.error||playtests.error||contributions.error;if(error)throw error;
      return json({ok:true,dashboard:{users:users.data?.users?.length||0,projects:projects.count||0,approved_documents:documents.count||0,pending_requests:requests.count||0,open_playtests:playtests.count||0,contributions:contributions.count||0}});
    }

    if(action==='list_projects'){
      const {data,error}=await service.from('projects').select('*').order('sort_order');if(error)throw error;return json({ok:true,projects:data||[]});
    }

    if(action==='save_project'){
      const p=body.project||{},id=p.id?uuid(p.id):null,payload={
        slug:slug(p.slug),name:text(p.name,180),type:enumValue(p.type,PROJECT_TYPES,'game'),
        status:enumValue(p.status,PROJECT_STATUSES,'development'),visibility:enumValue(p.visibility,PROJECT_VISIBILITIES,'account'),
        description:text(p.description,5000),cover_url:safeMediaUrl(p.cover_url),public_path:localPath(p.public_path),play_path:localPath(p.play_path),
        allow_tester_requests:p.allow_tester_requests!==false,sort_order:int(p.sort_order,0,100000,100)??100
      };
      if(payload.name.length<2)throw new Error('NAME_REQUIRED');
      let result;
      if(id){const {data,error}=await service.from('projects').update(payload).eq('id',id).select('*').single();if(error)throw error;result=data}
      else{const {data,error}=await service.from('projects').insert(payload).select('*').single();if(error)throw error;result=data}
      await audit(service,user.id,'save_project','project',result.id,`Projet ${result.name} enregistré`,{slug:result.slug,status:result.status,visibility:result.visibility});
      return json({ok:true,project:result});
    }

    if(action==='list_documents'){
      const {data,error}=await service.from('documents').select('*,projects(name,slug)').order('created_at',{ascending:false});if(error)throw error;return json({ok:true,documents:data||[]});
    }

    if(action==='prepare_document_upload'){
      const x=body.document||{},projectId=uuid(x.project_id),project=await projectExists(service,projectId),title=text(x.title,220),mime=text(x.mime_type,100).toLowerCase();
      if(title.length<2)throw new Error('TITLE_REQUIRED');
      const ext=MIME_EXT[mime];if(!ext)throw new Error('INVALID_MIME');
      const size=int(x.file_size_bytes,1,MAX_PRIVATE_DOCUMENT_BYTES,null);if(size==null)throw new Error('INVALID_FILE_SIZE');
      const bucket='sinjira-private-documents',path=`${project.slug}/${crypto.randomUUID()}/${safeName(title)}.${ext}`;
      const {data:upload,error:uploadError}=await service.storage.from(bucket).createSignedUploadUrl(path);if(uploadError||!upload?.token)throw uploadError||new Error('UPLOAD_TOKEN_MISSING');
      const {data:row,error:rowError}=await service.from('documents').insert({
        project_id:projectId,title,description:text(x.description,5000),document_type:text(x.document_type||'document',100)||'document',
        version:text(x.version||'1.0',50)||'1.0',status:'draft',access_level:enumValue(x.access_level,DOCUMENT_ACCESS,'account'),
        storage_bucket:bucket,storage_path:path,mime_type:mime,file_size_bytes:size,sort_order:int(x.sort_order,0,100000,100)??100,created_by:user.id
      }).select('*').single();
      if(rowError){await service.storage.from(bucket).remove([path]).catch(()=>{});throw rowError}
      await audit(service,user.id,'prepare_document_upload','document',row.id,`Téléversement préparé : ${title}`,{project_id:projectId,mime_type:mime,file_size_bytes:size});
      return json({ok:true,document:row,upload:{path,token:upload.token,bucket}});
    }

    if(action==='finalize_document'||action==='set_document_status'){
      const documentId=uuid(body.document_id),desired=action==='finalize_document'?enumValue(body.status,new Set(['review','approved']),'review'):enumValue(body.status,DOCUMENT_STATUSES);
      const {data:current,error:currentError}=await service.from('documents').select('*').eq('id',documentId).single();if(currentError)throw currentError;
      if(desired==='approved'&&current.storage_path){
        const exists=await storageObjectExists(service,current.storage_bucket||'sinjira-private-documents',current.storage_path);if(!exists)throw new Error('DOCUMENT_FILE_MISSING');
      }
      const update:any={status:desired};
      if(desired==='approved'){update.approved_by=user.id;update.approved_at=new Date().toISOString()}
      else{update.approved_by=null;update.approved_at=null}
      const {data,error}=await service.from('documents').update(update).eq('id',documentId).select('*').single();if(error)throw error;
      await audit(service,user.id,'set_document_status','document',documentId,`Document passé à ${desired}`,{previous_status:current.status,status:desired});
      return json({ok:true,document:data});
    }

    if(action==='list_access_requests'){
      const {data,error}=await service.from('access_requests').select('*,projects(name,slug)').order('created_at',{ascending:false});if(error)throw error;
      const ids=[...new Set((data||[]).map((x:any)=>x.user_id).filter(Boolean))],users:any[]=[];
      for(const id of ids){const {data:u,error:e}=await service.auth.admin.getUserById(id);if(e)continue;if(u?.user)users.push({id,email:u.user.email})}
      return json({ok:true,requests:data||[],users});
    }

    if(action==='review_access_request'){
      const requestId=uuid(body.request_id),decision=body.decision==='approved'?'approved':body.decision==='refused'?'refused':null;if(!decision)throw new Error('INVALID_DECISION');
      const {data:r,error:rerr}=await service.from('access_requests').select('*').eq('id',requestId).single();if(rerr)throw rerr;if(r.status!=='pending')throw new Error('REQUEST_ALREADY_REVIEWED');
      if(decision==='approved'){
        const level=enumValue(r.requested_level,ACCESS_LEVELS);
        const {error}=await service.from('project_access').upsert({user_id:r.user_id,project_id:r.project_id,access_level:level,granted_by:user.id,source:'request'},{onConflict:'user_id,project_id'});if(error)throw error;
      }
      const {data:reviewed,error}=await service.from('access_requests').update({status:decision,reviewed_by:user.id,reviewed_at:new Date().toISOString(),review_note:text(body.review_note,1500)}).eq('id',r.id).eq('status','pending').select('id').single();if(error)throw error;
      await audit(service,user.id,'review_access_request','access_request',reviewed.id,`Demande ${decision}`,{user_id:r.user_id,project_id:r.project_id,requested_level:r.requested_level});
      return json({ok:true});
    }

    if(action==='list_users'){
      const {data:authData,error:authError}=await service.auth.admin.listUsers({page:1,perPage:1000});if(authError)throw authError;
      const [profilesRes,accessRes,adminsRes]=await Promise.all([service.from('profiles').select('*'),service.from('project_access').select('*,projects(name,slug)'),service.from('internal_admin_users').select('user_id')]);
      const err=profilesRes.error||accessRes.error||adminsRes.error;if(err)throw err;
      const pmap=new Map((profilesRes.data||[]).map((p:any)=>[p.user_id,p])),adminIds=new Set((adminsRes.data||[]).map((a:any)=>a.user_id)),byUser=new Map<string,any[]>();
      for(const item of accessRes.data||[]){const rows=byUser.get(item.user_id)||[];rows.push(item);byUser.set(item.user_id,rows)}
      return json({ok:true,users:(authData.users||[]).map((u:any)=>({id:u.id,email:u.email,created_at:u.created_at,last_sign_in_at:u.last_sign_in_at,pseudo:pmap.get(u.id)?.pseudo||'',display_name:pmap.get(u.id)?.display_name||'',avatar_path:pmap.get(u.id)?.avatar_path||null,is_admin:adminIds.has(u.id),access:byUser.get(u.id)||[]}))});
    }

    if(action==='grant_access'){
      const userId=uuid(body.user_id),projectId=uuid(body.project_id),level=enumValue(body.access_level,ACCESS_LEVELS,'player');await projectExists(service,projectId);
      const {data:target,error:targetError}=await service.auth.admin.getUserById(userId);if(targetError||!target?.user)throw new Error('USER_NOT_FOUND');
      const {error}=await service.from('project_access').upsert({user_id:userId,project_id:projectId,access_level:level,granted_by:user.id,source:'manual'},{onConflict:'user_id,project_id'});if(error)throw error;
      await audit(service,user.id,'grant_access','project_access',`${userId}:${projectId}`,`Accès ${level} accordé`,{user_id:userId,project_id:projectId,access_level:level});return json({ok:true});
    }

    if(action==='revoke_access'){
      const userId=uuid(body.user_id),projectId=uuid(body.project_id);const {error}=await service.from('project_access').delete().eq('user_id',userId).eq('project_id',projectId);if(error)throw error;
      await audit(service,user.id,'revoke_access','project_access',`${userId}:${projectId}`,'Accès projet retiré',{user_id:userId,project_id:projectId});return json({ok:true});
    }

    if(action==='list_playtests'){
      const {data,error}=await service.from('playtests').select('*,projects(name,slug),playtest_participants(*)').order('created_at',{ascending:false});if(error)throw error;return json({ok:true,playtests:data||[]});
    }

    if(action==='save_playtest'){
      const p=body.playtest||{},id=p.id?uuid(p.id):null,projectId=uuid(p.project_id),title=text(p.title,220),starts=isoDate(p.starts_at),ends=isoDate(p.ends_at);if(title.length<2)throw new Error('TITLE_REQUIRED');await projectExists(service,projectId);
      if(starts&&ends&&new Date(ends)<=new Date(starts))throw new Error('INVALID_DATE_RANGE');
      const payload:any={project_id:projectId,title,description:text(p.description,5000),status:enumValue(p.status,PLAYTEST_STATUSES,'draft'),required_access:enumValue(p.required_access,PLAYTEST_ACCESS,'tester'),starts_at:starts,ends_at:ends,max_participants:p.max_participants==null||p.max_participants===''?null:int(p.max_participants,1,10000,null)};
      let row;if(id){const {data,error}=await service.from('playtests').update(payload).eq('id',id).select('*').single();if(error)throw error;row=data}else{payload.created_by=user.id;const {data,error}=await service.from('playtests').insert(payload).select('*').single();if(error)throw error;row=data}
      await audit(service,user.id,'save_playtest','playtest',row.id,`Playtest ${row.title} enregistré`,{status:row.status,project_id:row.project_id});return json({ok:true,playtest:row});
    }

    if(action==='review_playtest_participant'){
      const playtestId=uuid(body.playtest_id),targetUserId=uuid(body.user_id),state=enumValue(body.status,PARTICIPANT_REVIEW_STATUSES);
      const {data:row,error:findError}=await service.from('playtest_participants').select('status,playtests(project_id,max_participants)').eq('playtest_id',playtestId).eq('user_id',targetUserId).single();if(findError)throw findError;
      const projectId=row.playtests?.project_id;if(!projectId)throw new Error('PROJECT_NOT_FOUND');
      if(state==='approved'&&Number(row.playtests?.max_participants)>0){const {count,error}=await service.from('playtest_participants').select('user_id',{head:true,count:'exact'}).eq('playtest_id',playtestId).eq('status','approved').neq('user_id',targetUserId);if(error)throw error;if((count||0)>=Number(row.playtests.max_participants))throw new Error('PLAYTEST_FULL')}
      const {error}=await service.from('playtest_participants').update({status:state,reviewed_by:user.id,reviewed_at:new Date().toISOString()}).eq('playtest_id',playtestId).eq('user_id',targetUserId);if(error)throw error;
      if(state==='approved'){
        const {data:existing,error:existingError}=await service.from('project_access').select('access_level,source').eq('user_id',targetUserId).eq('project_id',projectId).maybeSingle();if(existingError)throw existingError;
        if(existing?.access_level!=='tester'){
          const {error:grantError}=await service.from('project_access').upsert({user_id:targetUserId,project_id:projectId,access_level:'tester',granted_by:user.id,source:'playtest'},{onConflict:'user_id,project_id'});if(grantError)throw grantError;
        }
      }
      await audit(service,user.id,'review_playtest_participant','playtest_participant',`${playtestId}:${targetUserId}`,`Participant ${state}`,{playtest_id:playtestId,user_id:targetUserId,project_id:projectId});return json({ok:true});
    }

    if(action==='list_extensions'){
      const [extensionsRes,signalsRes]=await Promise.all([service.from('extensions').select('*,projects(name,slug)').order('created_at',{ascending:false}),service.from('internal_gameplay_contributions').select('game_slug,feedback,created_at').order('created_at',{ascending:false}).limit(2000)]);if(extensionsRes.error||signalsRes.error)throw extensionsRes.error||signalsRes.error;
      const signals=(signalsRes.data||[]).map((r:any)=>({game_slug:r.game_slug,idea:text(r.feedback?.extension_idea,2000),favorite:text(r.feedback?.favorite_mechanic,1000),unclear:text(r.feedback?.unclear_text,2000),created_at:r.created_at})).filter((x:any)=>x.idea||x.favorite||x.unclear);
      return json({ok:true,extensions:extensionsRes.data||[],signals});
    }

    if(action==='save_extension'){
      const e=body.extension||{},id=e.id?uuid(e.id):null,projectId=uuid(e.project_id),title=text(e.title,220);if(title.length<2)throw new Error('TITLE_REQUIRED');await projectExists(service,projectId);
      const payload:any={project_id:projectId,title,description:text(e.description,10000),status:enumValue(e.status,EXTENSION_STATUSES,'idea'),is_public:Boolean(e.is_public)};
      let row;if(id){const {data,error}=await service.from('extensions').update(payload).eq('id',id).select('*').single();if(error)throw error;row=data}else{payload.created_by=user.id;const {data,error}=await service.from('extensions').insert(payload).select('*').single();if(error)throw error;row=data}
      await audit(service,user.id,'save_extension','extension',row.id,`Extension ${row.title} enregistrée`,{status:row.status,is_public:row.is_public});return json({ok:true,extension:row});
    }

    if(action==='analytics'){
      const {data:rows=[],error}=await service.from('internal_gameplay_contributions').select('game_slug,metrics,feedback,created_at').order('created_at',{ascending:false}).limit(10000);if(error)throw error;const byGame:any={};
      for(const r of rows){const k=text(r.game_slug,80)||'inconnu',m=r.metrics||{},f=r.feedback||{};byGame[k]||={count:0,players:0,pc:0,duration:0,dc:0,ratings:0,rc:0,difficulty:{}};const g=byGame[k];g.count++;
        const players=Number(m.human_player_count??m.player_count);if(Number.isFinite(players)&&players>0&&players<=20){g.players+=players;g.pc++}
        const duration=Number(m.duration_minutes);if(Number.isFinite(duration)&&duration>=0&&duration<=1440){g.duration+=duration;g.dc++}
        const rating=Number(f.rating);if(Number.isFinite(rating)&&rating>0&&rating<=5){g.ratings+=rating;g.rc++}
        if(f.difficulty){const d=text(f.difficulty,120);g.difficulty[d]=(g.difficulty[d]||0)+1}}
      for(const g of Object.values(byGame) as any[]){g.average_players=g.pc?Math.round(g.players/g.pc*10)/10:null;g.average_duration=g.dc?Math.round(g.duration/g.dc):null;g.average_rating=g.rc?Math.round(g.ratings/g.rc*10)/10:null;delete g.players;delete g.pc;delete g.duration;delete g.dc;delete g.ratings;delete g.rc}
      return json({ok:true,analytics:byGame});
    }

    return json({ok:false,error:'Action inconnue.'},400);
  }catch(e){
    console.error('[SINJIRA admin console]',e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(e?.message==='ADMIN_REQUIRED')return json({ok:false,error:'Accès administrateur refusé.'},403);
    if(e?.message==='INVALID_SLUG')return json({ok:false,error:'Identifiant technique invalide.'},400);
    if(e?.message==='INVALID_UUID'||e?.message==='INVALID_ENUM'||e?.message==='INVALID_NUMBER'||e?.message==='INVALID_DATE'||e?.message==='INVALID_PATH'||e?.message==='INVALID_URL')return json({ok:false,error:'Une valeur transmise à la console est invalide.'},400);
    if(e?.message==='INVALID_DATE_RANGE')return json({ok:false,error:'La date de fin doit être postérieure à la date de début.'},400);
    if(e?.message==='INVALID_MIME'||e?.message==='INVALID_FILE_SIZE')return json({ok:false,error:'Type ou taille de document non autorisé.'},400);
    if(e?.message==='NAME_REQUIRED'||e?.message==='TITLE_REQUIRED')return json({ok:false,error:'Le nom ou le titre est requis.'},400);
    if(e?.message==='PROJECT_NOT_FOUND')return json({ok:false,error:'Projet introuvable.'},404);
    if(e?.message==='USER_NOT_FOUND')return json({ok:false,error:'Compte joueur introuvable.'},404);
    if(e?.message==='DOCUMENT_FILE_MISSING')return json({ok:false,error:'Le fichier privé n’est pas présent dans le stockage; le document ne peut pas être approuvé.'},409);
    if(e?.message==='STORAGE_CHECK_FAILED')return json({ok:false,error:'Le stockage privé ne peut pas être vérifié pour le moment.'},502);
    if(e?.message==='REQUEST_ALREADY_REVIEWED')return json({ok:false,error:'Cette demande a déjà été traitée.'},409);
    if(e?.message==='INVALID_DECISION')return json({ok:false,error:'Décision de demande invalide.'},400);
    if(e?.message==='PLAYTEST_FULL')return json({ok:false,error:'Le nombre maximal de participants approuvés est déjà atteint.'},409);
    return json({ok:false,error:'Erreur administration SINJIRA.'},500);
  }
});
