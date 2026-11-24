-- Run only appended to the local candidate transaction.
INSERT INTO auth.users(id, email, aud, role, raw_user_meta_data, created_at, updated_at)
VALUES ('aa000000-0000-4000-8000-000000000001','license-quota-a@example.invalid','authenticated','authenticated',
        '{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"female"}'::jsonb,now(),now()),
       ('aa000000-0000-4000-8000-000000000002','license-quota-b@example.invalid','authenticated','authenticated',
        '{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"female"}'::jsonb,now(),now());
DO $acl$
BEGIN
  IF has_function_privilege('anon','public.consume_license_attempt_budget(uuid)','EXECUTE')
  OR has_function_privilege('authenticated','public.consume_license_attempt_budget(uuid)','EXECUTE')
  OR has_table_privilege('anon','private.license_attempt_budget','SELECT')
  OR has_table_privilege('authenticated','private.license_attempt_budget','INSERT')
  OR has_table_privilege('anon','private.license_global_attempt_budget','SELECT')
  OR has_table_privilege('authenticated','private.license_global_attempt_budget','UPDATE')
  OR NOT has_function_privilege('service_role','public.consume_license_attempt_budget(uuid)','EXECUTE')
  THEN RAISE EXCEPTION 'unexpected ACL'; END IF;
END;
$acl$;
SET LOCAL ROLE service_role;
DO $test$
DECLARE a uuid := 'aa000000-0000-4000-8000-000000000001';
        b uuid := 'aa000000-0000-4000-8000-000000000002';
        i integer;
BEGIN
  IF public.consume_license_attempt_budget(NULL) THEN RAISE EXCEPTION 'null account accepted'; END IF;
  FOR i IN 1..5 LOOP
    IF NOT public.consume_license_attempt_budget(a) THEN RAISE EXCEPTION 'early refusal'; END IF;
  END LOOP;
  IF public.consume_license_attempt_budget(a) THEN RAISE EXCEPTION 'quota exceeded'; END IF;
  IF NOT public.consume_license_attempt_budget(b) THEN RAISE EXCEPTION 'second account blocked'; END IF;
END;
$test$;
RESET ROLE;
UPDATE private.license_attempt_budget SET window_start=clock_timestamp()-interval '11 minutes'
WHERE user_id='aa000000-0000-4000-8000-000000000001';
SET LOCAL ROLE service_role;
DO $reset$
BEGIN
  IF NOT public.consume_license_attempt_budget('aa000000-0000-4000-8000-000000000001')
  THEN RAISE EXCEPTION 'window did not reset'; END IF;
END;
$reset$;
RESET ROLE;
DO $state$
BEGIN
  IF (SELECT count(*) FROM private.license_attempt_budget)<>2
    OR EXISTS(SELECT 1 FROM private.license_attempt_budget WHERE used<>1)
  THEN RAISE EXCEPTION 'invalid quota counters'; END IF;
END;
$state$;
-- Seed the collective budget just below its ceiling. No real accounts,
-- codes, external load, or disabling signup triggers are required.
UPDATE private.license_global_attempt_budget SET used=59, window_start=clock_timestamp();
SET LOCAL ROLE service_role;
DO $global$
BEGIN
  IF NOT public.consume_license_attempt_budget('aa000000-0000-4000-8000-000000000001')
  THEN RAISE EXCEPTION 'last collective admission refused'; END IF;
  IF public.consume_license_attempt_budget('aa000000-0000-4000-8000-000000000002')
  THEN RAISE EXCEPTION 'second account bypassed global quota'; END IF;
END;
$global$;
RESET ROLE;
DO $global_state$
BEGIN
  IF (SELECT used FROM private.license_global_attempt_budget WHERE singleton) <> 60
    OR (SELECT used FROM private.license_attempt_budget WHERE user_id='aa000000-0000-4000-8000-000000000002') <> 2
  THEN RAISE EXCEPTION 'collective denial did not retain account charge'; END IF;
END;
$global_state$;
UPDATE private.license_global_attempt_budget SET window_start=clock_timestamp()-interval '2 minutes';
SET LOCAL ROLE service_role;
DO $global_reset$
BEGIN
  IF NOT public.consume_license_attempt_budget('aa000000-0000-4000-8000-000000000002')
  THEN RAISE EXCEPTION 'global window did not reset'; END IF;
END;
$global_reset$;
RESET ROLE;
DO $global_final$
BEGIN
  IF (SELECT count(*) FROM private.license_global_attempt_budget) <> 1
    OR (SELECT used FROM private.license_global_attempt_budget WHERE singleton) <> 1
  THEN RAISE EXCEPTION 'invalid global counter state'; END IF;
END;
$global_final$;
ROLLBACK;
