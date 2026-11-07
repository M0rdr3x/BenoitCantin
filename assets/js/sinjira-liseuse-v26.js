import { getSupabase, requireUser } from './sinjira-supabase.js';
import { pdfTextToParagraphs, speechTextChunks } from './sinjira-liseuse-text-v27.mjs';
import { createReaderCompanion } from './sinjira-liseuse-companion-v28.mjs';

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
const state={pdf:null,page:1,mode:'texte',theme:'sepia',size:20,zoom:1,
  font:'serif',lineHeight:1.75,textWidth:780,letterSpacing:0,
  voiceURI:'',speed:1,autoSpeech:false,
  user:null,novelId:null,renderVersion:0,renderQueue:Promise.resolve(),saveTimer:null};
const speech={active:false,paused:false,token:0,chunks:[],index:0,voices:[],utterance:null};
const speechReady='speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
const storageKey='sinjira:liseuse:'+edition+':la-cendre-du-jugement';
const themeKey='sinjira:liseuse:preferences';
const pageStorageKey=()=>isFull?storageKey+':'+(state.user?.id||'non-connecte'):storageKey;
let companion=null;

function safeLocalGet(key){try{return localStorage.getItem(key)}catch{return null}}
function safeLocalSet(key,value){try{localStorage.setItem(key,value)}catch{/* navigation privée */}}
function clamp(value,min,max){return Math.max(min,Math.min(max,Number(value)||min))}
function message(value,type='info'){
  const node=$('reader-status');
  node.textContent=value;node.dataset.type=type;node.hidden=false;
}
function savePreferences(){
  // Seules les préférences de présentation sont mémorisées, jamais le texte privé.
  const {theme,size,zoom,mode,font,lineHeight,textWidth,letterSpacing,voiceURI,speed,autoSpeech}=state;
  safeLocalSet(themeKey,JSON.stringify({theme,size,zoom,mode,font,lineHeight,textWidth,letterSpacing,voiceURI,speed,autoSpeech}));
}
function loadPreferences(){
  try{
    const prefs=JSON.parse(safeLocalGet(themeKey)||'{}');
    if(['clair','sepia','nuit'].includes(prefs.theme))state.theme=prefs.theme;
    if(['texte','page'].includes(prefs.mode))state.mode=prefs.mode;
    if(['serif','sans','accessible'].includes(prefs.font))state.font=prefs.font;
    if([1.45,1.75,2.1].includes(Number(prefs.lineHeight)))state.lineHeight=Number(prefs.lineHeight);
    if([600,780,960].includes(Number(prefs.textWidth)))state.textWidth=Number(prefs.textWidth);
    if([0,0.035,0.07].includes(Number(prefs.letterSpacing)))state.letterSpacing=Number(prefs.letterSpacing);
    if([0.75,1,1.25,1.5].includes(Number(prefs.speed)))state.speed=Number(prefs.speed);
    if(typeof prefs.voiceURI==='string')state.voiceURI=prefs.voiceURI.slice(0,300);
    if(typeof prefs.autoSpeech==='boolean')state.autoSpeech=prefs.autoSpeech;
    state.size=clamp(prefs.size||20,16,34);
    state.zoom=clamp(prefs.zoom||1,.8,1.5);
  }catch{/* valeurs par défaut */}
}
function setTheme(){
  const fonts={
    serif:"Georgia, 'Times New Roman', serif",
    sans:"system-ui, -apple-system, 'Segoe UI', Arial, sans-serif",
    accessible:"Verdana, Tahoma, Arial, sans-serif"
  };
  document.body.dataset.readTheme=state.theme;
  document.body.style.setProperty('--reader-text-size',state.size+'px');
  document.body.style.setProperty('--reader-font',fonts[state.font]);
  document.body.style.setProperty('--reader-line-height',String(state.lineHeight));
  document.body.style.setProperty('--reader-measure',state.textWidth+'px');
  document.body.style.setProperty('--reader-letter-spacing',state.letterSpacing+'em');
  $('reader-theme').value=state.theme;
  $('reader-font').value=state.font;
  $('reader-size').value=String(state.size);
  $('reader-size-value').textContent=state.size+' px';
  $('reader-line-height').value=String(state.lineHeight);
  $('reader-text-width').value=String(state.textWidth);
  $('reader-letter-spacing').value=String(state.letterSpacing);
  $('reader-zoom').value=String(state.zoom);
  $('reader-speed').value=String(state.speed);
  $('reader-voice-auto').checked=state.autoSpeech;
  $('reader-mode').textContent=state.mode==='texte'?'Afficher le PDF':'Texte adaptable';
  $('reader-mode').setAttribute('aria-pressed',String(state.mode==='page'));
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
async function syncProgress(){
  if(!isFull||!state.user||!state.novelId||!state.pdf)return;
  const page=state.page;
  const payload={user_id:state.user.id,novel_id:state.novelId,
    last_page:page,progress_percent:Math.round(page/state.pdf.numPages*100),
    last_opened_at:new Date().toISOString(),updated_at:new Date().toISOString()};
  try{
    const {error}=await getSupabase().from('sinjira_reader_library').upsert(payload,{onConflict:'user_id,novel_id'});
    if(error)throw error;
  }catch{
    message('La synchronisation de progression a échoué. La dernière page reste enregistrée sur cet appareil.','warning');
  }
}
function flushProgress(){
  if(!state.saveTimer)return;
  clearTimeout(state.saveTimer);state.saveTimer=null;
  void syncProgress();
}
function persist(){
  // Éviter de mélanger la progression de différents comptes partageant un appareil.
  safeLocalSet(pageStorageKey(),String(state.page));
  if(!isFull||!state.user||!state.novelId)return;
  clearTimeout(state.saveTimer);
  state.saveTimer=setTimeout(()=>{state.saveTimer=null;void syncProgress()},450);
}
function updateSpeechControls(){
  $('reader-voice-play').disabled=!speechReady||!state.pdf||speech.active&&!speech.paused;
  $('reader-voice-pause').disabled=!speechReady||!speech.active;
  $('reader-voice-pause').textContent=speech.paused?'▶ Reprendre':'⏸ Pause';
  $('reader-voice-stop').disabled=!speechReady||!speech.active;
}
function speechStatus(text){
  $('reader-voice-status').textContent=text;
  updateSpeechControls();
}
function stopNarration(announce=true){
  speech.token++;
  speech.active=false;speech.paused=false;speech.chunks=[];speech.index=0;speech.utterance=null;
  if(speechReady)window.speechSynthesis.cancel();
  if(announce)speechStatus('Lecture vocale arrêtée.');
  else updateSpeechControls();
}
function listVoices(){
  if(!speechReady)return;
  const available=window.speechSynthesis.getVoices();
  speech.voices=available.filter(voice=>/^fr(?:-|$)/i.test(voice.lang));
  const select=$('reader-voice');
  const chosen=state.voiceURI;
  select.replaceChildren();
  const defaultOption=document.createElement('option');
  defaultOption.value='';defaultOption.textContent='Voix automatique en français';
  select.append(defaultOption);
  for(const voice of speech.voices){
    const option=document.createElement('option');
    option.value=voice.voiceURI;
    option.textContent=voice.name+' ('+voice.lang+')';
    select.append(option);
  }
  select.value=speech.voices.some(v=>v.voiceURI===chosen)?chosen:'';
}
function configureSpeech(){
  if(!speechReady){
    $('reader-voice').disabled=true;
    $('reader-speed').disabled=true;
    $('reader-voice-auto').disabled=true;
    speechStatus('Lecture vocale indisponible dans ce navigateur.');
    return;
  }
  listVoices();
  window.speechSynthesis.addEventListener?.('voiceschanged',listVoices);
  updateSpeechControls();
}
function speakNext(token){
  if(!speechReady||token!==speech.token||!speech.active)return;
  if(speech.index>=speech.chunks.length){
    const continueReading=state.autoSpeech&&state.page<state.pdf.numPages;
    stopNarration(false);
    if(continueReading){
      changePage(state.page+1);
      startNarration().catch(()=>speechStatus('Lecture vocale interrompue.'));
    }else{
      speechStatus('Page terminée. Vous pouvez poursuivre à la page suivante.');
    }
    return;
  }
  const utterance=new SpeechSynthesisUtterance(speech.chunks[speech.index]);
  utterance.lang='fr-CA';
  utterance.rate=state.speed;
  utterance.voice=speech.voices.find(voice=>voice.voiceURI===state.voiceURI)||null;
  utterance.onend=()=>{
    if(token!==speech.token)return;
    speech.index++;
    speakNext(token);
  };
  utterance.onerror=event=>{
    if(token!==speech.token)return;
    if(event.error==='interrupted'||event.error==='canceled')return;
    stopNarration(false);
    speechStatus('La voix ne peut pas lire ce passage sur cet appareil.');
  };
  // Garder la référence en mémoire : certains moteurs WebKit interrompent autrement la voix.
  speech.utterance=utterance;
  window.speechSynthesis.speak(utterance);
}
async function startNarration(){
  if(!speechReady||!state.pdf)return;
  stopNarration(false);
  const token=speech.token;
  const pageNumber=state.page;
  const page=await state.pdf.getPage(pageNumber);
  const content=await page.getTextContent();
  if(token!==speech.token||pageNumber!==state.page)return;
  const text=pdfTextToParagraphs(content.items);
  if(!text){
    speechStatus('Cette page ne contient pas de texte lisible par la voix. Essayez la suivante.');
    return;
  }
  speech.chunks=speechTextChunks(text);
  if(!speech.chunks.length)return;
  state.mode='texte';
  setTheme();renderPage();
  speech.index=0;speech.active=true;speech.paused=false;
  speechStatus('Lecture vocale de la page '+pageNumber+' en cours…');
  speakNext(token);
}
function toggleSpeechPause(){
  if(!speechReady||!speech.active)return;
  if(speech.paused){
    window.speechSynthesis.resume();
    speech.paused=false;
    speechStatus('Lecture vocale reprise.');
  }else{
    window.speechSynthesis.pause();
    speech.paused=true;
    speechStatus('Lecture vocale en pause.');
  }
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
      const readable=pdfTextToParagraphs(text.items);
      $('reader-text').textContent=readable||'Cette page contient surtout des images ou du texte non sélectionnable. Utilisez « Afficher le PDF » pour consulter sa mise en page.';
      $('reader-canvas').hidden=true;
      $('reader-text').hidden=false;
      companion?.onTextRendered();
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
  stopNarration(false);
  state.page=next;
  updateToolbar();persist();renderPage();
  companion?.onPageChange();
  $('reader-viewer').scrollTo({top:0,left:0,behavior:'auto'});
}
function bindControls(){
  $('reader-previous').addEventListener('click',()=>changePage(state.page-1));
  $('reader-next').addEventListener('click',()=>changePage(state.page+1));
  $('reader-page').addEventListener('change',event=>changePage(event.target.value));
  $('reader-range').addEventListener('change',event=>changePage(event.target.value));
  $('reader-chapters').addEventListener('change',event=>changePage(event.target.value));
  $('reader-mode').addEventListener('click',()=>{
    stopNarration(false);
    state.mode=state.mode==='page'?'texte':'page';
    setTheme();renderPage();
    companion?.onModeChange();
  });
  $('reader-theme').addEventListener('change',event=>{
    state.theme=event.target.value;setTheme();
  });
  $('reader-size').addEventListener('input',event=>{
    state.size=clamp(event.target.value,16,34);setTheme();
  });
  $('reader-font').addEventListener('change',event=>{
    if(['serif','sans','accessible'].includes(event.target.value)){state.font=event.target.value;setTheme()}
  });
  $('reader-line-height').addEventListener('change',event=>{
    state.lineHeight=Number(event.target.value);setTheme();
  });
  $('reader-text-width').addEventListener('change',event=>{
    state.textWidth=Number(event.target.value);setTheme();
  });
  $('reader-letter-spacing').addEventListener('change',event=>{
    state.letterSpacing=Number(event.target.value);setTheme();
  });
  $('reader-speed').addEventListener('change',event=>{
    state.speed=Number(event.target.value);savePreferences();
  });
  $('reader-voice').addEventListener('change',event=>{
    state.voiceURI=event.target.value;stopNarration(false);savePreferences();
  });
  $('reader-voice-auto').addEventListener('change',event=>{
    state.autoSpeech=event.target.checked;savePreferences();
  });
  $('reader-voice-play').addEventListener('click',()=>startNarration().catch(()=>{
    stopNarration(false);speechStatus('Impossible de lancer la lecture à voix haute.');
  }));
  $('reader-voice-pause').addEventListener('click',toggleSpeechPause);
  $('reader-voice-stop').addEventListener('click',()=>stopNarration());
  window.addEventListener('pagehide',()=>{stopNarration(false);flushProgress();companion?.close()});
  document.addEventListener('visibilitychange',()=>{
    if(document.visibilityState==='hidden')flushProgress();
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
  // Sur une première ouverture, commencer sur le prologue plutôt que sur la couverture image.
  const firstReadablePage=isFull?4:3;
  let saved=clamp(Number(safeLocalGet(pageStorageKey())||firstReadablePage),1,state.pdf.numPages);
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
  loadPreferences();setTheme();bindControls();configureSpeech();
  if(window.matchMedia?.('(max-width: 980px)').matches){
    document.querySelectorAll('.reader-sidebar details').forEach(detail=>{detail.open=false});
  }
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
    companion=createReaderCompanion({
      isFull,
      getPdf:()=>state.pdf,
      getPage:()=>state.page,
      goToPage:changePage,
      getChapters:()=>isFull?chaptersFull:chaptersDemo,
      getUser:()=>state.user,
      getNovelId:()=>state.novelId,
      getSupabase,
      getTextAtPage:async pageNumber=>{
        const page=await state.pdf.getPage(pageNumber);
        const text=await page.getTextContent();
        return pdfTextToParagraphs(text.items);
      },
    });
    $('reader-loading').hidden=true;
    $('reader-content').hidden=false;
    updateToolbar();renderPage();updateSpeechControls();
    // L'indisponibilité de la synchronisation des notes ne bloque pas la lecture.
    companion.ready().catch(()=>message('La liseuse fonctionne, mais les repères personnels ne sont pas disponibles.','warning'));
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
