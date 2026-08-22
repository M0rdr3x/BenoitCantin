create schema if not exists preorder_public_internal;
revoke all on schema preorder_public_internal from public;
grant usage on schema preorder_public_internal to anon, authenticated;

create or replace function preorder_public_internal.product_preorder_commercial_info(p_product_slug text)
returns table(
  product_slug text,
  product_name text,
  revision integer,
  currency text,
  paper_price_cents integer,
  digital_price_cents integer,
  paper_edition_label text,
  digital_edition_label text,
  release_at timestamptz,
  reservation_closes_at timestamptz,
  availability_note text,
  terms_summary text,
  published_at timestamptz,
  sales_enabled boolean,
  checkout_enabled boolean,
  payment_enabled boolean,
  external_fulfillment_enabled boolean,
  auto_conversion_allowed boolean
)
language sql
stable
security definer
set search_path = ''
as $$
  select
    p.slug,
    p.name,
    c.revision,
    c.currency,
    c.paper_price_cents,
    c.digital_price_cents,
    c.paper_edition_label,
    c.digital_edition_label,
    c.release_at,
    c.reservation_closes_at,
    c.availability_note,
    c.terms_summary,
    c.published_at,
    c.sales_enabled,
    c.checkout_enabled,
    c.payment_enabled,
    c.external_fulfillment_enabled,
    c.auto_conversion_allowed
  from public.preorder_commercial_plans c
  join public.products p on p.id = c.product_id
  where p.slug = p_product_slug
    and c.status = 'published'
  order by c.revision desc
  limit 1
$$;

revoke all on function preorder_public_internal.product_preorder_commercial_info(text) from public;
grant execute on function preorder_public_internal.product_preorder_commercial_info(text) to anon, authenticated;

create or replace function public.product_preorder_commercial_info(p_product_slug text)
returns table(
  product_slug text,
  product_name text,
  revision integer,
  currency text,
  paper_price_cents integer,
  digital_price_cents integer,
  paper_edition_label text,
  digital_edition_label text,
  release_at timestamptz,
  reservation_closes_at timestamptz,
  availability_note text,
  terms_summary text,
  published_at timestamptz,
  sales_enabled boolean,
  checkout_enabled boolean,
  payment_enabled boolean,
  external_fulfillment_enabled boolean,
  auto_conversion_allowed boolean
)
language sql
stable
security invoker
set search_path = ''
as $$
  select * from preorder_public_internal.product_preorder_commercial_info(p_product_slug)
$$;
revoke all on function public.product_preorder_commercial_info(text) from public;
grant execute on function public.product_preorder_commercial_info(text) to anon, authenticated;

create or replace function preorder_public_internal.product_preorder_fulfillment_options(p_product_slug text)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_product_id uuid;
  v_settings public.preorder_fulfillment_settings%rowtype;
  v_zones jsonb := '[]'::jsonb;
  v_pickups jsonb := '[]'::jsonb;
begin
  select p.id into v_product_id
  from public.products p
  where p.slug = p_product_slug and p.active = true and p.product_type = 'novel'
  limit 1;
  if v_product_id is null then return null; end if;

  select s.* into v_settings
  from public.preorder_fulfillment_settings s
  where s.product_id = v_product_id;

  if coalesce(v_settings.shipping_estimates_enabled,false) then
    select coalesce(jsonb_agg(jsonb_build_object(
      'zone_code', z.zone_code,
      'label', z.label,
      'country_code', z.country_code,
      'subdivision_code', z.subdivision_code,
      'currency', z.currency,
      'estimate_note', z.estimate_note
    ) order by z.label), '[]'::jsonb)
    into v_zones
    from public.preorder_shipping_zones z
    where z.product_id = v_product_id and z.active = true and z.published_at is not null;
  end if;

  if coalesce(v_settings.pickup_points_enabled,false) then
    select coalesce(jsonb_agg(jsonb_build_object(
      'pickup_code', pp.pickup_code,
      'label', pp.label,
      'public_address', pp.public_address,
      'city', pp.city,
      'region', pp.region,
      'country_code', pp.country_code,
      'pickup_window_text', pp.pickup_window_text,
      'instructions', pp.instructions
    ) order by pp.label), '[]'::jsonb)
    into v_pickups
    from public.preorder_pickup_points pp
    where pp.product_id = v_product_id and pp.active = true and pp.published_at is not null;
  end if;

  return jsonb_build_object(
    'shipping_customer_pays', true,
    'shipping_estimate_nonbinding', true,
    'shipping_estimates_enabled', coalesce(v_settings.shipping_estimates_enabled,false),
    'pickup_interest_enabled', true,
    'pickup_points_enabled', coalesce(v_settings.pickup_points_enabled,false),
    'pickup_shipping_charge_cents', 0,
    'external_carrier_api_enabled', false,
    'external_shipping_purchase_enabled', false,
    'shipping_zones', v_zones,
    'pickup_points', v_pickups
  );
