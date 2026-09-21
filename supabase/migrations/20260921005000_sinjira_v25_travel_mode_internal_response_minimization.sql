-- SINJIRA™ V25 — minimisation de la réponse interne du Mode Voyage.
-- L’HUMAIN AVANT TOUT : les wrappers publics redigés ne doivent pas pouvoir être
-- contournés par un appel direct à une implémentation interne encore exécutable par
-- authenticated. Les fonctions internes conservent leurs gardes et mutations, mais
-- ne retournent plus les colonnes de rétention ou d'identité serveur.

begin;

create or replace function sinjira_security_internal.security_create_travel_plan(
  p_starts_at timestamptz,
  p_ends_at timestamptz,
  p_destinations text[],
  p_multi_country boolean default false
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth, sinjira_security_internal
as $$
declare
  v_user uuid := auth.uid();
  v_row public.security_travel_plans;
  v_dest text[];
  v_has_invalid boolean := false;
begin
  if v_user is null then
    raise exception 'AUTH_REQUIRED' using errcode='42501';
  end if;

  perform private.security_require_aal2_if_available(v_user);

  if p_starts_at is null
     or p_ends_at is null
     or p_ends_at <= p_starts_at
     or p_ends_at <= now()
     or p_ends_at > p_starts_at + interval '180 days' then
    raise exception 'INVALID_TRAVEL_PERIOD' using errcode='22023';
  end if;

  select exists(
    select 1
    from unnest(coalesce(p_destinations,'{}'::text[])) x
    where x is null
       or trim(x) = ''
       or not private.security_is_iso_country_code_v25(x)
  ) into v_has_invalid;

  if v_has_invalid then
    raise exception 'INVALID_TRAVEL_COUNTRY_CODE' using errcode='22023';
  end if;

  select array_agg(code order by code)
    into v_dest
  from (
    select distinct upper(trim(x)) as code
    from unnest(coalesce(p_destinations,'{}'::text[])) x
  ) normalized;

  if cardinality(coalesce(v_dest,'{}'::text[])) not between 1 and 12 then
    raise exception 'INVALID_DESTINATIONS' using errcode='22023';
  end if;

  insert into public.security_travel_plans(
    user_id,starts_at,ends_at,destinations,multi_country,delete_after
  ) values(
    v_user,
    p_starts_at,
    p_ends_at,
    v_dest,
    cardinality(v_dest) > 1,
    p_ends_at + interval '7 days'
  ) returning * into v_row;

  insert into public.security_events(user_id,event_type,summary,severity)
  values(
    v_user,
    'travel_plan_created',
    'Mode Voyage planifié. Les détails servent uniquement à la sécurité.',
    'info'
  );

  return pg_catalog.jsonb_build_object(
    'id',v_row.id,
    'status',v_row.status,
    'starts_at',v_row.starts_at,
    'ends_at',v_row.ends_at,
    'destinations',to_jsonb(v_row.destinations)
  );
end;
$$;

revoke all on function sinjira_security_internal.security_create_travel_plan(
  timestamptz,timestamptz,text[],boolean
) from public, anon;
grant execute on function sinjira_security_internal.security_create_travel_plan(
  timestamptz,timestamptz,text[],boolean
) to authenticated, service_role;

create or replace function sinjira_security_internal.security_cancel_travel_plan(
  p_plan_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth, sinjira_security_internal
as $$
declare
  v_user uuid := auth.uid();
  v_row public.security_travel_plans;
begin
  if v_user is null then
    raise exception 'AUTH_REQUIRED' using errcode='42501';
  end if;

  perform private.security_require_aal2_if_available(v_user);

  update public.security_travel_plans
     set status='cancelled',
         cancelled_at=now(),
         delete_after=least(delete_after,now()+interval '7 days')
   where id=p_plan_id
     and user_id=v_user
     and status='active'
  returning * into v_row;

  if not found then
    raise exception 'TRAVEL_PLAN_NOT_FOUND';
  end if;

  insert into public.security_events(user_id,event_type,summary,severity)
  values(v_user,'travel_plan_cancelled','Mode Voyage annulé.','info');

  return pg_catalog.jsonb_build_object(
    'id',v_row.id,
    'status',v_row.status
  );
end;
$$;

revoke all on function sinjira_security_internal.security_cancel_travel_plan(uuid)
from public, anon;
grant execute on function sinjira_security_internal.security_cancel_travel_plan(uuid)
to authenticated, service_role;

comment on function sinjira_security_internal.security_create_travel_plan(
  timestamptz,timestamptz,text[],boolean
) is
  'Implémentation privilégiée Mode Voyage: garde AAL2/validation/rétention inchangées; réponse directe minimisée aux mêmes données utilisateur que le wrapper public.';

comment on function sinjira_security_internal.security_cancel_travel_plan(uuid) is
  'Implémentation privilégiée d’annulation Mode Voyage: mutation/rétention inchangées; réponse directe minimisée à id et status.';

commit;
