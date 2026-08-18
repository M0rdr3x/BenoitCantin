-- SINJIRA V24.4.54 — index de support des clés étrangères licences.
-- Correctif performance ciblé; aucun changement de données ni de permissions.

create index if not exists activation_codes_redeemed_by_idx
  on public.activation_codes(redeemed_by);

create index if not exists license_batches_created_by_idx
  on public.license_batches(created_by);

create or replace function public.sinjira_license_index_health()
returns jsonb
language sql
stable
security invoker
set search_path=public
as $$
  select jsonb_build_object(
    'ok',
      to_regclass('public.activation_codes_redeemed_by_idx') is not null and
      to_regclass('public.license_batches_created_by_idx') is not null,
    'activation_codes_redeemed_by_idx',to_regclass('public.activation_codes_redeemed_by_idx') is not null,
    'license_batches_created_by_idx',to_regclass('public.license_batches_created_by_idx') is not null,
    'version','24.4.54'
  );
$$;

revoke all on function public.sinjira_license_index_health() from public,anon,authenticated;
grant execute on function public.sinjira_license_index_health() to service_role;
