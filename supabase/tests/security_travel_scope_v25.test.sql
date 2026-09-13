begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(8);

-- Le Mode Voyage ne doit jamais devenir un bonus de confiance global.
select is(
  (private.security_risk_score_v25(
    true,false,false,false,false,false,true,false,false,true
  )->>'score')::integer,
  50::integer,
  'Mode Voyage ne réduit ni appareil inconnu ni action sensible'
);

select is(
  private.security_risk_score_v25(
    true,false,false,false,false,false,true,false,false,true
  )->>'band',
  'high',
  'les risques non géographiques gardent leur bande high'
);

select is(
  (private.security_risk_score_v25(
    false,false,false,false,true,false,false,false,false,true
  )->>'score')::integer,
  25::integer,
  'Mode Voyage ne réduit pas une récupération récente'
);

select is(
  (private.security_risk_score_v25(
    false,false,true,false,false,false,false,false,false,true
  )->>'score')::integer,
  30::integer,
  'Mode Voyage ne réduit pas le signal voyage impossible'
);

select ok(
  not (
    private.security_risk_score_v25(
      true,false,false,false,false,false,true,false,false,true
    )->'reasons' ? 'travel_match'
  ),
  'travel_match n’est pas journalisé comme réduction sans anomalie géographique'
);

-- Le comportement historique reste disponible uniquement lorsqu’un composant
-- géographique inattendu est effectivement présent dans l’appel déterministe.
select is(
  (private.security_risk_score_v25(
    false,true,false,false,false,false,false,false,false,true
  )->>'score')::integer,
  5::integer,
  'la réduction Mode Voyage reste bornée au composant région/pays inattendu'
);

select ok(
  (
    private.security_risk_score_v25(
      false,true,false,false,false,false,false,false,false,true
    )->'reasons' ? 'travel_match'
  ),
  'travel_match n’apparaît que lorsqu’il compense un signal géographique'
);

select ok(
  pg_get_functiondef(
    'public.security_evaluate_context(uuid,text,text,text,text,text,text,text)'::regprocedure
  ) like '%v_unexpected_region := v_previous.country_code <> v_country and not v_travel_match%'
  and pg_get_functiondef(
    'public.security_evaluate_context(uuid,text,text,text,text,text,text,text)'::regprocedure
  ) like '%if v_impossible_travel then%'
  and pg_get_functiondef(
    'public.security_evaluate_context(uuid,text,text,text,text,text,text,text)'::regprocedure
  ) like '%v_force_challenge := true%',
  'le chemin réel neutralise seulement l’anomalie géographique et conserve le challenge de voyage impossible'
);

select * from finish();
rollback;
