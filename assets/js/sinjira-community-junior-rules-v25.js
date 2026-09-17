import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';

const s=getSupabase();
const status=document.querySelector('[data-junior-rules-status]');
const button=document.querySelector('[data-junior-rules-accept]');

(async()=>{
  try{
    const user=await requireUser('/compte/connexion.html');
    const {data:band,error:bandError}=await s.rpc('sinjira_my_age_band');
    if(bandError)throw bandError;
    if(band!=='child'){
      location.replace('/compte/communaute.html');
      return;
    }

    const {data:enabled,error:enabledError}=await s.rpc('sinjira_junior_community_enabled',{p_user_id:user.id});
    if(enabledError)throw enabledError;
    if(enabled!==true){
      if(button)button.disabled=true;
      setStatus(status,'Ton parent ou tuteur doit d’abord activer la Communauté Junior dans Relations.','info');
      return;
    }

    const {data:accepted,error:acceptedError}=await s.rpc('has_accepted_junior_community_rules',{p_user_id:user.id});
    if(acceptedError)throw acceptedError;
    if(accepted===true){
      if(button){button.disabled=true;button.textContent='Règles Junior déjà acceptées';}
      setStatus(status,'Tu as déjà accepté la version actuelle des règles Junior.','success');
    }

    button?.addEventListener('click',async()=>{
      button.disabled=true;
      const {data,error}=await s.rpc('junior_community_accept_rules');
      if(error){
        button.disabled=false;
        const msg=String(error.message||'').includes('JUNIOR_GUARDIAN_CONSENT_REQUIRED')
          ? 'Ton parent ou tuteur doit d’abord activer la Communauté Junior dans Relations.'
          : 'Impossible d’enregistrer les règles Junior pour le moment.';
        setStatus(status,msg,'error');
        return;
      }
      if(!data?.ok){
        button.disabled=false;
        setStatus(status,'Impossible d’enregistrer les règles Junior pour le moment.','error');
        return;
      }
      setStatus(status,'Règles Junior acceptées. Ouverture de la Communauté Junior…','success');
      const next=new URLSearchParams(location.search).get('next');
      setTimeout(()=>{location.href=next&&next.startsWith('/')?next:'/compte/communaute-junior.html';},400);
    });
  }catch(error){
    if(error?.message!=='Connexion requise')setStatus(status,'La page des règles Junior n’a pas pu terminer sa vérification.','error');
  }
})();