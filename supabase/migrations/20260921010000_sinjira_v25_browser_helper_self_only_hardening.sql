-- SINJIRA™ V25 — durcissement self-only des helpers navigateur de catalogue.
-- L’HUMAIN AVANT TOUT : une fonction interne exécutable pour permettre la RLS ne
-- doit jamais devenir une API permettant de sonder le rang ou l’existence d’un
-- autre compte/contenu par UUID.

begin;

-- Les policies RLS projects/documents dépendent de l'OID de cette fonction.
-- CREATE OR REPLACE conserve cet OID tout en bornant les appels navigateur :
-- anon/authenticated peuvent uniquement calculer le rang du compte courant
-- (NULL pour anon); service_role conserve l'usage serveur avec p_user_id arbitraire.
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
from public,anon,authenticated;
grant execute on function sinjira_catalog_internal.project_access_rank(uuid,uuid)
to anon,authenticated,service_role;

-- Le helper reste exécutable par anon car les policies publiques l'utilisent,
-- mais anon ne peut plus confirmer l'existence d'un projet visibility='account'.
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

-- La disponibilité document suit désormais aussi le rang d'accès réel.
-- Un appel anon ne peut donc confirmer qu'un document public d'un projet public;
-- un compte authentifié reste borné à son propre rang via project_access_rank.
create or replace function sinjira_v25_internal.sinjira_child_document_available(
  p_document_id uuid
)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,auth,sinjira_v25_internal,sinjira_catalog_internal
as $child_document$
  select exists(
    select 1
    from public.documents d
    where d.id=p_document_id
      and d.status='approved'
      and d.child_access_status='approved_11_12'
      and sinjira_v25_internal.sinjira_child_project_available(d.project_id)
      and sinjira_catalog_internal.project_access_rank(d.project_id,auth.uid())
          >= public.document_access_rank(d.access_level)
  );
$child_document$;

revoke all on function sinjira_v25_internal.sinjira_child_document_available(uuid)
from public,anon,authenticated;
grant execute on function sinjira_v25_internal.sinjira_child_document_available(uuid)
to anon,authenticated,service_role;

comment on function sinjira_catalog_internal.project_access_rank(uuid,uuid) is
  'Helper RLS catalogue: anon/authenticated uniquement pour auth.uid(); service_role peut cibler un UUID explicite. Retourne 0 sur tentative navigateur de sonder un autre compte.';

comment on function sinjira_v25_internal.sinjira_child_project_available(uuid) is
  'Disponibilité 11–12: anon uniquement pour projet public; account exige une session authentifiée; restricted reste fermé.';

comment on function sinjira_v25_internal.sinjira_child_document_available(uuid) is
  'Disponibilité document 11–12: double approbation et rang d’accès réel du compte courant; aucun oracle anon sur contenu account/restricted.';

commit;
