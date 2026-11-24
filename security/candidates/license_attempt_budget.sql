-- CANDIDAT DE REVUE UNIQUEMENT. Ne jamais exécuter en production.
BEGIN;
CREATE TABLE private.license_attempt_budget (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  window_start timestamptz NOT NULL,
  used integer NOT NULL CHECK (used BETWEEN 1 AND 5)
);
ALTER TABLE private.license_attempt_budget ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE private.license_attempt_budget FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE private.license_attempt_budget TO service_role;
CREATE FUNCTION public.consume_license_attempt_budget(p_user_id uuid)
RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path TO 'pg_catalog'
SET lock_timeout TO '250ms'
AS $quota$
DECLARE
  v_now timestamptz := clock_timestamp();
  v_count integer;
BEGIN
  IF p_user_id IS NULL THEN RETURN false; END IF;
  INSERT INTO private.license_attempt_budget AS b (user_id, window_start, used)
    VALUES (p_user_id, v_now, 1)
    ON CONFLICT (user_id) DO UPDATE SET
      used = CASE WHEN b.window_start <= v_now - interval '10 minutes' THEN 1 ELSE b.used + 1 END,
      window_start = CASE WHEN b.window_start <= v_now - interval '10 minutes' THEN v_now ELSE b.window_start END
    WHERE b.window_start <= v_now AND
      (b.window_start <= v_now - interval '10 minutes' OR b.used < 5);
  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count = 1;
EXCEPTION WHEN lock_not_available OR foreign_key_violation THEN
  RETURN false;
END;
$quota$;
REVOKE ALL ON FUNCTION public.consume_license_attempt_budget(uuid) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.consume_license_attempt_budget(uuid) TO service_role;
ROLLBACK;
