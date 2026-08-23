alter table public.preorder_tax_estimate_profiles
  drop constraint if exists preorder_tax_profiles_label_length_check,
  drop constraint if exists preorder_tax_profiles_subdivision_length_check,
  drop constraint if exists preorder_tax_profiles_source_length_check,
  drop constraint if exists preorder_tax_profiles_note_length_check,
  add constraint preorder_tax_profiles_label_length_check check (char_length(btrim(label)) between 1 and 160),
  add constraint preorder_tax_profiles_subdivision_length_check check (subdivision_code is null or char_length(subdivision_code) <= 24),
  add constraint preorder_tax_profiles_source_length_check check (source_reference is null or char_length(source_reference) <= 700),
  add constraint preorder_tax_profiles_note_length_check check (estimate_note is null or char_length(estimate_note) <= 900);

create or replace function preorder_tax_internal.product_preorder_tax_estimate(
  p_product_slug text,p_tax_code text,p_format text,p_quantity integer default 1,
  p_fulfillment_method text default 'undecided',p_shipping_zone_code text default null
)
returns table(tax_code text,tax_label text,currency text,subtotal_min_cents integer,subtotal_max_cents integer,
  estimated_tax_min_cents integer,estimated_tax_max_cents integer,estimated_total_min_cents integer,
  estimated_total_max_cents integer,source_reference text,effective_on date,estimate_note text,
  estimate_complete boolean,estimate_nonbinding boolean,billing_authoritative boolean,
  external_tax_api_enabled boolean,final_tax_confirmation_required boolean)
language plpgsql stable security definer set search_path=''
as $$
declare
  v_product_id uuid; v_tax public.preorder_tax_estimate_profiles%rowtype; v_com public.preorder_commercial_plans%rowtype;
  v_ship public.preorder_shipping_zones%rowtype; v_shipping_enabled boolean:=false; v_book integer:=0; v_book_tax integer:=0;
  v_ship_min integer:=0; v_ship_max integer:=0; v_ship_tax_min integer:=0; v_ship_tax_max integer:=0; v_complete boolean:=true;
begin
  if p_quantity is null or p_quantity<1 or p_quantity>5 then raise exception using errcode='22023',message='INVALID_PREORDER_QUANTITY'; end if;
  if p_format is null or p_format not in ('paper','digital','both') then raise exception using errcode='22023',message='INVALID_PREORDER_FORMAT'; end if;
  if p_fulfillment_method is null or p_fulfillment_method not in ('shipping','pickup','undecided') then raise exception using errcode='22023',message='INVALID_FULFILLMENT_METHOD'; end if;
  if nullif(btrim(coalesce(p_tax_code,'')),'') is null then raise exception using errcode='22023',message='INVALID_TAX_CODE'; end if;

  select id into v_product_id from public.products where slug=p_product_slug and active=true and product_type='novel' limit 1;
  if v_product_id is null then return; end if;
  select * into v_tax from public.preorder_tax_estimate_profiles t where t.product_id=v_product_id and t.tax_code=lower(btrim(p_tax_code)) and t.active=true and t.published_at is not null limit 1;
  if v_tax.id is null then return; end if;
  select * into v_com from public.preorder_commercial_plans c where c.product_id=v_product_id and c.status='published' order by c.revision desc limit 1;
  if v_com.id is null or v_com.sales_enabled is distinct from false or v_com.checkout_enabled is distinct from false or v_com.payment_enabled is distinct from false or v_com.external_fulfillment_enabled is distinct from false or v_com.auto_conversion_allowed is distinct from false then return; end if;

  if p_format in ('paper','both') then
    if v_com.paper_price_cents is null or v_tax.paper_rate_basis_points is null then v_complete:=false;
    else v_book:=v_book+v_com.paper_price_cents*p_quantity; v_book_tax:=v_book_tax+round((v_com.paper_price_cents*p_quantity)::numeric*v_tax.paper_rate_basis_points/10000)::integer; end if;
  end if;
  if p_format in ('digital','both') then
    if v_com.digital_price_cents is null or v_tax.digital_rate_basis_points is null then v_complete:=false;
    else v_book:=v_book+v_com.digital_price_cents*p_quantity; v_book_tax:=v_book_tax+round((v_com.digital_price_cents*p_quantity)::numeric*v_tax.digital_rate_basis_points/10000)::integer; end if;
  end if;

  if p_format in ('paper','both') then
    if p_fulfillment_method='pickup' then v_ship_min:=0;v_ship_max:=0;
    elsif p_fulfillment_method='shipping' then
      select shipping_estimates_enabled into v_shipping_enabled from public.preorder_fulfillment_settings where product_id=v_product_id;
      select * into v_ship from public.preorder_shipping_zones z where z.product_id=v_product_id and z.zone_code=lower(btrim(coalesce(p_shipping_zone_code,''))) and z.active=true and z.published_at is not null limit 1;
      if not coalesce(v_shipping_enabled,false) or v_ship.id is null or v_ship.base_min_cents is null or v_ship.base_max_cents is null or v_ship.currency<>v_com.currency or v_tax.shipping_rate_basis_points is null then v_complete:=false;
      else
        v_ship_min:=v_ship.base_min_cents+greatest(p_quantity-1,0)*v_ship.additional_copy_min_cents;
        v_ship_max:=v_ship.base_max_cents+greatest(p_quantity-1,0)*v_ship.additional_copy_max_cents;
        v_ship_tax_min:=round(v_ship_min::numeric*v_tax.shipping_rate_basis_points/10000)::integer;
        v_ship_tax_max:=round(v_ship_max::numeric*v_tax.shipping_rate_basis_points/10000)::integer;
      end if;
    else v_complete:=false; end if;
  end if;

  return query select v_tax.tax_code,v_tax.label,v_com.currency,
    case when v_complete then v_book+v_ship_min else null end,case when v_complete then v_book+v_ship_max else null end,
    case when v_complete then v_book_tax+v_ship_tax_min else null end,case when v_complete then v_book_tax+v_ship_tax_max else null end,
    case when v_complete then v_book+v_ship_min+v_book_tax+v_ship_tax_min else null end,
    case when v_complete then v_book+v_ship_max+v_book_tax+v_ship_tax_max else null end,
    v_tax.source_reference,v_tax.effective_on,v_tax.estimate_note,v_complete,true,false,false,true;
