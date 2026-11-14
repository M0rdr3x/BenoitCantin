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
  return (Array.isArray(data?.totp)?data.totp:[]).filter(factor=>factor?.status==='verified');
}

// Les clés d'appareil fournies par le navigateur ne sont jamais une preuve
// d'autorisation : la RPC doit aussi vérifier l'appartenance et la session.
function strongDeviceKey(value){
  if(typeof value!=='string')return false;
  if(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value))return true;
  const legacy=/^sinjira-([0-9a-f]{48})(?:-[0-9a-z]{1,15})?$/i.exec(value);
  return Boolean(legacy&&!/^0{48}$/.test(legacy[1]));
}
function validChallengeId(value){
  return typeof value==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

let navigationBlocked=false;
let verifying=false;
async function closeLocalSession(){
  try{
    const result=await s.auth.signOut({scope:'local'});
    return Boolean(result&&result.error===null);
  }catch{return false}
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
    if(!validChallengeId(challengeId)||!strongDeviceKey(deviceKey))return null;
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

  if(navigationBlocked)throw new Error('SECURITY_FLOW_BLOCKED');
  const {error}=await s.rpc('security_resolve_connection_challenge_mfa',{
    p_challenge_id:pending.challengeId,
    p_device_key:pending.deviceKey
  });
  if(error)throw error;
  if(navigationBlocked)throw new Error('SECURITY_FLOW_BLOCKED');
  clearPendingSecurityChallenge();
  return {ok:true,next:pending.next};
}

async function failSecurityChallenge(){
  navigationBlocked=true;
  console.warn('[SINJIRA security MFA approval] vérification non confirmée.');
  clearPendingSecurityChallenge();
  if(form)form.hidden=true;
  const closed=await closeLocalSession();
  setStatus(status,closed
    ? 'Cette connexion inhabituelle n’a pas été autorisée. La déconnexion locale est confirmée; reconnectez-vous pour réessayer.'
    : 'Cette connexion inhabituelle n’a pas été autorisée. La déconnexion locale n’a pas pu être confirmée : fermez cet onglet, puis reconnectez-vous.','error');
}

async function init(){
  const {data:userResult,error:userError}=await s.auth.getUser();
  const user=userResult?.user;
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
        if(!navigationBlocked)location.replace(result.next);
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
      await failSecurityChallenge();
    }else{
      setStatus(status,'Aucun facteur TOTP vérifié n’est disponible pour terminer cette connexion. Déconnectez-vous puis reconnectez-vous, ou gérez le MFA depuis le Centre de sécurité.','error');
    }
    return;
  }

  renderFactorOptions(totp);
  form.hidden=false;

  form.addEventListener('submit',async event=>{
    event.preventDefault();
    const submit=form.querySelector('[type="submit"]');
    if(verifying||navigationBlocked||submit?.disabled)return;
    const code=String(new FormData(form).get('code')||'').replace(/\s+/g,'');
    const factorId=factorSelect?.value||'';
    if(!factorId){
      setStatus(status,'Choisissez un facteur TOTP valide.','error');
      return;
    }
    if(!/^\d{6}$/.test(code)){
      setStatus(status,'Entrez le code à 6 chiffres affiché par votre application d’authentification.','error');
      return;
    }
    verifying=true;
    if(submit)submit.disabled=true;
    try{
      const {data:verifiedSession,error}=await s.auth.mfa.challengeAndVerify({factorId,code});
      if(navigationBlocked)return;
      if(error){
        setStatus(status,'Code invalide ou expiré. Utilisez le code actuel de votre application d’authentification.','error');
        return;
      }
      // Une promesse résolue sans erreur n'est pas une preuve d'élévation MFA.
      if(!verifiedSession?.access_token){
        setStatus(status,'Le serveur n’a pas confirmé la vérification TOTP. Réessayez après vérification de votre compte.','error');
        return;
      }
      const {data:aal,error:aalError}=await s.auth.mfa.getAuthenticatorAssuranceLevel();
      if(navigationBlocked)return;
      if(aalError||aal?.currentLevel!=='aal2'){
        setStatus(status,'Le niveau de sécurité AAL2 n’a pas été confirmé. Ne poursuivez pas cette connexion.','error');
        return;
      }
      if(securityFlow){
        const result=await finishSecurityChallenge();
        if(!navigationBlocked)location.replace(result.next);
      }else if(!navigationBlocked){
        location.replace(next);
      }
    }catch{
      if(securityFlow && !navigationBlocked){
        await failSecurityChallenge();
      }else if(!navigationBlocked){
        setStatus(status,'La vérification TOTP est temporairement indisponible. Réessayez.','error');
      }
    }finally{
      verifying=false;
      if(submit)submit.disabled=false;
    }
  });
}

signOutButton?.addEventListener('click',async()=>{
  if(signOutButton.disabled)return;
  signOutButton.disabled=true;
  navigationBlocked=true;
  clearPendingSecurityChallenge();
  if(form)form.hidden=true;
  const closed=await closeLocalSession();
  if(closed){
    location.replace('/compte/connexion.html');
    return;
  }
  console.warn('[SINJIRA MFA signout] déconnexion locale non confirmée.');
  setStatus(status,'La déconnexion locale n’a pas pu être confirmée. Fermez cet onglet et réessayez.','error');
  signOutButton.disabled=false;
});

init().catch(async()=>{
  console.warn('[SINJIRA MFA challenge] initialisation indisponible.');
  if(securityFlow){
    await failSecurityChallenge();
  }else{
    navigationBlocked=true;
    if(form)form.hidden=true;
    setStatus(status,'Le second facteur ne peut pas être vérifié pour le moment. Réessayez après une nouvelle connexion.','error');
  }
});
