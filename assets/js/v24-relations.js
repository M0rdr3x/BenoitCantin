import {getSupabase,requireUser,setStatus,escapeHtml,formatDate} from './sinjira-supabase.js';

const form=document.querySelector('[data-relation-form]');
const status=document.querySelector('[data-relation-status]');
const list=document.querySelector('[data-relations-list]');
const guardianButton=document.querySelector('[data-create-guardian-code]');
const guardianStatus=document.querySelector('[data-guardian-status]');
const guardianCodes=document.querySelector('[data-guardian-codes]');
const guardianLinks=document.querySelector('[data-guardian-links]');
const guardianAdultTools=document.querySelector('[data-guardian-adult-tools]');
const guardianYouthTools=document.querySelector('[data-guardian-youth-tools]');
const guardianNeutralTools=document.querySelector('[data-guardian-neutral-tools]');
const redeemInput=document.querySelector('[data-redeem-guardian-code]');
const redeemButton=document.querySelector('[data-redeem-guardian-code-button]');
const user=await requireUser();
const s=getSupabase();
const CODE_RE=/^YOUTH-[A-Z0-9]{10}$/;
let ageBand='unverified';

function serverMissing(error){const code=String(error?.code||''),text=String(error?.message||'');return code==='PGRST205'||code==='PGRST202'||/family_relationships|guardian_signup_invites|guardian_links|relation .* does not exist|schema cache|Could not find/i.test(text)}
function normalizeCode(v=''){return String(v).trim().toUpperCase().replace(/\s+/g,'')}
function configureGuardianTools(){
  if(guardianAdultTools)guardianAdultTools.hidden=ageBand!=='adult';
  if(guardianYouthTools)guardianYouthTools.hidden=ageBand!=='youth_pending';
  if(guardianNeutralTools)guardianNeutralTools.hidden=['adult','youth_pending'].includes(ageBand);
}
async function refreshAgeBand(){
  const {data,error}=await s.rpc('sinjira_age_band',{p_user_id:user.id});
  if(!error&&typeof data==='string')ageBand=data;
  configureGuardianTools();
}

async function renderGuardian(){
  if(!guardianLinks)return;
  let codesResult={data:[],error:null};
  if(ageBand==='adult'&&guardianCodes){
    codesResult=await s.from('guardian_signup_invites').select('id,invite_code,consented_at,expires_at,used_at,minor_user_id,created_at').eq('guardian_user_id',user.id).order('created_at',{ascending:false}).limit(10);
    if(codesResult.error){guardianCodes.innerHTML=serverMissing(codesResult.error)?'<div class="v2433-server-note">Le module d’autorisation parentale doit être synchronisé côté serveur.</div>':'<div class="v24-empty">Impossible de charger les codes parentaux.</div>'}
    else{
      const rows=codesResult.data||[];
      guardianCodes.innerHTML=rows.length?rows.map(x=>{const used=Boolean(x.used_at),expired=!used&&new Date(x.expires_at).getTime()<Date.now();const state=used?'Utilisé':expired?'Expiré':'Valide';return `<article class="v24-panel"><strong>${escapeHtml(x.invite_code)}</strong><p>${state} · expire ${escapeHtml(formatDate(x.expires_at))}</p>${used?`<small>Utilisé ${escapeHtml(formatDate(x.used_at))}</small>`:''}</article>`}).join(''):'<div class="v24-empty">Aucun code parental créé.</div>';
    }
  }

  const linksResult=await s.from('guardian_links')
    .select('id,minor_user_id,guardian_user_id,status,guardian_role,can_view_contact_metadata,consented_at,revoked_at,created_at')
    .or(`guardian_user_id.eq.${user.id},minor_user_id.eq.${user.id}`)
    .order('created_at',{ascending:false}).limit(20);
  if(linksResult.error){guardianLinks.innerHTML='<div class="v24-empty">Impossible de charger les liens de supervision.</div>';return}
  const rows=linksResult.data||[];
  guardianLinks.innerHTML=rows.length?rows.map(x=>{
    const mine=x.guardian_user_id===user.id?'Tuteur / parent':'Compte jeunesse';
    const active=x.status==='verified';
    return `<article class="v24-panel"><strong>${escapeHtml(mine)} · ${escapeHtml(x.status||'—')}</strong><p>Rôle : ${escapeHtml(x.guardian_role||'parent/tuteur')}</p><small>${x.can_view_contact_metadata?'Métadonnées de contact autorisées':'Métadonnées de contact non autorisées'} · aucun contenu privé de message</small>${active?`<div class="hero-actions"><button class="btn btn-secondary btn-small" type="button" data-revoke-guardian-link="${escapeHtml(x.id)}">Révoquer ce lien</button></div>`:''}</article>`;
  }).join(''):'<div class="v24-empty">Aucun lien de supervision.</div>';
  guardianLinks.querySelectorAll('[data-revoke-guardian-link]').forEach(button=>button.addEventListener('click',async()=>{
    if(!confirm('Révoquer ce lien de supervision? Les fonctions jeunesse qui exigent un tuteur vérifié pourront être limitées.'))return;
    button.disabled=true;
    const {data,error}=await s.rpc('revoke_guardian_link',{p_link_id:button.dataset.revokeGuardianLink});
    if(error||!data?.ok){button.disabled=false;setStatus(guardianStatus,'Impossible de révoquer ce lien pour le moment.','error');return}
    await refreshAgeBand();setStatus(guardianStatus,'Lien de supervision révoqué.','success');await renderGuardian();
  }));
}

