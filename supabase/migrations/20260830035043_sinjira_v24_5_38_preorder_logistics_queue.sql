create or replace function preorder_admin_internal.admin_preorder_logistics_queue(
  p_product_slug text,
  p_limit integer default 250
)
returns table(
  reservation_reference text,
  product_name text,
  quantity integer,
  preferred_format text,
  preorder_status text,
  fulfillment_preference text,
  pickup_point_label text,
  pickup_city text,
  disclosure_version text,
  disclosure_acknowledged_at timestamptz,
  workflow_state text
)
language plpgsql
stable
security definer
set search_path=''
as $$
declare
  v_admin uuid;
  v_limit integer;
begin
  v_admin := private.require_sinjira_admin_aal2();
  v_limit := greatest(1, least(coalesce(p_limit,250),500));

  return query
  select
    pp.reservation_reference,
    p.name::text,
    pp.quantity::integer,
    pp.preferred_format,
    pp.status,
    pp.fulfillment_preference,
    case when pp.fulfillment_preference='pickup' then nullif(btrim(pk.label),'') else null end::text,
    case when pp.fulfillment_preference='pickup' then nullif(btrim(pk.city),'') else null end::text,
    pp.disclosure_version,
    pp.disclosure_acknowledged_at,
    coalesce(w.workflow_state,'pending')::text
  from public.product_preorders pp
  join public.products p on p.id=pp.product_id
  left join public.preorder_pickup_points pk on pk.id=pp.pickup_point_id and pk.product_id=pp.product_id
  left join private.preorder_admin_workflow w on w.preorder_id=pp.id
  where p.slug=btrim(coalesce(p_product_slug,''))
  order by pp.created_at asc
  limit v_limit;
end;
$$;

create or replace function public.admin_preorder_logistics_queue(
  p_product_slug text,
  p_limit integer default 250
)
returns table(
  reservation_reference text,
  product_name text,
  quantity integer,
  preferred_format text,
  preorder_status text,
  fulfillment_preference text,
  pickup_point_label text,
  pickup_city text,
  disclosure_version text,
  disclosure_acknowledged_at timestamptz,
  workflow_state text
)
language sql
stable
security invoker
set search_path=''
as $$
  select * from preorder_admin_internal.admin_preorder_logistics_queue($1,$2)
$$;

revoke all on function public.admin_preorder_logistics_queue(text,integer) from public, anon;
grant execute on function public.admin_preorder_logistics_queue(text,integer) to authenticated, service_role;
revoke all on function preorder_admin_internal.admin_preorder_logistics_queue(text,integer) from public, anon;
grant execute on function preorder_admin_internal.admin_preorder_logistics_queue(text,integer) to authenticated, service_role;
