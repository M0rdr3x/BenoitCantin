import { getSupabase, getCurrentUser, requireUser } from './sinjira-supabase.js';

/* SINJIRA 2026 — liseuse : le PDF intégral n'entre jamais dans le dépôt public
   ni dans localStorage. Le serveur attribue le droit de lecture avant de signer l'accès. */
const DEMO_URL='/projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf';
const SIGNED_ORIGIN='https://gpvivleexywljowcqkru.supabase.co';
const PDFJS='https://cdn.jsdelivr.net/npm/pdfjs-dist@4.9.155/build/pdf.min.mjs';
const PDF_WORKER='https://cdn.jsdelivr.net/npm/pdfjs-dist@4.9.155/build/pdf.worker.min.mjs';
const NOVEL_SLUG='la-cendre-du-jugement';
const edition=new URLSearchParams(location.search).get('edition')==='integrale'?'integrale':'demo';
const isFull=edition==='integrale';
const chaptersFull=[
  [1,'Couverture et mentions légales'],[3,'Table des matières'],[4,'Prologue'],
  [26,'Chapitre 1 — Le matin qui hésite'],[42,'Chapitre 2 — Les choses normales'],
  [62,'Chapitre 3 — Une erreur qui regarde'],[82,'Chapitre 4 — Le premier refuge'],
  [116,'Chapitre 5 — Les voix sans visage'],[131,'Chapitre 6 — Le pont qui ment'],
  [145,'Chapitre 7 — Sofia coupe le fil'],[159,'Chapitre 8 — La carte de papier'],
  [173,'Chapitre 9 — Le nom de Jonas'],[189,'Chapitre 10 — Vortek observe'],
  [210,'Chapitre 11 — Le pacte de silence'],[225,'Chapitre 12 — Sous les rails fondus'],
  [240,'Chapitre 13 — Le convoi des enfants'],[263,'Chapitre 14 — La voix conservée'],
  [278,'Chapitre 15 — L’homme qui refuse de fuir'],[295,'Chapitre 16 — Ligne rouge'],
  [310,'Chapitre 17 — Hydres mécaniques'],[327,'Chapitre 18 — La pluie de métal'],
  [342,'Chapitre 19 — Les vivants se comptent'],[359,'Chapitre 20 — Le relais Écho'],
  [376,'Chapitre 21 — La ville sans nuit'],[395,'Chapitre 22 — Un mensonge utile'],
  [412,'Chapitre 23 — Le fleuve sous la cendre'],[430,'Chapitre 24 — Les mains invisibles'],
  [448,'Chapitre 25 — Ronan dans la fumée'],[465,'Chapitre 26 — La faille du nord'],
  [481,'Chapitre 27 — La question de Sofia'],[503,'Chapitre 28 — Ce que le système apprend'],
  [506,'Chapitre 29 — Les morts sans tombe'],[512,'Chapitre 30 — Le choix de Cade'],
  [518,'Épilogue — La première loi']
];
const chaptersDemo=[
  [1,'Couverture et mentions légales'],[3,'Prologue'],
  [25,'Chapitre 1 — Le matin qui hésite'],[41,'Chapitre 2 — Les choses normales'],
  [61,'Chapitre 3 — Une erreur qui regarde']
];
const $=id=>document.getElementById(id);
const state={pdf:null,page:1,mode:'page',theme:'sepia',size:20,zoom:1,
  user:null,novelId:null,renderVersion:0,renderQueue:Promise.resolve(),saveTimer:null};
const storageKey='sinjira:liseuse:'+edition+':la-cendre-du-jugement';
const themeKey='sinjira:liseuse:preferences';

