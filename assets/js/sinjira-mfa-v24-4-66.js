import {getSupabase,safeInternalDestination,setStatus} from './sinjira-supabase.js';

const s=getSupabase();
const form=document.querySelector('[data-mfa-challenge-form]');
const factorSelect=document.querySelector('[data-mfa-factor]');
const status=document.querySelector('[data-mfa-status]');
const signOutButton=document.querySelector('[data-mfa-signout]');
const params=new URLSearchParams(location.search);
const next=safeInternalDestination(params.get('next'),'/compte/index.html');
const securityFlow=params.get('security')==='1';
const DEVICE_KEY_STORAGE='sinjira.security.device_key.v1';
const PENDING_CHALLENGE_STORAGE='sinjira.security.pending_challenge.v1';
const PENDING_DESTINATION_STORAGE='sinjira.security.pending_destination.v1';

function verifiedTotp(data){
  return (data?.totp||[]).filter(factor=>factor?.status==='verified');
}

function renderFactorOptions(factors){
  if(!factorSelect)return;
  factorSelect.replaceChildren();
  factors.forEach((factor,index)=>{
    const option=document.createElement('option');
    option.value=String(factor.id||'');
    option.textContent=String(factor.friendly_name||`Application d’authentification ${index+1}`);
    factorSelect.append(option);
  });
}

function pendingSecurityChallenge(){
  if(!securityFlow)return null;
  try{
    const challengeId=String(sessionStorage.getItem(PENDING_CHALLENGE_STORAGE)||'');
    const deviceKey=String(localStorage.getItem(DEVICE_KEY_STORAGE)||sessionStorage.getItem(DEVICE_KEY_STORAGE)||'');
    const storedNext=safeInternalDestination(sessionStorage.getItem(PENDING_DESTINATION_STORAGE),next);
    if(!challengeId||deviceKey.length<16)return null;
    return {challengeId,deviceKey,next:storedNext};
  }catch{return null}
}

function clearPendingSecurityChallenge(){
  try{
    sessionStorage.removeItem(PENDING_CHALLENGE_STORAGE);
    sessionStorage.removeItem(PENDING_DESTINATION_STORAGE);
  }catch{}
}

async function finishSecurityChallenge(){
  const pending=pendingSecurityChallenge();
  if(!securityFlow)return {ok:true,next};
  if(!pending)throw new Error('SECURITY_CHALLENGE_STATE_MISSING');

  const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if(aalError||aal?.currentLevel!=='aal2')throw new Error('AAL2_REQUIRED');

  const {error}=await s.rpc('security_resolve_connection_challenge_mfa',{
    p_challenge_id:pending.challengeId,
    p_device_key:pending.deviceKey
  });
  if(error)throw error;
  clearPendingSecurityChallenge();
  return {ok:true,next:pending.next};
}

async function failSecurityChallenge(error){
  console.warn('[SINJIRA security MFA approval]',error);
  clearPendingSecurityChallenge();
  await s.auth.signOut({scope:'local'}).catch(()=>{});
  if(form)form.hidden=true;
  setStatus(status,'La vérification renforcée n’a pas pu confirmer cette connexion inhabituelle. La session a été fermée; reconnectez-vous pour réessayer.','error');
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
    if(securityFlow){
      try{
        const result=await finishSecurityChallenge();
        location.replace(result.next);
      }catch(error){await failSecurityChallenge(error)}
      return;
    }
    location.replace(next);
    return;
  }

  const {data:factors,error:factorsError}=await s.auth.mfa.listFactors();
  if(factorsError)throw factorsError;
  const totp=verifiedTotp(factors);
  if(!totp.length){
    form.hidden=true;
    if(securityFlow){
      clearPendingSecurityChallenge();
      await s.auth.signOut({scope:'local'}).catch(()=>{});
      setStatus(status,'Aucun facteur TOTP vérifié n’est disponible. Cette connexion inhabituelle doit être autorisée depuis un autre appareil déjà fiable, puis vous pourrez vous reconnecter.','error');
    }else{
      setStatus(status,'Aucun facteur TOTP vérifié n’est disponible pour terminer cette connexion. Déconnectez-vous puis reconnectez-vous, ou gérez le MFA depuis le Centre de sécurité.','error');
    }
    return;
  }

  renderFactorOptions(totp);
  form.hidden=false;

  form.addEventListener('submit',async event=>{
    event.preventDefault();
    const code=String(new FormData(form).get('code')||'').replace(/\s+/g,'');
    const factorId=factorSelect.value;
    if(!factorId){
      setStatus(status,'Choisissez un facteur TOTP valide.','error');
      return;
    }
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

    if(securityFlow){
      try{
        const result=await finishSecurityChallenge();
        location.replace(result.next);
      }catch(securityError){
        await failSecurityChallenge(securityError);
      }
      return;
    }
    location.replace(next);
  });
}

signOutButton?.addEventListener('click',async()=>{
  clearPendingSecurityChallenge();
  await s.auth.signOut();
  location.replace('/compte/connexion.html');
});

init().catch(error=>{
  console.warn('[SINJIRA MFA challenge]',error);
  if(form)form.hidden=true;
  setStatus(status,'Le second facteur ne peut pas être vérifié pour le moment. Réessayez après une nouvelle connexion.','error');
});
