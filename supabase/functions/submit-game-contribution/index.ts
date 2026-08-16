import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';

const clean=(v:unknown,max=160)=>String(v??'').trim().slice(0,max);
const boundedInt=(v:unknown,min=0,max=100000)=>{const n=Number(v);return Number.isFinite(n)?Math.max(min,Math.min(Math.trunc(n),max)):null};

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req),body=await req.json().catch(()=>({})),sessionId=String(body?.session_id||'').trim();
    if(!sessionId)return json({ok:false,error:'Partie manquante.'},400);
    const s=serviceClient();
    const [consentRes,sessionRes,endgameRes]=await Promise.all([
      s.from('research_consents').select('participate').eq('user_id',user.id).maybeSingle(),
      s.from('game_sessions').select('*').eq('id',sessionId).eq('user_id',user.id).maybeSingle(),
      s.from('endgame_sheets').select('fields').eq('session_id',sessionId).eq('user_id',user.id).maybeSingle()
    ]);
    const firstError=consentRes.error||sessionRes.error||endgameRes.error;if(firstError)throw firstError;
    const consent=consentRes.data,session=sessionRes.data,endgame=endgameRes.data;
    if(!consent?.participate)return json({ok:false,error:'Activez d’abord le Programme Contributeur dans votre compte.'},403);
    if(!session||!endgame)return json({ok:false,error:'Sauvegardez d’abord la Feuille de fin de partie.'},400);
    const f=endgame.fields||{};
    const rounds=Array.from({length:10},(_,i)=>{const n=i+1;return{
      round:n,
      resistance_points:clean(f[`tour_${n}_points_resistance`],40),
      reseau_mere_points:clean(f[`tour_${n}_points_reseau_mere`],40),
      resistance_won:Boolean(f[`tour_${n}_resistance_gagne`]),
      reseau_mere_won:Boolean(f[`tour_${n}_reseau_mere_gagne`])
    }});
    const playerCount=boundedInt(session.player_count,1,20);
    const metrics={
      play_mode:session.play_mode||((playerCount===1)?'solo':'multiplayer'),
      human_player_count:boundedInt(session.human_player_count??playerCount,1,20),
      effective_player_count:boundedInt(session.effective_player_count??playerCount,1,20),
      duration_minutes:boundedInt(session.duration_minutes,0,1440),
      bonus_resistance:clean(f.bonus_resistance,60),bonus_reseau_mere:clean(f.bonus_reseau_mere,60),
      total_resistance:clean(f.total_resistance,60),total_reseau_mere:clean(f.total_reseau_mere,60),
      winner:clean(f.gagnant,120),rounds
    };
    const {data:id,error}=await s.rpc('record_sinjira_contribution',{
      p_user_id:user.id,p_session_id:session.id,p_game_slug:session.game_slug,p_metrics:metrics,p_feedback:{},p_version:'3.0-endgame-only'
    });
    if(error){const duplicate=String(error.message||'').includes('déjà été partagée');return json({ok:false,error:duplicate?'Cette fin de partie a déjà été transmise.':'Transmission impossible.'},duplicate?409:500)}
    return json({ok:true,contribution_id:id,source:'endgame_only'});
  }catch(e){
    console.error('[SINJIRA contribution]',e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    return json({ok:false,error:'Erreur de transmission.'},500);
  }
});