end;
$$;

create or replace function preorder_readiness_internal.sale_readiness(p_product_slug text)
returns jsonb language plpgsql security definer set search_path='pg_catalog','public','private'
as $$
declare
  v_product_id uuid; v_plan public.preorder_commercial_plans%rowtype; v_settings public.preorder_fulfillment_settings%rowtype;
  v_shipping_zone_count integer:=0; v_pickup_count integer:=0; v_tax_profile_count integer:=0;
  v_has_paper boolean:=false; v_has_digital boolean:=false; v_shipping_ready boolean:=false; v_pickup_ready boolean:=false;
  v_paper_fulfillment_ready boolean:=true; v_locks_ok boolean:=false; v_ready boolean:=false; v_blockers jsonb:='[]'::jsonb;
begin
  perform private.require_sinjira_admin_aal2();
  select id into v_product_id from public.products where slug=p_product_slug limit 1;
  if v_product_id is null then raise exception 'PRODUCT_NOT_FOUND'; end if;
  select * into v_plan from public.preorder_commercial_plans where product_id=v_product_id and status='published' order by revision desc limit 1;
  select * into v_settings from public.preorder_fulfillment_settings where product_id=v_product_id limit 1;
  select count(*) into v_shipping_zone_count from public.preorder_shipping_zones where product_id=v_product_id and active is true and published_at is not null and base_min_cents is not null and base_max_cents is not null and base_min_cents>=0 and base_max_cents>=base_min_cents;
  select count(*) into v_pickup_count from public.preorder_pickup_points where product_id=v_product_id and active is true and published_at is not null and coalesce(nullif(btrim(label),''),'')<>'' and coalesce(nullif(btrim(public_address),''),'')<>'';
  select count(*) into v_tax_profile_count from public.preorder_tax_estimate_profiles where product_id=v_product_id and active is true and published_at is not null and source_reference is not null and effective_on is not null;

  if v_plan.id is null then v_blockers:=v_blockers||jsonb_build_array('Publier une fiche commerciale avant toute future ouverture de vente.');
  else
    v_has_paper:=v_plan.paper_price_cents is not null; v_has_digital:=v_plan.digital_price_cents is not null;
    if not (v_has_paper or v_has_digital) then v_blockers:=v_blockers||jsonb_build_array('Publier au moins un prix officiel pour une édition réellement offerte.'); end if;
    if v_plan.release_at is null then v_blockers:=v_blockers||jsonb_build_array('Publier une date ou heure de sortie officielle.'); end if;
    if coalesce(length(btrim(v_plan.terms_summary)),0)<20 then v_blockers:=v_blockers||jsonb_build_array('Compléter le résumé des conditions avant toute future vente.'); end if;
    if coalesce(length(btrim(v_plan.availability_note)),0)<10 then v_blockers:=v_blockers||jsonb_build_array('Compléter l’information de disponibilité ou de production.'); end if;
    if v_has_paper and coalesce(length(btrim(v_plan.paper_edition_label)),0)=0 then v_blockers:=v_blockers||jsonb_build_array('Nommer clairement l’édition papier associée au prix publié.'); end if;
    if v_has_digital and coalesce(length(btrim(v_plan.digital_edition_label)),0)=0 then v_blockers:=v_blockers||jsonb_build_array('Nommer clairement l’édition numérique associée au prix publié.'); end if;
    if v_plan.sales_enabled or v_plan.checkout_enabled or v_plan.payment_enabled or v_plan.external_fulfillment_enabled or v_plan.auto_conversion_allowed then v_blockers:=v_blockers||jsonb_build_array('Les verrous commerciaux doivent rester désactivés pendant la phase de préparation.'); end if;
  end if;
  if v_tax_profile_count=0 then v_blockers:=v_blockers||jsonb_build_array('Publier au moins un profil fiscal indicatif vérifié avant de considérer la préparation commerciale complète.'); end if;

  if v_settings.product_id is null then if v_has_paper then v_blockers:=v_blockers||jsonb_build_array('Configurer la réception du livre papier avant toute future vente.'); end if;
  else
    v_shipping_ready:=v_settings.shipping_estimates_enabled is true and v_shipping_zone_count>0; v_pickup_ready:=v_settings.pickup_points_enabled is true and v_pickup_count>0;
    v_paper_fulfillment_ready:=(not v_has_paper) or v_shipping_ready or v_pickup_ready;
    v_locks_ok:=v_settings.shipping_customer_pays is true and v_settings.external_carrier_api_enabled is false and v_settings.external_shipping_purchase_enabled is false and v_settings.pickup_shipping_charge_cents=0;
    if v_has_paper and not v_paper_fulfillment_ready then v_blockers:=v_blockers||jsonb_build_array('Publier au moins une estimation de livraison valide ou un point de ramassage avant toute future vente papier.'); end if;
    if not v_locks_ok then v_blockers:=v_blockers||jsonb_build_array('Rétablir les verrous de livraison : frais client, aucune API transporteur, aucun achat externe et ramassage à 0 $ de frais de livraison.'); end if;
  end if;

  v_ready:=v_plan.id is not null and (v_has_paper or v_has_digital) and v_plan.release_at is not null
    and coalesce(length(btrim(v_plan.terms_summary)),0)>=20 and coalesce(length(btrim(v_plan.availability_note)),0)>=10
    and ((not v_has_paper) or coalesce(length(btrim(v_plan.paper_edition_label)),0)>0)
    and ((not v_has_digital) or coalesce(length(btrim(v_plan.digital_edition_label)),0)>0)
    and v_tax_profile_count>0
    and not v_plan.sales_enabled and not v_plan.checkout_enabled and not v_plan.payment_enabled and not v_plan.external_fulfillment_enabled and not v_plan.auto_conversion_allowed
    and ((not v_has_paper) or (v_settings.product_id is not null and v_paper_fulfillment_ready and v_locks_ok));

  return jsonb_build_object('product_slug',p_product_slug,'ready_for_future_manual_opening',v_ready,'commercial_plan_published',v_plan.id is not null,
    'paper_price_published',v_has_paper,'digital_price_published',v_has_digital,'release_date_published',v_plan.release_at is not null,
    'terms_ready',coalesce(length(btrim(v_plan.terms_summary)),0)>=20,'availability_ready',coalesce(length(btrim(v_plan.availability_note)),0)>=10,
    'shipping_estimate_ready',v_shipping_ready,'pickup_ready',v_pickup_ready,'paper_fulfillment_ready',v_paper_fulfillment_ready,
    'tax_estimate_ready',v_tax_profile_count>0,'published_tax_profiles',v_tax_profile_count,
    'shipping_customer_pays',coalesce(v_settings.shipping_customer_pays,true),'pickup_shipping_charge_cents',coalesce(v_settings.pickup_shipping_charge_cents,0),
    'sales_enabled',coalesce(v_plan.sales_enabled,false),'checkout_enabled',coalesce(v_plan.checkout_enabled,false),'payment_enabled',coalesce(v_plan.payment_enabled,false),
    'external_fulfillment_enabled',coalesce(v_plan.external_fulfillment_enabled,false),'auto_conversion_allowed',coalesce(v_plan.auto_conversion_allowed,false),
    'external_carrier_api_enabled',coalesce(v_settings.external_carrier_api_enabled,false),'external_shipping_purchase_enabled',coalesce(v_settings.external_shipping_purchase_enabled,false),
    'published_shipping_zones',v_shipping_zone_count,'published_pickup_points',v_pickup_count,'taxes_calculated_by_sinjira',false,'blockers',v_blockers);
end;
$$;
