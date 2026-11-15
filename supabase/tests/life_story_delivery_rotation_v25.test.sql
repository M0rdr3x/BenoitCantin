-- Test SQL pgtap exécuté sur PostgreSQL local uniquement.
-- Aucun utilisateur réel, jeton réel ou modification de production.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,extensions;

select plan(10);
select ok(
  to_regprocedure('public.service_life_story_rotate_delivery_links(uuid,jsonb)') is not null,
  'la RPC atomique de liens existe'
);
select ok(
  (select p.prosecdef from pg_proc p
   where p.oid='public.service_life_story_rotate_delivery_links(uuid,jsonb)'::regprocedure),
  'l implémentation est SECURITY DEFINER'
);
select ok(
  not has_function_privilege('anon',
    'public.service_life_story_rotate_delivery_links(uuid,jsonb)','EXECUTE'),
  'anon ne peut pas appeler la rotation'
);
select ok(
  not has_function_privilege('authenticated',
    'public.service_life_story_rotate_delivery_links(uuid,jsonb)','EXECUTE'),
  'le navigateur authentifié ne peut pas appeler la rotation'
);
select ok(
  has_function_privilege('service_role',
    'public.service_life_story_rotate_delivery_links(uuid,jsonb)','EXECUTE'),
  'seul service_role peut exécuter la rotation'
);
select ok(
  position('search_path' in lower(pg_get_functiondef(
    'public.service_life_story_rotate_delivery_links(uuid,jsonb)'::regprocedure))) > 0,
  'la fonction fixe explicitement son search_path'
);
select ok(
  position('for update' in lower(pg_get_functiondef(
    'public.service_life_story_rotate_delivery_links(uuid,jsonb)'::regprocedure))) > 0,
  'le verrou par export existe'
);
select ok(
  position('jsonb_array_length(v_export.recipients_snapshot)' in
    pg_get_functiondef('public.service_life_story_rotate_delivery_links(uuid,jsonb)'::regprocedure)) > 0,
  'le nombre de nouveaux jetons suit le snapshot serveur'
);
select ok(
  position('delete from public.life_story_delivery_links' in lower(pg_get_functiondef(
    'public.service_life_story_rotate_delivery_links(uuid,jsonb)'::regprocedure))) > 0
  and position('insert into public.life_story_delivery_links' in lower(pg_get_functiondef(
    'public.service_life_story_rotate_delivery_links(uuid,jsonb)'::regprocedure))) > 0,
  'la suppression et l insertion partagent une fonction SQL'
);
select throws_ok(
  $$ select public.service_life_story_rotate_delivery_links(
    '00000000-0000-4000-8000-000000000001'::uuid,
    '[]'::jsonb) $$,
  'P0001',
  'SERVICE_ROLE_REQUIRED',
  'un appel SQL non serveur échoue avant l accès aux données'
);

select * from finish();
rollback;
