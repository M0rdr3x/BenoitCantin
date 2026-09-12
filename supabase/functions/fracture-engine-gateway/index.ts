import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { corsHeaders } from '../_shared/cors.ts';

const GATEWAY_VERSION='24.4.15';
const MAX_BODY_BYTES=32_000;
const PARTY_RE=/^FRM-[A-Z0-9]{6}$/;

const ALLOWED_ACTIONS=new Set([
  'fracture_engine_start',
  'fracture_engine_submit_keep',
  'fracture_engine_pick',
  'fracture_engine_submit_report',
  'fracture_engine_submit_accusation'
]);

const PRIVATE_HEADERS={
  ...corsHeaders,
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  'Pragma':'no-cache',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer'
};

type JsonRecord=Record<string,unknown>;

function privateJson(data:unknown,status=200){
  return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS});
}

function asInt(value:unknown,name:string){
  const n=Number(value);
  if(!Number.isInteger(n)||n<=0) throw new Error(`INVALID_${name.toUpperCase()}`);
  return n;
}

function asIntArray(value:unknown,name:string,min:number,max:number){
  if(!Array.isArray(value)) throw new Error(`INVALID_${name.toUpperCase()}`);
  const out=[...new Set(value.map(v=>asInt(v,name)))];
  if(out.length<min||out.length>max) throw new Error(`INVALID_${name.toUpperCase()}`);
  return out;
}

function normalizeArgs(action:string,input:JsonRecord,partyCode:string):JsonRecord{
  switch(action){
    case 'fracture_engine_start':
      return {p_party_code:partyCode};

    case 'fracture_engine_submit_keep':
      return {
        p_party_code:partyCode,
        p_card_ids:asIntArray(input.p_card_ids,'card_ids',2,2)
      };

    case 'fracture_engine_pick':
      return {
        p_party_code:partyCode,
        p_card_id:asInt(input.p_card_id,'card_id')
      };

    case 'fracture_engine_submit_report':{
      const report=String(input.p_report||'').toUpperCase();
      if(!['R','RM','EQ'].includes(report)) throw new Error('INVALID_REPORT');
      const proof=input.p_proof_card_id==null||input.p_proof_card_id===''?null:asInt(input.p_proof_card_id,'proof_card_id');
      return {
        p_party_code:partyCode,
        p_report:report,
        p_suspect_seat:asInt(input.p_suspect_seat,'suspect_seat'),
        p_proof_card_id:proof
      };
    }

    case 'fracture_engine_submit_accusation':
      return {
        p_party_code:partyCode,
        p_accused_seats:asIntArray(input.p_accused_seats,'accused_seats',1,20)
      };

    default:
      throw new Error('ACTION_NOT_ALLOWED');
  }
}

function publicError(message:string){
  const upper=message.toUpperCase();
  if(upper.includes('ALREADY_SUBMITTED')) return 'Cette action a déjà été enregistrée et ne peut plus être modifiée.';
  if(upper.includes('NOT_YOUR_TURN')) return 'Ce n’est pas votre tour.';
  if(upper.includes('NOT_MEMBER')||upper.includes('UNAUTHORIZED')||upper.includes('FORBIDDEN')) return 'Vous n’avez pas accès à cette partie.';
  if(upper.includes('INVALID_')) return 'Les données de cette action sont invalides.';
  if(upper.includes('GAME_FINISHED')) return 'Cette partie est déjà terminée.';
  return 'Action refusée par le moteur de jeu.';
}

