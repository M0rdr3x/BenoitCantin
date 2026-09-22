-- SINJIRA™ V25 — accès extension privée par achat réel.
-- Une extension publique reste gratuite; une extension privée liée à un produit
-- n'est visible au membre standard qu'après entitlement ou commande paid.

begin;

alter table public.extensions
  add column if not exists product_slug text;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname='extensions_product_slug_fkey'
      and conrelid='public.extensions'::regclass
  ) then
    alter table public.extensions
      add constraint extensions_product_slug_fkey
      foreign key(product_slug)
      references public.products(slug)
      on update cascade
      on delete set null;
  end if;
end;
$$;

create index if not exists extensions_product_slug_idx
  on public.extensions(product_slug)
  where product_slug is not null;

drop policy if exists "extensions public read" on public.extensions;
create policy "extensions public read"
on public.extensions
for select
to anon,authenticated
using (
  is_public=true
  and status in ('approved','released')
  and exists(
    select 1
    from public.projects parent_project
    where parent_project.id=extensions.project_id
      and parent_project.status<>'draft'
  )
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
  and public.sinjira_age_band((select auth.uid())) in ('adult','youth')
  and public.has_sinjira_product(product_slug,(select auth.uid()))
);

create or replace function sinjira_v25_internal.sinjira_my_extension_catalog()
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $extension_access$
declare
  uid uuid:=auth.uid();
  band text;
  owner_mode boolean:=false;
  family_mode boolean:=false;
  full_catalog boolean:=false;
  result jsonb;
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED' using errcode='42501';
  end if;

  band:=public.sinjira_age_band(uid);
  owner_mode:=public.is_sinjira_owner(uid);
  family_mode:=public.is_sinjira_catalog_family_member(uid);
  full_catalog:=owner_mode or family_mode;

  if band not in ('adult','youth','child') then
    return '[]'::jsonb;
  end if;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',e.id,
        'project_id',e.project_id,
        'project_slug',p.slug,
        'title',case
          when band='child' then 'Extension SINJIRA™ protégée'
          else e.title
        end,
        'description',case
          when band='child' then 'Extension visible dans le catalogue familial. Contenu protégé jusqu’à classification adaptée.'
          else e.description
        end,
        'status',case when band='child' then 'protected' else e.status end,
        'is_public',case when band='child' then false else e.is_public end,
        'creator_mode',owner_mode,
        'family_mode',family_mode,
        'content_available',case when band='child' then false else true end,
        'access_source',case
          when band='child' and family_mode then 'family_catalog'
          when owner_mode then 'owner'
          when family_mode then 'family'
          when e.product_slug is not null
               and public.has_sinjira_product(e.product_slug,uid) then 'product'
          when e.is_public=true and e.status in ('approved','released') then 'public'
          else 'catalogue'
        end
      )
      order by p.sort_order,p.name,e.created_at,e.title
    ),
    '[]'::jsonb
  ) into result
  from public.extensions e
  join public.projects p on p.id=e.project_id
  where
    case
      when band='child' then full_catalog
      when full_catalog then true
      else (
        p.status<>'draft'
        and (
          (e.is_public=true and e.status in ('approved','released'))
          or (
            e.status in ('approved','released')
            and e.product_slug is not null
            and public.has_sinjira_product(e.product_slug,uid)
          )
        )
      )
    end;

  return result;
end;
$extension_access$;

revoke all on function sinjira_v25_internal.sinjira_my_extension_catalog()
from public,anon,authenticated;
grant execute on function sinjira_v25_internal.sinjira_my_extension_catalog()
to authenticated,service_role;

comment on column public.extensions.product_slug is
  'Produit optionnel donnant accès à une extension privée. Aucun achat ni entitlement artificiel n est créé.';
comment on policy extensions_purchased_read_v25 on public.extensions is
  'Une extension privée publiée liée à un produit est lisible seulement par un compte adult/youth possédant un droit produit réel et si le projet parent n est pas un brouillon.';
comment on function public.sinjira_my_extension_catalog() is
  'Catalogue extension self-only: créateur/famille complet, public gratuit pour membre standard, privé acheté via droit produit réel, 11–12 famille minimisé et non ouvrable.';

commit;
