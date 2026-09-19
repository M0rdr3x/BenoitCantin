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
const juniorCommunityChildren=document.querySelector('[data-junior-community-children]');
const redeemInput=document.querySelector('[data-redeem-guardian-code]');
const redeemButton=document.querySelector('[data-redeem-guardian-code-button]');
const user=await requireUser();
const s=getSupabase();
const CODE_RE=/^YOUTH-[A-Z0-9]{10}$/;
let ageBand='unverified';

function serverMissing(error){const code=String(error?.code||''),text=String(error?.message||'');return code==='PGRST205'||code==='PGRST202'||/family_relationships|guardian_signup_invites|guardian_links|relation .* does not exist|schema cache|Could not find/i.test(text)}
function normalizeCode(v=''){return String(v).trim().toUpperCase().replace(/\s+/g,'')}
function configureGuardianTools(){
  const pending=['child_pending','youth_pending'].includes(ageBand);
  if(guardianAdultTools)guardianAdultTools.hidden=ageBand!=='adult';
  if(guardianYouthTools)guardianYouthTools.hidden=!pending;
  if(guardianNeutralTools)guardianNeutralTools.hidden=ageBand==='adult'||pending;
}
async function refreshAgeBand(){
  const {data:capabilities,error}=await s.rpc('sinjira_my_account_capabilities');
  if(!error&&capabilities&&typeof capabilities.age_band==='string')ageBand=capabilities.age_band;
  configureGuardianTools();
}

async function renderJuniorCommunityChildren(){
  if(!juniorCommunityChildren||ageBand!=='adult')return;
  const {data,error}=await s.rpc('guardian_junior_community_children');
  if(error){
    juniorCommunityChildren.innerHTML='<div class="v24-empty">Le contrôle Communauté Junior sera disponible lorsque le module serveur sera synchronisé.</div>';
    return;
  }
  const rows=Array.isArray(data)?data:[];
  juniorCommunityChildren.innerHTML=rows.length?rows.map(row=>{
    const enabled=row.enabled===true;
    return `<article class="v24-panel"><strong>${escapeHtml(row.label||'Compte enfant')} · ${escapeHtml(row.junior_alias||'Pseudonyme Junior')}</strong><p>${enabled?'Communauté Junior activée':'Communauté Junior désactivée'}</p><small>11–12 ans · aucun message privé · contenu non visible automatiquement au parent.</small><div class="hero-actions"><button class="btn ${enabled?'btn-secondary':'btn-primary'} btn-small" type="button" data-junior-community-toggle="${escapeHtml(row.minor_user_id)}" data-junior-enabled="${enabled?'true':'false'}">${enabled?'Désactiver':'Activer'} la Communauté Junior</button><button class="btn btn-secondary btn-small" type="button" data-junior-community-summary="${escapeHtml(row.minor_user_id)}">Voir le résumé de sécurité</button></div><div class="v24-feature-note" data-junior-summary-for="${escapeHtml(row.minor_user_id)}" hidden></div></article>`;
  }).join(''):'<div class="v24-empty">Aucun compte enfant 11–12 ans lié et vérifié.</div>';

  juniorCommunityChildren.querySelectorAll('[data-junior-community-toggle]').forEach(button=>button.addEventListener('click',async()=>{
    const childId=button.dataset.juniorCommunityToggle;
    const next=button.dataset.juniorEnabled!=='true';
    if(next){
      button.disabled=true;
      const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
      if(aalError){
        button.disabled=false;
        setStatus(guardianStatus,'Impossible de vérifier le niveau de sécurité. La Communauté Junior reste désactivée.','error');
        return;
      }
      if(aal?.currentLevel!=='aal2'){
        button.disabled=false;
        if(aal?.nextLevel==='aal2'){
          location.assign(`/compte/mfa.html?next=${encodeURIComponent('/compte/relations.html')}`);
          return;
        }
        setStatus(guardianStatus,'Activer la Communauté Junior exige un second facteur. Configurez-le dans Sécurité puis revenez ici.','error');
        return;
      }
      if(!confirm('Activer la Communauté Junior pour ce compte enfant? L’enfant devra aussi accepter les règles Junior.')){button.disabled=false;return}
    }else{
      if(!confirm('Désactiver la Communauté Junior? Le compte enfant perdra immédiatement l’accès au fil Junior.'))return;
      button.disabled=true;
    }
    const {data:result,error:toggleError}=await s.rpc('guardian_set_junior_community',{p_child_user_id:childId,p_enabled:next});
    if(toggleError||!result?.ok){
      button.disabled=false;
      const raw=String(toggleError?.message||'');
      if(next&&/MFA_AAL2_REQUIRED/i.test(raw)){
        setStatus(guardianStatus,'La session doit être vérifiée au niveau AAL2 avant d’activer la Communauté Junior.','error');
      }else{
        setStatus(guardianStatus,'Impossible de modifier l’accès à la Communauté Junior pour le moment.','error');
      }
      return;
    }
    setStatus(guardianStatus,next?'Communauté Junior activée. L’enfant doit maintenant accepter les règles Junior.':'Communauté Junior désactivée.','success');
    await renderJuniorCommunityChildren();
  }));

  juniorCommunityChildren.querySelectorAll('[data-junior-community-summary]').forEach(button=>button.addEventListener('click',async()=>{
    const childId=button.dataset.juniorCommunitySummary;
    const target=juniorCommunityChildren.querySelector(`[data-junior-summary-for="${CSS.escape(childId)}"]`);
    button.disabled=true;
    const {data:summary,error:summaryError}=await s.rpc('junior_guardian_summary',{p_child_user_id:childId});
    button.disabled=false;
    if(summaryError||!summary){
      if(target){target.hidden=false;target.textContent='Résumé temporairement indisponible.';}
      return;
    }
    if(target){
      const last=summary.last_activity_at?formatDate(summary.last_activity_at):'aucune activité';
      target.hidden=false;
      target.textContent=`Résumé seulement : ${Number(summary.posts||0)} publication(s), ${Number(summary.comments||0)} commentaire(s), dernière activité : ${last}. Le contenu reste privé à l’enfant et à la Communauté Junior.`;
    }
  }));
}

