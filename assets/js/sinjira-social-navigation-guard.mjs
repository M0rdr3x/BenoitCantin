// Lien relatif à l'origine du site uniquement. Aucun traitement d'URL fourni
// par les notifications ou la page d'acceptation des règles ne fait confiance
// aux seules chaînes commençant par une barre oblique.
export function safeSocialDestination(value,{origin,scopes=[]}={}){
  if(typeof value!=='string'||!value||value.length>2048||
     value!==value.trim()||!value.startsWith('/')||value.startsWith('//')||
     /[\u0000-\u0020\u007f\\]/.test(value))return '';
  const rawPath=value.split(/[?#]/,1)[0];
  if(/%(?:0[0-9a-f]|1[0-9a-f]|2f|5c|7f)/i.test(rawPath))return '';
  try{
    const base=new URL(origin);
    if(base.protocol!=='https:'||base.username||base.password)return '';
    const target=new URL(value,base);
    if(target.origin!==base.origin||target.username||target.password||
       target.pathname!==rawPath)return '';
    if(!Array.isArray(scopes)||!scopes.every(scope=>
      typeof scope==='string'&&scope.startsWith('/')&&!scope.startsWith('//')
    ))return '';
    if(scopes.length&&!scopes.some(scope=>target.pathname.startsWith(scope)))return '';
    return target.pathname+target.search+target.hash;
  }catch{return ''}
}
