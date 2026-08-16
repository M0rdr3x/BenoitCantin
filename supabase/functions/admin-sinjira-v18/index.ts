import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';
import {SINJIRA_CANON_PUBLIC_GUIDE} from '../_shared/sinjira-canon-public.ts';
import {loadSinjiraCanonContext,canonPrompt} from '../_shared/sinjira-canon-context.ts';

const OWNER_EMAIL='kingtyrano@gmail.com';
const CHARACTER_STATUSES=new Set(['ai_draft','author_review','approved','assigned','future','published','archived']);
const CANON_STATUSES=new Set(['PROVISOIRE','CANON','SECRET_AUTEUR','A_ARBITRER']);
const PRIVATE_KEYS=['prenom_legal','nom_legal','courriel','telephone','date_naissance','region','courriel_retrait','nom_signature','parent_nom','parent_courriel','parent_telephone','parent_signature','compte_courriel','compte_pseudo'];
const MAX_BIBLE_BYTES=250_000;

function characterAiEnabled(){return String(Deno.env.get('SINJIRA_CHARACTER_AI_ENABLED')||'').trim().toLowerCase()==='true'}
function isOwner(user:any){return String(user?.email||'').trim().toLowerCase()===OWNER_EMAIL}
function creativePayload(src:Record<string,unknown>){const out:Record<string,unknown>={};for(const [k,v] of Object.entries(src||{})){if(PRIVATE_KEYS.includes(k)||k.startsWith('parent_')||k.startsWith('photo'))continue;out[k]=v}return out}
function ensureBible(value:unknown){const bible=value&&typeof value==='object'&&!Array.isArray(value)?value:{};if(new TextEncoder().encode(JSON.stringify(bible)).byteLength>MAX_BIBLE_BYTES)throw new Error('BIBLE_TOO_LARGE');return bible}

async function audit(s:any,userId:string,action:string,entity_type='',entity_id='',summary='',metadata:any={}){
  try{await s.from('admin_audit_log').insert({admin_user_id:userId,action,entity_type,entity_id:String(entity_id||''),summary,metadata})}
  catch(e){console.warn('[SINJIRA admin audit]',e)}
}
async function statusEvent(s:any,submission_id:string,user_id:string,status:string,note=''){
  try{await s.from('character_status_events').insert({submission_id,user_id,status,note})}catch(e){console.warn('[SINJIRA status event]',e)}
}
async function ctx(req:Request){
  const user=await requiredUser(req),s=serviceClient();
  const {data,error}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});
  if(error||!data)throw new Error('ADMIN_REQUIRED');
  return {user,s,owner:isOwner(user)};
}

const schema={type:'object',additionalProperties:false,required:['character_name','age_range','gender','appearance','origin','role','faction','personality_summary','values','strengths','weaknesses','fears','contradictions','voice','motivations','relationships','narrative_arc','novel_fit','recommended_placement','continuity_flags','canon_notes','prohibited_elements'],properties:{character_name:{type:'string'},age_range:{type:'string'},gender:{type:'string'},appearance:{type:'string'},origin:{type:'string'},role:{type:'string'},faction:{type:'string'},personality_summary:{type:'string'},values:{type:'array',items:{type:'string'}},strengths:{type:'array',items:{type:'string'}},weaknesses:{type:'array',items:{type:'string'}},fears:{type:'array',items:{type:'string'}},contradictions:{type:'array',items:{type:'string'}},voice:{type:'string'},motivations:{type:'array',items:{type:'string'}},relationships:{type:'array',items:{type:'string'}},narrative_arc:{type:'string'},novel_fit:{type:'string'},recommended_placement:{type:'string'},continuity_flags:{type:'array',items:{type:'string'}},canon_notes:{type:'array',items:{type:'string'}},prohibited_elements:{type:'array',items:{type:'string'}}}};

