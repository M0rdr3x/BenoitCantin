import {getSupabase,requireUser,RULES_VERSION,socialStatus,socialErrorStatus} from './sinjira-social-common.js?v=24.4.82';

const status=document.querySelector('[data-rules-status]');
const button=document.querySelector('[data-accept-rules]');

function installV2Rules(){
  const rules=document.querySelector('.v20-rules');
  if(!rules||rules.querySelector('[data-rules-v2-safety]'))return;
  const card=document.createElement('article');
  card.className='v20-rule-card';
  card.dataset.rulesV2Safety='';
  card.innerHTML=`<h2>Protection renforcée des mineurs et interdictions absolues</h2>
    <p><strong>Rencontres SINJIRA™ est strictement réservé aux personnes de 18 ans et plus : les 17 ans et moins n’y ont aucun accès.</strong></p>
    <p>Sur tout SINJIRA™, sont interdits : la prostitution et sa promotion, le proxénétisme, l’exploitation sexuelle, la traite, la vente ou l’achat de personnes, la vente de drogues, ainsi que la vente, promotion ou redirection vers du contenu sexuel payant ou des services de type OnlyFans.</p>
    <p>La protection jeunesse interdit aussi les sollicitations sexuelles ou financières, le grooming, les demandes de photos intimes, les invitations à garder une interaction secrète et le transfert d’un mineur vers des coordonnées, réseaux sociaux ou messageries externes. Les espaces jeunesse et adultes restent séparés côté serveur.</p>`;
  rules.prepend(card);
}

function fail(error,fallback='Impossible d’enregistrer les règles pour le moment.'){
  socialErrorStatus(status,error,fallback);
}

installV2Rules();

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
    if(error?.message!=='Connexion requise')fail(error,'La page des règles n’a pas pu terminer sa vérification.');
  }
})();
