-- SINJIRA™ V25 — accès produit générique pour jeux et autres projets.
-- La Bibliothèque d'un membre standard contient les créations gratuites et celles
-- réellement autorisées/achetées. Le catalogue public peut conserver une fiche
-- marketing, mais les documents et actions privées restent bornés au droit réel.

begin;

alter table public.projects
  add column if not exists product_slug text;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname='projects_product_slug_fkey'
      and conrelid='public.projects'::regclass
  ) then
    alter table public.projects
      add constraint projects_product_slug_fkey
      foreign key(product_slug)
      references public.products(slug)
      on update cascade
      on delete set null;
  end if;
end;
$$;

create index if not exists projects_product_slug_idx
  on public.projects(product_slug)
  where product_slug is not null;

-- Convergence du jeu actuellement licencié vers le mécanisme générique.
update public.projects p
set product_slug='fracture-du-reseau-mere'
where p.slug='fracture-du-reseau-mere'
  and exists(
    select 1 from public.products product
    where product.slug='fracture-du-reseau-mere'
  );

drop policy if exists projects_purchased_read_v25 on public.projects;
create policy projects_purchased_read_v25
on public.projects
for select
to authenticated
using (
  status<>'draft'
  and product_slug is not null
  and public.sinjira_my_age_band() in ('adult','youth')
  and public.has_sinjira_product(product_slug,(select auth.uid()))
);

-- Les documents d'un projet lié à un produit ne deviennent pas lisibles par la
-- seule visibilité publique/account du projet. Un droit produit réel, un accès
-- projet explicite ou le catalogue créateur/famille adulte est requis.
drop policy if exists "approved documents visible by access" on public.documents;
create policy "approved documents visible by access"
on public.documents
for select
to anon,authenticated
using (
  status='approved'
  and sinjira_catalog_internal.project_access_rank(project_id,(select auth.uid()))
      >= public.document_access_rank(access_level)
  and (
    (select auth.uid()) is null
    or public.sinjira_my_age_band() in ('adult','youth')
    or (
      public.sinjira_my_age_band()='child'
      and public.sinjira_child_document_available(id)
    )
  )
  and (
    not exists(
      select 1
      from public.projects parent_project
      where parent_project.id=documents.project_id
        and parent_project.product_slug is not null
    )
    or (
      (select auth.uid()) is not null
      and exists(
        select 1
        from public.projects parent_project
        where parent_project.id=documents.project_id
          and parent_project.status<>'draft'
          and parent_project.product_slug is not null
          and public.has_sinjira_product(
            parent_project.product_slug,
            (select auth.uid())
          )
      )
    )
    or sinjira_catalog_internal.project_access_rank(
         project_id,
         (select auth.uid())
       )>=20
  )
);

-- Un projet payant n'est jamais rendu ouvrable dans la bande 11–12 ans.
create or replace function sinjira_v25_internal.sinjira_child_project_available(
  p_project_id uuid
)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,auth
as $child_project$
  select exists(
    select 1
    from public.projects p
    where p.id=p_project_id
      and p.status<>'draft'
      and p.child_access_status='approved_11_12'
      and p.product_slug is null
      and (
        p.visibility='public'
        or (p.visibility='account' and auth.uid() is not null)
      )
  );
$child_project$;

revoke all on function sinjira_v25_internal.sinjira_child_project_available(uuid)
from public,anon,authenticated;
grant execute on function sinjira_v25_internal.sinjira_child_project_available(uuid)
to anon,authenticated,service_role;

-- La policy générale conserve les fiches publiques/account historiques pour
-- adultes/jeunes, mais les comptes child ne reçoivent jamais un projet payant.
drop policy if exists "projects readable when accessible" on public.projects;
create policy "projects readable when accessible"
on public.projects
for select
to anon,authenticated
using (
  status<>'draft' and (
    (
      visibility='public'
      and product_slug is null
      and (
        (select auth.uid()) is null
        or public.sinjira_my_age_band() in ('adult','youth')
        or (
          public.sinjira_my_age_band()='child'
          and child_access_status='approved_11_12'
        )
      )
    )
    or (
      (select auth.uid()) is not null
      and public.sinjira_my_age_band() in ('adult','youth')
      and (
        (visibility='account' and product_slug is null)
        or sinjira_catalog_internal.project_access_rank(id,(select auth.uid()))>=20
      )
    )
    or (
      (select auth.uid()) is not null
      and public.sinjira_my_age_band()='child'
      and visibility='account'
      and child_access_status='approved_11_12'
      and product_slug is null
    )
  )
);

