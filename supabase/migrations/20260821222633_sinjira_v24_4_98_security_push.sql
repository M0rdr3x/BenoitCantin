-- SINJIRA™ V24.4.98 — notifications push de sécurité
-- Les jetons push sont des identifiants techniques privés. Ils ne sont jamais exposés par SELECT au navigateur.

begin;

create table if not exists public.security_push_endpoints (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  device_id uuid not null references public.security_devices(id) on delete cascade,
  expo_push_token text not null check (char_length(expo_push_token) between 20 and 300),
  platform text not null default '' check (char_length(platform) <= 40),
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  unique(user_id, expo_push_token)
);
create index if not exists security_push_endpoints_user_enabled_idx
  on public.security_push_endpoints(user_id, enabled) where enabled;

alter table public.security_push_endpoints enable row level security;
revoke all on table public.security_push_endpoints from public, anon, authenticated;
grant select, insert, update, delete on table public.security_push_endpoints to service_role;

create or replace function public.security_register_push_endpoint(
  p_device_key text,p_expo_push_token text,p_platform text default ''
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user uuid:=auth.uid(); v_device public.security_devices; v_row public.security_push_endpoints;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if p_expo_push_token is null or char_length(trim(p_expo_push_token)) not between 20 and 300 then raise exception 'INVALID_PUSH_TOKEN'; end if;
  select * into v_device from public.security_devices where user_id=v_user and device_key=p_device_key and revoked_at is null;
  if not found then raise exception 'DEVICE_NOT_FOUND'; end if;
  insert into public.security_push_endpoints(user_id,device_id,expo_push_token,platform)
  values(v_user,v_device.id,trim(p_expo_push_token),left(coalesce(p_platform,''),40))
  on conflict(user_id,expo_push_token) do update set device_id=excluded.device_id,platform=excluded.platform,enabled=true,last_seen_at=now(),updated_at=now()
  returning * into v_row;
  return jsonb_build_object('ok',true,'endpoint_id',v_row.id,'enabled',v_row.enabled);
end;
$$;
revoke all on function public.security_register_push_endpoint(text,text,text) from public, anon;
grant execute on function public.security_register_push_endpoint(text,text,text) to authenticated;

create or replace function public.security_disable_push_for_device(p_device_key text)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user uuid:=auth.uid(); v_device uuid; v_count integer;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  select id into v_device from public.security_devices where user_id=v_user and device_key=p_device_key;
  if v_device is null then return jsonb_build_object('ok',true,'disabled',0); end if;
  update public.security_push_endpoints set enabled=false,updated_at=now() where user_id=v_user and device_id=v_device and enabled;
  get diagnostics v_count=row_count;
  return jsonb_build_object('ok',true,'disabled',v_count);
end;
$$;
revoke all on function public.security_disable_push_for_device(text) from public, anon;
grant execute on function public.security_disable_push_for_device(text) to authenticated;

create or replace function public.security_push_status(p_device_key text)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user uuid:=auth.uid(); v_device uuid; v_enabled integer;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  select id into v_device from public.security_devices where user_id=v_user and device_key=p_device_key;
  select count(*)::int into v_enabled from public.security_push_endpoints where user_id=v_user and device_id=v_device and enabled;
  return jsonb_build_object('enabled',v_enabled>0,'endpoint_count',v_enabled);
end;
$$;
revoke all on function public.security_push_status(text) from public, anon;
grant execute on function public.security_push_status(text) to authenticated;

commit;
