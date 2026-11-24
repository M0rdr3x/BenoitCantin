-- REVIEW ONLY; never execute on production. Candidate intentionally rolls back.
BEGIN;
CREATE TABLE private.report_pdf_budget (
  authenticated boolean PRIMARY KEY,
  window_start timestamptz NOT NULL,
  used integer NOT NULL CHECK (used >= 0 AND used <= 30)
);
ALTER TABLE private.report_pdf_budget ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE private.report_pdf_budget FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, UPDATE ON TABLE private.report_pdf_budget TO service_role;
INSERT INTO private.report_pdf_budget(authenticated, window_start, used)
VALUES (false, date_trunc('minute', clock_timestamp()), 0),
       (true, date_trunc('minute', clock_timestamp()), 0);
CREATE FUNCTION public.consume_report_pdf_budget(p_authenticated boolean)
RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path TO 'pg_catalog'
AS $budget$
DECLARE
  v_start timestamptz;
  v_used integer;
  v_now timestamptz;
  v_limit integer;
BEGIN
  IF p_authenticated IS NULL THEN RETURN false; END IF;
  v_limit := CASE WHEN p_authenticated THEN 30 ELSE 12 END;
  SELECT b.window_start, b.used INTO v_start, v_used
    FROM private.report_pdf_budget b
    WHERE b.authenticated = p_authenticated
    FOR UPDATE NOWAIT;
  IF NOT FOUND THEN RETURN false; END IF;
  v_now := date_trunc('minute', clock_timestamp());
  IF v_now < v_start THEN RETURN false; END IF;
  IF v_now > v_start THEN v_used := 0; END IF;
  IF v_used >= v_limit THEN RETURN false; END IF;
  UPDATE private.report_pdf_budget
     SET window_start = v_now, used = v_used + 1
   WHERE authenticated = p_authenticated;
  RETURN true;
EXCEPTION WHEN lock_not_available THEN
  RETURN false;
END;
$budget$;
REVOKE ALL ON FUNCTION public.consume_report_pdf_budget(boolean) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.consume_report_pdf_budget(boolean) TO service_role;
ROLLBACK;
