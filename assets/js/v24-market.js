import {getSupabase,isSinjiraBackendConfigured,escapeHtml} from './sinjira-supabase.js';
import {featureEnabled} from './v24-feature-flags.js';
const box=document.querySelector('[data-v24-market-feed]');
if(box && featureEnabled('market') && isSinjiraBackendConfigured()){
  try{
    const {data,error}=await getSupabase().from('market_listings').select('id,title,description,price_cad,listing_type,condition_label,location_label,created_at').eq('status','active').order('created_at',{ascending:false}).limit(24);
    if(error) throw error;
    box.innerHTML=(data||[]).length?(data||[]).map(x=>`<article class="v24-market-card"><div class="body"><span class="v24-badge">${escapeHtml(x.listing_type||'vente')}</span><h2>${escapeHtml(x.title||'Article')}</h2><p>${escapeHtml(x.description||'')}</p><p class="v24-price ${Number(x.price_cad)===0?'v24-free':''}">${Number(x.price_cad)===0?'GRATUIT':Number(x.price_cad).toLocaleString('fr-CA',{style:'currency',currency:'CAD'})}</p><small>${escapeHtml(x.location_label||'')}</small></div></article>`).join(''):'<div class="v24-empty">Aucune annonce active.</div>';
  }catch(e){box.innerHTML='<div class="v24-empty">Le Marché est temporairement indisponible.</div>'}
}
