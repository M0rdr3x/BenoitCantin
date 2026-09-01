import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

const MAX_REQUEST_BYTES=2048;
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const PRIVATE_HEADERS={
  ...corsHeaders,
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'private, no-store, max-age=0',
  'Pragma':'no-cache',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer'
};

function privateJson(data:unknown,status=200){
  return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS});
}

async function readBoundedJson(req:Request){
  const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
  if(contentType!=='application/json')throw new Error('JSON_REQUIRED');

  const declaredRaw=req.headers.get('content-length');
  if(declaredRaw){
    const declared=Number(declaredRaw);
    if(Number.isFinite(declared)&&declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');
  }

  const raw=await req.text();
  if(new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');

  let body:unknown;
  try{ body=JSON.parse(raw); }
  catch{ throw new Error('INVALID_JSON'); }
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body as Record<string,unknown>;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return privateJson({ok:false,error:'Méthode non autorisée.',code:'METHOD_NOT_ALLOWED'},405);
  try {
    const user = await requiredUser(req);
    const body = await readBoundedJson(req);

    if('all' in body && typeof body.all!=='boolean'){
      return privateJson({ok:false,error:'Le champ all doit être booléen.',code:'INVALID_SCOPE'},400);
    }

    const revokeAll=body.all===true;
    const sessionId=typeof body.session_id==='string'?body.session_id.trim():'';

    if(revokeAll && sessionId){
      return privateJson({ok:false,error:'Choisissez soit toutes les contributions, soit une session précise.',code:'AMBIGUOUS_SCOPE'},400);
    }
    if(!revokeAll && !UUID_RE.test(sessionId)){
      return privateJson({ok:false,error:'Une session valide est requise.',code:'SESSION_REQUIRED'},400);
    }

    const service = serviceClient();
    const { data, error } = await service.rpc('revoke_sinjira_contributions', {
      p_user_id: user.id,
      p_session_id: revokeAll ? null : sessionId
    });
    if (error) {
      console.error('[revoke-my-contributions] RPC failed',error);
      return privateJson({ ok: false, error: 'Révocation impossible.',code:'REVOCATION_FAILED' }, 500);
    }
    return privateJson({ ok: true, removed: data || 0, scope: revokeAll ? 'all' : 'session' });
  } catch (error) {
    console.error('[revoke-my-contributions]',error);
    if (error?.message === 'AUTH_REQUIRED') return privateJson({ ok: false, error: 'Connexion requise.',code:'AUTH_REQUIRED' }, 401);
    if (error?.message === 'JSON_REQUIRED') return privateJson({ ok: false, error: 'Corps JSON requis.',code:'JSON_REQUIRED' }, 415);
    if (error?.message === 'REQUEST_TOO_LARGE') return privateJson({ ok: false, error: 'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE' }, 413);
    if (error?.message === 'INVALID_JSON') return privateJson({ ok: false, error: 'JSON invalide.',code:'INVALID_JSON' }, 400);
    return privateJson({ ok: false, error: 'Erreur.',code:'REVOCATION_FAILED' }, 500);
  }
});
