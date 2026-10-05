-- SINJIRA V25 — garde explicite des repères de source canonique
-- Forward-only : ne réécrit aucune migration V25 déjà existante.
-- Une source canonique vérifiée doit toujours conserver un repère exploitable
-- afin que les erreurs d'administration restent déterministes et auditables.

create or replace function private.sinjira_guard_canon_source_lifecycle()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $canon_source_lifecycle$
begin
  if new.verification_status in ('VERIFIED','SECRET_AUTEUR')
     and (
       (
         new.source_kind='roman'
         and nullif(btrim(coalesce(new.chapter_reference,'')),'') is null
       )
       or (
         nullif(btrim(coalesce(new.chapter_reference,'')),'') is null
         and nullif(btrim(coalesce(new.passage_reference,'')),'') is null
         and nullif(btrim(coalesce(new.source_version,'')),'') is null
       )
     ) then
    raise exception 'CANON_SOURCE_LOCATOR_REQUIRED';
  end if;

  if tg_op='INSERT' and new.verification_status='RETIRED' then
    raise exception 'CANON_SOURCE_CREATE_RETIRED_FORBIDDEN';
  end if;

  if tg_op='UPDATE'
     and old.verification_status='RETIRED'
     and new.verification_status is distinct from 'RETIRED' then
    raise exception 'CANON_SOURCE_RETIRED_FINAL';
  end if;

  if new.supersedes_source_id is not null
     and new.source_kind not in ('roman','bible','author_decision','archive') then
    raise exception 'CANON_SOURCE_SUPERSEDES_KIND_INVALID';
  end if;

  return new;
end;
$canon_source_lifecycle$;

drop trigger if exists sinjira_canon_sources_guard_lifecycle
on public.sinjira_canon_sources;

create trigger sinjira_canon_sources_guard_lifecycle
before insert or update of
  source_kind,
  verification_status,
  supersedes_source_id,
  chapter_reference,
  passage_reference,
  source_version
on public.sinjira_canon_sources
for each row execute function private.sinjira_guard_canon_source_lifecycle();

revoke all on function private.sinjira_guard_canon_source_lifecycle()
from public,anon,authenticated,service_role;
