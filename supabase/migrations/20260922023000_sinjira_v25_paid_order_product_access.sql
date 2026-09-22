-- SINJIRA™ V25 — droit produit aligné sur achat réel et entitlement durable.
-- Un produit acheté reste accessible même s'il n'est plus actif à la vente.
-- Une commande non payée ne confère aucun droit.

begin;

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

comment on function public.has_sinjira_product(text,uuid) is
  'Droit produit self-only: propriétaire, famille adult/youth, entitlement durable ou commande paid. Une commande non payée ne donne aucun accès; aucun faux entitlement n est créé.';

commit;
