import {getSupabase,getCurrentUser,escapeHtml,formatDate} from './sinjira-supabase.js';
const page=document.body.dataset.readerPage||'',slug=document.body.dataset.novelSlug||'';
const status=document.querySelector('[data-reader-status]');
function setStatus(msg,type='info'){if(!status)return;status.textContent=msg;status.dataset.statusType=type;status.hidden=false}
async function getNovel(){const {data,error}=await getSupabase().from('novels').select('*').eq('slug',slug).maybeSingle();if(error)throw error;return data}
async function markReading(user,novel){if(!user||!novel)return;await getSupabase().from('reader_library').upsert({user_id:user.id,novel_id:novel.id,last_opened_at:new Date().toISOString()},{onConflict:'user_id,novel_id'})}
async function comments(){
  const s=getSupabase(),novel=await getNovel(),user=await getCurrentUser();
  if(user)await markReading(user,novel);
  const {data=[],error}=await s.from('novel_comments').select('id,body,display_name_snapshot,created_at').eq('novel_id',novel.id).eq('status','approved').order('created_at',{ascending:false}).limit(100);
  if(error)throw error;
  const list=document.querySelector('[data-novel-comments]');
  list.innerHTML=data.length?data.map(c=>`<article class="reader-comment"><header><strong>${escapeHtml(c.display_name_snapshot||'Lecteur SINJIRA')}</strong><time>${escapeHtml(formatDate(c.created_at))}</time></header><p>${escapeHtml(c.body)}</p></article>`).join(''):'<p>Aucun commentaire publié pour le moment.</p>';
  const account=document.querySelector('[data-comment-account]'),form=document.querySelector('[data-comment-form]');
  if(!user){account.innerHTML='<div class="reader-login-note">Connectez-vous à votre Compte SINJIRA pour laisser un commentaire. <a href="../../../compte/connexion.html?next=/projets/sinjira/romans/index.html%23commentaires">Connexion</a></div>';return}
  const {data:p}=await s.from('profiles').select('pseudo,display_name').eq('user_id',user.id).maybeSingle();
  account.innerHTML=`<div class="reader-login-note">Commentaire associé au compte <strong>${escapeHtml(p?.pseudo||p?.display_name||user.email||'SINJIRA')}</strong>. Il sera publié après modération.</div>`;form.hidden=false;
  form.addEventListener('submit',async e=>{e.preventDefault();const body=String(new FormData(form).get('body')||'').trim();if(body.length<3)return setStatus('Le commentaire est trop court.','error');const {error}=await s.from('novel_comments').insert({novel_id:novel.id,user_id:user.id,display_name_snapshot:p?.pseudo||p?.display_name||'Lecteur SINJIRA',body,status:'pending'});if(error)return setStatus(error.message,'error');form.reset();setStatus('Commentaire envoyé. Il apparaîtra après approbation.','success')});
}
(async()=>{try{if(!slug)return;const novel=await getNovel();const user=await getCurrentUser();if(user)await markReading(user,novel);if(page==='novel')await comments()}catch(e){setStatus(e?.message||'Erreur lecteur.','error')}})();