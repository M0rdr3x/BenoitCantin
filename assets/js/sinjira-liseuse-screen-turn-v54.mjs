/* SINJIRA V54 — navigation par écrans visibles sans conserver le texte privé.
 * Le PDF continue à définir le numéro de page; le défilement intrapage
 * reste suivi par le ratio V31 existant, y compris lorsque l'écran change.
 */
export function planReaderScreenTurn({direction,mode,scrollTop,scrollHeight,clientHeight}={}){
  const stepDirection=direction===1?1:direction===-1?-1:0;
  if(!stepDirection)return {kind:'none'};
  const nextPage={kind:'page',delta:stepDirection,end:stepDirection<0};
  if(mode!=='texte')return {...nextPage,end:false};

  const viewport=Number(clientHeight);
  const height=Number(scrollHeight);
  const current=Number(scrollTop);
  if(!Number.isFinite(viewport)||viewport<=0||
     !Number.isFinite(height)||!Number.isFinite(current))return nextPage;

  const max=Math.max(0,height-viewport);
  const top=Math.max(0,Math.min(max,current));
  if(max<=2)return nextPage;
  const stride=Math.max(1,Math.floor(viewport*.88));

  // Quelques pixels de tolérance évitent de bloquer le passage aux pages
  // PDF suivantes/précédentes sur les navigateurs à défilement fractionnaire.
  if(stepDirection>0&&top<max-2){
    return {kind:'scroll',top:Math.min(max,top+stride)};
  }
  if(stepDirection<0&&top>2){
    return {kind:'scroll',top:Math.max(0,top-stride)};
  }
  return nextPage;
}
