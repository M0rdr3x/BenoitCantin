import {getSupabase,requireUser,escapeHtml,setStatus} from './sinjira-supabase.js';

const sessionBox=document.querySelector('[data-v24-security-session]');
const mfaBox=document.querySelector('[data-v24-security-mfa]');
const factorsBox=document.querySelector('[data-mfa-factors]');
const enrollButton=document.querySelector('[data-mfa-enroll]');
const setup=document.querySelector('[data-mfa-setup]');
const qr=document.querySelector('[data-mfa-qr]');
const secret=document.querySelector('[data-mfa-secret]');
const enrollForm=document.querySelector('[data-mfa-enroll-form]');
const cancelButton=document.querySelector('[data-mfa-cancel]');
const status=document.querySelector('[data-v24-security-status]');
const MAX_TOTP_FACTORS=10;

let pendingFactorId='';

function totpFactors(data){
  return data?.totp||[];
}

async function loadFactors(s){
  const {data,error}=await s.auth.mfa.listFactors();
  if(error)throw error;
  const factors=totpFactors(data);
  const verified=factors.filter(factor=>factor.status==='verified');
  const pending=factors.filter(factor=>factor.status!=='verified');
  const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if(aalError)throw aalError;

  if(mfaBox){
    mfaBox.innerHTML=verified.length
      ? `<p><strong>${verified.length} facteur${verified.length===1?'':'s'} TOTP vérifié${verified.length===1?'':'s'}.</strong></p><p>Session actuelle : ${escapeHtml(aal?.currentLevel||'aal1')}.</p>`
      : '<p><strong>Aucun facteur TOTP vérifié.</strong></p><p>Vous pouvez activer gratuitement une application d’authentification.</p>';
  }

  if(factorsBox){
    factorsBox.innerHTML=verified.length
      ? verified.map((factor,index)=>`<article class="v24-panel"><span class="v24-badge live">TOTP vérifié</span><h3>${escapeHtml(factor.friendly_name||`Application d’authentification ${index+1}`)}</h3><p>Facteur actif sur votre Compte SINJIRA™.</p><button class="btn btn-secondary btn-small" type="button" data-mfa-remove="${escapeHtml(factor.id)}">Retirer ce facteur</button></article>`).join('')
      : '<div class="v24-empty">Aucune application d’authentification active.</div>';
  }

  factorsBox?.querySelectorAll('[data-mfa-remove]').forEach(button=>button.addEventListener('click',async()=>{
    if(!confirm('Retirer ce facteur TOTP? Après retrait du dernier facteur, le second facteur ne sera plus demandé à la connexion.'))return;
    button.disabled=true;
    const {error:removeError}=await s.auth.mfa.unenroll({factorId:button.dataset.mfaRemove});
    if(removeError){
      button.disabled=false;
      setStatus(status,'Impossible de retirer ce facteur. Vérifiez d’abord votre second facteur puis réessayez.','error');
      return;
    }
    setStatus(status,'Facteur TOTP retiré.','success');
    await loadFactors(s);
  }));

  if(enrollButton){
    enrollButton.disabled=factors.length>=MAX_TOTP_FACTORS||Boolean(pendingFactorId);
    enrollButton.textContent=verified.length?'Ajouter une application d’authentification de secours':'Activer une application d’authentification';
  }
  return {verified,pending,factors};
}

function hideSetup(){
  pendingFactorId='';
  if(setup)setup.hidden=true;
  if(qr){qr.removeAttribute('src');qr.alt='';}
  if(secret)secret.textContent='—';
  enrollForm?.reset();
}

try{
  const user=await requireUser();
  const s=getSupabase();
  const {data:{session}}=await s.auth.getSession();
  const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if(aalError)throw aalError;

  if(sessionBox)sessionBox.innerHTML=`<p><strong>${escapeHtml(user.email||'Compte')}</strong></p><p>Courriel : ${user.email_confirmed_at?'vérifié':'à confirmer'}</p><p>Session active : ${session?'oui':'non'}</p><p>Niveau d’assurance : ${escapeHtml(aal?.currentLevel||'aal1')}</p>`;

  await loadFactors(s);

  enrollButton?.addEventListener('click',async()=>{
    enrollButton.disabled=true;
    try{
      const {data:current,error:listError}=await s.auth.mfa.listFactors();
      if(listError)throw listError;
      for(const factor of totpFactors(current).filter(item=>item.status!=='verified')){
        const {error:cleanupError}=await s.auth.mfa.unenroll({factorId:factor.id});
        if(cleanupError)throw cleanupError;
      }
      const verifiedCount=totpFactors(current).filter(item=>item.status==='verified').length;
      if(verifiedCount>=MAX_TOTP_FACTORS)throw new Error('TOTP_FACTOR_LIMIT');

      const {data,error}=await s.auth.mfa.enroll({factorType:'totp',friendlyName:`SINJIRA TOTP ${verifiedCount+1}`});
      if(error)throw error;
      pendingFactorId=data.id;
      const qrCode=String(data?.totp?.qr_code||'');
      if(qr){
        if(qrCode.startsWith('data:image/')){
          qr.src=qrCode;
          qr.alt='Code QR TOTP à scanner avec votre application d’authentification';
        }else{
          qr.removeAttribute('src');
          qr.alt='';
        }
      }
      if(secret)secret.textContent=data?.totp?.secret||'—';
      if(setup)setup.hidden=false;
      setStatus(status,'Scannez le QR ou saisissez le secret, puis entrez le code à 6 chiffres pour terminer l’activation.','info');
    }catch(error){
      console.warn('[SINJIRA MFA enroll]',error);
      enrollButton.disabled=false;
      setStatus(status,error?.message==='TOTP_FACTOR_LIMIT'?'Le nombre maximal de facteurs TOTP est déjà atteint.':'Impossible de démarrer l’activation TOTP pour le moment.','error');
    }
  });

  enrollForm?.addEventListener('submit',async event=>{
    event.preventDefault();
    if(!pendingFactorId)return;
    const code=String(new FormData(enrollForm).get('code')||'').replace(/\s+/g,'');
    if(!/^\d{6}$/.test(code)){
      setStatus(status,'Entrez le code à 6 chiffres de votre application d’authentification.','error');
      return;
    }
    const submit=enrollForm.querySelector('[type="submit"]');
    if(submit)submit.disabled=true;
    const {error}=await s.auth.mfa.challengeAndVerify({factorId:pendingFactorId,code});
    if(error){
      if(submit)submit.disabled=false;
      setStatus(status,'Le code TOTP est invalide ou expiré. Utilisez le code actuellement affiché.','error');
      return;
    }
    hideSetup();
    setStatus(status,'Authentification TOTP activée. Les prochaines connexions aux pages privées demanderont ce second facteur.','success');
    await loadFactors(s);
  });

  cancelButton?.addEventListener('click',async()=>{
    const factorId=pendingFactorId;
    cancelButton.disabled=true;
    if(factorId){
      const {error}=await s.auth.mfa.unenroll({factorId});
      if(error)console.warn('[SINJIRA MFA cancel]',error);
    }
    hideSetup();
    cancelButton.disabled=false;
    await loadFactors(s).catch(()=>{});
    setStatus(status,'Activation TOTP annulée.','info');
  });
}catch(error){
  console.warn('[SINJIRA security]',error);
  setStatus(status,'Impossible de lire ou modifier l’état de sécurité pour le moment.','error');
}
