-- SINJIRA™ V25 — droit produit aligné sur achat réel et entitlement durable.
-- Un produit acheté reste accessible même s'il n'est plus actif à la vente.
-- Une commande non payée ne confère aucun droit.

begin;

drop policy if exists products_ordered_read on public.products;
create policy products_ordered_read
on public.products
for select
to authenticated
using (
  exists(
    select 1
    from public.order_items oi
    join public.orders o on o.id=oi.order_id
    where oi.product_id=products.id
      and o.user_id=(select auth.uid())
      and o.status='paid'
  )
);

create or replace function public.has_sinjira_product(
  p_product_slug text,
  p_user_id uuid default auth.uid()
)
returns boolean
language sql
stable
security invoker
set search_path=pg_catalog,public,private,auth
as $paid_access$
  select case
    when p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')<>'service_role'
         and p_user_id is distinct from auth.uid() then false
    else public.is_sinjira_owner(p_user_id)
      or (
        public.is_sinjira_catalog_family_member(p_user_id)
        and public.sinjira_age_band(p_user_id) in ('adult','youth')
        and exists(
          select 1
          from public.products family_product
          where family_product.slug=p_product_slug
        )
      )
      or exists(
        select 1
        from public.user_entitlements ue
        join public.products p on p.id=ue.product_id
        where ue.user_id=p_user_id
          and p.slug=p_product_slug
      )
      or exists(
        select 1
        from public.orders o
        join public.order_items oi on oi.order_id=o.id
        join public.products p on p.id=oi.product_id
        where o.user_id=p_user_id
          and o.status='paid'
          and p.slug=p_product_slug
      )
  end;
$paid_access$;

revoke all on function public.has_sinjira_product(text,uuid)
from public,anon;
grant execute on function public.has_sinjira_product(text,uuid)
to authenticated,service_role;

create or replace function sinjira_v25_internal.sinjira_my_product_rights()
returns jsonb
language sql
stable
security definer
set search_path=pg_catalog,public,auth
as $rights$
  with current_account as (
    select
      auth.uid() as uid,
      case
        when auth.uid() is null then 'unverified'
        else public.sinjira_age_band(auth.uid())
      end as band
  ),
  rights as (
    select
      p.id as product_id,
      p.slug,
      p.name,
      p.product_type,
      ue.source::text as source,
      0 as source_rank
    from current_account a
    join public.user_entitlements ue on ue.user_id=a.uid
    join public.products p on p.id=ue.product_id
    where a.uid is not null
      and a.band in ('adult','youth')

    union all

    select
      p.id as product_id,
      p.slug,
      p.name,
      p.product_type,
      'paid_order'::text as source,
      1 as source_rank
    from current_account a
    join public.orders o on o.user_id=a.uid
    join public.order_items oi on oi.order_id=o.id
    join public.products p on p.id=oi.product_id
    where a.uid is not null
      and a.band in ('adult','youth')
      and o.status='paid'
  ),
  deduplicated as (
    select distinct on(product_id)
      product_id,slug,name,product_type,source
    from rights
    order by product_id,source_rank,source
  )
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'product_id',product_id,
        'slug',slug,
        'name',name,
        'product_type',product_type,
        'source',source
      )
      order by name,slug
    ),
    '[]'::jsonb
  )
  from deduplicated;
$rights$;

revoke all on function sinjira_v25_internal.sinjira_my_product_rights()
from public,anon,authenticated;
grant execute on function sinjira_v25_internal.sinjira_my_product_rights()
to authenticated,service_role;

create or replace function public.sinjira_my_product_rights()
returns jsonb
language sql
stable
security invoker
set search_path=''
as $wrapper$
  select sinjira_v25_internal.sinjira_my_product_rights();
$wrapper$;

revoke all on function public.sinjira_my_product_rights()
from public,anon;
grant execute on function public.sinjira_my_product_rights()
to authenticated,service_role;

comment on policy products_ordered_read on public.products is
  'V25: un produit commandé reste lisible au compte uniquement après paiement confirmé status=paid; une commande pending ne confère aucun droit.';

comment on function public.has_sinjira_product(text,uuid) is
  'Droit produit self-only: propriétaire, famille adult/youth, entitlement durable ou commande paid. Une commande non payée ne donne aucun accès; aucun faux entitlement n est créé.';
comment on function sinjira_v25_internal.sinjira_my_product_rights() is
  'Implémentation privilégiée self-only et minimisée des droits produit commerciaux du compte courant. Les comptes 11–12 et états non vérifiés restent masqués côté navigateur.';
comment on function public.sinjira_my_product_rights() is
  'Wrapper SECURITY INVOKER vers la liste self-only des droits produit commerciaux: entitlement durable ou commande paid. Aucun détail de commande, aucun faux droit owner/famille.';

commit;