async function renderGuardian(){
  if(!guardianLinks)return;
  let codesResult={data:[],error:null};
  if(ageBand==='adult'&&guardianCodes){
    const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
    if(aalError){
      guardianCodes.innerHTML='<div class="v24-empty">Impossible de vérifier le niveau de sécurité. Les codes parentaux restent masqués.</div>';
    }else if(aal?.currentLevel!=='aal2'){
      const action=aal?.nextLevel==='aal2'
        ? `<a class="btn btn-secondary btn-small" href="/compte/mfa.html?next=${encodeURIComponent('/compte/relations.html')}">Vérifier avec mon second facteur</a>`
        : '<a class="btn btn-secondary btn-small" href="securite.html#mfa-active-title">Configurer le second facteur</a>';
      guardianCodes.innerHTML=`<div class="v24-empty"><strong>Codes parentaux masqués.</strong><br>Une session AAL2 est requise pour relire un code parental.<div class="hero-actions">${action}</div></div>`;
    }else{
      codesResult=await s.from('guardian_signup_invites').select('id,invite_code,consented_at,expires_at,used_at,minor_user_id,created_at').eq('guardian_user_id',user.id).order('created_at',{ascending:false}).limit(10);
      if(codesResult.error){guardianCodes.innerHTML=serverMissing(codesResult.error)?'<div class="v2433-server-note">Le module d’autorisation parentale doit être synchronisé côté serveur.</div>':'<div class="v24-empty">Impossible de charger les codes parentaux.</div>'}
      else{
        const rows=codesResult.data||[];
        guardianCodes.innerHTML=rows.length?rows.map(x=>{const used=Boolean(x.used_at),expired=!used&&new Date(x.expires_at).getTime()<Date.now();const state=used?'Utilisé':expired?'Expiré':'Valide';return `<article class="v24-panel"><strong>${escapeHtml(x.invite_code)}</strong><p>${state} · expire ${escapeHtml(formatDate(x.expires_at))}</p>${used?`<small>Utilisé ${escapeHtml(formatDate(x.used_at))}</small>`:''}</article>`}).join(''):'<div class="v24-empty">Aucun code parental créé.</div>';
      }
    }
  }

  const linksResult=await s.from('guardian_links')
    .select('id,minor_user_id,guardian_user_id,status,guardian_role,can_view_contact_metadata,consented_at,revoked_at,created_at')
    .or(`guardian_user_id.eq.${user.id},minor_user_id.eq.${user.id}`)
    .order('created_at',{ascending:false}).limit(20);
  if(linksResult.error){guardianLinks.innerHTML='<div class="v24-empty">Impossible de charger les liens de supervision.</div>';return}
  const rows=linksResult.data||[];
  guardianLinks.innerHTML=rows.length?rows.map(x=>{
    const asGuardian=x.guardian_user_id===user.id;
    const asMinor=x.minor_user_id===user.id;
    const mine=asGuardian?'Tuteur / parent':'Compte enfant / jeunesse';
    const active=x.status==='verified'&&!x.revoked_at;
    const contactControl=active&&asMinor
      ? `<button class="btn btn-secondary btn-small" type="button" data-contact-metadata-toggle="${escapeHtml(x.id)}" data-contact-metadata-allowed="${x.can_view_contact_metadata?'true':'false'}">${x.can_view_contact_metadata?'Retirer':'Autoriser'} les métadonnées de contacts</button>`
      : '';
    const revokeControl=active
      ? `<button class="btn btn-secondary btn-small" type="button" data-revoke-guardian-link="${escapeHtml(x.id)}" data-revoke-as-guardian="${asGuardian?'true':'false'}">Révoquer ce lien</button>`
      : '';
    const actions=contactControl||revokeControl?`<div class="hero-actions">${contactControl}${revokeControl}</div>`:'';
    return `<article class="v24-panel"><strong>${escapeHtml(mine)} · ${escapeHtml(active?'verified':x.status||'—')}</strong><p>Rôle : ${escapeHtml(x.guardian_role||'parent/tuteur')}</p><small>${x.can_view_contact_metadata?'Métadonnées de contact autorisées par le compte jeunesse':'Métadonnées de contact non autorisées'} · aucun contenu privé de message</small>${actions}</article>`;
  }).join(''):'<div class="v24-empty">Aucun lien de supervision.</div>';
  await renderJuniorCommunityChildren();
  guardianLinks.querySelectorAll('[data-contact-metadata-toggle]').forEach(button=>button.addEventListener('click',async()=>{
    const allowed=button.dataset.contactMetadataAllowed==='true';
    const next=!allowed;
    const prompt=next
      ? 'Autoriser ce tuteur à voir uniquement les métadonnées de vos contacts jeunesse (pseudo, réseau et dernière date de contact)? Le contenu des messages reste privé.'
      : 'Retirer immédiatement au tuteur l’accès aux métadonnées de vos contacts jeunesse?';
    if(!confirm(prompt))return;
    button.disabled=true;
    const {data,error}=await s.rpc('set_my_guardian_contact_metadata',{p_link_id:button.dataset.contactMetadataToggle,p_allowed:next});
    button.disabled=false;
    if(error||!data?.ok){
      setStatus(guardianStatus,'Impossible de modifier cette permission pour le moment.','error');
      return;
    }
    setStatus(guardianStatus,next?'Métadonnées de contacts autorisées. Le contenu de vos messages reste privé.':'Permission retirée. Le tuteur ne peut plus consulter vos métadonnées de contacts.','success');
    await renderGuardian();
  }));
  guardianLinks.querySelectorAll('[data-revoke-guardian-link]').forEach(button=>button.addEventListener('click',async()=>{
    const asGuardian=button.dataset.revokeAsGuardian==='true';
    if(asGuardian){
      button.disabled=true;
      const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
      if(aalError){
        button.disabled=false;
        setStatus(guardianStatus,'Impossible de vérifier le niveau de sécurité. Le lien reste actif.','error');
        return;
      }
      if(aal?.currentLevel!=='aal2'){
        button.disabled=false;
        if(aal?.nextLevel==='aal2'){
          location.assign(`/compte/mfa.html?next=${encodeURIComponent('/compte/relations.html')}`);
          return;
        }
        setStatus(guardianStatus,'Révoquer un lien comme tuteur exige un second facteur. Configurez-le dans Sécurité puis revenez ici.','error');
        return;
      }
    }
    if(!confirm(asGuardian?'Révoquer ce lien de supervision? Une vérification AAL2 protège cette décision.':'Quitter ce lien de supervision? Vous pouvez retirer immédiatement cette supervision de votre compte.')){button.disabled=false;return}
    button.disabled=true;
    const {data,error}=await s.rpc('revoke_guardian_link',{p_link_id:button.dataset.revokeGuardianLink});
    if(error||!data?.ok){
      button.disabled=false;
      if(asGuardian&&/MFA_AAL2_REQUIRED/i.test(String(error?.message||''))){
        setStatus(guardianStatus,'La session tuteur doit être vérifiée au niveau AAL2 avant de révoquer ce lien.','error');
      }else{
        setStatus(guardianStatus,'Impossible de révoquer ce lien pour le moment.','error');
      }
      return;
    }
    await refreshAgeBand();setStatus(guardianStatus,asGuardian?'Lien de supervision révoqué par le tuteur.':'Vous avez quitté ce lien de supervision.','success');await renderGuardian();
  }));
}

