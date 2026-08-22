import {getSupabase,isSinjiraBackendConfigured,setStatus} from './sinjira-supabase.js';

const s=getSupabase();
const form=document.querySelector('[data-reset-form]');
const status=document.querySelector('[data-account-status]');
const backend=document.querySelector('[data-backend-state]');
const DEVICE_KEY_STORAGE='sinjira.security.device_key.v1';
const RESET_PATH='/compte/reinitialiser-mot-de-passe.html';

function setBusy(busy){
  form?.setAttribute('aria-busy',busy?'true':'false');
  form?.querySelectorAll('input,button').forEach(el=>{el.disabled=Boolean(busy)});
}
function randomDeviceKey(){
  if(globalThis.crypto?.randomUUID)return globalThis.crypto.randomUUID();
  const bytes=new Uint8Array(24);globalThis.crypto?.getRandomValues?.(bytes);
  return `sinjira-${Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')}-${Date.now().toString(36)}`;
}
function deviceKey(){
  try{
    let value=localStorage.getItem(DEVICE_KEY_STORAGE);
    if(!value){value=randomDeviceKey();localStorage.setItem(DEVICE_KEY_STORAGE,value)}
    return value;
  }catch{
    try{
      let value=sessionStorage.getItem(DEVICE_KEY_STORAGE);
      if(!value){value=randomDeviceKey();sessionStorage.setItem(DEVICE_KEY_STORAGE,value)}
      return value;
    }catch{return randomDeviceKey()}
  }
}
async function requireRecoveryAal2WhenAvailable(){
  const {data,error}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
  if(error)throw error;
  if(data?.nextLevel==='aal2'&&data?.currentLevel!=='aal2'){
    setBusy(true);
    setStatus(status,'Votre compte possède un second facteur. Vérifiez-le avant de choisir un nouveau mot de passe.','info');
    location.replace(`/compte/mfa.html?recovery=1&next=${encodeURIComponent(RESET_PATH)}`);
    return false;
  }
  return true;
}
async function boot(){
  if(!form)return;
  const configured=isSinjiraBackendConfigured();
  if(backend)backend.textContent=configured?'Service de comptes sécurisé actif.':'Service de comptes temporairement indisponible.';
  if(!configured){setBusy(true);setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');return}

  setBusy(true);
  const {data:{user},error:userError}=await s.auth.getUser();
  if(userError||!user){
    setStatus(status,'Ce lien de récupération est invalide ou expiré. Demandez un nouveau lien.','error');
    return;
  }
  if(!await requireRecoveryAal2WhenAvailable())return;
  setBusy(false);

  form.addEventListener('submit',async event=>{
    event.preventDefault();
    if(!form.checkValidity()){form.reportValidity();return}
    const d=new FormData(form);
    const password=String(d.get('password')||'');
    const confirm=String(d.get('password_confirm')||'');
    if(password.length<12||password!==confirm){
      setStatus(status,'Les mots de passe doivent correspondre et contenir au moins 12 caractères.','error');
      return;
    }
    setBusy(true);
    try{
      if(!await requireRecoveryAal2WhenAvailable())return;
      const {error:updateError}=await s.auth.updateUser({password});
      if(updateError){
        setStatus(status,'Impossible de mettre à jour le mot de passe. Demandez un nouveau lien de récupération.','error');
        return;
      }

      let cleanupOk=true;
      const {error:cleanupError}=await s.rpc('security_after_password_recovery',{p_device_key:deviceKey()});
      if(cleanupError){cleanupOk=false;console.warn('[SINJIRA recovery security cleanup]',cleanupError)}

      await s.auth.signOut({scope:'global'}).catch(()=>s.auth.signOut());
      setStatus(status,cleanupOk
        ? 'Mot de passe mis à jour. Toutes les sessions ont été fermées et les appareils devront être vérifiés de nouveau.'
        : 'Mot de passe mis à jour et sessions fermées. Après reconnexion, vérifiez immédiatement Ma sécurité pour confirmer vos appareils.',
        cleanupOk?'success':'info');
      setTimeout(()=>location.replace('/compte/connexion.html?reset=1'),1200);
    }catch(error){
      console.warn('[SINJIRA secure recovery]',error);
      setStatus(status,'La récupération n’a pas pu être terminée. Réessayez avec un nouveau lien si nécessaire.','error');
    }finally{setBusy(false)}
  });
}

boot().catch(error=>{
  console.warn('[SINJIRA secure recovery init]',error);
  setBusy(true);
  setStatus(status,'La récupération sécurisée ne peut pas être vérifiée pour le moment. Réessayez plus tard.','error');
});
