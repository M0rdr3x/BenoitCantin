import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';
import {SINJIRA_CANON_PUBLIC_GUIDE} from '../_shared/sinjira-canon-public.ts';
import {loadSinjiraCanonContext,canonPrompt} from '../_shared/sinjira-canon-context.ts';

const PRIVATE_KEYS=['prenom_legal','nom_legal','courriel','telephone','date_naissance','region','courriel_retrait','nom_signature','parent_nom','parent_courriel','parent_telephone','parent_signature','compte_courriel','compte_pseudo'];
function creativePayload(src:Record<string,unknown>){const out:Record<string,unknown>={};for(const [k,v] of Object.entries(src||{})){if(PRIVATE_KEYS.includes(k)||k.startsWith('parent_')||k.startsWith('photo'))continue;out[k]=v}return out}
const schema={type:'object',additionalProperties:false,required:['character_name','age_range','gender','appearance','origin','role','faction','personality_summary','values','strengths','weaknesses','fears','contradictions','voice','motivations','relationships','narrative_arc','novel_fit','recommended_placement','continuity_flags','canon_notes','prohibited_elements'],properties:{
 character_name:{type:'string'},age_range:{type:'string'},gender:{type:'string'},appearance:{type:'string'},origin:{type:'string'},role:{type:'string'},faction:{type:'string'},personality_summary:{type:'string'},
 values:{type:'array',items:{type:'string'}},strengths:{type:'array',items:{type:'string'}},weaknesses:{type:'array',items:{type:'string'}},fears:{type:'array',items:{type:'string'}},contradictions:{type:'array',items:{type:'string'}},
 voice:{type:'string'},motivations:{type:'array',items:{type:'string'}},relationships:{type:'array',items:{type:'string'}},narrative_arc:{type:'string'},novel_fit:{type:'string'},recommended_placement:{type:'string'},continuity_flags:{type:'array',items:{type:'string'}},canon_notes:{type:'array',items:{type:'string'}},prohibited_elements:{type:'array',items:{type:'string'}}
}};
async function generate(answers:Record<string,unknown>,service:any){
 const key=Deno.env.get('OPENAI_API_KEY');if(!key)return null;
 const model=Deno.env.get('OPENAI_CHARACTER_MODEL')||'gpt-5';
 const contexts=await loadSinjiraCanonContext(service);
 const privateCanon=canonPrompt(contexts);
 const res=await fetch('https://api.openai.com/v1/responses',{method:'POST',headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:JSON.stringify({
  model,store:false,input:[{role:'system',content:`Tu aides Benoit Cantin à préparer un brouillon de personnage ORIGINAL pour SINJIRA.

RÈGLES PUBLIQUES :
${SINJIRA_CANON_PUBLIC_GUIDE}

CONTEXTE CANONIQUE PRIVÉ FOURNI PAR LE SERVEUR :
${privateCanon}

Contraintes obligatoires :
- Les éléments SECRET_AUTEUR servent uniquement de garde-fous de continuité. Ne les révèle jamais dans la fiche visible au fan et ne les résous jamais.
- Les éléments À ARBITRER ne doivent jamais être tranchés automatiquement.
- Le Roman 1 — La Cendre du Jugement est verrouillé : ne prétends jamais qu’un nouveau personnage y apparaît déjà. La recommandation normale est un futur roman ou un emplacement à décider par Benoit Cantin.
- N’utilise pas le nom d’un personnage canonique existant et ne duplique pas sa fonction dramatique.
- Aucune magie ni superpouvoir n’est établi : reste technologique, humain, informationnel ou volontairement non résolu.
- Le participant décrit sa personnalité réelle, mais transforme fortement identité, contexte, apparence et biographie.
- Ne copie aucune personne publique ni personnage existant.
- Ne produis jamais de coordonnées personnelles.
- Le résultat est toujours PROVISOIRE et n’est jamais canonique avant validation explicite de Benoit Cantin.
- Dans continuity_flags, indique toute proximité risquée avec un personnage, mystère, lieu, technologie ou fil canonique réservé.
`},{role:'user',content:JSON.stringify(creativePayload(answers))}],
  text:{format:{type:'json_schema',name:'sinjira_character_bible',strict:true,schema}}
 })});
 if(!res.ok)throw new Error(`OPENAI_${res.status}`);const data=await res.json();return {model,bible:JSON.parse(data.output_text)};
}
Deno.serve(async(req)=>{if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
 try{const user=await requiredUser(req),service=serviceClient(),{answers,photo_path,manual_only=true}=await req.json();const {data:p}=await service.from('profiles').select('pseudo,display_name').eq('user_id',user.id).maybeSingle();
 const {data:sub,error}=await service.from('character_submissions').insert({user_id:user.id,account_pseudo:p?.pseudo||p?.display_name||'',account_email:user.email||'',source_payload:answers||{},photo_path:photo_path||null,status:'submitted'}).select('*').single();if(error)throw error;
 let generated=null;if(manual_only!==true){try{generated=await generate(answers||{},service)}catch(e){await service.from('character_generation_runs').insert({submission_id:sub.id,status:'failed',error_text:String(e?.message||e)});}}
 if(generated){const b=generated.bible;const {data:ch,error:ce}=await service.from('characters').insert({submission_id:sub.id,user_id:user.id,public_name:b.character_name,public_description:b.personality_summary,status:'author_review',bible:b,ai_generated:true,visible_to_user:true,canon_status:'PROVISOIRE',canon_version:'v1.0'}).select('*').single();if(ce)throw ce;await service.from('character_submissions').update({status:'ai_draft'}).eq('id',sub.id);await service.from('character_generation_runs').insert({submission_id:sub.id,character_id:ch.id,model:generated.model,status:'completed'});return json({ok:true,submission_id:sub.id,character_id:ch.id,ai_generated:true});}
 return json({ok:true,submission_id:sub.id,ai_generated:false});
 }catch(e){console.error(e);if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);return json({ok:false,error:'Impossible de transmettre le questionnaire.'},500)}});