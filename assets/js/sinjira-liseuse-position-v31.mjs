/* SINJIRA V31 — sauvegarde de position sans conserver le texte du roman.
   Le pourcentage désigne seulement le défilement à l'intérieur d'une page PDF. */

export function readingRatio(value){
  const n=Number(value);
  return Number.isFinite(n)?Math.round(Math.max(0,Math.min(1,n))*1000)/1000:0;
}

export function ratioFromScroll(scrollTop,scrollHeight,clientHeight){
  const max=Math.max(0,Number(scrollHeight)-Number(clientHeight));
  if(!Number.isFinite(max)||!max)return 0;
  return readingRatio(Number(scrollTop)/max);
}

export function scrollTopForRatio(ratio,scrollHeight,clientHeight){
  const max=Math.max(0,Number(scrollHeight)-Number(clientHeight));
  return Number.isFinite(max)?Math.round(readingRatio(ratio)*max):0;
}

/** Sélectionne la position la plus récemment enregistrée entre ce navigateur et le compte.
    Les anciens comptes qui n'ont qu'un last_page restent compatibles.
    Le serveur ne stocke actuellement que la page, jamais le défilement intrapage. */
export function chooseReadingPosition({localPage,localRatio,localUpdatedAt,
    serverPage,serverUpdatedAt,totalPages,defaultPage}){
  const total=Math.max(1,Math.floor(Number(totalPages)||1));
  const validPage=(page)=>Number.isInteger(Number(page))&&Number(page)>=1&&Number(page)<=total;
  const fallback=validPage(defaultPage)?Number(defaultPage):1;
  const localValid=validPage(localPage);
  const serverValid=validPage(serverPage);
  const localDate=Date.parse(localUpdatedAt||'')||0;
  const serverDate=Date.parse(serverUpdatedAt||'')||0;
  if(serverValid&&(!localValid||!localDate||serverDate>localDate)){
    return {page:Number(serverPage),ratio:0,source:'compte'};
  }
  if(localValid){
    return {page:Number(localPage),ratio:readingRatio(localRatio),source:'appareil'};
  }
  return {page:fallback,ratio:0,source:'debut'};
}
