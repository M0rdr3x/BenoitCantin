-- SINJIRA™ V25 — capacités self-only du compte.
-- Une seule décision serveur décrit les surfaces autorisées; aucune date de naissance ni UUID arbitraire n'est exposé.

create or replace function public.sinjira_my_account_capabilities()
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $cap$
declare
  uid uuid:=auth.uid();
  band text;
  standard boolean;
  junior_enabled boolean:=false;
  junior_rules boolean:=false;
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED' using errcode='42501';
  end if;

  band:=public.sinjira_age_band(uid);
  standard:=band in ('adult','youth');

  if band='child' then
    junior_enabled:=private.sinjira_junior_community_enabled(uid);
    junior_rules:=private.has_accepted_junior_community_rules(uid);
  end if;

  return jsonb_build_object(
    'account_mode',case when band='child' then 'child' when standard then 'standard' else 'restricted' end,
    'age_band',band,
    'child_11_12',band='child',
    'guardian_supervision',band in ('child','youth'),
    'junior_community_eligible',band='child',
    'junior_community_enabled',junior_enabled,
    'junior_rules_accepted',junior_rules,
    'general_community',standard,
    'private_messages',standard,
    'native_general_hubs',standard,
    'dating',band='adult',
    'commerce',standard,
    'employment',standard,
    'personal_ai',standard,
    'playtests',standard,
    'contributor',standard,
    'library_mode',case when band='child' then 'reviewed_11_12' when standard then 'full' else 'none' end,
    'security_center',band in ('child','youth','adult')
  );
end;
$cap$;

revoke all on function public.sinjira_my_account_capabilities() from public,anon;
grant execute on function public.sinjira_my_account_capabilities() to authenticated,service_role;

comment on function public.sinjira_my_account_capabilities() is
  'Capacités du compte courant uniquement. Aucun argument UUID; fail-closed pour bandes non vérifiées/pending; ne renvoie ni date de naissance ni identité.';
