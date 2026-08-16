import {getSupabase,getCurrentUser,isSinjiraOwner,escapeHtml} from './sinjira-supabase.js';

if(!document.querySelector('link[data-v2436-admin-fixes]')){
  const css=document.createElement('link');
  css.rel='stylesheet';
  css.href='/assets/css/v24-3-3-fixes.css?v=24.3.6';
  css.dataset.v2436AdminFixes='';
  document.head.appendChild(css);
}

function technicalSlug(value=''){
  return String(value)
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .toLowerCase().trim()
    .replace(/[^a-z0-9]+/g,'-')
    .replace(/^-+|-+$/g,'')
    .slice(0,80);
}

function configureProjectIdentifierUI(){
  const form=document.querySelector('[data-project-form]');
  if(!form)return;
  const name=form.elements.name;
  const slug=form.elements.slug;
  const id=form.elements.id;
  if(!name||!slug)return;

  const nameField=name.closest('.field');
  const nameLabel=nameField?.querySelector('label');
  if(nameLabel)nameLabel.textContent='Identifiant du projet';
  if(nameField&&!nameField.querySelector('[data-project-identifier-help]')){
    const help=document.createElement('small');
    help.dataset.projectIdentifierHelp='';
    help.className='v24-feature-note';
    help.textContent='Nom officiel visible partout dans SINJIRA™. Exemple : Fracture du Réseau-Mère. L’identifiant technique utilisé par les URL est généré automatiquement et reste caché.';
    nameField.appendChild(help);
  }

  const slugField=slug.closest('.field');
  if(slugField)slugField.hidden=true;
  slug.type='hidden';
  slug.tabIndex=-1;
  slug.setAttribute('aria-hidden','true');

  const normalizeFractureIdentifier=()=>{
    if(String(slug.value||'').trim()==='fracture-du-reseau-mere')name.value='Fracture du Réseau-Mère';
  };
  const ensureTechnicalSlug=()=>{
    if(!String(slug.value||'').trim())slug.value=technicalSlug(name.value);
    normalizeFractureIdentifier();
  };

  name.addEventListener('input',()=>{
    if(!String(id?.value||'').trim())slug.value=technicalSlug(name.value);
  });
  form.addEventListener('submit',ensureTechnicalSlug,true);
  form.addEventListener('reset',()=>window.setTimeout(()=>{slug.value='';},0));
  document.addEventListener('click',(event)=>{
    if(!event.target?.closest?.('[data-edit-project]'))return;
    window.setTimeout(normalizeFractureIdentifier,0);
  },true);

  const list=document.querySelector('[data-admin-project-list]');
  const cleanList=()=>{
    list?.querySelectorAll('.admin-management-row span').forEach((span)=>{
      const parts=String(span.textContent||'').split('·').map(x=>x.trim()).filter(Boolean);
      if(parts.length<3)return;
      const status=({active:'Disponible',development:'En développement',testing:'En test',draft:'Brouillon',archived:'Archivé'})[parts[1]]||parts[1];
      const visibility=({account:'Tous les comptes',public:'Public',restricted:'Accès approuvé'})[parts[2]]||parts[2];
      span.textContent=`${status} · ${visibility}`;
    });
  };
  if(list){
    cleanList();
    new MutationObserver(cleanList).observe(list,{childList:true,subtree:true});
  }
}

