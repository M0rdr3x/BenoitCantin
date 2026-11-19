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

/** Choisit la sauvegarde la plus récente. Le champ cloud scroll_ratio est nullable :
    null signifie une ancienne progression V31 sans emplacement précis.
    Aucun texte, passage ou citation du roman n'est stocké. */
export function chooseReadingPosition({localPage,localRatio,localUpdatedAt,
    serverPage,serverRatio=null,serverUpdatedAt,totalPages,defaultPage}){
  const total=Math.max(1,Math.floor(Number(totalPages)||1));
  const validPage=(page)=>Number.isInteger(Number(page))&&Number(page)>=1&&Number(page)<=total;
  const fallback=validPage(defaultPage)?Number(defaultPage):1;
  const localValid=validPage(localPage);
  const serverValid=validPage(serverPage);
  const localDate=Date.parse(localUpdatedAt||'')||0;
  const serverDate=Date.parse(serverUpdatedAt||'')||0;
  const hasServerRatio=serverRatio!==null&&serverRatio!==undefined&&
    Number.isFinite(Number(serverRatio))&&Number(serverRatio)>=0&&Number(serverRatio)<=1;
  if(serverValid&&(!localValid||!localDate||serverDate>localDate)){
    // Une ancienne ligne SQL n'a pas encore de position intrapage.
    // Conserver l'emplacement local si les deux copies pointent vers la même page.
    if(localValid&&Number(localPage)===Number(serverPage)&&!hasServerRatio){
      return {page:Number(localPage),ratio:readingRatio(localRatio),source:'appareil'};
    }
    return {page:Number(serverPage),
      ratio:hasServerRatio?readingRatio(serverRatio):0,source:'compte'};
  }
  if(localValid){
    return {page:Number(localPage),ratio:readingRatio(localRatio),source:'appareil'};
  }
  if(serverValid){
    return {page:Number(serverPage),
      ratio:hasServerRatio?readingRatio(serverRatio):0,source:'compte'};
  }
  return {page:fallback,ratio:0,source:'debut'};
}

/** V34 — ne jamais réécrire une progression de cet appareil si le compte
    dispose déjà d'une sauvegarde plus récente. Les dates invalides refusent
    le rejeu (sauf l'absence de ligne serveur, qui est un cas normal). */
export function shouldReplayReadingProgress(pendingAt,serverUpdatedAt){
  const local=Date.parse(pendingAt||'');
  if(!Number.isFinite(local)||local<=0)return false;
  if(!serverUpdatedAt)return true;
  const remote=Date.parse(serverUpdatedAt);
  return Number.isFinite(remote)&&remote>0&&local>=remote;
}

/** V51.5 : une sauvegarde CAS doit être rejouée selon la révision SERVEUR,
    jamais selon l'horloge locale. 'current' signifie que l'écriture CAS peut
    être tentée, pas qu'elle est définitivement autorisée : une autre session
    peut encore agir, et l'UPDATE atomique serveur fera foi. */
export function cloudRevisionDecision(expectedRevision,remoteRecord){
  const normalize=value=>{
    if(value===null)return null;
    if((typeof value!=='number'&&typeof value!=='string')||value==='')return undefined;
    const n=Number(value);
    return Number.isSafeInteger(n)&&n>=0?n:undefined;
  };
  const expected=normalize(expectedRevision);
  if(expected===undefined)return 'invalid';
  if(remoteRecord===null)return expected===null?'current':'conflict';
  if(!remoteRecord||typeof remoteRecord!=='object')return 'invalid';
  const actual=normalize(remoteRecord.revision);
  if(actual===undefined||actual===null)return 'invalid';
  return expected===actual?'current':'conflict';
}