function safeLocalGet(key){try{return localStorage.getItem(key)}catch{return null}}
function safeLocalSet(key,value){try{localStorage.setItem(key,value)}catch{/* navigation privée */}}
function clamp(value,min,max){return Math.max(min,Math.min(max,Number(value)||min))}
function message(value,type='info'){
  const node=$('reader-status');
  node.textContent=value;node.dataset.type=type;node.hidden=false;
}
function savePreferences(){
  safeLocalSet(themeKey,JSON.stringify({theme:state.theme,size:state.size,zoom:state.zoom,mode:state.mode}));
}
function loadPreferences(){
  try{
    const prefs=JSON.parse(safeLocalGet(themeKey)||'{}');
    if(['clair','sepia','nuit'].includes(prefs.theme))state.theme=prefs.theme;
    if(['texte','page'].includes(prefs.mode))state.mode=prefs.mode;
    state.size=clamp(prefs.size||20,16,32);
    state.zoom=clamp(prefs.zoom||1,.8,1.5);
  }catch{/* valeurs par défaut */}
}
function setTheme(){
  document.body.dataset.readTheme=state.theme;
  $('reader-theme').value=state.theme;
  $('reader-size').value=String(state.size);
  $('reader-zoom').value=String(state.zoom);
  document.body.style.setProperty('--reader-text-size',state.size+'px');
  $('reader-mode').textContent=state.mode==='texte'?'Mode pages':'Mode texte';
  savePreferences();
}
function currentChapter(){
  const chapters=isFull?chaptersFull:chaptersDemo;
  return [...chapters].reverse().find(chapter=>chapter[0]<=state.page)||chapters[0];
}
function updateToolbar(){
  if(!state.pdf)return;
  const max=state.pdf.numPages,percentage=Math.round(state.page/max*100);
  $('reader-page').value=String(state.page);
  $('reader-page').max=String(max);
  $('reader-range').max=String(max);
  $('reader-range').value=String(state.page);
  $('reader-total').textContent=String(max);
  $('reader-percent').textContent=percentage+' %';
  $('reader-bar').style.width=percentage+'%';
  $('reader-previous').disabled=state.page<=1;
  $('reader-next').disabled=state.page>=max;
  const chapter=currentChapter();
  $('reader-chapter-label').textContent=chapter[1];
  $('reader-chapters').value=String(chapter[0]);
}
function persist(){
  safeLocalSet(storageKey,String(state.page));
  if(!isFull||!state.user||!state.novelId)return;
  clearTimeout(state.saveTimer);
  state.saveTimer=setTimeout(async()=>{
    const payload={user_id:state.user.id,novel_id:state.novelId,
      last_page:state.page,progress_percent:Math.round(state.page/state.pdf.numPages*100),
      last_opened_at:new Date().toISOString(),updated_at:new Date().toISOString()};
    const {error}=await getSupabase().from('sinjira_reader_library').upsert(payload,{onConflict:'user_id,novel_id'});
    if(error)message('Lecture affichée. La synchronisation de votre progression a échoué; votre page reste mémorisée sur cet appareil.','warning');
  },650);
}
function renderPage(){
  const version=++state.renderVersion;
  state.renderQueue=state.renderQueue.catch(()=>{}).then(async()=>{
    if(version!==state.renderVersion||!state.pdf)return;
    const page=await state.pdf.getPage(state.page);
    if(version!==state.renderVersion)return;
    if(state.mode==='texte'){
      const text=await page.getTextContent();
      if(version!==state.renderVersion)return;
      const lines=[],items=Array.isArray(text.items)?text.items:[];
      let line='',previousY=null;
      for(const item of items){
        if(typeof item.str!=='string')continue;
        const y=Array.isArray(item.transform)?Math.round(item.transform[5]):previousY;
        if(previousY!==null&&y!==null&&Math.abs(y-previousY)>3){
          if(line.trim())lines.push(line.trim());
          line='';
        }
        const word=item.str;
        if(word){
          if(line&&!/[\s\u2019'-]$/.test(line)&&!/^[,.;:!?)\]]/.test(word))line+=' ';
          line+=word;
        }
        if(item.hasEOL){
          if(line.trim())lines.push(line.trim());
          line='';
        }
        previousY=y;
      }
      if(line.trim())lines.push(line.trim());
      $('reader-text').textContent=lines.join('\n');
      $('reader-canvas').hidden=true;
      $('reader-text').hidden=false;
    }else{
      const viewer=$('reader-viewer');
      const baseWidth=Math.max(280,Math.min(1150,viewer.clientWidth-40));
      const viewport=page.getViewport({scale:1});
      const scale=(baseWidth/viewport.width)*state.zoom;
      const drawing=page.getViewport({scale});
      const pixelRatio=Math.min(window.devicePixelRatio||1,2);
      const canvas=$('reader-canvas'),context=canvas.getContext('2d',{alpha:false});
      canvas.width=Math.round(drawing.width*pixelRatio);
      canvas.height=Math.round(drawing.height*pixelRatio);
      canvas.style.width=Math.round(drawing.width)+'px';
      canvas.style.height=Math.round(drawing.height)+'px';
      await page.render({canvasContext:context,viewport:drawing,
        transform:pixelRatio===1?undefined:[pixelRatio,0,0,pixelRatio,0,0]}).promise;
      $('reader-text').hidden=true;
      canvas.hidden=false;
    }
  }).catch(error=>message('Impossible d’afficher cette page. Réessayez ou utilisez le lecteur PDF de secours.','error'));
}
function changePage(value){
  if(!state.pdf)return;
  const next=clamp(Math.round(value),1,state.pdf.numPages);
  if(next===state.page)return;
  state.page=next;
  updateToolbar();persist();renderPage();
  $('reader-viewer').scrollTo({top:0,left:0,behavior:'auto'});
}
function bindControls(){
  $('reader-previous').addEventListener('click',()=>changePage(state.page-1));
  $('reader-next').addEventListener('click',()=>changePage(state.page+1));
  $('reader-page').addEventListener('change',event=>changePage(event.target.value));
  $('reader-range').addEventListener('change',event=>changePage(event.target.value));
  $('reader-chapters').addEventListener('change',event=>changePage(event.target.value));
  $('reader-mode').addEventListener('click',()=>{
    state.mode=state.mode==='page'?'texte':'page';
    setTheme();renderPage();
  });
  $('reader-theme').addEventListener('change',event=>{
    state.theme=event.target.value;setTheme();
  });
  $('reader-size').addEventListener('input',event=>{
    state.size=clamp(event.target.value,16,32);setTheme();
  });
  $('reader-zoom').addEventListener('change',event=>{
    state.zoom=clamp(event.target.value,.8,1.5);setTheme();
    if(state.mode==='page')renderPage();
  });
  document.addEventListener('keydown',event=>{
    const tag=document.activeElement?.tagName||'';
    if(['INPUT','SELECT','TEXTAREA','BUTTON'].includes(tag)||event.altKey||event.ctrlKey||event.metaKey)return;
    if(event.key==='ArrowRight'||event.key==='PageDown'){event.preventDefault();changePage(state.page+1)}
    if(event.key==='ArrowLeft'||event.key==='PageUp'){event.preventDefault();changePage(state.page-1)}
  });
  let resizeTimer;
  window.addEventListener('resize',()=>{
    if(state.mode!=='page')return;
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(renderPage,250);
  });
}
async function resolvePrivateUrl(){
  state.user=await requireUser('/compte/connexion.html');
  const {data,error}=await getSupabase().functions.invoke('get-novel-file-url',{body:{slug:NOVEL_SLUG}});
  if(error||data?.ok!==true||typeof data.url!=='string'){
    throw new Error(data?.error||'Lecture intégrale non disponible pour ce compte. Vérifiez vos droits numériques ou votre rôle propriétaire.');
  }
  const url=new URL(data.url);
  if(url.protocol!=='https:'||url.origin!==SIGNED_ORIGIN||
     !url.pathname.startsWith('/storage/v1/object/sign/')){
    throw new Error('Le serveur a renvoyé une adresse de fichier non reconnue.');
  }
  return url.href;
}
async function restorePage(){
  let saved=clamp(Number(safeLocalGet(storageKey)||1),1,state.pdf.numPages);
  if(isFull&&state.user){
    const {data:novel,error:novelError}=await getSupabase().from('sinjira_novels')
      .select('id').eq('slug',NOVEL_SLUG).maybeSingle();
    if(!novelError&&novel?.id){
      state.novelId=novel.id;
      const {data:progress}=await getSupabase().from('sinjira_reader_library')
        .select('last_page').eq('user_id',state.user.id).eq('novel_id',novel.id).maybeSingle();
      if(progress?.last_page)saved=clamp(progress.last_page,1,state.pdf.numPages);
    }
  }
  state.page=saved;
}
async function init(){
  loadPreferences();setTheme();bindControls();
  const chapters=isFull?chaptersFull:chaptersDemo;
  const picker=$('reader-chapters');
  for(const [page,label] of chapters){
    const option=document.createElement('option');
    option.value=String(page);option.textContent=label;
    picker.append(option);
  }
  $('reader-edition').textContent=isFull?'Édition intégrale privée · 520 pages':'Démo gratuite · 82 pages';
  $('reader-demo-link').hidden=!isFull;
  $('reader-privacy').textContent=isFull
    ?'Lecture intégrale : une session authentifiée et un droit validé par le serveur sont nécessaires. Le fichier n’est pas enregistré dans le site public.'
    :'Démo officielle : prologue et chapitres 1 à 3. Vous pouvez aussi télécharger le PDF gratuit.';
  $('reader-download-demo').hidden=isFull;
  message(isFull?'Vérification de votre accès privé…':'Chargement de la démo officielle…');
  try{
    const url=isFull?await resolvePrivateUrl():DEMO_URL;
    /* Charger tous les octets une seule fois : aucune requête tardive après l’expiration
       du lien signé, aucun jeton dans l’URL d’un iframe ni dans le stockage local. */
    const response=await fetch(url,{cache:'no-store',referrerPolicy:'no-referrer'});
    if(!response.ok)throw new Error('Le fichier PDF ne peut pas être chargé ('+response.status+').');
    const data=new Uint8Array(await response.arrayBuffer());
    if(data.byteLength<1024||data.byteLength>20*1024*1024)throw new Error('Taille du document inattendue.');
    const pdfjs=await import(PDFJS);
    pdfjs.GlobalWorkerOptions.workerSrc=PDF_WORKER;
    state.pdf=await pdfjs.getDocument({data,isEvalSupported:false,useSystemFonts:true}).promise;
    if(state.pdf.numPages!==(isFull?520:82))throw new Error('Le nombre de pages de ce document ne correspond pas à l’édition attendue.');
    await restorePage();
    $('reader-loading').hidden=true;
    $('reader-content').hidden=false;
    updateToolbar();renderPage();
    $('reader-status').hidden=true;
  }catch(error){
    if(error?.message==='Connexion requise')return;
    $('reader-loading').hidden=true;
    message(error?.message||'Lecture actuellement indisponible.','error');
    $('reader-error').hidden=false;
    if(!isFull){
      const link=$('reader-native-demo');
      link.href=DEMO_URL;
      link.hidden=false;
    }
  }
}
init().catch(()=>message('La liseuse ne peut pas démarrer actuellement.','error'));
