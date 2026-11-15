-- Projet Nova : référence source déployée le 2026-11-03 sous le nom
-- nova_poll_private_aggregates_prelaunch_20261103 (projet gpvivleexywljowcqkru).
-- Ne pas rejouer en production sans revue des différences et de la migration distante.
-- Données individuelles : AUCUNE réponse persistée; seules les sommes par choix sont conservées.
BEGIN;

CREATE TABLE IF NOT EXISTS public.nova_poll_questions (
  poll_version text NOT NULL,
  question_id text NOT NULL,
  ordinal smallint NOT NULL CHECK (ordinal BETWEEN 1 AND 32),
  question_text text NOT NULL CHECK (length(question_text) BETWEEN 10 AND 500),
  PRIMARY KEY (poll_version, question_id),
  UNIQUE (poll_version, ordinal)
);
CREATE TABLE IF NOT EXISTS public.nova_poll_counts (
  poll_version text NOT NULL,
  question_id text NOT NULL,
  option_value smallint NOT NULL CHECK (option_value IN (-2,-1,0,1,2,9)),
  total bigint NOT NULL DEFAULT 0 CHECK (total >= 0),
  PRIMARY KEY (poll_version,question_id,option_value),
  FOREIGN KEY(poll_version,question_id)
    REFERENCES public.nova_poll_questions(poll_version,question_id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS public.nova_poll_receipts (
  poll_version text NOT NULL,
  token_hash text NOT NULL CHECK (token_hash ~ '^[0-9a-f]{64}$'),
  received_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (poll_version,token_hash)
);
CREATE TABLE IF NOT EXISTS public.nova_poll_public_counts (
  poll_version text NOT NULL,
  question_id text NOT NULL,
  option_value smallint NOT NULL CHECK (option_value IN (-2,-1,0,1,2,9)),
  total bigint NOT NULL DEFAULT 0 CHECK (total >= 0),
  PRIMARY KEY(poll_version,question_id,option_value),
  FOREIGN KEY(poll_version,question_id)
    REFERENCES public.nova_poll_questions(poll_version,question_id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS public.nova_poll_publication_state (
  poll_version text PRIMARY KEY,
  published_ballots bigint NOT NULL DEFAULT 0 CHECK (published_ballots >= 0),
  published_at timestamptz
);
COMMENT ON TABLE public.nova_poll_public_counts IS
  'Instantané public par lot; aucun compteur brut temps reel n est exposé.';
COMMENT ON TABLE public.nova_poll_publication_state IS
  'Publication atomique au minimum tous les dix nouveaux bulletins, jamais plus d une fois par six heures.';
COMMENT ON TABLE public.nova_poll_receipts IS
  'Anti-rejeu par jeton aléatoire haché côté serveur; aucun choix politique, compte, courriel ou IP n est conservé. À purger après clôture du sondage. Ne garantit pas une personne unique.';
ALTER TABLE public.nova_poll_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nova_poll_counts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nova_poll_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nova_poll_public_counts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nova_poll_publication_state ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.nova_poll_questions,public.nova_poll_counts,public.nova_poll_receipts,public.nova_poll_public_counts,public.nova_poll_publication_state FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON public.nova_poll_questions,public.nova_poll_counts TO service_role;
GRANT SELECT,INSERT ON public.nova_poll_receipts TO service_role;
GRANT SELECT,INSERT,UPDATE ON public.nova_poll_public_counts,public.nova_poll_publication_state TO service_role;
INSERT INTO public.nova_poll_publication_state(poll_version) VALUES('nova-consultation-v1')
 ON CONFLICT (poll_version) DO NOTHING;

-- Les formulations sont figées dès le premier vote. Une modification exige une nouvelle version.
INSERT INTO public.nova_poll_questions(poll_version,question_id,ordinal,question_text) VALUES
  ('nova-consultation-v1', 'q02', 1, 'Le gouvernement du Québec devrait réduire les restrictions à l’entrée de nouvelles entreprises dans les secteurs actuellement réglementés.'),
  ('nova-consultation-v1', 'q09', 2, 'La majorité des soins de première ligne financés par l’État devrait être fournie par des établissements publics.'),
  ('nova-consultation-v1', 'q17', 3, 'Le gouvernement du Québec devrait augmenter le financement consacré aux logements sociaux, coopératifs et sans but lucratif.'),
  ('nova-consultation-v1', 'q22', 4, 'Le gouvernement du Québec devrait renoncer à une nouvelle norme environnementale si son analyse d’impact prévoit une hausse du coût de biens essentiels.'),
  ('nova-consultation-v1', 'q29', 5, 'Les organismes publics ne devraient pas pouvoir élargir la surveillance numérique sans autorisation judiciaire préalable, sauf dans une urgence prévue par la loi.'),
  ('nova-consultation-v1', 'q33', 6, 'Une pétition atteignant un seuil prévu par la loi devrait pouvoir déclencher un référendum provincial obligatoire.'),
  ('nova-consultation-v1', 'q47', 7, 'Le gouvernement du Québec devrait préparer les conditions permettant la tenue d’un référendum sur la souveraineté.'),
  ('nova-consultation-v1', 'q61', 8, 'Toute décision administrative importante prise à l’aide d’un système d’IA devrait pouvoir être expliquée à la personne concernée.')
ON CONFLICT (poll_version,question_id) DO NOTHING;

CREATE OR REPLACE FUNCTION public.nova_poll_submit(
  p_version text, p_token_hash text, p_answers jsonb
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $fn$
DECLARE
  v_question_count integer;
  v_inserted integer;
  v_total_ballots bigint;
  v_published_ballots bigint;
  v_published_at timestamptz;
BEGIN
  IF p_version <> 'nova-consultation-v1'
     OR p_token_hash IS NULL OR p_token_hash !~ '^[0-9a-f]{64}$'
     OR p_answers IS NULL OR jsonb_typeof(p_answers) <> 'object' THEN
    RAISE EXCEPTION 'Sondage ou bulletin invalide' USING ERRCODE='22023';
  END IF;
  SELECT count(*) INTO v_question_count
    FROM public.nova_poll_questions WHERE poll_version=p_version;
  IF v_question_count <> 8
     OR (SELECT count(*) FROM jsonb_object_keys(p_answers)) <> v_question_count
     OR EXISTS (
       SELECT 1 FROM public.nova_poll_questions q
        WHERE q.poll_version=p_version AND
          (NOT (p_answers ? q.question_id)
           OR p_answers ->> q.question_id NOT IN ('-2','-1','0','1','2','9'))
     )
     OR EXISTS (
       SELECT 1 FROM jsonb_object_keys(p_answers) AS answer(question_id)
       WHERE NOT EXISTS (
         SELECT 1 FROM public.nova_poll_questions q
         WHERE q.poll_version=p_version AND q.question_id=answer.question_id
       )
     ) THEN
    RAISE EXCEPTION 'Questionnaire incomplet ou invalide' USING ERRCODE='22023';
  END IF;

  INSERT INTO public.nova_poll_receipts (poll_version,token_hash)
   VALUES(p_version,p_token_hash) ON CONFLICT DO NOTHING;
  GET DIAGNOSTICS v_inserted=ROW_COUNT;
  IF v_inserted=0 THEN RETURN 'duplicate'; END IF;

  INSERT INTO public.nova_poll_counts(poll_version,question_id,option_value,total)
    SELECT p_version,choice.key,choice.value::smallint,1
    FROM jsonb_each_text(p_answers) AS choice
  ON CONFLICT(poll_version,question_id,option_value)
    DO UPDATE SET total=public.nova_poll_counts.total+1;

  -- La publication par lot atténue l'inférence de réponses individuelles
  -- par comparaison répétée des résultats publics.
  SELECT published_ballots,published_at
   INTO v_published_ballots,v_published_at
   FROM public.nova_poll_publication_state
   WHERE poll_version=p_version FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Publication non configurée' USING ERRCODE='55000'; END IF;
  SELECT count(*) INTO v_total_ballots
    FROM public.nova_poll_receipts WHERE poll_version=p_version;
  IF v_total_ballots >= 10
     AND v_total_ballots - v_published_ballots >= 10
     AND (v_published_at IS NULL OR now() - v_published_at >= interval '6 hours')
     -- Un instantané diffusé ne doit pas révéler une variation de 1 à 4
     -- avis, même si les totaux cumulés dépassent le seuil de confidentialité.
     AND NOT EXISTS (
       SELECT 1 FROM public.nova_poll_counts AS current_count
       LEFT JOIN public.nova_poll_public_counts AS previous_count
         ON previous_count.poll_version=current_count.poll_version
        AND previous_count.question_id=current_count.question_id
        AND previous_count.option_value=current_count.option_value
       WHERE current_count.poll_version=p_version
         AND (
           current_count.total < COALESCE(previous_count.total,0)
           OR (
             current_count.total > COALESCE(previous_count.total,0)
             AND current_count.total - COALESCE(previous_count.total,0) < 5
           )
         )
     ) THEN
    INSERT INTO public.nova_poll_public_counts(poll_version,question_id,option_value,total)
      SELECT poll_version,question_id,option_value,total
      FROM public.nova_poll_counts WHERE poll_version=p_version
      ON CONFLICT(poll_version,question_id,option_value)
      DO UPDATE SET total=EXCLUDED.total;
    UPDATE public.nova_poll_publication_state
      SET published_ballots=v_total_ballots,published_at=now()
      WHERE poll_version=p_version;
  END IF;
  RETURN 'accepted';
END;
$fn$;
REVOKE ALL ON FUNCTION public.nova_poll_submit(text,text,jsonb) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.nova_poll_submit(text,text,jsonb) TO service_role;
COMMIT;

-- Pré-vol : vérifier RLS, les GRANT, la correspondance des 8 textes et le refus d'EXECUTE pour anon/authenticated.
-- Aucune donnée personnelle à mettre dans Git; les secrets Turnstile et HMAC doivent rester côté serveur.