async function ai(src:Record<string,unknown>,s:any){
  if(!characterAiEnabled())throw new Error('CHARACTER_AI_DISABLED');
  const key=Deno.env.get('OPENAI_API_KEY');if(!key)throw new Error('OPENAI_NOT_CONFIGURED');
  const model=Deno.env.get('OPENAI_CHARACTER_MODEL')||'gpt-5';
  const contexts=await loadSinjiraCanonContext(s),privateCanon=canonPrompt(contexts);
  const r=await fetch('https://api.openai.com/v1/responses',{method:'POST',headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:JSON.stringify({model,store:false,input:[{role:'system',content:`Génère un brouillon ORIGINAL de personnage SINJIRA à partir de traits humains anonymisés.\n\nGuide public :\n${SINJIRA_CANON_PUBLIC_GUIDE}\n\nContexte privé de continuité :\n${privateCanon}\n\nRègles :\n- SECRET_AUTEUR = garde-fou interne seulement : ne jamais révéler ni résoudre.\n- À ARBITRER = ne jamais trancher automatiquement.\n- Le Roman 1 est verrouillé; un nouveau personnage n’y est jamais inséré automatiquement.\n- Éviter les noms et fonctions dramatiques des personnages déjà CANON.\n- Aucune magie ou superpouvoir établi.\n- Le brouillon reste PROVISOIRE jusqu’à une décision explicite de Benoit Cantin.\n- continuity_flags doit signaler tout risque de collision avec le canon.\nAucune personne publique, aucune donnée personnelle.`},{role:'user',content:JSON.stringify(creativePayload(src))}],text:{format:{type:'json_schema',name:'sinjira_character_bible',strict:true,schema}}})});
  if(!r.ok)throw new Error(`OPENAI_${r.status}`);
  const d=await r.json();return {model,bible:JSON.parse(d.output_text)};
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const {user,s,owner}=await ctx(req),b=await req.json().catch(()=>({})),a=String(b.action||'');

    if(a==='dashboard'){
      const [c,sub,rev]=await Promise.all([
        s.from('novel_comments').select('id',{count:'exact',head:true}).eq('status','pending'),
        s.from('character_submissions').select('id',{count:'exact',head:true}),
        s.from('characters').select('id',{count:'exact',head:true}).in('status',['ai_draft','author_review'])
      ]);
      return json({ok:true,dashboard:{pending_comments:c.count||0,character_submissions:sub.count||0,characters_in_review:rev.count||0,character_ai_enabled:characterAiEnabled()}});
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
        if(sub.photo_path){const {data:signed,error:signedError}=await s.storage.from('sinjira-character-sources').createSignedUrl(sub.photo_path,600);if(!signedError)photo_url=signed?.signedUrl||null}
        rows.push({...sub,photo_url});
      }
      return json({ok:true,submissions:rows});
    }

    if(a==='create_manual_character'){
      const {data:sub,error}=await s.from('character_submissions').select('*').eq('id',b.submission_id).single();if(error)throw error;
      const {data:existing}=await s.from('characters').select('*').eq('user_id',sub.user_id).maybeSingle();if(existing)return json({ok:true,character:existing});
      const {data:ch,error:ce}=await s.from('characters').insert({submission_id:sub.id,user_id:sub.user_id,public_name:'À définir',public_description:'Personnage en préparation par Benoit Cantin.',status:'author_review',bible:{source:'Registre des Consciences',mode:'manuel',notes:'À compléter par l’auteur.'},ai_generated:false,visible_to_user:true,canon_status:'PROVISOIRE'}).select('*').single();if(ce)throw ce;
      await s.from('character_submissions').update({status:'author_review'}).eq('id',sub.id);
      await statusEvent(s,sub.id,sub.user_id,'author_review','Fiche de personnage créée manuellement par Benoit Cantin.');
      await audit(s,user.id,'create_manual_character','character',ch.id,'Fiche manuelle créée',{submission_id:sub.id});
      return json({ok:true,character:ch});
    }

    if(a==='generate_character'){
      if(!characterAiEnabled())throw new Error('CHARACTER_AI_DISABLED');
      const {data:sub,error}=await s.from('character_submissions').select('*').eq('id',b.submission_id).single();if(error)throw error;if(!sub.source_payload)throw new Error('SOURCE_PURGED');
      const g=await ai(sub.source_payload,s),{data:existing}=await s.from('characters').select('id').eq('submission_id',sub.id).maybeSingle();let ch;
      if(existing){const {data,error}=await s.from('characters').update({public_name:g.bible.character_name,public_description:g.bible.personality_summary,status:'author_review',bible:g.bible,ai_generated:true,visible_to_user:true,canon_status:'PROVISOIRE',canon_version:'v1.0'}).eq('id',existing.id).select('*').single();if(error)throw error;ch=data}
      else{const {data,error}=await s.from('characters').insert({submission_id:sub.id,user_id:sub.user_id,public_name:g.bible.character_name,public_description:g.bible.personality_summary,status:'author_review',bible:g.bible,ai_generated:true,visible_to_user:true,canon_status:'PROVISOIRE',canon_version:'v1.0'}).select('*').single();if(error)throw error;ch=data}
      await s.from('character_submissions').update({status:'ai_draft'}).eq('id',sub.id);
      await s.from('character_generation_runs').insert({submission_id:sub.id,character_id:ch.id,model:g.model,status:'completed'});
      await audit(s,user.id,'generate_character','character',ch.id,'Brouillon IA généré',{submission_id:sub.id,model:g.model});
      return json({ok:true,character:ch});
    }

    if(a==='system_health'){
      const checks:any={};for(const table of ['profiles','game_sessions','novel_comments','character_submissions','characters']){const {count,error}=await s.from(table).select('*',{count:'exact',head:true});checks[table]={ok:!error,count:count||0,error:error?.message||null}}
      return json({ok:true,checks,features:{character_ai_enabled:characterAiEnabled()}});
    }

    if(a==='audit_log'){
      const {data,error}=await s.from('admin_audit_log').select('*').order('created_at',{ascending:false}).limit(200);if(error)throw error;return json({ok:true,rows:data||[]});
    }

    if(a==='purge_submission_source'){
      const {data:sub,error}=await s.from('character_submissions').select('id,photo_path').eq('id',b.submission_id).single();if(error)throw error;
      if(sub.photo_path){
        const {error:storageError}=await s.storage.from('sinjira-character-sources').remove([sub.photo_path]);
        if(storageError)throw new Error('SOURCE_PHOTO_DELETE_FAILED');
      }
      const {error:updateError}=await s.from('character_submissions').update({source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()}).eq('id',sub.id);
      if(updateError)throw updateError;
      await audit(s,user.id,'purge_submission_source','character_submission',sub.id,'Données sources personnelles supprimées');
      return json({ok:true});
    }

    if(a==='list_characters'){
      const [{data:chars,error},{data:novels}]=await Promise.all([s.from('characters').select('*,novels(title)').order('updated_at',{ascending:false}),s.from('novels').select('id,title').order('sort_order')]);if(error)throw error;
      return json({ok:true,characters:(chars||[]).map((x:any)=>({...x,novel_title:x.novels?.title||''})),novels:novels||[]});
    }

    if(a==='canon_overview'){
      const contexts=await loadSinjiraCanonContext(s);return json({ok:true,contexts});
    }

    if(a==='save_character'){
      const c=b.character||{};
      const status=String(c.status||'author_review');if(!CHARACTER_STATUSES.has(status))throw new Error('INVALID_CHARACTER_STATUS');
      const canonStatus=CANON_STATUSES.has(String(c.canon_status||''))?String(c.canon_status):'PROVISOIRE';
      if(canonStatus==='CANON'&&(!owner||c.author_confirmed_canon!==true))throw new Error('CANON_CONFIRMATION_REQUIRED');
      if(c.novel_id){const {data:novel}=await s.from('novels').select('slug').eq('id',c.novel_id).maybeSingle();if(novel?.slug==='la-cendre-du-jugement'&&(!owner||c.author_confirmed_retcon!==true))throw new Error('ROMAN1_LOCKED')}
      const payload={public_name:String(c.public_name||'').slice(0,160),public_description:String(c.public_description||'').slice(0,8000),status,novel_id:c.novel_id||null,novel_note:String(c.novel_note||'').slice(0,500),visible_to_user:Boolean(c.visible_to_user),canon_status:canonStatus,canon_version:String(c.canon_version||'v1.0').slice(0,30),bible:ensureBible(c.bible)};
      const {data,error}=await s.from('characters').update(payload).eq('id',c.id).select('*').single();if(error)throw error;
      if(data?.submission_id){await s.from('character_submissions').update({status:payload.status}).eq('id',data.submission_id);await statusEvent(s,data.submission_id,data.user_id,payload.status,payload.novel_id?'Roman attribué / statut mis à jour.':'Statut du personnage mis à jour.')}
      await audit(s,user.id,'save_character','character',data.id,'Personnage mis à jour',{status:payload.status,canon_status:payload.canon_status});
      return json({ok:true,character:data});
    }

    return json({ok:false,error:'Action inconnue.'},400);
  }catch(e){
    console.error('[SINJIRA admin V18]',e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    if(e?.message==='ADMIN_REQUIRED')return json({ok:false,error:'Administration refusée.'},403);
    if(e?.message==='CHARACTER_AI_DISABLED')return json({ok:false,error:'L’IA de personnage est désactivée tant que le site SINJIRA™ n’est pas finalisé.'},503);
    if(e?.message==='OPENAI_NOT_CONFIGURED')return json({ok:false,error:'Le fournisseur IA n’est pas configuré côté serveur.'},503);
    if(e?.message==='SOURCE_PURGED')return json({ok:false,error:'Les données sources ont déjà été supprimées.'},409);
    if(e?.message==='SOURCE_PHOTO_DELETE_FAILED')return json({ok:false,error:'La photo source n’a pas pu être supprimée du stockage; le dossier n’a pas été marqué comme purgé.'},502);
    if(e?.message==='CANON_CONFIRMATION_REQUIRED')return json({ok:false,error:'Seul le propriétaire peut passer un personnage CANON, avec confirmation explicite d’un manuscrit officiel finalisé.'},409);
    if(e?.message==='ROMAN1_LOCKED')return json({ok:false,error:'Le Roman 1 est verrouillé. Seul le propriétaire peut confirmer explicitement une décision de retcon.'},409);
    if(e?.message==='INVALID_CHARACTER_STATUS')return json({ok:false,error:'Statut de personnage non reconnu.'},400);
    if(e?.message==='BIBLE_TOO_LARGE')return json({ok:false,error:'La fiche personnage dépasse la taille autorisée.'},413);
    return json({ok:false,error:'Erreur administration SINJIRA™.'},500);
  }
});
