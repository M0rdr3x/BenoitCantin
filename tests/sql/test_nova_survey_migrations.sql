-- Contrats Nova SQL, PostgreSQL local jetable, aucun Supabase distant.
\set ON_ERROR_STOP on
DO $setup$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='anon') THEN CREATE ROLE anon NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='service_role') THEN CREATE ROLE service_role NOLOGIN; END IF;
END
$setup$;
\ir ../../supabase/candidate-migrations/20261019170000_nova_adult_opinion_survey_v1.sql
\ir ../../supabase/candidate-migrations/20261019190000_nova_foundations_40_survey_v1.sql

-- Les rôles web ne voient aucun résultat et ne peuvent pas invoquer les RPC.
DO $guards$
DECLARE tab text; fn text; rol text;
BEGIN
  FOREACH tab IN ARRAY ARRAY['nova_survey_participants','nova_survey_aggregate_counts',
                             'nova_consultation40_participants','nova_consultation40_aggregate_counts'] LOOP
    IF NOT EXISTS (
      SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public' AND c.relname=tab AND c.relrowsecurity
    ) THEN RAISE EXCEPTION 'RLS_DISABLED: %',tab; END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_policies WHERE schemaname='public' AND tablename=tab)
    THEN RAISE EXCEPTION 'UNAPPROVED_POLICY: %',tab; END IF;
    FOREACH rol IN ARRAY ARRAY['anon','authenticated'] LOOP
      IF pg_catalog.has_table_privilege(rol,'public.'||tab,'SELECT,INSERT,UPDATE,DELETE')
      THEN RAISE EXCEPTION 'PUBLIC_TABLE_PRIVILEGE: % %',rol,tab; END IF;
    END LOOP;
  END LOOP;
  FOREACH fn IN ARRAY ARRAY['public.nova_survey_submit_v1(text,text,jsonb)',
                             'public.nova_consultation40_submit_v1(text,text,jsonb)'] LOOP
    FOREACH rol IN ARRAY ARRAY['anon','authenticated'] LOOP
      IF pg_catalog.has_function_privilege(rol,fn,'EXECUTE')
      THEN RAISE EXCEPTION 'PUBLIC_RPC_EXECUTE: % %',rol,fn; END IF;
    END LOOP;
    IF NOT pg_catalog.has_function_privilege('service_role',fn,'EXECUTE')
    THEN RAISE EXCEPTION 'SERVICE_ROLE_DENIED: %',fn; END IF;
  END LOOP;
END
$guards$;

