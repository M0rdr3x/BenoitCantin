import {corsHeaders,json} from '../_shared/cors.ts';
import {requiredUser,serviceClient} from '../_shared/auth.ts';

function cleanText(v:unknown,max=300){return String(v??'').trim().slice(0,max)}
function num(v:unknown,min=-100000,max=100000){const n=Number(v);return Number.isFinite(n)?Math.max(min,Math.min(n,max)):0}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const user=await requiredUser(req),s=serviceClient(),body=await req.json().catch(()=>({})),code=cleanText(body?.party_code,10).toUpperCase();
    if(!/^FRM-[A-Z0-9]{6}$/.test(code))return json({ok:false,error:'Code de partie invalide.'},400);
    const {data:party,error:partyError}=await s.from('fracture_parties').select('*').eq('party_code',code).maybeSingle();
    if(partyError)throw partyError;
    if(!party)return json({ok:false,error:'Partie introuvable.'},404);
    if(party.owner_user_id!==user.id)return json({ok:false,error:'Seul le créateur de la partie peut transmettre la fin de partie.'},403);
    const {data:report,error:reportError}=await s.from('fracture_endgame_reports').select('*').eq('party_id',party.id).maybeSingle();
    if(reportError)throw reportError;
    if(!report)return json({ok:false,error:'Sauvegardez la Feuille de fin de partie avant de la transmettre.'},400);

    const f=report.fields||{},rounds:any[]=[];
    for(let i=1;i<=Math.max(1,Math.min(Number(party.round_count)||10,20));i++)rounds.push({
      round:i,
      resistance:num(f[`r${i}_resistance`],0,10000),
      network:num(f[`r${i}_network`],0,10000),
      winner:cleanText(f[`r${i}_winner`],4)
    });
    const metrics={
      human_player_count:num(party.human_player_count,1,20),effective_player_count:num(party.effective_player_count,1,20),
      play_mode:cleanText(party.play_mode,30),round_count:num(party.round_count,1,20),network_agents:num(f.network_agents,0,20),rounds,
      bonus_resistance:num(f.bonus_resistance),bonus_network:num(f.bonus_network),rounds_resistance:num(f.rounds_resistance,0,20),
      rounds_network:num(f.rounds_network,0,20),rounds_tied:num(f.rounds_tied,0,20),total_resistance:num(f.total_resistance),
      total_network:num(f.total_network),winner_final:cleanText(f.winner_final,80),tiebreak_required:cleanText(f.tiebreak_required,8)
    };

    const {data:existing,error:existingError}=await s.from('internal_gameplay_contributions').select('id').eq('source_party_id',party.id).eq('source_kind','fracture_endgame').maybeSingle();
    if(existingError)throw existingError;
    if(existing)return json({ok:false,error:'Cette fin de partie a déjà été transmise.'},409);
    const {error:insertError}=await s.from('internal_gameplay_contributions').insert({
      game_slug:'fracture-du-reseau-mere',metrics,feedback:{},contribution_version:'fracture-endgame-v9',source_party_id:party.id,source_kind:'fracture_endgame'
    });
    if(insertError){if(String(insertError.code||'')==='23505')return json({ok:false,error:'Cette fin de partie a déjà été transmise.'},409);throw insertError}

    const now=new Date().toISOString();
    const [reportUpdate,partyUpdate,sessionUpdate]=await Promise.all([
      s.from('fracture_endgame_reports').update({submitted_at:now}).eq('party_id',party.id),
      s.from('fracture_parties').update({status:'finished'}).eq('id',party.id),
      s.from('game_sessions').update({status:'finished',finished_at:now}).eq('game_slug','fracture-du-reseau-mere').eq('party_code',party.party_code)
    ]);
    const updateError=reportUpdate.error||partyUpdate.error||sessionUpdate.error;
    if(updateError)throw updateError;

    let email_sent=false;
    const resend=Deno.env.get('RESEND_API_KEY'),from=Deno.env.get('REPORT_FROM_EMAIL'),to=Deno.env.get('FRACTURE_REPORT_TO_EMAIL')||'kingtyrano@gmail.com';
    if(resend&&from){
      const bodyText=[
        `Fracture du Réseau-Mère — fin de partie ${party.party_code}`,
        `Humains : ${party.human_player_count}`,`Sièges effectifs : ${party.effective_player_count}`,
        `Format : ${party.round_count} rondes`,`Agents Réseau-Mère : ${metrics.network_agents}`,
        `Total Résistance : ${metrics.total_resistance}`,`Total Réseau-Mère : ${metrics.total_network}`,
        `Rondes gagnées R : ${metrics.rounds_resistance}`,`Rondes gagnées RM : ${metrics.rounds_network}`,
        `Égalités : ${metrics.rounds_tied}`,`Gagnant : ${metrics.winner_final}`,`Départage : ${metrics.tiebreak_required}`
      ].join('\n');
      try{
        const r=await fetch('https://api.resend.com/emails',{method:'POST',signal:AbortSignal.timeout(10_000),headers:{Authorization:`Bearer ${resend}`,'Content-Type':'application/json'},body:JSON.stringify({from,to:[to],subject:`SINJIRA — Fin de partie ${party.party_code}`,text:bodyText})});
        email_sent=r.ok;if(!r.ok)console.warn('[SINJIRA fracture endgame email]',r.status);
      }catch(e){console.warn('[SINJIRA fracture endgame email]',e)}
    }
    return json({ok:true,email_sent});
  }catch(e){
    console.error('[SINJIRA fracture endgame]',e);
    if(e?.message==='AUTH_REQUIRED')return json({ok:false,error:'Connexion requise.'},401);
    return json({ok:false,error:'Transmission de la fin de partie impossible.'},500);
  }
});
