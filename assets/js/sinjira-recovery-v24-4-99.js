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
function validDeviceKey(value){
  // Conserver uniquement les identifiants forts préexistants (UUID ou 192 bits).
  // Exclure les identifiants historiques composés d'octets nuls + horodatage.
  if(typeof value!=='string'||value.length>128)return false;
  if(/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(value))
    return !/^0{8}-(?:0{4}-){3}0{12}$/i.test(value);
  const match=/^sinjira-([0-9a-f]{48})(?:-[0-9a-z]+)?$/i.exec(value);
  return Boolean(match&&!/^0{48}$/.test(match[1]));
}
function deviceKey(){
  // La récupération ne doit JAMAIS inventer un appareil : le RPC accepte
  // p_device_key=null et révoque alors tous les appareils, sans exception.
  for(const storageName of ['localStorage','sessionStorage']){
    try{
      const value=globalThis[storageName]?.getItem(DEVICE_KEY_STORAGE);
      if(validDeviceKey(value))return value;
    }catch{/* Stockage inaccessible : appliquer la révocation globale. */}
  }
  return null;
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

      // Un incident de révocation n'interrompt pas la déconnexion : on ne
      // prétend jamais avoir révoqué les appareils sans preuve RPC ok=true.
      let cleanupOk=false;
      try{
        const {data,error:cleanupError}=await s.rpc('security_after_password_recovery',{p_device_key:deviceKey()});
        cleanupOk=!cleanupError&&data?.ok===true;
      }catch{/* Échec RPC : poursuivre la déconnexion globale. */}

      let globalSignoutOk=false;
      try{
        const result=await s.auth.signOut({scope:'global'});
        globalSignoutOk=!result?.error;
      }catch{/* L'API peut échouer sans exposer la cause à la console. */}
      if(!globalSignoutOk){
        // Retirer au moins la session locale, mais ne pas la présenter comme
        // une révocation globale si le fournisseur d'authentification échoue.
        try{await s.auth.signOut({scope:'local'});}catch{/* Signalement ci-dessous. */}
        setStatus(status,'Mot de passe modifié, mais la déconnexion globale n’a pas été confirmée. Reconnectez-vous et vérifiez immédiatement les sessions et appareils dans Ma sécurité.','error');
        return;
      }
      setStatus(status,cleanupOk
        ? 'Mot de passe mis à jour. Toutes les sessions ont été fermées et les appareils devront être vérifiés de nouveau.'
        : 'Mot de passe mis à jour et déconnexion globale effectuée. La révocation des appareils n’a pas été confirmée : vérifiez immédiatement Ma sécurité après reconnexion.',
        cleanupOk?'success':'info');
      setTimeout(()=>location.replace('/compte/connexion.html?reset=1'),1200);
    }catch{
      setStatus(status,'La récupération n’a pas pu être terminée. Réessayez avec un nouveau lien si nécessaire.','error');
    }finally{setBusy(false)}
  });
}

boot().catch(()=>{
  // Les exceptions Auth peuvent contenir des détails de session privés.
  setBusy(true);
  setStatus(status,'La récupération sécurisée ne peut pas être vérifiée pour le moment. Réessayez plus tard.','error');
});
