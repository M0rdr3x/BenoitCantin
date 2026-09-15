export const LIVRE_I_PRODUCT_SLUG='sinjira-livre-01-la-cendre-du-jugement';
export const LIVRE_I_SIGNED_URL_SECONDS=300;

export type PrivateBookAccess='entitlement'|'owner';

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
  const {data:product,error:productError}=await service
    .from('products')
    .select('id,slug,active')
    .eq('slug',LIVRE_I_PRODUCT_SLUG)
    .eq('active',true)
    .maybeSingle();
  if(productError||!product)throw new Error('BOOK_UNAVAILABLE');

  const {data:entitlement,error:entitlementError}=await service
    .from('user_entitlements')
    .select('product_id')
    .eq('user_id',userId)
    .eq('product_id',product.id)
    .maybeSingle();
  if(entitlementError)throw new Error('BOOK_ACCESS_CHECK_FAILED');
  if(entitlement)return 'entitlement';

  const {data:isOwner,error:ownerError}=await service.rpc('is_sinjira_owner',{p_user_id:userId});
  if(ownerError)throw new Error('BOOK_ACCESS_CHECK_FAILED');
  if(isOwner===true)return 'owner';

  throw new Error('BOOK_ACCESS_DENIED');
}