end;
$$;
revoke all on function preorder_public_internal.product_preorder_fulfillment_options(text) from public;
grant execute on function preorder_public_internal.product_preorder_fulfillment_options(text) to anon, authenticated;

create or replace function public.product_preorder_fulfillment_options(p_product_slug text)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $$
  select preorder_public_internal.product_preorder_fulfillment_options(p_product_slug)
$$;
revoke all on function public.product_preorder_fulfillment_options(text) from public;
grant execute on function public.product_preorder_fulfillment_options(text) to anon, authenticated;

create or replace function preorder_public_internal.product_preorder_shipping_estimate(
  p_product_slug text,
  p_zone_code text,
  p_quantity integer default 1
)
returns table(
  zone_code text,
  zone_label text,
  currency text,
  estimate_min_cents integer,
  estimate_max_cents integer,
  estimate_note text,
  shipping_customer_pays boolean,
  estimate_nonbinding boolean
)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_product_id uuid;
  v_zone public.preorder_shipping_zones%rowtype;
  v_enabled boolean := false;
begin
  if p_quantity is null or p_quantity < 1 or p_quantity > 5 then
    raise exception using errcode = '22023', message = 'INVALID_PREORDER_QUANTITY';
  end if;

  select p.id into v_product_id
  from public.products p
  where p.slug = p_product_slug and p.active = true and p.product_type = 'novel'
  limit 1;
  if v_product_id is null then return; end if;

  select s.shipping_estimates_enabled into v_enabled
  from public.preorder_fulfillment_settings s
  where s.product_id = v_product_id;
  if not coalesce(v_enabled,false) then return; end if;

  select z.* into v_zone
  from public.preorder_shipping_zones z
  where z.product_id = v_product_id
    and z.zone_code = lower(btrim(coalesce(p_zone_code,'')))
    and z.active = true
    and z.published_at is not null
  limit 1;

  if v_zone.id is null or v_zone.base_min_cents is null or v_zone.base_max_cents is null then return; end if;

  return query select
    v_zone.zone_code,
    v_zone.label,
    v_zone.currency,
    v_zone.base_min_cents + greatest(p_quantity - 1,0) * v_zone.additional_copy_min_cents,
    v_zone.base_max_cents + greatest(p_quantity - 1,0) * v_zone.additional_copy_max_cents,
    v_zone.estimate_note,
    true,
    true;
end;
$$;
revoke all on function preorder_public_internal.product_preorder_shipping_estimate(text,text,integer) from public;
grant execute on function preorder_public_internal.product_preorder_shipping_estimate(text,text,integer) to anon, authenticated;

create or replace function public.product_preorder_shipping_estimate(
  p_product_slug text,
  p_zone_code text,
  p_quantity integer default 1
)
returns table(
  zone_code text,
  zone_label text,
  currency text,
  estimate_min_cents integer,
  estimate_max_cents integer,
  estimate_note text,
  shipping_customer_pays boolean,
  estimate_nonbinding boolean
)
language sql
stable
security invoker
set search_path = ''
as $$
  select * from preorder_public_internal.product_preorder_shipping_estimate(p_product_slug, p_zone_code, p_quantity)
$$;
revoke all on function public.product_preorder_shipping_estimate(text,text,integer) from public;
grant execute on function public.product_preorder_shipping_estimate(text,text,integer) to anon, authenticated;

-- Une seule politique SELECT évite deux politiques permissives concurrentes.
drop policy if exists product_preorders_admin_read on public.product_preorders;
drop policy if exists product_preorders_own_read on public.product_preorders;
drop policy if exists product_preorders_read on public.product_preorders;
create policy product_preorders_read
on public.product_preorders
for select
to authenticated
using (
  (select auth.uid()) = user_id
  or public.is_sinjira_admin((select auth.uid()))
);

-- Couverture des anciennes clés étrangères signalées par l'advisor performance.
create index if not exists moderation_appeals_reviewed_by_fkey_idx on private.moderation_appeals(reviewed_by);
create index if not exists moderation_decisions_decided_by_fkey_idx on private.moderation_decisions(decided_by);
create index if not exists moderation_decisions_reversed_by_fkey_idx on private.moderation_decisions(reversed_by);
create index if not exists privacy_incident_register_created_by_fkey_idx on private.privacy_incident_register(created_by);
create index if not exists privacy_incident_register_updated_by_fkey_idx on private.privacy_incident_register(updated_by);
create index if not exists privacy_legal_holds_created_by_fkey_idx on private.privacy_legal_holds(created_by);
create index if not exists privacy_legal_holds_user_id_fkey_idx on private.privacy_legal_holds(user_id);
create index if not exists dating_connections_requested_by_profile_id_fkey_idx on public.dating_connections(requested_by_profile_id);
create index if not exists dating_messages_sender_profile_id_fkey_idx on public.dating_messages(sender_profile_id);

comment on schema preorder_public_internal is
  'Schéma interne non exposé directement par PostgREST. Les wrappers publics de précommande restent SECURITY INVOKER; seuls des lecteurs internes strictement bornés utilisent SECURITY DEFINER.';
