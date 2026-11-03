// Projet Nova — consultation publique agrégée (écritures interdites si secrets / contrôle anti-bot absents).
// Aucun bulletin individuel, identité, IP ou choix politique n'est journalisé ou enregistré.
const VERSION = "nova-consultation-v1";
const ORIGINS = new Set(["https://www.benoitcantin.com","https://benoitcantin.com"]);
const MAX_BODY_BYTES = 8192;
const OPTIONS = new Set([-2,-1,0,1,2,9]);
const MIN_PUBLIC_BALLOTS = 10;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const CAPTCHA_SECRET = Deno.env.get("NOVA_POLL_TURNSTILE_SECRET") || "";
const CAPTCHA_SITE_KEY = Deno.env.get("NOVA_POLL_TURNSTILE_SITE_KEY") || "";
const HMAC_KEY = Deno.env.get("NOVA_POLL_HMAC_KEY") || "";
// Une activation accidentelle du flag ne suffit jamais : le corpus final
// doit avoir été approuvé explicitement dans la configuration serveur.
const isOpen = () => Deno.env.get("NOVA_POLL_APPROVED_VERSION") === VERSION
  && Deno.env.get("NOVA_POLL_ENABLED") === "true"
  && !!CAPTCHA_SECRET && !!CAPTCHA_SITE_KEY && HMAC_KEY.length >= 32 && !!SERVICE_KEY;

