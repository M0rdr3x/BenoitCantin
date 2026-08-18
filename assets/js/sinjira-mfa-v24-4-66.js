import {getSupabase,safeInternalDestination,setStatus} from './sinjira-supabase.js';

const s=getSupabase();
const form=document.querySelector('[data-mfa-challenge-form]');
const factorSelect=document.querySelector('[data-mfa-factor]');
const status=document.querySelector('[data-mfa-status]');
const signOutButton=document.querySelector('[data-mfa-signout]');
const next=safeInternalDestination(new URLSearchParams(location.search).get('next'),'/compte/index.html');

function verifiedTotp(data){
  return (data?.totp||[]).filter(factor=>factor?.status==='verified');
}

async function init(){
  const {data:{user},error:userError}=await s.auth.getUser();
  if(userError||!user){
    location.replace(`/compte/connexion.html?next=${encodeURIComponent(next)}`);
    return;
  }

  const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if(aalError)throw aalError;
  if(aal?.currentLevel==='aal2'){
    location.replace(next);
    return;
  }

  const {data:factors,error:factorsError}=await s.auth.mfa.listFactors();
  if(factorsError)throw factorsError;
  const totp=verifiedTotp(factors);
  if(!totp.length){
    form.hidden=true;
    setStatus(status,'Aucun facteur TOTP vérifié n’est disponible pour terminer cette connexion. Déconnectez-vous puis reconnectez-vous, ou gérez le MFA depuis le Centre de sécurité.','error');
    return;
  }

  factorSelect.innerHTML=totp.map((factor,index)=>`<option value="${factor.id}">${factor.friendly_name||`Application d’authentification ${index+1}`}</option>`).join('');
  form.hidden=false;

  form.addEventListener('submit',async event=>{
    event.preventDefault();
    const code=String(new FormData(form).get('code')||'').replace(/\s+/g,'');
    const factorId=factorSelect.value;
    if(!/^\d{6}$/.test(code)){
      setStatus(status,'Entrez le code à 6 chiffres affiché par votre application d’authentification.','error');
      return;
    }
    const submit=form.querySelector('[type="submit"]');
    if(submit)submit.disabled=true;
    const {error}=await s.auth.mfa.challengeAndVerify({factorId,code});
    if(error){
      if(submit)submit.disabled=false;
      setStatus(status,'Code invalide ou expiré. Utilisez le code actuel de votre application d’authentification.','error');
      return;
    }
    location.replace(next);
  });
}

signOutButton?.addEventListener('click',async()=>{
  await s.auth.signOut();
  location.replace('/compte/connexion.html');
});

init().catch(error=>{
  console.warn('[SINJIRA MFA challenge]',error);
  if(form)form.hidden=true;
  setStatus(status,'Le second facteur ne peut pas être vérifié pour le moment. Réessayez après une nouvelle connexion.','error');
});
