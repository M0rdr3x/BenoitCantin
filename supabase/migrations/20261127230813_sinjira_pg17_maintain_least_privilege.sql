-- Candidat à une migration générée par le CLI; jamais exécuté directement en production.
-- PostgreSQL 17+, propriétaires applicatifs postgres uniquement.
do $remediation$
declare
  item record;
begin
  if current_setting('server_version_num')::int < 170000 then
    raise exception 'PG17_REQUIRED_FOR_MAINTAIN';
  end if;
  if not pg_has_role(current_user,'postgres','USAGE') then
    raise exception 'POSTGRES_OWNER_REQUIRED';
  end if;
  perform set_config('lock_timeout','5s',true);
  perform set_config('statement_timeout','60s',true);

  -- Refus explicite si le périmètre de propriété diverge de l'audit.
  if exists (
    select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname in ('public','private') and c.relkind in ('r','p')
      and c.relowner <> 'postgres'::regrole
      and (has_table_privilege('anon',c.oid,'MAINTAIN')
        or has_table_privilege('authenticated',c.oid,'MAINTAIN'))
  ) then raise exception 'UNEXPECTED_TABLE_OWNER'; end if;

  -- Une ACL globale ne peut pas être annulée par un retrait par schéma.
  if exists (
    select 1 from pg_default_acl d cross join lateral aclexplode(d.defaclacl) a
    where d.defaclrole='postgres'::regrole and d.defaclnamespace=0
      and d.defaclobjtype='r' and a.privilege_type='MAINTAIN'
      and a.grantee in (0,'anon'::regrole::oid,'authenticated'::regrole::oid)
  ) then raise exception 'GLOBAL_MAINTAIN_DEFAULT_REQUIRES_REVIEW'; end if;

  for item in
    select n.nspname,c.relname from pg_class c
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname in ('public','private') and c.relkind in ('r','p')
      and c.relowner='postgres'::regrole
      and (has_table_privilege('anon',c.oid,'MAINTAIN')
        or has_table_privilege('authenticated',c.oid,'MAINTAIN'))
    order by n.nspname,c.relname
  loop
    execute format('revoke maintain on table %I.%I from public, anon, authenticated',
                   item.nspname,item.relname);
  end loop;
  execute 'alter default privileges for role postgres in schema public, private revoke maintain on tables from public, anon, authenticated';

  if exists (
    select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname in ('public','private') and c.relkind in ('r','p')
      and (has_table_privilege('anon',c.oid,'MAINTAIN')
        or has_table_privilege('authenticated',c.oid,'MAINTAIN'))
  ) then raise exception 'EFFECTIVE_MAINTAIN_REMAINS'; end if;
  if exists (
    select 1 from pg_default_acl d
    join pg_namespace n on n.oid=d.defaclnamespace
    cross join lateral aclexplode(d.defaclacl) a
    where d.defaclrole='postgres'::regrole and n.nspname in ('public','private')
      and d.defaclobjtype='r' and a.privilege_type='MAINTAIN'
      and a.grantee in (0,'anon'::regrole::oid,'authenticated'::regrole::oid)
  ) then raise exception 'POSTGRES_DEFAULT_MAINTAIN_REMAINS'; end if;
  -- Les ACL du rôle hébergeur supabase_admin ne sont pas modifiées.
end
$remediation$;