function respond(status: number, data: unknown, origin: string | null): Response {
  const headers = new Headers({
    "Content-Type":"application/json; charset=utf-8",
    "Cache-Control":"no-store, private",
    "X-Content-Type-Options":"nosniff",
    "Referrer-Policy":"no-referrer",
    "Vary":"Origin"
  });
  if(origin && ORIGINS.has(origin)) {
    headers.set("Access-Control-Allow-Origin",origin);
    headers.set("Access-Control-Allow-Methods","GET, POST, OPTIONS");
    headers.set("Access-Control-Allow-Headers","content-type");
  }
  return new Response(status===204 ? null : JSON.stringify(data),{status,headers});
}
async function readLimitedJson(req: Request): Promise<unknown> {
  if(!req.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
    throw new Error("type");
  }
  const reader = req.body?.getReader();
  if(!reader) throw new Error("body");
  let size=0; const chunks: Uint8Array[]=[];
  try {
    while(true) {
      const {done,value}=await reader.read();
      if(done) break;
      size+=value.byteLength;
      if(size>MAX_BODY_BYTES) { await reader.cancel(); throw new Error("size"); }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const buffer = new Uint8Array(size); let offset=0;
  for(const chunk of chunks) {buffer.set(chunk,offset);offset+=chunk.byteLength;}
  return JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(buffer));
}
async function db(path: string, init: RequestInit={}) {
  if(!SUPABASE_URL || !SERVICE_KEY) throw new Error("backend_unavailable");
  const url=SUPABASE_URL.replace(/\/$/,"")+"/rest/v1/"+path;
  const response=await fetch(url,{
    ...init,
    headers:{
      "apikey":SERVICE_KEY,"Authorization":"Bearer "+SERVICE_KEY,
      "Content-Type":"application/json","Accept":"application/json",...(init.headers||{})
    },
    signal:AbortSignal.timeout(7000)
  });
  if(!response.ok) throw new Error("database_unavailable");
  return response.status === 204 ? null : response.json();
}
async function publicResults() {
  const [questions,counts,publications] = await Promise.all([
    db("nova_poll_questions?poll_version=eq."+VERSION+"&select=question_id,ordinal,question_text&order=ordinal.asc"),
    db("nova_poll_public_counts?poll_version=eq."+VERSION+"&select=question_id,option_value,total"),
    db("nova_poll_publication_state?poll_version=eq."+VERSION+"&select=published_ballots,published_at")
  ]);
  if(!Array.isArray(questions) || questions.length!==8 || !Array.isArray(counts)
     || !Array.isArray(publications) || publications.length!==1) throw new Error("not_ready");
  const countsById = new Map<string,number[]>();
  for(const q of questions) countsById.set(q.question_id,Array(6).fill(0));
  const values=[-2,-1,0,1,2,9];
  for(const row of counts) {
    if(!countsById.has(row.question_id)) continue;
    const ix=values.indexOf(Number(row.option_value));
    if(ix>=0 && Number.isSafeInteger(Number(row.total))) countsById.get(row.question_id)![ix]=Number(row.total);
  }
  const snapshot=publications[0];
  const ballotCount=Number(snapshot.published_ballots);
  if(!Number.isSafeInteger(ballotCount) || ballotCount<0) throw new Error("invalid_publication");
  const showCounts=ballotCount>=MIN_PUBLIC_BALLOTS;
  return {
    version: VERSION, open:isOpen(), siteKey:isOpen()?CAPTCHA_SITE_KEY:null,
    eligibility:"18+ déclaré", method:"consultation ouverte non probabiliste",
    minPublicBallots:MIN_PUBLIC_BALLOTS, ballots:showCounts?ballotCount:null,
    resultsVisible:showCounts,
    publishedAt:showCounts ? snapshot.published_at : null,
    publication: "lots d au moins dix nouveaux bulletins; publication au plus une fois par six heures",
    questions:questions.map(q=>({
      id:q.question_id,ordinal:q.ordinal,text:q.question_text,
      counts:showCounts?Object.fromEntries(values.map((v,i)=>[String(v),countsById.get(q.question_id)![i]])):null
    }))
  };
}
async function confirmCaptcha(token: string) {
  const params=new URLSearchParams({secret:CAPTCHA_SECRET,response:token});
  const response=await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify",{
    method:"POST",body:params,signal:AbortSignal.timeout(7000)
  });
  if(!response.ok) return false;
  const result=await response.json();
  return result.success===true
    && (result.hostname==="www.benoitcantin.com" || result.hostname==="benoitcantin.com")
    && result.action==="nova_poll_vote";
}
async function hashToken(token: string) {
  const key=await crypto.subtle.importKey("raw",new TextEncoder().encode(HMAC_KEY),
    {name:"HMAC",hash:"SHA-256"},false,["sign"]);
  const bytes=new Uint8Array(await crypto.subtle.sign("HMAC",key,new TextEncoder().encode(VERSION+":"+token)));
  return Array.from(bytes,b=>b.toString(16).padStart(2,"0")).join("");
}
Deno.serve(async (req:Request)=>{
  const origin=req.headers.get("origin");
  // N'autoriser que les origines de l'interface publique; aucune intégration tierce.
  if(!origin || !ORIGINS.has(origin)) return respond(403,{error:"origine_non_autorisee"},null);
  if(req.method==="OPTIONS") return respond(204,null,origin);
  if(req.method==="GET") {
    try { return respond(200,await publicResults(),origin); }
    catch { return respond(503,{error:"resultats_temporairement_indisponibles"},origin); }
  }
  if(req.method!=="POST") return respond(405,{error:"methode_non_autorisee"},origin);
  if(!isOpen()) return respond(503,{error:"consultation_non_ouverte"},origin);
  let payload: any;
  try { payload=await readLimitedJson(req); }
  catch { return respond(400,{error:"bulletin_invalide"},origin); }
  if(!payload || typeof payload!=="object" || Array.isArray(payload)
      || payload.version!==VERSION || payload.ageConfirmed!==true
      || typeof payload.ballotToken!=="string" || !/^[0-9a-f]{48}$/.test(payload.ballotToken)
      || typeof payload.captchaToken!=="string" || payload.captchaToken.length<10 || payload.captchaToken.length>4096
      || !payload.answers || typeof payload.answers!=="object" || Array.isArray(payload.answers)
      || Object.keys(payload.answers).length!==8
      || Object.values(payload.answers).some(x=>typeof x!=="number" || !OPTIONS.has(x))) {
    return respond(400,{error:"bulletin_invalide"},origin);
  }
  try {
    const questions=await db("nova_poll_questions?poll_version=eq."+VERSION+"&select=question_id");
    const expected=new Set(questions.map((q:any)=>q.question_id));
    if(expected.size!==8 || Object.keys(payload.answers).some(key=>!expected.has(key))) {
      return respond(400,{error:"questions_incompatibles"},origin);
    }
    if(!await confirmCaptcha(payload.captchaToken)) return respond(403,{error:"verification_anti_robot_echouee"},origin);
    const tokenHash=await hashToken(payload.ballotToken);
    const result=await db("rpc/nova_poll_submit",{
      method:"POST",
      body:JSON.stringify({p_version:VERSION,p_token_hash:tokenHash,p_answers:payload.answers})
    });
    if(result==="duplicate") return respond(409,{error:"bulletin_deja_recu"},origin);
    if(result!=="accepted") throw new Error("submission_failure");
    return respond(201,{status:"accepted"},origin);
  } catch {
    return respond(503,{error:"soumission_temporairement_indisponible"},origin);
  }
});
