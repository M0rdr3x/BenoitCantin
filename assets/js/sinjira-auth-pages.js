import {getSupabase,getCurrentUser,isSinjiraBackendConfigured,SINJIRA_CONFIG,setStatus} from './sinjira-supabase.js';

const page=document.body?.dataset?.accountPage||'';
const status=document.querySelector('[data-account-status]');
const backend=document.querySelector('[data-backend-state]');

function destination(fallback='/compte/index.html'){
  return window.SINJIRA_AUTH_ROUTE?.next?.(fallback)||fallback;
}
function ready(){
  const ok=isSinjiraBackendConfigured();
  if(backend)backend.textContent=ok?'Service de comptes sécurisé actif.':'Service de comptes temporairement indisponible.';
  return ok;
}

async function login(){
  const form=document.querySelector('[data-login-form]');if(!form)return;
  const existing=await getCurrentUser();
  if(existing){location.replace(destination());return}
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!ready())return setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');
    const submit=form.querySelector('[type="submit"]');if(submit)submit.disabled=true;
    const d=new FormData(form);
    try{
      const {error}=await getSupabase().auth.signInWithPassword({email:String(d.get('email')||'').trim(),password:String(d.get('password')||'')});
      if(error)return setStatus(status,'Connexion impossible. Vérifiez vos informations et la confirmation du courriel.','error');
      location.replace(destination());
    }finally{if(submit)submit.disabled=false}
  });
}

async function forgot(){
  const form=document.querySelector('[data-forgot-form]');if(!form)return;
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!ready())return setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');
    const email=String(new FormData(form).get('email')||'').trim();
    const submit=form.querySelector('[type="submit"]');if(submit)submit.disabled=true;
    try{
      await getSupabase().auth.resetPasswordForEmail(email,{redirectTo:`${SINJIRA_CONFIG.siteUrl}/compte/reinitialiser-mot-de-passe.html`});
      // Réponse identique qu'un compte existe ou non : évite l'énumération d'adresses.
      setStatus(status,'Si un compte correspond à cette adresse, un lien de récupération sera envoyé.','success');
      form.reset();
    }finally{if(submit)submit.disabled=false}
  });
}

async function reset(){
  const form=document.querySelector('[data-reset-form]');if(!form)return;
  if(!ready())return setStatus(status,'Le service de comptes SINJIRA™ est temporairement indisponible.','error');
  const {data:{session}}=await getSupabase().auth.getSession();
  if(!session){
    form.querySelectorAll('input,button').forEach(el=>el.disabled=true);
    setStatus(status,'Ce lien de récupération est invalide ou expiré. Demandez un nouveau lien.','error');
    return;
  }
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    const d=new FormData(form),password=String(d.get('password')||''),confirm=String(d.get('password_confirm')||'');
    if(password.length<12||password!==confirm)return setStatus(status,'Les mots de passe doivent correspondre et contenir au moins 12 caractères.','error');
    const submit=form.querySelector('[type="submit"]');if(submit)submit.disabled=true;
    try{
      const {error}=await getSupabase().auth.updateUser({password});
      if(error)return setStatus(status,'Impossible de mettre à jour le mot de passe. Demandez un nouveau lien de récupération.','error');
      await getSupabase().auth.signOut({scope:'global'}).catch(()=>getSupabase().auth.signOut());
      setStatus(status,'Mot de passe mis à jour. Toutes les sessions ont été fermées; reconnectez-vous avec le nouveau mot de passe.','success');
      setTimeout(()=>location.replace('/compte/connexion.html?reset=1'),900);
    }finally{if(submit)submit.disabled=false}
  });
}

ready();
try{
  if(page==='login')await login();
  else if(page==='forgot')await forgot();
  else if(page==='reset')await reset();
}catch(err){console.warn('[SINJIRA auth]',err);setStatus(status,'Le service d’authentification n’a pas pu terminer cette opération.','error')}
