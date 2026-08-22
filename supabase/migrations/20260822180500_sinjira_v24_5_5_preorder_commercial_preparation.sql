create table if not exists public.preorder_commercial_plans (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  revision integer not null check (revision > 0),
  status text not null default 'draft' check (status in ('draft','ready','published','superseded','cancelled')),
  currency text not null default 'CAD' check (currency ~ '^[A-Z]{3}$'),
  paper_price_cents integer check (paper_price_cents is null or paper_price_cents between 0 and 100000000),
  digital_price_cents integer check (digital_price_cents is null or digital_price_cents between 0 and 100000000),
  paper_edition_label text check (paper_edition_label is null or char_length(paper_edition_label) <= 160),
  digital_edition_label text check (digital_edition_label is null or char_length(digital_edition_label) <= 160),
  release_at timestamptz,
  reservation_closes_at timestamptz,
  availability_note text check (availability_note is null or char_length(availability_note) <= 1200),
  terms_summary text check (terms_summary is null or char_length(terms_summary) <= 2400),
  sales_enabled boolean not null default false check (sales_enabled = false),
  checkout_enabled boolean not null default false check (checkout_enabled = false),
  payment_enabled boolean not null default false check (payment_enabled = false),
  external_fulfillment_enabled boolean not null default false check (external_fulfillment_enabled = false),
  auto_conversion_allowed boolean not null default false check (auto_conversion_allowed = false),
  created_by uuid not null references auth.users(id) on delete restrict,
  updated_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  ready_at timestamptz,
  published_at timestamptz,
  superseded_at timestamptz,
  constraint preorder_commercial_plans_product_revision_key unique (product_id, revision),
  constraint preorder_commercial_ready_fields check (
    status not in ('ready','published') or (
      release_at is not null
      and nullif(btrim(coalesce(terms_summary,'')), '') is not null
      and (
        (paper_price_cents is not null and nullif(btrim(coalesce(paper_edition_label,'')), '') is not null)
        or
        (digital_price_cents is not null and nullif(btrim(coalesce(digital_edition_label,'')), '') is not null)
      )
    )
  )
);

comment on table public.preorder_commercial_plans is
  'V24.5.5: préparation et publication d informations commerciales, sans vente, checkout, paiement, livraison externe ni conversion automatique.';

create unique index if not exists preorder_commercial_working_product_uq
  on public.preorder_commercial_plans(product_id)
  where status in ('draft','ready');
create unique index if not exists preorder_commercial_published_product_uq
  on public.preorder_commercial_plans(product_id)
  where status = 'published';
create index if not exists preorder_commercial_product_status_idx
  on public.preorder_commercial_plans(product_id, status, revision desc);
create index if not exists preorder_commercial_created_by_idx
  on public.preorder_commercial_plans(created_by);
create index if not exists preorder_commercial_updated_by_idx
  on public.preorder_commercial_plans(updated_by);

alter table public.preorder_commercial_plans enable row level security;
revoke all on table public.preorder_commercial_plans from public, anon, authenticated;

create or replace function public.preorder_commercial_plan_server_fields()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at := now();
  new.sales_enabled := false;
  new.checkout_enabled := false;
  new.payment_enabled := false;
  new.external_fulfillment_enabled := false;
  new.auto_conversion_allowed := false;

  if tg_op = 'UPDATE' then
    new.product_id := old.product_id;
    new.revision := old.revision;
    new.created_by := old.created_by;
    new.created_at := old.created_at;

    if old.status in ('published','superseded','cancelled') then
      if to_jsonb(new) - array['updated_at']::text[] is distinct from to_jsonb(old) - array['updated_at']::text[] then
        raise exception using errcode = '22023', message = 'COMMERCIAL_PLAN_IMMUTABLE';
      end if;
    end if;
  end if;

  return new;
end;
$$;

revoke all on function public.preorder_commercial_plan_server_fields() from public, anon, authenticated;

drop trigger if exists preorder_commercial_plan_server_fields_trg on public.preorder_commercial_plans;
create trigger preorder_commercial_plan_server_fields_trg
before insert or update on public.preorder_commercial_plans
for each row execute function public.preorder_commercial_plan_server_fields();

