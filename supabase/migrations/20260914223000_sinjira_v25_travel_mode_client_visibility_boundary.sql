-- SINJIRA™ V25 — frontière de visibilité client du Mode Voyage
-- L’HUMAIN AVANT TOUT : la rétention technique ne doit jamais devenir un droit
-- de lecture navigateur. Un client authentifié ne voit que ses déclarations
-- encore actives et non expirées. Les lignes annulées/terminées restent
-- disponibles uniquement aux chemins serveur privilégiés jusqu'à leur purge.

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

comment on policy security_travel_plans_read_own on public.security_travel_plans is
  'Lecture navigateur self-only limitée aux voyages actifs non expirés. Les lignes annulées ou terminées retenues techniquement restent serveur uniquement.';

comment on table public.security_travel_plans is
  'Mode Voyage: pays approximatifs et période seulement. Lecture client limitée aux voyages actifs non expirés; rétention technique serveur jusqu’à delete_after.';

commit;
