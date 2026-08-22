insert into public.products (slug, name, product_type, active)
values (
  'sinjira-livre-01-la-cendre-du-jugement',
  'SINJIRA™ — Livre I : La Cendre du Jugement',
  'novel',
  true
)
on conflict (slug) do update
set name = excluded.name,
    product_type = excluded.product_type,
    active = true;

create table if not exists public.product_preorders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  product_id uuid not null references public.products(id) on delete restrict,
  quantity smallint not null default 1 check (quantity between 1 and 5),
  preferred_format text not null default 'undecided' check (preferred_format in ('digital','paper','both','undecided')),
  status text not null default 'reserved' check (status in ('reserved','cancelled')),
  contact_when_sales_open boolean not null default true,
  payment_status text not null default 'not_collected' check (payment_status = 'not_collected'),
  financial_commitment boolean not null default false check (financial_commitment = false),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  cancelled_at timestamptz,
  constraint product_preorders_user_product_key unique (user_id, product_id),
  constraint product_preorders_cancel_state_check check (
    (status = 'reserved' and cancelled_at is null)
    or
    (status = 'cancelled' and cancelled_at is not null)
  )
);

comment on table public.product_preorders is
  'Réservations de précommande SINJIRA. V24.5.3: aucune transaction, aucun paiement et aucun engagement financier.';
comment on column public.product_preorders.payment_status is
  'V24.5.3 verrouillé à not_collected; aucune donnée bancaire n est collectée.';
comment on column public.product_preorders.financial_commitment is
  'V24.5.3 verrouillé à false; la réservation ne constitue pas une vente.';

create index if not exists product_preorders_product_status_idx
  on public.product_preorders(product_id, status, updated_at desc);
create index if not exists product_preorders_user_status_idx
  on public.product_preorders(user_id, status, updated_at desc);

alter table public.product_preorders enable row level security;

revoke all on table public.product_preorders from anon, authenticated;
grant select on table public.product_preorders to authenticated;

drop policy if exists product_preorders_own_read on public.product_preorders;
create policy product_preorders_own_read
on public.product_preorders
for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists product_preorders_admin_read on public.product_preorders;
create policy product_preorders_admin_read
on public.product_preorders
for select
to authenticated
using (public.is_sinjira_admin((select auth.uid())));

create or replace function public.product_preorders_server_fields()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at := now();
  new.payment_status := 'not_collected';
  new.financial_commitment := false;

  if tg_op = 'UPDATE' then
    new.user_id := old.user_id;
    new.product_id := old.product_id;
    new.created_at := old.created_at;
  end if;

  if new.status = 'cancelled' then
    if tg_op = 'INSERT' then
      new.cancelled_at := coalesce(new.cancelled_at, now());
    elsif old.status is distinct from 'cancelled' or old.cancelled_at is null then
      new.cancelled_at := now();
    else
      new.cancelled_at := old.cancelled_at;
    end if;
  else
    new.cancelled_at := null;
  end if;

  return new;
end;
$$;

revoke all on function public.product_preorders_server_fields() from public, anon, authenticated;

drop trigger if exists product_preorders_server_fields_trg on public.product_preorders;
create trigger product_preorders_server_fields_trg
before insert or update on public.product_preorders
for each row execute function public.product_preorders_server_fields();

create or replace function public.product_preorder_reserve(
  p_product_slug text,
  p_preferred_format text default 'undecided',
  p_quantity integer default 1,
  p_contact_when_sales_open boolean default true
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user_id uuid := auth.uid();
  v_product_id uuid;
  v_preorder_id uuid;
begin
  if v_user_id is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
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

  select p.id
    into v_product_id
  from public.products p
  where p.slug = p_product_slug
    and p.active = true
    and p.product_type = 'novel'
  limit 1;

  if v_product_id is null then
    raise exception using errcode = '22023', message = 'PREORDER_PRODUCT_NOT_OPEN';
  end if;

  insert into public.product_preorders (
    user_id,
    product_id,
    quantity,
    preferred_format,
    status,
    contact_when_sales_open,
    payment_status,
    financial_commitment,
    cancelled_at
  )
  values (
    v_user_id,
    v_product_id,
    p_quantity,
    p_preferred_format,
    'reserved',
    coalesce(p_contact_when_sales_open, true),
    'not_collected',
    false,
    null
  )
  on conflict (user_id, product_id) do update
    set quantity = excluded.quantity,
        preferred_format = excluded.preferred_format,
        status = 'reserved',
        contact_when_sales_open = excluded.contact_when_sales_open,
        payment_status = 'not_collected',
        financial_commitment = false,
        cancelled_at = null
  returning id into v_preorder_id;

  return v_preorder_id;
end;
$$;

create or replace function public.product_preorder_cancel(p_product_slug text)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user_id uuid := auth.uid();
  v_updated integer := 0;
begin
  if v_user_id is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;

  update public.product_preorders pp
  set status = 'cancelled'
  from public.products p
  where pp.user_id = v_user_id
    and pp.product_id = p.id
    and p.slug = p_product_slug
    and pp.status <> 'cancelled';

  get diagnostics v_updated = row_count;
  return v_updated > 0;
end;
$$;

create or replace function public.product_preorder_my_status(p_product_slug text)
returns table (
  preorder_id uuid,
  product_slug text,
  product_name text,
  quantity integer,
  preferred_format text,
  status text,
  contact_when_sales_open boolean,
  payment_status text,
  financial_commitment boolean,
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
    pp.id,
    p.slug,
    p.name,
    pp.quantity::integer,
    pp.preferred_format,
    pp.status,
    pp.contact_when_sales_open,
    pp.payment_status,
    pp.financial_commitment,
    pp.created_at,
    pp.updated_at,
    pp.cancelled_at
  from public.product_preorders pp
  join public.products p on p.id = pp.product_id
  where pp.user_id = auth.uid()
    and p.slug = p_product_slug
  limit 1
$$;

revoke all on function public.product_preorder_reserve(text,text,integer,boolean) from public, anon, authenticated;
revoke all on function public.product_preorder_cancel(text) from public, anon, authenticated;
revoke all on function public.product_preorder_my_status(text) from public, anon, authenticated;
grant execute on function public.product_preorder_reserve(text,text,integer,boolean) to authenticated;
grant execute on function public.product_preorder_cancel(text) to authenticated;
grant execute on function public.product_preorder_my_status(text) to authenticated;
