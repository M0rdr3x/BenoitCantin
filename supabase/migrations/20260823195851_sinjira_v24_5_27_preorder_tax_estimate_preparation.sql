create table if not exists public.preorder_tax_estimate_profiles (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  tax_code text not null,
  label text not null,
  country_code text,
  subdivision_code text,
  paper_rate_basis_points integer,
  digital_rate_basis_points integer,
  shipping_rate_basis_points integer,
  source_reference text,
  effective_on date,
  estimate_note text,
  active boolean not null default true,
  published_at timestamptz,
  created_by uuid references auth.users(id) on delete set null,
  updated_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint preorder_tax_profiles_product_code_key unique(product_id,tax_code),
  constraint preorder_tax_profiles_code_check check (tax_code ~ '^[a-z0-9][a-z0-9_-]{1,39}$'),
  constraint preorder_tax_profiles_country_check check (country_code is null or country_code ~ '^[A-Z]{2}$'),
  constraint preorder_tax_profiles_rates_check check (
    (paper_rate_basis_points is null or paper_rate_basis_points between 0 and 10000)
    and (digital_rate_basis_points is null or digital_rate_basis_points between 0 and 10000)
    and (shipping_rate_basis_points is null or shipping_rate_basis_points between 0 and 10000)
  )
);

comment on table public.preorder_tax_estimate_profiles is
  'Profils fiscaux indicatifs V24.5.27. Aucun profil n est créé automatiquement; publication humaine requise; jamais utilisé comme montant de facturation.';
comment on column public.preorder_tax_estimate_profiles.source_reference is
  'Référence publique ou note de vérification du taux. Obligatoire avant publication, sans document sensible.';
comment on column public.preorder_tax_estimate_profiles.published_at is
  'Un profil est lisible publiquement uniquement après publication explicite par un administrateur MFA/AAL2.';

create index if not exists preorder_tax_profiles_product_published_idx
  on public.preorder_tax_estimate_profiles(product_id,active,published_at);
create index if not exists preorder_tax_profiles_created_by_idx
  on public.preorder_tax_estimate_profiles(created_by);
create index if not exists preorder_tax_profiles_updated_by_idx
  on public.preorder_tax_estimate_profiles(updated_by);

alter table public.preorder_tax_estimate_profiles enable row level security;
revoke all on table public.preorder_tax_estimate_profiles from public, anon, authenticated;
grant select,insert,update,delete on table public.preorder_tax_estimate_profiles to service_role;

drop policy if exists preorder_tax_profiles_service_role on public.preorder_tax_estimate_profiles;
create policy preorder_tax_profiles_service_role
on public.preorder_tax_estimate_profiles
for all to service_role
using (true)
with check (true);

create schema if not exists preorder_tax_internal;
revoke all on schema preorder_tax_internal from public;
grant usage on schema preorder_tax_internal to anon, authenticated, service_role;

create or replace function preorder_tax_internal.admin_preorder_tax_get(p_product_slug text)
returns jsonb
language plpgsql
security definer
set search_path=''
as $$
declare
  v_product_id uuid;
  v_profiles jsonb := '[]'::jsonb;
begin
  perform private.require_sinjira_admin_aal2();
  select id into v_product_id from public.products where slug=p_product_slug and active=true limit 1;
  if v_product_id is null then
    raise exception using errcode='22023',message='PREORDER_PRODUCT_NOT_FOUND';
  end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'tax_code',t.tax_code,'label',t.label,'country_code',t.country_code,'subdivision_code',t.subdivision_code,
    'paper_rate_basis_points',t.paper_rate_basis_points,'digital_rate_basis_points',t.digital_rate_basis_points,
    'shipping_rate_basis_points',t.shipping_rate_basis_points,'source_reference',t.source_reference,
    'effective_on',t.effective_on,'estimate_note',t.estimate_note,'active',t.active,'published_at',t.published_at,
    'updated_at',t.updated_at
  ) order by t.tax_code),'[]'::jsonb) into v_profiles
  from public.preorder_tax_estimate_profiles t where t.product_id=v_product_id;
  return jsonb_build_object(
    'profiles',v_profiles,
    'external_tax_api_enabled',false,
    'billing_authoritative',false,
    'estimate_nonbinding',true,
    'final_tax_confirmation_required',true
  );
