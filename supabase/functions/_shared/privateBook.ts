export const LIVRE_I_PRODUCT_SLUG='sinjira-livre-01-la-cendre-du-jugement';
export const LIVRE_I_SIGNED_URL_SECONDS=300;

export type PrivateBookAccess='product'|'owner'|'family';

export function privateBookStorageConfig(){
  const enabled=Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED')==='true';
  const bucket=(Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_BUCKET')||'').trim();
  const storagePath=(Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_PATH')||'').trim();
  if(!enabled)return {enabled:false,bucket:'',storagePath:''};
  if(!bucket||!storagePath||storagePath.startsWith('/')||storagePath.includes('://')){
    throw new Error('PRIVATE_STORAGE_NOT_CONFIGURED');
  }
  return {enabled:true,bucket,storagePath};
}

export async function requirePrivateBookAccess(service:any,userId:string):Promise<PrivateBookAccess>{
  // L'auteur/propriétaire est une identité de gestion vérifiée côté serveur.
  // Son accès au Livre I ne dépend pas de l'état commercial du produit et ne
  // crée jamais de ligne user_entitlements.
  const {data:isOwner,error:ownerError}=await service.rpc('is_sinjira_owner',{p_user_id:userId});
  if(ownerError)throw new Error('BOOK_ACCESS_CHECK_FAILED');
  if(isOwner===true)return 'owner';

  // Les comptes famille adult/youth suivent le même catalogue complet V25 que
  // les autres créations, sans fabriquer d'achat ni d'entitlement.
  const {data:fullCatalog,error:fullCatalogError}=await service.rpc(
    'sinjira_has_full_catalog_access',
    {p_user_id:userId}
  );
  if(fullCatalogError)throw new Error('BOOK_ACCESS_CHECK_FAILED');
  if(fullCatalog===true)return 'family';

  // Pour les autres membres, le helper canonique couvre entitlement actif ET
  // commande réellement payée. Une commande pending ne suffit jamais.
  const {data:hasProduct,error:productAccessError}=await service.rpc(
    'has_sinjira_product',
    {p_product_slug:LIVRE_I_PRODUCT_SLUG,p_user_id:userId}
  );
  if(productAccessError)throw new Error('BOOK_ACCESS_CHECK_FAILED');
  if(hasProduct===true)return 'product';

  throw new Error('BOOK_ACCESS_DENIED');
}
