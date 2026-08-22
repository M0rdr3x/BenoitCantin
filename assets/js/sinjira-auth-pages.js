import {getSupabase,getCurrentUser,isSinjiraBackendConfigured,SINJIRA_CONFIG,setStatus} from './sinjira-supabase.js';

const page=document.body?.dataset?.accountPage||'';
const status=document.querySelector('[data-account-status]');
const backend=document.querySelector('[data-backend-state]');
const DEVICE_KEY_STORAGE='sinjira.security.device_key.v1';
const PENDING_CHALLENGE_STORAGE='sinjira.security.pending_challenge.v1';
const PENDING_DESTINATION_STORAGE='sinjira.security.pending_destination.v1';

function destination(fallback='/compte/index.html'){
  return window.SINJIRA_AUTH_ROUTE?.next?.(fallback)||fallback;
}
function ready(){
  const ok=isSinjiraBackendConfigured();
  if(backend)backend.textContent=ok?'Service de comptes sécurisé actif.':'Service de comptes temporairement indisponible.';
  return ok;
}
function setBusy(form,busy){
  form?.setAttribute('aria-busy',busy?'true':'false');
  const submit=form?.querySelector('[type="submit"]');
  if(submit)submit.disabled=Boolean(busy);
}
function reportInvalid(form){
  if(form.checkValidity())return false;
  form.reportValidity();
  return true;
}
function randomDeviceKey(){
  if(globalThis.crypto?.randomUUID)return globalThis.crypto.randomUUID();
  const bytes=new Uint8Array(24);globalThis.crypto?.getRandomValues?.(bytes);
  return `sinjira-${Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')}-${Date.now().toString(36)}`;
}
function securityDeviceKey(){
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
function securityDeviceMetadata(){
  const ua=navigator.userAgent||'';
  const platform=String(navigator.userAgentData?.platform||navigator.platform||'').slice(0,120);
  let device_type='browser';
  if(/iPad|Tablet/i.test(ua))device_type='tablet';
  else if(/iPhone|iPod/i.test(ua))device_type='ios';
  else if(/Android/i.test(ua))device_type='android';
  const browser=/Firefox/i.test(ua)?'Firefox':/Edg\//i.test(ua)?'Edge':/Chrome|CriOS/i.test(ua)?'Chrome':/Safari/i.test(ua)?'Safari':'Navigateur';
  return {device_key:securityDeviceKey(),display_name:`${browser}${platform?` — ${platform}`:''}`.slice(0,120),device_type,platform};
}
async function evaluateLoginSecurity(){
  const meta=securityDeviceMetadata();
  const {data,error}=await getSupabase().functions.invoke('security-context',{body:{...meta,action:'login'}});
  if(error||!data?.ok||!data?.security)throw new Error(data?.error||error?.message||'SECURITY_CONTEXT_UNAVAILABLE');
  return {meta,security:data.security};
}
function storePendingChallenge(challengeId,next){
  try{
    sessionStorage.setItem(PENDING_CHALLENGE_STORAGE,String(challengeId));
    sessionStorage.setItem(PENDING_DESTINATION_STORAGE,String(next));
  }catch(error){console.warn('[SINJIRA security challenge storage]',error)}
}
function clearPendingChallenge(){
  try{
    sessionStorage.removeItem(PENDING_CHALLENGE_STORAGE);
    sessionStorage.removeItem(PENDING_DESTINATION_STORAGE);
  }catch{}
}

async function login(){
  const form=document.querySelector('[data-login-form]');if(!form)return;
  const existing=await getCurrentUser();
  if(existing){location.replace(destination());return}
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(reportInvalid(form))return;
    if(!ready())return setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');
    const d=new FormData(form);
    const next=destination();
    setBusy(form,true);
    clearPendingChallenge();
    try{
      const {error}=await getSupabase().auth.signInWithPassword({email:String(d.get('email')||'').trim(),password:String(d.get('password')||'')});
      if(error)return setStatus(status,'Connexion impossible. Vérifiez vos informations et la confirmation du courriel.','error');

      let evaluated=null;
      try{
        evaluated=await evaluateLoginSecurity();
      }catch(securityError){
        console.warn('[SINJIRA login shield unavailable]',securityError);
        // Le moteur contextuel est une couche supplémentaire. Une panne de cette
        // couche ne doit pas verrouiller tout le compte; les zones extrêmement
        // sensibles conservent leur propre contrôle MFA côté serveur.
        location.replace(next);
        return;
      }

      const outcome=String(evaluated.security?.outcome||'allow');
      if(outcome==='block'){
        await getSupabase().auth.signOut({scope:'local'}).catch(()=>{});
        setStatus(status,'Connexion refusée : cet appareil a été révoqué dans Ma sécurité. Utilisez un appareil fiable pour vérifier votre compte.','error');
        return;
      }

      if(outcome==='challenge'){
        const challengeId=String(evaluated.security?.challenge_id||'');
        if(!challengeId){
          await getSupabase().auth.signOut({scope:'local'}).catch(()=>{});
          setStatus(status,'Connexion inhabituelle détectée, mais la confirmation de sécurité n’a pas pu être créée. Réessayez.','error');
          return;
        }

        const {data:aal,error:aalError}=await getSupabase().auth.mfa.getAuthenticatorAssuranceLevel();
        if(!aalError&&aal?.nextLevel==='aal2'){
          storePendingChallenge(challengeId,next);
          setStatus(status,'Connexion inhabituelle détectée. Une vérification renforcée est requise avant de continuer.','info');
          location.replace(`/compte/mfa.html?security=1&next=${encodeURIComponent(next)}`);
          return;
        }

        await getSupabase().auth.signOut({scope:'local'}).catch(()=>{});
        setStatus(status,'Connexion inhabituelle détectée. Autorisez cette tentative depuis un autre appareil déjà marqué comme fiable dans Ma sécurité, puis reconnectez-vous.','error');
        return;
      }

      location.replace(next);
    }catch(err){
      console.warn('[SINJIRA auth login]',err);
      setStatus(status,'Connexion impossible pour le moment. Réessayez dans quelques instants.','error');
    }finally{setBusy(form,false)}
  });
}

