import {createClient} from 'npm:@supabase/supabase-js@2';

const cors={
  'Access-Control-Allow-Origin':'https://www.benoitcantin.com',
  'Access-Control-Allow-Headers':'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods':'POST, OPTIONS',
  'Vary':'Origin'
};
const json=(x:unknown,status=200)=>new Response(JSON.stringify(x),{status,headers:{...cors,'Content-Type':'application/json; charset=utf-8'}});
const PAID_EXTERNAL_SERVICES_ENABLED=false;
function service(){
  const url=Deno.env.get('SUPABASE_URL'),key=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if(!url||!key)throw new Error('SERVER_CONFIG');
  return createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}});
}
async function userFrom(req:Request,s:any){
  const h=req.headers.get('Authorization')||'',token=h.startsWith('Bearer ')?h.slice(7):'';
  if(!token)throw new Error('AUTH');
  const {data,error}=await s.auth.getUser(token);if(error||!data.user)throw new Error('AUTH');return data.user;
}
function cleanText(v:unknown,max=300){return String(v??'').trim().slice(0,max)}
function num(v:unknown){const n=Number(v);return Number.isFinite(n)?n:0}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:cors});
  if(req.method!=='POST')return json({ok:false,error:'Méthode non autorisée.'},405);
  try{
    const s=service(),user=await userFrom(req,s),body=await req.json(),code=cleanText(body?.party_code,10).toUpperCase();
    const {data:party}=await s.from('fracture_parties').select('*').eq('party_code',code).maybeSingle();
    if(!party)return json({ok:false,error:'Partie introuvable.'},404);
    if(party.owner_user_id!==user.id)return json({ok:false,error:'Seul le créateur de la partie peut transmettre la fin de partie.'},403);
    const {data:report}=await s.from('fracture_endgame_reports').select('*').eq('party_id',party.id).maybeSingle();
    if(!report)return json({ok:false,error:'Sauvegardez la Feuille de fin de partie avant de la transmettre.'},400);
    const f=report.fields||{},rounds:any[]=[];
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
    const feedback={};
    const {data:existing}=await s.from('internal_gameplay_contributions').select('id').eq('source_party_id',party.id).eq('source_kind','fracture_endgame').maybeSingle();
    if(existing)return json({ok:false,error:'Cette fin de partie a déjà été transmise.'},409);
    const {error:insertError}=await s.from('internal_gameplay_contributions').insert({
      game_slug:'fracture-du-reseau-mere',metrics,feedback,contribution_version:'fracture-endgame-v9',source_party_id:party.id,source_kind:'fracture_endgame'
    });
    if(insertError)throw insertError;
    await s.from('fracture_endgame_reports').update({submitted_at:new Date().toISOString()}).eq('party_id',party.id);
    await s.from('fracture_parties').update({status:'finished'}).eq('id',party.id);
    await s.from('game_sessions').update({status:'finished',finished_at:new Date().toISOString()}).eq('game_slug','fracture-du-reseau-mere').eq('party_code',party.party_code);

    let email_sent=false;
    const resend=Deno.env.get('RESEND_API_KEY'),from=Deno.env.get('REPORT_FROM_EMAIL'),to=Deno.env.get('FRACTURE_REPORT_TO_EMAIL')||'kingtyrano@gmail.com';
    if(PAID_EXTERNAL_SERVICES_ENABLED&&resend&&from){
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
      const r=await fetch('https://api.resend.com/emails',{method:'POST',headers:{Authorization:`Bearer ${resend}`,'Content-Type':'application/json'},body:JSON.stringify({from,to:[to],subject:`SINJIRA — Fin de partie ${party.party_code}`,text:bodyText})});
      email_sent=r.ok;
    }
    return json({ok:true,email_sent,paid_external_services_enabled:PAID_EXTERNAL_SERVICES_ENABLED});
  }catch(e){
    console.error(e);
    if(e?.message==='AUTH')return json({ok:false,error:'Connexion requise.'},401);
    return json({ok:false,error:'Transmission de la fin de partie impossible.'},500);
  }
});
