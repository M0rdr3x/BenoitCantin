import {getSupabase,requireUser,setStatus,escapeHtml} from './sinjira-supabase.js';

const form=document.querySelector('[data-relation-form]');
const status=document.querySelector('[data-relation-status]');
const list=document.querySelector('[data-relations-list]');

function serverMissing(error){
  const code=String(error?.code||'');
  const text=String(error?.message||'');
  return code==='PGRST205'||/family_relationships|relation .* does not exist|schema cache/i.test(text);
}
function setFormReady(ready){
  for(const el of form.elements){if(el.type==='submit'||el.tagName==='BUTTON')el.disabled=!ready}
}

if(form&&list){
  const user=await requireUser();
  const s=getSupabase();
  let ready=true;

  async function render(){
    const {data,error}=await s.from('family_relationships').select('*').eq('owner_user_id',user.id).order('created_at',{ascending:true});
    if(error){
      ready=!serverMissing(error);
      setFormReady(ready);
      list.innerHTML=serverMissing(error)?'<div class="v2433-server-note"><strong>Relations privées en préparation</strong><br>Le serveur SINJIRA™ doit encore être synchronisé avant de pouvoir enregistrer cette section. Rien n’est rendu public pendant cette attente.</div>':'<div class="v24-empty">Impossible de charger vos relations privées pour le moment.</div>';
      return;
    }
    ready=true;setFormReady(true);
    const rows=Array.isArray(data)?data:[];
    list.innerHTML=rows.length?rows.map(x=>`<article class="v24-panel"><strong>${escapeHtml(x.relationship_type)}</strong><p>${escapeHtml(x.relative_name)}</p>${x.since_date?`<small>Depuis ${escapeHtml(x.since_date)}</small>`:''}<div class="hero-actions"><button class="btn btn-secondary btn-small" type="button" data-delete-relation="${x.id}">Retirer</button></div></article>`).join(''):'<div class="v24-empty">Aucune relation enregistrée.</div>';
    list.querySelectorAll('[data-delete-relation]').forEach(b=>b.addEventListener('click',async()=>{
      if(!confirm('Retirer cette relation de votre profil privé?'))return;
      const {error}=await s.from('family_relationships').delete().eq('id',b.dataset.deleteRelation).eq('owner_user_id',user.id);
      if(error){setStatus(status,'Impossible de retirer cette relation pour le moment.','error');return}
      await render();
    }));
  }

  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(!ready){setStatus(status,'Enregistrement temporairement indisponible tant que le serveur n’est pas synchronisé.','info');return}
    const d=new FormData(form);
    const relativeName=String(d.get('relative_name')||'').trim();
    const relationshipType=String(d.get('relationship_type')||'').trim();
    if(!relationshipType||!relativeName){setStatus(status,'Choisissez le type de relation et indiquez un nom ou un pseudo.','error');return}
    const payload={owner_user_id:user.id,relationship_type:relationshipType,relative_name:relativeName,since_date:d.get('since_date')||null,until_date:d.get('until_date')||null,private_note:String(d.get('private_note')||'').trim()||null,status:'private_record'};
    const {error}=await s.from('family_relationships').insert(payload);
    if(error){
      if(serverMissing(error)){ready=false;setFormReady(false);setStatus(status,'Le serveur des relations privées doit encore être synchronisé.','info');return}
      setStatus(status,'Impossible d’ajouter cette relation pour le moment.','error');return;
    }
    form.reset();setStatus(status,'Relation ajoutée dans votre espace privé.','success');await render();
  });
  await render();
}
