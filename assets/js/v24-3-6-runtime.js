import {getSupabase,getCurrentUser,isSinjiraOwner,escapeHtml} from './sinjira-supabase.js';

const path=location.pathname.replace(/\/+$/,'')||'/';
function setFormsEnabled(enabled){document.querySelectorAll('[data-create-party],[data-join-party]').forEach(form=>form.querySelectorAll('input,select,button').forEach(control=>{control.disabled=!enabled}))}
function accessHost(){return document.querySelector('[data-fracture-access-status]')}
function setAccess(html,type='info'){const host=accessHost();if(!host)return;host.innerHTML=html;host.hidden=false;host.dataset.statusType=type;host.dataset.type=type}
function isMissing(error){const code=String(error?.code||'');const text=String(error?.message||'');return code==='PGRST202'||code==='PGRST205'||/Could not find the function|schema cache|does not exist/i.test(text)}
async function serverVersion(){const {data,error}=await getSupabase().rpc('get_sinjira_server_version');if(error)throw error;return String(data||'')}
async function verifyFractureProduction(){
  if(!path.startsWith('/projets/sinjira/jeux/fracture-du-reseau-mere'))return;
  const mode=document.querySelector('[data-v2431-fracture-mode] strong');if(mode)mode.textContent='Mode Web V24.4 — moteur numérique complet';
  const isLobby=/\/jouer(?:\.html)?$/.test(path);if(!isLobby)return;
  let ready=false;setFormsEnabled(false);setAccess('<strong>Vérification du moteur Fracture…</strong> Contrôle de Supabase V24.4 et de votre droit d’accès.');
  document.addEventListener('submit',event=>{if(!event.target?.matches?.('[data-create-party],[data-join-party]')||ready)return;event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();setAccess('<strong>Fracture Online n’est pas encore synchronisé.</strong> Le moteur serveur V24.4 doit être déployé avant de créer ou rejoindre une partie.','error')},true);
  const keepLocked=setInterval(()=>{if(!ready)setFormsEnabled(false)},250);
  try{
    const user=await getCurrentUser();if(!user){setAccess('<strong>Connexion requise.</strong> Connectez-vous à votre Compte SINJIRA™ pour vérifier votre accès Fracture.','info');return}
    let version='';try{version=await serverVersion()}catch(error){if(isMissing(error)){setAccess('<strong>Supabase production doit être synchronisé.</strong> Le moteur serveur V24.4 est absent.','error');return}throw error}
    if(!version.startsWith('24.4.')){setAccess(`<strong>Version serveur trop ancienne.</strong> Interface V24.4, serveur ${escapeHtml(version||'inconnu')}. Ouvrez <a href="/admin/sinjira/index.html">Administration → État du système</a>.`,'error');return}
    if(isSinjiraOwner(user)){const {data,error}=await getSupabase().rpc('ensure_sinjira_owner_character');if(error||!data?.ok){setAccess('<strong>AbyssTime est reconnu, mais la réparation propriétaire n’est pas complète côté serveur.</strong> Ouvrez <a href="/admin/sinjira/index.html">État du système</a>.','error');return}ready=true;setFormsEnabled(true);setAccess('<strong>Accès propriétaire AbyssTime — moteur V24.4 synchronisé.</strong> Vous pouvez créer une partie 100 % numérique.','success');return}
    const {data:allowed,error}=await getSupabase().rpc('has_sinjira_product',{p_product_slug:'fracture-du-reseau-mere'});if(error)throw error;if(allowed!==true){setAccess('<strong>Accès Fracture requis.</strong> Activez une licence physique ou numérique dans <a href="/compte/licences.html">Mes licences</a>.','info');return}
    ready=true;setFormsEnabled(true);setAccess('<strong>Accès Fracture vérifié — moteur V24.4 prêt.</strong> Vous pouvez créer ou rejoindre une partie 100 % numérique.','success');
  }catch(error){console.warn('[SINJIRA V24.4 Fracture]',error);setAccess('<strong>Fracture Online est temporairement indisponible.</strong> Vérifiez <a href="/admin/sinjira/index.html">État du système</a>.','error')}
  finally{clearInterval(keepLocked);if(!ready)setFormsEnabled(false)}
}
const start=()=>verifyFractureProduction();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
