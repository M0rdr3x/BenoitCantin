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
  'le scoreur n’utilise pas travel_match comme raison de réduction globale'
);

-- Même dans un appel synthétique contradictoire où unexpected_region et travel_match
-- sont vrais ensemble, le scoreur ne compense rien. Le chemin réel neutralise
-- unexpected_region avant le scoreur lorsqu’un voyage actif correspond.
select is(
  (private.security_risk_score_v25(
    false,true,false,false,false,false,false,false,false,true
  )->>'score')::integer,
  20::integer,
  'travel_match ne réduit pas directement le composant géographique dans le scoreur'
);

select ok(
  not (
    private.security_risk_score_v25(
      false,true,false,false,false,false,false,false,false,true
    )->'reasons' ? 'travel_match'
  ),
  'travel_match reste hors des raisons de score; l’évaluateur porte l’exception géographique'
);

select ok(
  (
    select
      body like '%v_unexpected_region := v_previous.country_code <> v_country and not v_travel_match%'
      and position('if v_impossible_travel then' in body)>0
      and position(
        'v_force_challenge := true;'
        in substring(body from position('if v_impossible_travel then' in body))
      )>0
      and position(
        'v_force_challenge := true;'
        in substring(body from position('if v_impossible_travel then' in body))
      ) < position(
        'end if;'
        in substring(body from position('if v_impossible_travel then' in body))
      )
    from (
      select pg_get_functiondef(
        'public.security_evaluate_context(uuid,text,text,text,text,text,text,text)'::regprocedure
      ) as body
    ) evaluator
  ),
  'le chemin réel neutralise seulement l’anomalie géographique et conserve le challenge de voyage impossible'
);

select * from finish();
rollback;
