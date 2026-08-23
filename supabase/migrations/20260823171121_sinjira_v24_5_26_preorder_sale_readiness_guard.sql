create schema if not exists preorder_readiness_internal;
revoke all on schema preorder_readiness_internal from public, anon;
grant usage on schema preorder_readiness_internal to authenticated, service_role;

create or replace function preorder_readiness_internal.sale_readiness(p_product_slug text)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_product_id uuid;
  v_plan public.preorder_commercial_plans%rowtype;
  v_settings public.preorder_fulfillment_settings%rowtype;
  v_shipping_zone_count integer := 0;
  v_pickup_count integer := 0;
  v_has_paper boolean := false;
  v_has_digital boolean := false;
  v_shipping_ready boolean := false;
  v_pickup_ready boolean := false;
  v_paper_fulfillment_ready boolean := true;
  v_locks_ok boolean := false;
  v_ready boolean := false;
  v_blockers jsonb := '[]'::jsonb;
begin
  perform private.require_sinjira_admin_aal2();

  select id into v_product_id
  from public.products
  where slug = p_product_slug
  limit 1;

  if v_product_id is null then
    raise exception 'PRODUCT_NOT_FOUND';
  end if;

  select * into v_plan
  from public.preorder_commercial_plans
  where product_id = v_product_id and status = 'published'
  order by revision desc
  limit 1;

  select * into v_settings
  from public.preorder_fulfillment_settings
  where product_id = v_product_id
  limit 1;

  select count(*) into v_shipping_zone_count
  from public.preorder_shipping_zones
  where product_id = v_product_id
    and active is true
    and published_at is not null
    and base_min_cents is not null
    and base_max_cents is not null
    and base_min_cents >= 0
    and base_max_cents >= base_min_cents;

  select count(*) into v_pickup_count
  from public.preorder_pickup_points
  where product_id = v_product_id
    and active is true
    and published_at is not null
    and coalesce(nullif(btrim(label),''), '') <> ''
    and coalesce(nullif(btrim(public_address),''), '') <> '';

  if v_plan.id is null then
    v_blockers := v_blockers || jsonb_build_array('Publier une fiche commerciale avant toute future ouverture de vente.');
  else
    v_has_paper := v_plan.paper_price_cents is not null;
    v_has_digital := v_plan.digital_price_cents is not null;

    if not (v_has_paper or v_has_digital) then
      v_blockers := v_blockers || jsonb_build_array('Publier au moins un prix officiel pour une édition réellement offerte.');
    end if;
    if v_plan.release_at is null then
      v_blockers := v_blockers || jsonb_build_array('Publier une date ou heure de sortie officielle.');
    end if;
    if coalesce(length(btrim(v_plan.terms_summary)),0) < 20 then
      v_blockers := v_blockers || jsonb_build_array('Compléter le résumé des conditions avant toute future vente.');
    end if;
    if coalesce(length(btrim(v_plan.availability_note)),0) < 10 then
      v_blockers := v_blockers || jsonb_build_array('Compléter l’information de disponibilité ou de production.');
    end if;
    if v_has_paper and coalesce(length(btrim(v_plan.paper_edition_label)),0) = 0 then
      v_blockers := v_blockers || jsonb_build_array('Nommer clairement l’édition papier associée au prix publié.');
    end if;
    if v_has_digital and coalesce(length(btrim(v_plan.digital_edition_label)),0) = 0 then
      v_blockers := v_blockers || jsonb_build_array('Nommer clairement l’édition numérique associée au prix publié.');
    end if;
    if v_plan.sales_enabled or v_plan.checkout_enabled or v_plan.payment_enabled or v_plan.external_fulfillment_enabled or v_plan.auto_conversion_allowed then
      v_blockers := v_blockers || jsonb_build_array('Les verrous commerciaux doivent rester désactivés pendant la phase de préparation.');
    end if;
  end if;

  if v_settings.product_id is null then
    if v_has_paper then
      v_blockers := v_blockers || jsonb_build_array('Configurer la réception du livre papier avant toute future vente.');
    end if;
  else
    v_shipping_ready := v_settings.shipping_estimates_enabled is true and v_shipping_zone_count > 0;
    v_pickup_ready := v_settings.pickup_points_enabled is true and v_pickup_count > 0;
    v_paper_fulfillment_ready := (not v_has_paper) or v_shipping_ready or v_pickup_ready;
    v_locks_ok := v_settings.shipping_customer_pays is true
      and v_settings.external_carrier_api_enabled is false
      and v_settings.external_shipping_purchase_enabled is false
      and v_settings.pickup_shipping_charge_cents = 0;

    if v_has_paper and not v_paper_fulfillment_ready then
      v_blockers := v_blockers || jsonb_build_array('Publier au moins une estimation de livraison valide ou un point de ramassage avant toute future vente papier.');
    end if;
    if not v_locks_ok then
      v_blockers := v_blockers || jsonb_build_array('Rétablir les verrous de livraison : frais client, aucune API transporteur, aucun achat externe et ramassage à 0 $ de frais de livraison.');
    end if;
  end if;

  v_ready := v_plan.id is not null
    and (v_has_paper or v_has_digital)
    and v_plan.release_at is not null
    and coalesce(length(btrim(v_plan.terms_summary)),0) >= 20
    and coalesce(length(btrim(v_plan.availability_note)),0) >= 10
    and ((not v_has_paper) or coalesce(length(btrim(v_plan.paper_edition_label)),0) > 0)
    and ((not v_has_digital) or coalesce(length(btrim(v_plan.digital_edition_label)),0) > 0)
    and not v_plan.sales_enabled
    and not v_plan.checkout_enabled
    and not v_plan.payment_enabled
    and not v_plan.external_fulfillment_enabled
    and not v_plan.auto_conversion_allowed
    and ((not v_has_paper) or (v_settings.product_id is not null and v_paper_fulfillment_ready and v_locks_ok));

  return jsonb_build_object(
    'product_slug', p_product_slug,
    'ready_for_future_manual_opening', v_ready,
    'commercial_plan_published', v_plan.id is not null,
    'paper_price_published', v_has_paper,
    'digital_price_published', v_has_digital,
    'release_date_published', v_plan.release_at is not null,
    'terms_ready', coalesce(length(btrim(v_plan.terms_summary)),0) >= 20,
    'availability_ready', coalesce(length(btrim(v_plan.availability_note)),0) >= 10,
    'shipping_estimate_ready', v_shipping_ready,
    'pickup_ready', v_pickup_ready,
    'paper_fulfillment_ready', v_paper_fulfillment_ready,
    'shipping_customer_pays', coalesce(v_settings.shipping_customer_pays,true),
    'pickup_shipping_charge_cents', coalesce(v_settings.pickup_shipping_charge_cents,0),
    'sales_enabled', coalesce(v_plan.sales_enabled,false),
    'checkout_enabled', coalesce(v_plan.checkout_enabled,false),
    'payment_enabled', coalesce(v_plan.payment_enabled,false),
    'external_fulfillment_enabled', coalesce(v_plan.external_fulfillment_enabled,false),
    'auto_conversion_allowed', coalesce(v_plan.auto_conversion_allowed,false),
    'external_carrier_api_enabled', coalesce(v_settings.external_carrier_api_enabled,false),
    'external_shipping_purchase_enabled', coalesce(v_settings.external_shipping_purchase_enabled,false),
    'published_shipping_zones', v_shipping_zone_count,
    'published_pickup_points', v_pickup_count,
    'taxes_calculated_by_sinjira', false,
    'blockers', v_blockers
  );
end;
$$;

revoke all on function preorder_readiness_internal.sale_readiness(text) from public, anon;
grant execute on function preorder_readiness_internal.sale_readiness(text) to authenticated, service_role;

create or replace function public.admin_preorder_sale_readiness(p_product_slug text)
returns jsonb
language sql
security invoker
set search_path = pg_catalog, public, private, preorder_readiness_internal
as $$
  select preorder_readiness_internal.sale_readiness(p_product_slug);
$$;

revoke all on function public.admin_preorder_sale_readiness(text) from public, anon;
grant execute on function public.admin_preorder_sale_readiness(text) to authenticated, service_role;
