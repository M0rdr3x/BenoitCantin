begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

-- SINJIRA V25 — contrat Performance Advisor.
-- Vérifié contre la production le 2026-09-05 : aucun `unindexed_foreign_keys`
-- n'est présent. Les `unused_index` restent informatifs et ne constituent jamais,
-- à eux seuls, un ordre de suppression.
--
-- Un index couvre une FK lorsque ses premières colonnes indexées correspondent,
-- dans l'ordre, aux colonnes de la FK. Un index partiel peut convenir : c'est le
-- cas volontaire de conscience_vault_audit_session_idx (session_id IS NOT NULL).

create temporary table v25_tables (
  schema_name text not null,
  table_name text not null,
  primary key(schema_name,table_name)
) on commit drop;

insert into v25_tables(schema_name,table_name) values
  ('private','conscience_entries'),
  ('private','conscience_vault_sessions'),
  ('private','conscience_vault_audit'),
  ('public','employment_profiles'),
  ('public','employment_applications'),
  ('private','personal_ai_settings'),
  ('private','personal_ai_source_permissions'),
  ('private','personal_ai_audit');

create temporary table v25_preserved_indexes (
  schema_name text not null,
  index_name text not null,
  primary key(schema_name,index_name)
) on commit drop;

-- Ces index sont actuellement remontés comme `unused_index` sur des modules V25
-- neufs/peu peuplés. Ils restent conservés car ils couvrent une FK ou un chemin
-- de requête explicite. Leur faible utilisation n'est pas une preuve d'inutilité.
insert into v25_preserved_indexes(schema_name,index_name) values
  ('private','conscience_entries_user_created_idx'),
  ('private','conscience_vault_sessions_user_active_idx'),
  ('private','conscience_vault_audit_user_time_idx'),
  ('private','conscience_vault_audit_session_idx'),
  ('public','employment_applications_user_created_idx'),
  ('public','employment_applications_user_status_idx'),
  ('private','personal_ai_audit_user_idx');

select plan(6);

select is(
  (select count(*)::int from v25_tables),
  8,
  'le contrat performance couvre les 8 tables des fondations V25 déployées'
);

select is(
  (
    select count(*)::int
    from pg_constraint con
    join pg_class c on c.oid=con.conrelid
    join pg_namespace n on n.oid=c.relnamespace
    join v25_tables t on t.schema_name=n.nspname and t.table_name=c.relname
    where con.contype='f'
  ),
  9,
  'les 8 tables V25 portent les 9 FK attendues'
);

select is(
  (
    select string_agg(format('%I.%I:%I',n.nspname,c.relname,con.conname), ', ' order by n.nspname,c.relname,con.conname)
    from pg_constraint con
    join pg_class c on c.oid=con.conrelid
    join pg_namespace n on n.oid=c.relnamespace
    join v25_tables t on t.schema_name=n.nspname and t.table_name=c.relname
    where con.contype='f'
      and not exists (
        select 1
        from pg_index i
        where i.indrelid=con.conrelid
          and i.indisvalid
          and i.indisready
          and i.indnkeyatts >= cardinality(con.conkey)
          and not exists (
            select 1
            from generate_subscripts(con.conkey,1) s
            where (i.indkey::smallint[])[s-1] is distinct from con.conkey[s]
          )
      )
  ),
  null::text,
  'aucune FK V25 ne peut rester sans index couvrant'
);

select is(
  (
    select string_agg(format('%I.%I',p.schema_name,p.index_name), ', ' order by p.schema_name,p.index_name)
    from v25_preserved_indexes p
    left join pg_class idx on idx.oid=to_regclass(format('%I.%I',p.schema_name,p.index_name))
    left join pg_index i on i.indexrelid=idx.oid
    where idx.oid is null or not coalesce(i.indisvalid,false) or not coalesce(i.indisready,false)
  ),
  null::text,
  'les 7 index V25 conservés malgré unused_index existent et restent valides/prêts'
);

select is(
  (
    select count(*)::int
    from pg_constraint con
    join pg_class c on c.oid=con.conrelid
    join pg_namespace n on n.oid=c.relnamespace
    join pg_index i on i.indrelid=c.oid
    join pg_class idx on idx.oid=i.indexrelid
    where n.nspname='private'
      and c.relname='conscience_vault_audit'
      and con.conname='conscience_vault_audit_session_id_fkey'
      and idx.relname='conscience_vault_audit_session_idx'
      and i.indisvalid
      and i.indisready
      and i.indpred is not null
      and i.indnkeyatts >= cardinality(con.conkey)
      and not exists (
        select 1
        from generate_subscripts(con.conkey,1) s
        where (i.indkey::smallint[])[s-1] is distinct from con.conkey[s]
      )
  ),
  1,
  'l’index partiel audit_session_idx couvre bien la FK session_id du coffre'
);

select is(
  (
    select string_agg(format('%I.%I',n.nspname,idx.relname), ', ' order by n.nspname,idx.relname)
    from pg_index i
    join pg_class tbl on tbl.oid=i.indrelid
    join pg_namespace n on n.oid=tbl.relnamespace
    join pg_class idx on idx.oid=i.indexrelid
    join v25_tables t on t.schema_name=n.nspname and t.table_name=tbl.relname
    where not i.indisvalid or not i.indisready
  ),
  null::text,
  'aucun index des tables V25 n’est invalide ou non prêt'
);

select * from finish();
rollback;
