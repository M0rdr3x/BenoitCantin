-- V24.5.46 : aucun UUID interne de précommande ne doit traverser les RPC client/admin.

drop function if exists public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean);
drop function if exists preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean);

create function preorder_user_internal.product_preorder_reserve_confirmed(
  p_product_slug text,
  p_preferred_format text,
  p_quantity integer,
  p_contact_when_sales_open boolean,
  p_disclosure_version text,
  p_disclosure_acknowledged boolean
)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user_id uuid := auth.uid();
  v_product_id uuid;
  v_reference text;
  v_expected_version constant text := 'preorder-disclosure-v24.5.31';
begin
  if v_user_id is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  if p_disclosure_acknowledged is distinct from true
     or p_disclosure_version is distinct from v_expected_version then
    raise exception using errcode = '42501', message = 'PREORDER_DISCLOSURE_REQUIRED';
  end if;

  if p_product_slug is distinct from 'sinjira-livre-01-la-cendre-du-jugement' then
    raise exception using errcode = '22023', message = 'PREORDER_PRODUCT_NOT_OPEN';
  end if;

  if p_preferred_format is null or p_preferred_format not in ('digital','paper','both','undecided') then
    raise exception using errcode = '22023', message = 'INVALID_PREORDER_FORMAT';
  end if;

  if p_quantity is null or p_quantity < 1 or p_quantity > 5 then
    raise exception using errcode = '22023', message = 'INVALID_PREORDER_QUANTITY';
  end if;

  select p.id into v_product_id
  from public.products p
  where p.slug = p_product_slug
    and p.active = true
    and p.product_type = 'novel'
  limit 1;

  if v_product_id is null then
    raise exception using errcode = '22023', message = 'PREORDER_PRODUCT_NOT_OPEN';
  end if;

  insert into public.product_preorders (
    user_id, product_id, quantity, preferred_format, status,
    contact_when_sales_open, payment_status, financial_commitment, cancelled_at,
    disclosure_version, disclosure_acknowledged_at
  ) values (
    v_user_id, v_product_id, p_quantity, p_preferred_format, 'reserved',
    coalesce(p_contact_when_sales_open,true), 'not_collected', false, null,
    v_expected_version, now()
  )
  on conflict (user_id, product_id) do update
    set quantity = excluded.quantity,
        preferred_format = excluded.preferred_format,
        status = 'reserved',
        contact_when_sales_open = excluded.contact_when_sales_open,
        payment_status = 'not_collected',
        financial_commitment = false,
        cancelled_at = null,
        disclosure_version = excluded.disclosure_version,
        disclosure_acknowledged_at = excluded.disclosure_acknowledged_at
  returning reservation_reference into v_reference;

  return v_reference;
end;
$$;

revoke all on function preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) from public, anon;
grant execute on function preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) to authenticated, service_role;

create function public.product_preorder_reserve_confirmed(
  p_product_slug text,
  p_preferred_format text,
  p_quantity integer,
  p_contact_when_sales_open boolean,
  p_disclosure_version text,
  p_disclosure_acknowledged boolean
)
returns text
language sql
security invoker
set search_path = ''
as $$
  select preorder_user_internal.product_preorder_reserve_confirmed($1,$2,$3,$4,$5,$6)
$$;

revoke all on function public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) from public, anon;
grant execute on function public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) to authenticated, service_role;

-- La console admin reçoit désormais la référence partageable, jamais l'UUID interne.
drop function if exists public.admin_preorder_list(text,text,text,integer,integer);
drop function if exists preorder_admin_internal.admin_preorder_list(text,text,text,integer,integer);

create function preorder_admin_internal.admin_preorder_list(
  p_product_slug text,
  p_status text default null,
  p_format text default null,
  p_limit integer default 100,
  p_offset integer default 0
)
returns table(
  reservation_reference text,
  user_label text,
  quantity integer,
  preferred_format text,
  status text,
  contact_when_sales_open boolean,
  created_at timestamptz,
  updated_at timestamptz,
  cancelled_at timestamptz
)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
begin
  v_admin := private.require_sinjira_admin_aal2();
  if p_status is not null and p_status not in ('reserved','cancelled') then
    raise exception using errcode='22023', message='INVALID_STATUS_FILTER';
  end if;
  if p_format is not null and p_format not in ('digital','paper','both','undecided') then
    raise exception using errcode='22023', message='INVALID_FORMAT_FILTER';
  end if;
  if coalesce(p_limit,0) < 1 or p_limit > 250 or coalesce(p_offset,0) < 0 then
    raise exception using errcode='22023', message='INVALID_PAGINATION';
  end if;

  return query
  select
    pp.reservation_reference,
    coalesce(nullif(pr.pseudo,''),nullif(pr.display_name,''),'Compte SINJIRA')::text,
    pp.quantity::integer,
    pp.preferred_format,
    pp.status,
    pp.contact_when_sales_open,
    pp.created_at,
    pp.updated_at,
    pp.cancelled_at
  from public.product_preorders pp
  join public.products p on p.id=pp.product_id
  left join public.profiles pr on pr.user_id=pp.user_id
  where p.slug=p_product_slug
    and (p_status is null or pp.status=p_status)
    and (p_format is null or pp.preferred_format=p_format)
  order by pp.updated_at desc
  limit p_limit offset p_offset;
end;
$$;

revoke all on function preorder_admin_internal.admin_preorder_list(text,text,text,integer,integer) from public, anon;
grant execute on function preorder_admin_internal.admin_preorder_list(text,text,text,integer,integer) to authenticated, service_role;

create function public.admin_preorder_list(
  p_product_slug text,
  p_status text default null,
  p_format text default null,
  p_limit integer default 100,
  p_offset integer default 0
)
returns table(
  reservation_reference text,
  user_label text,
  quantity integer,
  preferred_format text,
  status text,
  contact_when_sales_open boolean,
  created_at timestamptz,
  updated_at timestamptz,
  cancelled_at timestamptz
)
language sql
stable
security invoker
set search_path = ''
as $$
  select * from preorder_admin_internal.admin_preorder_list($1,$2,$3,$4,$5)
$$;

revoke all on function public.admin_preorder_list(text,text,text,integer,integer) from public, anon;
grant execute on function public.admin_preorder_list(text,text,text,integer,integer) to authenticated, service_role;
