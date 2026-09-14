-- SINJIRA™ V25 — frontière de visibilité client du Mode Voyage
-- L’HUMAIN AVANT TOUT : la rétention technique ne doit jamais devenir un droit
-- de lecture navigateur. Un client authentifié ne voit que ses déclarations
-- encore actives et non expirées. Les réponses RPC publiques ne renvoient que
-- les propriétés nécessaires à l’interface; les détails de rétention restent serveur.

begin;

alter table public.security_travel_plans enable row level security;

revoke all on table public.security_travel_plans from public, anon, authenticated;
grant select on table public.security_travel_plans to authenticated;

drop policy if exists security_travel_plans_read_own on public.security_travel_plans;
create policy security_travel_plans_read_own
on public.security_travel_plans
for select
to authenticated
using (
  (select auth.uid()) = user_id
  and status = 'active'
  and ends_at >= statement_timestamp()
);

-- Les implémentations privilégiées restent dans sinjira_security_internal.
-- Le schéma public ne sérialise plus la ligne complète renvoyée par ces fonctions.
create or replace function public.security_create_travel_plan(
  p_starts_at timestamptz,
  p_ends_at timestamptz,
  p_destinations text[],
  p_multi_country boolean default false
)
returns jsonb
language sql
security invoker
set search_path = ''
as $$
  select pg_catalog.jsonb_build_object(
    'id', result->'id',
    'status', result->'status',
    'starts_at', result->'starts_at',
    'ends_at', result->'ends_at',
    'destinations', result->'destinations'
  )
  from (
    select sinjira_security_internal.security_create_travel_plan($1,$2,$3,$4) as result
  ) response
$$;

revoke all on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)
from public, anon;
grant execute on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)
to authenticated, service_role;

create or replace function public.security_cancel_travel_plan(p_plan_id uuid)
returns jsonb
language sql
security invoker
set search_path = ''
as $$
  select pg_catalog.jsonb_build_object(
    'id', result->'id',
    'status', result->'status'
  )
  from (
    select sinjira_security_internal.security_cancel_travel_plan($1) as result
  ) response
$$;

revoke all on function public.security_cancel_travel_plan(uuid) from public, anon;
grant execute on function public.security_cancel_travel_plan(uuid) to authenticated, service_role;

comment on policy security_travel_plans_read_own on public.security_travel_plans is
  'Lecture navigateur self-only limitée aux voyages actifs non expirés. Les lignes annulées ou terminées retenues techniquement restent serveur uniquement.';

comment on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) is
  'Wrapper SECURITY INVOKER: crée un Mode Voyage via l’implémentation interne et ne renvoie que id, status, starts_at, ends_at et destinations.';

comment on function public.security_cancel_travel_plan(uuid) is
  'Wrapper SECURITY INVOKER: annule le Mode Voyage via l’implémentation interne et ne renvoie que id et status.';

comment on table public.security_travel_plans is
  'Mode Voyage: pays approximatifs et période seulement. Lecture client limitée aux voyages actifs non expirés; rétention technique serveur jusqu’à delete_after.';

commit;