SET ROLE service_role;
DO $cases$
DECLARE a40 jsonb; a64 jsonb;
BEGIN
  SELECT pg_catalog.jsonb_object_agg('q'||pg_catalog.lpad(i::text,2,'0'),
    CASE WHEN i=1 THEN 'sans_opinion' ELSE 'pour' END)
    INTO a40 FROM pg_catalog.generate_series(1,40) g(i);
  SELECT pg_catalog.jsonb_object_agg('q'||pg_catalog.lpad(i::text,2,'0'),
    CASE WHEN i=64 THEN 'skip' ELSE '-3' END)
    INTO a64 FROM pg_catalog.generate_series(1,64) g(i);

  -- Invalidité, absence de réponse et version inconnue : transaction refusée.
  BEGIN
    PERFORM public.nova_consultation40_submit_v1('nova-orientations-40-v1',pg_catalog.repeat('b',64),a40-'q40');
    RAISE EXCEPTION 'PARTIAL_40_ACCEPTED';
  EXCEPTION WHEN invalid_parameter_value THEN
    IF SQLERRM NOT LIKE '%INVALID_SURVEY_ANSWERS%' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.nova_consultation40_submit_v1('nova-orientations-40-v1',pg_catalog.repeat('b',64),
      pg_catalog.jsonb_set(a40,'{q15}','"autre"'::jsonb));
    RAISE EXCEPTION 'BAD_VALUE_40_ACCEPTED';
  EXCEPTION WHEN invalid_parameter_value THEN
    IF SQLERRM NOT LIKE '%INVALID_SURVEY_ANSWERS%' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.nova_consultation40_submit_v1('nova-orientations-40-v1',pg_catalog.repeat('b',64),
      pg_catalog.jsonb_set(a40,'{q15}','null'::jsonb));
    RAISE EXCEPTION 'JSON_NULL_40_ACCEPTED';
  EXCEPTION WHEN invalid_parameter_value THEN
    IF SQLERRM NOT LIKE '%INVALID_SURVEY_ANSWERS%' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.nova_consultation40_submit_v1('wrong-version',pg_catalog.repeat('b',64),a40);
    RAISE EXCEPTION 'WRONG_VERSION_40_ACCEPTED';
  EXCEPTION WHEN invalid_parameter_value THEN
    IF SQLERRM NOT LIKE '%INVALID_SURVEY_PAYLOAD%' THEN RAISE; END IF;
  END;
  IF public.nova_consultation40_submit_v1('nova-orientations-40-v1',pg_catalog.repeat('a',64),a40)<>'RECORDED'
  THEN RAISE EXCEPTION 'VALID_40_REJECTED'; END IF;
  BEGIN
    PERFORM public.nova_consultation40_submit_v1('nova-orientations-40-v1',pg_catalog.repeat('a',64),a40);
    RAISE EXCEPTION 'DUPLICATE_40_ACCEPTED';
  EXCEPTION WHEN unique_violation THEN
    IF SQLERRM NOT LIKE '%ALREADY_SUBMITTED%' THEN RAISE; END IF;
  END;

  BEGIN
    PERFORM public.nova_survey_submit_v1('nova-consultation-64-v1',pg_catalog.repeat('b',64),a64-'q02');
    RAISE EXCEPTION 'PARTIAL_64_ACCEPTED';
  EXCEPTION WHEN invalid_parameter_value THEN
    IF SQLERRM NOT LIKE '%INVALID_SURVEY_ANSWERS%' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.nova_survey_submit_v1('nova-consultation-64-v1',pg_catalog.repeat('b',64),
      pg_catalog.jsonb_set(a64,'{q08}','"invalid"'::jsonb));
    RAISE EXCEPTION 'BAD_VALUE_64_ACCEPTED';
  EXCEPTION WHEN invalid_parameter_value THEN
    IF SQLERRM NOT LIKE '%INVALID_SURVEY_ANSWERS%' THEN RAISE; END IF;
  END;
  -- La représentation JSON compte : 1 (nombre) n'est pas « 1 » (texte).
  BEGIN
    PERFORM public.nova_survey_submit_v1('nova-consultation-64-v1',pg_catalog.repeat('b',64),
      pg_catalog.jsonb_set(a64,'{q08}','1'::jsonb));
    RAISE EXCEPTION 'JSON_NUMBER_64_ACCEPTED';
  EXCEPTION WHEN invalid_parameter_value THEN
    IF SQLERRM NOT LIKE '%INVALID_SURVEY_ANSWERS%' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.nova_survey_submit_v1('nova-consultation-64-v1',pg_catalog.repeat('b',64),
      pg_catalog.jsonb_set(a64,'{q08}','null'::jsonb));
    RAISE EXCEPTION 'JSON_NULL_64_ACCEPTED';
  EXCEPTION WHEN invalid_parameter_value THEN
    IF SQLERRM NOT LIKE '%INVALID_SURVEY_ANSWERS%' THEN RAISE; END IF;
  END;
  IF public.nova_survey_submit_v1('nova-consultation-64-v1',pg_catalog.repeat('a',64),a64)<>'RECORDED'
  THEN RAISE EXCEPTION 'VALID_64_REJECTED'; END IF;
  BEGIN
    PERFORM public.nova_survey_submit_v1('nova-consultation-64-v1',pg_catalog.repeat('a',64),a64);
    RAISE EXCEPTION 'DUPLICATE_64_ACCEPTED';
  EXCEPTION WHEN unique_violation THEN
    IF SQLERRM NOT LIKE '%ALREADY_SUBMITTED%' THEN RAISE; END IF;
  END;
END
$cases$;
RESET ROLE;

DO $counts$
BEGIN
  IF (SELECT count(*) FROM public.nova_consultation40_participants)<>1
     OR (SELECT count(*) FROM public.nova_consultation40_aggregate_counts)<>40
     OR (SELECT sum(answer_count) FROM public.nova_consultation40_aggregate_counts)<>40
     OR (SELECT answer_count FROM public.nova_consultation40_aggregate_counts
         WHERE question_id='q01' AND response_value='sans_opinion')<>1
  THEN RAISE EXCEPTION 'WRONG_TOTALS_40'; END IF;
  IF (SELECT count(*) FROM public.nova_survey_participants)<>1
     OR (SELECT count(*) FROM public.nova_survey_aggregate_counts)<>64
     OR (SELECT sum(answer_count) FROM public.nova_survey_aggregate_counts)<>64
     OR (SELECT answer_count FROM public.nova_survey_aggregate_counts
         WHERE question_id='q64' AND response_value='skip')<>1
  THEN RAISE EXCEPTION 'WRONG_TOTALS_64'; END IF;
END
$counts$;
\echo 'OK: Nova 40/64, refus SQL, anti-doublons, RLS, permissions et agrégats sur PostgreSQL local'
