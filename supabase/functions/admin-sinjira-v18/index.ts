import {corsHeaders} from '../_shared/cors.ts';
import {requiredAdmin} from '../_shared/auth.ts';
import {loadSinjiraCanonContext} from '../_shared/sinjira-canon-context.ts';

const MAX_REQUEST_BYTES=262144;
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
  'JSON_REQUIRED','REQUEST_TOO_LARGE','INVALID_JSON','SOURCE_PURGED',
  'SOURCE_PURGE_CONFIRMATION_REQUIRED','SOURCE_PURGE_STORAGE_FAILED',
  'CANON_CONFIRMATION_REQUIRED','EXTENDED_CANON_CONFIRMATION_REQUIRED','STORY_CONTINUITY_CONFLICT','STORY_CONTINUITY_INCOMPLETE','NOTIFICATION_ID_REQUIRED','CENTRAL_CANON_LOCKED'
]);

function privateJson(data:unknown,status=200){
  return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS});
}

function adminV18LogCode(error:unknown){
  const code=error instanceof Error?error.message:'';
  return SAFE_LOG_CODES.has(code)?code:'ADMIN_V18_BACKEND_FAILED';
}

async function readBoundedJson(req:Request){
  const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(contentType!=='application/json')throw new Error('JSON_REQUIRED');
  const declaredRaw=req.headers.get('content-length');
  if(declaredRaw){
    const declared=Number(declaredRaw);
    if(Number.isFinite(declared)&&declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  }
  const raw=await req.text();
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  let body:unknown;
  try{body=JSON.parse(raw)}catch{throw new Error('INVALID_JSON')}
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body as Record<string,any>;
}

async function audit(s:any,userId:string,action:string,entity_type='',entity_id='',summary='',metadata:any={}){try{await s.from('admin_audit_log').insert({admin_user_id:userId,action,entity_type,entity_id:String(entity_id||''),summary,metadata})}catch{}}
async function statusEvent(s:any,submission_id:string,user_id:string,status:string,note=''){try{await s.from('character_status_events').insert({submission_id,user_id,status,note})}catch{}}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.',code:'METHOD_NOT_ALLOWED'},405);
  try{
    const {user,service:s}=await requiredAdmin(req);
    const b=await readBoundedJson(req),a=String(b.action||'');

    if(a==='dashboard'){
      const [c,sub,rev]=await Promise.all([
        s.from('novel_comments').select('id',{count:'exact',head:true}).eq('status','pending'),
        s.from('character_submissions').select('id',{count:'exact',head:true}),
        s.from('characters').select('id',{count:'exact',head:true}).in('status',['ai_draft','author_review'])
      ]);
      return privateJson({ok:true,dashboard:{pending_comments:c.count||0,character_submissions:sub.count||0,characters_in_review:rev.count||0}});
    }

    if(a==='list_comments'){
      const {data,error}=await s.from('novel_comments').select('id,body,display_name_snapshot,status,contains_spoilers,created_at,novels(title)').eq('status','pending').order('created_at');
      if(error)throw error;
      return privateJson({ok:true,comments:(data||[]).map((x:any)=>({...x,novel_title:x.novels?.title||''}))});
    }

    if(a==='moderate_comment'){
      const decision=b.decision==='approved'?'approved':'refused';
      const {error}=await s.from('novel_comments').update({status:decision,moderated_by:user.id,moderated_at:new Date().toISOString()}).eq('id',b.comment_id);
      if(error)throw error;
      await audit(s,user.id,'moderate_comment','novel_comment',b.comment_id,decision);
      return privateJson({ok:true});
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
      return privateJson({ok:true,submissions:rows});
    }

    if(a==='create_manual_character'){
      const {data:sub,error}=await s.from('character_submissions').select('*').eq('id',b.submission_id).single();
      if(error)throw error;
      const {data:existing}=await s.from('characters').select('*').eq('user_id',sub.user_id).maybeSingle();
      if(existing)return privateJson({ok:true,character:existing});
      const {data:ch,error:ce}=await s.from('characters').insert({submission_id:sub.id,user_id:sub.user_id,public_name:'À définir',public_description:'Personnage en préparation par Benoit Cantin.',status:'author_review',bible:{source:'Registre des Consciences',mode:'manuel',notes:'À compléter par l’auteur.'},ai_generated:false,visible_to_user:true,canon_status:'PROVISOIRE'}).select('*').single();
      if(ce)throw ce;
      await s.from('character_submissions').update({status:'author_review'}).eq('id',sub.id);
      await statusEvent(s,sub.id,sub.user_id,'author_review','Fiche de personnage créée manuellement par Benoit Cantin.');
      await audit(s,user.id,'create_manual_character','character',ch.id,'Fiche manuelle créée',{submission_id:sub.id});
      return privateJson({ok:true,character:ch});
    }

    if(a==='generate_character'){
      return privateJson({ok:false,error:'IA distante désactivée pendant le mode gratuit.',code:'REMOTE_AI_DISABLED_FREE_ONLY'},503);
    }

    if(a==='system_health'){
      const checks:any={};
      for(const table of ['profiles','game_sessions','novel_comments','character_submissions','characters','sinjira_extended_stories','sinjira_world_locations','sinjira_canon_events']){
        const {count,error}=await s.from(table).select('*',{count:'exact',head:true});
        checks[table]={ok:!error,count:count||0,code:error?'CHECK_FAILED':null};
      }
      return privateJson({ok:true,checks,remote_ai:false,free_only:true});
    }

    if(a==='list_notifications'){
      const {data,error}=await s.from('admin_notifications').select('id,notification_type,title,body,related_user_id,related_entity_type,related_entity_id,read_at,created_at').order('created_at',{ascending:false}).limit(200);
      if(error)throw error;
      const rows=data||[];
      return privateJson({ok:true,notifications:rows,unread:rows.filter((n:any)=>!n.read_at).length});
    }

    if(a==='mark_notification_read'){
      const id=String(b.notification_id||'');if(!id)throw new Error('NOTIFICATION_ID_REQUIRED');
      const {error}=await s.from('admin_notifications').update({read_at:new Date().toISOString()}).eq('id',id);if(error)throw error;
      await audit(s,user.id,'mark_notification_read','admin_notification',id,'Notification marquée comme lue');
      return privateJson({ok:true});
    }

    if(a==='mark_all_notifications_read'){
      const {error}=await s.from('admin_notifications').update({read_at:new Date().toISOString()}).is('read_at',null);if(error)throw error;
      await audit(s,user.id,'mark_all_notifications_read','admin_notification','','Toutes les notifications ont été marquées comme lues');
      return privateJson({ok:true});
    }

    if(a==='audit_log'){
      const {data,error}=await s.from('admin_audit_log').select('*').order('created_at',{ascending:false}).limit(200);if(error)throw error;
      return privateJson({ok:true,rows:data||[]});
    }

    if(a==='purge_submission_source'){
      if(b.author_confirmed_source_purge!==true)throw new Error('SOURCE_PURGE_CONFIRMATION_REQUIRED');
      const {data:sub,error}=await s.from('character_submissions').select('photo_path,source_purged_at').eq('id',b.submission_id).single();if(error)throw error;
      if(sub.source_purged_at)throw new Error('SOURCE_PURGED');
      if(sub.photo_path){
        const {error:storageError}=await s.storage.from('sinjira-character-sources').remove([sub.photo_path]);
        if(storageError)throw new Error('SOURCE_PURGE_STORAGE_FAILED');
      }
      const {error:e}=await s.from('character_submissions').update({source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()}).eq('id',b.submission_id);if(e)throw e;
      await audit(s,user.id,'purge_submission_source','character_submission',b.submission_id,'Données sources personnelles supprimées');
      return privateJson({ok:true});
    }

    if(a==='list_characters'){
      const [{data:chars,error},{data:novels}]=await Promise.all([
        s.from('characters').select('*,novels(title)').order('updated_at',{ascending:false}),
        s.from('novels').select('id,title').order('sort_order')
      ]);
      if(error)throw error;
      return privateJson({ok:true,characters:(chars||[]).map((x:any)=>({...x,novel_title:x.novels?.title||''})),novels:novels||[]});
    }

    if(a==='canon_overview'){
      const contexts=await loadSinjiraCanonContext(s);
      return privateJson({ok:true,contexts});
    }

    if(a==='list_extended_stories'){
      const {data,error}=await s.from('sinjira_extended_stories')
        .select('*,characters(public_name),sinjira_world_locations(name,slug),sinjira_story_character_presence(*,characters(public_name),sinjira_world_locations(name,slug))')
        .order('updated_at',{ascending:false});
      if(error)throw error;
      return privateJson({ok:true,stories:(data||[]).map((x:any)=>({...x,character_name:x.characters?.public_name||'',location_name_canon:x.sinjira_world_locations?.name||''}))});
    }

    if(a==='save_extended_story_segment'){
      const x=b.segment||{};
      if(!x.story_id||!x.character_id)return privateJson({ok:false,error:'Chronique et personnage requis pour un segment.',code:'SEGMENT_REQUIRED'},400);
      const {data:story,error:storyError}=await s.from('sinjira_extended_stories').select('id,status').eq('id',x.story_id).maybeSingle();if(storyError)throw storyError;if(!story)return privateJson({ok:false,error:'Chronique introuvable.',code:'STORY_NOT_FOUND'},404);if(story.status==='published')throw new Error('STORY_UNPUBLISH_FIRST');
      const kinds=['scene','travel','reference'],certainties=['confirmed','approximate','unknown'];
      const segmentKey=String(x.segment_key||'').trim().slice(0,120)||`segment-${crypto.randomUUID().slice(0,8)}`;
      if(segmentKey==='primary'||x.presence_kind==='story_span')return privateJson({ok:false,error:'Le segment primary/story_span est réservé à la fiche principale de la Chronique.',code:'PRIMARY_SEGMENT_LOCKED'},409);
      const startsAt=x.starts_at||null,endsAt=x.ends_at||null;
      if(startsAt&&endsAt&&new Date(endsAt).getTime()<new Date(startsAt).getTime())return privateJson({ok:false,error:'La fin du segment ne peut pas précéder son début.',code:'INVALID_SEGMENT_RANGE'},400);
      const payload={story_id:x.story_id,character_id:x.character_id,starts_at:startsAt,ends_at:endsAt,location_id:x.location_id||null,location_name:String(x.location_name||'').trim().slice(0,220)||null,certainty:certainties.includes(x.certainty)?x.certainty:'confirmed',presence_kind:kinds.includes(x.presence_kind)?x.presence_kind:'scene',segment_key:segmentKey,source_note:String(x.source_note||'').slice(0,2000)||null};
      let saved;
      if(x.id){const {data,error}=await s.from('sinjira_story_character_presence').update(payload).eq('id',x.id).select('*').single();if(error)throw error;saved=data}
      else{const {data,error}=await s.from('sinjira_story_character_presence').insert(payload).select('*').single();if(error)throw error;saved=data}
      await audit(s,user.id,x.id?'update_extended_story_segment':'create_extended_story_segment','sinjira_story_character_presence',saved.id,'Segment de continuité',{story_id:x.story_id,character_id:x.character_id,segment_key:segmentKey});
      return privateJson({ok:true,segment:saved});
    }

    if(a==='remove_extended_story_segment'){
      if(!b.segment_id)return privateJson({ok:false,error:'Segment requis.',code:'SEGMENT_REQUIRED'},400);
      const {data:segment,error:lookupError}=await s.from('sinjira_story_character_presence').select('id,story_id,segment_key').eq('id',b.segment_id).maybeSingle();if(lookupError)throw lookupError;if(!segment)return privateJson({ok:true});
      if(segment.segment_key==='primary')return privateJson({ok:false,error:'Le segment principal est géré par la fiche de Chronique et ne peut pas être supprimé ici.',code:'PRIMARY_SEGMENT_LOCKED'},409);
      const {data:story,error:storyError}=await s.from('sinjira_extended_stories').select('status').eq('id',segment.story_id).maybeSingle();if(storyError)throw storyError;if(story?.status==='published')throw new Error('STORY_UNPUBLISH_FIRST');
      const {error}=await s.from('sinjira_story_character_presence').delete().eq('id',segment.id);if(error)throw error;
      await audit(s,user.id,'remove_extended_story_segment','sinjira_story_character_presence',segment.id,'Segment de continuité retiré',{story_id:segment.story_id});
      return privateJson({ok:true});
    }

    if(a==='list_world_continuity'){
      const [locations,events,travel]=await Promise.all([
        s.from('sinjira_world_locations').select('*').order('name'),
        s.from('sinjira_canon_events').select('*,sinjira_world_locations(name,slug),sinjira_canon_event_characters(*,characters(public_name))').order('starts_at',{ascending:true,nullsFirst:false}),
        s.from('sinjira_world_travel_rules').select('*,from:sinjira_world_locations!sinjira_world_travel_rules_from_location_id_fkey(name),to:sinjira_world_locations!sinjira_world_travel_rules_to_location_id_fkey(name)').order('minimum_minutes')
      ]);
      if(locations.error)throw locations.error;if(events.error)throw events.error;if(travel.error)throw travel.error;
      return privateJson({ok:true,locations:locations.data||[],events:events.data||[],travel_rules:travel.data||[]});
    }

    if(a==='save_world_location'){
      const x=b.location||{};
      const id=x.id||null;
      const name=String(x.name||'').trim().slice(0,180);
      const slugSource=String(x.slug||name).normalize('NFD').replace(/[\u0300-\u036f]/g,'');
      const slug=slugSource.trim().toLowerCase().replace(/[^a-z0-9-]+/g,'-').replace(/^-+|-+$/g,'').slice(0,120);
      const types=['world','continent','country','province_state','region','city','district','site','place'];
      const canon=['PROVISOIRE','CANON','A_ARBITRER'];
      if(!slug||!name)return privateJson({ok:false,error:'Nom et slug du lieu requis.',code:'LOCATION_REQUIRED'},400);
      const payload={slug,name,location_type:types.includes(x.location_type)?x.location_type:'place',parent_id:x.parent_id||null,country_code:String(x.country_code||'').trim().slice(0,8)||null,timezone_name:String(x.timezone_name||'').trim().slice(0,80)||null,latitude:x.latitude===''||x.latitude==null?null:Number(x.latitude),longitude:x.longitude===''||x.longitude==null?null:Number(x.longitude),canon_status:canon.includes(x.canon_status)?x.canon_status:'PROVISOIRE',source_reference:String(x.source_reference||'').trim().slice(0,500)||null,notes:String(x.notes||'').slice(0,4000)||null};
      if(payload.canon_status==='CANON'&&!payload.source_reference)return privateJson({ok:false,error:'Un lieu CANON doit citer sa source dans les romans ou la Bible canonique.',code:'LOCATION_SOURCE_REQUIRED'},400);
      let saved;
      if(id){const {data,error}=await s.from('sinjira_world_locations').update(payload).eq('id',id).select('*').single();if(error)throw error;saved=data}
      else{const {data,error}=await s.from('sinjira_world_locations').insert(payload).select('*').single();if(error)throw error;saved=data}
      await audit(s,user.id,id?'update_world_location':'create_world_location','sinjira_world_location',saved.id,name,{canon_status:payload.canon_status});
      return privateJson({ok:true,location:saved});
    }

    if(a==='save_world_travel_rule'){
      const x=b.rule||{};
      const id=x.id||null;
      if(!x.from_location_id||!x.to_location_id||x.from_location_id===x.to_location_id)return privateJson({ok:false,error:'Deux lieux différents sont requis pour une règle de déplacement.',code:'TRAVEL_LOCATIONS_REQUIRED'},400);
      const minutes=Number(x.minimum_minutes);
      if(!Number.isFinite(minutes)||minutes<0||minutes>525600)return privateJson({ok:false,error:'Durée minimale de déplacement invalide.',code:'TRAVEL_MINUTES_INVALID'},400);
      const canon=['PROVISOIRE','CANON','A_ARBITRER'];
      const payload={from_location_id:x.from_location_id,to_location_id:x.to_location_id,minimum_minutes:Math.round(minutes),travel_mode:String(x.travel_mode||'unspecified').trim().slice(0,120)||'unspecified',bidirectional:x.bidirectional!==false,valid_from:x.valid_from||null,valid_until:x.valid_until||null,canon_status:canon.includes(x.canon_status)?x.canon_status:'PROVISOIRE',source_reference:String(x.source_reference||'').trim().slice(0,700)||null,notes:String(x.notes||'').slice(0,4000)||null};
      if(payload.canon_status==='CANON'&&!payload.source_reference)return privateJson({ok:false,error:'Une règle de déplacement CANON doit avoir une source.',code:'TRAVEL_SOURCE_REQUIRED'},400);
      if(payload.valid_from&&payload.valid_until&&new Date(payload.valid_until).getTime()<new Date(payload.valid_from).getTime())return privateJson({ok:false,error:'La fin de validité ne peut pas précéder le début.',code:'TRAVEL_WINDOW_INVALID'},400);
      let saved;
      if(id){const {data,error}=await s.from('sinjira_world_travel_rules').update(payload).eq('id',id).select('*').single();if(error)throw error;saved=data}
      else{const {data,error}=await s.from('sinjira_world_travel_rules').insert(payload).select('*').single();if(error)throw error;saved=data}
      await audit(s,user.id,id?'update_world_travel_rule':'create_world_travel_rule','sinjira_world_travel_rule',saved.id,'Règle de déplacement',{minimum_minutes:payload.minimum_minutes,canon_status:payload.canon_status});
      return privateJson({ok:true,rule:saved});
    }

    if(a==='save_canon_event'){
      const x=b.event||{};
      const id=x.id||null;
      const scopes=['LIVRES_1_12','ORIGINES_13_14','CANON_ETENDU'];
      const classifications=['CANON','SECRET_AUTEUR','A_ARBITRER','PROVISOIRE'];
      const title=String(x.title||'').trim().slice(0,240);
      const sourceReference=String(x.source_reference||'').trim().slice(0,700);
      if(!title||!sourceReference)return privateJson({ok:false,error:'Titre et source canonique requis.',code:'EVENT_SOURCE_REQUIRED'},400);
      const startsAt=x.starts_at||null,endsAt=x.ends_at||null;
      if(startsAt&&endsAt&&new Date(endsAt).getTime()<new Date(startsAt).getTime())return privateJson({ok:false,error:'La fin de l’événement ne peut pas précéder son début.',code:'INVALID_EVENT_RANGE'},400);
      const payload={event_key:String(x.event_key||'').trim().slice(0,160)||null,title,summary:String(x.summary||'').slice(0,12000)||null,starts_at:startsAt,ends_at:endsAt,timezone_name:String(x.timezone_name||'').trim().slice(0,80)||null,location_id:x.location_id||null,location_name_snapshot:String(x.location_name_snapshot||'').trim().slice(0,220)||null,source_scope:scopes.includes(x.source_scope)?x.source_scope:'LIVRES_1_12',source_reference:sourceReference,classification:classifications.includes(x.classification)?x.classification:'PROVISOIRE',public_safe:x.public_safe===true,consequences:x.consequences&&typeof x.consequences==='object'?x.consequences:{}};
      let saved;
      if(id){const {data,error}=await s.from('sinjira_canon_events').update(payload).eq('id',id).select('*').single();if(error)throw error;saved=data}
      else{const {data,error}=await s.from('sinjira_canon_events').insert(payload).select('*').single();if(error)throw error;saved=data}
      await audit(s,user.id,id?'update_canon_event':'create_canon_event','sinjira_canon_event',saved.id,title,{classification:payload.classification,source_scope:payload.source_scope});
      return privateJson({ok:true,event:saved});
    }

    if(a==='save_canon_event_character'){
      const x=b.presence||{};
      if(!x.event_id||!x.character_id)return privateJson({ok:false,error:'Événement et personnage requis.',code:'EVENT_CHARACTER_REQUIRED'},400);
      const {data:event,error:eventError}=await s.from('sinjira_canon_events').select('id,starts_at,ends_at,location_id,location_name_snapshot,source_reference').eq('id',x.event_id).maybeSingle();
      if(eventError)throw eventError;if(!event)return privateJson({ok:false,error:'Événement canonique introuvable.',code:'EVENT_NOT_FOUND'},404);
      const certainties=['confirmed','approximate','unknown'];
      const payload={event_id:x.event_id,character_id:x.character_id,role:String(x.role||'').trim().slice(0,160)||null,starts_at:x.starts_at||event.starts_at||null,ends_at:x.ends_at||event.ends_at||null,location_id:x.location_id||event.location_id||null,location_name_snapshot:String(x.location_name_snapshot||event.location_name_snapshot||'').trim().slice(0,220)||null,certainty:certainties.includes(x.certainty)?x.certainty:'confirmed',source_reference:String(x.source_reference||event.source_reference||'').trim().slice(0,700)||null};
      if(payload.starts_at&&payload.ends_at&&new Date(payload.ends_at).getTime()<new Date(payload.starts_at).getTime())return privateJson({ok:false,error:'La fin de présence ne peut pas précéder son début.',code:'INVALID_PRESENCE_RANGE'},400);
      const {data,error}=await s.from('sinjira_canon_event_characters').upsert(payload,{onConflict:'event_id,character_id'}).select('*').single();if(error)throw error;
      await audit(s,user.id,'save_canon_event_character','sinjira_canon_event_character',x.event_id,'Présence canonique mise à jour',{character_id:x.character_id});
      return privateJson({ok:true,presence:data});
    }

    if(a==='remove_canon_event_character'){
      if(!b.event_id||!b.character_id)return privateJson({ok:false,error:'Événement et personnage requis.',code:'EVENT_CHARACTER_REQUIRED'},400);
      const {error}=await s.from('sinjira_canon_event_characters').delete().eq('event_id',b.event_id).eq('character_id',b.character_id);if(error)throw error;
      await audit(s,user.id,'remove_canon_event_character','sinjira_canon_event_character',b.event_id,'Présence canonique retirée',{character_id:b.character_id});
      return privateJson({ok:true});
    }

    if(a==='check_extended_story_continuity'){
      if(!b.story_id)return privateJson({ok:false,error:'Chronique requise.',code:'STORY_REQUIRED'},400);
      const {data,error}=await s.rpc('admin_sinjira_story_continuity_check',{p_story_id:b.story_id});if(error)throw error;
      return privateJson({ok:true,continuity:data});
    }

    if(a==='publish_extended_story'){
      if(!b.story_id)return privateJson({ok:false,error:'Chronique requise.',code:'STORY_REQUIRED'},400);
      if(b.author_confirmed_publication!==true)throw new Error('STORY_PUBLICATION_CONFIRMATION_REQUIRED');
      const audience=['members','public'].includes(b.audience)?b.audience:null;
      if(!audience)return privateJson({ok:false,error:'La publication exige une audience Membres ou Public.',code:'STORY_PUBLIC_AUDIENCE_REQUIRED'},400);
      const {data,error}=await s.rpc('admin_sinjira_publish_extended_story',{p_story_id:b.story_id,p_audience:audience});
      if(error)throw error;
      const {data:story,error:storyError}=await s.from('sinjira_extended_stories').select('*').eq('id',b.story_id).single();
      if(storyError)throw storyError;
      await audit(s,user.id,'publish_extended_story','sinjira_extended_story',b.story_id,story?.title||'Chronique publiée',{audience});
      return privateJson({ok:true,story,publication:data});
    }

    if(a==='unpublish_extended_story'){
      if(!b.story_id)return privateJson({ok:false,error:'Chronique requise.',code:'STORY_REQUIRED'},400);
      if(b.author_confirmed_unpublish!==true)throw new Error('STORY_UNPUBLISH_CONFIRMATION_REQUIRED');
      const {data,error}=await s.rpc('admin_sinjira_unpublish_extended_story',{p_story_id:b.story_id});
      if(error)throw error;
      const {data:story,error:storyError}=await s.from('sinjira_extended_stories').select('*').eq('id',b.story_id).single();
      if(storyError)throw storyError;
      await audit(s,user.id,'unpublish_extended_story','sinjira_extended_story',b.story_id,story?.title||'Chronique retirée de publication',{});
      return privateJson({ok:true,story,publication:data});
    }

    if(a==='save_extended_story'){
      const story=b.story||{};
      const storyTypes=['character_chronicle','world_chronicle','quebec_chronicle','archive','fragment','novella'];
      const anchorScopes=['LIVRES_1_12','ORIGINES_13_14','MULTI_PERIODE','UNASSIGNED'];
      const canonStatuses=['PROVISOIRE','CANON_ETENDU','A_ARBITRER','NON_CANON'];
      const workflowStatuses=['draft','author_review','validated','published','archived'];
      const audiences=['private','members','public'];
      const storyType=storyTypes.includes(story.story_type)?story.story_type:'character_chronicle';
      const anchorScope=anchorScopes.includes(story.anchor_scope)?story.anchor_scope:'UNASSIGNED';
      const requestedCanon=canonStatuses.includes(story.canon_status)?story.canon_status:'PROVISOIRE';
      const status=workflowStatuses.includes(story.status)?story.status:'draft';
      const audience=audiences.includes(story.audience)?story.audience:'private';
      if(status==='published')throw new Error('STORY_PUBLISH_SEPARATELY');
      let currentStory:any=null;
      if(story.id){
        const current=await s.from('sinjira_extended_stories').select('id,status,canon_status,published_at,audience').eq('id',story.id).maybeSingle();
        if(current.error)throw current.error;
        currentStory=current.data;
        if(currentStory?.status==='published')throw new Error('STORY_UNPUBLISH_FIRST');
      }
      if(requestedCanon==='CANON_ETENDU'&&story.author_confirmed_extended_canon!==true)throw new Error('EXTENDED_CANON_CONFIRMATION_REQUIRED');
      const characterId=story.character_id||null;
      if(storyType==='character_chronicle'&&!characterId)return privateJson({ok:false,error:'Une Chronique de personnage doit être liée à une Conscience.',code:'CHARACTER_REQUIRED'},400);
      const title=String(story.title||'').trim().slice(0,220);
      if(!title)return privateJson({ok:false,error:'Titre de Chronique requis.',code:'TITLE_REQUIRED'},400);
      const startsAt=story.starts_at||null,endsAt=story.ends_at||null;
      if(startsAt&&endsAt&&new Date(endsAt).getTime()<new Date(startsAt).getTime())return privateJson({ok:false,error:'La fin de la Chronique ne peut pas précéder son début.',code:'INVALID_STORY_RANGE'},400);
      const payload={
        story_type:storyType,
        character_id:characterId,
        title,
        slug:String(story.slug||'').trim().slice(0,180)||null,
        summary:String(story.summary||'').slice(0,12000)||null,
        content:String(story.content||'').slice(0,1000000)||null,
        region_name:String(story.region_name||'').trim().slice(0,220)||null,
        location_id:story.location_id||null,
        anchor_scope:anchorScope,
        canon_status:requestedCanon==='CANON_ETENDU'?'PROVISOIRE':requestedCanon,
        status,
        starts_at:startsAt,
        ends_at:endsAt,
        continuity_data:story.continuity_data&&typeof story.continuity_data==='object'?story.continuity_data:{},
        audience,
        visible_to_character_owner:story.visible_to_character_owner!==false,
        published_at:null
      };
      let saved:any=null;
      if(story.id){
        const {data,error}=await s.from('sinjira_extended_stories').update(payload).eq('id',story.id).select('*').single();
        if(error)throw error;saved=data;
      }else{
        const {data,error}=await s.from('sinjira_extended_stories').insert(payload).select('*').single();
        if(error)throw error;saved=data;
      }
      if(characterId){
        const {error:presenceError}=await s.from('sinjira_story_character_presence').upsert({
          story_id:saved.id,
          character_id:characterId,
          starts_at:startsAt,
          ends_at:endsAt,
          location_id:payload.location_id,
          location_name:payload.region_name,
          certainty:'confirmed',
          presence_kind:'story_span',
          segment_key:'primary',
          source_note:`Présence dérivée de la Chronique : ${title}`
        },{onConflict:'story_id,character_id,segment_key'});
        if(presenceError)throw presenceError;
        const {error:stalePrimaryError}=await s.from('sinjira_story_character_presence').delete().eq('story_id',saved.id).eq('segment_key','primary').neq('character_id',characterId);
        if(stalePrimaryError)throw stalePrimaryError;
      }else{
        const {error:stalePrimaryError}=await s.from('sinjira_story_character_presence').delete().eq('story_id',saved.id).eq('segment_key','primary');
        if(stalePrimaryError)throw stalePrimaryError;
      }
      let continuity:any=null;
      if(requestedCanon==='CANON_ETENDU'){
        const check=await s.rpc('admin_sinjira_story_continuity_check',{p_story_id:saved.id});
        if(check.error)throw check.error;
        continuity=check.data;
        if(Number(continuity?.blocking_conflicts||0)>0){
          await audit(s,user.id,'extended_story_continuity_blocked','sinjira_extended_story',saved.id,title,{blocking_conflicts:continuity.blocking_conflicts});
          return privateJson({ok:false,persisted:true,story:saved,continuity,error:'Canonisation bloquée : une collision de continuité doit être corrigée.',code:'STORY_CONTINUITY_CONFLICT'},409);
        }
        if(Number(continuity?.warnings||0)>0){
          await audit(s,user.id,'extended_story_continuity_incomplete','sinjira_extended_story',saved.id,title,{warnings:continuity.warnings});
          return privateJson({ok:false,persisted:true,story:saved,continuity,error:'Canonisation bloquée : la date ou le lieu d’une présence doit être complété dans le Calendrier-Monde / Atlas.',code:'STORY_CONTINUITY_INCOMPLETE'},409);
        }
        const promotion=await s.rpc('admin_sinjira_promote_extended_story',{p_story_id:saved.id});
        if(promotion.error)throw promotion.error;
        saved={...saved,canon_status:promotion.data?.canon_status||'CANON_ETENDU',status:promotion.data?.status||saved.status};
      }
      await audit(s,user.id,story.id?'update_extended_story':'create_extended_story','sinjira_extended_story',saved.id,title,{story_type:storyType,canon_status:saved.canon_status,anchor_scope:anchorScope});
      return privateJson({ok:true,story:saved,continuity});
    }

    if(a==='save_character'){
      const c=b.character||{};
      const canonStatus=['PROVISOIRE','CANON','SECRET_AUTEUR','A_ARBITRER'].includes(c.canon_status)?c.canon_status:'PROVISOIRE';
      if(canonStatus==='CANON'&&c.author_confirmed_canon!==true)throw new Error('CANON_CONFIRMATION_REQUIRED');
      if(c.novel_id&&c.author_confirmed_retcon!==true)throw new Error('CENTRAL_CANON_LOCKED')
      const payload={public_name:String(c.public_name||'').slice(0,160),public_description:String(c.public_description||'').slice(0,8000),status:c.status||'author_review',novel_id:c.novel_id||null,novel_note:String(c.novel_note||'').slice(0,500),visible_to_user:Boolean(c.visible_to_user),canon_status:canonStatus,canon_version:String(c.canon_version||'v1.0').slice(0,30),bible:c.bible||{}};
      const {data,error}=await s.from('characters').update(payload).eq('id',c.id).select('*').single();if(error)throw error;
      if(data?.submission_id){await s.from('character_submissions').update({status:payload.status}).eq('id',data.submission_id);await statusEvent(s,data.submission_id,data.user_id,payload.status,payload.novel_id?'Roman attribué / statut mis à jour.':'Statut du personnage mis à jour.')}
      await audit(s,user.id,'save_character','character',data.id,'Personnage mis à jour',{status:payload.status,canon_status:payload.canon_status});
      return privateJson({ok:true,character:data});
    }

    return privateJson({ok:false,error:'Action inconnue.',code:'UNKNOWN_ACTION'},400);
  }catch(e){
    console.error('[admin-sinjira-v18]',adminV18LogCode(e));
    if(e?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(e?.message==='ADMIN_REQUIRED')return privateJson({ok:false,error:'Administration refusée.',code:'ADMIN_REQUIRED'},403);
    if(e?.message==='MFA_REQUIRED')return privateJson({ok:false,error:'MFA_REQUIRED',code:'MFA_REQUIRED'},403);
    if(e?.message==='MFA_STATE_UNAVAILABLE')return privateJson({ok:false,error:'État MFA temporairement indisponible.',code:'MFA_STATE_UNAVAILABLE'},503);
    if(e?.message==='JSON_REQUIRED')return privateJson({ok:false,error:'Corps JSON requis.',code:'JSON_REQUIRED'},415);
    if(e?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE'},413);
    if(e?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON'},400);
    if(e?.message==='SOURCE_PURGE_CONFIRMATION_REQUIRED')return privateJson({ok:false,error:'Confirmation explicite requise avant suppression définitive des sources.',code:'SOURCE_PURGE_CONFIRMATION_REQUIRED'},409);
    if(e?.message==='SOURCE_PURGED')return privateJson({ok:false,error:'Les données sources ont déjà été supprimées.',code:'SOURCE_PURGED'},409);
    if(e?.message==='SOURCE_PURGE_STORAGE_FAILED')return privateJson({ok:false,error:'La suppression du fichier source a échoué; les références ont été conservées.',code:'SOURCE_PURGE_STORAGE_FAILED'},503);
    if(e?.message==='CANON_CONFIRMATION_REQUIRED')return privateJson({ok:false,error:'Confirmez explicitement que ce personnage est établi par un manuscrit officiel finalisé avant de le passer CANON.'},409);
    if(e?.message==='EXTENDED_CANON_CONFIRMATION_REQUIRED')return privateJson({ok:false,error:'Confirmez explicitement la validation auteur avant de passer cette histoire en CANON ÉTENDU.',code:'EXTENDED_CANON_CONFIRMATION_REQUIRED'},409);
    if(e?.message==='STORY_PUBLICATION_CONFIRMATION_REQUIRED')return privateJson({ok:false,error:'Confirmez explicitement la publication de cette Chronique.',code:'STORY_PUBLICATION_CONFIRMATION_REQUIRED'},409);
    if(e?.message==='STORY_UNPUBLISH_CONFIRMATION_REQUIRED')return privateJson({ok:false,error:'Confirmez explicitement le retrait de publication avant modification.',code:'STORY_UNPUBLISH_CONFIRMATION_REQUIRED'},409);
    if(e?.message==='STORY_PUBLISH_SEPARATELY')return privateJson({ok:false,error:'Enregistrez et canonisez d’abord la Chronique, puis utilisez le bouton Publier.',code:'STORY_PUBLISH_SEPARATELY'},409);
    if(e?.message==='STORY_UNPUBLISH_FIRST')return privateJson({ok:false,error:'Cette Chronique est publiée. Retirez-la de publication avant de modifier son contenu ou sa continuité.',code:'STORY_UNPUBLISH_FIRST'},409);
    if(e?.message==='STORY_PUBLIC_AUDIENCE_REQUIRED')return privateJson({ok:false,error:'La publication exige une audience Membres ou Public.',code:'STORY_PUBLIC_AUDIENCE_REQUIRED'},409);
    if(e?.message==='STORY_NOT_CANON_EXTENDED')return privateJson({ok:false,error:'La Chronique doit être CANON ÉTENDU avant publication.',code:'STORY_NOT_CANON_EXTENDED'},409);
    if(e?.message==='STORY_ARCHIVED')return privateJson({ok:false,error:'Une Chronique archivée ne peut pas être publiée.',code:'STORY_ARCHIVED'},409);
    if(e?.message==='STORY_ANCHOR_REQUIRED')return privateJson({ok:false,error:'Définissez l’ancrage canonique avant publication.',code:'STORY_ANCHOR_REQUIRED'},409);
    if(e?.message==='STORY_METADATA_INCOMPLETE')return privateJson({ok:false,error:'La publication exige une période complète et un lieu Atlas.',code:'STORY_METADATA_INCOMPLETE'},409);
    if(e?.message==='STORY_CONTENT_REQUIRED')return privateJson({ok:false,error:'Le contenu de la Chronique doit être rédigé avant publication.',code:'STORY_CONTENT_REQUIRED'},409);
    if(e?.message==='STORY_CONTINUITY_CONFLICT')return privateJson({ok:false,error:'Canonisation refusée : collision de continuité détectée.',code:'STORY_CONTINUITY_CONFLICT'},409);
    if(e?.message==='STORY_CONTINUITY_INCOMPLETE')return privateJson({ok:false,error:'Canonisation refusée : date ou lieu de continuité incomplet.',code:'STORY_CONTINUITY_INCOMPLETE'},409);
    if(e?.message==='NOTIFICATION_ID_REQUIRED')return privateJson({ok:false,error:'Identifiant de notification requis.'},400);
    if(e?.message==='CENTRAL_CANON_LOCKED')return privateJson({ok:false,error:'Les 14 romans principaux constituent le Canon central verrouillé. Une attribution directe à un roman central exige une confirmation auteur explicite; utilisez normalement une Chronique du Canon étendu pour les personnages du Registre.',code:'CENTRAL_CANON_LOCKED'},409);
    return privateJson({ok:false,error:'Erreur administration V18.',code:'ADMIN_V18_FAILED'},500);
  }
});
