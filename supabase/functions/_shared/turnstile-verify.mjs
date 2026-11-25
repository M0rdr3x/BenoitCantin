import { readLimitedUtf8BodyWithDeadline } from "./read-chunk-deadline.mjs";

const SITEVERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify";
const MAX_RESPONSE_BYTES = 8192;
const MAX_AGE_MS = 300_000;
const CLOCK_SKEW_MS = 30_000;

// No retry, no raw provider logs, no remote IP, no following redirects.
// An ambiguous or unavailable verification must never authorize an action.
export async function verifyTurnstileChallenge(token, secret, expectedAction, expectedHosts, timeoutMs=7000) {
  if(typeof token!=="string" || token.length<10 || token.length>2048 ||
     typeof secret!=="string" || !secret || typeof expectedAction!=="string" || !expectedAction ||
     !Array.isArray(expectedHosts) || expectedHosts.length===0 ||
     !Number.isSafeInteger(timeoutMs) || timeoutMs<1 || timeoutMs>7000) return false;
  const controller=new AbortController();
  let timer;
  try {
    const deadlineAt=performance.now()+timeoutMs;
    const deadline=new Promise(resolve=>{
      timer=setTimeout(()=>{controller.abort();resolve(false);},timeoutMs);
    });
    const verify=async()=>{
      const response=await fetch(SITEVERIFY,{
        method:"POST",body:new URLSearchParams({secret,response:token}),
        redirect:"error",credentials:"omit",referrerPolicy:"no-referrer",
        cache:"no-store",signal:controller.signal
      });
      if(controller.signal.aborted || !response.ok ||
         !/^application\/json(?:\s*;|$)/i.test(response.headers.get("content-type")||"")) return false;
      const remaining=Math.floor(deadlineAt-performance.now());
      if(remaining<1) return false;
      const limited=await readLimitedUtf8BodyWithDeadline(
        {headers:response.headers,body:response.body,signal:controller.signal},MAX_RESPONSE_BYTES,remaining);
      if(!limited.ok || controller.signal.aborted || performance.now()>=deadlineAt) return false;
      const result=JSON.parse(limited.raw);
      if(!result || typeof result!=="object" || Array.isArray(result) ||
         result.success!==true || !expectedHosts.includes(result.hostname) ||
         result.action!==expectedAction || typeof result.challenge_ts!=="string" ||
         !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})$/.test(result.challenge_ts)) return false;
      const stamp=Date.parse(result.challenge_ts);
      const age=Date.now()-stamp;
      return Number.isFinite(stamp) && age>=-CLOCK_SKEW_MS && age<=MAX_AGE_MS;
    };
    return (await Promise.race([verify(),deadline]))===true;
  }catch{return false;}
  finally{
    clearTimeout(timer);
    controller.abort();
  }
}