end;
$$;

create or replace function preorder_tax_internal.admin_preorder_tax_profile_save(
  p_product_slug text,
  p_tax_code text,
  p_label text,
  p_country_code text default null,
  p_subdivision_code text default null,
  p_paper_rate_basis_points integer default null,
  p_digital_rate_basis_points integer default null,
  p_shipping_rate_basis_points integer default null,
  p_source_reference text default null,
  p_effective_on date default null,
  p_estimate_note text default null,
  p_active boolean default true
)
returns uuid
language plpgsql
security definer
set search_path=''
as $$
declare
  v_admin uuid := auth.uid();
  v_product_id uuid;
  v_id uuid;
  v_code text := lower(btrim(coalesce(p_tax_code,'')));
begin
  perform private.require_sinjira_admin_aal2();
  select id into v_product_id from public.products where slug=p_product_slug and active=true limit 1;
  if v_product_id is null then raise exception using errcode='22023',message='PREORDER_PRODUCT_NOT_FOUND'; end if;
  if v_code !~ '^[a-z0-9][a-z0-9_-]{1,39}$' then raise exception using errcode='22023',message='INVALID_TAX_CODE'; end if;
  if nullif(btrim(coalesce(p_label,'')),'') is null then raise exception using errcode='22023',message='TAX_LABEL_REQUIRED'; end if;
  if p_country_code is not null and upper(btrim(p_country_code)) !~ '^[A-Z]{2}$' then raise exception using errcode='22023',message='INVALID_COUNTRY_CODE'; end if;
  if coalesce(p_paper_rate_basis_points,0) < 0 or coalesce(p_paper_rate_basis_points,0) > 10000
     or coalesce(p_digital_rate_basis_points,0) < 0 or coalesce(p_digital_rate_basis_points,0) > 10000
     or coalesce(p_shipping_rate_basis_points,0) < 0 or coalesce(p_shipping_rate_basis_points,0) > 10000 then
    raise exception using errcode='22023',message='INVALID_TAX_RATE';
  end if;

  insert into public.preorder_tax_estimate_profiles(
    product_id,tax_code,label,country_code,subdivision_code,paper_rate_basis_points,digital_rate_basis_points,
    shipping_rate_basis_points,source_reference,effective_on,estimate_note,active,published_at,created_by,updated_by
  ) values (
    v_product_id,v_code,btrim(p_label),nullif(upper(btrim(coalesce(p_country_code,''))),''),
    nullif(upper(btrim(coalesce(p_subdivision_code,''))),''),p_paper_rate_basis_points,p_digital_rate_basis_points,
    p_shipping_rate_basis_points,nullif(btrim(coalesce(p_source_reference,'')),''),p_effective_on,
    nullif(btrim(coalesce(p_estimate_note,'')),''),coalesce(p_active,true),null,v_admin,v_admin
  )
  on conflict(product_id,tax_code) do update set
    label=excluded.label,country_code=excluded.country_code,subdivision_code=excluded.subdivision_code,
    paper_rate_basis_points=excluded.paper_rate_basis_points,digital_rate_basis_points=excluded.digital_rate_basis_points,
    shipping_rate_basis_points=excluded.shipping_rate_basis_points,source_reference=excluded.source_reference,
    effective_on=excluded.effective_on,estimate_note=excluded.estimate_note,active=excluded.active,
    published_at=null,updated_by=v_admin,updated_at=now()
  returning id into v_id;
  return v_id;
end;
$$;

create or replace function preorder_tax_internal.admin_preorder_tax_profile_publish(p_product_slug text,p_tax_code text)
returns boolean
language plpgsql
security definer
set search_path=''
as $$
declare
  v_product_id uuid;
  v_updated integer := 0;
