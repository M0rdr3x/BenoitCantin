import {getSupabase,requireUser,setStatus,escapeHtml,isSinjiraOwner} from './sinjira-supabase.js';

const form=document.querySelector('[data-license-redeem-form]');
const status=document.querySelector('[data-license-status]');
const list=document.querySelector('[data-license-list]');

function serverMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||/products|user_entitlements|relation .* does not exist|schema cache/i.test(text);
}

if(form&&list){
  const user=await requireUser();
  const s=getSupabase();
  const owner=isSinjiraOwner(user);

  async function render(){
    if(owner){
      form.hidden=true;
      const ownerCard='<article class="v24-panel v24-owner-access"><span class="v24-badge live">Compte propriétaire</span><h3>Accès total SINJIRA™</h3><p>AbyssTime dispose d’un accès permanent à tous les romans, jeux, licences, tests, projets et futurs contenus SINJIRA™. Aucun code d’activation n’est requis.</p></article>';
      const {data,error}=await s.from('products').select('slug,name,product_type,active').eq('active',true).order('name');
      if(error){
        list.innerHTML=ownerCard+'<div class="v2433-server-note"><strong>Catalogue serveur en attente</strong><br>L’accès propriétaire reste actif même si le catalogue détaillé n’est pas encore synchronisé.</div>';
        return;
      }
      const products=Array.isArray(data)?data:[];
      list.innerHTML=ownerCard+(products.length?products.map(x=>`<article class="v24-panel"><span class="v24-badge live">Accès propriétaire</span><h3>${escapeHtml(x.name||x.slug||'Produit SINJIRA™')}</h3><p>${escapeHtml(x.product_type||'contenu')}</p></article>`).join(''):'<div class="v24-empty">Le catalogue ne contient encore aucun produit actif; l’accès propriétaire universel reste néanmoins actif.</div>');
      return;
    }

    const {data,error}=await s.from('user_entitlements').select('source,granted_at,products(slug,name,product_type)').eq('user_id',user.id).order('granted_at',{ascending:false});
    if(error){
      list.innerHTML=serverMissing(error)?'<div class="v2433-server-note"><strong>Licences en préparation</strong><br>Le serveur des droits d’accès doit encore être synchronisé. Aucun droit existant n’est supprimé pendant cette attente.</div>':'<div class="v24-empty">Impossible de lire les licences pour le moment.</div>';
      return;
    }
    const rows=Array.isArray(data)?data:[];
    list.innerHTML=rows.length?rows.map(x=>`<article class="v24-panel"><span class="v24-badge live">Possédé</span><h3>${escapeHtml(x.products?.name||x.products?.slug||'Produit SINJIRA™')}</h3><p>Source : ${escapeHtml(x.source||'licence')}</p></article>`).join(''):'<div class="v24-empty">Aucune licence liée à ce compte.</div>';
  }

  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(owner)return;
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
