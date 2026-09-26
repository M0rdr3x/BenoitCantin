-- SINJIRA™ V25 — Rétention serveur du Mode Voyage
-- L’HUMAIN AVANT TOUT : la date delete_after déjà enregistrée reste l’unique
-- autorité de suppression. Cette migration ne configure aucun ordonnanceur.

begin;

create or replace function private.security_purge_expired_travel_plans_v25()
returns bigint
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_deleted bigint;
begin
  delete from public.security_travel_plans
  where delete_after <= statement_timestamp();

  get diagnostics v_deleted = row_count;
  return v_deleted;
end;
$$;

revoke all on function private.security_purge_expired_travel_plans_v25()
from public, anon, authenticated;
grant execute on function private.security_purge_expired_travel_plans_v25()
to service_role;

comment on function private.security_purge_expired_travel_plans_v25() is
  'Primitive serveur V25 de purge du Mode Voyage. Supprime uniquement les lignes dont delete_after est échu, ne prend aucun instant arbitraire en paramètre et ne configure aucun ordonnanceur.';

commit;
