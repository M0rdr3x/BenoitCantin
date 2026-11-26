// REVIEW ONLY: candidate, not imported by any deployed Edge handler.
// Supply a dedicated server-only client configured with db.retry=false.
// No client-supplied identity: userId must come from verified server Auth.
export async function consumeRegistryPhotoBudget(service,userId,timeoutMs=1500){
  if(typeof userId!=='string'||! /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(userId)||
    userId.length!==36||userId==='00000000-0000-0000-0000-000000000000'||
    !Number.isSafeInteger(timeoutMs)||timeoutMs<1||timeoutMs>1500)return 'unavailable';
  const controller=new AbortController();
  let timer;
  try{
    const timeout=new Promise(resolve=>{
      timer=setTimeout(()=>{controller.abort();resolve(null)},timeoutMs);
    });
    const request=Promise.resolve().then(()=>service.rpc('consume_registry_photo_budget',{p_user_id:userId}).abortSignal(controller.signal));
    const result=await Promise.race([request,timeout]);
    if(!result||typeof result!=='object'||Array.isArray(result)||result.error!==null||typeof result.data!=='boolean')return 'unavailable';
    return result.data===true?'allowed':'limited';
  }catch{return 'unavailable'}
  finally{clearTimeout(timer)}
}
