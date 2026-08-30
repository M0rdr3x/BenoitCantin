create or replace function preorder_admin_internal.admin_preorder_find_by_reference(p_reservation_reference text)
returns table(
  reservation_reference text,
  user_label text,
  product_name text,
  quantity integer,
  preferred_format text,
  status text,
  contact_when_sales_open boolean,
  fulfillment_preference text,
  disclosure_version text,
  disclosure_acknowledged_at timestamptz,
  created_at timestamptz,
  updated_at timestamptz
)
language plpgsql
stable
security definer
set search_path=''
as $$
declare
  v_admin uuid;
  v_reference text;
begin
  v_admin := private.require_sinjira_admin_aal2();
  v_reference := upper(btrim(coalesce(p_reservation_reference, '')));

  if v_reference !~ '^PR-[0-9A-F]{16}$' then
    raise exception using errcode='22023', message='INVALID_RESERVATION_REFERENCE';
  end if;

  return query
  select
    pp.reservation_reference,
    coalesce(nullif(pr.pseudo,''), nullif(pr.display_name,''), 'Compte SINJIRA')::text,
    p.name::text,
    pp.quantity::integer,
    pp.preferred_format,
    pp.status,
    pp.contact_when_sales_open,
    pp.fulfillment_preference,
    pp.disclosure_version,
    pp.disclosure_acknowledged_at,
    pp.created_at,
    pp.updated_at
  from public.product_preorders pp
  join public.products p on p.id=pp.product_id
  left join public.profiles pr on pr.user_id=pp.user_id
  where pp.reservation_reference=v_reference
  limit 1;
end;
$$;

revoke all on function preorder_admin_internal.admin_preorder_find_by_reference(text) from public, anon;
grant execute on function preorder_admin_internal.admin_preorder_find_by_reference(text) to authenticated, service_role;

create or replace function public.admin_preorder_find_by_reference(p_reservation_reference text)
returns table(
  reservation_reference text,
  user_label text,
  product_name text,
  quantity integer,
  preferred_format text,
  status text,
  contact_when_sales_open boolean,
  fulfillment_preference text,
  disclosure_version text,
  disclosure_acknowledged_at timestamptz,
  created_at timestamptz,
  updated_at timestamptz
)
language sql
stable
security invoker
set search_path=''
as $$
  select * from preorder_admin_internal.admin_preorder_find_by_reference($1)
$$;

revoke all on function public.admin_preorder_find_by_reference(text) from public, anon;
grant execute on function public.admin_preorder_find_by_reference(text) to authenticated, service_role;

comment on function public.admin_preorder_find_by_reference(text) is 'V24.5.35 — recherche admin MFA/AAL2 par référence PR, résultat minimal sans UUID, courriel, adresse ni donnée de paiement.';
