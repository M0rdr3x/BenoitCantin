-- SINJIRA™ V25 — catalogue compte/créateur cohérent et relisible.
-- Membres : produits actifs + produits réellement achetés/attribués.
-- Créateur : catalogue interne complet sans fabriquer de faux achat.
-- Littérature : convergence du Livre II vers la table canonique sinjira_novels.

drop policy if exists sinjira_novels_owner_read on public.sinjira_novels;
create policy sinjira_novels_owner_read
on public.sinjira_novels
for select
to authenticated
using (public.is_sinjira_owner((select auth.uid())));

drop policy if exists products_entitled_read on public.products;
create policy products_entitled_read
on public.products
for select
to authenticated
using (
  exists(
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
  exists(
    select 1
    from public.order_items oi
    join public.orders o on o.id=oi.order_id
    where oi.product_id=products.id
      and o.user_id=(select auth.uid())
      and o.status='paid'
  )
);

drop policy if exists products_owner_read on public.products;
create policy products_owner_read
on public.products
for select
to authenticated
using (public.is_sinjira_owner((select auth.uid())));

insert into public.sinjira_novels(
  slug,title,subtitle,description,status,public_path,demo_path,comments_enabled,sort_order
)
values(
  'le-sang-du-sauveur',
  'SINJIRA — Le Sang du Sauveur',
  'Livre II',
  'Deuxième roman officiellement confirmé de SINJIRA™, actuellement en production éditoriale.',
  'announced',
  '/projets/sinjira/romans/le-sang-du-sauveur/index.html',
  null,
  false,
  20
)
on conflict(slug) do update
set title=excluded.title,
    subtitle=excluded.subtitle,
    description=excluded.description,
    public_path=excluded.public_path,
    sort_order=excluded.sort_order,
    updated_at=now();

comment on policy sinjira_novels_owner_read on public.sinjira_novels is
  'V25: le propriétaire SINJIRA voit tout le catalogue roman, y compris les brouillons, sans créer de droit acheté.';
comment on policy products_entitled_read on public.products is
  'V25: un membre peut relire un produit lié à son propre entitlement même si ce produit devient inactif.';
comment on policy products_ordered_read on public.products is
  'V25: un membre peut relire un produit présent dans sa propre commande uniquement après paiement confirmé status=paid, même si ce produit devient ensuite inactif.';
comment on policy products_owner_read on public.products is
  'V25: le propriétaire SINJIRA voit tout le catalogue produit pour gérer ses créations; ce droit n est pas un achat.';
