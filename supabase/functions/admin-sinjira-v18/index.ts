import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';
import {SINJIRA_CANON_PUBLIC_GUIDE} from '../_shared/sinjira-canon-public.ts';
import {loadSinjiraCanonContext,canonPrompt} from '../_shared/sinjira-canon-context.ts';
async function ctx(req:Request){const user=await requiredUser(req),s=serviceClient();const {data}=await s.rpc('is_sinjira_admin',{p_user_id:user.id});if(!data)throw new Error('ADMIN_REQUIRED');return {user,s}}
const PRIVATE_KEYS=['prenom_legal','nom_legal','courriel','telephone','date_naissance','region','courriel_retrait','nom_signature','parent_nom','parent_courriel','parent_telephone','parent_signature','compte_courriel','compte_pseudo'];
function creativePayload(src:Record<string,unknown>){const out:Record<string,unknown>={};for(const [k,v] of Object.entries(src||{})){if(PRIVATE_KEYS.includes(k)||k.startsWith('parent_')||k.startsWith('photo'))continue;out[k]=v}return out}
const schema={type:'object',additionalProperties:false,required:['character_name','age_range','gender','appearance','origin','role','faction','personality_summary','values','strengths','weaknesses','fears','contradictions','voice','motivations','relationships','narrative_arc','novel_fit','recommended_placement','continuity_flags','canon_notes','prohibited_elements'],properties:{character_name:{type:'string'},age_range:{type:'string'},gender:{type:'string'},appearance:{type:'string'},origin:{type:'string'},role:{type:'string'},faction:{type:'string'},personality_summary:{type:'string'},values:{type:'array',items:{type:'string'}},strengths:{type:'array',items:{type:'string'}},weaknesses:{type:'array',items:{type:'string'}},fears:{type:'array',items:{type:'string'}},contradictions:{type:'array',items:{type:'string'}},voice:{type:'string'},motivations:{type:'array',items:{type:'string'}},relationships:{type:'array',items:{type:'string'}},narrative_arc:{type:'string'},novel_fit:{type:'string'},recommended_placement:{type:'string'},continuity_flags:{type:'array',items:{type:'string'}},canon_notes:{type:'array',items:{type:'string'}},prohibited_elements:{type:'array',items:{type:'string'}}}};
async function ai(src:Record<string,unknown>,s:any){
 const key=Deno.env.get('OPENAI_API_KEY');if(!key)throw new Error('OPENAI_NOT_CONFIGURED');
 const model=Deno.env.get('OPENAI_CHARACTER_MODEL')||'gpt-5';
 const contexts=await loadSinjiraCanonContext(s);
 const privateCanon=canonPrompt(contexts);
 const r=await fetch('https://api.openai.com/v1/responses',{method:'POST',headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:JSON.stringify({model,store:false,input:[{role:'system',content:`Génère un brouillon ORIGINAL de personnage SINJIRA à partir de traits humains anonymisés.

Guide public :
${SINJIRA_CANON_PUBLIC_GUIDE}

Contexte privé de continuité :
${privateCanon}

Règles :
- SECRET_AUTEUR = garde-fou interne seulement : ne jamais révéler ni résoudre.
- À ARBITRER = ne jamais trancher automatiquement.
- Le Roman 1 est verrouillé; un nouveau personnage n’y est jamais inséré automatiquement.
- Éviter les noms et fonctions dramatiques des personnages déjà CANON.
- Aucune magie ou superpouvoir établi.
- Le brouillon reste PROVISOIRE jusqu’à une décision explicite de Benoit Cantin.
- continuity_flags doit signaler tout risque de collision avec le canon.
Aucune personne publique, aucune donnée personnelle.`},{role:'user',content:JSON.stringify(creativePayload(src))}],text:{format:{type:'json_schema',name:'sinjira_character_bible',strict:true,schema}}})});
 if(!r.ok)throw new Error(`OPENAI_${r.status}`);const d=await r.json();return {model,bible:JSON.parse(d.output_text)}
}
Deno.serve(async(req)=>{if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
 try{const {user,s}=await ctx(req),b=await req.json(),a=String(b.action||'');
 if(a==='dashboard'){const [c,sub,rev]=await Promise.all([s.from('novel_comments').select('id',{count:'exact',head:true}).eq('status','pending'),s.from('character_submissions').select('id',{count:'exact',head:true}),s.from('characters').select('id',{count:'exact',head:true}).in('status',['ai_draft','author_review'])]);return json({ok:true,dashboard:{pending_comments:c.count||0,character_submissions:sub.count||0,characters_in_review:rev.count||0}})}
 if(a==='list_comments'){const {data,error}=await s.from('novel_comments').select('id,body,display_name_snapshot,status,created_at,novels(title)').eq('status','pending').order('created_at');if(error)throw error;return json({ok:true,comments:(data||[]).map((x:any)=>({...x,novel_title:x.novels?.title||''}))})}
 if(a==='moderate_comment'){const decision=b.decision==='approved'?'approved':'refused';const {error}=await s.from('novel_comments').update({status:decision,moderated_by:user.id,moderated_at:new Date().toISOString()}).eq('id',b.comment_id);if(error)throw error;return json({ok:true})}
 if(a==='list_submissions'){const {data,error}=await s.from('character_submissions').select('id,user_id,account_pseudo,account_email,status,source_purged_at,created_at').order('created_at',{ascending:false});if(error)throw error;return json({ok:true,submissions:data||[]})}
 if(a==='generate_character'){const {data:sub,error}=await s.from('character_submissions').select('*').eq('id',b.submission_id).single();if(error)throw error;if(!sub.source_payload)throw new Error('SOURCE_PURGED');const g=await ai(sub.source_payload,s);const {data:existing}=await s.from('characters').select('id').eq('submission_id',sub.id).maybeSingle();let ch;if(existing){const {data,error}=await s.from('characters').update({public_name:g.bible.character_name,public_description:g.bible.personality_summary,status:'author_review',bible:g.bible,ai_generated:true,visible_to_user:true,canon_status:'PROVISOIRE',canon_version:'v1.0'}).eq('id',existing.id).select('*').single();if(error)throw error;ch=data}else{const {data,error}=await s.from('characters').insert({submission_id:sub.id,user_id:sub.user_id,public_name:g.bible.character_name,public_description:g.bible.personality_summary,status:'author_review',bible:g.bible,ai_generated:true,visible_to_user:true,canon_status:'PROVISOIRE',canon_version:'v1.0'}).select('*').single();if(error)throw error;ch=data}await s.from('character_submissions').update({status:'ai_draft'}).eq('id',sub.id);await s.from('character_generation_runs').insert({submission_id:sub.id,character_id:ch.id,model:g.model,status:'completed'});return json({ok:true,character:ch})}
 if(a==='purge_submission_source'){const {data:sub,error}=await s.from('character_submissions').select('photo_path').eq('id',b.submission_id).single();if(error)throw error;if(sub.photo_path)await s.storage.from('sinjira-character-sources').remove([sub.photo_path]);const {error:e}=await s.from('character_submissions').update({source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()}).eq('id',b.submission_id);if(e)throw e;return json({ok:true})}
 if(a==='list_characters'){const [{data:chars,error},{data:novels}]=await Promise.all([s.from('characters').select('*,novels(title)').order('updated_at',{ascending:false}),s.from('novels').select('id,title').order('sort_order')]);if(error)throw error;return json({ok:true,characters:(chars||[]).map((x:any)=>({...x,novel_title:x.novels?.title||''})),novels:novels||[]})}

 if(a==='canon_overview'){
   const contexts=await loadSinjiraCanonContext(s);
   return json({ok:true,contexts});
 }

 if(a==='save_character'){const c=b.character||{};const canonStatus=['PROVISOIRE','CANON','SECRET_AUTEUR','A_ARBITRER'].includes(c.canon_status)?c.canon_status:'PROVISOIRE';
 if(canonStatus==='CANON' && c.author_confirmed_canon!==true) throw new Error('CANON_CONFIRMATION_REQUIRED');
 if(c.novel_id){const {data:novel}=await s.from('novels').select('slug').eq('id',c.novel_id).maybeSingle();if(novel?.slug==='la-cendre-du-jugement' && c.author_confirmed_retcon!==true) throw new Error('ROMAN1_LOCKED');}
 const payload={public_name:String(c.public_name||'').slice(0,160),public_description:String(c.public_description||'').slice(0,8000),status:c.status||'author_review',novel_id:c.novel_id||null,novel_note:String(c.novel_note||'').slice(0,500),visible_to_user:Boolean(c.visible_to_user),canon_status:canonStatus,canon_version:String(c.canon_version||'v1.0').slice(0,30),bible:c.bible||{}};
 const {data,error}=await s.from('characters').update(payload).eq('id',c.id).select('*').single();if(error)throw error;if(data?.submission_id)await s.from('character_submissions').update({status:payload.status}).eq('id',data.submission_id);return json({ok:true,character:data})}
 return json({ok:false,error:'Action inconnue.'},400)
 }catch(e){console.error(e);if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);if(e?.message==='ADMIN_REQUIRED')return json({ok:false,error:'Administration refusée.'},403);if(e?.message==='OPENAI_NOT_CONFIGURED')return json({ok:false,error:'La clé OpenAI n’est pas encore configurée côté serveur.'},503);if(e?.message==='SOURCE_PURGED')return json({ok:false,error:'Les données sources ont déjà été supprimées.'},409);if(e?.message==='CANON_CONFIRMATION_REQUIRED')return json({ok:false,error:'Confirmez explicitement que ce personnage est établi par un manuscrit officiel finalisé avant de le passer CANON.'},409);if(e?.message==='ROMAN1_LOCKED')return json({ok:false,error:'Le Roman 1 est verrouillé. Pour y attribuer rétroactivement un nouveau personnage, confirmez explicitement la décision auteur / retcon.'},409);return json({ok:false,error:'Erreur administration V18.'},500)}});