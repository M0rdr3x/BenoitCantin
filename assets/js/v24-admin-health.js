import {getSupabase,getCurrentUser,isSinjiraOwner,escapeHtml} from './sinjira-supabase.js';

const PLATFORM_VERSION='24.4.13';
const FRACTURE_ENGINE_VERSION='24.4.6';

if(!document.querySelector('link[data-v244-admin-fixes]')){
  const css=document.createElement('link');css.rel='stylesheet';css.href=`/assets/css/v24-3-3-fixes.css?v=${PLATFORM_VERSION}`;css.dataset.v244AdminFixes='';document.head.appendChild(css);
}

function technicalSlug(value=''){return String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,80)}
function configureProjectIdentifierUI(){
  const form=document.querySelector('[data-project-form]');if(!form)return;
  const name=form.elements.name,slug=form.elements.slug,id=form.elements.id;if(!name||!slug)return;
  const field=name.closest('.field'),label=field?.querySelector('label');if(label)label.textContent='Identifiant du projet';
  if(field&&!field.querySelector('[data-project-identifier-help]')){const help=document.createElement('small');help.dataset.projectIdentifierHelp='';help.className='v24-feature-note';help.textContent='Nom officiel visible. La clé technique URL est générée automatiquement et reste cachée.';field.appendChild(help)}
  const slugField=slug.closest('.field');if(slugField)slugField.hidden=true;slug.type='hidden';slug.tabIndex=-1;slug.setAttribute('aria-hidden','true');
  const normalize=()=>{if(String(slug.value||'').trim()==='fracture-du-reseau-mere')name.value='Fracture du Réseau-Mère'};
  const ensure=()=>{if(!String(slug.value||'').trim())slug.value=technicalSlug(name.value);normalize()};
  name.addEventListener('input',()=>{if(!String(id?.value||'').trim())slug.value=technicalSlug(name.value)});form.addEventListener('submit',ensure,true);document.addEventListener('click',e=>{if(e.target?.closest?.('[data-edit-project]'))setTimeout(normalize,0)},true);
}
configureProjectIdentifierUI();

