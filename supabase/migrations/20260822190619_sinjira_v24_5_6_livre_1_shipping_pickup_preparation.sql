create table if not exists public.preorder_fulfillment_settings (
  product_id uuid primary key references public.products(id) on delete cascade,
  currency text not null default 'CAD' check (currency ~ '^[A-Z]{3}$'),
  shipping_customer_pays boolean not null default true check (shipping_customer_pays = true),
  shipping_estimates_enabled boolean not null default false,
  pickup_interest_enabled boolean not null default true check (pickup_interest_enabled = true),
  pickup_points_enabled boolean not null default false,
  external_carrier_api_enabled boolean not null default false check (external_carrier_api_enabled = false),
  external_shipping_purchase_enabled boolean not null default false check (external_shipping_purchase_enabled = false),
  pickup_shipping_charge_cents integer not null default 0 check (pickup_shipping_charge_cents = 0),
  updated_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.preorder_fulfillment_settings is
  'V24.5.6: préparation livraison/ramassage du Livre I. Livraison à la charge du client; aucune API transporteur ni achat d étiquette externe activé.';

create table if not exists public.preorder_shipping_zones (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  zone_code text not null check (zone_code ~ '^[a-z0-9][a-z0-9_-]{1,39}$'),
  label text not null check (char_length(label) between 2 and 120),
  country_code text check (country_code is null or country_code ~ '^[A-Z]{2}$'),
  subdivision_code text check (subdivision_code is null or char_length(subdivision_code) <= 24),
  currency text not null default 'CAD' check (currency ~ '^[A-Z]{3}$'),
  base_min_cents integer check (base_min_cents is null or base_min_cents between 0 and 10000000),
  base_max_cents integer check (base_max_cents is null or base_max_cents between 0 and 10000000),
  additional_copy_min_cents integer not null default 0 check (additional_copy_min_cents between 0 and 10000000),
  additional_copy_max_cents integer not null default 0 check (additional_copy_max_cents between 0 and 10000000),
  estimate_note text check (estimate_note is null or char_length(estimate_note) <= 700),
  active boolean not null default true,
  published_at timestamptz,
  created_by uuid not null references auth.users(id) on delete restrict,
  updated_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint preorder_shipping_zones_product_code_key unique (product_id, zone_code),
  constraint preorder_shipping_base_range_check check (
    (base_min_cents is null and base_max_cents is null)
    or (base_min_cents is not null and base_max_cents is not null and base_min_cents <= base_max_cents)
  ),
  constraint preorder_shipping_additional_range_check check (additional_copy_min_cents <= additional_copy_max_cents)
);

create index if not exists preorder_shipping_zones_product_active_idx
  on public.preorder_shipping_zones(product_id, active, published_at desc);
create index if not exists preorder_shipping_zones_created_by_idx on public.preorder_shipping_zones(created_by);
create index if not exists preorder_shipping_zones_updated_by_idx on public.preorder_shipping_zones(updated_by);

create table if not exists public.preorder_pickup_points (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  pickup_code text not null check (pickup_code ~ '^[a-z0-9][a-z0-9_-]{1,39}$'),
  label text not null check (char_length(label) between 2 and 120),
  public_address text check (public_address is null or char_length(public_address) <= 300),
  city text check (city is null or char_length(city) <= 120),
  region text check (region is null or char_length(region) <= 120),
  country_code text not null default 'CA' check (country_code ~ '^[A-Z]{2}$'),
  pickup_window_text text check (pickup_window_text is null or char_length(pickup_window_text) <= 500),
  instructions text check (instructions is null or char_length(instructions) <= 900),
  active boolean not null default true,
  published_at timestamptz,
  created_by uuid not null references auth.users(id) on delete restrict,
  updated_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint preorder_pickup_points_product_code_key unique (product_id, pickup_code)
);

create index if not exists preorder_pickup_points_product_active_idx
  on public.preorder_pickup_points(product_id, active, published_at desc);
create index if not exists preorder_pickup_points_created_by_idx on public.preorder_pickup_points(created_by);
create index if not exists preorder_pickup_points_updated_by_idx on public.preorder_pickup_points(updated_by);

alter table public.preorder_fulfillment_settings enable row level security;
alter table public.preorder_shipping_zones enable row level security;
alter table public.preorder_pickup_points enable row level security;
revoke all on table public.preorder_fulfillment_settings from public, anon, authenticated;
revoke all on table public.preorder_shipping_zones from public, anon, authenticated;
revoke all on table public.preorder_pickup_points from public, anon, authenticated;

alter table public.product_preorders
  add column if not exists fulfillment_preference text not null default 'undecided'
    check (fulfillment_preference in ('shipping','pickup','undecided')),
  add column if not exists pickup_point_id uuid references public.preorder_pickup_points(id) on delete set null;

create index if not exists product_preorders_pickup_point_idx on public.product_preorders(pickup_point_id);
create index if not exists product_preorders_fulfillment_idx on public.product_preorders(product_id, status, fulfillment_preference);

alter table public.product_preorders drop constraint if exists product_preorders_pickup_preference_check;
alter table public.product_preorders add constraint product_preorders_pickup_preference_check
  check (pickup_point_id is null or fulfillment_preference = 'pickup');

create or replace function public.preorder_fulfillment_settings_guard()
returns trigger language plpgsql security invoker set search_path = '' as $$
begin
  new.updated_at := now();
  new.shipping_customer_pays := true;
  new.pickup_interest_enabled := true;
  new.external_carrier_api_enabled := false;
  new.external_shipping_purchase_enabled := false;
  new.pickup_shipping_charge_cents := 0;
  if tg_op = 'UPDATE' then new.product_id := old.product_id; new.created_at := old.created_at; end if;
  return new;
end;
$$;
revoke all on function public.preorder_fulfillment_settings_guard() from public, anon, authenticated;
drop trigger if exists preorder_fulfillment_settings_guard_trg on public.preorder_fulfillment_settings;
create trigger preorder_fulfillment_settings_guard_trg before insert or update on public.preorder_fulfillment_settings for each row execute function public.preorder_fulfillment_settings_guard();

create or replace function public.preorder_shipping_zone_touch()
returns trigger language plpgsql security invoker set search_path = '' as $$
begin
  new.updated_at := now();
  new.zone_code := lower(btrim(new.zone_code));
  new.currency := upper(btrim(new.currency));
  new.country_code := case when new.country_code is null then null else upper(btrim(new.country_code)) end;
  new.subdivision_code := nullif(upper(btrim(coalesce(new.subdivision_code,''))), '');
  if tg_op = 'UPDATE' then new.product_id := old.product_id; new.created_by := old.created_by; new.created_at := old.created_at; end if;
  return new;
end;
$$;
revoke all on function public.preorder_shipping_zone_touch() from public, anon, authenticated;
drop trigger if exists preorder_shipping_zone_touch_trg on public.preorder_shipping_zones;
create trigger preorder_shipping_zone_touch_trg before insert or update on public.preorder_shipping_zones for each row execute function public.preorder_shipping_zone_touch();

create or replace function public.preorder_pickup_point_touch()
returns trigger language plpgsql security invoker set search_path = '' as $$
begin
  new.updated_at := now();
  new.pickup_code := lower(btrim(new.pickup_code));
  new.country_code := upper(btrim(new.country_code));
  if tg_op = 'UPDATE' then new.product_id := old.product_id; new.created_by := old.created_by; new.created_at := old.created_at; end if;
  return new;
end;
$$;
revoke all on function public.preorder_pickup_point_touch() from public, anon, authenticated;
drop trigger if exists preorder_pickup_point_touch_trg on public.preorder_pickup_points;
create trigger preorder_pickup_point_touch_trg before insert or update on public.preorder_pickup_points for each row execute function public.preorder_pickup_point_touch();

create or replace function public.product_preorder_fulfillment_options(p_product_slug text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  v_product_id uuid; v_settings public.preorder_fulfillment_settings%rowtype;
  v_zones jsonb := '[]'::jsonb; v_pickups jsonb := '[]'::jsonb;
begin
  select p.id into v_product_id from public.products p where p.slug = p_product_slug and p.active = true and p.product_type = 'novel' limit 1;
  if v_product_id is null then return null; end if;
  select s.* into v_settings from public.preorder_fulfillment_settings s where s.product_id = v_product_id;
  if coalesce(v_settings.shipping_estimates_enabled,false) then
    select coalesce(jsonb_agg(jsonb_build_object('zone_code', z.zone_code,'label', z.label,'country_code', z.country_code,'subdivision_code', z.subdivision_code,'currency', z.currency,'estimate_note', z.estimate_note) order by z.label), '[]'::jsonb)
    into v_zones from public.preorder_shipping_zones z where z.product_id = v_product_id and z.active = true and z.published_at is not null;
  end if;
  if coalesce(v_settings.pickup_points_enabled,false) then
    select coalesce(jsonb_agg(jsonb_build_object('pickup_code', pp.pickup_code,'label', pp.label,'public_address', pp.public_address,'city', pp.city,'region', pp.region,'country_code', pp.country_code,'pickup_window_text', pp.pickup_window_text,'instructions', pp.instructions) order by pp.label), '[]'::jsonb)
    into v_pickups from public.preorder_pickup_points pp where pp.product_id = v_product_id and pp.active = true and pp.published_at is not null;
  end if;
  return jsonb_build_object('shipping_customer_pays', true,'shipping_estimate_nonbinding', true,'shipping_estimates_enabled', coalesce(v_settings.shipping_estimates_enabled,false),'pickup_interest_enabled', true,'pickup_points_enabled', coalesce(v_settings.pickup_points_enabled,false),'pickup_shipping_charge_cents', 0,'external_carrier_api_enabled', false,'external_shipping_purchase_enabled', false,'shipping_zones', v_zones,'pickup_points', v_pickups);
end;
$$;

create or replace function public.product_preorder_shipping_estimate(p_product_slug text,p_zone_code text,p_quantity integer default 1)
returns table (zone_code text,zone_label text,currency text,estimate_min_cents integer,estimate_max_cents integer,estimate_note text,shipping_customer_pays boolean,estimate_nonbinding boolean)
language plpgsql stable security definer set search_path = '' as $$
declare v_product_id uuid; v_zone public.preorder_shipping_zones%rowtype; v_enabled boolean := false;
begin
  if p_quantity is null or p_quantity < 1 or p_quantity > 5 then raise exception using errcode = '22023', message = 'INVALID_PREORDER_QUANTITY'; end if;
  select p.id into v_product_id from public.products p where p.slug = p_product_slug and p.active = true and p.product_type = 'novel' limit 1;
  if v_product_id is null then return; end if;
  select s.shipping_estimates_enabled into v_enabled from public.preorder_fulfillment_settings s where s.product_id = v_product_id;
  if not coalesce(v_enabled,false) then return; end if;
  select z.* into v_zone from public.preorder_shipping_zones z where z.product_id = v_product_id and z.zone_code = lower(btrim(coalesce(p_zone_code,''))) and z.active = true and z.published_at is not null limit 1;
  if v_zone.id is null or v_zone.base_min_cents is null or v_zone.base_max_cents is null then return; end if;
  return query select v_zone.zone_code,v_zone.label,v_zone.currency,v_zone.base_min_cents + greatest(p_quantity - 1,0) * v_zone.additional_copy_min_cents,v_zone.base_max_cents + greatest(p_quantity - 1,0) * v_zone.additional_copy_max_cents,v_zone.estimate_note,true,true;
end;
$$;

create or replace function public.product_preorder_fulfillment_status(p_product_slug text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare v_user uuid := auth.uid(); v_result jsonb;
begin
  if v_user is null then raise exception using errcode = '42501', message = 'AUTH_REQUIRED'; end if;
  select jsonb_build_object('fulfillment_preference', pp.fulfillment_preference,'pickup_code', case when px.published_at is not null and px.active then px.pickup_code else null end,'pickup_label', case when px.published_at is not null and px.active then px.label else null end,'pickup_city', case when px.published_at is not null and px.active then px.city else null end,'pickup_region', case when px.published_at is not null and px.active then px.region else null end)
  into v_result from public.product_preorders pp join public.products p on p.id = pp.product_id left join public.preorder_pickup_points px on px.id = pp.pickup_point_id where pp.user_id = v_user and p.slug = p_product_slug limit 1;
  return v_result;
end;
$$;

create or replace function public.product_preorder_set_fulfillment_preference(p_product_slug text,p_fulfillment_preference text,p_pickup_code text default null)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_user uuid := auth.uid(); v_product_id uuid; v_pickup_id uuid; v_updated integer := 0; v_method text := lower(btrim(coalesce(p_fulfillment_preference,'')));
begin
  if v_user is null then raise exception using errcode = '42501', message = 'AUTH_REQUIRED'; end if;
  if v_method not in ('shipping','pickup','undecided') then raise exception using errcode = '22023', message = 'INVALID_FULFILLMENT_PREFERENCE'; end if;
  select p.id into v_product_id from public.products p where p.slug = p_product_slug and p.active = true and p.product_type = 'novel' limit 1;
  if v_product_id is null then raise exception using errcode = '22023', message = 'PREORDER_PRODUCT_NOT_FOUND'; end if;
  if v_method = 'pickup' and nullif(btrim(coalesce(p_pickup_code,'')),'') is not null then
    select pp.id into v_pickup_id from public.preorder_pickup_points pp left join public.preorder_fulfillment_settings s on s.product_id = pp.product_id where pp.product_id = v_product_id and pp.pickup_code = lower(btrim(p_pickup_code)) and pp.active = true and pp.published_at is not null and coalesce(s.pickup_points_enabled,false) = true limit 1;
    if v_pickup_id is null then raise exception using errcode = '22023', message = 'PICKUP_POINT_NOT_AVAILABLE'; end if;
  end if;
  update public.product_preorders pp set fulfillment_preference = v_method,pickup_point_id = case when v_method = 'pickup' then v_pickup_id else null end where pp.user_id = v_user and pp.product_id = v_product_id and pp.status = 'reserved';
  get diagnostics v_updated = row_count; return v_updated > 0;
end;
$$;

create or replace function public.admin_preorder_fulfillment_get(p_product_slug text)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare v_product_id uuid; v_settings jsonb; v_zones jsonb; v_pickups jsonb; v_summary jsonb;
begin
  perform private.require_sinjira_admin_aal2();
  select p.id into v_product_id from public.products p where p.slug = p_product_slug limit 1;
  if v_product_id is null then raise exception using errcode='22023', message='PREORDER_PRODUCT_NOT_FOUND'; end if;
  select jsonb_build_object('currency', s.currency,'shipping_customer_pays', s.shipping_customer_pays,'shipping_estimates_enabled', s.shipping_estimates_enabled,'pickup_interest_enabled', s.pickup_interest_enabled,'pickup_points_enabled', s.pickup_points_enabled,'external_carrier_api_enabled', s.external_carrier_api_enabled,'external_shipping_purchase_enabled', s.external_shipping_purchase_enabled,'pickup_shipping_charge_cents', s.pickup_shipping_charge_cents,'updated_at', s.updated_at) into v_settings from public.preorder_fulfillment_settings s where s.product_id = v_product_id;
  if v_settings is null then v_settings := jsonb_build_object('currency','CAD','shipping_customer_pays',true,'shipping_estimates_enabled',false,'pickup_interest_enabled',true,'pickup_points_enabled',false,'external_carrier_api_enabled',false,'external_shipping_purchase_enabled',false,'pickup_shipping_charge_cents',0); end if;
  select coalesce(jsonb_agg(jsonb_build_object('zone_code',z.zone_code,'label',z.label,'country_code',z.country_code,'subdivision_code',z.subdivision_code,'currency',z.currency,'base_min_cents',z.base_min_cents,'base_max_cents',z.base_max_cents,'additional_copy_min_cents',z.additional_copy_min_cents,'additional_copy_max_cents',z.additional_copy_max_cents,'estimate_note',z.estimate_note,'active',z.active,'published_at',z.published_at,'updated_at',z.updated_at) order by z.label), '[]'::jsonb) into v_zones from public.preorder_shipping_zones z where z.product_id = v_product_id;
  select coalesce(jsonb_agg(jsonb_build_object('pickup_code',pp.pickup_code,'label',pp.label,'public_address',pp.public_address,'city',pp.city,'region',pp.region,'country_code',pp.country_code,'pickup_window_text',pp.pickup_window_text,'instructions',pp.instructions,'active',pp.active,'published_at',pp.published_at,'updated_at',pp.updated_at) order by pp.label), '[]'::jsonb) into v_pickups from public.preorder_pickup_points pp where pp.product_id = v_product_id;
  select jsonb_build_object('shipping', count(*) filter (where pp.status='reserved' and pp.fulfillment_preference='shipping'),'pickup', count(*) filter (where pp.status='reserved' and pp.fulfillment_preference='pickup'),'undecided', count(*) filter (where pp.status='reserved' and pp.fulfillment_preference='undecided')) into v_summary from public.product_preorders pp where pp.product_id = v_product_id;
  return jsonb_build_object('settings',v_settings,'zones',v_zones,'pickup_points',v_pickups,'summary',v_summary);
end;
$$;

create or replace function public.admin_preorder_fulfillment_settings_save(p_product_slug text,p_currency text default 'CAD',p_shipping_estimates_enabled boolean default false,p_pickup_points_enabled boolean default false)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_admin uuid; v_product_id uuid; v_currency text := upper(btrim(coalesce(p_currency,'CAD')));
begin
  v_admin := private.require_sinjira_admin_aal2();
  if v_currency !~ '^[A-Z]{3}$' then raise exception using errcode='22023', message='INVALID_CURRENCY'; end if;
  select p.id into v_product_id from public.products p where p.slug=p_product_slug limit 1;
  if v_product_id is null then raise exception using errcode='22023', message='PREORDER_PRODUCT_NOT_FOUND'; end if;
  insert into public.preorder_fulfillment_settings(product_id,currency,shipping_customer_pays,shipping_estimates_enabled,pickup_interest_enabled,pickup_points_enabled,external_carrier_api_enabled,external_shipping_purchase_enabled,pickup_shipping_charge_cents,updated_by)
  values (v_product_id,v_currency,true,coalesce(p_shipping_estimates_enabled,false),true,coalesce(p_pickup_points_enabled,false),false,false,0,v_admin)
  on conflict(product_id) do update set currency=excluded.currency,shipping_estimates_enabled=excluded.shipping_estimates_enabled,pickup_points_enabled=excluded.pickup_points_enabled,shipping_customer_pays=true,pickup_interest_enabled=true,external_carrier_api_enabled=false,external_shipping_purchase_enabled=false,pickup_shipping_charge_cents=0,updated_by=v_admin;
  return true;
end;
$$;

create or replace function public.admin_preorder_shipping_zone_save(p_product_slug text,p_zone_code text,p_label text,p_country_code text default null,p_subdivision_code text default null,p_currency text default 'CAD',p_base_min_cents integer default null,p_base_max_cents integer default null,p_additional_copy_min_cents integer default 0,p_additional_copy_max_cents integer default 0,p_estimate_note text default null,p_active boolean default true)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_admin uuid; v_product_id uuid; v_code text := lower(btrim(coalesce(p_zone_code,''))); v_currency text := upper(btrim(coalesce(p_currency,'CAD')));
begin
  v_admin := private.require_sinjira_admin_aal2();
  if v_code !~ '^[a-z0-9][a-z0-9_-]{1,39}$' then raise exception using errcode='22023', message='INVALID_ZONE_CODE'; end if;
  if char_length(btrim(coalesce(p_label,''))) < 2 then raise exception using errcode='22023', message='INVALID_ZONE_LABEL'; end if;
  if v_currency !~ '^[A-Z]{3}$' then raise exception using errcode='22023', message='INVALID_CURRENCY'; end if;
  if (p_base_min_cents is null) <> (p_base_max_cents is null) then raise exception using errcode='22023', message='INCOMPLETE_SHIPPING_RANGE'; end if;
  if p_base_min_cents is not null and (p_base_min_cents < 0 or p_base_max_cents < p_base_min_cents) then raise exception using errcode='22023', message='INVALID_SHIPPING_RANGE'; end if;
  if coalesce(p_additional_copy_min_cents,0) < 0 or coalesce(p_additional_copy_max_cents,0) < coalesce(p_additional_copy_min_cents,0) then raise exception using errcode='22023', message='INVALID_ADDITIONAL_SHIPPING_RANGE'; end if;
  select p.id into v_product_id from public.products p where p.slug=p_product_slug limit 1;
  if v_product_id is null then raise exception using errcode='22023', message='PREORDER_PRODUCT_NOT_FOUND'; end if;
  insert into public.preorder_shipping_zones(product_id,zone_code,label,country_code,subdivision_code,currency,base_min_cents,base_max_cents,additional_copy_min_cents,additional_copy_max_cents,estimate_note,active,published_at,created_by,updated_by)
  values (v_product_id,v_code,btrim(p_label),case when nullif(btrim(coalesce(p_country_code,'')),'') is null then null else upper(btrim(p_country_code)) end,nullif(upper(btrim(coalesce(p_subdivision_code,''))),''),v_currency,p_base_min_cents,p_base_max_cents,coalesce(p_additional_copy_min_cents,0),coalesce(p_additional_copy_max_cents,0),nullif(btrim(coalesce(p_estimate_note,'')),''),coalesce(p_active,true),null,v_admin,v_admin)
  on conflict(product_id,zone_code) do update set label=excluded.label,country_code=excluded.country_code,subdivision_code=excluded.subdivision_code,currency=excluded.currency,base_min_cents=excluded.base_min_cents,base_max_cents=excluded.base_max_cents,additional_copy_min_cents=excluded.additional_copy_min_cents,additional_copy_max_cents=excluded.additional_copy_max_cents,estimate_note=excluded.estimate_note,active=excluded.active,published_at=null,updated_by=v_admin;
  return true;
end;
$$;

create or replace function public.admin_preorder_shipping_zone_publish(p_product_slug text,p_zone_code text)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_admin uuid; v_updated integer:=0;
begin
  v_admin := private.require_sinjira_admin_aal2();
  update public.preorder_shipping_zones z set published_at=now(),active=true,updated_by=v_admin from public.products p where z.product_id=p.id and p.slug=p_product_slug and z.zone_code=lower(btrim(coalesce(p_zone_code,''))) and z.base_min_cents is not null and z.base_max_cents is not null;
  get diagnostics v_updated=row_count; return v_updated>0;
end;
$$;

create or replace function public.admin_preorder_pickup_point_save(p_product_slug text,p_pickup_code text,p_label text,p_public_address text default null,p_city text default null,p_region text default null,p_country_code text default 'CA',p_pickup_window_text text default null,p_instructions text default null,p_active boolean default true)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_admin uuid; v_product_id uuid; v_code text:=lower(btrim(coalesce(p_pickup_code,''))); v_country text:=upper(btrim(coalesce(p_country_code,'CA')));
begin
  v_admin := private.require_sinjira_admin_aal2();
  if v_code !~ '^[a-z0-9][a-z0-9_-]{1,39}$' then raise exception using errcode='22023', message='INVALID_PICKUP_CODE'; end if;
  if char_length(btrim(coalesce(p_label,'')))<2 then raise exception using errcode='22023', message='INVALID_PICKUP_LABEL'; end if;
  if v_country !~ '^[A-Z]{2}$' then raise exception using errcode='22023', message='INVALID_COUNTRY_CODE'; end if;
  select p.id into v_product_id from public.products p where p.slug=p_product_slug limit 1;
  if v_product_id is null then raise exception using errcode='22023', message='PREORDER_PRODUCT_NOT_FOUND'; end if;
  insert into public.preorder_pickup_points(product_id,pickup_code,label,public_address,city,region,country_code,pickup_window_text,instructions,active,published_at,created_by,updated_by)
  values (v_product_id,v_code,btrim(p_label),nullif(btrim(coalesce(p_public_address,'')),''),nullif(btrim(coalesce(p_city,'')),''),nullif(btrim(coalesce(p_region,'')),''),v_country,nullif(btrim(coalesce(p_pickup_window_text,'')),''),nullif(btrim(coalesce(p_instructions,'')),''),coalesce(p_active,true),null,v_admin,v_admin)
  on conflict(product_id,pickup_code) do update set label=excluded.label,public_address=excluded.public_address,city=excluded.city,region=excluded.region,country_code=excluded.country_code,pickup_window_text=excluded.pickup_window_text,instructions=excluded.instructions,active=excluded.active,published_at=null,updated_by=v_admin;
  return true;
end;
$$;

create or replace function public.admin_preorder_pickup_point_publish(p_product_slug text,p_pickup_code text)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_admin uuid; v_updated integer:=0;
begin
  v_admin := private.require_sinjira_admin_aal2();
  update public.preorder_pickup_points pp set published_at=now(),active=true,updated_by=v_admin from public.products p where pp.product_id=p.id and p.slug=p_product_slug and pp.pickup_code=lower(btrim(coalesce(p_pickup_code,''))) and nullif(btrim(coalesce(pp.public_address,'')),'') is not null and nullif(btrim(coalesce(pp.city,'')),'') is not null;
  get diagnostics v_updated=row_count; return v_updated>0;
end;
$$;

revoke all on function public.product_preorder_fulfillment_options(text) from public, anon, authenticated;
revoke all on function public.product_preorder_shipping_estimate(text,text,integer) from public, anon, authenticated;
revoke all on function public.product_preorder_fulfillment_status(text) from public, anon, authenticated;
revoke all on function public.product_preorder_set_fulfillment_preference(text,text,text) from public, anon, authenticated;
revoke all on function public.admin_preorder_fulfillment_get(text) from public, anon, authenticated;
revoke all on function public.admin_preorder_fulfillment_settings_save(text,text,boolean,boolean) from public, anon, authenticated;
revoke all on function public.admin_preorder_shipping_zone_save(text,text,text,text,text,text,integer,integer,integer,integer,text,boolean) from public, anon, authenticated;
revoke all on function public.admin_preorder_shipping_zone_publish(text,text) from public, anon, authenticated;
revoke all on function public.admin_preorder_pickup_point_save(text,text,text,text,text,text,text,text,text,boolean) from public, anon, authenticated;
revoke all on function public.admin_preorder_pickup_point_publish(text,text) from public, anon, authenticated;

grant execute on function public.product_preorder_fulfillment_options(text) to anon, authenticated;
grant execute on function public.product_preorder_shipping_estimate(text,text,integer) to anon, authenticated;
grant execute on function public.product_preorder_fulfillment_status(text) to authenticated;
grant execute on function public.product_preorder_set_fulfillment_preference(text,text,text) to authenticated;
grant execute on function public.admin_preorder_fulfillment_get(text) to authenticated;
grant execute on function public.admin_preorder_fulfillment_settings_save(text,text,boolean,boolean) to authenticated;
grant execute on function public.admin_preorder_shipping_zone_save(text,text,text,text,text,text,integer,integer,integer,integer,text,boolean) to authenticated;
grant execute on function public.admin_preorder_shipping_zone_publish(text,text) to authenticated;
grant execute on function public.admin_preorder_pickup_point_save(text,text,text,text,text,text,text,text,text,boolean) to authenticated;
grant execute on function public.admin_preorder_pickup_point_publish(text,text) to authenticated;