guardianButton?.addEventListener('click',async()=>{
  guardianButton.disabled=true;setStatus(guardianStatus,'Création sécurisée du code parental…','info');
  const {data,error}=await s.rpc('create_guardian_signup_invite');
  guardianButton.disabled=false;
  if(error){setStatus(guardianStatus,'Impossible de générer le code parental. Vérifiez que votre compte est adulte et que les exigences de sécurité sont satisfaites.','error');return}
  setStatus(guardianStatus,`Code créé : ${String(data||'')}. Il est à usage unique et expire automatiquement.`,'success');
  await renderGuardian();
});

redeemButton?.addEventListener('click',async()=>{
  const code=normalizeCode(redeemInput?.value||'');
  if(!CODE_RE.test(code)){setStatus(guardianStatus,'Entrez un code valide au format YOUTH-XXXXXXXXXX.','error');return}
  redeemButton.disabled=true;setStatus(guardianStatus,'Vérification du code parental…','info');
  const {data,error}=await s.rpc('redeem_guardian_signup_invite',{p_code:code});
  redeemButton.disabled=false;
  if(error||!data?.ok){setStatus(guardianStatus,'Ce code est invalide, expiré, déjà utilisé ou ne peut pas être associé à ce compte.','error');return}
  if(redeemInput)redeemInput.value='';
  await refreshAgeBand();setStatus(guardianStatus,'Lien parental vérifié. Les protections jeunesse utilisent maintenant cette supervision.','success');await renderGuardian();
});

if(form&&list){
  let ready=true;
  function setFormReady(value){ready=value;for(const el of form.elements){if(el.type==='submit'||el.tagName==='BUTTON')el.disabled=!value}}
  async function render(){
    const {data,error}=await s.from('family_relationships').select('*').eq('owner_user_id',user.id).order('created_at',{ascending:true});
    if(error){ready=!serverMissing(error);setFormReady(ready);list.innerHTML=serverMissing(error)?'<div class="v2433-server-note"><strong>Relations privées en préparation</strong><br>Le serveur doit encore être synchronisé pour cette section.</div>':'<div class="v24-empty">Impossible de charger vos relations privées.</div>';return}
    setFormReady(true);const rows=Array.isArray(data)?data:[];
    list.innerHTML=rows.length?rows.map(x=>`<article class="v24-panel"><strong>${escapeHtml(x.relationship_type)}</strong><p>${escapeHtml(x.relative_name)}</p>${x.since_date?`<small>Depuis ${escapeHtml(x.since_date)}</small>`:''}<div class="hero-actions"><button class="btn btn-secondary btn-small" type="button" data-delete-relation="${x.id}">Retirer</button></div></article>`).join(''):'<div class="v24-empty">Aucune relation enregistrée.</div>';
    list.querySelectorAll('[data-delete-relation]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('Retirer cette relation de votre profil privé?'))return;const {error}=await s.from('family_relationships').delete().eq('id',b.dataset.deleteRelation).eq('owner_user_id',user.id);if(error){setStatus(status,'Impossible de retirer cette relation.','error');return}await render()}));
  }
  form.addEventListener('submit',async e=>{e.preventDefault();if(!ready){setStatus(status,'Enregistrement temporairement indisponible.','info');return}const d=new FormData(form),relativeName=String(d.get('relative_name')||'').trim(),relationshipType=String(d.get('relationship_type')||'').trim();if(!relationshipType||!relativeName){setStatus(status,'Choisissez le type de relation et indiquez un nom ou un pseudo.','error');return}const payload={owner_user_id:user.id,relationship_type:relationshipType,relative_name:relativeName,since_date:d.get('since_date')||null,until_date:d.get('until_date')||null,private_note:String(d.get('private_note')||'').trim()||null,status:'private_record'};const {error}=await s.from('family_relationships').insert(payload);if(error){setStatus(status,error.message||'Impossible d’ajouter cette relation.','error');return}form.reset();setStatus(status,'Relation ajoutée dans votre espace privé.','success');await render()});
  await render();
}
await refreshAgeBand();
await renderGuardian();
