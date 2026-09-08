begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,extensions;

select plan(33);

-- Trois commandes nommées, aucune fonction générique qui interprète du texte.
select has_function('public','social_live_join_public_room',array['text'],'RPC /join présente');
select has_function('public','social_live_list_rooms',array['integer'],'RPC /rooms présente');
select has_function('public','social_live_me',array[]::text[],'RPC /me présente');

select ok(not (select prosecdef from pg_proc where oid='public.social_live_join_public_room(text)'::regprocedure),'/join reste SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.social_live_list_rooms(integer)'::regprocedure),'/rooms reste SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.social_live_me()'::regprocedure),'/me reste SECURITY INVOKER');

select ok(has_function_privilege('authenticated','public.social_live_join_public_room(text)','EXECUTE'),'authenticated peut appeler /join');
select ok(has_function_privilege('authenticated','public.social_live_list_rooms(integer)','EXECUTE'),'authenticated peut appeler /rooms');
select ok(has_function_privilege('authenticated','public.social_live_me()','EXECUTE'),'authenticated peut appeler /me');
select ok(not has_function_privilege('anon','public.social_live_join_public_room(text)','EXECUTE'),'anon ne peut pas appeler /join');
select ok(not has_function_privilege('anon','public.social_live_list_rooms(integer)','EXECUTE'),'anon ne peut pas appeler /rooms');
select ok(not has_function_privilege('anon','public.social_live_me()','EXECUTE'),'anon ne peut pas appeler /me');

select is(
  (select oidvectortypes(proargtypes) from pg_proc where oid='public.social_live_join_public_room(text)'::regprocedure),
  'text'::text,
  '/join accepte uniquement un slug texte, jamais un UUID utilisateur'
);
select ok(
  position('^[a-z0-9][a-z0-9-]{2,47}$' in pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure))>0,
  '/join valide le format canonique du slug'
);
select ok(
  position('visibility = ''public''' in pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure))>0
  or position('visibility=''public''' in pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure))>0,
  '/join cible explicitement les salons publics seulement'
);
select ok(
  position('not r.is_archived' in pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure))>0,
  '/join refuse les salons archivés'
);
select ok(
  position('insert into public.social_live_room_members (room_id)' in lower(pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure)))>0
  or position('insert into public.social_live_room_members(room_id)' in lower(pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure)))>0,
  '/join ne fournit que room_id; identité et rôle restent dérivés côté DB'
);
select ok(
  position('social_live_room_invites' in pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure))=0,
  '/join ne contourne jamais le système d invitations privées'
);
select ok(
  position('execute ' in lower(pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure)))=0
  and position('format(' in lower(pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure)))=0,
  '/join ne contient aucun SQL dynamique'
);

select ok(
  position('from public.social_live_rooms' in lower(pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure)))>0,
  '/rooms lit la table canonique soumise à RLS'
);
select ok(
  position('''owner_user_id''' in pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure))=0
  and position('''user_id''' in pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure))=0,
  '/rooms ne sérialise aucun UUID utilisateur dans le JSON'
);
select ok(
  position('least(coalesce(p_limit, 50), 100)' in pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure))>0
  or position('least(coalesce(p_limit,50),100)' in pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure))>0,
  '/rooms borne la taille de réponse à 100 salons'
);
select ok(
  position('m.user_id = v_user' in pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure))>0
  or position('m.user_id=v_user' in pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure))>0,
  '/rooms calcule joined uniquement pour le compte courant'
);

select ok(
  position('''profile_label''' in pg_get_functiondef('public.social_live_me()'::regprocedure))>0,
  '/me retourne un libellé de profil minimal'
);
select ok(
  position('''user_id''' in pg_get_functiondef('public.social_live_me()'::regprocedure))=0
  and position('''owner_user_id''' in pg_get_functiondef('public.social_live_me()'::regprocedure))=0,
  '/me ne retourne aucun UUID utilisateur'
);
select ok(
  position('date_of_birth' in lower(pg_get_functiondef('public.social_live_me()'::regprocedure)))=0
  and position('sinjira_age_band' in lower(pg_get_functiondef('public.social_live_me()'::regprocedure)))=0,
  '/me ne retourne ni date de naissance ni cohorte d âge'
);

select ok(
  position('inet_client_addr' in lower(pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure)))=0
  and position('inet_client_addr' in lower(pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure)))=0
  and position('inet_client_addr' in lower(pg_get_functiondef('public.social_live_me()'::regprocedure)))=0,
  'les commandes ne collectent aucune IP'
);
select ok(
  position('latitude' in lower(pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure)))=0
  and position('longitude' in lower(pg_get_functiondef('public.social_live_join_public_room(text)'::regprocedure)))=0
  and position('latitude' in lower(pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure)))=0
  and position('longitude' in lower(pg_get_functiondef('public.social_live_list_rooms(integer)'::regprocedure)))=0
  and position('latitude' in lower(pg_get_functiondef('public.social_live_me()'::regprocedure)))=0
  and position('longitude' in lower(pg_get_functiondef('public.social_live_me()'::regprocedure)))=0,
  'les commandes ne collectent aucun GPS'
);
select ok(
  not exists(
    select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.proname in ('social_live_join_public_room','social_live_list_rooms','social_live_me')
      and p.prosecdef
  ),
  'aucune commande En direct publique privilégiée n existe'
);
select ok(to_regclass('public.social_live_presence') is null,'les commandes n ajoutent aucune présence persistante');

select throws_ok($$select public.social_live_join_public_room('salon-test')$$,'P0001','AUTH_REQUIRED','/join échoue fermé sans session');
select throws_ok($$select public.social_live_list_rooms(20)$$,'P0001','AUTH_REQUIRED','/rooms échoue fermé sans session');
select throws_ok($$select public.social_live_me()$$,'P0001','AUTH_REQUIRED','/me échoue fermé sans session');

select * from finish();
rollback;