begin
  perform private.require_sinjira_admin_aal2();
  select id into v_product_id from public.products where slug=p_product_slug and active=true limit 1;
  if v_product_id is null then raise exception using errcode='22023',message='PREORDER_PRODUCT_NOT_FOUND'; end if;
  update public.preorder_tax_estimate_profiles t set published_at=now(),updated_by=auth.uid(),updated_at=now()
  where t.product_id=v_product_id
    and t.tax_code=lower(btrim(coalesce(p_tax_code,'')))
    and t.active=true
    and nullif(btrim(coalesce(t.source_reference,'')),'') is not null
    and t.effective_on is not null
    and (t.paper_rate_basis_points is not null or t.digital_rate_basis_points is not null or t.shipping_rate_basis_points is not null);
  get diagnostics v_updated=row_count;
  return v_updated=1;
end;
$$;

create or replace function preorder_tax_internal.product_preorder_tax_options(p_product_slug text)
returns jsonb
language plpgsql
stable
security definer
set search_path=''
as $$
declare
  v_product_id uuid;
  v_profiles jsonb := '[]'::jsonb;
begin
  select id into v_product_id from public.products where slug=p_product_slug and active=true and product_type='novel' limit 1;
  if v_product_id is null then
    return jsonb_build_object('tax_profiles','[]'::jsonb,'estimate_nonbinding',true,'billing_authoritative',false,'external_tax_api_enabled',false,'final_tax_confirmation_required',true);
  end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'tax_code',t.tax_code,'label',t.label,'country_code',t.country_code,'subdivision_code',t.subdivision_code,
    'paper_rate_basis_points',t.paper_rate_basis_points,'digital_rate_basis_points',t.digital_rate_basis_points,
    'shipping_rate_basis_points',t.shipping_rate_basis_points,'source_reference',t.source_reference,
    'effective_on',t.effective_on,'estimate_note',t.estimate_note
  ) order by t.label),'[]'::jsonb) into v_profiles
  from public.preorder_tax_estimate_profiles t
  where t.product_id=v_product_id and t.active=true and t.published_at is not null;
  return jsonb_build_object(
    'tax_profiles',v_profiles,
    'estimate_nonbinding',true,
    'billing_authoritative',false,
    'external_tax_api_enabled',false,
    'final_tax_confirmation_required',true
  );
end;
$$;

create or replace function preorder_tax_internal.product_preorder_tax_estimate(
  p_product_slug text,
  p_tax_code text,
  p_format text,
  p_quantity integer default 1,
  p_fulfillment_method text default 'undecided',
  p_shipping_zone_code text default null
)
returns table(
  tax_code text,
  tax_label text,
  currency text,
  subtotal_min_cents integer,
  subtotal_max_cents integer,
  estimated_tax_min_cents integer,
  estimated_tax_max_cents integer,
  estimated_total_min_cents integer,
  estimated_total_max_cents integer,
  source_reference text,
  effective_on date,
  estimate_note text,
  estimate_complete boolean,
  estimate_nonbinding boolean,
  billing_authoritative boolean,
  external_tax_api_enabled boolean,
  final_tax_confirmation_required boolean
)
language plpgsql
stable
security definer
set search_path=''
as $$
declare
  v_product_id uuid;
  v_tax public.preorder_tax_estimate_profiles%rowtype;
  v_com public.preorder_commercial_plans%rowtype;
  v_ship public.preorder_shipping_zones%rowtype;
  v_shipping_enabled boolean := false;
  v_book integer := 0;
  v_book_tax integer := 0;
  v_ship_min integer := 0;
  v_ship_max integer := 0;
  v_ship_tax_min integer := 0;
  v_ship_tax_max integer := 0;
  v_complete boolean := true;
