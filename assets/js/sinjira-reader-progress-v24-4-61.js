import {getSupabase,getCurrentUser} from './sinjira-supabase.js';

const slug=document.body.dataset.novelSlug||'';
const page=document.body.dataset.readerPage||'';

async function syncCanonicalPage(user,novel,pageNumber){
  // L'ancien UPSERT contournerait la révision du lecteur intégral.
  // Toutes les sauvegardes canoniques doivent passer par l'écriture CAS V51.
  const s=getSupabase();
  const pageValue=Math.max(1,Number(pageNumber)||1);
  const progress=Math.max(0,Math.min(100,Math.round((pageValue/83)*100)));
  const {data:current,error:readError}=await s.from('sinjira_reader_library')
    .select('revision').eq('user_id',user.id).eq('novel_id',novel.id).maybeSingle();
  if(readError)return false; // V51 absente : ne pas tenter un UPSERT aveugle.
  const expected=current?Number(current.revision):null;
  if(current&&(!Number.isSafeInteger(expected)||expected<0))return false;
  const {data,error}=await s.rpc('sinjira_reader_save_progress_cas',{
    p_novel_id:novel.id,p_expected_revision:expected,
    p_last_page:pageValue,p_progress_percent:progress,p_scroll_ratio:null
  }).single();
  // Conflit (autre appareil) ou RPC absente : ne jamais écraser une ligne.
  return !error&&data?.result_status==='saved';
}

async function initialCanonicalSync(user,canonicalNovel){
  const s=getSupabase();
  const existing=await s.from('sinjira_reader_library').select('novel_id,last_page,progress_percent,revision').eq('user_id',user.id).eq('novel_id',canonicalNovel.id).maybeSingle();
  if(existing.error||existing.data)return;

  let pageValue=1;
  const legacyNovel=await s.from('novels').select('id').eq('slug',slug).maybeSingle();
  if(!legacyNovel.error&&legacyNovel.data?.id){
    const legacyReading=await s.from('reader_library').select('last_page').eq('user_id',user.id).eq('novel_id',legacyNovel.data.id).maybeSingle();
    if(!legacyReading.error&&legacyReading.data?.last_page)pageValue=Number(legacyReading.data.last_page)||1;
  }
  await syncCanonicalPage(user,canonicalNovel,pageValue);
}

async function init(){
  if(page!=='demo'||!slug)return;
  const user=await getCurrentUser();
  if(!user)return;
  const s=getSupabase();
  const {data:novel,error}=await s.from('sinjira_novels').select('id,slug,status').eq('slug',slug).in('status',['announced','published']).maybeSingle();
  if(error||!novel)return;

  const input=document.querySelector('[data-reader-page-number]');
  const bookmark=document.querySelector('[data-reader-bookmark]');
  if(!input)return;

  await initialCanonicalSync(user,novel).catch(()=>{});

  bookmark?.addEventListener('click',()=>{
    syncCanonicalPage(user,novel,input.value).catch(()=>{});
  });
}

init().catch(()=>{});
