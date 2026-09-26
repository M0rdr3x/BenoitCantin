export const PRIVATE_NOVEL_SIGNED_URL_SECONDS=300;

export type PrivateNovelAccess='product'|'owner'|'family';

export type PrivateNovelAsset={
  novel_id:string;
  novel_slug:string;
  title:string;
  product_slug:string|null;
  delivery_mode:'legacy_env'|'storage';
  storage_bucket:string|null;
  storage_path:string|null;
  download_name:string|null;
  total_pages:number|null;
  enabled:boolean;
};

export async function getPrivateNovelAsset(service:any,novelSlug:string):Promise<PrivateNovelAsset>{
  const slug=String(novelSlug||'').trim();
  if(!slug||slug.length>160)throw new Error('NOVEL_SLUG_INVALID');
  const {data,error}=await service.rpc('sinjira_private_novel_asset_for_delivery',{p_novel_slug:slug});
  if(error||!data)throw new Error('NOVEL_PRIVATE_ASSET_NOT_FOUND');
  return data as PrivateNovelAsset;
}

export async function requirePrivateNovelAccess(service:any,userId:string,asset:PrivateNovelAsset):Promise<PrivateNovelAccess>{
  const {data:isOwner,error:ownerError}=await service.rpc('is_sinjira_owner',{p_user_id:userId});
  if(ownerError)throw new Error('NOVEL_ACCESS_CHECK_FAILED');
  if(isOwner===true)return 'owner';

  const {data:fullCatalog,error:fullCatalogError}=await service.rpc('sinjira_has_full_catalog_access',{p_user_id:userId});
  if(fullCatalogError)throw new Error('NOVEL_ACCESS_CHECK_FAILED');
  if(fullCatalog===true)return 'family';

  const productSlug=String(asset.product_slug||'').trim();
  if(!productSlug)throw new Error('NOVEL_ACCESS_DENIED');

  const {data:hasProduct,error:productAccessError}=await service.rpc(
    'has_sinjira_product',
    {p_product_slug:productSlug,p_user_id:userId}
  );
  if(productAccessError)throw new Error('NOVEL_ACCESS_CHECK_FAILED');
  if(hasProduct===true)return 'product';

  throw new Error('NOVEL_ACCESS_DENIED');
}

export function resolvePrivateNovelStorage(asset:PrivateNovelAsset){
  if(asset.enabled!==true)throw new Error('NOVEL_PRIVATE_DELIVERY_DISABLED');

  if(asset.delivery_mode==='legacy_env'){
    if(asset.novel_slug!=='la-cendre-du-jugement')throw new Error('NOVEL_PRIVATE_STORAGE_NOT_CONFIGURED');
    const enabled=Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED')==='true';
    const bucket=(Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_BUCKET')||'').trim();
    const storagePath=(Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_PATH')||'').trim();
    if(!enabled)throw new Error('NOVEL_PRIVATE_DELIVERY_DISABLED');
    if(!bucket||!storagePath||storagePath.startsWith('/')||storagePath.includes('://')){
      throw new Error('NOVEL_PRIVATE_STORAGE_NOT_CONFIGURED');
    }
    return {bucket,storagePath};
  }

  const bucket=String(asset.storage_bucket||'').trim();
  const storagePath=String(asset.storage_path||'').trim();
  if(!bucket||!storagePath||storagePath.startsWith('/')||storagePath.includes('://')){
    throw new Error('NOVEL_PRIVATE_STORAGE_NOT_CONFIGURED');
  }
  return {bucket,storagePath};
}
