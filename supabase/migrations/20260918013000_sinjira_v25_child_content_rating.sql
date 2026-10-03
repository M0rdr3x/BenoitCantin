-- SINJIRA™ V25 — classement explicite des projets/documents pour les comptes 11–12 ans.
-- Aucun contenu existant n'est automatiquement approuvé : le défaut reste unreviewed.

alter table public.projects
  add column if not exists child_access_status text not null default 'unreviewed'
    check (child_access_status in ('unreviewed','approved_11_12','blocked_11_12')),
  add column if not exists child_access_reviewed_at timestamptz,
  add column if not exists child_access_reviewed_by uuid references auth.users(id) on delete set null,
  add column if not exists child_access_review_note text;

alter table public.documents
  add column if not exists child_access_status text not null default 'unreviewed'
    check (child_access_status in ('unreviewed','approved_11_12','blocked_11_12')),
  add column if not exists child_access_reviewed_at timestamptz,
  add column if not exists child_access_reviewed_by uuid references auth.users(id) on delete set null,
  add column if not exists child_access_review_note text;

create or replace function public.sinjira_child_project_available(p_project_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,auth
as $child_rating$
  select exists(
    select 1 from public.projects p
    where p.id=p_project_id
      and p.status<>'draft'
      and (
        p.visibility='public'
        or (p.visibility='account' and auth.uid() is not null)
      )
      and p.child_access_status='approved_11_12'
  );
$child_rating$;
revoke all on function public.sinjira_child_project_available(uuid) from public;
grant execute on function public.sinjira_child_project_available(uuid) to anon,authenticated,service_role;

create or replace function public.sinjira_child_document_available(p_document_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,auth
as $child_rating$
  select exists(
    select 1 from public.documents d
    where d.id=p_document_id
      and d.status='approved'
      and d.child_access_status='approved_11_12'
      and public.sinjira_child_project_available(d.project_id)
      and public.project_access_rank(d.project_id,auth.uid())
          >= public.document_access_rank(d.access_level)
  );
$child_rating$;
revoke all on function public.sinjira_child_document_available(uuid) from public;
grant execute on function public.sinjira_child_document_available(uuid) to anon,authenticated,service_role;

-- Projets : un child ne voit dans sa bibliothèque que les projets explicitement approuvés 11–12.
-- Les visiteurs anonymes et les autres bandes conservent le comportement historique.
drop policy if exists "projects readable when accessible" on public.projects;
drop policy if exists admin_read_all_projects on public.projects;
drop policy if exists projects_read on public.projects;
drop policy if exists projects_public_read on public.projects;
drop policy if exists projects_authenticated_read on public.projects;
create policy "projects readable when accessible" on public.projects for select to anon,authenticated
using(
  status<>'draft' and (
    (
      visibility='public'
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
      and (visibility='account' or public.project_access_rank(id,(select auth.uid()))>=20)
    )
    or (
      (select auth.uid()) is not null
      and public.sinjira_my_age_band()='child'
      and visibility='account'
      and child_access_status='approved_11_12'
    )
  )
);

-- Documents : un child exige une double approbation explicite document + projet.
drop policy if exists "approved documents visible by access" on public.documents;
drop policy if exists documents_read_by_access on public.documents;
drop policy if exists admin_read_all_documents on public.documents;
drop policy if exists documents_anon_read on public.documents;
drop policy if exists documents_authenticated_read on public.documents;
create policy "approved documents visible by access" on public.documents for select to anon,authenticated
using(
  status='approved'
  and public.project_access_rank(project_id,(select auth.uid()))>=public.document_access_rank(access_level)
  and (
    (select auth.uid()) is null
    or public.sinjira_my_age_band() in ('adult','youth')
    or (
      public.sinjira_my_age_band()='child'
      and public.sinjira_child_document_available(id)
    )
  )
);

comment on column public.projects.child_access_status is
  'Décision humaine explicite pour la bande 11–12. unreviewed reste fermé; aucune approbation implicite.';
comment on column public.documents.child_access_status is
  'Décision humaine explicite document par document pour 11–12; le projet parent doit aussi être approuvé.';
comment on function public.sinjira_child_project_available(uuid) is
  'Disponibilité 11–12 : projet non brouillon explicitement approuvé; anon seulement pour public, account exige une session authentifiée.';
comment on function public.sinjira_child_document_available(uuid) is
  'Disponibilité 11–12 : document + projet approuvés et rang d accès réel du compte courant suffisant; aucun oracle anon sur account/restricted.';
