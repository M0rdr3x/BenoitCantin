-- SINJIRA™ V25 — Mode Voyage cohérent avec le moteur de risque
-- L’HUMAIN AVANT TOUT : l’utilisateur déclare volontairement uniquement des pays
-- et une période. Aucun itinéraire, hôtel, vol, IP brute ou GPS n’est demandé.

begin;

create or replace function private.security_is_iso_country_code_v25(p_code text)
returns boolean
language sql
immutable
set search_path = pg_catalog, private
as $$
  select upper(trim(coalesce(p_code,''))) = any(array[
    'AD','AE','AF','AG','AI','AL','AM','AO','AQ','AR','AS','AT','AU','AW','AX','AZ',
    'BA','BB','BD','BE','BF','BG','BH','BI','BJ','BL','BM','BN','BO','BQ','BR','BS','BT','BV','BW','BY','BZ',
    'CA','CC','CD','CF','CG','CH','CI','CK','CL','CM','CN','CO','CR','CU','CV','CW','CX','CY','CZ',
    'DE','DJ','DK','DM','DO','DZ','EC','EE','EG','EH','ER','ES','ET','FI','FJ','FK','FM','FO','FR',
    'GA','GB','GD','GE','GF','GG','GH','GI','GL','GM','GN','GP','GQ','GR','GS','GT','GU','GW','GY',
    'HK','HM','HN','HR','HT','HU','ID','IE','IL','IM','IN','IO','IQ','IR','IS','IT','JE','JM','JO','JP',
    'KE','KG','KH','KI','KM','KN','KP','KR','KW','KY','KZ','LA','LB','LC','LI','LK','LR','LS','LT','LU','LV','LY',
    'MA','MC','MD','ME','MF','MG','MH','MK','ML','MM','MN','MO','MP','MQ','MR','MS','MT','MU','MV','MW','MX','MY','MZ',
    'NA','NC','NE','NF','NG','NI','NL','NO','NP','NR','NU','NZ','OM','PA','PE','PF','PG','PH','PK','PL','PM','PN','PR','PS','PT','PW','PY',
    'QA','RE','RO','RS','RU','RW','SA','SB','SC','SD','SE','SG','SH','SI','SJ','SK','SL','SM','SN','SO','SR','SS','ST','SV','SX','SY','SZ',
    'TC','TD','TF','TG','TH','TJ','TK','TL','TM','TN','TO','TR','TT','TV','TW','TZ','UA','UG','UM','US','UY','UZ',
    'VA','VC','VE','VG','VI','VN','VU','WF','WS','YE','YT','ZA','ZM','ZW'
  ]::text[]);
$$;

revoke all on function private.security_is_iso_country_code_v25(text) from public, anon, authenticated;
grant execute on function private.security_is_iso_country_code_v25(text) to service_role;

-- Depuis V24.5.10, les RPC publiques du Centre de sécurité sont uniquement
-- SECURITY INVOKER. L'implémentation privilégiée reste hors du schéma API.
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

  return to_jsonb(v_row);
end;
$$;

revoke all on function sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)
from public, anon;
grant execute on function sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)
to authenticated, service_role;

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
  select sinjira_security_internal.security_create_travel_plan($1,$2,$3,$4)
$$;

revoke all on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)
from public, anon;
grant execute on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)
to authenticated, service_role;

comment on function private.security_is_iso_country_code_v25(text) is
  'Validation locale et déterministe des codes pays ISO alpha-2 du Mode Voyage. Aucune géolocalisation ni appel réseau.';
comment on function sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) is
  'Implémentation privilégiée Mode Voyage V25: validation ISO alpha-2, normalisation/déduplication, période <= 180 jours, rétention cible +7 jours.';
comment on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) is
  'Wrapper SECURITY INVOKER du Mode Voyage V25; aucune logique privilégiée dans le schéma API public.';

commit;
