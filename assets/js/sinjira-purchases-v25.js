import {getSupabase,requireUser,escapeHtml,formatDate} from './sinjira-supabase.js';

const rows=value=>Array.isArray(value)?value:[];
const money=(cents,currency='CAD')=>new Intl.NumberFormat('fr-CA',{style:'currency',currency:currency||'CAD'}).format((Number(cents)||0)/100);

function setHtml(selector,html){
  const node=document.querySelector(selector);
  if(node)node.innerHTML=html;
}

function renderOrders(orders,resolved=true){
  const box=document.querySelector('[data-purchase-history]');
  if(!box)return;
  if(!resolved){
    box.innerHTML='<div class="notice"><strong>Historique temporairement indisponible.</strong><p>Les commandes n’ont pas pu être vérifiées; aucune absence d’achat n’est déduite.</p></div>';
    return;
  }
  box.innerHTML=orders.length?orders.map(order=>{
    const items=rows(order.order_items);
    const itemHtml=items.length?items.map(item=>{
      const product=item.products;
      const label=product?.name||'Produit SINJIRA™';
      return `<div class="account-content-row"><div><strong>${escapeHtml(label)}</strong><small>${escapeHtml(product?.product_type||'produit')} · quantité ${Number(item.quantity||1)}</small></div><span>${escapeHtml(money(Number(item.unit_price_cents||0)*Number(item.quantity||1),order.currency))}</span></div>`;
    }).join(''):'<div class="account-content-row"><div><strong>Commande enregistrée</strong><small>Détail produit temporairement indisponible.</small></div></div>';
    return `<article class="account-content-category"><h3>Commande ${escapeHtml(order.order_number||'SINJIRA')}</h3><p><span class="status-badge">${escapeHtml(order.status||'—')}</span> · ${escapeHtml(formatDate(order.created_at))}</p><div class="account-content-list">${itemHtml}</div><p><strong>Total enregistré : ${escapeHtml(money(order.total_cents,order.currency))}</strong></p></article>`;
  }).join(''):'<div class="notice"><strong>Aucune commande enregistrée.</strong><p>Les commandes associées à votre compte apparaîtront ici avec leur statut. Une précommande sans paiement reste séparée.</p></div>';
}

function renderEntitlements(entitlements,resolved=true){
  const box=document.querySelector('[data-purchase-entitlements]');
  if(!box)return;
  if(!resolved){
    box.innerHTML='<div class="notice"><strong>Droits numériques temporairement indisponibles.</strong><p>Les droits du compte n’ont pas pu être vérifiés; aucun accès supplémentaire n’est accordé ou retiré.</p></div>';
    return;
  }
  box.innerHTML=entitlements.length?entitlements.map(row=>{
    const product=row.products;
    return `<article class="account-content-row"><div><strong>${escapeHtml(product?.name||'Droit numérique SINJIRA™')}</strong><small>${escapeHtml(product?.product_type||'accès')} · source : ${escapeHtml(row.source||'compte')} · attribué ${escapeHtml(formatDate(row.granted_at))}</small></div><span class="role-chip">Accès actif</span></article>`;
  }).join(''):'<div class="notice"><strong>Aucun droit numérique attribué.</strong><p>Les licences, achats numériques ou accès accordés à votre compte apparaîtront ici.</p></div>';
}

function renderCreatorPortfolio(projectsResult,novelsResult,productsResult){
  const root=document.querySelector('[data-creator-portfolio]');
  if(!root)return;
  root.hidden=false;
  const projects=rows(projectsResult.data),novels=rows(novelsResult.data),products=rows(productsResult.data);
  const projectRows=projectsResult.error
    ?'<p>Catalogue des projets temporairement indisponible.</p>'
    :projects.map(row=>`<div class="account-content-row"><div><strong>${escapeHtml(row.name)}</strong><small>${escapeHtml(row.type||'projet')} · ${escapeHtml(row.status||'—')} · ${escapeHtml(row.visibility||'—')}</small></div><span class="role-chip">Création</span></div>`).join('')||'<p>Aucun projet enregistré.</p>';
  const novelRows=novelsResult.error
    ?'<p>Catalogue des romans temporairement indisponible.</p>'
    :novels.map(row=>`<div class="account-content-row"><div><strong>${escapeHtml(row.title)}</strong><small>roman · ${escapeHtml(row.status||'—')}</small></div><span class="role-chip">Création</span></div>`).join('')||'<p>Aucun roman enregistré.</p>';
  const productRows=productsResult.error
    ?'<p>Catalogue des produits temporairement indisponible.</p>'
    :products.map(row=>`<div class="account-content-row"><div><strong>${escapeHtml(row.name)}</strong><small>${escapeHtml(row.product_type||'produit')} · ${row.active?'actif':'inactif / préparation'}</small></div><span class="role-chip">Catalogue</span></div>`).join('')||'<p>Aucun produit enregistré.</p>';
  setHtml('[data-creator-projects]',projectRows);
  setHtml('[data-creator-novels]',novelRows);
  setHtml('[data-creator-products]',productRows);
}

