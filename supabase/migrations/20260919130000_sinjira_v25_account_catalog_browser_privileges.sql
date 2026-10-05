-- SINJIRA™ V25 — convergence des privilèges navigateur du catalogue Compte
--
-- Les tables ci-dessous sont protégées par RLS et sont lues directement par les
-- clients Compte/Bibliothèque. La reconstruction locale ne conservait pas les
-- privilèges SQL explicites attendus, ce qui rendait les policies inatteignables.
--
-- Cette migration ne contourne aucune policy : elle retire d'abord les privilèges
-- navigateur implicites puis réaccorde uniquement les opérations utilisées par
-- les parcours publics/authentifiés. Administration et mutations privilégiées
-- restent côté serveur/service_role.

begin;

-- project_access_rank() était volontairement service_role-only en public depuis
-- V24.5.24 afin d'éviter l'exposition directe d'un SECURITY DEFINER acceptant
-- un p_user_id arbitraire. Les policies RLS projects/documents dépendent toutefois
-- de son OID. On déplace donc l'implémentation privilégiée hors du schéma API
-- public sans la recréer : les policies existantes conservent cet OID.
create schema if not exists sinjira_catalog_internal;
revoke all on schema sinjira_catalog_internal from public, anon, authenticated;
grant usage on schema sinjira_catalog_internal to anon, authenticated, service_role;

do $catalog_boundary$
declare
  v_oid oid;
begin
  select p.oid
    into v_oid
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public'
    and p.proname='project_access_rank'
    and pg_get_function_identity_arguments(p.oid)='p_project_id uuid, p_user_id uuid'
    and p.prosecdef;

  if v_oid is null then
    raise exception 'V25 catalogue: project_access_rank public SECURITY DEFINER attendu avant déplacement';
  end if;

  execute 'alter function public.project_access_rank(uuid,uuid) set schema sinjira_catalog_internal';
end
$catalog_boundary$;

-- Fermer immédiatement l'oracle de rang après le déplacement. Les policies RLS
-- conservent le même OID; anon/authenticated ne peuvent calculer que le rang de
-- auth.uid() (NULL pour anon). service_role conserve le ciblage UUID explicite.
create or replace function sinjira_catalog_internal.project_access_rank(
  p_project_id uuid,
  p_user_id uuid default auth.uid()
)
returns integer
language sql
stable
security definer
set search_path=pg_catalog,public,auth
as $catalog_rank$
  select case
    when coalesce(auth.jwt()->>'role','') <> 'service_role'
         and p_user_id is distinct from auth.uid() then 0
    when public.is_sinjira_admin(p_user_id) then 100
    when exists(
      select 1
      from public.project_access pa
      where pa.project_id=p_project_id
        and pa.user_id=p_user_id
        and (pa.expires_at is null or pa.expires_at>now())
        and pa.access_level='tester'
    ) then 30
    when exists(
      select 1
      from public.project_access pa
      where pa.project_id=p_project_id
        and pa.user_id=p_user_id
        and (pa.expires_at is null or pa.expires_at>now())
        and pa.access_level='player'
    ) then 20
    when p_user_id is not null
         and exists(
           select 1 from public.projects p
           where p.id=p_project_id and p.visibility in ('public','account')
         ) then 10
    when exists(
      select 1 from public.projects p
      where p.id=p_project_id and p.visibility='public'
    ) then 1
    else 0
  end;
$catalog_rank$;

revoke all on function sinjira_catalog_internal.project_access_rank(uuid,uuid)
from public, anon, authenticated;
grant execute on function sinjira_catalog_internal.project_access_rank(uuid,uuid)
to anon, authenticated, service_role;

create function public.project_access_rank(
  p_project_id uuid,
  p_user_id uuid default auth.uid()
)
returns integer
language sql
stable
security invoker
set search_path=''
as $catalog_wrapper$
  select sinjira_catalog_internal.project_access_rank(p_project_id,p_user_id);
$catalog_wrapper$;

revoke all on function public.project_access_rank(uuid,uuid)
from public, anon, authenticated;
grant execute on function public.project_access_rank(uuid,uuid)
to service_role;

comment on schema sinjira_catalog_internal is
  'Implémentation privilégiée du rang projet utilisée par RLS. Hors schéma API public; wrapper public réservé au service_role.';

-- Catalogue projets : public/account filtré par RLS; aucune écriture navigateur.
revoke all on table public.projects from anon, authenticated;
grant select on table public.projects to anon, authenticated;

-- Accès projet : un membre relit uniquement ses propres lignes via RLS.
revoke all on table public.project_access from anon, authenticated;
grant select on table public.project_access to authenticated;

-- Demandes d'accès : lecture self-only + création d'une demande, sans décision client.
revoke all on table public.access_requests from anon, authenticated;
grant select, insert on table public.access_requests to authenticated;

-- Documents approuvés : lecture uniquement, bornée par RLS et les helpers d'accès.
revoke all on table public.documents from anon, authenticated;
grant select on table public.documents to anon, authenticated;

-- Playtests : consultation authentifiée uniquement.
revoke all on table public.playtests from anon, authenticated;
grant select on table public.playtests to authenticated;

-- Candidatures playtest : lecture self-only + candidature; aucune revue client.
revoke all on table public.playtest_participants from anon, authenticated;
grant select, insert on table public.playtest_participants to authenticated;

-- Extensions publiées : lecture uniquement, selon la policy publique existante.
revoke all on table public.extensions from anon, authenticated;
grant select on table public.extensions to anon, authenticated;

commit;