begin
  if p_quantity is null or p_quantity < 1 or p_quantity > 5 then raise exception using errcode='22023',message='INVALID_PREORDER_QUANTITY'; end if;
  if p_format not in ('paper','digital','both') then raise exception using errcode='22023',message='INVALID_PREORDER_FORMAT'; end if;
  if p_fulfillment_method not in ('shipping','pickup','undecided') then raise exception using errcode='22023',message='INVALID_FULFILLMENT_METHOD'; end if;

  select id into v_product_id from public.products where slug=p_product_slug and active=true and product_type='novel' limit 1;
  if v_product_id is null then return; end if;
  select * into v_tax from public.preorder_tax_estimate_profiles t where t.product_id=v_product_id and t.tax_code=lower(btrim(coalesce(p_tax_code,''))) and t.active=true and t.published_at is not null limit 1;
  if v_tax.id is null then return; end if;
  select * into v_com from public.preorder_commercial_plans c where c.product_id=v_product_id and c.status='published' order by c.revision desc limit 1;
  if v_com.id is null or v_com.sales_enabled is distinct from false or v_com.checkout_enabled is distinct from false or v_com.payment_enabled is distinct from false or v_com.external_fulfillment_enabled is distinct from false or v_com.auto_conversion_allowed is distinct from false then return; end if;

  if p_format in ('paper','both') then
    if v_com.paper_price_cents is null or v_tax.paper_rate_basis_points is null then v_complete:=false;
    else
      v_book:=v_book + v_com.paper_price_cents*p_quantity;
      v_book_tax:=v_book_tax + round((v_com.paper_price_cents*p_quantity)::numeric*v_tax.paper_rate_basis_points/10000)::integer;
    end if;
  end if;
  if p_format in ('digital','both') then
    if v_com.digital_price_cents is null or v_tax.digital_rate_basis_points is null then v_complete:=false;
    else
      v_book:=v_book + v_com.digital_price_cents*p_quantity;
      v_book_tax:=v_book_tax + round((v_com.digital_price_cents*p_quantity)::numeric*v_tax.digital_rate_basis_points/10000)::integer;
    end if;
  end if;

  if p_format in ('paper','both') then
    if p_fulfillment_method='pickup' then
      v_ship_min:=0;v_ship_max:=0;
    elsif p_fulfillment_method='shipping' then
      select shipping_estimates_enabled into v_shipping_enabled from public.preorder_fulfillment_settings where product_id=v_product_id;
      select * into v_ship from public.preorder_shipping_zones z where z.product_id=v_product_id and z.zone_code=lower(btrim(coalesce(p_shipping_zone_code,''))) and z.active=true and z.published_at is not null limit 1;
      if not coalesce(v_shipping_enabled,false) or v_ship.id is null or v_ship.base_min_cents is null or v_ship.base_max_cents is null or v_ship.currency<>v_com.currency or v_tax.shipping_rate_basis_points is null then
        v_complete:=false;
      else
        v_ship_min:=v_ship.base_min_cents+greatest(p_quantity-1,0)*v_ship.additional_copy_min_cents;
        v_ship_max:=v_ship.base_max_cents+greatest(p_quantity-1,0)*v_ship.additional_copy_max_cents;
        v_ship_tax_min:=round(v_ship_min::numeric*v_tax.shipping_rate_basis_points/10000)::integer;
        v_ship_tax_max:=round(v_ship_max::numeric*v_tax.shipping_rate_basis_points/10000)::integer;
      end if;
    else
      v_complete:=false;
    end if;
  end if;

  return query select
    v_tax.tax_code,v_tax.label,v_com.currency,
    case when v_complete then v_book+v_ship_min else null end,
    case when v_complete then v_book+v_ship_max else null end,
    case when v_complete then v_book_tax+v_ship_tax_min else null end,
    case when v_complete then v_book_tax+v_ship_tax_max else null end,
    case when v_complete then v_book+v_ship_min+v_book_tax+v_ship_tax_min else null end,
    case when v_complete then v_book+v_ship_max+v_book_tax+v_ship_tax_max else null end,
    v_tax.source_reference,v_tax.effective_on,v_tax.estimate_note,v_complete,true,false,false,true;
end;
$$;

