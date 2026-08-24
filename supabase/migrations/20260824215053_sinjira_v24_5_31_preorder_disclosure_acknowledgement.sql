alter table public.product_preorders
  add column if not exists disclosure_version text,
  add column if not exists disclosure_acknowledged_at timestamptz;

alter table public.product_preorders
  drop constraint if exists product_preorders_disclosure_pair_chk;
alter table public.product_preorders
  add constraint product_preorders_disclosure_pair_chk
  check ((disclosure_version is null) = (disclosure_acknowledged_at is null));

comment on column public.product_preorders.disclosure_version is
  'Version du texte de transparence explicitement compris lors de la dernière réservation/mise à jour. Null pour les réservations historiques antérieures à V24.5.31.';
comment on column public.product_preorders.disclosure_acknowledged_at is
  'Date de confirmation explicite du texte de transparence. Aucun consentement financier; aucune conversion automatique en commande.';

create or replace function preorder_user_internal.product_preorder_reserve(
  p_product_slug text,
  p_preferred_format text default 'undecided'::text,
  p_quantity integer default 1,
  p_contact_when_sales_open boolean default true
)
returns uuid
language plpgsql
security definer
set search_path to ''
as $function$
begin
  raise exception using errcode = '42501', message = 'PREORDER_DISCLOSURE_REQUIRED';
end;
$function$;

create or replace function public.product_preorder_reserve(
  p_product_slug text,
  p_preferred_format text default 'undecided'::text,
  p_quantity integer default 1,
  p_contact_when_sales_open boolean default true
)
returns uuid
language sql
security invoker
set search_path to ''
as $function$
  select preorder_user_internal.product_preorder_reserve($1,$2,$3,$4)
$function$;

revoke all on function public.product_preorder_reserve(text,text,integer,boolean) from public, anon;
grant execute on function public.product_preorder_reserve(text,text,integer,boolean) to authenticated, service_role;

create or replace function preorder_user_internal.product_preorder_reserve_confirmed(
  p_product_slug text,
  p_preferred_format text,
  p_quantity integer,
  p_contact_when_sales_open boolean,
  p_disclosure_version text,
  p_disclosure_acknowledged boolean
)
returns uuid
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_user_id uuid := auth.uid();
  v_product_id uuid;
  v_preorder_id uuid;
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
  returning id into v_preorder_id;

  return v_preorder_id;
end;
$function$;

create or replace function public.product_preorder_reserve_confirmed(
  p_product_slug text,
  p_preferred_format text,
  p_quantity integer,
  p_contact_when_sales_open boolean,
  p_disclosure_version text,
  p_disclosure_acknowledged boolean
)
returns uuid
language sql
security invoker
set search_path to ''
as $function$
  select preorder_user_internal.product_preorder_reserve_confirmed($1,$2,$3,$4,$5,$6)
$function$;

revoke all on function preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) from public, anon;
grant execute on function preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) to authenticated, service_role;
revoke all on function public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) from public, anon;
grant execute on function public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) to authenticated, service_role;

comment on function public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) is
  'Réserve/met à jour une précommande uniquement après confirmation explicite du texte V24.5.31. Aucun paiement ni engagement financier.';
