import {getSupabase,requireUser,setStatus,escapeHtml} from './sinjira-supabase.js';

const form=document.querySelector('[data-market-listing-form]');
const box=document.querySelector('[data-market-own-listings]');
const status=document.querySelector('[data-market-account-status]');

function serverMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||/market_listings|relation .* does not exist|schema cache/i.test(text);
}
function setFormReady(ready){
  if(!form)return;
  for(const el of form.elements){if(el.type==='submit'||el.tagName==='BUTTON')el.disabled=!ready}
}
function tokenRule(price){return Number(price)>20?1:0}

if(form&&box){
  const user=await requireUser();
  const s=getSupabase();
  let ready=true;

  async function render(){
    const {data,error}=await s.from('market_listings').select('*').eq('seller_user_id',user.id).order('created_at',{ascending:false});
    if(error){
      ready=!serverMissing(error);setFormReady(ready);
      box.innerHTML=serverMissing(error)?'<div class="v2433-server-note"><strong>Marché en préparation</strong><br>Les brouillons seront disponibles après la synchronisation du serveur. Aucun paiement ni débit de jeton n’est actif pendant cette phase.</div>':'<div class="v24-empty">Impossible de charger vos annonces pour le moment.</div>';
      return;
    }
    ready=true;setFormReady(true);
    const rows=Array.isArray(data)?data:[];
    box.innerHTML=rows.length?rows.map(x=>{
      const price=Number(x.price_cad||0),cost=tokenRule(price);
      return `<article class="v24-panel"><span class="v24-badge">${escapeHtml(x.status)}</span><h3>${escapeHtml(x.title)}</h3><p class="v24-price ${price===0?'v24-free':''}">${price===0?'GRATUIT':price.toLocaleString('fr-CA',{style:'currency',currency:'CAD'})}</p><small>${price===0?'Don réel : 0 $ doit rester 0 $.':cost?'Publication future : 1 Jeton SINJIRA™.':'Publication future : aucun jeton requis.'}</small><button class="btn btn-secondary btn-small" type="button" data-delete-listing="${x.id}">Supprimer</button></article>`;
    }).join(''):'<div class="v24-empty">Aucun brouillon.</div>';
    box.querySelectorAll('[data-delete-listing]').forEach(b=>b.addEventListener('click',async()=>{
      if(!confirm('Supprimer ce brouillon?'))return;
      const {error}=await s.from('market_listings').delete().eq('id',b.dataset.deleteListing).eq('seller_user_id',user.id);
      if(error){setStatus(status,'Impossible de supprimer ce brouillon pour le moment.','error');return}
      await render();
    }));
  }

  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!ready){setStatus(status,'Les brouillons sont temporairement indisponibles tant que le serveur n’est pas synchronisé.','info');return}
    const d=new FormData(form);
    let price=Number(d.get('price_cad')||0);
    let type=String(d.get('listing_type')||'sale');
    if(!Number.isFinite(price)||price<0){setStatus(status,'Indiquez un prix valide de 0 $ ou plus.','error');return}
    if(type==='gift')price=0;
    if(price===0)type='gift';
    const title=String(d.get('title')||'').trim(),description=String(d.get('description')||'').trim();
    if(!title||!description){setStatus(status,'Le titre et la description sont obligatoires.','error');return}
    const {error}=await s.from('market_listings').insert({seller_user_id:user.id,title,description,price_cad:price,listing_type:type,condition_label:String(d.get('condition_label')||''),location_label:String(d.get('location_label')||'').trim()||null,status:'draft'});
    if(error){
      if(serverMissing(error)){ready=false;setFormReady(false);setStatus(status,'Le serveur du Marché doit encore être synchronisé.','info');return}
      setStatus(status,'Impossible d’enregistrer ce brouillon pour le moment.','error');return;
    }
    form.reset();
    const cost=tokenRule(price);
    setStatus(status,price===0?'Brouillon de don enregistré. Rappel : 0 $ devra rester 0 $ réellement lors de la publication.':cost?'Brouillon enregistré. Lors de la publication future, cette annonce de plus de 20 $ utilisera 1 Jeton SINJIRA™; aucune commission ne sera prélevée pour un particulier.':'Brouillon enregistré. Aucune utilisation de jeton ne sera requise pour une annonce de 20 $ ou moins.','success');
    await render();
  });
  await render();
}
