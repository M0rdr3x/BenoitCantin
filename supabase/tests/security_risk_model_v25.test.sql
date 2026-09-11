begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(27);

-- Provenance du score : la version du modèle doit être conservée sur chaque événement.
select ok(
  exists(
    select 1
    from information_schema.columns
    where table_schema='public'
      and table_name='security_connection_events'
      and column_name='risk_model_version'
      and is_nullable='NO'
  ),
  'security_connection_events journalise une version de modèle non nulle'
);

-- Le calcul déterministe reste un détail serveur.
select ok(
  not has_function_privilege(
    'anon',
    'private.security_risk_score_v25(boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean)',
    'EXECUTE'
  ),
  'anon ne peut pas exécuter le moteur V25'
);
select ok(
  not has_function_privilege(
    'authenticated',
    'private.security_risk_score_v25(boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean)',
    'EXECUTE'
  ),
  'authenticated ne peut pas exécuter directement le moteur V25'
);
select ok(
  has_function_privilege(
    'service_role',
    'private.security_risk_score_v25(boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean)',
    'EXECUTE'
  ),
  'service_role peut exécuter le moteur V25'
);

-- Le point d’entrée contextuel existant demeure strictement serveur.
select ok(
  not has_function_privilege(
    'anon',
    'public.security_evaluate_context(uuid,text,text,text,text,text,text,text)',
    'EXECUTE'
  ),
  'anon ne peut pas évaluer un contexte de sécurité'
);
select ok(
  not has_function_privilege(
    'authenticated',
    'public.security_evaluate_context(uuid,text,text,text,text,text,text,text)',
    'EXECUTE'
  ),
  'authenticated ne peut pas évaluer directement un contexte de sécurité'
);
select ok(
  has_function_privilege(
    'service_role',
    'public.security_evaluate_context(uuid,text,text,text,text,text,text,text)',
    'EXECUTE'
  ),
  'service_role conserve le point d’entrée security_evaluate_context'
);

-- Aucun signal : 0, bande faible.
select is(
  (private.security_risk_score_v25(false,false,false,false,false,false,false,false,false,false)->>'score')::integer,
  0::integer,
  'aucun signal produit un score de 0'
);
select is(
  private.security_risk_score_v25(false,false,false,false,false,false,false,false,false,false)->>'band',
  'low',
  'score 0 appartient à la bande low'
);

-- Appareil inconnu : +30 => medium.
select is(
  (private.security_risk_score_v25(true,false,false,false,false,false,false,false,false,false)->>'score')::integer,
  30::integer,
  'appareil inconnu vaut +30'
);
select is(
  private.security_risk_score_v25(true,false,false,false,false,false,false,false,false,false)->>'band',
  'medium',
  'score 30 appartient à la bande medium'
);

-- Appareil inconnu + région inattendue : 30 + 20 = 50 => high.
select is(
  (private.security_risk_score_v25(true,true,false,false,false,false,false,false,false,false)->>'score')::integer,
  50::integer,
  'appareil inconnu plus région inattendue vaut 50'
);
select is(
  private.security_risk_score_v25(true,true,false,false,false,false,false,false,false,false)->>'band',
  'high',
  'score 50 appartient à la bande high'
);

-- Même avec Mode Voyage, une action sensible garde son poids propre : 30 + 20 + 20 - 15 = 55.
select is(
  (private.security_risk_score_v25(true,true,false,false,false,false,true,false,false,true)->>'score')::integer,
  55::integer,
  'Mode Voyage réduit de 15 sans supprimer le risque sensible'
);
select is(
  private.security_risk_score_v25(true,true,false,false,false,false,true,false,false,true)->>'band',
  'high',
  'score 55 reste high'
);

