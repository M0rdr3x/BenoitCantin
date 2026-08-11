import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

async function adminContext(req:Request){
  const user=await requiredUser(req),service=serviceClient();
  const {data}=await service.from('internal_admin_users').select('user_id').eq('user_id',user.id).maybeSingle();
  if(!data)throw new Error('ADMIN_REQUIRED');
  return {user,service};
}
function safeName(v:string){
  return String(v||'document').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()
    .replace(/[^a-z0-9._-]+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,120)||'document';
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,service}=await adminContext(req);
    const body=await req.json(),action=String(body?.action||'');

    if(action==='dashboard'){
      const [users,projects,documents,requests,playtests,contributions]=await Promise.all([
        service.auth.admin.listUsers({page:1,perPage:1000}),
        service.from('projects').select('id',{count:'exact',head:true}),
        service.from('documents').select('id',{count:'exact',head:true}).eq('status','approved'),
        service.from('access_requests').select('id',{count:'exact',head:true}).eq('status','pending'),
        service.from('playtests').select('id',{count:'exact',head:true}).in('status',['open','active']),
        service.from('internal_gameplay_contributions').select('id',{count:'exact',head:true})
      ]);
      return json({ok:true,dashboard:{
        users:users.data?.users?.length||0,projects:projects.count||0,approved_documents:documents.count||0,
        pending_requests:requests.count||0,open_playtests:playtests.count||0,contributions:contributions.count||0
      }});
    }

    if(action==='list_projects'){
      const {data,error}=await service.from('projects').select('*').order('sort_order');
      if(error)throw error;return json({ok:true,projects:data||[]});
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
      if(!payload.slug||!payload.name)return json({ok:false,error:'Nom et slug requis.'},400);
      const {data,error}=await service.from('projects').upsert(payload).select('*').single();
      if(error)throw error;return json({ok:true,project:data});
    }

    if(action==='list_documents'){
      const {data,error}=await service.from('documents').select('*,projects(name,slug)').order('created_at',{ascending:false});
      if(error)throw error;return json({ok:true,documents:data||[]});
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
      return json({ok:true,document:row,upload:{path,token:upload.token,bucket}});
    }

    if(action==='finalize_document'||action==='set_document_status'){
      const documentId=body.document_id,desired=action==='finalize_document'
        ?(['review','approved'].includes(body.status)?body.status:'review')
        :body.status;
      if(!['draft','review','approved','archived'].includes(desired))return json({ok:false,error:'Statut invalide.'},400);
      const update:any={status:desired};
      if(desired==='approved'){update.approved_by=user.id;update.approved_at=new Date().toISOString()}
      const {data,error}=await service.from('documents').update(update).eq('id',documentId).select('*').single();
      if(error)throw error;return json({ok:true,document:data});
    }

    if(action==='list_access_requests'){
      const {data,error}=await service.from('access_requests').select('*,projects(name,slug)').order('created_at',{ascending:false});
      if(error)throw error;
      const ids=[...new Set((data||[]).map((x:any)=>x.user_id))],users:any[]=[];
      for(const id of ids){const {data:u}=await service.auth.admin.getUserById(id);if(u?.user)users.push({id,email:u.user.email})}
      return json({ok:true,requests:data||[],users});
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
      }).eq('id',r.id);if(error)throw error;return json({ok:true});
    }

    if(action==='list_users'){
      const {data:authData,error:authError}=await service.auth.admin.listUsers({page:1,perPage:1000});if(authError)throw authError;
      const [{data:profiles},{data:access}]=await Promise.all([
        service.from('profiles').select('*'),service.from('project_access').select('*,projects(name,slug)')
      ]);
      const pmap=new Map((profiles||[]).map((p:any)=>[p.user_id,p]));
      const adminIds=new Set((await service.from('internal_admin_users').select('user_id')).data?.map((a:any)=>a.user_id)||[]);
      return json({ok:true,users:(authData.users||[]).map((u:any)=>({
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
      if(error)throw error;return json({ok:true});
    }

    if(action==='revoke_access'){
      const {error}=await service.from('project_access').delete().eq('user_id',body.user_id).eq('project_id',body.project_id);
      if(error)throw error;return json({ok:true});
    }

    if(action==='list_playtests'){
      const {data,error}=await service.from('playtests').select('*,projects(name,slug),playtest_participants(*)').order('created_at',{ascending:false});
      if(error)throw error;return json({ok:true,playtests:data||[]});
    }

    if(action==='save_playtest'){
      const p=body.playtest||{},payload:any={
        project_id:p.project_id,title:String(p.title||'').trim(),description:String(p.description||'').slice(0,5000),
        status:p.status||'draft',required_access:p.required_access||'tester',
        starts_at:p.starts_at||null,ends_at:p.ends_at||null,max_participants:Number(p.max_participants||0)||null,created_by:user.id
      };
      if(p.id)payload.id=p.id;
      const {data,error}=await service.from('playtests').upsert(payload).select('*').single();
      if(error)throw error;return json({ok:true,playtest:data});
    }

    if(action==='review_playtest_participant'){
      const state=['approved','refused','completed'].includes(body.status)?body.status:'refused';
      const {data:row,error:findError}=await service.from('playtest_participants').select('*,playtests(project_id)')
        .eq('playtest_id',body.playtest_id).eq('user_id',body.user_id).single();if(findError)throw findError;
      const {error}=await service.from('playtest_participants').update({
        status:state,reviewed_by:user.id,reviewed_at:new Date().toISOString()
      }).eq('playtest_id',body.playtest_id).eq('user_id',body.user_id);if(error)throw error;
      if(state==='approved'){
        await service.from('project_access').upsert({
          user_id:body.user_id,project_id:row.playtests.project_id,access_level:'tester',granted_by:user.id,source:'playtest'
        },{onConflict:'user_id,project_id'});
      }
      return json({ok:true});
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
      return json({ok:true,extensions:extensions||[],signals});
    }

    if(action==='save_extension'){
      const e=body.extension||{},payload:any={
        project_id:e.project_id,title:String(e.title||'').trim(),description:String(e.description||'').slice(0,10000),
        status:e.status||'idea',is_public:Boolean(e.is_public),created_by:user.id
      };
      if(e.id)payload.id=e.id;
      const {data,error}=await service.from('extensions').upsert(payload).select('*').single();
      if(error)throw error;return json({ok:true,extension:data});
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
      return json({ok:true,analytics:byGame});
    }

    return json({ok:false,error:'Action inconnue.'},400);
  }catch(e){
    console.error(e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(e?.message==='ADMIN_REQUIRED')return json({ok:false,error:'Accès administrateur refusé.'},403);
    return json({ok:false,error:'Erreur administration SINJIRA.'},500);
  }
});
