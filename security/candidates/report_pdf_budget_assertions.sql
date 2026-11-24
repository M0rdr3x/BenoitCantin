-- Append to candidate with final ROLLBACK removed, in an isolated LOCAL test only.
DO $acl$
BEGIN
  IF has_function_privilege('anon','public.consume_report_pdf_budget(boolean)','EXECUTE')
     OR has_function_privilege('authenticated','public.consume_report_pdf_budget(boolean)','EXECUTE')
     OR has_table_privilege('anon','private.report_pdf_budget','SELECT')
     OR has_table_privilege('authenticated','private.report_pdf_budget','UPDATE')
     OR NOT has_function_privilege('service_role','public.consume_report_pdf_budget(boolean)','EXECUTE')
  THEN RAISE EXCEPTION 'quota ACL failed'; END IF;
END;
$acl$;
-- Keep all assertions within a stable window. Start at current minute and
-- fail rather than silently accept unexpected boundary timing.
SET LOCAL ROLE service_role;
DO $quota$
DECLARE i integer;
BEGIN
  IF public.consume_report_pdf_budget(NULL) THEN RAISE EXCEPTION 'null accepted'; END IF;
  FOR i IN 1..12 LOOP
    IF NOT public.consume_report_pdf_budget(false) THEN RAISE EXCEPTION 'guest early refusal'; END IF;
  END LOOP;
  IF public.consume_report_pdf_budget(false) THEN RAISE EXCEPTION 'guest quota exceeded'; END IF;
  FOR i IN 1..30 LOOP
    IF NOT public.consume_report_pdf_budget(true) THEN RAISE EXCEPTION 'account early refusal'; END IF;
  END LOOP;
  IF public.consume_report_pdf_budget(true) THEN RAISE EXCEPTION 'account quota exceeded'; END IF;
END;
$quota$;
RESET ROLE;
UPDATE private.report_pdf_budget SET window_start = date_trunc('minute', clock_timestamp()) - interval '1 minute';
SET LOCAL ROLE service_role;
DO $reset$
BEGIN
  IF NOT public.consume_report_pdf_budget(false) OR NOT public.consume_report_pdf_budget(true)
  THEN RAISE EXCEPTION 'quota did not reset'; END IF;
END;
$reset$;
RESET ROLE;
DO $counts$
BEGIN
  IF (SELECT count(*) FROM private.report_pdf_budget) <> 2
     OR EXISTS (SELECT 1 FROM private.report_pdf_budget WHERE used <> 1)
  THEN RAISE EXCEPTION 'unexpected quota state'; END IF;
END;
$counts$;
ROLLBACK;
