import {getSupabase,getCurrentUser,isSinjiraOwner,escapeHtml} from './sinjira-supabase.js';

const box=document.querySelector('[data-admin-health]');
if(box){
  const s=getSupabase();
  const user=await getCurrentUser();

  const label={ok:'NORMAL',missing:'À SYNCHRONISER',restricted:'RESTREINT',degraded:'DÉGRADÉ'};
  const cls={ok:'live',missing:'staged',restricted:'staged',degraded:'staged'};
  const missing=(error)=>{
    const code=String(error?.code||'');
    const text=String(error?.message||'');
    return code==='PGRST205'||code==='PGRST202'||/relation .* does not exist|schema cache|Could not find the table|Could not find the function/i.test(text);
  };
  const restricted=(error)=>String(error?.code||'')==='42501'||/permission denied|row-level security|not allowed/i.test(String(error?.message||''));

  async function tableState(table){
    const {count,error}=await s.from(table).select('*',{head:true,count:'exact'}).limit(1);
    if(!error)return {name:table,state:'ok',detail:`${Number(count||0).toLocaleString('fr-CA')} ligne(s)`};
    if(missing(error))return {name:table,state:'missing',detail:'Table absente du schéma exposé'};
    if(restricted(error))return {name:table,state:'restricted',detail:'Table présente, accès limité par la sécurité'};
    console.warn('[SINJIRA admin health]',table,error);
    return {name:table,state:'degraded',detail:'Réponse serveur inattendue'};
  }

  async function functionState(name,body){
    const {data,error}=await s.functions.invoke(name,{body});
    if(!error&&data?.ok!==false)return {name:`Edge: ${name}`,state:'ok',detail:'Fonction joignable'};
    if(error&&(/FunctionsFetchError|Failed to send|404|not found/i.test(String(error?.name||'')+' '+String(error?.message||''))))return {name:`Edge: ${name}`,state:'missing',detail:'Fonction non déployée ou non joignable'};
    console.warn('[SINJIRA admin health edge]',name,error||data);
    return {name:`Edge: ${name}`,state:'degraded',detail:'Fonction joignable mais réponse incomplète'};
  }

  async function ownerRepairState(){
    if(!isSinjiraOwner(user))return {name:'AbyssTime / propriétaire',state:'restricted',detail:'Compte propriétaire requis'};
    const {data,error}=await s.rpc('ensure_sinjira_owner_character');
    if(!error&&data?.ok)return {name:'AbyssTime / propriétaire',state:'ok',detail:'Personnage, accès total et synchronisation propriétaire disponibles'};
    if(missing(error))return {name:'AbyssTime / propriétaire',state:'missing',detail:'RPC V24.3.1 non déployée'};
    console.warn('[SINJIRA admin health owner]',error||data);
    return {name:'AbyssTime / propriétaire',state:'degraded',detail:'RPC présente mais réparation incomplète'};
  }

  function card(row){
    return `<article class="v19-health-card"><div><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(row.detail)}</span></div><span class="v24-badge ${cls[row.state]||'staged'}">${escapeHtml(label[row.state]||row.state)}</span></article>`;
  }

  if(!user){
    box.innerHTML='<div class="v2433-server-note"><strong>Connexion requise</strong><br>Reconnectez-vous pour lancer le diagnostic propriétaire.</div>';
  }else if(!isSinjiraOwner(user)){
    box.innerHTML='<div class="v2433-server-note"><strong>Diagnostic propriétaire uniquement</strong><br>Cette page de santé système est réservée au propriétaire SINJIRA™.</div>';
  }else{
    box.innerHTML='<div class="v24-empty">Diagnostic en cours…</div>';
    const tables=['profiles','private_profiles','character_submissions','characters','character_social_profiles','parallel_character_state','fracture_parties','products','user_entitlements','token_ledger','market_listings','privacy_settings','notification_preferences','family_relationships','admin_notifications'];
    const tableRows=await Promise.all(tables.map(tableState));
    const ownerRow=await ownerRepairState();
    const edgeRows=await Promise.all([
      functionState('admin-console',{action:'dashboard'}),
      functionState('admin-reports',{action:'dashboard'})
    ]);
    const rows=[ownerRow,...edgeRows,...tableRows];
    const missingCount=rows.filter(x=>x.state==='missing').length;
    const degradedCount=rows.filter(x=>x.state==='degraded').length;
    const normalCount=rows.filter(x=>x.state==='ok').length;
    box.innerHTML=`<div class="v24-provenance"><div><small>État normal</small><strong>${normalCount}</strong></div><div><small>À synchroniser</small><strong>${missingCount}</strong></div><div><small>Dégradé</small><strong>${degradedCount}</strong></div><div><small>Version interface</small><strong>V24.3.5</strong></div></div><div class="v19-health-grid">${rows.map(card).join('')}</div><p class="v24-feature-note">Ce diagnostic lit seulement l’état des composants essentiels. La vérification AbyssTime appelle la réparation idempotente du compte propriétaire lorsqu’elle est disponible.</p>`;
  }
}
