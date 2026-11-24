import {getSupabase,isSinjiraBackendConfigured,setStatus,assertKnownAssuranceLevels} from './sinjira-supabase.js';

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
  const source=globalThis.crypto;
  if(typeof source?.randomUUID==='function'){
    try{return source.randomUUID()}catch{/* Utiliser uniquement un autre CSPRNG. */}
  }
  if(typeof source?.getRandomValues!=='function')throw new Error('SECURITY_CRYPTO_UNAVAILABLE');
  const bytes=new Uint8Array(24);
  source.getRandomValues(bytes);
  return 'sinjira-'+Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
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
  assertKnownAssuranceLevels(data);
  if(data?.nextLevel==='aal2'&&data?.currentLevel!=='aal2'){
    setBusy(true);
    setStatus(status,'Votre compte possède un second facteur. Vérifiez-le avant de choisir un nouveau mot de passe.','info');
    location.replace(`/compte/mfa.html?recovery=1&next=${encodeURIComponent(RESET_PATH)}`);
    return false;
  }
  return true;
}
async function revokeRecoverySessions(){
  // Supabase peut retourner une erreur sans rejeter la promesse.
  try{
    const result=await s.auth.signOut({scope:'global'});
    if(result?.error===null)return 'global';
  }catch{}
  // Le repli local ne prouve jamais que les autres sessions ont été révoquées.
  try{
    const result=await s.auth.signOut({scope:'local'});
    if(result?.error===null)return 'local';
  }catch{}
  return 'unconfirmed';
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

  let submitting=false, passwordUpdated=false;
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    if(submitting||passwordUpdated)return;
    if(!form.checkValidity()){form.reportValidity();return}
    const d=new FormData(form);
    const password=String(d.get('password')||'');
    const confirm=String(d.get('password_confirm')||'');
    if(password.length<12||password!==confirm){
      setStatus(status,'Les mots de passe doivent correspondre et contenir au moins 12 caractères.','error');
      return;
    }
    submitting=true;
    setBusy(true);
    try{
      if(!await requireRecoveryAal2WhenAvailable())return;
      const {error:updateError}=await s.auth.updateUser({password});
      if(updateError){
        setStatus(status,'Impossible de mettre à jour le mot de passe. Demandez un nouveau lien de récupération.','error');
        return;
      }

      passwordUpdated=true;
      let cleanupOk=false;
      try{
        const result=await s.rpc('security_after_password_recovery',{p_device_key:deviceKey()});
        cleanupOk=result?.error===null;
      }catch{}
      if(!cleanupOk)console.warn('[SINJIRA recovery security cleanup] non confirmé');

      const revoked=await revokeRecoverySessions();
      if(revoked!=='global'){
        setStatus(status,revoked==='local'
          ? 'Mot de passe mis à jour. Cet appareil est déconnecté, mais la révocation des autres sessions n’a pas été confirmée. Reconnectez-vous et révoquez-les dans Ma sécurité.'
          : 'Mot de passe mis à jour. La fermeture des sessions n’a pas été confirmée. N’utilisez pas cette session; ouvrez Ma sécurité pour révoquer les sessions dès que le service est disponible.',
          'error');
        return;
      }
      setStatus(status,cleanupOk
        ? 'Mot de passe mis à jour. La révocation globale a été acceptée; les jetons d’accès existants peuvent rester valides jusqu’à expiration. Les appareils devront être vérifiés de nouveau.'
        : 'Mot de passe mis à jour. La révocation globale a été acceptée, mais la vérification des appareils n’est pas confirmée. Après reconnexion, vérifiez Ma sécurité.',
        cleanupOk?'success':'info');
      setTimeout(()=>location.replace('/compte/connexion.html?reset=1'),1200);
    }catch(error){
      console.warn('[SINJIRA secure recovery]',error);
      setStatus(status,'La récupération n’a pas pu être terminée. Réessayez avec un nouveau lien si nécessaire.','error');
    }finally{submitting=false;setBusy(passwordUpdated)}
  });
}

boot().catch(error=>{
  console.warn('[SINJIRA secure recovery init]',error);
  setBusy(true);
  setStatus(status,'La récupération sécurisée ne peut pas être vérifiée pour le moment. Réessayez plus tard.','error');
});
