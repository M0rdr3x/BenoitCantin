-- SINJIRA V49: l'ancienne requête A du MEME compte arrive après la requête B.
-- ATTENTION: reproduit le risque, ne sécurise pas la production.
-- Correspond à l'UPSERT sans précondition de version du client existant.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';
INSERT INTO public.sinjira_reader_library(
 user_id,novel_id,last_page,progress_percent,scroll_ratio,updated_at,last_opened_at
) VALUES (
 (SELECT auth.uid()),'10000000-0000-0000-0000-000000000001',12,25,0.2100,
 '2026-11-09T13:00:00Z','2026-11-09T13:00:00Z'
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
 -- Une ancienne sauvegarde arrivée tard a remplacé la progression plus récente.
 -- Le test PASSE lorsque le risque est reproduit; ceci est un échec métier
 -- de cohérence multi-appareils, pas un critère de lancement satisfait.
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE user_id=(SELECT auth.uid()) AND last_page=12
 AND scroll_ratio=0.2100 AND updated_at='2026-11-09T13:00:00Z'::timestamptz;
 IF n<>1 THEN
   RAISE EXCEPTION 'V49: le comportement d écrasement attendu a changé, reviser le contrat';
 END IF;
END $test$;
RESET ROLE;
\echo 'V49-RACE-RISK-REPRODUCED-NO_GO: requete A ancienne a ecrase B plus recente; pas d activation'
