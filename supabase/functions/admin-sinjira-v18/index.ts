import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';
import {loadSinjiraCanonContext} from '../_shared/sinjira-canon-context.ts';

async function audit(s:any,userId:string,action:string,entity_type='',entity_id='',summary='',metadata:any={}){try{await s.from('admin_audit_log').insert({admin_user_id:userId,action,entity_type,entity_id:String(entity_id||''),summary,metadata})}catch{}}
async function statusEvent(s:any,submission_id:string,user_id:string,status:string,note=''){try{await s.from('character_status_events').insert({submission_id,user_id,status,note})}catch{}}
async function ctx(req:Request){const user=await requiredUser(req),s=serviceClient();const {data}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});if(!data)throw new Error('ADMIN_REQUIRED');return {user,s}}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,s}=await ctx(req),b=await req.json(),a=String(b.action||'');

    if(a==='dashboard'){
      const [c,sub,rev]=await Promise.all([
        s.from('novel_comments').select('id',{count:'exact',head:true}).eq('status','pending'),
        s.from('character_submissions').select('id',{count:'exact',head:true}),
        s.from('characters').select('id',{count:'exact',head:true}).in('status',['ai_draft','author_review'])
      ]);
      return json({ok:true,dashboard:{pending_comments:c.count||0,character_submissions:sub.count||0,characters_in_review:rev.count||0}});
    }

    if(a==='list_comments'){
      const {data,error}=await s.from('novel_comments').select('id,body,display_name_snapshot,status,contains_spoilers,created_at,novels(title)').eq('status','pending').order('created_at');
      if(error)throw error;
      return json({ok:true,comments:(data||[]).map((x:any)=>({...x,novel_title:x.novels?.title||''}))});
    }

    if(a==='moderate_comment'){
      const decision=b.decision==='approved'?'approved':'refused';
      const {error}=await s.from('novel_comments').update({status:decision,moderated_by:user.id,moderated_at:new Date().toISOString()}).eq('id',b.comment_id);
      if(error)throw error;
      await audit(s,user.id,'moderate_comment','novel_comment',b.comment_id,decision);
      return json({ok:true});
    }

    if(a==='list_submissions'){
      const {data,error}=await s.from('character_submissions').select('id,user_id,account_pseudo,account_email,status,source_payload,photo_path,source_purged_at,created_at').order('created_at',{ascending:false});
      if(error)throw error;
      const rows=[];
      for(const sub of data||[]){
        let photo_url=null;
        if(sub.photo_path){const {data:signed}=await s.storage.from('sinjira-character-sources').createSignedUrl(sub.photo_path,600);photo_url=signed?.signedUrl||null}
        rows.push({...sub,photo_url});
      }
      return json({ok:true,submissions:rows});
    }

    if(a==='create_manual_character'){
      const {data:sub,error}=await s.from('character_submissions').select('*').eq('id',b.submission_id).single();
      if(error)throw error;
      const {data:existing}=await s.from('characters').select('*').eq('user_id',sub.user_id).maybeSingle();
      if(existing)return json({ok:true,character:existing});
      const {data:ch,error:ce}=await s.from('characters').insert({submission_id:sub.id,user_id:sub.user_id,public_name:'À définir',public_description:'Personnage en préparation par Benoit Cantin.',status:'author_review',bible:{source:'Registre des Consciences',mode:'manuel',notes:'À compléter par l’auteur.'},ai_generated:false,visible_to_user:true,canon_status:'PROVISOIRE'}).select('*').single();
      if(ce)throw ce;
      await s.from('character_submissions').update({status:'author_review'}).eq('id',sub.id);
      await statusEvent(s,sub.id,sub.user_id,'author_review','Fiche de personnage créée manuellement par Benoit Cantin.');
      await audit(s,user.id,'create_manual_character','character',ch.id,'Fiche manuelle créée',{submission_id:sub.id});
      return json({ok:true,character:ch});
    }

    if(a==='generate_character'){
      return json({ok:false,error:'IA distante désactivée pendant le mode gratuit.',code:'REMOTE_AI_DISABLED_FREE_ONLY'},503);
    }

    if(a==='system_health'){
      const checks:any={};
      for(const table of ['profiles','game_sessions','novel_comments','character_submissions','characters']){
        const {count,error}=await s.from(table).select('*',{count:'exact',head:true});
        checks[table]={ok:!error,count:count||0,error:error?.message||null};
      }
      return json({ok:true,checks,remote_ai:false,free_only:true});
    }

    if(a==='list_notifications'){
      const {data,error}=await s.from('admin_notifications').select('id,notification_type,title,body,related_user_id,related_entity_type,related_entity_id,read_at,created_at').order('created_at',{ascending:false}).limit(200);
      if(error)throw error;
      const rows=data||[];
      return json({ok:true,notifications:rows,unread:rows.filter((n:any)=>!n.read_at).length});
    }

    if(a==='mark_notification_read'){
      const id=String(b.notification_id||'');if(!id)throw new Error('NOTIFICATION_ID_REQUIRED');
      const {error}=await s.from('admin_notifications').update({read_at:new Date().toISOString()}).eq('id',id);if(error)throw error;
      await audit(s,user.id,'mark_notification_read','admin_notification',id,'Notification marquée comme lue');
      return json({ok:true});
    }

    if(a==='mark_all_notifications_read'){
      const {error}=await s.from('admin_notifications').update({read_at:new Date().toISOString()}).is('read_at',null);if(error)throw error;
      await audit(s,user.id,'mark_all_notifications_read','admin_notification','','Toutes les notifications ont été marquées comme lues');
      return json({ok:true});
    }

    if(a==='audit_log'){
      const {data,error}=await s.from('admin_audit_log').select('*').order('created_at',{ascending:false}).limit(200);if(error)throw error;
      return json({ok:true,rows:data||[]});
    }

    if(a==='purge_submission_source'){
      const {data:sub,error}=await s.from('character_submissions').select('photo_path').eq('id',b.submission_id).single();if(error)throw error;
      if(sub.photo_path)await s.storage.from('sinjira-character-sources').remove([sub.photo_path]);
      const {error:e}=await s.from('character_submissions').update({source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()}).eq('id',b.submission_id);if(e)throw e;
      await audit(s,user.id,'purge_submission_source','character_submission',b.submission_id,'Données sources personnelles supprimées');
      return json({ok:true});
    }

    if(a==='list_characters'){
      const [{data:chars,error},{data:novels}]=await Promise.all([
        s.from('characters').select('*,novels(title)').order('updated_at',{ascending:false}),
        s.from('novels').select('id,title').order('sort_order')
      ]);
      if(error)throw error;
      return json({ok:true,characters:(chars||[]).map((x:any)=>({...x,novel_title:x.novels?.title||''})),novels:novels||[]});
    }

    if(a==='canon_overview'){
      const contexts=await loadSinjiraCanonContext(s);
      return json({ok:true,contexts});
    }

    if(a==='save_character'){
      const c=b.character||{};
      const canonStatus=['PROVISOIRE','CANON','SECRET_AUTEUR','A_ARBITRER'].includes(c.canon_status)?c.canon_status:'PROVISOIRE';
      if(canonStatus==='CANON'&&c.author_confirmed_canon!==true)throw new Error('CANON_CONFIRMATION_REQUIRED');
      if(c.novel_id){const {data:novel}=await s.from('novels').select('slug').eq('id',c.novel_id).maybeSingle();if(novel?.slug==='la-cendre-du-jugement'&&c.author_confirmed_retcon!==true)throw new Error('ROMAN1_LOCKED')}
      const payload={public_name:String(c.public_name||'').slice(0,160),public_description:String(c.public_description||'').slice(0,8000),status:c.status||'author_review',novel_id:c.novel_id||null,novel_note:String(c.novel_note||'').slice(0,500),visible_to_user:Boolean(c.visible_to_user),canon_status:canonStatus,canon_version:String(c.canon_version||'v1.0').slice(0,30),bible:c.bible||{}};
      const {data,error}=await s.from('characters').update(payload).eq('id',c.id).select('*').single();if(error)throw error;
      if(data?.submission_id){await s.from('character_submissions').update({status:payload.status}).eq('id',data.submission_id);await statusEvent(s,data.submission_id,data.user_id,payload.status,payload.novel_id?'Roman attribué / statut mis à jour.':'Statut du personnage mis à jour.')}
      await audit(s,user.id,'save_character','character',data.id,'Personnage mis à jour',{status:payload.status,canon_status:payload.canon_status});
      return json({ok:true,character:data});
    }

    return json({ok:false,error:'Action inconnue.'},400);
  }catch(e){
    console.error(e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(e?.message==='ADMIN_REQUIRED')return json({ok:false,error:'Administration refusée.',code:'ADMIN_REQUIRED'},403);
    if(e?.message==='MFA_REQUIRED')return json({ok:false,error:'MFA_REQUIRED',code:'MFA_REQUIRED'},403);
    if(e?.message==='MFA_STATE_UNAVAILABLE')return json({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(e?.message==='SOURCE_PURGED')return json({ok:false,error:'Les données sources ont déjà été supprimées.'},409);
    if(e?.message==='CANON_CONFIRMATION_REQUIRED')return json({ok:false,error:'Confirmez explicitement que ce personnage est établi par un manuscrit officiel finalisé avant de le passer CANON.'},409);
    if(e?.message==='NOTIFICATION_ID_REQUIRED')return json({ok:false,error:'Identifiant de notification requis.'},400);
    if(e?.message==='ROMAN1_LOCKED')return json({ok:false,error:'Le Roman 1 est verrouillé. Pour y attribuer rétroactivement un nouveau personnage, confirmez explicitement la décision auteur / retcon.'},409);
    return json({ok:false,error:'Erreur administration V18.'},500);
  }
});