async function init(){
  const root=document.querySelector('[data-purchases-v25]');
  if(!root)return;
  const user=await requireUser('/compte/connexion.html');
  const s=getSupabase();

  const capabilitiesResult=await s.rpc('sinjira_my_account_capabilities');
  const capabilitiesResolved=!capabilitiesResult.error&&capabilitiesResult.data;
  const childMode=capabilitiesResolved&&capabilitiesResult.data.library_mode==='reviewed_11_12';
  const commerceAllowed=capabilitiesResolved&&capabilitiesResult.data.commerce===true;
  const orderCount=document.querySelector('[data-paid-order-count]');
  const rightsCount=document.querySelector('[data-purchase-right-count]');
  const role=document.querySelector('[data-purchase-account-role]');
  const status=document.querySelector('[data-purchases-v25-status]');

  if(!capabilitiesResolved){
    renderOrders([],false);
    renderEntitlements([],false);
    if(orderCount)orderCount.textContent='—';
    if(rightsCount)rightsCount.textContent='—';
    if(role)role.textContent='État du compte non confirmé';
    if(status){
      status.hidden=false;
      status.dataset.statusType='error';
      status.textContent='La sécurité du compte n’a pas pu être vérifiée. Les informations commerciales restent masquées.';
    }
    return;
  }

  if(!commerceAllowed){
    setHtml('[data-purchase-history]',childMode
      ?'<div class="notice"><strong>Achats protégés pour les comptes 11–12 ans.</strong><p>Les commandes peuvent rester associées au compte, mais leurs détails commerciaux ne sont pas exposés ici. Les contenus adaptés apparaissent dans la Bibliothèque après vérification humaine.</p></div>'
      :'<div class="notice"><strong>Historique commercial non disponible pour cet état de compte.</strong></div>');
    setHtml('[data-purchase-entitlements]',childMode
      ?'<div class="notice"><strong>Droits numériques protégés pour les comptes 11–12 ans.</strong><p>Les droits peuvent rester enregistrés côté serveur sans afficher les produits, sources ou dates au navigateur.</p></div>'
      :'<div class="notice"><strong>Droits commerciaux non disponibles pour cet état de compte.</strong></div>');
    if(orderCount)orderCount.textContent='—';
    if(rightsCount)rightsCount.textContent='—';
    if(role)role.textContent=childMode?'Compte Junior 11–12 ans':'Compte à accès commercial restreint';
    if(status){
      status.hidden=false;
      status.dataset.statusType='info';
      status.textContent=childMode?'Compte Junior 11–12 ans · informations commerciales masquées.':'Informations commerciales masquées pour cet état de compte.';
    }
    return;
  }

  const [ownerResult,ordersResult,entitlementsResult]=await Promise.all([
    s.rpc('is_sinjira_owner',{p_user_id:user.id}),
    s.from('orders').select('id,order_number,status,currency,total_cents,created_at,order_items(quantity,unit_price_cents,products(id,slug,name,product_type,active))').eq('user_id',user.id).order('created_at',{ascending:false}),
    s.from('user_entitlements').select('product_id,source,granted_at,products(id,slug,name,product_type,active)').eq('user_id',user.id).order('granted_at',{ascending:false})
  ]);

  const catalogAccessResult=await s.rpc('sinjira_my_catalog_access_mode');

  const orders=rows(ordersResult.data);
  const entitlements=rows(entitlementsResult.data);
  const ordersResolved=!ordersResult.error,entitlementsResolved=!entitlementsResult.error;
  renderOrders(orders,ordersResolved);
  renderEntitlements(entitlements,entitlementsResolved);

  if(orderCount)orderCount.textContent=ordersResolved?String(orders.length):'—';
  if(rightsCount)rightsCount.textContent=entitlementsResolved?String(entitlements.length):'—';

  const ownerResolved=!ownerResult.error;
  const isOwner=ownerResolved&&ownerResult.data===true;
  const catalogAccessResolved=!catalogAccessResult.error;
  const catalogAccessMode=catalogAccessResolved?String(catalogAccessResult.data||'member'):'member';
  const isFamily=catalogAccessMode==='family';
  const hasCreatorCatalog=isOwner||isFamily;
  if(role)role.textContent=!ownerResolved&&!catalogAccessResolved?'Rôle du compte non confirmé':isOwner?'Compte créateur SINJIRA™':isFamily?'Compte famille créateur SINJIRA™':'Compte membre SINJIRA™';

  let creatorResults=[];
  if(hasCreatorCatalog){
    creatorResults=await Promise.all([
      s.from('projects').select('id,slug,name,type,status,visibility,sort_order').order('sort_order'),
      s.from('sinjira_novels').select('id,slug,title,status,sort_order').order('sort_order'),
      s.from('products').select('id,slug,name,product_type,active,created_at').order('created_at')
    ]);
    renderCreatorPortfolio(...creatorResults);
  }

  const errors=[ownerResult,ordersResult,entitlementsResult,...creatorResults].filter(result=>result.error);
  if(catalogAccessResult.error)errors.push(catalogAccessResult);
  if(errors.length&&status){
    status.hidden=false;
    status.dataset.statusType='error';
    status.textContent='Certaines informations d’achat, de rôle ou du portefeuille créateur n’ont pas pu être vérifiées. Aucun accès supplémentaire n’a été accordé automatiquement.';
  }
}

init().catch(error=>{
  const status=document.querySelector('[data-purchases-v25-status]');
  if(status){
    status.hidden=false;
    status.dataset.statusType='error';
    status.textContent=error?.message||'Impossible de charger vos acquisitions pour le moment.';
  }
});
