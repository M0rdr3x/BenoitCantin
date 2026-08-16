import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';
import {SINJIRA_CANON_PUBLIC_GUIDE} from '../_shared/sinjira-canon-public.ts';
import {loadSinjiraCanonContext,canonPrompt} from '../_shared/sinjira-canon-context.ts';

const PRIVATE_KEYS=['prenom_legal','nom_legal','courriel','telephone','date_naissance','region','courriel_retrait','nom_signature','parent_nom','parent_courriel','parent_telephone','parent_signature','compte_courriel','compte_pseudo'];
const MAX_ANSWERS_BYTES=120_000;
function characterAiEnabled(){return String(Deno.env.get('SINJIRA_CHARACTER_AI_ENABLED')||'').trim().toLowerCase()==='true'}
function creativePayload(src:Record<string,unknown>){const out:Record<string,unknown>={};for(const [k,v] of Object.entries(src||{})){if(PRIVATE_KEYS.includes(k)||k.startsWith('parent_')||k.startsWith('photo'))continue;out[k]=v}return out}
function validateAnswers(value:unknown){
 if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('INVALID_ANSWERS');
 const encoded=new TextEncoder().encode(JSON.stringify(value));
 if(encoded.byteLength>MAX_ANSWERS_BYTES)throw new Error('ANSWERS_TOO_LARGE');
 return value as Record<string,unknown>;
}
const schema={type:'object',additionalProperties:false,required:['character_name','age_range','gender','appearance','origin','role','faction','personality_summary','values','strengths','weaknesses','fears','contradictions','voice','motivations','relationships','narrative_arc','novel_fit','recommended_placement','continuity_flags','canon_notes','prohibited_elements'],properties:{
 character_name:{type:'string'},age_range:{type:'string'},gender:{type:'string'},appearance:{type:'string'},origin:{type:'string'},role:{type:'string'},faction:{type:'string'},personality_summary:{type:'string'},
 values:{type:'array',items:{type:'string'}},strengths:{type:'array',items:{type:'string'}},weaknesses:{type:'array',items:{type:'string'}},fears:{type:'array',items:{type:'string'}},contradictions:{type:'array',items:{type:'string'}},
 voice:{type:'string'},motivations:{type:'array',items:{type:'string'}},relationships:{type:'array',items:{type:'string'}},narrative_arc:{type:'string'},novel_fit:{type:'string'},recommended_placement:{type:'string'},continuity_flags:{type:'array',items:{type:'string'}},canon_notes:{type:'array',items:{type:'string'}},prohibited_elements:{type:'array',items:{type:'string'}}
}};
async function generate(answers:Record<string,unknown>,service:any){
 if(!characterAiEnabled())throw new Error('CHARACTER_AI_DISABLED');
 const key=Deno.env.get('OPENAI_API_KEY');if(!key)throw new Error('OPENAI_NOT_CONFIGURED');
 const model=Deno.env.get('OPENAI_CHARACTER_MODEL')||'gpt-5';
 const contexts=await loadSinjiraCanonContext(service);const privateCanon=canonPrompt(contexts);
 const res=await fetch('https://api.openai.com/v1/responses',{method:'POST',headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:JSON.stringify({
  model,store:false,input:[{role:'system',content:`Tu aides Benoit Cantin à préparer un brouillon de personnage ORIGINAL pour SINJIRA.\n\nRÈGLES PUBLIQUES :\n${SINJIRA_CANON_PUBLIC_GUIDE}\n\nCONTEXTE CANONIQUE PRIVÉ FOURNI PAR LE SERVEUR :\n${privateCanon}\n\nContraintes obligatoires :\n- Les éléments SECRET_AUTEUR servent uniquement de garde-fous de continuité. Ne les révèle jamais dans la fiche visible au fan et ne les résous jamais.\n- Les éléments À ARBITRER ne doivent jamais être tranchés automatiquement.\n- Le Roman 1 — La Cendre du Jugement est verrouillé : ne prétends jamais qu’un nouveau personnage y apparaît déjà. La recommandation normale est un futur roman ou un emplacement à décider par Benoit Cantin.\n- N’utilise pas le nom d’un personnage canonique existant et ne duplique pas sa fonction dramatique.\n- Aucune magie ni superpouvoir n’est établi : reste technologique, humain, informationnel ou volontairement non résolu.\n- Le participant décrit sa personnalité réelle, mais transforme fortement identité, contexte, apparence et biographie.\n- Ne copie aucune personne publique ni personnage existant.\n- Ne produis jamais de coordonnées personnelles.\n- Le résultat est toujours PROVISOIRE et n’est jamais canonique avant validation explicite de Benoit Cantin.\n- Dans continuity_flags, indique toute proximité risquée avec un personnage, mystère, lieu, technologie ou fil canonique réservé.`},{role:'user',content:JSON.stringify(creativePayload(answers))}],
  text:{format:{type:'json_schema',name:'sinjira_character_bible',strict:true,schema}}
 })});
 if(!res.ok)throw new Error(`OPENAI_${res.status}`);const data=await res.json();return {model,bible:JSON.parse(data.output_text)};
}
async function notifyAdmin(service:any,sub:any,user:any,p:any,updated=false){
 let internal=false,email=false;
 try{
  const {error}=await service.from('admin_notifications').insert({
    notification_type:'character_submission',title:updated?'Questionnaire SINJIRA™ mis à jour':'Nouveau questionnaire SINJIRA™',
    body:`${updated?'Mise à jour':'Nouvelle participation'} de ${p?.pseudo||p?.display_name||user.email||'un membre'}.`,
    related_user_id:user.id,related_entity_type:'character_submission',related_entity_id:sub.id
  });
  internal=!error;
 }catch(e){console.warn('admin notification unavailable',e)}
 const resend=Deno.env.get('RESEND_API_KEY');
 const from=Deno.env.get('REPORT_FROM_EMAIL');
 const to=Deno.env.get('CHARACTER_REPORT_TO_EMAIL')||Deno.env.get('FRACTURE_REPORT_TO_EMAIL')||'kingtyrano@gmail.com';
 if(resend&&from){
  try{
   const r=await fetch('https://api.resend.com/emails',{method:'POST',headers:{Authorization:`Bearer ${resend}`,'Content-Type':'application/json'},body:JSON.stringify({
    from,to:[to],subject:updated?'SINJIRA™ — questionnaire personnage mis à jour':'SINJIRA™ — nouveau questionnaire personnage',
    html:`<p>${updated?'Un questionnaire':'Une nouvelle participation au Registre des Consciences'} a été ${updated?'mis à jour':'enregistrée'}.</p><p><strong>Compte :</strong> ${String(p?.pseudo||p?.display_name||'Compte SINJIRA™').replace(/[<>&]/g,'')}<br><strong>Courriel :</strong> ${String(user.email||'').replace(/[<>&]/g,'')}<br><strong>Dossier :</strong> ${sub.id}</p><p>Consultez l’administration SINJIRA™ pour voir le questionnaire complet.</p>`
   })});
   email=r.ok;if(!r.ok)console.warn('resend',await r.text());
  }catch(e){console.warn('email notification failed',e)}
 }
 return {internal,email};
}

