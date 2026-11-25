import {getSupabase,requireUser,setStatus,escapeHtml,formatDate,SINJIRA_CONFIG} from './sinjira-supabase.js';

const form=document.querySelector('[data-license-redeem-form]');
const status=document.querySelector('[data-license-status]');
const list=document.querySelector('[data-license-list]');
const BOOK_ONE_SLUG='sinjira-livre-01-la-cendre-du-jugement';

function serverMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||/products|user_entitlements|relation .* does not exist|schema cache/i.test(text);
}
function freeModeCard(){
  if(SINJIRA_CONFIG.freeOnlyMode!==true)return '';
  return '<article class="v24-panel"><span class="v24-badge live">Mode gratuit verrouillé</span><h3>Aucun achat requis sur le site</h3><p>Paiements, IA distante, publication commerciale et achats de jetons sont désactivés. L’activation d’un code physique existant reste disponible.</p></article>';
}
function ownerRoleCard(){
  return '<article class="v24-panel v24-owner-access"><span class="v24-badge live">Rôle propriétaire vérifié</span><h3>Rôle de gestion SINJIRA™</h3><p>Le rôle propriétaire ouvre les espaces et fonctions prévus pour la gestion du projet. Il ne crée pas automatiquement un droit numérique sur chaque produit : seuls les droits réellement attribués au compte sont affichés ci-dessous.</p></article>';
}
function entitlementCard(row){
  const product=row.products||{};
  const name=escapeHtml(product.name||product.slug||'Produit SINJIRA™');
  const source=escapeHtml(row.source||'licence');
  const granted=row.granted_at?`<small>Attribué le ${escapeHtml(formatDate(row.granted_at))}</small>`:'';
  if(product.slug===BOOK_ONE_SLUG){
    return `<article class="v24-panel"><span class="v24-badge live">Droit numérique reconnu</span><h3>${name}</h3><p>Source : ${source}. Ce droit est associé à votre compte. L’édition intégrale n’est jamais exposée ici par un lien public : sa disponibilité est contrôlée séparément par la diffusion privée du Livre I.</p>${granted}<div class="hero-actions"><a class="btn btn-secondary" href="/projets/sinjira/romans/">Page du roman</a></div></article>`;
  }
  return `<article class="v24-panel"><span class="v24-badge live">Possédé</span><h3>${name}</h3><p>Source : ${source}</p>${granted}</article>`;
}

if(form&&list){
  const input=form.elements.code,button=form.querySelector('button[type="submit"]');
  let ready=false,busy=false;
  // Bloquer la soumission native avant toute opération asynchrone.
  form.addEventListener('submit',event=>event.preventDefault());
  const user=await requireUser();
  const s=getSupabase();
  const ownerResult=await s.rpc('is_sinjira_owner',{p_user_id:user.id});
  const owner=!ownerResult.error&&ownerResult.data===true;
  if(ownerResult.error){
    setStatus(status,'Le rôle du compte n’a pas pu être confirmé par le serveur. Les licences individuelles restent consultables.','info');
  }

  async function render(){
    const freeCard=freeModeCard();
    const roleCard=owner?ownerRoleCard():'';
    const {data,error}=await s.from('user_entitlements').select('source,granted_at,products(slug,name,product_type)').eq('user_id',user.id).order('granted_at',{ascending:false});
    if(error){
      list.innerHTML=freeCard+roleCard+(serverMissing(error)?'<div class="v2433-server-note"><strong>Licences en préparation</strong><br>Le serveur des droits d’accès doit encore être synchronisé. Aucun droit existant n’est supprimé pendant cette attente.</div>':'<div class="v24-empty">Impossible de lire les licences pour le moment.</div>');
      return;
    }
    const rows=Array.isArray(data)?data:[];
    const empty=owner
      ?'<div class="v24-empty">Aucun droit numérique explicite n’est attribué à ce compte pour le moment. Le rôle propriétaire reste actif pour les fonctions qui lui sont réservées, sans inventer de possession produit.</div>'
      :'<div class="v24-empty">Aucune licence liée à ce compte.</div>';
    list.innerHTML=freeCard+roleCard+(rows.length?rows.map(entitlementCard).join(''):empty);
  }

  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!ready||busy)return;
    const code=String(input.value||'').trim();
    if(code.length<12||code.length>80){
      setStatus(status,'Entrez un code d’activation de 12 à 80 caractères.','error');
      input.focus();return;
    }
    busy=true;
    input.readOnly=true;button.disabled=true;
    form.setAttribute('aria-busy','true');
    button.textContent='Activation en cours…';
    setStatus(status,'Vérification de votre code…','info');
    try{
      const {data,error}=await s.functions.invoke('redeem-license-code',{body:{code}});
      if(error||!data?.ok){
        setStatus(status,'Activation non confirmée. Vérifiez vos licences avant de réessayer ou contactez le support.','error');
        try{await render()}catch{}
        return;
      }
      form.reset();
      setStatus(status,'Produit activé sur votre Compte SINJIRA™.','success');
      try{await render()}catch{
        setStatus(status,'Produit activé. Rechargez la page pour actualiser vos licences.','success');
      }
    }catch{
      setStatus(status,'Activation non confirmée. Votre saisie est conservée dans cet onglet. Vérifiez vos licences avant de réessayer.','error');
      try{await render()}catch{}
    }finally{
      busy=false;input.readOnly=false;button.disabled=false;
      button.textContent='Activer';
      form.setAttribute('aria-busy','false');
    }
  });
  await render();
  ready=true;input.disabled=false;button.disabled=false;
  form.setAttribute('aria-busy','false');
  if(!ownerResult.error)setStatus(status,'Vous pouvez saisir votre code physique.','info');
}
