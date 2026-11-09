// Frontière de confiance des liens de documents renvoyés par les Edge Functions.
// Les contrôles d'accès restent serveur : cette vérification côté navigateur
// refuse les protocoles exécutables et les liens signés vers d'autres origines.
export function resolveDocumentUrl(value,{siteOrigin,storageOrigin,protectedDocument}={}){
  if(typeof value!=='string'||!value||value.length>2048||
     /[\u0000-\u0020\u007f\\]/.test(value))return null;
  if(protectedDocument!==true&&protectedDocument!==false)return null;
  const relative=value.startsWith('/');
  if(relative&&value.startsWith('//'))return null;
  if(!relative&&!/^https:\/\//i.test(value))return null;
  try{
    const site=new URL(siteOrigin),storage=new URL(storageOrigin);
    if(site.protocol!=='https:'||storage.protocol!=='https:'||
       site.username||site.password||storage.username||storage.password)return null;
    const target=new URL(value,site);
    if(target.protocol!=='https:'||target.username||target.password)return null;
    if(relative&&(target.origin!==site.origin||
       target.pathname!==value.split(/[?#]/,1)[0]))return null;
    if(protectedDocument&&(relative||target.origin!==storage.origin||
       !target.pathname.startsWith('/storage/v1/object/sign/')))return null;
    return target.href;
  }catch{return null}
}
