// SINJIRA — livraison Formspree après persistance / vérification Supabase.
// L'inscription et les réponses officielles restent dans Supabase.
// Aucun mot de passe, code parental, date de naissance, photo ou pièce jointe n'est partagé.
type EventName = 'compte_confirme' | 'registre_enregistre';
const ENDPOINTS: Record<EventName,string> = {
  compte_confirme: 'https://formspree.io/f/xzeeqynp',
  registre_enregistre: 'https://formspree.io/f/mrppvrwa'
};
export type FormspreeOptions = {
  // L'adresse doit venir du compte authentifié (jamais d'un champ fourni au serveur).
  email: string;
  // Seulement pour le Registre, avec consentement exprès du participant.
  answers?: Record<string,unknown>;
};
type DeliveryResult = {accepted:boolean; already:boolean; configured:boolean; reason?:string};

// Liste blanche : champs de personnalité / création affichés dans le Registre.
// Ne pas ajouter ici de données d'identité, famille, profil privé ou de sécurité.
const QUESTIONNAIRE_FIELDS = [
  'appearance_build','appearance_height','appearance_hair','appearance_eyes',
  'appearance_style','appearance_distinctive','scale_reserved_social','scale_cautious_bold',
  'scale_calm_impulsive','scale_logic_instinct','scale_conciliatory_confrontational',
  'scale_follower_leader','scale_wary_trusting','scale_flexible_rigid',
  'strengths','weaknesses','values','pressure_first_reaction','conflict_reaction',
  'danger_reaction','mistake_reaction','trust_speed','preferred_group',
  'communication_style','humor_style','skills','organization_style','preferred_environment',
  'narrative_role','narrative_importance','moral_orientation','placement_preference',
  'prohibited_elements','personality_notes'
] as const;

function safeEmail(value:unknown):string {
  const email=String(value||'').trim().toLowerCase();
  if(email.length>254 || !/^[^\s@]{1,64}@[^\s@]+\.[^\s@]+$/.test(email) || /[\r\n]/.test(email))return '';
  return email;
}

function questionnaireText(answers:Record<string,unknown>):string|null {
  const lines:string[]=[];
  for(const key of QUESTIONNAIRE_FIELDS){
    const value=answers[key];
    if(value==null || value==='')continue;
    const parts=Array.isArray(value)?value.map(String):[String(value)];
    const text=parts.map(v=>v.trim()).filter(Boolean).join(', ');
    if(!text)continue;
    lines.push(`${key.replaceAll('_',' ')} : ${text}`);
  }
  // Les limites évitent une soumission externe trop volumineuse et l'envoi
  // d'un questionnaire incomplet (ne pas tronquer silencieusement).
  const formatted=lines.join('\n');
  if(!formatted || new TextEncoder().encode(formatted).byteLength>28000)return null;
  return formatted;
}

// Le déclencheur est uniquement côté serveur après réussite confirmée.
// La contrainte SQL (event_type,source_id) évite les doubles avis et réponses automatiques.
export async function sendFormspreeNotice(
  service:any, kind:EventName, sourceId:string, options:FormspreeOptions
): Promise<DeliveryResult> {
  const url=ENDPOINTS[kind];
  const email=safeEmail(options?.email);
  if(!url || !email || !/^[0-9a-f]{8}-[0-9a-f-]{27,36}$/i.test(String(sourceId))){
    return {accepted:false,already:false,configured:false,reason:'INVALID_RECIPIENT_OR_SOURCE'};
  }
  const questionnaire=kind==='registre_enregistre' ? questionnaireText(options?.answers||{}) : null;
  if(kind==='registre_enregistre' && !questionnaire){
    return {accepted:false,already:false,configured:false,reason:'INVALID_QUESTIONNAIRE_EXPORT'};
  }
  // Toute référence transmise à Formspree est aléatoire et distincte de la clé de dossier.
  const {data:receipt,error:reserveError}=await service
    .from('sinjira_formspree_events')
    .insert({event_type:kind,source_id:sourceId,delivery_status:'pending'})
    .select('id')
    .single();
  if(reserveError){
    if(reserveError.code==='23505')return {accepted:false,already:true,configured:true};
    console.warn('[SINJIRA Formspree]','OUTBOX_RESERVATION_FAILED');
    return {accepted:false,already:false,configured:false,reason:'OUTBOX_RESERVATION_FAILED'};
  }
  const fields:Record<string,string>={
    email, // Champ officiel Formspree : destinataire de la réponse automatique.
    event:kind,
    reference:String(receipt.id),
    message:kind==='compte_confirme'
      ? 'Votre Compte SINJIRA est confirmé. Aucun mot de passe ni donnée de profil ne figure dans cette notification.'
      : 'Participation au Registre des Consciences SINJIRA enregistrée dans la base officielle.',
    date:new Date().toISOString()
  };
  if(questionnaire)fields.questionnaire=questionnaire;
  let accepted=false;
  try{
    const response=await fetch(url,{
      method:'POST',
      headers:{'Content-Type':'application/json','Accept':'application/json'},
      body:JSON.stringify(fields),
      redirect:'error',
      signal:AbortSignal.timeout(6500)
    });
    accepted=response.ok;
    if(!accepted)console.warn('[SINJIRA Formspree]','DELIVERY_REJECTED');
  }catch{
    console.warn('[SINJIRA Formspree]','DELIVERY_UNAVAILABLE');
  }
  const {error:stateError}=await service.from('sinjira_formspree_events')
    .update({delivery_status:accepted?'sent':'failed',sent_at:accepted?new Date().toISOString():null})
    .eq('id',receipt.id);
  if(stateError)console.warn('[SINJIRA Formspree]','OUTBOX_STATUS_UPDATE_FAILED');
  return {accepted,already:false,configured:true,reason:accepted?undefined:'DELIVERY_FAILED'};
}
