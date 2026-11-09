-- SINJIRA V49: une sauvegarde plus récente B du MEME compte arrive la première.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';
INSERT INTO public.sinjira_reader_library(
 user_id,novel_id,last_page,progress_percent,scroll_ratio,updated_at,last_opened_at
) VALUES (
 (SELECT auth.uid()),'10000000-0000-0000-0000-000000000001',31,60,0.8123,
 '2026-11-09T13:05:00Z','2026-11-09T13:05:00Z'
)
ON CONFLICT (user_id,novel_id) DO UPDATE SET
 last_page=excluded.last_page,
 progress_percent=excluded.progress_percent,
 scroll_ratio=excluded.scroll_ratio,
 updated_at=excluded.updated_at,
 last_opened_at=excluded.last_opened_at;
DO $test$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE user_id=(SELECT auth.uid()) AND
 last_page=31 AND scroll_ratio=0.8123 AND
 updated_at='2026-11-09T13:05:00Z'::timestamptz;
 IF n<>1 THEN RAISE EXCEPTION 'V49: sauvegarde B plus récente absente'; END IF;
END $test$;
RESET ROLE;
\echo 'V49-DEVICE-B-FRESH-PASS: position B 31/0.8123 enregistrée à 13:05'
