/* Outils purs pour lecture reformatable et synthèse vocale SINJIRA.
   Le contenu des romans ne quitte pas la session navigateur. */

const punctuationStart=/^[,.;:!?)\]\u00bb]/u;

function appendText(previous,fragment,previousItem,item){
  if(!previous)return fragment;
  if(!fragment)return previous;
  if(/\s$/u.test(previous)||/^\s/u.test(fragment)||punctuationStart.test(fragment))return previous+fragment;
  const x=Number(item?.transform?.[4]);
  const oldX=Number(previousItem?.transform?.[4]);
  const width=Number(previousItem?.width);
  if(Number.isFinite(x)&&Number.isFinite(oldX)&&Number.isFinite(width)&&
      Array.isArray(item?.transform)&&Array.isArray(previousItem?.transform)){
    const gap=x-(oldX+width);
    if(gap<=1.35)return previous+fragment;
    return previous+' '+fragment;
  }
  // En l'absence de coordonnées, ne pas séparer toutes les lettres.
  return previous.length===1||fragment.length===1?previous+fragment:previous+' '+fragment;
}

/** Convertit des segments PDF.js en paragraphes fluides, sans introduire de HTML. */
export function pdfTextToParagraphs(items){
  if(!Array.isArray(items))return '';
  const lines=[];
  let line='',y=null,lineHeight=12,x=null,previousItem=null;
  const flush=()=>{
    const text=line.replace(/[ \t]+/gu,' ').trim();
    if(text)lines.push({text,y,height:lineHeight,x});
    line='';y=null;x=null;lineHeight=12;previousItem=null;
  };
  for(const item of items){
    if(!item||typeof item.str!=='string')continue;
    const nextY=Array.isArray(item.transform)?Number(item.transform[5]):NaN;
    const nextX=Array.isArray(item.transform)?Number(item.transform[4]):NaN;
    if(line&&Number.isFinite(y)&&Number.isFinite(nextY)&&Math.abs(nextY-y)>3.5)flush();
    if(y===null&&Number.isFinite(nextY))y=nextY;
    if(x===null&&Number.isFinite(nextX))x=nextX;
    if(Number.isFinite(item.height)&&item.height>0)lineHeight=Math.max(lineHeight,item.height);
    line=appendText(line,item.str,previousItem,item);
    previousItem=item;
    if(item.hasEOL)flush();
  }
  flush();
  if(!lines.length)return '';
  const result=[];
  let paragraph=lines[0].text;
  for(let i=1;i<lines.length;i++){
    const prev=lines[i-1],next=lines[i];
    const delta=Number.isFinite(prev.y)&&Number.isFinite(next.y)?Math.abs(prev.y-next.y):0;
    const height=Math.min(24,Math.max(10,(prev.height+next.height)/2));
    const indented=Number.isFinite(prev.x)&&Number.isFinite(next.x)&&next.x-prev.x>height*1.5;
    // Des blancs significatifs sont des séparateurs de paragraphes,
    // pas des coupures de ligne forcées par le format PDF.
    const paragraphBreak=(delta>height*1.65||indented||/^[—–]\s/u.test(next.text));
    if(paragraphBreak){result.push(paragraph.trim());paragraph=next.text}
    else paragraph+=(/[\s-]$/u.test(paragraph)||punctuationStart.test(next.text)?'':' ')+next.text;
  }
  if(paragraph.trim())result.push(paragraph.trim());
  return result.join('\n\n');
}

/** Découpe le texte en phrases courtes pour contourner les limites Web Speech. */
export function speechTextChunks(input,maxLength=190){
  const max=Math.max(60,Math.min(300,Math.floor(maxLength)));
  const text=String(input||'').replace(/\s+/gu,' ').trim();
  if(!text)return [];
  const chunks=[];
  let remaining=text;
  while(remaining.length>max){
    const sample=remaining.slice(0,max+1);
    const punctuation=[...sample.matchAll(/[.!?;:]\s+/gu)].map(match=>match.index+match[0].length);
    let cut=punctuation.filter(i=>i>=max*.40&&i<=max).pop()||0;
    if(!cut){const space=sample.lastIndexOf(' ',max);cut=space>=max*.40?space+1:max}
    const chunk=remaining.slice(0,cut).trim();
    if(chunk)chunks.push(chunk);
    remaining=remaining.slice(cut).trimStart();
  }
  if(remaining)chunks.push(remaining);
  return chunks;
}
