import {getSupabase,requireUser,setStatus,escapeHtml,SINJIRA_CONFIG} from './sinjira-supabase.js';

const form=document.querySelector('[data-license-redeem-form]');
const status=document.querySelector('[data-license-status]');
const list=document.querySelector('[data-license-list]');
const BOOK_ONE_SLUG='sinjira-livre-01-la-cendre-du-jugement';

function serverMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST202'||code==='PGRST205'||/products|sinjira_my_product_rights|relation .* does not exist|schema cache/i.test(text);
}
function freeModeCard(){
  if(SINJIRA_CONFIG.freeOnlyMode!==true)return '';
  return '<article class="v24-panel"><span class="v24-badge live">Mode gratuit verrouillé</span><h3>Aucun achat requis sur le site</h3><p>Paiements, IA distante, publication commerciale et achats de jetons sont désactivés. L’activation d’un code physique existant reste disponible.</p></article>';
}
function ownerRoleCard(){
  return '<article class="v24-panel v24-owner-access"><span class="v24-badge live">Rôle propriétaire vérifié</span><h3>Rôle de gestion SINJIRA™</h3><p>Le rôle propriétaire ouvre les espaces et fonctions prévus pour la gestion du projet. Il ne crée pas automatiquement un droit numérique sur chaque produit : seuls les droits réellement attribués au compte sont affichés ci-dessous.</p></article>';
}
function productRightCard(row){
  const name=escapeHtml(row.name||row.slug||'Produit SINJIRA™');
  const source=escapeHtml(row.source==='paid_order'?'achat payé':row.source||'licence');
  if(row.slug===BOOK_ONE_SLUG){
    return `<article class="v24-panel"><span class="v24-badge live">Droit numérique reconnu</span><h3>${name}</h3><p>Source : ${source}. Ce droit est réellement associé à votre compte. L’édition intégrale n’est jamais exposée ici par un lien public : sa disponibilité est contrôlée séparément par la diffusion privée du Livre I.</p><div class="hero-actions"><a class="btn btn-secondary" href="/projets/sinjira/romans/">Page du roman</a></div></article>`;
  }
  return `<article class="v24-panel"><span class="v24-badge live">Possédé</span><h3>${name}</h3><p>Source : ${source}</p></article>`;
}

async function init(){
  if(!form||!list)return;
  const user=await requireUser();
  const s=getSupabase();
  const [ownerResult,capabilitiesResult]=await Promise.all([
    s.rpc('is_sinjira_owner',{p_user_id:user.id}),
    s.rpc('sinjira_my_account_capabilities')
  ]);
  const owner=!ownerResult.error&&ownerResult.data===true;
  const capabilitiesResolved=!capabilitiesResult.error&&capabilitiesResult.data;
  const childMode=capabilitiesResolved&&capabilitiesResult.data.library_mode==='reviewed_11_12';
  if(!capabilitiesResolved){
    form.hidden=true;
    list.innerHTML='<div class="v24-empty">Impossible de vérifier l’état de sécurité du compte. Les licences restent masquées.</div>';
    setStatus(status,'La vérification de sécurité du compte est temporairement indisponible. Aucun droit commercial n’est affiché.','error');
    return;
  }
  if(childMode){
    form.hidden=true;
    list.innerHTML='<div class="notice"><strong>Licences protégées pour les comptes 11–12 ans.</strong><p>Les droits commerciaux peuvent rester associés au compte, mais leurs détails et les contenus payants ne sont pas exposés ici. Les contenus adaptés apparaissent dans la Bibliothèque après vérification humaine.</p></div>';
    setStatus(status,'Compte Junior 11–12 ans · droits commerciaux masqués.','info');
    return;
  }
  if(ownerResult.error){
    setStatus(status,'Le rôle du compte n’a pas pu être confirmé par le serveur. Les droits commerciaux explicites restent consultables.','info');
  }

  async function render(){
    const freeCard=freeModeCard();
    const roleCard=owner?ownerRoleCard():'';
    const {data,error}=await s.rpc('sinjira_my_product_rights');
    if(error){
      list.innerHTML=freeCard+roleCard+(serverMissing(error)?'<div class="v2433-server-note"><strong>Licences en préparation</strong><br>Le serveur des droits d’accès doit encore être synchronisé. Aucun droit existant n’est supprimé pendant cette attente.</div>':'<div class="v24-empty">Impossible de lire les licences pour le moment.</div>');
      return;
    }
    const rows=Array.isArray(data)?data:[];
    const empty=owner
      ?'<div class="v24-empty">Aucun droit numérique explicite n’est attribué à ce compte pour le moment. Le rôle propriétaire reste actif pour les fonctions qui lui sont réservées, sans inventer de possession produit.</div>'
      :'<div class="v24-empty">Aucune licence liée à ce compte.</div>';
    list.innerHTML=freeCard+roleCard+(rows.length?rows.map(productRightCard).join(''):empty);
  }

  form.addEventListener('submit',async e=>{
    e.preventDefault();
    const code=String(new FormData(form).get('code')||'').trim();
    if(!code){setStatus(status,'Entrez un code d’activation.','error');return}
    const {data,error}=await s.functions.invoke('redeem-license-code',{body:{code}});
    if(error||!data?.ok){
      setStatus(status,error&&serverMissing(error)?'Le service d’activation n’est pas encore disponible.':data?.error||'Activation impossible pour le moment.','error');
      return;
    }
    form.reset();setStatus(status,'Produit activé sur votre Compte SINJIRA™.','success');await render();
  });
  await render();
}

init().catch(error=>{
  if(form)form.hidden=true;
  if(list)list.innerHTML='<div class="v24-empty">Impossible de charger les licences pour le moment. Aucun droit commercial supplémentaire n’est affiché.</div>';
  if(error?.message!=='Connexion requise')setStatus(status,'La vérification des licences a échoué de façon sécurisée. Réessayez plus tard.','error');
});
