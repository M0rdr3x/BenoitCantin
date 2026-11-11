-- SINJIRA V51 — sauvegarde atomique des positions, sans horloge client.
-- À APPLIQUER UNIQUEMENT APRÈS revue humaine, sauvegarde et tests de préproduction.
-- Migration additive. Les marque-pages préexistants conservent revision=0.
-- Les clients anciens avec UPSERT direct échoueront explicitement après retrait
-- des GRANT d'écriture : ordre de déploiement et préavis indispensables.
ALTER TABLE public.sinjira_reader_library
  ADD COLUMN IF NOT EXISTS revision bigint NOT NULL DEFAULT 0;

DO $guard$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='public.sinjira_reader_library'::regclass
      AND conname='sinjira_reader_library_revision_nonnegative'
  ) THEN
    ALTER TABLE public.sinjira_reader_library
      ADD CONSTRAINT sinjira_reader_library_revision_nonnegative
      CHECK (revision >= 0);
  END IF;
END $guard$;

COMMENT ON COLUMN public.sinjira_reader_library.revision
  IS 'Revision monotone serveur par lecteur et roman. CAS obligatoire pour eviter les pertes entre appareils.';

-- SECURITY DEFINER est nécessaire parce que les écritures directes sont
-- retirées à authenticated. auth.uid() est vérifié; l'appelant ne peut fournir
-- ni user_id, ni nom de table, ni identité d'une autre personne.
-- search_path vide + références qualifiées : pas de détournement de fonction.
CREATE OR REPLACE FUNCTION public.sinjira_reader_save_progress_cas(
  p_novel_id uuid,
  p_expected_revision bigint,
  p_last_page integer,
  p_progress_percent integer,
  p_scroll_ratio numeric
)
RETURNS TABLE(
  result_status text,
  result_revision bigint,
  result_page integer,
  result_ratio numeric,
  result_updated_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
DECLARE
  v_user uuid := auth.uid();
  v_row public.sinjira_reader_library%ROWTYPE;
BEGIN
  IF v_user IS NULL THEN
    RAISE EXCEPTION 'authenticated reader required'
      USING ERRCODE = '42501';
  END IF;
  IF p_novel_id IS NULL
     OR p_last_page IS NULL OR p_last_page NOT BETWEEN 1 AND 10000
     OR p_progress_percent IS NULL OR p_progress_percent NOT BETWEEN 0 AND 100
     OR (p_scroll_ratio IS NOT NULL AND
         (p_scroll_ratio < 0 OR p_scroll_ratio > 1))
     OR (p_expected_revision IS NOT NULL AND p_expected_revision < 0) THEN
    RAISE EXCEPTION 'invalid reader progression'
      USING ERRCODE = '22023';
  END IF;

  -- V59: contrôle d'autorisation MÉTIER au sein de la RPC privilégiée.
  -- La validation des droits du PDF par l'Edge Function ne protège pas une
  -- invocation directe de cette fonction SECURITY DEFINER.
  -- Aligner: roman publié + fichier disponible et
  -- (propriétaire, admin, ou droit sur produit actif).
  -- Le même statut "unavailable" est renvoyé pour tout roman inaccessible,
  -- publié ou non / existant ou non, sans révéler son existence.
  IF NOT EXISTS (
    SELECT 1
      FROM public.sinjira_novels AS novel
     WHERE novel.id=p_novel_id
       AND novel.status='published'
       AND novel.file_ready IS TRUE
       AND (
         COALESCE(public.is_sinjira_owner(v_user),false)
         OR COALESCE(public.is_sinjira_admin(v_user),false)
         OR (
           novel.product_id IS NOT NULL
           AND EXISTS (
             SELECT 1
               FROM public.user_entitlements AS entitlement
               JOIN public.products AS product ON product.id=entitlement.product_id
              WHERE entitlement.user_id=v_user
                AND entitlement.product_id=novel.product_id
                AND product.active IS TRUE
           )
         )
       )
  ) THEN
    RETURN QUERY SELECT 'unavailable'::text,NULL::bigint,NULL::integer,
      NULL::numeric,NULL::timestamptz;
    RETURN;
  END IF;

  IF p_expected_revision IS NULL THEN
    -- Première sauvegarde. Deux appareils nouveaux : un seul INSERT réussi.
    -- Ne jamais convertir un conflit initial en UPDATE aveugle.
    INSERT INTO public.sinjira_reader_library AS library
      (user_id,novel_id,last_page,progress_percent,scroll_ratio,
       last_opened_at,updated_at,revision)
    VALUES
      (v_user,p_novel_id,p_last_page,p_progress_percent,p_scroll_ratio,
       pg_catalog.clock_timestamp(),pg_catalog.clock_timestamp(),0)
    ON CONFLICT (user_id,novel_id) DO NOTHING
    RETURNING library.* INTO v_row;
  ELSE
    -- UPDATE réellement atomique sous verrou de ligne PostgreSQL :
    -- la version est testée au moment de l'écriture, pas à l'ouverture.
    UPDATE public.sinjira_reader_library AS library
       SET last_page=p_last_page,
           progress_percent=p_progress_percent,
           scroll_ratio=p_scroll_ratio,
           last_opened_at=pg_catalog.clock_timestamp(),
           updated_at=pg_catalog.clock_timestamp(),
           revision=library.revision+1
     WHERE library.user_id=v_user
       AND library.novel_id=p_novel_id
       AND library.revision=p_expected_revision
    RETURNING library.* INTO v_row;
  END IF;

  IF FOUND THEN
    RETURN QUERY SELECT 'saved'::text,v_row.revision,v_row.last_page,
      v_row.scroll_ratio,v_row.updated_at;
    RETURN;
  END IF;

  -- Conflit : retourner UNIQUEMENT le marque-page du compte courant.
  -- Aucune mise à jour de repli ni reprise aveugle. L'UI devra décider.
  SELECT * INTO v_row FROM public.sinjira_reader_library
   WHERE user_id=v_user AND novel_id=p_novel_id;
  IF FOUND THEN
    RETURN QUERY SELECT 'conflict'::text,v_row.revision,v_row.last_page,
      v_row.scroll_ratio,v_row.updated_at;
  ELSE
    RETURN QUERY SELECT 'conflict'::text,NULL::bigint,NULL::integer,
      NULL::numeric,NULL::timestamptz;
  END IF;
END;
$function$;

REVOKE ALL ON FUNCTION public.sinjira_reader_save_progress_cas(
 uuid,bigint,integer,integer,numeric) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.sinjira_reader_save_progress_cas(
 uuid,bigint,integer,integer,numeric) FROM anon;
GRANT EXECUTE ON FUNCTION public.sinjira_reader_save_progress_cas(
 uuid,bigint,integer,integer,numeric) TO authenticated;

-- Sans ces retraits, les anciens appareils peuvent continuer l'UPSERT direct
-- et contourner la protection CAS. Une migration ne doit PAS être déclarée GO
-- sans test de l'absence de privilège INSERT/UPDATE direct.
REVOKE INSERT,UPDATE ON public.sinjira_reader_library FROM PUBLIC;
REVOKE INSERT,UPDATE ON public.sinjira_reader_library FROM anon;
REVOKE INSERT,UPDATE ON public.sinjira_reader_library FROM authenticated;