guardianButton?.addEventListener('click',async()=>{
  guardianButton.disabled=true;setStatus(guardianStatus,'Vérification renforcée avant création du code parental…','info');
  const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if(aalError){
    guardianButton.disabled=false;
    setStatus(guardianStatus,'Impossible de vérifier le niveau de sécurité de votre session. Aucun code parental n’a été créé.','error');
    return;
  }
  if(aal?.currentLevel!=='aal2'){
    guardianButton.disabled=false;
    if(aal?.nextLevel==='aal2'){
      location.assign(`/compte/mfa.html?next=${encodeURIComponent('/compte/relations.html')}`);
      return;
    }
    setStatus(guardianStatus,'La création d’un code parental exige un second facteur. Activez d’abord une application d’authentification dans Sécurité, puis revenez ici.','error');
    return;
  }
  const {data,error}=await s.rpc('create_guardian_signup_invite');
  guardianButton.disabled=false;
  if(error){
    const raw=String(error.message||'');
    if(/MFA_AAL2_REQUIRED|MFA_REQUIRED/i.test(raw)){
      setStatus(guardianStatus,'Votre session doit être vérifiée au niveau AAL2 avant de créer un code parental. Utilisez la vérification renforcée puis réessayez.','error');
    }else{
      setStatus(guardianStatus,'Impossible de générer le code parental. Vérifiez que votre compte est adulte et que les exigences de sécurité sont satisfaites.','error');
    }
    return;
  }
  setStatus(guardianStatus,`Code créé : ${String(data||'')}. Copiez-le dans l’inscription de l’enfant. Il est à usage unique et expire automatiquement.`,'success');
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
  await refreshAgeBand();setStatus(guardianStatus,'Lien parental vérifié. Les protections enfant/jeunesse utilisent maintenant cette supervision.','success');await renderGuardian();
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