async function readLimitedJson(req:Request):Promise<{body?:JsonRecord;response?:Response}>{
  const contentType=(req.headers.get('content-type')||'').toLowerCase();
  if(!contentType.startsWith('application/json')){
    return {response:privateJson({ok:false,error:'Content-Type application/json requis.',gateway_version:GATEWAY_VERSION},415)};
  }

  const rawLength=req.headers.get('content-length');
  if(rawLength!==null){
    const declaredLength=Number(rawLength);
    if(Number.isFinite(declaredLength)&&declaredLength>MAX_BODY_BYTES){
      return {response:privateJson({ok:false,error:'Requête trop volumineuse.',gateway_version:GATEWAY_VERSION},413)};
    }
  }

  const raw=await req.text();
  if(new TextEncoder().encode(raw).byteLength>MAX_BODY_BYTES){
    return {response:privateJson({ok:false,error:'Requête trop volumineuse.',gateway_version:GATEWAY_VERSION},413)};
  }

  let parsed:unknown;
  try{
    parsed=JSON.parse(raw||'{}');
  }catch{
    return {response:privateJson({ok:false,error:'JSON invalide.',gateway_version:GATEWAY_VERSION},400)};
  }
  if(!parsed||typeof parsed!=='object'||Array.isArray(parsed)){
    return {response:privateJson({ok:false,error:'Corps JSON invalide.',gateway_version:GATEWAY_VERSION},400)};
  }
  return {body:parsed as JsonRecord};
}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS') return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST') return privateJson({ok:false,error:'Méthode non autorisée.',gateway_version:GATEWAY_VERSION},405);

  const authorization=req.headers.get('Authorization')||'';
  if(!authorization.startsWith('Bearer ')) return privateJson({ok:false,error:'Connexion requise.',gateway_version:GATEWAY_VERSION},401);

  const supabaseUrl=Deno.env.get('SUPABASE_URL');
  const anonKey=Deno.env.get('SUPABASE_ANON_KEY');
  if(!supabaseUrl||!anonKey){
    console.error('[fracture-engine-gateway]',{code:'FRACTURE_GATEWAY_CONFIG_MISSING'});
    return privateJson({ok:false,error:'Service de jeu indisponible.',gateway_version:GATEWAY_VERSION},503);
  }

  try{
    const client=createClient(supabaseUrl,anonKey,{
      global:{headers:{Authorization:authorization}},
      auth:{persistSession:false,autoRefreshToken:false,detectSessionInUrl:false}
    });

    // Vérification explicite avant toute lecture du corps : un JWT invalide ne
    // peut pas forcer le serveur à parser ou tamponner une requête applicative.
    const token=authorization.slice(7);
    const {data:userData,error:userError}=await client.auth.getUser(token);
    if(userError||!userData?.user) return privateJson({ok:false,error:'Session invalide ou expirée.',gateway_version:GATEWAY_VERSION},401);

    const parsed=await readLimitedJson(req);
    if(parsed.response) return parsed.response;
    const body=parsed.body||{};

    const action=String(body.action||'');
    if(!ALLOWED_ACTIONS.has(action)) return privateJson({ok:false,error:'Action non autorisée.',gateway_version:GATEWAY_VERSION},400);

    const rawArgs=(body.args&&typeof body.args==='object'&&!Array.isArray(body.args))?body.args as JsonRecord:{};
    const partyCode=String(rawArgs.p_party_code||'').trim().toUpperCase();
    if(!PARTY_RE.test(partyCode)) return privateJson({ok:false,error:'Code de partie invalide.',gateway_version:GATEWAY_VERSION},400);

    const args=normalizeArgs(action,rawArgs,partyCode);
    const {error:actionError}=await client.rpc(action,args);
    if(actionError){
      console.warn('[fracture-engine-gateway]',{code:'FRACTURE_ACTION_REJECTED',action});
      return privateJson({ok:false,error:publicError(actionError.message||''),gateway_version:GATEWAY_VERSION},400);
    }

    // On ignore volontairement la réponse brute de l'action. Elle ne traverse
    // jamais la frontière serveur -> navigateur. On relit l'état via la RPC
    // de confidentialité qui retire identités et soupçons non autorisés.
    const {data:state,error:stateError}=await client.rpc('fracture_engine_get_state_safe',{p_party_code:partyCode});
    if(stateError){
      console.error('[fracture-engine-gateway]',{code:'FRACTURE_STATE_LOAD_FAILED'});
      return privateJson({ok:false,error:'La partie a été modifiée, mais son nouvel état ne peut pas être chargé.',gateway_version:GATEWAY_VERSION},502);
    }

    if(state&&typeof state==='object'&&!Array.isArray(state)){
      return privateJson({...state,gateway_version:GATEWAY_VERSION});
    }
    return privateJson({ok:false,error:'État de partie invalide.',gateway_version:GATEWAY_VERSION},502);
  }catch(error){
    const message=error instanceof Error?error.message:'';
    console.error('[fracture-engine-gateway]',{code:'FRACTURE_GATEWAY_REQUEST_REJECTED'});
    return privateJson({ok:false,error:publicError(message),gateway_version:GATEWAY_VERSION},400);
  }
});
