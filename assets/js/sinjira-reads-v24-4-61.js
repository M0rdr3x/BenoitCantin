import {getSupabase,requireUser,escapeHtml,setStatus} from './sinjira-supabase.js';

const status=document.querySelector('[data-v18-status]');
const rows=value=>Array.isArray(value)?value:[];

function progressBar(value){
  const progress=Math.max(0,Math.min(100,Number(value||0)));
  return `<div class="v19-progress-track"><span style="width:${progress}%"></span></div>`;
}

async function load(){
  if(document.body.dataset.v18Page!=='reads-v24-4-61')return;
  const user=await requireUser('/compte/connexion.html');
  const s=getSupabase();
  const [novelsResult,libraryResult]=await Promise.all([
    s.from('sinjira_novels').select('id,slug,title,subtitle,description,status,cover_url,public_path,demo_path,sort_order').in('status',['announced','published']).order('sort_order'),
    s.from('sinjira_reader_library').select('novel_id,last_opened_at,last_page,progress_percent,updated_at').eq('user_id',user.id)
  ]);
  if(novelsResult.error)throw novelsResult.error;
  if(libraryResult.error)throw libraryResult.error;

  const novels=rows(novelsResult.data);
  let library=rows(libraryResult.data);
  const box=document.querySelector('[data-reader-library]');
  if(!box)return;

  const render=()=>{
    const map=new Map(library.map(item=>[item.novel_id,item]));
    box.innerHTML=novels.map(novel=>{
      const saved=map.get(novel.id);
      const progress=Math.max(0,Math.min(100,Number(saved?.progress_percent||0)));
      return `<article class="reader-book-card" data-v2461-novel="${novel.id}">
        <span class="eyebrow">${escapeHtml(novel.status==='published'?'Roman disponible':'Roman annoncé')}</span>
        <h2>${escapeHtml(novel.title)}</h2>
        ${novel.subtitle?`<p><strong>${escapeHtml(novel.subtitle)}</strong></p>`:''}
        <p>${escapeHtml(novel.description||'')}</p>
        ${progressBar(progress)}
        <p>${saved?`Dans votre bibliothèque · progression ${progress}%${saved.last_page?` · page ${Number(saved.last_page)}`:''}`:'Pas encore ajouté à votre bibliothèque.'}</p>
        <div class="hero-actions">
          ${novel.demo_path?`<a class="btn btn-primary" href="${escapeHtml(novel.demo_path)}">${saved&&progress>0?'Continuer ma lecture':'Lire la démo'}</a>`:''}
          <a class="btn btn-secondary" href="${escapeHtml(novel.public_path||'/projets/sinjira/romans/')}">Page du roman</a>
          ${saved?`<button class="btn btn-secondary" type="button" data-v2461-remove-read="${novel.id}">Retirer de ma bibliothèque</button>`:`<button class="btn btn-secondary" type="button" data-v2461-add-read="${novel.id}">Ajouter à ma bibliothèque</button>`}
        </div>
      </article>`;
    }).join('')||'<div class="notice"><strong>Aucun roman disponible pour le moment.</strong></div>';

    box.querySelectorAll('[data-v2461-add-read]').forEach(button=>button.addEventListener('click',async()=>{
      const novelId=button.dataset.v2461AddRead;
      button.disabled=true;
      const payload={user_id:user.id,novel_id:novelId,last_page:1,progress_percent:0,last_opened_at:new Date().toISOString(),updated_at:new Date().toISOString()};
      const {error}=await s.from('sinjira_reader_library').upsert(payload,{onConflict:'user_id,novel_id'});
      if(error){button.disabled=false;setStatus(status,'Impossible d’ajouter ce roman à votre bibliothèque.','error');return;}
      library=[...library.filter(item=>item.novel_id!==novelId),payload];
      setStatus(status,'Roman ajouté à votre bibliothèque SINJIRA™.','success');
      render();
    }));

    box.querySelectorAll('[data-v2461-remove-read]').forEach(button=>button.addEventListener('click',async()=>{
      const novelId=button.dataset.v2461RemoveRead;
      if(!confirm('Retirer ce roman de votre bibliothèque? Votre progression enregistrée dans cette bibliothèque sera supprimée.'))return;
      button.disabled=true;
      const {error}=await s.from('sinjira_reader_library').delete().eq('user_id',user.id).eq('novel_id',novelId);
      if(error){button.disabled=false;setStatus(status,'Impossible de retirer ce roman.','error');return;}
      library=library.filter(item=>item.novel_id!==novelId);
      setStatus(status,'Roman retiré de votre bibliothèque.','success');
      render();
    }));
  };

  render();
}

load().catch(error=>{
  if(error?.message!=='Connexion requise')setStatus(status,'Impossible de charger vos lectures pour le moment.','error');
});
