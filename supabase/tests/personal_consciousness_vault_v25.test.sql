begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, private, auth, extensions;

select plan(24);

select has_table('private','conscience_entries','le coffre personnel existe dans le schema private');
select has_table('private','conscience_vault_sessions','les sessions temporaires du coffre existent');
select has_table('private','conscience_vault_audit','audit prive du coffre existe');

-- Aucun rôle client ni service_role ne lit directement le contenu intime.
select ok(not has_table_privilege('anon','private.conscience_entries','SELECT'),
  'anon ne peut pas lire directement les entrees');
select ok(not has_table_privilege('authenticated','private.conscience_entries','SELECT'),
  'authenticated ne peut pas lire directement ses propres entrees');
select ok(not has_table_privilege('service_role','private.conscience_entries','SELECT'),
  'service_role ne peut pas SELECT directement le contenu du coffre');
select ok(not has_table_privilege('anon','private.conscience_vault_sessions','SELECT'),
  'anon ne peut pas lire les capacites du coffre');
select ok(not has_table_privilege('authenticated','private.conscience_vault_sessions','SELECT'),
  'authenticated ne peut pas lire les capacites du coffre');
select ok(not has_table_privilege('service_role','private.conscience_vault_sessions','SELECT'),
  'service_role ne peut pas contourner les RPC via la table de sessions');

-- Les points d'entree publics restent strictement serveur.
select ok(not has_function_privilege('anon',
  'public.service_conscience_open_session(uuid,text,integer,text,text,integer)','EXECUTE'),
  'anon ne peut pas ouvrir une session de coffre');
select ok(not has_function_privilege('authenticated',
  'public.service_conscience_open_session(uuid,text,integer,text,text,integer)','EXECUTE'),
  'authenticated ne peut pas ouvrir directement une session de coffre');
select ok(has_function_privilege('service_role',
  'public.service_conscience_open_session(uuid,text,integer,text,text,integer)','EXECUTE'),
  'service_role peut appeler le point entree serveur');
select ok(not has_function_privilege('authenticated',
  'public.service_conscience_list_entries(uuid,uuid)','EXECUTE'),
  'authenticated ne peut pas lister directement le Registre personnel');
select ok(has_function_privilege('service_role',
  'public.service_conscience_list_entries(uuid,uuid)','EXECUTE'),
  'service_role peut utiliser la voie serveur avec capacite');

-- Les helpers privés ne constituent pas une porte de derrière pour service_role.
select ok(not has_function_privilege('service_role',
  'private.conscience_vault_require_service_role()','EXECUTE'),
  'helper de role non invocable directement par service_role');
select ok(not has_function_privilege('service_role',
  'private.conscience_vault_assert_session(uuid,uuid)','EXECUTE'),
  'helper de session non invocable directement par service_role');

-- L'audit ne possède aucune colonne de contenu ou de résumé intime.
select ok(not exists(
  select 1 from information_schema.columns
  where table_schema='private' and table_name='conscience_vault_audit'
    and column_name in ('content','content_payload','payload','body','summary','text','ciphertext')
), 'audit du coffre ne contient aucune colonne de contenu intime');

-- Tous les RPC de coffre sont SECURITY DEFINER avec search_path explicite.
select ok(
  (select count(*)=6 and bool_and(p.prosecdef)
   from pg_proc p
   join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname like 'service_conscience_%'),
  'les six RPC de coffre sont SECURITY DEFINER'
);
select ok(
  (select count(*)=6 and bool_and(array_to_string(p.proconfig,',') like '%search_path=%')
   from pg_proc p
   join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname like 'service_conscience_%'),
  'les six RPC de coffre figent leur search_path'
);

-- Les assertions suivantes simulent uniquement le contexte serveur. Aucun utilisateur valide
-- n'est nécessaire car chaque garde doit refuser avant toute lecture/écriture du coffre.
select set_config('request.jwt.claims','{"role":"service_role"}',true);

select throws_ok(
  $$select public.service_conscience_open_session('00000000-0000-0000-0000-000000000001','aal1',0,'allow','v25.0',300)$$,
  '42501','AAL2_REQUIRED',
  'AAL1 est toujours refuse meme si le risque est faible'
);
select throws_ok(
  $$select public.service_conscience_open_session('00000000-0000-0000-0000-000000000001','aal2',80,'allow','v25.0',300)$$,
  '42501','RISK_NOT_ACCEPTABLE',
  'un risque critique bloque le coffre'
);
select throws_ok(
  $$select public.service_conscience_open_session('00000000-0000-0000-0000-000000000001','aal2',50,'challenge','v25.0',300)$$,
  '42501','RISK_APPROVAL_REQUIRED',
  'un challenge non resolu ne peut pas ouvrir le coffre'
);
select throws_ok(
  $$select public.service_conscience_open_session('00000000-0000-0000-0000-000000000001','aal2',20,'allow','v25.0',601)$$,
  '22023','VAULT_TTL_INVALID',
  'une capacite de plus de dix minutes est refusee'
);
select throws_ok(
  $$select public.service_conscience_open_session('00000000-0000-0000-0000-000000000001','aal2',20,'allow','legacy',300)$$,
  '42501','RISK_MODEL_V25_REQUIRED',
  'le coffre refuse une decision provenant dun ancien modele de risque'
);

select * from finish();
rollback;