revoke all on function preorder_tax_internal.admin_preorder_tax_get(text) from public,anon;
revoke all on function preorder_tax_internal.admin_preorder_tax_profile_save(text,text,text,text,text,integer,integer,integer,text,date,text,boolean) from public,anon;
revoke all on function preorder_tax_internal.admin_preorder_tax_profile_publish(text,text) from public,anon;
revoke all on function preorder_tax_internal.product_preorder_tax_options(text) from public;
revoke all on function preorder_tax_internal.product_preorder_tax_estimate(text,text,text,integer,text,text) from public;
grant execute on function preorder_tax_internal.admin_preorder_tax_get(text) to authenticated,service_role;
grant execute on function preorder_tax_internal.admin_preorder_tax_profile_save(text,text,text,text,text,integer,integer,integer,text,date,text,boolean) to authenticated,service_role;
grant execute on function preorder_tax_internal.admin_preorder_tax_profile_publish(text,text) to authenticated,service_role;
grant execute on function preorder_tax_internal.product_preorder_tax_options(text) to anon,authenticated,service_role;
grant execute on function preorder_tax_internal.product_preorder_tax_estimate(text,text,text,integer,text,text) to anon,authenticated,service_role;

create or replace function public.admin_preorder_tax_get(p_product_slug text)
returns jsonb language sql security invoker set search_path='' as $$select preorder_tax_internal.admin_preorder_tax_get($1)$$;
create or replace function public.admin_preorder_tax_profile_save(p_product_slug text,p_tax_code text,p_label text,p_country_code text default null,p_subdivision_code text default null,p_paper_rate_basis_points integer default null,p_digital_rate_basis_points integer default null,p_shipping_rate_basis_points integer default null,p_source_reference text default null,p_effective_on date default null,p_estimate_note text default null,p_active boolean default true)
returns uuid language sql security invoker set search_path='' as $$select preorder_tax_internal.admin_preorder_tax_profile_save($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)$$;
create or replace function public.admin_preorder_tax_profile_publish(p_product_slug text,p_tax_code text)
returns boolean language sql security invoker set search_path='' as $$select preorder_tax_internal.admin_preorder_tax_profile_publish($1,$2)$$;
create or replace function public.product_preorder_tax_options(p_product_slug text)
returns jsonb language sql stable security invoker set search_path='' as $$select preorder_tax_internal.product_preorder_tax_options($1)$$;
create or replace function public.product_preorder_tax_estimate(p_product_slug text,p_tax_code text,p_format text,p_quantity integer default 1,p_fulfillment_method text default 'undecided',p_shipping_zone_code text default null)
returns table(tax_code text,tax_label text,currency text,subtotal_min_cents integer,subtotal_max_cents integer,estimated_tax_min_cents integer,estimated_tax_max_cents integer,estimated_total_min_cents integer,estimated_total_max_cents integer,source_reference text,effective_on date,estimate_note text,estimate_complete boolean,estimate_nonbinding boolean,billing_authoritative boolean,external_tax_api_enabled boolean,final_tax_confirmation_required boolean)
language sql stable security invoker set search_path='' as $$select * from preorder_tax_internal.product_preorder_tax_estimate($1,$2,$3,$4,$5,$6)$$;

revoke all on function public.admin_preorder_tax_get(text) from public,anon;
revoke all on function public.admin_preorder_tax_profile_save(text,text,text,text,text,integer,integer,integer,text,date,text,boolean) from public,anon;
revoke all on function public.admin_preorder_tax_profile_publish(text,text) from public,anon;
revoke all on function public.product_preorder_tax_options(text) from public;
revoke all on function public.product_preorder_tax_estimate(text,text,text,integer,text,text) from public;
grant execute on function public.admin_preorder_tax_get(text) to authenticated,service_role;
grant execute on function public.admin_preorder_tax_profile_save(text,text,text,text,text,integer,integer,integer,text,date,text,boolean) to authenticated,service_role;
grant execute on function public.admin_preorder_tax_profile_publish(text,text) to authenticated,service_role;
grant execute on function public.product_preorder_tax_options(text) to anon,authenticated,service_role;
grant execute on function public.product_preorder_tax_estimate(text,text,text,integer,text,text) to anon,authenticated,service_role;