Deno.serve(async(req)=>{if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
 try{
  const user=await requiredUser(req),service=serviceClient(),body=await req.json();
  const answers=validateAnswers(body?.answers||{}),photo_path=body?.photo_path?String(body.photo_path).slice(0,500):null,update_existing=body?.update_existing===true;
  const aiRequested=body?.manual_only===false;
  const aiAllowed=aiRequested&&characterAiEnabled();
  const owner=String(user?.email||'').trim().toLowerCase()==='kingtyrano@gmail.com';
  const [{data:p},{data:existingSubmission},{data:existingCharacter}]=await Promise.all([
    service.from('profiles').select('pseudo,display_name').eq('user_id',user.id).maybeSingle(),
    service.from('character_submissions').select('*').eq('user_id',user.id).order('created_at',{ascending:false}).limit(1).maybeSingle(),
    service.from('characters').select('id,status,submission_id').eq('user_id',user.id).order('updated_at',{ascending:false}).limit(1).maybeSingle()
  ]);

  if((existingSubmission||existingCharacter)&&!(owner&&update_existing)){
    return json({ok:false,error:'Ce Compte SINJIRA possède déjà une demande ou son unique personnage. Modifiez votre dossier existant au lieu d’en créer un deuxième.',code:'ONE_CHARACTER_PER_ACCOUNT'},409);
  }

  if(owner&&update_existing&&(existingSubmission||existingCharacter)){
    let sub=existingSubmission;
    if(existingSubmission){
      const nextStatus=existingCharacter?'assigned':'submitted';
      const {data:updated,error:updateError}=await service.from('character_submissions').update({
        account_pseudo:p?.pseudo||p?.display_name||'AbyssTime',
        account_email:user.email||'',
        source_payload:answers,
        photo_path:photo_path||existingSubmission.photo_path||null,
        status:nextStatus,
        source_purged_at:null
      }).eq('id',existingSubmission.id).select('*').single();
      if(updateError)throw updateError;
      sub=updated;
    }else{
      const {data:created,error:createError}=await service.from('character_submissions').insert({
        user_id:user.id,account_pseudo:p?.pseudo||p?.display_name||'AbyssTime',account_email:user.email||'',
        source_payload:answers,photo_path:photo_path||null,status:existingCharacter?'assigned':'submitted'
      }).select('*').single();
      if(createError)throw createError;
      sub=created;
    }

    try{await service.rpc('ensure_sinjira_owner_character')}catch(e){console.warn('owner repair rpc unavailable',e)}
    const notification=await notifyAdmin(service,sub,user,p,true);
    return json({ok:true,submission_id:sub.id,character_id:existingCharacter?.id||null,ai_generated:false,ai_enabled:characterAiEnabled(),updated_existing:true,notification_created:notification.internal,notification_sent:notification.email});
  }

  const {data:sub,error}=await service.from('character_submissions').insert({user_id:user.id,account_pseudo:p?.pseudo||p?.display_name||'',account_email:user.email||'',source_payload:answers,photo_path:photo_path||null,status:'submitted'}).select('*').single();if(error)throw error;
  const notification=await notifyAdmin(service,sub,user,p,false);
  let generated=null;
  if(aiAllowed){
    try{generated=await generate(answers,service)}
    catch(e){await service.from('character_generation_runs').insert({submission_id:sub.id,status:'failed',error_text:String(e?.message||e).slice(0,1000)});}
  }
  if(generated){const b=generated.bible;const {data:ch,error:ce}=await service.from('characters').insert({submission_id:sub.id,user_id:user.id,public_name:b.character_name,public_description:b.personality_summary,status:'author_review',bible:b,ai_generated:true,visible_to_user:true,canon_status:'PROVISOIRE',canon_version:'v1.0'}).select('*').single();if(ce)throw ce;await service.from('character_submissions').update({status:'ai_draft'}).eq('id',sub.id);await service.from('character_generation_runs').insert({submission_id:sub.id,character_id:ch.id,model:generated.model,status:'completed'});return json({ok:true,submission_id:sub.id,character_id:ch.id,ai_generated:true,ai_enabled:true,notification_created:notification.internal,notification_sent:notification.email});}
  return json({ok:true,submission_id:sub.id,ai_generated:false,ai_enabled:characterAiEnabled(),ai_requested:aiRequested,notification_created:notification.internal,notification_sent:notification.email});
 }catch(e){console.error(e);if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);if(e?.message==='INVALID_ANSWERS')return json({ok:false,error:'Questionnaire invalide.'},400);if(e?.message==='ANSWERS_TOO_LARGE')return json({ok:false,error:'Le questionnaire dépasse la taille autorisée.'},413);return json({ok:false,error:'Impossible de transmettre le questionnaire.'},500)}});