configureProjectIdentifierUI();

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
    if(missing(error))return {name:table,state:'missing',detail:'Table absente de Supabase production'};
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

  async function rpcState(name,args={},detail='RPC disponible'){
    const {data,error}=await s.rpc(name,args);
    if(!error)return {name:`RPC: ${name}`,state:'ok',detail,raw:data};
    if(missing(error))return {name:`RPC: ${name}`,state:'missing',detail:'Fonction absente de Supabase production'};
    if(restricted(error))return {name:`RPC: ${name}`,state:'restricted',detail:'Fonction présente, accès refusé à ce compte'};
    console.warn('[SINJIRA admin health rpc]',name,error);
    return {name:`RPC: ${name}`,state:'degraded',detail:'Fonction présente mais réponse inattendue'};
  }

  async function serverVersionState(){
    const row=await rpcState('get_sinjira_server_version',{},'Version serveur détectée');
    if(row.state!=='ok')return {...row,name:'Version Supabase SINJIRA™'};
    const value=String(row.raw||'');
    return {name:'Version Supabase SINJIRA™',state:value.startsWith('24.3.6')?'ok':'missing',detail:value?`Serveur ${value}`:'Version serveur non retournée'};
  }

  async function ownerRepairState(){
    if(!isSinjiraOwner(user))return {name:'AbyssTime / propriétaire',state:'restricted',detail:'Compte propriétaire requis'};
    const {data,error}=await s.rpc('ensure_sinjira_owner_character');
    if(!error&&data?.ok)return {name:'AbyssTime / propriétaire',state:'ok',detail:'Personnage, accès total et synchronisation propriétaire disponibles'};
    if(missing(error))return {name:'AbyssTime / propriétaire',state:'missing',detail:'Réparation propriétaire V24.3.1 absente de Supabase'};
    console.warn('[SINJIRA admin health owner]',error||data);
    return {name:'AbyssTime / propriétaire',state:'degraded',detail:'RPC présente mais réparation incomplète'};
  }

  async function fractureAccessState(){
    const {data,error}=await s.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'});
    if(!error&&data===true)return {name:'Fracture du Réseau-Mère / accès',state:'ok',detail:'Droit serveur confirmé pour ce compte'};
    if(!error)return {name:'Fracture du Réseau-Mère / accès',state:'restricted',detail:'Serveur disponible, mais aucun droit Fracture pour ce compte'};
    if(missing(error))return {name:'Fracture du Réseau-Mère / accès',state:'missing',detail:'Contrôle de licence V24.1 absent de Supabase'};
    console.warn('[SINJIRA admin health fracture]',error);
    return {name:'Fracture du Réseau-Mère / accès',state:'degraded',detail:'Contrôle de licence en erreur'};
  }

  function card(row){
    return `<article class="v19-health-card"><div><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(row.detail)}</span></div><span class="v24-badge ${cls[row.state]||'staged'}">${escapeHtml(label[row.state]||row.state)}</span></article>`;
  }

  if(!user){
    box.innerHTML='<div class="v2433-server-note"><strong>Connexion requise</strong><br>Reconnectez-vous pour lancer le diagnostic propriétaire.</div>';
  }else if(!isSinjiraOwner(user)){
    box.innerHTML='<div class="v2433-server-note"><strong>Diagnostic propriétaire uniquement</strong><br>Cette page de santé système est réservée au propriétaire SINJIRA™.</div>';
  }else{
    box.innerHTML='<div class="v24-empty">Diagnostic complet de Supabase production en cours…</div>';
    const tables=[
      'profiles','private_profiles','privacy_settings','notification_preferences','family_relationships',
      'character_submissions','characters','character_social_profiles','parallel_character_state',
      'fracture_parties','fracture_party_members','fracture_player_documents','fracture_endgame_reports','game_sessions',
      'products','user_entitlements','reader_library','token_ledger','market_listings','admin_notifications'
    ];
    const tableRows=await Promise.all(tables.map(tableState));
    const [versionRow,ownerRow,fractureRow,capabilitiesRow]=await Promise.all([
      serverVersionState(),
      ownerRepairState(),
      fractureAccessState(),
      rpcState('get_sinjira_account_capabilities',{},'Capacités du compte disponibles')
    ]);
    const edgeRows=await Promise.all([
      functionState('admin-console',{action:'dashboard'}),
      functionState('admin-reports',{action:'dashboard'})
    ]);
    const rows=[versionRow,ownerRow,fractureRow,capabilitiesRow,...edgeRows,...tableRows];
    const missingCount=rows.filter(x=>x.state==='missing').length;
    const degradedCount=rows.filter(x=>x.state==='degraded').length;
    const restrictedCount=rows.filter(x=>x.state==='restricted').length;
    const normalCount=rows.filter(x=>x.state==='ok').length;
    const syncHelp=(missingCount||degradedCount)?`<div class="v2433-server-note" style="margin:18px 0"><strong>Synchronisation Supabase production requise</strong><br>Appliquer dans l’ordre : <code>20260814_sinjira_v24_foundation.sql</code> → <code>20260815_sinjira_v24_1_owner_and_live_fixes.sql</code> → <code>20260815_sinjira_v24_3_1_owner_repair_and_fracture_access.sql</code> → <code>20260815_sinjira_v24_3_6_server_marker_and_project_identity.sql</code>.<div class="hero-actions" style="margin-top:12px"><a class="btn btn-secondary btn-small" href="https://supabase.com/dashboard/project/gpvivleexywljowcqkru/sql/new" target="_blank" rel="noopener">Ouvrir SQL Editor Supabase</a></div></div>`:'<div class="v24-callout" style="margin:18px 0"><strong>Supabase production est synchronisé.</strong> Les composants essentiels contrôlés par V24.3.6 répondent correctement.</div>';
    box.innerHTML=`<div class="v24-provenance"><div><small>État normal</small><strong>${normalCount}</strong></div><div><small>À synchroniser</small><strong>${missingCount}</strong></div><div><small>Dégradé</small><strong>${degradedCount}</strong></div><div><small>Restreint</small><strong>${restrictedCount}</strong></div><div><small>Version interface</small><strong>V24.3.6</strong></div></div>${syncHelp}<div class="v19-health-grid">${rows.map(card).join('')}</div><p class="v24-feature-note">Ce diagnostic ne lit pas le contenu privé des messages ni les données de paiement. La vérification AbyssTime appelle uniquement la réparation idempotente du compte propriétaire lorsqu’elle est disponible.</p>`;
  }
}
