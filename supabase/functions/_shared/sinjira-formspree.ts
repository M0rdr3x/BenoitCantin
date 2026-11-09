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

const QUESTION_LABELS:Record<string,string>={
  appearance_build:'Apparence — silhouette générale',
  appearance_height:'Apparence — taille approximative',
  appearance_hair:'Apparence — cheveux',
  appearance_eyes:'Apparence — yeux',
  appearance_style:'Apparence — style vestimentaire',
  appearance_distinctive:'Apparence — signe distinctif',
  scale_reserved_social:'Personnalité — réservé / sociable (1 à 5)',
  scale_cautious_bold:'Personnalité — prudent / audacieux (1 à 5)',
  scale_calm_impulsive:'Personnalité — calme / impulsif (1 à 5)',
  scale_logic_instinct:'Personnalité — logique / instinctif (1 à 5)',
  scale_conciliatory_confrontational:'Personnalité — conciliant / confrontant (1 à 5)',
  scale_follower_leader:'Personnalité — suiveur / meneur (1 à 5)',
  scale_wary_trusting:'Personnalité — méfiant / confiant (1 à 5)',
  scale_flexible_rigid:'Personnalité — flexible / rigide (1 à 5)',
  strengths:'Forces',
  weaknesses:'Faiblesses',
  values:'Valeurs',
  pressure_first_reaction:'Premier réflexe face à un problème',
  conflict_reaction:'Réaction en cas de conflit',
  danger_reaction:'Réaction face au danger',
  mistake_reaction:'Réaction face à une erreur',
  trust_speed:'Facilité à accorder sa confiance',
  preferred_group:'Préférence de travail en groupe',
  communication_style:'Façon de communiquer',
  humor_style:'Type d’humour',
  skills:'Compétences',
  organization_style:'Organisation personnelle',
  preferred_environment:'Environnement préféré',
  narrative_role:'Rôle souhaité pour le personnage',
  narrative_importance:'Importance souhaitée dans le récit',
  moral_orientation:'Orientation morale',
  placement_preference:'Place souhaitée dans SINJIRA',
  prohibited_elements:'Éléments ou destins refusés',
  personality_notes:'Notes libres sur la personnalité'
};

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
    lines.push(`${QUESTION_LABELS[key]||key.replaceAll('_',' ')} : ${text}`);
  }
  // Les limites évitent une soumission externe trop volumineuse et l'envoi
  // d'un questionnaire incomplet (ne pas tronquer silencieusement).
  const formatted=lines.join('\n');
  if(!formatted || new TextEncoder().encode(formatted).byteLength>28000)return null;
  return formatted;
}

// Le déclencheur est uniquement côté serveur après réussite confirmée.
// La contrainte SQL (event_type,source_id) évite les doubles avis et réponses automatiques.
async function sendFormspreeNoticeCore(
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
    if(reserveError.code==='23505'){
      // Un avis déjà accepté ne doit jamais être renvoyé ni annoncé comme un échec.
      // La consultation est réservée au serveur et ne divulgue aucune identité.
      const {data:prior,error:priorError}=await service
        .from('sinjira_formspree_events')
        .select('delivery_status')
        .eq('event_type',kind)
        .eq('source_id',sourceId)
        .maybeSingle();
      return {
        accepted:!priorError&&prior?.delivery_status==='sent',
        already:true,
        configured:true,
        reason:priorError?'OUTBOX_STATE_UNAVAILABLE':undefined
      };
    }
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
  // Par défaut PostgREST peut réussir un UPDATE qui modifie zéro ligne.
  // Le SELECT du seul identifiant confirme que la réservation a bien été mise
  // à jour, sans exposer son contenu ni affaiblir RLS.
  const {data:updatedStatus,error:stateError}=await service.from('sinjira_formspree_events')
    .update({delivery_status:accepted?'sent':'failed',sent_at:accepted?new Date().toISOString():null})
    .eq('id',receipt.id)
    .select('id')
    .maybeSingle();
  if(stateError || updatedStatus?.id!==receipt.id){
    // Formspree a peut-être accepté la requête, mais son statut ne peut pas être
    // certifié dans le journal. Ne jamais annoncer une livraison prouvée,
    // et ne pas rejouer automatiquement un POST possiblement accepté.
    console.warn('[SINJIRA Formspree]','OUTBOX_STATUS_UPDATE_FAILED');
    return {accepted:false,already:false,configured:true,reason:'OUTBOX_STATUS_UPDATE_FAILED'};
  }
  return {accepted,already:false,configured:true,reason:accepted?undefined:'DELIVERY_FAILED'};
}

// Un avis externe ne doit JAMAIS faire échouer l'inscription confirmée ou la
// sauvegarde du Registre. Cet appel conserve un résultat borné et non nominatif,
// même si Supabase, Formspree ou le réseau lève une exception inattendue.
export async function sendFormspreeNotice(
  service:any, kind:EventName, sourceId:string, options:FormspreeOptions
): Promise<DeliveryResult> {
  try {
    return await sendFormspreeNoticeCore(service,kind,sourceId,options);
  } catch {
    console.warn('[SINJIRA Formspree]','SECONDARY_CHANNEL_UNAVAILABLE');
    return {accepted:false,already:false,configured:false,reason:'SECONDARY_CHANNEL_UNAVAILABLE'};
  }
}
