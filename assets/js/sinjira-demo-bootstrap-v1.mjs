/**
 * SINJIRA — démarrage autonome de la démo publique.
 * L'interface PDF fonctionne avant tout import du client Supabase externe.
 * La synchronisation du compte n'est qu'un enrichissement facultatif.
 */
import {startDemoNavigation} from './sinjira-demo-navigation-v1.mjs';

const frame=document.querySelector('[data-pdf-reader]');
const slug=document.body.dataset.novelSlug||'';
const configuredPages=Number(document.body.dataset.readerTotalPages||82);
const totalPages=Number.isSafeInteger(configuredPages)&&configuredPages>0?configuredPages:82;

if(frame&&slug){
  let account=null;
  let legacyNovel=null;
  let supabase=null;
  const reader=startDemoNavigation({
    document,frame,slug,totalPages,
    onBookmark:async pageNumber=>{
      if(!account||!legacyNovel||!supabase)return false;
      const safePage=Math.max(1,Math.min(totalPages,pageNumber));
      const {error}=await supabase.from('reader_library').upsert({
        user_id:account.id,
        novel_id:legacyNovel.id,
        last_opened_at:new Date().toISOString(),
        last_page:safePage,
        progress_percent:Math.round(safePage/totalPages*100)
      },{onConflict:'user_id,novel_id'});
      if(error)throw error;
      return true;
    }
  });

  async function optionalAccountSync(){
    try{
      // Import dynamique : si le CDN échoue, le lecteur local reste opérationnel.
      const {getCurrentUser,getSupabase}=await import('./sinjira-supabase.js');
      const user=await getCurrentUser();
      if(!user)return;
      const s=getSupabase();
      const {data:novel,error:novelError}=await s.from('novels')
        .select('id').eq('slug',slug).maybeSingle();
      if(novelError||!novel)return;
      account=user;
      legacyNovel=novel;
      supabase=s;
      const {data, error}=await s.from('reader_library')
        .select('last_page').eq('user_id',user.id).eq('novel_id',novel.id)
        .maybeSingle();
      if(!error&&data?.last_page)reader.restoreRemotePage(data.last_page);
    }catch(_){
      // La panne d'authentification, du réseau ou du CDN reste non bloquante.
    }
  }

  optionalAccountSync();
}
