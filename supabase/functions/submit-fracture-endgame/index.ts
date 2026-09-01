import { corsHeaders } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

const PAID_EXTERNAL_SERVICES_ENABLED=false;
const MAX_REQUEST_BYTES=2048;
const PARTY_CODE_RE=/^[A-Z0-9-]{10}$/;
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
  try{body=JSON.parse(raw);}catch{throw new Error('INVALID_JSON');}
  if(!body||typeof body!=='object'||Array.isArray(body))throw new Error('INVALID_JSON');
  return body as Record<string,unknown>;
}

function cleanText(v:unknown,max=300){return String(v??'').trim().slice(0,max);}
function num(v:unknown){const n=Number(v);return Number.isFinite(n)?n:0;}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.',code:'METHOD_NOT_ALLOWED'},405);
  try{
    const user=await requiredUser(req);
    const body=await readBoundedJson(req);
    const code=typeof body.party_code==='string'?body.party_code.trim().toUpperCase():'';
    if(!PARTY_CODE_RE.test(code))return privateJson({ok:false,error:'Code de partie invalide.',code:'INVALID_PARTY_CODE'},400);

    const s=serviceClient();
    const {data:party,error:partyError}=await s
      .from('fracture_parties')
      .select('id,party_code,owner_user_id,human_player_count,effective_player_count,play_mode,round_count')
      .eq('party_code',code)
      .maybeSingle();
    if(partyError)throw new Error('PARTY_LOOKUP_FAILED');
    if(!party)return privateJson({ok:false,error:'Partie introuvable.',code:'PARTY_NOT_FOUND'},404);
    if(party.owner_user_id!==user.id)return privateJson({ok:false,error:'Seul le créateur de la partie peut transmettre la fin de partie.',code:'OWNER_REQUIRED'},403);

    const [{data:report,error:reportError},{data:session,error:sessionError}]=await Promise.all([
      s.from('fracture_endgame_reports').select('fields').eq('party_id',party.id).maybeSingle(),
      s.from('game_sessions').select('id').eq('user_id',user.id).eq('game_slug','fracture-du-reseau-mere').eq('party_code',party.party_code).maybeSingle()
    ]);
    if(reportError||sessionError)throw new Error('ENDGAME_LOOKUP_FAILED');
    if(!report)return privateJson({ok:false,error:'Sauvegardez la Feuille de fin de partie avant de la transmettre.',code:'ENDGAME_REQUIRED'},400);
    if(!session)return privateJson({ok:false,error:'Session de partie introuvable.',code:'SESSION_NOT_FOUND'},409);

    const f=report.fields||{};
    const rounds:any[]=[];
    for(let i=1;i<=party.round_count;i++)rounds.push({
      round:i,
      resistance:num(f[`r${i}_resistance`]),
      network:num(f[`r${i}_network`]),
      winner:cleanText(f[`r${i}_winner`],4)
    });
    const metrics={
      human_player_count:party.human_player_count,
      effective_player_count:party.effective_player_count,
      play_mode:party.play_mode,
      round_count:party.round_count,
      network_agents:num(f.network_agents),
      rounds,
      bonus_resistance:num(f.bonus_resistance),
      bonus_network:num(f.bonus_network),
      rounds_resistance:num(f.rounds_resistance),
      rounds_network:num(f.rounds_network),
      rounds_tied:num(f.rounds_tied),
      total_resistance:num(f.total_resistance),
      total_network:num(f.total_network),
      winner_final:cleanText(f.winner_final,80),
      tiebreak_required:cleanText(f.tiebreak_required,8)
    };

    const {error:recordError}=await s.rpc('record_sinjira_fracture_endgame_contribution',{
      p_user_id:user.id,
      p_session_id:session.id,
      p_party_id:party.id,
      p_metrics:metrics,
      p_version:'fracture-endgame-v9'
    });
    if(recordError){
      const duplicate=recordError.message?.includes('déjà été partagée');
      console.error('[submit-fracture-endgame] record RPC',recordError);
      return privateJson({
        ok:false,
        error:duplicate?'Cette fin de partie a déjà été transmise.':'Transmission de la fin de partie impossible.',
        code:duplicate?'ALREADY_SUBMITTED':'SUBMISSION_FAILED'
      },duplicate?409:500);
    }

    // Transport courriel préparé mais volontairement inactif tant qu'un service payant
    // n'a pas été explicitement autorisé et activé séparément.
    let email_sent=false;
    if(PAID_EXTERNAL_SERVICES_ENABLED){
      const resend=Deno.env.get('RESEND_API_KEY');
      const from=Deno.env.get('REPORT_FROM_EMAIL');
      const to=Deno.env.get('FRACTURE_REPORT_TO_EMAIL');
      if(resend&&from&&to){
        const bodyText=[
          `Fracture du Réseau-Mère — fin de partie ${party.party_code}`,
          `Humains : ${party.human_player_count}`,
          `Sièges effectifs : ${party.effective_player_count}`,
          `Format : ${party.round_count} rondes`,
          `Agents Réseau-Mère : ${metrics.network_agents}`,
          `Total Résistance : ${metrics.total_resistance}`,
          `Total Réseau-Mère : ${metrics.total_network}`,
          `Rondes gagnées R : ${metrics.rounds_resistance}`,
          `Rondes gagnées RM : ${metrics.rounds_network}`,
          `Égalités : ${metrics.rounds_tied}`,
          `Gagnant : ${metrics.winner_final}`,
          `Départage : ${metrics.tiebreak_required}`
        ].join('\n');
        const r=await fetch('https://api.resend.com/emails',{
          method:'POST',
          headers:{Authorization:`Bearer ${resend}`,'Content-Type':'application/json'},
          body:JSON.stringify({from,to:[to],subject:`SINJIRA — Fin de partie ${party.party_code}`,text:bodyText})
        });
        email_sent=r.ok;
      }
    }

    return privateJson({ok:true,submitted:true,email_sent,paid_external_services_enabled:PAID_EXTERNAL_SERVICES_ENABLED});
  }catch(e){
    console.error('[submit-fracture-endgame]',e);
    if(e?.message==='AUTH_REQUIRED')return privateJson({ok:false,error:'Connexion requise.',code:'AUTH_REQUIRED'},401);
    if(e?.message==='JSON_REQUIRED')return privateJson({ok:false,error:'Corps JSON requis.',code:'JSON_REQUIRED'},415);
    if(e?.message==='REQUEST_TOO_LARGE')return privateJson({ok:false,error:'Requête trop volumineuse.',code:'REQUEST_TOO_LARGE'},413);
    if(e?.message==='INVALID_JSON')return privateJson({ok:false,error:'JSON invalide.',code:'INVALID_JSON'},400);
    if(e?.message==='PARTY_LOOKUP_FAILED'||e?.message==='ENDGAME_LOOKUP_FAILED')return privateJson({ok:false,error:'État de partie temporairement indisponible.',code:e.message},503);
    return privateJson({ok:false,error:'Transmission de la fin de partie impossible.',code:'SUBMISSION_FAILED'},500);
  }
});
