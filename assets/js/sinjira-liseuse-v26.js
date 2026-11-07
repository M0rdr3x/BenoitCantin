import { getSupabase, requireUser } from './sinjira-supabase.js';
import { pdfTextToParagraphs, speechTextChunks } from './sinjira-liseuse-text-v27.mjs';
import { createReaderCompanion } from './sinjira-liseuse-companion-v28.mjs';
import { chooseReadingPosition, ratioFromScroll, scrollTopForRatio } from './sinjira-liseuse-position-v31.mjs';

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
  user:null,novelId:null,renderVersion:0,renderQueue:Promise.resolve(),saveTimer:null,
  progressQueue:Promise.resolve(),accessEpoch:0,accessInvalidated:false,
  loadController:null,authSubscription:null,
  positionRatio:0,restorePending:null,restoringScroll:false,scrollTimer:null,resumeSource:'debut'};
const speech={active:false,paused:false,token:0,chunks:[],index:0,voices:[],utterance:null};
const speechReady='speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
const storageKey='sinjira:liseuse:'+edition+':la-cendre-du-jugement';
const themeKey='sinjira:liseuse:preferences';
const pageStorageKey=()=>isFull?storageKey+':'+(state.user?.id||'non-connecte'):storageKey;
let companion=null;

function safeLocalGet(key){try{return localStorage.getItem(key)}catch{return null}}
function safeLocalSet(key,value){try{localStorage.setItem(key,value);return true}catch{return false}}
function clamp(value,min,max){return Math.max(min,Math.min(max,Number(value)||min))}
function message(value,type='info'){
  const node=$('reader-status');
  node.textContent=value;node.dataset.type=type;node.hidden=false;
}
function positionNotice(value,type='info'){
  const node=$('reader-position-status');
  node.textContent=value;
  node.dataset.type=type;
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
function syncProgress(){
  if(!isFull||!state.user||!state.novelId||!state.pdf||state.accessInvalidated){
    return Promise.resolve(false);
  }
  // La file d'écriture évite qu'une ancienne requête écrase la dernière page.
  const userId=state.user.id,novelId=state.novelId,pdf=state.pdf;
  const send=async()=>{
    if(!state.pdf||state.pdf!==pdf||state.user?.id!==userId||state.novelId!==novelId)return false;
    const page=state.page,updatedAt=new Date().toISOString();
    const payload={user_id:userId,novel_id:novelId,
      last_page:page,progress_percent:Math.round(page/pdf.numPages*100),
      last_opened_at:updatedAt,updated_at:updatedAt};
    try{
      const {error}=await getSupabase().from('sinjira_reader_library')
        .upsert(payload,{onConflict:'user_id,novel_id'});
      if(error)throw error;
      return true;
    }catch{
      if(state.pdf===pdf&&state.user?.id===userId){
        message('La synchronisation a échoué. Votre page reste enregistrée sur cet appareil.','warning');
      }
      return false;
    }
  };
  state.progressQueue=state.progressQueue.catch(()=>false).then(send);
  return state.progressQueue;
}
function flushProgress(){
  if(!state.saveTimer)return;
  clearTimeout(state.saveTimer);state.saveTimer=null;
  void syncProgress();
}
function persist({syncCloud=true}={}){
  if(!state.pdf||(isFull&&state.accessInvalidated))return false;
  // La page, l'horodatage et la position numérique sont les SEULES données
  // de lecture écrites dans le navigateur. Aucun contenu du roman n'y entre.
  const key=pageStorageKey(),at=new Date().toISOString();
  const savedPage=safeLocalSet(key,String(state.page));
  const savedTime=safeLocalSet(key+':updated',at);
  const savedSpot=safeLocalSet(key+':spot',JSON.stringify({
    page:state.page,ratio:state.positionRatio
  }));
  if(syncCloud&&isFull&&state.user&&state.novelId){
    clearTimeout(state.saveTimer);
    state.saveTimer=setTimeout(()=>{state.saveTimer=null;void syncProgress()},450);
  }
  return savedPage&&savedTime&&savedSpot;
}
function flushScrollPosition(){
  if(!state.scrollTimer)return;
  clearTimeout(state.scrollTimer);state.scrollTimer=null;
  if(!state.pdf||state.restoringScroll)return;
  const viewer=$('reader-viewer');
  state.positionRatio=ratioFromScroll(viewer.scrollTop,viewer.scrollHeight,viewer.clientHeight);
  persist({syncCloud:false});
}
function restoreScrollAfterRender(version){
  if(state.restorePending===null)return;
  const ratio=state.restorePending;
  state.restorePending=null;
  state.restoringScroll=true;
  requestAnimationFrame(()=>{
    if(!state.pdf||version!==state.renderVersion)return;
    const viewer=$('reader-viewer');
    viewer.scrollTop=scrollTopForRatio(ratio,viewer.scrollHeight,viewer.clientHeight);
    requestAnimationFrame(()=>{
      if(version===state.renderVersion)state.restoringScroll=false;
    });
  });
}
async function saveCurrentPosition(){
  if(!state.pdf)return;
  flushScrollPosition();
  const viewer=$('reader-viewer');
  state.positionRatio=ratioFromScroll(viewer.scrollTop,viewer.scrollHeight,viewer.clientHeight);
  const localSaved=persist({syncCloud:false});
  $('reader-save-position').disabled=true;
  try{
    if(isFull){
      clearTimeout(state.saveTimer);state.saveTimer=null;
      const cloudSaved=await syncProgress();
      if(!state.pdf||state.accessInvalidated)return;
      positionNotice(cloudSaved
        ?'Position enregistrée : page '+state.page+' sur votre compte. Emplacement précis conservé sur cet appareil.'
        :localSaved
          ?'Page '+state.page+' enregistrée sur cet appareil. Synchronisation du compte indisponible : réessayez.'
          :'Impossible d’enregistrer la position. Vérifiez la connexion et les paramètres du navigateur.',
        cloudSaved?'success':'warning');
    }else{
      positionNotice(localSaved
        ?'Position enregistrée : page '+state.page+' et emplacement précis sur cet appareil.'
        :'Le navigateur ne permet pas la sauvegarde. Désactivez le mode privé ou autorisez le stockage.',
        localSaved?'success':'warning');
    }
  }finally{
    $('reader-save-position').disabled=false;
  }
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
      restoreScrollAfterRender(version);
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
      restoreScrollAfterRender(version);
    }
  }).catch(error=>message('Impossible d’afficher cette page. Réessayez ou utilisez le lecteur PDF de secours.','error'));
}
function changePage(value){
  if(!state.pdf)return;
  const next=clamp(Math.round(value),1,state.pdf.numPages);
  if(next===state.page)return;
  flushScrollPosition();
  stopNarration(false);
  state.page=next;
  state.positionRatio=0;
  state.restorePending=0;
  state.restoringScroll=true;
  $('reader-viewer').scrollTo({top:0,left:0,behavior:'instant'});
  updateToolbar();persist();renderPage();
  positionNotice('Page '+state.page+' mémorisée automatiquement. Vous pouvez aussi l’enregistrer maintenant.');
  companion?.onPageChange();
}
function bindControls(){
  $('reader-save-position').addEventListener('click',()=>{void saveCurrentPosition()});
  $('reader-viewer').addEventListener('scroll',()=>{
    if(!state.pdf||state.restoringScroll)return;
    clearTimeout(state.scrollTimer);
    state.scrollTimer=setTimeout(()=>{
      state.scrollTimer=null;
      if(!state.pdf||state.restoringScroll)return;
      const viewer=$('reader-viewer');
      state.positionRatio=ratioFromScroll(viewer.scrollTop,viewer.scrollHeight,viewer.clientHeight);
      if(!persist({syncCloud:false})){
        positionNotice('Enregistrement automatique indisponible dans ce navigateur.','warning');
      }
    },650);
  },{passive:true});
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
  window.addEventListener('pagehide',()=>{
    flushScrollPosition();stopNarration(false);flushProgress();companion?.close();
  });
  document.addEventListener('visibilitychange',()=>{
    if(document.visibilityState==='hidden'){
      flushScrollPosition();flushProgress();
    }
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
function assertPrivateAccess(epoch){
  if(isFull&&(state.accessInvalidated||state.accessEpoch!==epoch||!state.user)){
    throw new Error('SESSION_CHANGED');
  }
}
function lockPrivateReader(){
  // Bloque aussi une déconnexion PENDANT la vérification, le téléchargement
  // ou l'analyse du PDF, avant même son premier affichage.
  if(!isFull||state.accessInvalidated)return;
  state.accessInvalidated=true;
  state.accessEpoch++;
  state.loadController?.abort();
  state.loadController=null;
  clearTimeout(state.saveTimer);state.saveTimer=null;
  clearTimeout(state.scrollTimer);state.scrollTimer=null;
  $('reader-position-status').textContent='';
  stopNarration(false);
  companion?.close();companion=null;
  const book=state.pdf;
  state.pdf=null;state.user=null;state.novelId=null;
  state.renderVersion++;
  // Aucun texte/citation privé ne reste visible après changement de compte.
  $('reader-text').textContent='';
  $('reader-marks-list').replaceChildren();
  $('reader-search-results').replaceChildren();
  $('reader-selection-preview').textContent='';
  $('reader-note-input').value='';
  $('reader-search-field').value='';
  $('reader-canvas').width=0;$('reader-canvas').height=0;
  $('reader-content').hidden=true;
  $('reader-loading').hidden=true;$('reader-error').hidden=false;
  message('Votre session a changé. Reconnectez-vous pour rouvrir le roman intégral.','error');
  try{Promise.resolve(book?.destroy?.()).catch(()=>{})}catch{/* PDF fermé */}
}
function watchPrivateSession(){
  if(!isFull||state.authSubscription)return;
  // S'abonner avant de signer et récupérer le PDF, pas après le chargement.
  const {data}=getSupabase().auth.onAuthStateChange((event,session)=>{
    if(event==='SIGNED_OUT'||
       (event==='SIGNED_IN'&&state.user&&session?.user?.id!==state.user.id)){
      lockPrivateReader();
    }
  });
  state.authSubscription=data?.subscription||null;
}
async function resolvePrivateUrl(){
  state.user=await requireUser('/compte/connexion.html');
  watchPrivateSession();
  const epoch=state.accessEpoch;
  const {data,error}=await getSupabase().functions.invoke('get-novel-file-url',{body:{slug:NOVEL_SLUG}});
  assertPrivateAccess(epoch);
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
  // Conserver la compatibilité avec les anciennes pages sauvegardées sans défilement.
  const defaultPage=isFull?4:3,key=pageStorageKey();
  const localPage=Number(safeLocalGet(key));
  let localRatio=0;
  try{
    const spot=JSON.parse(safeLocalGet(key+':spot')||'null');
    if(spot&&spot.page===localPage)localRatio=spot.ratio;
  }catch{/* ancien format de progression */}
  let serverPage=null,serverUpdatedAt=null;
  if(isFull&&state.user){
    const {data:novel,error:novelError}=await getSupabase().from('sinjira_novels')
      .select('id').eq('slug',NOVEL_SLUG).maybeSingle();
    if(!novelError&&novel?.id){
      state.novelId=novel.id;
      const {data:progress}=await getSupabase().from('sinjira_reader_library')
        .select('last_page,updated_at').eq('user_id',state.user.id).eq('novel_id',novel.id).maybeSingle();
      serverPage=progress?.last_page;
      serverUpdatedAt=progress?.updated_at;
    }
  }
  const spot=chooseReadingPosition({
    localPage,localRatio,localUpdatedAt:safeLocalGet(key+':updated'),
    serverPage,serverUpdatedAt,totalPages:state.pdf.numPages,defaultPage
  });
  state.page=spot.page;
  state.positionRatio=spot.ratio;
  state.restorePending=spot.ratio;
  state.resumeSource=spot.source;
  state.restoringScroll=true;
  if(spot.source==='compte'){
    // L'ancien schéma serveur mémorise la page, pas l'endroit exact dans cette page.
    safeLocalSet(key,String(spot.page));
    safeLocalSet(key+':updated',serverUpdatedAt||new Date().toISOString());
    safeLocalSet(key+':spot',JSON.stringify({page:spot.page,ratio:0}));
  }
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
  let loadedPdf=null;
  try{
    const url=isFull?await resolvePrivateUrl():DEMO_URL;
    const loadEpoch=state.accessEpoch;
    const expectedUserId=isFull?state.user?.id:null;
    // Le lien privé n'est pas persistant. Une déconnexion annule immédiatement
    // le téléchargement et interdit tout rendu même si une promesse se termine.
    state.loadController=new AbortController();
    const response=await fetch(url,{cache:'no-store',referrerPolicy:'no-referrer',
      signal:state.loadController.signal});
    assertPrivateAccess(loadEpoch);
    if(!response.ok)throw new Error('Le fichier PDF ne peut pas être chargé ('+response.status+').');
    const data=new Uint8Array(await response.arrayBuffer());
    assertPrivateAccess(loadEpoch);
    if(data.byteLength<1024||data.byteLength>20*1024*1024)throw new Error('Taille du document inattendue.');
    const pdfjs=await import(PDFJS);
    assertPrivateAccess(loadEpoch);
    pdfjs.GlobalWorkerOptions.workerSrc=PDF_WORKER;
    loadedPdf=await pdfjs.getDocument({data,isEvalSupported:false,useSystemFonts:true}).promise;
    assertPrivateAccess(loadEpoch);
    if(loadedPdf.numPages!==(isFull?520:82))throw new Error('Le nombre de pages de ce document ne correspond pas à l’édition attendue.');
    state.pdf=loadedPdf;
    await restorePage();
    assertPrivateAccess(loadEpoch);
    if(isFull){
      // Les droits sont attribués par le serveur; vérifier à nouveau la session
      // juste avant d'afficher les octets privés en mémoire.
      const {data:authData,error:authError}=await getSupabase().auth.getUser();
      if(authError||!authData?.user||authData.user.id!==expectedUserId){
        lockPrivateReader();
      }
      assertPrivateAccess(loadEpoch);
    }
    state.loadController=null;
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
    const origin=state.resumeSource==='compte'?'depuis votre compte'
      :state.resumeSource==='appareil'?'depuis cet appareil':'au début du roman';
    positionNotice('Lecture prête : page '+state.page+' reprise '+origin+'. Enregistrement automatique actif.');
    // L'indisponibilité de la synchronisation des notes ne bloque pas la lecture.
    companion.ready().catch(()=>message('La liseuse fonctionne, mais les repères personnels ne sont pas disponibles.','warning'));
    $('reader-status').hidden=true;
  }catch(error){
    state.loadController=null;
    if(loadedPdf){
      if(state.pdf===loadedPdf)state.pdf=null;
      try{await loadedPdf.destroy?.()}catch{/* Destruction best effort */}
    }
    if(error?.message==='Connexion requise')return;
    $('reader-loading').hidden=true;
    if(isFull&&(state.accessInvalidated||error?.message==='SESSION_CHANGED'||error?.name==='AbortError')){
      message('Votre session a changé. Reconnectez-vous pour accéder à cette édition.','error');
    }else{
      message(error?.message||'Lecture actuellement indisponible.','error');
    }
    $('reader-error').hidden=false;
    if(!isFull){
      const link=$('reader-native-demo');
      link.href=DEMO_URL;
      link.hidden=false;
    }
  }
}
init().catch(()=>message('La liseuse ne peut pas démarrer actuellement.','error'));
