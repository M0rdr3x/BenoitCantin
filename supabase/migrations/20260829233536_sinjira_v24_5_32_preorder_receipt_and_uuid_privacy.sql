alter table public.product_preorders
  add column if not exists reservation_reference text;

update public.product_preorders
set reservation_reference = 'PR-' || upper(encode(gen_random_bytes(8), 'hex'))
where reservation_reference is null;

alter table public.product_preorders
  alter column reservation_reference set default ('PR-' || upper(encode(gen_random_bytes(8), 'hex'))),
  alter column reservation_reference set not null;

create unique index if not exists product_preorders_reservation_reference_uidx
  on public.product_preorders(reservation_reference);

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid='public.product_preorders'::regclass
      and conname='product_preorders_reservation_reference_chk'
  ) then
    alter table public.product_preorders
      add constraint product_preorders_reservation_reference_chk
      check (reservation_reference ~ '^PR-[0-9A-F]{16}$');
  end if;
end $$;

-- V24.5.32 : l'UUID interne d'une précommande ne traverse plus la surface API.
drop function if exists public.product_preorder_my_status(text);
drop function if exists preorder_user_internal.product_preorder_my_status(text);

create function preorder_user_internal.product_preorder_my_status(p_product_slug text)
returns table(
  reservation_reference text,
  product_slug text,
  product_name text,
  quantity integer,
  preferred_format text,
  fulfillment_preference text,
  status text,
  contact_when_sales_open boolean,
  payment_status text,
  financial_commitment boolean,
  disclosure_version text,
  disclosure_acknowledged_at timestamptz,
  created_at timestamptz,
  updated_at timestamptz,
  cancelled_at timestamptz
)
language sql
stable
security definer
set search_path = ''
as $$
  select
    pp.reservation_reference,
    p.slug,
    p.name,
    pp.quantity::integer,
    pp.preferred_format,
    pp.fulfillment_preference,
    pp.status,
    pp.contact_when_sales_open,
    pp.payment_status,
    pp.financial_commitment,
    pp.disclosure_version,
    pp.disclosure_acknowledged_at,
    pp.created_at,
    pp.updated_at,
    pp.cancelled_at
  from public.product_preorders pp
  join public.products p on p.id = pp.product_id
  where pp.user_id = auth.uid()
    and p.slug = p_product_slug
  limit 1
$$;

revoke all on function preorder_user_internal.product_preorder_my_status(text) from public, anon;
grant execute on function preorder_user_internal.product_preorder_my_status(text) to authenticated, service_role;

create function public.product_preorder_my_status(p_product_slug text)
returns table(
  reservation_reference text,
  product_slug text,
  product_name text,
  quantity integer,
  preferred_format text,
  fulfillment_preference text,
  status text,
  contact_when_sales_open boolean,
  payment_status text,
  financial_commitment boolean,
  disclosure_version text,
  disclosure_acknowledged_at timestamptz,
  created_at timestamptz,
  updated_at timestamptz,
  cancelled_at timestamptz
)
language sql
stable
security invoker
set search_path = ''
as $$
  select * from preorder_user_internal.product_preorder_my_status($1)
$$;

revoke all on function public.product_preorder_my_status(text) from public, anon;
grant execute on function public.product_preorder_my_status(text) to authenticated, service_role;
