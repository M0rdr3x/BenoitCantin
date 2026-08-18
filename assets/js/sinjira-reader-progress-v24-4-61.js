import {getSupabase,getCurrentUser} from './sinjira-supabase.js';

const slug=document.body.dataset.novelSlug||'';
const page=document.body.dataset.readerPage||'';

async function syncCanonicalPage(user,novel,pageNumber){
  const pageValue=Math.max(1,Number(pageNumber)||1);
  const progress=Math.max(0,Math.min(100,Math.round((pageValue/83)*100)));
  await getSupabase().from('sinjira_reader_library').upsert({
    user_id:user.id,
    novel_id:novel.id,
    last_opened_at:new Date().toISOString(),
    last_page:pageValue,
    progress_percent:progress,
    updated_at:new Date().toISOString()
  },{onConflict:'user_id,novel_id'});
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

  await new Promise(resolve=>setTimeout(resolve,250));
  await syncCanonicalPage(user,novel,input.value).catch(()=>{});

  bookmark?.addEventListener('click',()=>{
    syncCanonicalPage(user,novel,input.value).catch(()=>{});
  });
}

init().catch(()=>{});
