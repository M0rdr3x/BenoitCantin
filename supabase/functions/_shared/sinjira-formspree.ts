// SINJIRA — avis techniques non nominatifs vers Formspree.
// Jamais de mot de passe, courriel, date de naissance, formulaire, photo, ou identifiant de compte.
type EventName = 'compte_confirme' | 'registre_enregistre';
const ENDPOINTS: Record<EventName,string> = {
  compte_confirme: 'https://formspree.io/f/xzeeqynp',
  registre_enregistre: 'https://formspree.io/f/mrppvrwa'
};

type DeliveryResult = {accepted:boolean; already:boolean; configured:boolean};

// Le déclencheur d'envoi est uniquement côté serveur, après succès confirmé dans Supabase.
// Une clé primaire unique sur (event_type, source_id) élimine les doubles avis.
export async function sendFormspreeNotice(service:any, kind:EventName, sourceId:string): Promise<DeliveryResult> {
  const url=ENDPOINTS[kind];
  if (!url || !/^[0-9a-f]{8}-[0-9a-f-]{27,36}$/i.test(String(sourceId))) {
    return {accepted:false,already:false,configured:false};
  }
  const {data:receipt,error:reserveError}=await service
    .from('sinjira_formspree_events')
    .insert({event_type:kind,source_id:sourceId,delivery_status:'pending'})
    .select('id')
    .single();
  if (reserveError){
    if (reserveError.code==='23505') return {accepted:false,already:true,configured:true};
    console.warn('[SINJIRA Formspree]', 'OUTBOX_RESERVATION_FAILED');
    return {accepted:false,already:false,configured:false};
  }
  // Le code public transmis au tiers est aléatoire, distinct de l'ID de compte / dossier.
  const fields={
    event:kind,
    reference:String(receipt.id),
    message:kind==='compte_confirme' ? 'Un compte SINJIRA a été confirmé.' : 'Un questionnaire SINJIRA a été enregistré.',
    date:new Date().toISOString()
  };
  let accepted=false;
  try{
    const response=await fetch(url,{
      method:'POST',
      headers:{'Content-Type':'application/json','Accept':'application/json'},
      body:JSON.stringify(fields),
      redirect:'error',
      signal:AbortSignal.timeout(6000)
    });
    accepted=response.ok;
    if (!accepted) console.warn('[SINJIRA Formspree]', 'DELIVERY_REJECTED');
  }catch{
    console.warn('[SINJIRA Formspree]', 'DELIVERY_UNAVAILABLE');
  }
  const {error:stateError}=await service.from('sinjira_formspree_events')
    .update({delivery_status:accepted?'sent':'failed',sent_at:accepted?new Date().toISOString():null})
    .eq('id',receipt.id);
  if(stateError)console.warn('[SINJIRA Formspree]','OUTBOX_STATUS_UPDATE_FAILED');
  return {accepted,already:false,configured:true};
}
