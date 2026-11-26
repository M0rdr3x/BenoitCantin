// Local-only PDF viewer. The runtime is enabled only after reviewed vendoring.
const RUNTIME_ENABLED = false;
const PUBLIC_FILES = Object.freeze({
  "resume": "01_Resume_Officiel_1_Page_Projet_Nova.pdf",
  "depliant": "02_Depliant_Public_4_Pages_Projet_Nova.pdf",
  "livre-court": "03_Livre_Nova_Version_Courte.pdf",
  "livre-complet": "04_Livre_Nova_Complet.pdf",
  "manifeste": "05_Manifeste_Officiel_Projet_Nova.pdf",
  "faq-citoyenne": "06_FAQ_Citoyenne_Officielle_Projet_Nova.pdf",
  "programme": "07_Programme_Electoral_Complet_Projet_Nova.pdf",
  "code-conduite": "08_Code_de_Conduite_Gouvernance_Nova.pdf",
  "dossier-presse": "09_Dossier_de_Presse_Projet_Nova.pdf",
  "charte-visuelle": "11_Charte_Visuelle_Projet_Nova.pdf",
  "resume-executif": "12_Resume_Executif_Officiel_Systeme_Nova.pdf"
});
const runtime = new URL('./pdfjs-6.5.438/', import.meta.url);
const directory = new URL('../documents/', import.meta.url);
const $ = id => document.getElementById(id);
const select = $('docSelect'), title = $('viewerTitle'), status = $('viewerStatus');
const download = $('downloadBtn'), open = $('openPdfBtn'), pages = $('pdfPages');
const pageInfo = $('pageInfo'), prev = $('prevPage'), next = $('nextPage');
const zoomOut = $('zoomOut'), zoomIn = $('zoomIn');
const docs = new Map();
for (const d of Array.isArray(window.NOVA_DOCUMENTS) ? window.NOVA_DOCUMENTS : []) {
  if (!d || typeof d.id !== 'string' || !Object.hasOwn(PUBLIC_FILES,d.id)
      || d.file !== PUBLIC_FILES[d.id] || d.path !== 'documents/' + d.file
      || d.format !== 'PDF' || typeof d.title !== 'string' || docs.has(d.id)) continue;
  const url = new URL(d.file,directory);
  if (url.origin !== location.origin || url.pathname !== directory.pathname + d.file) continue;
  docs.set(d.id, Object.freeze({id:d.id, file:d.file, title:d.title, url:url.href}));
}
let engine = null, worker = null, task = null, pdf = null, render = null;
let pageNum = 1, scale = 1.2, generation = 0, busy = false;
function controls(){
  prev.disabled = busy || !pdf || pageNum <= 1;
  next.disabled = busy || !pdf || pageNum >= pdf.numPages;
  zoomOut.disabled = busy || !pdf || scale <= 0.65;
  zoomIn.disabled = busy || !pdf || scale >= 2.6;
  pageInfo.textContent = pdf ? 'Page ' + pageNum + ' / ' + pdf.numPages : 'Page —';
}
function fallback(){
  status.textContent = 'Le rendu intégré est indisponible. Ouvrez le PDF dans votre navigateur ou téléchargez-le si vous le souhaitez.';
}
async function dispose(){
  const oldRender=render, oldTask=task, oldWorker=worker;
  render=null; task=null; worker=null; pdf=null;
  if(oldRender) { try { oldRender.cancel(); await oldRender.promise; } catch {} }
  if(oldTask) { try { await oldTask.destroy(); } catch {} }
  if(oldWorker) { try { oldWorker.destroy(); } catch {} }
}
async function draw(ticket){
  if(!pdf || ticket!==generation) return;
  busy=true; controls();
  try {
    const page=await pdf.getPage(pageNum);
    if(ticket!==generation) return;
    const viewport=page.getViewport({scale});
    const width=Math.ceil(viewport.width), height=Math.ceil(viewport.height);
    if(!Number.isSafeInteger(width)||!Number.isSafeInteger(height)||width<1||height<1||width>8192||height>8192||width*height>10000000) throw Error('Canvas limit');
    const holder=document.createElement('div'); holder.className='viewer-page-card';
    const canvas=document.createElement('canvas'); canvas.width=width; canvas.height=height;
    const context=canvas.getContext('2d'); if(!context) throw Error('Canvas unavailable');
    holder.append(canvas);
    render=page.render({canvasContext:context,viewport});
    await render.promise;
    if(ticket!==generation) return;
    pages.replaceChildren(holder);
    status.textContent='Document affiché dans le site. Le téléchargement reste volontaire.';
  } catch {
    if(ticket===generation){ await dispose(); if(ticket===generation){pages.replaceChildren();fallback();} }
  } finally {
    if(ticket===generation){ render=null;busy=false;controls(); }
  }
}
async function choose(id){
  if(busy) return;
  const d=docs.get(id); if(!d) return;
  const ticket=++generation; busy=true; select.disabled=true; controls();
  await dispose();
  if(ticket!==generation) return;
  select.value=d.id; title.textContent=d.title;
  open.href=d.url; open.hidden=false; download.href=d.url; download.download=d.file; download.hidden=false;
  pages.replaceChildren(); pageNum=1; scale=1.2; controls();
  const address=new URL(location.href); address.searchParams.set('doc',d.id); history.replaceState(null,'',address);
  try {
    if(!RUNTIME_ENABLED){ fallback();return; }
    engine ??= await import('./pdfjs-6.5.438/build/pdf.mjs');
    if(engine.version!=='6.5.438') throw Error('Unreviewed PDF engine');
    engine.GlobalWorkerOptions.workerSrc=new URL('build/pdf.worker.mjs',runtime).href;
    worker=new engine.PDFWorker(); await worker.promise;
    if(!(worker.port instanceof Worker)) throw Error('Dedicated worker required');
    task=engine.getDocument({
      url:d.url, worker, enableXfa:false, isEvalSupported:false, useWasm:false,
      disableWorkerRendering:true,isOffscreenCanvasSupported:false,isImageDecoderSupported:false,
      cMapUrl:new URL('web/cmaps/',runtime).href,cMapPacked:true,
      standardFontDataUrl:new URL('web/standard_fonts/',runtime).href,
      wasmUrl:new URL('web/wasm/',runtime).href,iccUrl:new URL('web/iccs/',runtime).href,
      disableAutoFetch:true,disableStream:true,maxImageSize:25000000,stopAtErrors:true
    });
    pdf=await task.promise;
    if(!Number.isSafeInteger(pdf.numPages)||pdf.numPages<1||pdf.numPages>10000) throw Error('Page limit');
    await draw(ticket);
  } catch { await dispose(); if(ticket===generation) fallback(); }
  finally { if(ticket===generation){busy=false;select.disabled=false;controls();} }
}
select.replaceChildren();
for(const d of docs.values()){
  const option=document.createElement('option'); option.value=d.id;option.textContent=d.title;select.append(option);
}
const requested=new URLSearchParams(location.search).get('doc');
select.addEventListener('change',()=>{ void choose(select.value); });
prev.addEventListener('click',()=>{if(!busy&&pdf&&pageNum>1){pageNum--;void draw(generation);}});
next.addEventListener('click',()=>{if(!busy&&pdf&&pageNum<pdf.numPages){pageNum++;void draw(generation);}});
zoomOut.addEventListener('click',()=>{if(!busy&&pdf){scale=Math.max(.65,scale-.15);void draw(generation);}});
zoomIn.addEventListener('click',()=>{if(!busy&&pdf){scale=Math.min(2.6,scale+.15);void draw(generation);}});
controls();
if(docs.size) void choose(docs.has(requested)?requested:docs.keys().next().value);
else {select.disabled=true;status.textContent='Aucun document public disponible.';}