create or replace function sinjira_v25_internal.sinjira_my_project_catalog()
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,auth,sinjira_catalog_internal,sinjira_v25_internal
as $project_catalog$
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
  family_mode:=sinjira_v25_internal.is_sinjira_catalog_family_member(uid);
  full_catalog:=owner_mode or family_mode;

  if band not in ('adult','youth','child') then
    return '[]'::jsonb;
  end if;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',p.id,
        'slug',p.slug,
        'name',p.name,
        'type',p.type,
        'status',p.status,
        'visibility',p.visibility,
        'description',case
          when band='child'
               and not (
                 p.status<>'draft'
                 and p.visibility in ('public','account')
                 and p.child_access_status='approved_11_12'
                 and p.product_slug is null
               )
            then 'Création SINJIRA™ visible dans le catalogue familial. Contenu protégé selon l’âge.'
          else p.description
        end,
        'cover_url',case
          when band='child'
               and not (
                 p.status<>'draft'
                 and p.visibility in ('public','account')
                 and p.child_access_status='approved_11_12'
                 and p.product_slug is null
               )
            then null
          else p.cover_url
        end,
        'public_path',case
          when band='child'
               and not (
                 p.status<>'draft'
                 and p.visibility in ('public','account')
                 and p.child_access_status='approved_11_12'
                 and p.product_slug is null
               )
            then null
          else p.public_path
        end,
        'play_path',case
          when band='child' then null
          else p.play_path
        end,
        'product_slug',case when band='child' then null else p.product_slug end,
        'allow_tester_requests',case when band='child' then false else p.allow_tester_requests end,
        'sort_order',p.sort_order,
        'child_access_status',p.child_access_status,
        'creator_mode',owner_mode,
        'family_mode',family_mode,
        'content_available',case
          when band='child' then
            p.status<>'draft'
            and p.visibility in ('public','account')
            and p.child_access_status='approved_11_12'
            and p.product_slug is null
          else true
        end,
        'access_source',case
          when band='child' and family_mode then 'family_catalog'
          when owner_mode then 'owner'
          when family_mode then 'family'
          when p.product_slug is not null
               and sinjira_v25_internal.has_sinjira_product(p.product_slug,uid)
            then 'product'
          when sinjira_catalog_internal.project_access_rank(p.id,uid)>=20
            then 'access'
          else 'free'
        end
      )
      order by p.sort_order,p.name
    ),
    '[]'::jsonb
  )
  into result
  from public.projects p
  where
    case
      when band='child' then
        full_catalog
        or (
          p.status<>'draft'
          and p.visibility in ('public','account')
          and p.child_access_status='approved_11_12'
          and p.product_slug is null
        )
      when full_catalog then true
      else
        p.status<>'draft'
        and (
          (
            p.visibility in ('public','account')
            and p.product_slug is null
          )
          or (
            p.product_slug is not null
            and sinjira_v25_internal.has_sinjira_product(p.product_slug,uid)
          )
          or sinjira_catalog_internal.project_access_rank(p.id,uid)>=20
        )
    end;

  return result;
end;
$project_catalog$;

revoke all on function sinjira_v25_internal.sinjira_my_project_catalog()
from public,anon,authenticated;
grant execute on function sinjira_v25_internal.sinjira_my_project_catalog()
to authenticated,service_role;

comment on column public.projects.product_slug is
  'Produit optionnel donnant accès au projet dans la Bibliothèque. NULL signifie création non liée à un achat.';
comment on policy projects_purchased_read_v25 on public.projects is
  'Un projet privé lié à un produit devient lisible au compte adult/youth seulement avec un droit produit réel.';
comment on function public.sinjira_my_project_catalog() is
  'Bibliothèque projet self-only: membre standard = gratuit + acheté/autorisé; créateur/famille = catalogue complet; 11–12 = fiches familiales minimisées et aucun projet payant ouvrable.';

commit;
