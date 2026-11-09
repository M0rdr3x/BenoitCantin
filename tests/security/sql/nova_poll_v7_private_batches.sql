-- Deux scénarios dans le même PostgreSQL JETABLE : seuil de six heures et
-- risque de reidentification par différences 9/1, puis lot compatible 9/5.
\set ON_ERROR_STOP on
SET ROLE service_role;
DO $rate$
DECLARE i integer; v bigint; state text;
BEGIN
  FOR i IN 11..20 LOOP
    SELECT public.nova_poll_submit(
      'nova-consultation-v1',
      repeat(lpad(to_hex(i),2,'0'),32),
      '{"q02":-2,"q09":-2,"q17":-2,"q22":-2,"q29":-2,"q33":-2,"q47":-2,"q61":-2}'::jsonb
    ) INTO state;
    IF state<>'accepted' THEN RAISE EXCEPTION 'V7: lot horaire refusé'; END IF;
  END LOOP;
  SELECT published_ballots INTO v FROM public.nova_poll_publication_state
    WHERE poll_version='nova-consultation-v1';
  IF v<>10 THEN RAISE EXCEPTION 'V7: lot publié sans délai de six heures'; END IF;
END $rate$;
RESET ROLE;
-- Simulation d'écoulement du temps, seulement dans la fixture éphémère.
UPDATE public.nova_poll_publication_state SET published_at=now()-interval '7 hours'
 WHERE poll_version='nova-consultation-v1';
SET ROLE service_role;
DO $release$
DECLARE state text;
BEGIN
  SELECT public.nova_poll_submit('nova-consultation-v1',
    repeat(lpad(to_hex(21),2,'0'),32),
    '{"q02":-2,"q09":-2,"q17":-2,"q22":-2,"q29":-2,"q33":-2,"q47":-2,"q61":-2}'::jsonb
  ) INTO state;
  IF state<>'accepted' THEN RAISE EXCEPTION 'V7: second lot horaire refusé'; END IF;
END $release$;
RESET ROLE;
DO $check$
BEGIN
 IF (SELECT published_ballots FROM public.nova_poll_publication_state
   WHERE poll_version='nova-consultation-v1')<>21 THEN
   RAISE EXCEPTION 'V7: lot après six heures non publié';
 END IF;
END $check$;
-- Réinitialisation sûre UNIQUEMENT de la base fictive, aucune donnée réelle.
TRUNCATE public.nova_poll_counts, public.nova_poll_receipts, public.nova_poll_public_counts;
UPDATE public.nova_poll_publication_state
 SET published_ballots=0,published_at=NULL WHERE poll_version='nova-consultation-v1';
SET ROLE service_role;
DO $first$
DECLARE i integer; state text;
BEGIN
 FOR i IN 1..10 LOOP
  SELECT public.nova_poll_submit(
   'nova-consultation-v1',repeat(lpad(to_hex(i),2,'0'),32),
   '{"q02":-2,"q09":-2,"q17":-2,"q22":-2,"q29":-2,"q33":-2,"q47":-2,"q61":-2}'::jsonb
  ) INTO state;
  IF state<>'accepted' THEN RAISE EXCEPTION 'V7: premier lot fictif rejeté'; END IF;
 END LOOP;
END $first$;
RESET ROLE;
UPDATE public.nova_poll_publication_state SET published_at=now()-interval '7 hours'
 WHERE poll_version='nova-consultation-v1';
SET ROLE service_role;
DO $small$
DECLARE i integer; state text; choice smallint; answers jsonb; v bigint;
BEGIN
 FOR i IN 11..20 LOOP
  choice=CASE WHEN i=20 THEN -1 ELSE -2 END;
  answers=jsonb_build_object('q02',choice,'q09',choice,'q17',choice,
    'q22',choice,'q29',choice,'q33',choice,'q47',choice,'q61',choice);
  SELECT public.nova_poll_submit(
   'nova-consultation-v1',repeat(lpad(to_hex(i),2,'0'),32),answers
  ) INTO state;
  IF state<>'accepted' THEN RAISE EXCEPTION 'V7: bulletin fictif -1 refusé'; END IF;
 END LOOP;
 SELECT published_ballots INTO v FROM public.nova_poll_publication_state
  WHERE poll_version='nova-consultation-v1';
 IF v<>10 THEN RAISE EXCEPTION 'V7: le lot 9/1 est divulgué (%).',v; END IF;
END $small$;
RESET ROLE;
SET ROLE service_role;
DO $safe$
DECLARE i integer; state text; v bigint;
BEGIN
 FOR i IN 21..24 LOOP
  SELECT public.nova_poll_submit(
   'nova-consultation-v1',repeat(lpad(to_hex(i),2,'0'),32),
   '{"q02":-1,"q09":-1,"q17":-1,"q22":-1,"q29":-1,"q33":-1,"q47":-1,"q61":-1}'::jsonb
  ) INTO state;
  IF state<>'accepted' THEN RAISE EXCEPTION 'V7: réponses supplémentaires rejetées'; END IF;
 END LOOP;
 SELECT published_ballots INTO v FROM public.nova_poll_publication_state
 WHERE poll_version='nova-consultation-v1';
 IF v<>24 THEN
  RAISE EXCEPTION 'V7: le lot cumulatif 9/5 n est pas publié (%).',v;
 END IF;
END $safe$;
RESET ROLE;
DO $final$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM public.nova_poll_public_counts
   WHERE poll_version='nova-consultation-v1' AND option_value=-2 AND total=19;
  IF n<>8 THEN RAISE EXCEPTION 'V7: 19 réponses fictives ne figurent pas dans le lot'; END IF;
  SELECT count(*) INTO n FROM public.nova_poll_public_counts
   WHERE poll_version='nova-consultation-v1' AND option_value=-1 AND total=5;
  IF n<>8 THEN RAISE EXCEPTION 'V7: la cellule de cinq réponses n'est pas présente'; END IF;
  IF (SELECT count(*) FROM public.nova_poll_receipts)<>24 THEN
   RAISE EXCEPTION 'V7: compteurs bruts divergents';
  END IF;
END $final$;
\echo 'NOVA-V7-PRIVATE-BATCHES-PASS: délai 6h, 9/1 masqué, 9/5 après 24 bulletins fictifs'
