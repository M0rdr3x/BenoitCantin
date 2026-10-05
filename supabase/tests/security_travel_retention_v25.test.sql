-- SINJIRA™ V25 — Contrat de rétention du Mode Voyage
-- Vérifie la primitive de purge sans exposer ni fabriquer de données de voyage.

begin;

select plan(11);

select ok(
  to_regprocedure('private.security_purge_expired_travel_plans_v25()') is not null,
  'la primitive privée de purge Mode Voyage existe'
);

select is(
  (
    select p.prorettype::regtype::text
    from pg_proc p
    where p.oid = to_regprocedure('private.security_purge_expired_travel_plans_v25()')
  ),
  'bigint',
  'la purge retourne uniquement un nombre de lignes supprimées'
);

select ok(
  coalesce((
    select p.prosecdef
    from pg_proc p
    where p.oid = to_regprocedure('private.security_purge_expired_travel_plans_v25()')
  ), false),
  'la purge est SECURITY DEFINER côté serveur'
);

select is(
  (
    select p.pronargs::integer
    from pg_proc p
    where p.oid = to_regprocedure('private.security_purge_expired_travel_plans_v25()')
  ),
  0,
  'aucun instant de purge arbitraire ne peut être fourni par un appelant'
);

select ok(
  has_function_privilege('service_role', 'private.security_purge_expired_travel_plans_v25()', 'EXECUTE'),
  'service_role peut lancer la purge serveur'
);

select ok(
  not has_function_privilege('authenticated', 'private.security_purge_expired_travel_plans_v25()', 'EXECUTE'),
  'authenticated ne peut pas lancer la purge'
);

select ok(
  not has_function_privilege('anon', 'private.security_purge_expired_travel_plans_v25()', 'EXECUTE'),
  'anon ne peut pas lancer la purge'
);

select ok(
  position(
    'delete from public.security_travel_plans'
    in lower(pg_get_functiondef(to_regprocedure('private.security_purge_expired_travel_plans_v25()')))
  ) > 0,
  'la purge cible uniquement la table Mode Voyage'
);

select ok(
  position(
    'where delete_after <= statement_timestamp()'
    in lower(pg_get_functiondef(to_regprocedure('private.security_purge_expired_travel_plans_v25()')))
  ) > 0,
  'delete_after est l’unique échéance canonique de purge'
);

select ok(
  position(
    'ends_at'
    in lower(pg_get_functiondef(to_regprocedure('private.security_purge_expired_travel_plans_v25()')))
  ) = 0,
  'la purge ne recalcule pas la rétention depuis ends_at'
);

select ok(
  position(
    'cron.schedule'
    in lower(pg_get_functiondef(to_regprocedure('private.security_purge_expired_travel_plans_v25()')))
  ) = 0
  and position(
    'pg_cron'
    in lower(pg_get_functiondef(to_regprocedure('private.security_purge_expired_travel_plans_v25()')))
  ) = 0,
  'la primitive ne prétend pas configurer un ordonnanceur de production'
);

select * from finish();
rollback;
