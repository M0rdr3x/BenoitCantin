import {getSupabase,requireUser,setStatus} from './sinjira-supabase.js';

const form=document.querySelector('[data-admin-license-form]');
const status=document.querySelector('[data-admin-license-status]');
const out=document.querySelector('[data-admin-license-output]');
const download=document.querySelector('[data-admin-license-download]');
const next=document.querySelector('[data-admin-license-next]');
const note=document.querySelector('[data-admin-license-export-note]');
let last='',ready=false,busy=false,uncertain=false;

function sync(){
  const disabled=!ready||busy||uncertain||Boolean(last);
  for(const control of form.querySelectorAll('input,button[type="submit"]'))control.disabled=disabled;
  form.setAttribute('aria-busy',String(busy));
  download.disabled=!last||busy;
  next.hidden=!last;
  next.disabled=!last||busy||uncertain;
  note.hidden=!last;
}

function validResult(result,body){
  if(result?.error!==null||result.data?.ok!==true)return false;
  const {batch,codes}=result.data;
  const prefix='SJR-'+(body.product_slug.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,6)||'PROD');
  return batch?.batch_code===body.batch_code.toUpperCase()&&
    Array.isArray(codes)&&codes.length===body.quantity&&new Set(codes).size===codes.length&&
    codes.every(code=>typeof code==='string'&&code.startsWith(prefix+'-')&&
      /^[A-HJ-NP-Z2-9]{5}(?:-[A-HJ-NP-Z2-9]{5}){2}$/.test(code.slice(prefix.length+1)));
}

if(form&&status&&out&&download&&next&&note){
  sync();
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    if(!ready||busy||uncertain||last)return;
    const fields=new FormData(form);
    const body={
      product_slug:String(fields.get('product_slug')||'').trim(),
      batch_code:String(fields.get('batch_code')||'').trim(),
      quantity:Number(fields.get('quantity')||0)
    };
    if(!body.product_slug||!body.batch_code||!Number.isInteger(body.quantity)||body.quantity<1||body.quantity>5000){
      setStatus(status,'Indiquez un produit, un code de lot et une quantité entière de 1 à 5 000.','error');
      return;
    }
    busy=true;sync();
    setStatus(status,'Génération en cours. Ne fermez pas cette page.','info');
    try{
      const result=await getSupabase().functions.invoke('admin-license-codes',{body});
      if(!validResult(result,body))throw new Error('LOT_NON_CONFIRME');
      const {batch,codes}=result.data;
      last=[`# SINJIRA™ — ${batch.batch_code}`,`# Produit: ${body.product_slug}`,`# Quantité: ${codes.length}`,`# Généré: ${new Date().toISOString()}`,'',...codes].join('\n');
      out.value=last;
      setStatus(status,'Lot généré. Conservez cet export maintenant : les codes bruts ne sont pas récupérables depuis la base.','success');
    }catch{
      uncertain=true;
      setStatus(status,'Génération non confirmée. Vérifiez l’existence du lot dans l’administration avant toute nouvelle tentative. Ne générez pas de doublon.','error');
    }finally{busy=false;sync();if(last)download.focus({preventScroll:true})}
  });
  download.addEventListener('click',()=>{
    if(!last||busy)return;
    let url;
    try{
      url=URL.createObjectURL(new Blob([last],{type:'text/plain;charset=utf-8'}));
      const a=document.createElement('a');a.href=url;a.download='sinjira-codes-activation.txt';a.click();
      setStatus(status,'Téléchargement demandé. Vérifiez que le fichier a bien été conservé avant de préparer un autre lot.','info');
    }catch{
      setStatus(status,'Téléchargement indisponible. L’export reste accessible dans le champ ci-dessous.','error');
    }finally{if(url)setTimeout(()=>URL.revokeObjectURL(url),1000)}
  });
  next.addEventListener('click',()=>{
    if(!last||busy||uncertain)return;
    if(!window.confirm('Confirmez-vous avoir conservé tous les codes dans un endroit sécurisé ? L’export affiché sera effacé.'))return;
    last='';out.value='';form.elements.batch_code.value='';
    sync();form.elements.batch_code.focus();
    setStatus(status,'Vous pouvez préparer un nouveau lot.','info');
  });
  window.addEventListener('beforeunload',event=>{
    if(busy||last){event.preventDefault();event.returnValue='';}
  });
  try{await requireUser();ready=true;sync()}
  catch{setStatus(status,'Session non confirmée. Reconnectez-vous avant de générer un lot.','error')}
}
