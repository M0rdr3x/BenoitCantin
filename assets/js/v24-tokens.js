import {getSupabase,requireUser,escapeHtml,isSinjiraOwner} from './sinjira-supabase.js';

const balance=document.querySelector('[data-token-balance]');
const ledger=document.querySelector('[data-token-ledger]');

function serverMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||/token_ledger|relation .* does not exist|schema cache/i.test(text);
}

if(balance&&ledger){
  const user=await requireUser();
  if(isSinjiraOwner(user)){
    balance.textContent='∞';
    ledger.innerHTML='<article class="v24-panel v24-owner-access"><span class="v24-badge live">Compte propriétaire</span><h3>Jetons illimités</h3><p>AbyssTime ne consomme aucun Jeton SINJIRA™ pour les fonctions internes de la plateforme.</p><p><small>Les Jetons restent des crédits de service : ils ne sont pas une cryptomonnaie, ne sont pas transférables entre utilisateurs vivants et ne donnent jamais d’avantage pay-to-win.</small></p></article>';
  }else{
    const {data,error}=await getSupabase().from('token_ledger').select('amount,entry_type,description,created_at').eq('user_id',user.id).order('created_at',{ascending:false}).limit(100);
    if(error){
      balance.textContent='—';
      ledger.innerHTML=serverMissing(error)?'<div class="v2433-server-note"><strong>Jetons en préparation</strong><br>Le grand livre serveur doit encore être synchronisé. Aucun achat réel de jetons n’est actif pendant cette phase.</div>':'<div class="v24-empty">Impossible de charger le solde des Jetons pour le moment.</div>';
    }else{
      const rows=Array.isArray(data)?data:[];
      balance.textContent=String(rows.reduce((sum,row)=>sum+Number(row.amount||0),0));
      ledger.innerHTML=rows.length?rows.map(x=>`<article class="v24-panel"><strong>${Number(x.amount)>0?'+':''}${Number(x.amount)}</strong> · ${escapeHtml(x.entry_type||'mouvement')}<p>${escapeHtml(x.description||'')}</p><small>${escapeHtml(x.created_at||'')}</small></article>`).join(''):'<div class="v24-empty">Aucun mouvement de jeton.</div>';
    }
  }
}
