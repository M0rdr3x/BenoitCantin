-- Le rôle public ne doit pas lire les agrégats privés ni appeler le RPC.
-- Les 10 envois ci-dessous sont intégralement fictifs et locaux.
\set ON_ERROR_STOP on
DO $access$
BEGIN
  IF has_function_privilege('anon','public.nova_poll_submit(text,text,jsonb)','EXECUTE') OR
     has_function_privilege('authenticated','public.nova_poll_submit(text,text,jsonb)','EXECUTE') THEN
    RAISE EXCEPTION 'V7: RPC accessible directement au public';
  END IF;
  IF has_table_privilege('anon','public.nova_poll_receipts','SELECT') OR
     has_table_privilege('authenticated','public.nova_poll_counts','SELECT') OR
     has_table_privilege('anon','public.nova_poll_public_counts','SELECT') THEN
    RAISE EXCEPTION 'V7: RLS ou ACL insuffisante';
  END IF;
  IF (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public' AND c.relname LIKE 'nova_poll_%'
      AND c.relkind='r' AND c.relrowsecurity)<>5 THEN
    RAISE EXCEPTION 'V7: les cinq tables ne sont pas protégées par RLS';
  END IF;
END $access$;
SET ROLE anon;
DO $blocked$
BEGIN
  BEGIN
    PERFORM public.nova_poll_submit(
      'nova-consultation-v1',repeat('a',64),'{}'::jsonb);
    RAISE EXCEPTION 'V7: RPC anonyme acceptée';
  EXCEPTION WHEN insufficient_privilege THEN
    NULL;
  END;
END $blocked$;
RESET ROLE;
SET ROLE service_role;
DO $ballots$
DECLARE i integer; state text;
BEGIN
  FOR i IN 1..10 LOOP
    SELECT public.nova_poll_submit(
       'nova-consultation-v1',
       repeat(lpad(to_hex(i),2,'0'),32),
       '{"q02":-2,"q09":-2,"q17":-2,"q22":-2,"q29":-2,"q33":-2,"q47":-2,"q61":-2}'::jsonb
    ) INTO state;
    IF state<>'accepted' THEN RAISE EXCEPTION 'V7: bulletin fictif refusé %',i; END IF;
  END LOOP;
  SELECT public.nova_poll_submit(
     'nova-consultation-v1',
     repeat(lpad(to_hex(1),2,'0'),32),
     '{"q02":9,"q09":9,"q17":9,"q22":9,"q29":9,"q33":9,"q47":9,"q61":9}'::jsonb
  ) INTO state;
  IF state<>'duplicate' THEN RAISE EXCEPTION 'V7: ancien jeton accepté'; END IF;
  BEGIN
    PERFORM public.nova_poll_submit('nova-consultation-v1',repeat('b',64),'{}'::jsonb);
    RAISE EXCEPTION 'V7: réponses incomplètes acceptées';
  EXCEPTION WHEN SQLSTATE '22023' THEN NULL;
  END;
  BEGIN
    PERFORM public.nova_poll_submit('nova-consultation-v1',repeat('c',64),
      '{"q02":-2,"q09":-2,"q17":-2,"q22":-2,"q29":-2,"q33":-2,"q47":-2,"q99":-2}'::jsonb);
    RAISE EXCEPTION 'V7: questionnaire falsifié accepté';
  EXCEPTION WHEN SQLSTATE '22023' THEN NULL;
  END;
  BEGIN
    PERFORM public.nova_poll_submit('nova-consultation-v1',repeat('d',64),
      '{"q02":8,"q09":-2,"q17":-2,"q22":-2,"q29":-2,"q33":-2,"q47":-2,"q61":-2}'::jsonb);
    RAISE EXCEPTION 'V7: choix interdit accepté';
  EXCEPTION WHEN SQLSTATE '22023' THEN NULL;
  END;
END $ballots$;
RESET ROLE;
DO $verify$
DECLARE n bigint; v bigint;
BEGIN
  SELECT count(*) INTO n FROM public.nova_poll_receipts;
  IF n<>10 THEN RAISE EXCEPTION 'V7: doublon ou bulletin invalide enregistré, %',n; END IF;
  SELECT published_ballots INTO v FROM public.nova_poll_publication_state
  WHERE poll_version='nova-consultation-v1';
  IF v<>10 THEN RAISE EXCEPTION 'V7: premier lot de 10 non publié, %',v; END IF;
  SELECT count(*) INTO n FROM public.nova_poll_public_counts
  WHERE poll_version='nova-consultation-v1' AND option_value=-2 AND total=10;
  IF n<>8 THEN RAISE EXCEPTION 'V7: instantané agrégé incohérent, %',n; END IF;
  SELECT count(*) INTO n FROM public.nova_poll_counts WHERE total<>10;
  IF n<>0 THEN RAISE EXCEPTION 'V7: anti-rejeu non fonctionnel'; END IF;
END $verify$;
\echo 'NOVA-V7-SECURITY-REPLAY-PASS: rôles publics refusés, 10 bulletins fictifs, duplicat rejeté'
