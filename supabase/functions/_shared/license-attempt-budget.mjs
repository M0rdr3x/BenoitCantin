// Only the verified account identifier may be passed by the route.
export async function consumeLicenseAttempt(service, userId, timeoutMs=1500) {
  if(typeof userId!=='string'||!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(userId)||
     !Number.isSafeInteger(timeoutMs)||timeoutMs<1||timeoutMs>1500)return 'unavailable';
  const controller=new AbortController();
  let timer;
  try {
    const deadline=new Promise(resolve=>{
      timer=setTimeout(()=>{controller.abort();resolve(null);},timeoutMs);
    });
    const request=Promise.resolve().then(()=>service.rpc('consume_license_attempt_budget',{p_user_id:userId}).abortSignal(controller.signal));
    const result=await Promise.race([request,deadline]);
    if(!result||result.error||typeof result.data!=='boolean')return 'unavailable';
    return result.data===true?'allowed':'limited';
  }catch{return 'unavailable';}
  finally{clearTimeout(timer);}
}