create or replace function public.admin_preorder_commercial_plan_get(p_product_slug text)
returns table (
  revision integer,
  status text,
  currency text,
  paper_price_cents integer,
  digital_price_cents integer,
  paper_edition_label text,
  digital_edition_label text,
  release_at timestamptz,
  reservation_closes_at timestamptz,
  availability_note text,
  terms_summary text,
  sales_enabled boolean,
  checkout_enabled boolean,
  payment_enabled boolean,
  external_fulfillment_enabled boolean,
  auto_conversion_allowed boolean,
  ready_at timestamptz,
  published_at timestamptz,
  updated_at timestamptz
)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  perform private.require_sinjira_admin_aal2();

  return query
  select
    c.revision,
    c.status,
    c.currency,
    c.paper_price_cents,
    c.digital_price_cents,
    c.paper_edition_label,
    c.digital_edition_label,
    c.release_at,
    c.reservation_closes_at,
    c.availability_note,
    c.terms_summary,
    c.sales_enabled,
    c.checkout_enabled,
    c.payment_enabled,
    c.external_fulfillment_enabled,
    c.auto_conversion_allowed,
    c.ready_at,
    c.published_at,
    c.updated_at
  from public.preorder_commercial_plans c
  join public.products p on p.id = c.product_id
  where p.slug = p_product_slug
    and c.status in ('draft','ready','published')
  order by case c.status when 'draft' then 0 when 'ready' then 0 else 1 end, c.revision desc;
end;
$$;

create or replace function public.admin_preorder_commercial_plan_save(
  p_product_slug text,
  p_currency text default 'CAD',
  p_paper_price_cents integer default null,
  p_digital_price_cents integer default null,
  p_paper_edition_label text default null,
  p_digital_edition_label text default null,
  p_release_at timestamptz default null,
  p_reservation_closes_at timestamptz default null,
  p_availability_note text default null,
  p_terms_summary text default null
)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
  v_product_id uuid;
  v_id uuid;
  v_revision integer;
  v_currency text := upper(btrim(coalesce(p_currency,'CAD')));
begin
  v_admin := private.require_sinjira_admin_aal2();

  select p.id into v_product_id
  from public.products p
  where p.slug = p_product_slug and p.product_type = 'novel'
  limit 1;
  if v_product_id is null then
    raise exception using errcode = '22023', message = 'PREORDER_PRODUCT_NOT_FOUND';
  end if;

  if v_currency !~ '^[A-Z]{3}$' then
    raise exception using errcode = '22023', message = 'INVALID_CURRENCY';
  end if;
  if p_paper_price_cents is not null and (p_paper_price_cents < 0 or p_paper_price_cents > 100000000) then
    raise exception using errcode = '22023', message = 'INVALID_PAPER_PRICE';
  end if;
  if p_digital_price_cents is not null and (p_digital_price_cents < 0 or p_digital_price_cents > 100000000) then
    raise exception using errcode = '22023', message = 'INVALID_DIGITAL_PRICE';
  end if;
  if char_length(coalesce(p_paper_edition_label,'')) > 160 or char_length(coalesce(p_digital_edition_label,'')) > 160 then
    raise exception using errcode = '22023', message = 'EDITION_LABEL_TOO_LONG';
  end if;
  if char_length(coalesce(p_availability_note,'')) > 1200 or char_length(coalesce(p_terms_summary,'')) > 2400 then
    raise exception using errcode = '22023', message = 'COMMERCIAL_TEXT_TOO_LONG';
  end if;

  select c.id, c.revision into v_id, v_revision
  from public.preorder_commercial_plans c
  where c.product_id = v_product_id and c.status in ('draft','ready')
  order by c.revision desc
  limit 1
  for update;

  if v_id is null then
    select coalesce(max(c.revision),0) + 1 into v_revision
    from public.preorder_commercial_plans c
    where c.product_id = v_product_id;

    insert into public.preorder_commercial_plans (
      product_id, revision, status, currency,
      paper_price_cents, digital_price_cents,
      paper_edition_label, digital_edition_label,
      release_at, reservation_closes_at,
      availability_note, terms_summary,
      created_by, updated_by
    ) values (
      v_product_id, v_revision, 'draft', v_currency,
      p_paper_price_cents, p_digital_price_cents,
      nullif(btrim(coalesce(p_paper_edition_label,'')),''),
      nullif(btrim(coalesce(p_digital_edition_label,'')),''),
      p_release_at, p_reservation_closes_at,
      nullif(btrim(coalesce(p_availability_note,'')),''),
      nullif(btrim(coalesce(p_terms_summary,'')),''),
      v_admin, v_admin
    );
  else
    update public.preorder_commercial_plans c
    set status = 'draft',
        currency = v_currency,
        paper_price_cents = p_paper_price_cents,
        digital_price_cents = p_digital_price_cents,
        paper_edition_label = nullif(btrim(coalesce(p_paper_edition_label,'')),''),
        digital_edition_label = nullif(btrim(coalesce(p_digital_edition_label,'')),''),
        release_at = p_release_at,
        reservation_closes_at = p_reservation_closes_at,
        availability_note = nullif(btrim(coalesce(p_availability_note,'')),''),
        terms_summary = nullif(btrim(coalesce(p_terms_summary,'')),''),
        updated_by = v_admin,
        ready_at = null
    where c.id = v_id;
  end if;

  return v_revision;
