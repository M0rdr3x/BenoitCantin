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

const clean=(v:unknown,max=160)=>String(v??'').trim().slice(0,max);

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.',code:'METHOD_NOT_ALLOWED'},405);
  try{
    const user=await requiredUser(req);
    const body=await readBoundedJson(req);
    const sessionId=typeof body.session_id==='string'?body.session_id.trim():'';
    if(!UUID_RE.test(sessionId))return privateJson({ok:false,error:'Partie invalide.',code:'INVALID_SESSION'},400);

    const s=serviceClient();
    const [{data:consent},{data:session},{data:endgame}]=await Promise.all([
      s.from('research_consents').select('participate').eq('user_id',user.id).maybeSingle(),
      s.from('game_sessions')
        .select('id,game_slug,play_mode,human_player_count,effective_player_count,player_count,duration_minutes')
        .eq('id',sessionId).eq('user_id',user.id).maybeSingle(),
      s.from('endgame_sheets').select('fields').eq('session_id',sessionId).eq('user_id',user.id).maybeSingle()
    ]);

    if(!consent?.participate)return privateJson({ok:false,error:'Activez d’abord le Programme Contributeur dans votre compte.',code:'CONTRIBUTION_CONSENT_REQUIRED'},403);
    if(!session||!endgame)return privateJson({ok:false,error:'Sauvegardez d’abord la Feuille de fin de partie.',code:'ENDGAME_REQUIRED'},400);

    const f=endgame.fields||{};
    const rounds=Array.from({length:10},(_,i)=>{
      const n=i+1;
      return {
        round:n,
        resistance_points:clean(f[`tour_${n}_points_resistance`],40),
        reseau_mere_points:clean(f[`tour_${n}_points_reseau_mere`],40),
        resistance_won:Boolean(f[`tour_${n}_resistance_gagne`]),
        reseau_mere_won:Boolean(f[`tour_${n}_reseau_mere_gagne`])
      };
    });

    const metrics={
      play_mode:session.play_mode||((session.player_count===1)?'solo':'multiplayer'),
      human_player_count:session.human_player_count??session.player_count??null,
      effective_player_count:session.effective_player_count??session.player_count??null,
      duration_minutes:session.duration_minutes??null,
      bonus_resistance:clean(f.bonus_resistance,60),
      bonus_reseau_mere:clean(f.bonus_reseau_mere,60),
      total_resistance:clean(f.total_resistance,60),
      total_reseau_mere:clean(f.total_reseau_mere,60),
      winner:clean(f.gagnant,120),
      rounds
    };

    const {error}=await s.rpc('record_sinjira_contribution',{
      p_user_id:user.id,
      p_session_id:session.id,
      p_game_slug:session.game_slug,
      p_metrics:metrics,
      p_feedback:{},
      p_version:'3.0-endgame-only'
    });
    if(error){
      const duplicate=error.message?.includes('déjà été partagée');
      return privateJson({
        ok:false,
        error:duplicate?'Cette fin de partie a déjà été transmise.':'Transmission impossible.',
        code:duplicate?'ALREADY_SUBMITTED':'SUBMISSION_FAILED'
      },duplicate?409:500);
    }

    return privateJson({ok:true,submitted:true,source:'endgame_only'});
  }catch(e){
    console.error('[submit-game-contribution]',e);
    if(e?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(e?.message==='JSON_REQUIRED')return privateJson({ok:false,error:'Corps JSON requis.',code:'JSON_REQUIRED'},415);
    if(e?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE'},413);
    if(e?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON'},400);
    return privateJson({ok:false,error:'Erreur de transmission.',code:'SUBMISSION_FAILED'},500);
  }
});
