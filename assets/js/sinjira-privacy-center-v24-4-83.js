import {getSupabase,requireUser,escapeHtml,formatDate} from './sinjira-supabase.js';

const form=document.querySelector('[data-privacy-request-form]');
const list=document.querySelector('[data-privacy-requests]');
const statusNode=document.querySelector('[data-privacy-status]');
const labels={access:'Accès',portability:'Copie / portabilité',rectification:'Rectification',deletion:'Suppression',consent_withdrawal:'Retrait de consentement',objection:'Opposition',complaint:'Plainte',other:'Autre'};
const statusLabels={open:'Ouverte',identity_check:'Vérification d’identité',in_review:'En révision',waiting_user:'Information demandée',completed:'Terminée',refused:'Refusée / limitée',cancelled:'Annulée'};
let authenticated=false;
const permanentlyDisabled=new Set([...(form?.elements||[])].filter(el=>el.disabled));
function setFormLocked(locked){
  for(const el of form?.elements||[]){
    if(permanentlyDisabled.has(el)){el.disabled=true;continue}
    el.disabled=locked;
  }
}
setFormLocked(true);

function showStatus(message,type='info'){
  if(!statusNode)return;
  statusNode.hidden=false;
  statusNode.dataset.statusType=type;
  statusNode.textContent=message;
}

function render(rows){
  if(!list)return;
  if(!rows.length){list.innerHTML='<p>Aucune demande enregistrée pour ce compte.</p>';return;}
  list.innerHTML=rows.map(row=>`<article class="v24-panel"><h3>${escapeHtml(labels[row.request_type]||row.request_type)}</h3><p><strong>${escapeHtml(statusLabels[row.status]||row.status)}</strong> · créée le ${escapeHtml(formatDate(row.created_at))}</p><p>Échéance interne cible : ${escapeHtml(formatDate(row.due_at))}</p>${row.response_note?`<p><strong>Réponse :</strong> ${escapeHtml(row.response_note)}</p>`:''}</article>`).join('');
}

async function loadRequests(){
  const {data=[],error}=await getSupabase().rpc('privacy_my_requests',{p_limit:20});
  if(error)throw error;
  render(data);
}

(async()=>{
  try{
    await requireUser('/compte/connexion.html');
    authenticated=true;
    setFormLocked(false);
  }catch(error){
    showStatus('Connexion requise pour utiliser le Centre Vie privée.','error');
    return;
  }
  try{
    await loadRequests();
  }catch(error){
    showStatus('Vos demandes existantes ne peuvent pas être chargées pour le moment. Vous pouvez tout de même créer une nouvelle demande.','error');
  }
})();

form?.addEventListener('submit',async event=>{
  event.preventDefault();
  if(!authenticated){
    showStatus('Connexion requise avant d’envoyer une demande.','error');
    return;
  }
  const button=form.querySelector('button[type="submit"]');
  if(button)button.disabled=true;
  try{
    const fd=new FormData(form);
    const requestType=String(fd.get('request_type')||'').trim();
    const details=String(fd.get('details')||'').trim();
    if(!requestType)throw new Error('Choisissez un type de demande.');
    const {error}=await getSupabase().rpc('privacy_create_request',{p_request_type:requestType,p_details:details||null});
    if(error)throw error;
    form.reset();
    showStatus('Votre demande a été enregistrée. Elle apparaît maintenant dans votre suivi.','success');
    try{
      await loadRequests();
    }catch(refreshError){
      showStatus('Votre demande a bien été enregistrée, mais le suivi ne peut pas être rafraîchi pour le moment.','info');
    }
  }catch(error){
    const msg=String(error?.message||'');
    if(msg.includes('PRIVACY_REQUEST_OPEN_LIMIT'))showStatus('Vous avez déjà plusieurs demandes ouvertes. Terminez leur suivi avant d’en créer une nouvelle.','error');
    else if(msg.includes('PRIVACY_REQUEST_DETAILS_TOO_LONG'))showStatus('Les précisions sont trop longues.','error');
    else showStatus('Impossible d’enregistrer la demande pour le moment.','error');
  }finally{if(button)button.disabled=false;}
});
