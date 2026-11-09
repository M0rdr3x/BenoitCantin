// Les chemins de romans proviennent de métadonnées Supabase. Échapper les
// caractères HTML ne désactive pas les protocoles exécutables dans href.
// Le contrôle d'accès aux éditions privées demeure entièrement côté serveur.
export function safeNovelHref(value,origin){
  if(typeof value!=='string'||!value||value.length>2048||
     value!==value.trim()||!value.startsWith('/')||value.startsWith('//')||
     /[\u0000-\u0020\u007f\\]/.test(value))return '';
  const rawPath=value.split(/[?#]/,1)[0];
  // Les séparateurs encodés, les caractères de contrôle et les chemins
  // à plusieurs niveaux d'encodage ne sont pas des routes canoniques.
  if(/%(?:0[0-9a-f]|1[0-9a-f]|25|2e|2f|5c|7f)/i.test(rawPath))return '';
  try{
    const base=new URL(origin),target=new URL(value,base);
    if(base.protocol!=='https:'||base.username||base.password||
       target.origin!==base.origin||target.username||target.password||
       target.pathname!==rawPath)return '';
    if(!target.pathname.startsWith('/compte/')&&
       !target.pathname.startsWith('/projets/sinjira/'))return '';
    return target.pathname+target.search+target.hash;
  }catch{return ''}
}
