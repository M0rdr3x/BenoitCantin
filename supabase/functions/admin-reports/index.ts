import { corsHeaders, json } from '../_shared/cors.ts';
import { requiredUser, serviceClient } from '../_shared/auth.ts';

async function requireAdmin(req: Request) {
  const user = await requiredUser(req);
  const service = serviceClient();
  const { data, error } = await service.rpc('is_sinjira_admin', { p_user_id: user.id });
  if (error || !data) throw new Error('ADMIN_REQUIRED');
  return { user, service };
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ ok:false, error:'Méthode non autorisée.' }, 405);

  try {
    const { service } = await requireAdmin(req);
    const body = await req.json();
    const action = String(body?.action || '');

    if (action === 'dashboard') {
      const [
        reports,
        active,
        finished
      ] = await Promise.all([
        service.from('fracture_endgame_reports').select('id', { count:'exact', head:true }).not('submitted_at','is',null),
        service.from('fracture_parties').select('id', { count:'exact', head:true }).eq('status','in_progress'),
        service.from('fracture_parties').select('id', { count:'exact', head:true }).eq('status','finished')
      ]);

      return json({
        ok:true,
        dashboard:{
          game_reports: reports.count || 0,
          active_parties: active.count || 0,
          finished_parties: finished.count || 0
        }
      });
    }

    if (action === 'list_game_reports') {
      const { data: rows = [], error } = await service
        .from('fracture_endgame_reports')
        .select(`
          id, party_id, owner_user_id, fields, submitted_at, created_at,
          fracture_parties(
            party_code, human_player_count, effective_player_count,
            play_mode, round_count, status
          )
        `)
        .not('submitted_at','is',null)
        .order('submitted_at',{ ascending:false })
        .limit(2000);

      if (error) throw error;

      const ownerIds = [...new Set(rows.map((r:any) => r.owner_user_id).filter(Boolean))];
      const { data: profiles = [] } = ownerIds.length
        ? await service.from('profiles').select('user_id,pseudo,display_name').in('user_id', ownerIds)
        : { data: [] as any[] };

      const profileMap = new Map((profiles || []).map((p:any) => [p.user_id,p]));
      const emails = new Map<string,string>();

      for (const id of ownerIds) {
        const { data } = await service.auth.admin.getUserById(id);
        if (data?.user?.email) emails.set(id, data.user.email);
      }

      const reports = rows.map((r:any) => {
        const p = r.fracture_parties || {};
        const profile = profileMap.get(r.owner_user_id) || {};
        return {
          id: r.id,
          party_code: p.party_code,
          human_player_count: p.human_player_count,
          effective_player_count: p.effective_player_count,
          play_mode: p.play_mode,
          round_count: p.round_count,
          party_status: p.status,
          fields: r.fields || {},
          submitted_at: r.submitted_at,
          owner: {
            pseudo: profile.pseudo || '',
            display_name: profile.display_name || '',
            email: emails.get(r.owner_user_id) || ''
          }
        };
      });

      let resistance = 0, network = 0, ties = 0;
      for (const r of reports) {
        const winner = String(r.fields?.winner_final || '').toLowerCase();
        if (winner.includes('résistance') || winner.includes('resistance')) resistance++;
        else if (winner.includes('réseau') || winner.includes('reseau')) network++;
        else ties++;
      }

      return json({
        ok:true,
        reports,
        summary:{
          count: reports.length,
          resistance_wins: resistance,
          network_wins: network,
          ties
        }
      });
    }

    return json({ ok:false, error:'Action inconnue.' }, 400);
  } catch (error) {
    console.error(error);
    if (error?.message === 'AUTH_REQUIRED') return json({ ok:false, error:'Connexion requise.' }, 401);
    if (error?.message === 'ADMIN_REQUIRED') return json({ ok:false, error:'Accès administrateur refusé.' }, 403);
    return json({ ok:false, error:'Erreur rapports administrateur.' }, 500);
  }
});
