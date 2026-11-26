-- Append after removing only the final ROLLBACK of the candidate, locally.
DO $acl$
BEGIN
  IF has_function_privilege('anon','public.consume_registry_photo_budget(uuid)','EXECUTE')
     OR has_function_privilege('authenticated','public.consume_registry_photo_budget(uuid)','EXECUTE')
     OR NOT has_function_privilege('service_role','public.consume_registry_photo_budget(uuid)','EXECUTE')
     OR has_table_privilege('anon','private.registry_photo_budget','SELECT')
     OR has_table_privilege('authenticated','private.registry_photo_budget','UPDATE')
     OR has_table_privilege('service_role','private.registry_photo_budget','INSERT')
     OR has_table_privilege('service_role','private.registry_photo_budget','DELETE')
  THEN RAISE EXCEPTION 'registry quota ACL failed'; END IF;
END;
$acl$;
SET LOCAL ROLE service_role;
DO $limits$
DECLARE i integer; j integer; u uuid;
BEGIN
  IF public.consume_registry_photo_budget(NULL) OR public.consume_registry_photo_budget('00000000-0000-0000-0000-000000000000')
  THEN RAISE EXCEPTION 'invalid identity accepted'; END IF;
  FOR i IN 1..10 LOOP
    u := ('10000000-0000-4000-8000-' || lpad(i::text,12,'0'))::uuid;
    FOR j IN 1..3 LOOP
      IF NOT public.consume_registry_photo_budget(u) THEN RAISE EXCEPTION 'early refusal'; END IF;
    END LOOP;
    IF public.consume_registry_photo_budget(u) THEN RAISE EXCEPTION 'account limit exceeded'; END IF;
  END LOOP;
  IF public.consume_registry_photo_budget('20000000-0000-4000-8000-000000000001')
  THEN RAISE EXCEPTION 'global limit exceeded'; END IF;
END;
$limits$;
RESET ROLE;
DO $state$
BEGIN
  IF (SELECT count(*) FROM private.registry_photo_budget) <> 1 OR NOT EXISTS (
    SELECT 1 FROM private.registry_photo_budget b WHERE b.used=30
      AND (SELECT count(*) FROM jsonb_each(b.accounts))=10
      AND NOT EXISTS (SELECT 1 FROM jsonb_each_text(b.accounts) e WHERE e.value<>'3')
  ) THEN RAISE EXCEPTION 'incorrect counters or row count'; END IF;
END;
$state$;
UPDATE private.registry_photo_budget SET window_start=clock_timestamp()+interval '60 seconds';
SET LOCAL ROLE service_role;
DO $backward$
BEGIN
  IF public.consume_registry_photo_budget('20000000-0000-4000-8000-000000000001')
  THEN RAISE EXCEPTION 'future clock accepted'; END IF;
END;
$backward$;
RESET ROLE;
UPDATE private.registry_photo_budget SET window_start=clock_timestamp()-interval '61 seconds';
SET LOCAL ROLE service_role;
DO $reset$
BEGIN
  IF NOT public.consume_registry_photo_budget('20000000-0000-4000-8000-000000000001')
  THEN RAISE EXCEPTION 'window did not reset'; END IF;
END;
$reset$;
RESET ROLE;
DO $final$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM private.registry_photo_budget WHERE used=1 AND
    accounts='{"20000000-0000-4000-8000-000000000001":1}'::jsonb)
  THEN RAISE EXCEPTION 'old account state not cleared'; END IF;
END;
$final$;
ROLLBACK;