-- Voyage impossible + récupération récente + changement de facteur : 30 + 25 + 25 = 80.
select is(
  (private.security_risk_score_v25(false,false,true,false,true,true,false,false,false,false)->>'score')::integer,
  80::integer,
  'voyage impossible, récupération et facteur récent valent 80'
);
select is(
  private.security_risk_score_v25(false,false,true,false,true,true,false,false,false,false)->>'band',
  'critical',
  'score 80 appartient à la bande critical'
);

-- Les réductions ne peuvent jamais produire un score négatif.
select is(
  (private.security_risk_score_v25(false,false,false,false,false,false,false,true,true,true)->>'score')::integer,
  0::integer,
  'appareil principal, fiable et voyage correspondant sont bornés à 0'
);

-- Tous les signaux positifs, même avec les réductions, sont bornés à 100.
select is(
  (private.security_risk_score_v25(true,true,true,true,true,true,true,true,true,true)->>'score')::integer,
  100::integer,
  'le score est borné à 100'
);

select is(
  private.security_risk_score_v25(false,false,false,false,false,false,false,false,false,false)->>'model_version',
  'v25.0',
  'le moteur annonce explicitement sa version v25.0'
);

-- Contrat Mode Voyage V25 : les valeurs enregistrées doivent être exactement celles
-- que le moteur peut comparer aux codes pays fournis par l’infrastructure de confiance.
select ok(
  to_regprocedure('private.security_is_iso_country_code_v25(text)') is not null,
  'le validateur ISO du Mode Voyage existe côté serveur'
);
select ok(
  private.security_is_iso_country_code_v25('MA')
  and private.security_is_iso_country_code_v25('ma'),
  'le validateur accepte un vrai code ISO et normalise la casse'
);
select ok(
  not private.security_is_iso_country_code_v25('ZZ')
  and not private.security_is_iso_country_code_v25('France')
  and not private.security_is_iso_country_code_v25(null),
  'les pseudo-codes, noms libres et valeurs nulles sont refusés'
);
select ok(
  has_function_privilege(
    'authenticated',
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)',
    'EXECUTE'
  )
  and not has_function_privilege(
    'anon',
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)',
    'EXECUTE'
  ),
  'le Mode Voyage reste réservé au propriétaire authentifié'
);
select ok(
  (select p.prosecdef
     and array_to_string(p.proconfig,',') like '%search_path=%'
   from pg_proc p
   join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public'
     and p.proname='security_create_travel_plan'
     and pg_get_function_identity_arguments(p.oid)='p_starts_at timestamp with time zone, p_ends_at timestamp with time zone, p_destinations text[], p_multi_country boolean'
   limit 1),
  'le RPC Mode Voyage reste SECURITY DEFINER avec search_path fixe'
);
select ok(
  pg_get_functiondef('public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure)
    like '%INVALID_TRAVEL_COUNTRY_CODE%'
  and pg_get_functiondef('public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure)
    like '%select distinct upper(trim(x)) as code%'
  and pg_get_functiondef('public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure)
    like '%cardinality(v_dest) > 1%'
  and pg_get_functiondef('public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure)
    like '%interval ''7 days''%'
  and pg_get_functiondef('public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure)
    like '%interval ''180 days''%',
  'le RPC normalise, déduplique, dérive multi-pays et borne période/rétention'
);
select ok(
  pg_get_functiondef('public.security_evaluate_context(uuid,text,text,text,text,text,text,text)'::regprocedure)
    like '%upper(trim(d))=v_country%'
  and pg_get_functiondef('public.security_evaluate_context(uuid,text,text,text,text,text,text,text)'::regprocedure)
    like '%if v_impossible_travel then%'
  and pg_get_functiondef('public.security_evaluate_context(uuid,text,text,text,text,text,text,text)'::regprocedure)
    like '%v_force_challenge := true%'
  and pg_get_functiondef('public.security_evaluate_context(uuid,text,text,text,text,text,text,text)'::regprocedure)
    like '%v_travel_match%'
  ,
  'le Mode Voyage correspond aux codes pays sans neutraliser le voyage impossible'
);

select * from finish();
rollback;