async function forgot(){
  const form=document.querySelector('[data-forgot-form]');if(!form)return;
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(reportInvalid(form))return;
    if(!ready())return setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');
    const email=String(new FormData(form).get('email')||'').trim();
    setBusy(form,true);
    try{
      const {error}=await getSupabase().auth.resetPasswordForEmail(email,{redirectTo:`${SINJIRA_CONFIG.siteUrl}/compte/reinitialiser-mot-de-passe.html`});
      if(error){
        console.warn('[SINJIRA auth recovery]',error);
        return setStatus(status,'La demande de récupération n’a pas pu être traitée pour le moment. Réessayez plus tard.','error');
      }
      setStatus(status,'Si un compte correspond à cette adresse, un lien de récupération sera envoyé.','success');
      form.reset();
    }catch(err){
      console.warn('[SINJIRA auth recovery]',err);
      setStatus(status,'La demande de récupération n’a pas pu être traitée pour le moment. Réessayez plus tard.','error');
    }finally{setBusy(form,false)}
  });
}

async function reset(){
  const form=document.querySelector('[data-reset-form]');if(!form)return;
  if(!ready())return setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');
  const {data:{user},error:userError}=await getSupabase().auth.getUser();
  if(userError||!user){
    form.querySelectorAll('input,button').forEach(el=>el.disabled=true);
    setStatus(status,'Ce lien de récupération est invalide ou expiré. Demandez un nouveau lien.','error');
    return;
  }
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(reportInvalid(form))return;
    const d=new FormData(form),password=String(d.get('password')||''),confirm=String(d.get('password_confirm')||'');
    if(password.length<12||password!==confirm)return setStatus(status,'Les mots de passe doivent correspondre et contenir au moins 12 caractères.','error');
    setBusy(form,true);
    try{
      const {error}=await getSupabase().auth.updateUser({password});
      if(error)return setStatus(status,'Impossible de mettre à jour le mot de passe. Demandez un nouveau lien de récupération.','error');
      await getSupabase().auth.signOut({scope:'global'}).catch(()=>getSupabase().auth.signOut());
      setStatus(status,'Mot de passe mis à jour. Toutes les sessions ont été fermées; reconnectez-vous avec le nouveau mot de passe.','success');
      setTimeout(()=>location.replace('/compte/connexion.html?reset=1'),900);
    }catch(err){
      console.warn('[SINJIRA auth reset]',err);
      setStatus(status,'Impossible de mettre à jour le mot de passe pour le moment. Demandez un nouveau lien si le problème persiste.','error');
    }finally{setBusy(form,false)}
  });
}

ready();
try{
  if(page==='login')await login();
  else if(page==='forgot')await forgot();
  else if(page==='reset')await reset();
}catch(err){console.warn('[SINJIRA auth init]',err);setStatus(status,'Le service d’authentification n’a pas pu terminer cette opération.','error')}