end;
$$;

create or replace function public.admin_preorder_commercial_plan_mark_ready(p_product_slug text)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
  v_id uuid;
  v_plan public.preorder_commercial_plans%rowtype;
begin
  v_admin := private.require_sinjira_admin_aal2();

  select c.* into v_plan
  from public.preorder_commercial_plans c
  join public.products p on p.id = c.product_id
  where p.slug = p_product_slug and c.status = 'draft'
  order by c.revision desc
  limit 1
  for update of c;

  v_id := v_plan.id;
  if v_id is null then return false; end if;
  if v_plan.release_at is null or nullif(btrim(coalesce(v_plan.terms_summary,'')),'') is null then
    raise exception using errcode = '22023', message = 'COMMERCIAL_PLAN_INCOMPLETE';
  end if;
  if not (
    (v_plan.paper_price_cents is not null and nullif(btrim(coalesce(v_plan.paper_edition_label,'')),'') is not null)
    or
    (v_plan.digital_price_cents is not null and nullif(btrim(coalesce(v_plan.digital_edition_label,'')),'') is not null)
  ) then
    raise exception using errcode = '22023', message = 'COMMERCIAL_PLAN_PRICE_EDITION_REQUIRED';
  end if;

  update public.preorder_commercial_plans
  set status = 'ready', ready_at = now(), updated_by = v_admin
  where id = v_id;
  return true;
end;
$$;

create or replace function public.admin_preorder_commercial_plan_publish(p_product_slug text)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
  v_product_id uuid;
  v_ready_id uuid;
begin
  v_admin := private.require_sinjira_admin_aal2();

  select c.id, c.product_id into v_ready_id, v_product_id
  from public.preorder_commercial_plans c
  join public.products p on p.id = c.product_id
  where p.slug = p_product_slug and c.status = 'ready'
  order by c.revision desc
  limit 1
  for update of c;

  if v_ready_id is null then return false; end if;

  update public.preorder_commercial_plans c
  set status = 'superseded', superseded_at = now(), updated_by = v_admin
  where c.product_id = v_product_id and c.status = 'published';

  update public.preorder_commercial_plans c
  set status = 'published', published_at = now(), updated_by = v_admin
  where c.id = v_ready_id and c.status = 'ready';

  return found;
end;
$$;

create or replace function public.product_preorder_commercial_info(p_product_slug text)
returns table (
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

revoke all on function public.admin_preorder_commercial_plan_get(text) from public, anon, authenticated;
revoke all on function public.admin_preorder_commercial_plan_save(text,text,integer,integer,text,text,timestamptz,timestamptz,text,text) from public, anon, authenticated;
revoke all on function public.admin_preorder_commercial_plan_mark_ready(text) from public, anon, authenticated;
revoke all on function public.admin_preorder_commercial_plan_publish(text) from public, anon, authenticated;
revoke all on function public.product_preorder_commercial_info(text) from public, anon, authenticated;

grant execute on function public.admin_preorder_commercial_plan_get(text) to authenticated;
grant execute on function public.admin_preorder_commercial_plan_save(text,text,integer,integer,text,text,timestamptz,timestamptz,text,text) to authenticated;
grant execute on function public.admin_preorder_commercial_plan_mark_ready(text) to authenticated;
grant execute on function public.admin_preorder_commercial_plan_publish(text) to authenticated;
grant execute on function public.product_preorder_commercial_info(text) to anon, authenticated;
