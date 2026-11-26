-- CANDIDAT NO-GO : test local exclusivement, hors migrations.
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '10s';
CREATE TABLE private.registry_photo_budget (
  singleton boolean PRIMARY KEY CHECK (singleton IS TRUE),
  window_start timestamptz NOT NULL,
  used integer NOT NULL CHECK (used BETWEEN 0 AND 30),
  accounts jsonb NOT NULL CHECK (jsonb_typeof(accounts) = 'object' AND octet_length(accounts::text) <= 4096)
);
ALTER TABLE private.registry_photo_budget ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE private.registry_photo_budget FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, UPDATE ON TABLE private.registry_photo_budget TO service_role;
INSERT INTO private.registry_photo_budget(singleton,window_start,used,accounts)
VALUES (true,clock_timestamp(),0,'{}'::jsonb);

CREATE FUNCTION public.consume_registry_photo_budget(p_user_id uuid)
RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path TO 'pg_catalog'
AS $budget$
DECLARE
  v_start timestamptz;
  v_now timestamptz;
  v_used integer;
  v_accounts jsonb;
  v_key text;
  v_count integer;
BEGIN
  IF p_user_id IS NULL OR p_user_id = '00000000-0000-0000-0000-000000000000'::uuid THEN RETURN false; END IF;
  SELECT b.window_start,b.used,b.accounts INTO v_start,v_used,v_accounts
    FROM private.registry_photo_budget b WHERE b.singleton IS TRUE
    FOR UPDATE NOWAIT;
  IF NOT FOUND THEN RETURN false; END IF;
  v_now := clock_timestamp();
  IF v_now < v_start THEN RETURN false; END IF;
  IF v_now >= v_start + interval '60 seconds' THEN
    v_start := v_now;
    v_used := 0;
    v_accounts := '{}'::jsonb;
  END IF;
  IF v_used >= 30 THEN RETURN false; END IF;
  v_key := p_user_id::text;
  IF v_accounts ? v_key THEN
    IF jsonb_typeof(v_accounts->v_key) <> 'number' OR (v_accounts->>v_key) !~ '^[1-3]$' THEN RETURN false; END IF;
    v_count := (v_accounts->>v_key)::integer;
  ELSE
    v_count := 0;
  END IF;
  IF v_count >= 3 THEN RETURN false; END IF;
  UPDATE private.registry_photo_budget
    SET window_start=v_start, used=v_used+1,
        accounts=jsonb_set(v_accounts,ARRAY[v_key],to_jsonb(v_count+1),true)
    WHERE singleton IS TRUE;
  RETURN FOUND;
EXCEPTION WHEN lock_not_available THEN
  RETURN false;
END;
$budget$;
REVOKE ALL ON FUNCTION public.consume_registry_photo_budget(uuid) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.consume_registry_photo_budget(uuid) TO service_role;
ROLLBACK;
