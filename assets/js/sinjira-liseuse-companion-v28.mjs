/* SINJIRA V28 — repères privés, recherche locale et confort d'accès.
   Le roman intégral reste en mémoire, sans indexation ni note locale.
   Les notes intégrales vont uniquement vers la table RLS du compte. */

export function normalizeSearch(value){
  return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr-CA').trim();
}
/** Returns ranges in the ORIGINAL string even with decomposed accents.
    NFD may remove combining marks, therefore indices of normalized text cannot
    be used directly to slice the PDF text. No full-book index is persisted. */
export function findMatchRanges(text,query,limit=40){
  const source=String(text||'');
  const needle=normalizeSearch(query);
  if(needle.length<2||needle.length>100)return [];
  const starts=[],ends=[];
  let folded='';
  for(let i=0;i<source.length;){
    const codepoint=source.codePointAt(i);
    const fragment=String.fromCodePoint(codepoint);
    const end=i+fragment.length;
    const normalized=fragment.normalize('NFD')
      .replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr-CA');
    if(!normalized&&/[\u0300-\u036f]/u.test(fragment)&&ends.length){
      // A combining accent belongs to the preceding visible character.
      ends[ends.length-1]=end;
    }
    for(let j=0;j<normalized.length;j++){
      folded+=normalized[j];starts.push(i);ends.push(end);
    }
    i=end;
  }
  const result=[];
  let offset=0;
  const maximum=Math.max(0,Math.min(1000,Number(limit)||0));
  while(result.length<maximum){
    const at=folded.indexOf(needle,offset);
    if(at<0)break;
    result.push({start:starts[at],end:ends[at+needle.length-1]});
    offset=at+needle.length;
  }
  return result;
}
export function findMatches(text,query,limit=40){
  return findMatchRanges(text,query,limit).map(range=>range.start);
}
export function makeExcerpt(text,index,termLength=0,width=135){
  const start=Math.max(0,index-Math.floor(width/2));
  const end=Math.min(text.length,index+termLength+width-Math.floor(width/2));
  return (start?'…':'')+String(text).slice(start,end).replace(/\s+/gu,' ').trim()+(end<text.length?'…':'');
}
/** Trouve une sélection malgré les retours de ligne imposés par la mise en page PDF. */
export function findQuoteRange(text,quote){
  const source=String(text||''),target=String(quote||'').replace(/\s+/gu,' ').trim();
  if(!target||target.length>280)return null;
  let collapsed='',startMap=[],endMap=[];
  for(let i=0;i<source.length;i++){
    if(/\s/u.test(source[i])){
      let end=i+1;
      while(end<source.length&&/\s/u.test(source[end]))end++;
      if(collapsed&&collapsed[collapsed.length-1]!==' '){
        collapsed+=' ';startMap.push(i);endMap.push(end);
      }
      i=end-1;
    }else{
      collapsed+=source[i];startMap.push(i);endMap.push(i+1);
    }
  }
  const at=collapsed.indexOf(target);
  if(at<0)return null;
  return {start:startMap[at],end:endMap[at+target.length-1]};
}

export function safeReaderMark(mark){
  if(!mark||typeof mark!=='object')return null;
  if(!['bookmark','highlight','note'].includes(mark.kind))return null;
  const page=Number(mark.page);
  if(!Number.isInteger(page)||page<1||page>520)return null;
  return {
    id:String(mark.id||'').slice(0,100),page,kind:mark.kind,
    quote:String(mark.quote||'').slice(0,280),
    note:String(mark.note||'').slice(0,1500),
    created_at:String(mark.created_at||''),
  };
}