const box=document.querySelector('[data-admin-health]');
if(box){
  const s=getSupabase(),user=await getCurrentUser();
  const labels={ok:'NORMAL',missing:'À SYNCHRONISER',restricted:'PROTÉGÉ',degraded:'DÉGRADÉ'},classes={ok:'live',missing:'staged',restricted:'live',degraded:'staged'};
  const isMissing=e=>['PGRST205','PGRST202'].includes(String(e?.code||''))||/does not exist|schema cache|Could not find/i.test(String(e?.message||''));
  const isRestricted=e=>String(e?.code||'')==='42501'||/permission denied|row-level security|not allowed/i.test(String(e?.message||''));
  async function tableState(table){const {count,error}=await s.from(table).select('*',{head:true,count:'exact'}).limit(1);if(!error)return{name:table,state:'ok',detail:`${Number(count||0).toLocaleString('fr-CA')} ligne(s)`};if(isMissing(error))return{name:table,state:'missing',detail:'Table absente de la production'};if(isRestricted(error))return{name:table,state:'restricted',detail:'Table présente, lecture directe volontairement bloquée'};return{name:table,state:'degraded',detail:'Réponse serveur inattendue'}}
  async function rpcState(name,args={},detail='RPC disponible'){const {data,error}=await s.rpc(name,args);if(!error)return{name:`RPC: ${name}`,state:'ok',detail,raw:data};if(isMissing(error))return{name:`RPC: ${name}`,state:'missing',detail:'RPC absent de la production'};if(isRestricted(error))return{name:`RPC: ${name}`,state:'restricted',detail:'RPC présent avec accès limité'};return{name:`RPC: ${name}`,state:'degraded',detail:'RPC en erreur'}}
  async function edgeState(name,body){const {data,error}=await s.functions.invoke(name,{body});if(!error&&data?.ok!==false)return{name:`Edge: ${name}`,state:'ok',detail:`Joignable${data?.version?` · ${data.version}`:''}`};if(error&&/Failed|404|not found|FunctionsFetchError/i.test(`${error?.name||''} ${error?.message||''}`))return{name:`Edge: ${name}`,state:'missing',detail:'Non déployée ou non joignable'};return{name:`Edge: ${name}`,state:'degraded',detail:'Réponse incomplète'}}
  async function versionState(){const row=await rpcState('get_sinjira_server_version');if(row.state!=='ok')return{...row,name:'Version Supabase SINJIRA™'};const value=String(row.raw||'');return{name:'Version Supabase SINJIRA™',state:value===PLATFORM_VERSION?'ok':'missing',detail:`Serveur ${value||'inconnu'} · attendu ${PLATFORM_VERSION}`}}
  async function runtimeState(){const row=await rpcState('get_sinjira_runtime_health');if(row.state!=='ok')return{...row,name:'Fondation SINJIRA™'};const parts=row.raw?.components||{},absent=Object.entries(parts).filter(([,ok])=>ok!==true).map(([name])=>name);const healthy=row.raw?.ok===true&&row.raw?.platform_version===PLATFORM_VERSION&&!absent.length;return{name:'Fondation SINJIRA™',state:healthy?'ok':'missing',detail:healthy?`Runtime confirmé · plateforme ${PLATFORM_VERSION}`:`Fondation incomplète${absent.length?` : ${absent.join(', ')}`:''}`}}
  async function ownerState(){if(!isSinjiraOwner(user))return{name:'AbyssTime / propriétaire',state:'restricted',detail:'Compte propriétaire requis'};const {data,error}=await s.rpc('ensure_sinjira_owner_character');return !error&&data?.ok?{name:'AbyssTime / propriétaire',state:'ok',detail:'Personnage et accès propriétaire synchronisés'}:isMissing(error)?{name:'AbyssTime / propriétaire',state:'missing',detail:'RPC propriétaire absent'}:{name:'AbyssTime / propriétaire',state:'degraded',detail:'Réparation propriétaire incomplète'}}
  async function fractureAccess(){const {data,error}=await s.rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'});if(!error&&data===true)return{name:'Fracture / droit d’accès',state:'ok',detail:'Entitlement serveur confirmé'};if(!error)return{name:'Fracture / droit d’accès',state:'restricted',detail:'Droit Fracture absent pour ce compte'};return{name:'Fracture / droit d’accès',state:isMissing(error)?'missing':'degraded',detail:'Contrôle de licence indisponible'}}
  async function engineHealth(){const row=await rpcState('fracture_engine_health');if(row.state!=='ok')return{...row,name:`Moteur Fracture V${FRACTURE_ENGINE_VERSION}`};const tables=row.raw?.tables||{},funcs=row.raw?.functions||{},missing=[...Object.entries(tables).filter(([,ok])=>ok!==true).map(([n])=>`table:${n}`),...Object.entries(funcs).filter(([,ok])=>ok!==true).map(([n])=>`rpc:${n}`)];const healthy=row.raw?.ok===true&&row.raw?.engine_version===FRACTURE_ENGINE_VERSION&&!missing.length;return{name:`Moteur Fracture V${FRACTURE_ENGINE_VERSION}`,state:healthy?'ok':'missing',detail:healthy?'Moteur autoritaire et composants critiques confirmés':`Moteur incomplet${missing.length?` : ${missing.join(', ')}`:''}`}}
  const card=row=>`<article class="v19-health-card"><div><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(row.detail)}</span></div><span class="v24-badge ${classes[row.state]||'staged'}">${escapeHtml(labels[row.state]||row.state)}</span></article>`;

  if(!user)box.innerHTML='<div class="v2433-server-note"><strong>Connexion requise</strong><br>Reconnectez-vous pour lancer le diagnostic propriétaire.</div>';
  else if(!isSinjiraOwner(user))box.innerHTML='<div class="v2433-server-note"><strong>Diagnostic propriétaire uniquement</strong><br>Cette page est réservée au propriétaire SINJIRA™.</div>';
  else{
    box.innerHTML='<div class="v24-empty">Diagnostic direct de Supabase production en cours…</div>';
    const tables=['profiles','account_safety_profiles','guardian_links','character_submissions','characters','character_social_profiles','parallel_character_state','fracture_parties','fracture_party_members','fracture_player_documents','fracture_endgame_reports','game_sessions','products','user_entitlements','reader_library','admin_notifications'];
    const tableRows=await Promise.all(tables.map(tableState));
    const [version,runtime,owner,fracture,capabilities,engine]=await Promise.all([versionState(),runtimeState(),ownerState(),fractureAccess(),rpcState('get_sinjira_account_capabilities',{},'Capacités du compte disponibles'),engineHealth()]);
    const edges=await Promise.all([edgeState('submit-character-questionnaire',{health:true}),edgeState('admin-console',{action:'dashboard'}),edgeState('admin-reports',{action:'dashboard'}),edgeState('redeem-license-code',{action:'health'})]);
    const rows=[version,runtime,owner,fracture,capabilities,engine,...edges,...tableRows],counts={ok:0,missing:0,degraded:0,restricted:0};rows.forEach(r=>counts[r.state]=(counts[r.state]||0)+1);
    const problems=(counts.missing||0)+(counts.degraded||0);
    const summary=problems?`<div class="v2433-server-note" style="margin:18px 0"><strong>Production partiellement synchronisée</strong><br>La plateforme ${PLATFORM_VERSION} répond, mais ${problems} composant(s) restent à corriger ou déployer. Un workflow GitHub vert sur simple push ne constitue pas un déploiement Supabase.</div>`:`<div class="v24-callout" style="margin:18px 0"><strong>Supabase production est synchronisé.</strong> Plateforme ${PLATFORM_VERSION} et moteur Fracture ${FRACTURE_ENGINE_VERSION} répondent. Les éléments PROTÉGÉ sont volontairement restreints.</div>`;
    box.innerHTML=`<div class="v24-provenance"><div><small>Normal</small><strong>${counts.ok}</strong></div><div><small>À synchroniser</small><strong>${counts.missing}</strong></div><div><small>Dégradé</small><strong>${counts.degraded}</strong></div><div><small>Protégé</small><strong>${counts.restricted}</strong></div><div><small>Interface</small><strong>V${PLATFORM_VERSION}</strong></div></div>${summary}<div class="v19-health-grid">${rows.map(card).join('')}</div><p class="v24-feature-note">Ce diagnostic ne lit aucune carte secrète, identité adverse, soupçon privé, message privé ni donnée de paiement.</p>`;
  }
}
