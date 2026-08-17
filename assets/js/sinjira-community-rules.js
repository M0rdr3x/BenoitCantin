import {getSupabase,requireUser,RULES_VERSION,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.42';

const status=document.querySelector('[data-rules-status]');
const button=document.querySelector('[data-accept-rules]');

function fail(error,fallback='Impossible d’enregistrer les règles pour le moment.'){
  socialErrorStatus(status,error,fallback);
}

(async()=>{
  try{
    const user=await requireUser('/compte/connexion.html');
    const {data,error}=await getSupabase()
      .from('community_rule_acceptances')
      .select('rules_version,accepted_at')
      .eq('user_id',user.id)
      .eq('rules_version',RULES_VERSION)
      .maybeSingle();
    if(error)throw error;

    if(data&&button){
      button.textContent='Règles déjà acceptées';
      button.disabled=true;
      socialStatus(status,'Vous avez déjà accepté la version actuelle des règles.','success');
    }

    button?.addEventListener('click',async()=>{
      button.disabled=true;
      try{
        const {error:saveError}=await getSupabase().from('community_rule_acceptances').upsert({
          user_id:user.id,
          rules_version:RULES_VERSION,
          accepted_at:new Date().toISOString()
        },{onConflict:'user_id,rules_version'});
        if(saveError)return fail(saveError);
        socialStatus(status,'Règles acceptées. Vous pouvez maintenant utiliser la Communauté et le Réseau personnage.','success');
        const next=new URLSearchParams(location.search).get('next');
        setTimeout(()=>{location.href=next&&next.startsWith('/')?next:'/compte/communaute.html';},500);
      }finally{
        if(button&&!button.textContent.includes('déjà'))button.disabled=false;
      }
    });
  }catch(error){
    if(error?.message!=='Connexion requise'){
      fail(error,'La page des règles n’a pas pu terminer sa vérification.');
    }
  }
})();
