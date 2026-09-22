-- SINJIRA™ V25 — frontière âge self-only pour le catalogue et les droits produit.
-- Les navigateurs ne doivent jamais exécuter sinjira_age_band(uuid), qui permettrait
-- de sonder l'âge d'un UUID arbitraire. Les policies utilisent le helper courant
-- sinjira_my_age_band(); l'implémentation privilégiée du droit produit reste interne.

begin;

create or replace function sinjira_v25_internal.has_sinjira_product(
  p_product_slug text,
  p_user_id uuid
)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $product_access$
  select case
    when p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')<>'service_role'
         and p_user_id is distinct from auth.uid() then false
    else public.is_sinjira_owner(p_user_id)
      or (
        sinjira_v25_internal.is_sinjira_catalog_family_member(p_user_id)
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
$product_access$;

revoke all on function sinjira_v25_internal.has_sinjira_product(text,uuid)
from public,anon,authenticated;
grant execute on function sinjira_v25_internal.has_sinjira_product(text,uuid)
to authenticated,service_role;

create or replace function public.has_sinjira_product(
  p_product_slug text,
  p_user_id uuid default auth.uid()
)
returns boolean
language sql
stable
security invoker
set search_path=''
as $wrapper$
  select sinjira_v25_internal.has_sinjira_product(p_product_slug,p_user_id);
$wrapper$;

revoke all on function public.has_sinjira_product(text,uuid)
from public,anon;
grant execute on function public.has_sinjira_product(text,uuid)
to authenticated,service_role;

drop policy if exists sinjira_novels_family_catalog_read_v25 on public.sinjira_novels;
create policy sinjira_novels_family_catalog_read_v25
on public.sinjira_novels
for select
to authenticated
using (
  public.is_sinjira_catalog_family_member((select auth.uid()))
  and public.sinjira_my_age_band() in ('adult','youth')
);

drop policy if exists products_entitled_read on public.products;
create policy products_entitled_read
on public.products
for select
to authenticated
using (
  public.sinjira_my_age_band() in ('adult','youth')
  and exists(
    select 1
    from public.user_entitlements ue
    where ue.product_id=products.id
      and ue.user_id=(select auth.uid())
  )
);

drop policy if exists products_ordered_read on public.products;
create policy products_ordered_read
on public.products
for select
to authenticated
using (
  public.sinjira_my_age_band() in ('adult','youth')
  and exists(
    select 1
    from public.order_items oi
    join public.orders o on o.id=oi.order_id
    where oi.product_id=products.id
      and o.user_id=(select auth.uid())
      and o.status='paid'
  )
);

drop policy if exists products_family_catalog_read_v25 on public.products;
create policy products_family_catalog_read_v25
on public.products
for select
to authenticated
using (
  public.is_sinjira_catalog_family_member((select auth.uid()))
  and public.sinjira_my_age_band() in ('adult','youth')
);

drop policy if exists projects_family_catalog_read_v25 on public.projects;
create policy projects_family_catalog_read_v25
on public.projects
for select
to authenticated
using (
  public.is_sinjira_catalog_family_member((select auth.uid()))
  and public.sinjira_my_age_band() in ('adult','youth')
);

drop policy if exists extensions_creator_family_catalog_read_v25 on public.extensions;
create policy extensions_creator_family_catalog_read_v25
on public.extensions
for select
to authenticated
using (
  public.sinjira_has_full_catalog_access((select auth.uid()))
  and public.sinjira_my_age_band() in ('adult','youth')
);

drop policy if exists extensions_purchased_read_v25 on public.extensions;
create policy extensions_purchased_read_v25
on public.extensions
for select
to authenticated
using (
  status in ('approved','released')
  and product_slug is not null
  and exists(
    select 1
    from public.projects parent_project
    where parent_project.id=extensions.project_id
      and parent_project.status<>'draft'
  )
  and public.sinjira_my_age_band() in ('adult','youth')
  and public.has_sinjira_product(product_slug,(select auth.uid()))
);

comment on function public.has_sinjira_product(text,uuid) is
  'Wrapper self-only SECURITY INVOKER vers une implémentation interne: propriétaire, famille adult/youth, entitlement durable ou commande paid. Aucun sondage âge UUID par le navigateur.';
comment on function sinjira_v25_internal.has_sinjira_product(text,uuid) is
  'Implémentation privilégiée self-only du droit produit. authenticated ne peut cibler que auth.uid(); service_role conserve le ciblage serveur explicite.';

commit;