export function createReaderCompanion({
  isFull, getPdf, getPage, goToPage, getChapters, getUser,
  getNovelId, getSupabase, getTextAtPage,
}){
  const $=id=>document.getElementById(id);
  const state={marks:[],selectedQuote:'',searchVersion:0,searchTerm:'',searchBusy:false,focus:false,closed:false};
  const DEMO_MARKS_KEY='sinjira:liseuse:demo:marks:v28';
  const db=()=>getSupabase().from('sinjira_reader_marks');
  const isReady=()=>!state.closed&&Boolean(getPdf());
  const currentPage=()=>Math.min(Math.max(1,getPage()),getPdf()?.numPages||520);
  function notice(text,kind='info',id='reader-marks-status'){
    const el=$(id);
    if(!el)return;
    el.textContent=text;el.dataset.type=kind;
  }
  function localMarksRead(){
    try{
      const parsed=JSON.parse(localStorage.getItem(DEMO_MARKS_KEY)||'[]');
      return Array.isArray(parsed)?parsed.slice(0,200).map(safeReaderMark).filter(Boolean):[];
    }catch{return []}
  }
  function localMarksWrite(){
    // Démo publique seulement. Aucune citation de l'intégrale n'est stockée localement.
    if(isFull)return;
    try{localStorage.setItem(DEMO_MARKS_KEY,JSON.stringify(state.marks.slice(0,200)))}catch{
      notice('Stockage local indisponible. Vos repères risquent de ne pas être conservés.','warning');
    }
  }
  async function loadMarks(){
    if(!isFull){
      state.marks=localMarksRead();
      notice('Marque-pages et notes enregistrés sur cet appareil pour la démo.');
      renderMarks();
      return;
    }
    const user=getUser(),novelId=getNovelId();
    if(!user||!novelId){
      notice('Les repères privés ne peuvent pas être synchronisés avec ce compte.','error');
      return;
    }
    const {data,error}=await db().select('id,page,kind,quote,note,created_at')
      .eq('user_id',user.id).eq('novel_id',novelId)
      .order('created_at',{ascending:false}).limit(300);
    if(!isReady()||getUser()?.id!==user.id||getNovelId()!==novelId)return;
    if(error){
      notice('Synchronisation indisponible : vos notes privées ne sont pas enregistrées localement.','error');
      return;
    }
    state.marks=(data||[]).map(safeReaderMark).filter(Boolean);
    notice('Repères personnels synchronisés avec votre compte.');
    renderMarks();
  }
  async function addMark(kind){
    if(!isReady())return;
    const page=currentPage();
    const note=$('reader-note-input').value.trim().slice(0,1500);
    const quote=state.selectedQuote.slice(0,280);
    if(kind==='bookmark'&&state.marks.some(m=>m.kind==='bookmark'&&m.page===page)){
      notice('Cette page possède déjà un marque-page.');
      return;
    }
    if(kind==='highlight'&&!quote){
      notice('Sélectionnez d’abord un passage dans le texte du roman.','warning');
      return;
    }
    if(kind==='note'&&!note){
      notice('Saisissez votre note privée avant de l’enregistrer.','warning');
      return;
    }
    const mark={kind,page,quote:kind==='bookmark'?'':quote,
      note:kind==='note'?note:''};
    if(kind==='highlight')mark.note='';
    if(kind==='bookmark'){mark.quote='';mark.note=''}
    if(!isFull){
      const created={...mark,id:window.crypto?.randomUUID?.()||String(Date.now()+Math.random()),
        created_at:new Date().toISOString()};
      state.marks.unshift(created);localMarksWrite();
      notice('Repère enregistré sur cet appareil.');
    }else{
      const user=getUser(),novelId=getNovelId();
      if(!user||!novelId){
        notice('Connexion et droit de lecture requis pour enregistrer un repère.','error');
        return;
      }
      const {data,error}=await db().insert({...mark,user_id:user.id,novel_id:novelId})
        .select('id,page,kind,quote,note,created_at').single();
      if(!isReady()||getUser()?.id!==user.id||getNovelId()!==novelId)return;
      if(error){
        notice('Impossible d’enregistrer ce repère privé. Veuillez réessayer.','error');
        return;
      }
      const sanitized=safeReaderMark(data);
      if(sanitized)state.marks.unshift(sanitized);
      notice('Repère privé synchronisé à votre compte.');
    }
    if(kind==='note')$('reader-note-input').value='';
    state.selectedQuote='';
    $('reader-selection-preview').textContent='Aucun passage sélectionné.';
    renderMarks();decoratePage();
  }
  async function deleteMark(id){
    const mark=state.marks.find(m=>m.id===id);
    if(!mark)return;
    if(!window.confirm('Supprimer ce repère personnel ?'))return;
    if(isFull){
      const user=getUser(),novelId=getNovelId();
      if(!user||!novelId)return;
      const {error}=await db().delete()
        .eq('id',mark.id).eq('user_id',user.id).eq('novel_id',novelId);
      if(!isReady()||getUser()?.id!==user.id||getNovelId()!==novelId)return;
      if(error){notice('La suppression n’a pas pu être synchronisée.','error');return}
    }
    state.marks=state.marks.filter(m=>m.id!==id);
    localMarksWrite();
    notice('Repère supprimé.');
    renderMarks();decoratePage();
  }
  function renderMarks(){
    const container=$('reader-marks-list');
    container.replaceChildren();
    const marks=[...state.marks].sort((a,b)=>{
      if(a.page!==b.page)return a.page-b.page;
      return b.created_at.localeCompare(a.created_at);
    });
    if(!marks.length){
      const p=document.createElement('p');
      p.className='reader-empty';p.textContent='Aucun marque-page ni aucune note pour le moment.';
      container.append(p);
    }
    for(const mark of marks.slice(0,250)){
      const item=document.createElement('div');
      item.className='reader-mark-item';
      const link=document.createElement('button');
      link.type='button';link.className='reader-mark-jump';
      const names={bookmark:'Signet',highlight:'Surlignage',note:'Note'};
      link.textContent=(names[mark.kind]||'Repère')+' · Page '+mark.page;
      link.addEventListener('click',()=>goToPage(mark.page));
      item.append(link);
      if(mark.quote){
        const quote=document.createElement('p');
        quote.className='reader-mark-quote';
        quote.textContent='« '+mark.quote+' »';
        item.append(quote);
      }
      if(mark.note){
        const note=document.createElement('p');
        note.className='reader-mark-note';note.textContent=mark.note;item.append(note);
      }
      const del=document.createElement('button');
      del.className='reader-mark-delete';del.type='button';
      del.textContent='Supprimer';
      del.setAttribute('aria-label','Supprimer '+(names[mark.kind]||'repère')+' page '+mark.page);
      del.addEventListener('click',()=>{void deleteMark(mark.id)});
      item.append(del);
      container.append(item);
    }
    const exists=state.marks.some(m=>m.kind==='bookmark'&&m.page===currentPage());
    $('reader-bookmark-add').textContent=exists?'✓ Page marquée':'☆ Marquer cette page';
    $('reader-bookmark-add').disabled=exists;
  }
  function decoratePage(){
    const article=$('reader-text');
    if(!article||article.hidden||!isReady())return;
    const text=article.textContent||'';
    if(!text)return;
    const intervals=[];
    for(const mark of state.marks){
      if(mark.page!==currentPage()||mark.kind!=='highlight'||!mark.quote)continue;
      const range=findQuoteRange(text,mark.quote);
      if(range)intervals.push({...range,kind:'personal'});
    }
    if(state.searchTerm){
      const ranges=findMatchRanges(text,state.searchTerm,15);
      for(const range of ranges)intervals.push({...range,kind:'search'});
    }
    if(!intervals.length){article.textContent=text;return;}
    intervals.sort((a,b)=>a.start-b.start||(b.end-a.end));
    const frag=document.createDocumentFragment();
    let position=0;
    for(const interval of intervals){
      if(interval.start<position||interval.end>text.length)continue;
      frag.append(document.createTextNode(text.slice(position,interval.start)));
      const mark=document.createElement('mark');
      mark.className='reader-mark-'+interval.kind;
      mark.textContent=text.slice(interval.start,interval.end);
      frag.append(mark);
      position=interval.end;
    }
    frag.append(document.createTextNode(text.slice(position)));
    article.replaceChildren(frag);
  }
  function selectedPassage(){
    const article=$('reader-text'),selection=window.getSelection();
    if(!article||article.hidden||!selection||selection.isCollapsed)return;
    if(!article.contains(selection.anchorNode)||!article.contains(selection.focusNode))return;
    const quote=selection.toString().replace(/\s+/gu,' ').trim().slice(0,280);
    if(!quote)return;
    state.selectedQuote=quote;
    $('reader-selection-preview').textContent='Passage sélectionné : « '+quote+' »';
  }
  function updateStats(){
    if(!isReady())return;
    const page=currentPage(),total=getPdf().numPages;
    const percent=Math.round(page*100/total);
    const remaining=Math.max(0,total-page);
    $('reader-reading-stats').textContent='Progression : '+percent+' % · Page '+page+' sur '+total+
      ' · '+remaining+' page'+(remaining>1?'s':'')+' restante'+(remaining>1?'s':'')+'.';
    renderMarks();
  }
  function focusMode(toggle){
    state.focus=Boolean(toggle);
    document.body.classList.toggle('reader-focus-mode',state.focus);
    $('reader-focus').setAttribute('aria-pressed',String(state.focus));
    $('reader-focus').textContent=state.focus?'Quitter le plein écran':'Lecture plein écran';
    $('reader-focus').focus();
  }
  function addResult(page,excerpt){
    const item=document.createElement('button');
    item.type='button';item.className='reader-search-result';
    item.textContent='Page '+page+' — '+excerpt;
    item.addEventListener('click',()=>goToPage(page));
    $('reader-search-results').append(item);
  }
  async function searchBook(){
    if(!isReady()||state.searchBusy)return;
    const query=$('reader-search-field').value.trim().slice(0,100);
    if(query.length<2){
      notice('Entrez au moins deux caractères pour rechercher.','warning','reader-search-status');
      return;
    }
    const version=++state.searchVersion;
    state.searchTerm=query;state.searchBusy=true;
    $('reader-search-submit').disabled=true;
    $('reader-search-cancel').hidden=false;
    $('reader-search-results').replaceChildren();
    const pdf=getPdf(),max=pdf.numPages;
    let found=0,shown=0;
    try{
      for(let page=1;page<=max;page++){
        if(version!==state.searchVersion)break;
        // Lecture de chaque page en mémoire, jamais de requête à un moteur externe.
        const text=await getTextAtPage(page);
        if(version!==state.searchVersion||!isReady())break;
        const matches=findMatchRanges(text,query,1000);
        found+=matches.length;
        if(matches.length&&shown<80){
          addResult(page,makeExcerpt(text,matches[0].start,matches[0].end-matches[0].start,130));
          shown++;
        }
        if(page%8===0||page===max){
          notice('Recherche en cours : '+page+' / '+max+' pages · '+found+' occurrence(s).',
            'info','reader-search-status');
          await new Promise(resolve=>setTimeout(resolve,0));
        }
      }
      if(version===state.searchVersion&&isReady()){
        notice(found+' occurrence(s) trouvée(s) dans '+max+' pages. '+(shown<found?'80 résultats/pages affichés au maximum.':''),
          'info','reader-search-status');
        if(!shown){
          const p=document.createElement('p');p.className='reader-empty';
          p.textContent='Aucun passage trouvé.';
          $('reader-search-results').append(p);
        }
        decoratePage();
      }
    }catch{
      if(version===state.searchVersion&&isReady()){
        notice('Recherche interrompue : une page n’a pas pu être analysée.','error','reader-search-status');
      }
    }finally{
      if(version===state.searchVersion){
        state.searchBusy=false;
        $('reader-search-submit').disabled=false;
        $('reader-search-cancel').hidden=true;
      }
    }
  }
  function cancelSearch(){
    state.searchVersion++;
    state.searchBusy=false;
    $('reader-search-submit').disabled=false;
    $('reader-search-cancel').hidden=true;
    notice('Recherche arrêtée.','info','reader-search-status');
  }
  function bind(){
    $('reader-bookmark-add').addEventListener('click',()=>{void addMark('bookmark')});
    $('reader-highlight-save').addEventListener('click',()=>{void addMark('highlight')});
    $('reader-note-save').addEventListener('click',()=>{void addMark('note')});
    $('reader-text').addEventListener('mouseup',selectedPassage);
    $('reader-text').addEventListener('keyup',selectedPassage);
    $('reader-text').addEventListener('touchend',()=>setTimeout(selectedPassage,100));
    $('reader-search-submit').addEventListener('click',()=>{void searchBook()});
    $('reader-search-field').addEventListener('keydown',event=>{
      if(event.key==='Enter'){event.preventDefault();void searchBook()}
    });
    $('reader-search-cancel').addEventListener('click',cancelSearch);
    $('reader-focus').addEventListener('click',()=>focusMode(!state.focus));
    $('reader-chapter-next').addEventListener('click',()=>{
      const next=getChapters().find(entry=>entry[0]>currentPage());
      if(next)goToPage(next[0]);
    });
    document.addEventListener('keydown',event=>{
      if(event.key==='Escape'&&state.focus)focusMode(false);
    });
    let x=0,y=0;
    const viewer=$('reader-viewer');
    viewer.addEventListener('touchstart',event=>{
      if(event.touches.length!==1)return;
      x=event.touches[0].clientX;y=event.touches[0].clientY;
    },{passive:true});
    viewer.addEventListener('touchend',event=>{
      // V57 : le module tactile V52 possède les gestes; V53 les interprète
      // par écran. Le compagnon historique ne doit JAMAIS tourner le PDF
      // une seconde fois après ces modules. Garde le repli uniquement si
      // une ancienne page HTML n'a pas chargé V52.
      if(viewer.dataset?.readerTouchManaged==='v52'||
         viewer.dataset?.readerLayout==='screens'||event.defaultPrevented)return;
      if(event.changedTouches.length!==1||window.getSelection()?.toString())return;
      const dx=event.changedTouches[0].clientX-x;
      const dy=event.changedTouches[0].clientY-y;
      if(Math.abs(dx)>90&&Math.abs(dy)<55)goToPage(currentPage()+(dx<0?1:-1));
    },{passive:true});
  }
  bind();
  return {
    async ready(){await loadMarks();if(isReady()){updateStats();decoratePage()}},
    onPageChange(){if(!isReady())return;state.selectedQuote='';$('reader-selection-preview').textContent='Aucun passage sélectionné.';updateStats()},
    onTextRendered(){if(isReady())decoratePage()},
    onModeChange(){if(isReady())decoratePage()},
    close(){
      // Invalidate all pending searches and data reads before releasing references.
      state.closed=true;state.searchVersion++;state.searchBusy=false;
      state.marks=[];state.selectedQuote='';state.searchTerm='';
      if(state.focus){
        state.focus=false;
        document.body.classList.remove('reader-focus-mode');
      }
      $('reader-marks-list').replaceChildren();
      $('reader-search-results').replaceChildren();
      $('reader-selection-preview').textContent='';
      $('reader-note-input').value='';
      $('reader-search-field').value='';
    },
  };
}
