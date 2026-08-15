import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';
import { SINJIRA_CONFIG, isSinjiraBackendConfigured } from './sinjira-supabase-config.js';

let client = null;
export function getSupabase() {
  if (!isSinjiraBackendConfigured()) throw new Error('Configuration Supabase requise.');
  if (!client) client = createClient(SINJIRA_CONFIG.supabaseUrl, SINJIRA_CONFIG.supabasePublishableKey, {
    auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}
  });
  return client;
}
export async function getCurrentUser() {
  if (!isSinjiraBackendConfigured()) return null;
  const {data,error}=await getSupabase().auth.getUser();
  return error ? null : (data.user || null);
}
export async function requireUser(redirect='/compte/connexion.html') {
  const user=await getCurrentUser();
  if (!user) {
    const next=encodeURIComponent(location.pathname+location.search+location.hash);
    location.href=`${redirect}?next=${next}`;
    throw new Error('Connexion requise');
  }
  return user;
}

export function isSinjiraOwner(user){return String(user?.email||'').trim().toLowerCase()==='kingtyrano@gmail.com'}
export async function signOut(){ if(isSinjiraBackendConfigured()) await getSupabase().auth.signOut(); location.href='/compte/connexion.html'; }
export function escapeHtml(v=''){return String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;')}
export function formatDate(v){if(!v)return '—';return new Intl.DateTimeFormat('fr-CA',{dateStyle:'medium',timeStyle:'short'}).format(new Date(v))}
export function setStatus(node,msg,type='info'){if(!node)return;node.textContent=msg;node.dataset.statusType=type;node.hidden=false}
export function roleLabel(v){return ({public:'Public',account:'Compte joueur',player:'Joueur approuvé',tester:'Testeur approuvé',admin:'Administration'})[v]||v||'—'}
export function projectStatusLabel(v){return ({draft:'Brouillon',development:'En développement',testing:'En test',active:'Disponible',archived:'Archivé'})[v]||v||'—'}
export { SINJIRA_CONFIG, isSinjiraBackendConfigured };
