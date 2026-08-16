-- SINJIRA™ V24.4.12 — identité personnage : verrouillage RLS exact
-- Un utilisateur ne peut publier/commenter/aimer qu'avec le character_id de SON profil personnage actif.
-- Le même invariant est vérifié à l'insertion et à la mise à jour.

-- Publications personnage
DROP POLICY IF EXISTS char_posts_insert ON public.social_character_posts;
CREATE POLICY char_posts_insert ON public.social_character_posts
FOR INSERT TO authenticated
WITH CHECK (
  (SELECT auth.uid()) = user_id
  AND public.sinjira_age_band((SELECT auth.uid())) IN ('youth','adult')
  AND public.has_accepted_community_rules((SELECT auth.uid()))
  AND NOT public.social_is_suspended((SELECT auth.uid()))
  AND EXISTS (
    SELECT 1
    FROM public.character_social_profiles c
    WHERE c.character_id = social_character_posts.character_id
      AND c.user_id = (SELECT auth.uid())
      AND lower(coalesce(c.status,'')) <> 'archived'
  )
);

DROP POLICY IF EXISTS char_posts_update ON public.social_character_posts;
CREATE POLICY char_posts_update ON public.social_character_posts
FOR UPDATE TO authenticated
USING ((SELECT auth.uid()) = user_id)
WITH CHECK (
  (SELECT auth.uid()) = user_id
  AND EXISTS (
    SELECT 1
    FROM public.character_social_profiles c
    WHERE c.character_id = social_character_posts.character_id
      AND c.user_id = (SELECT auth.uid())
      AND lower(coalesce(c.status,'')) <> 'archived'
  )
);

DROP POLICY IF EXISTS char_posts_delete ON public.social_character_posts;
CREATE POLICY char_posts_delete ON public.social_character_posts
FOR DELETE TO authenticated
USING ((SELECT auth.uid()) = user_id);

-- Commentaires personnage
DROP POLICY IF EXISTS char_comments_insert ON public.social_character_comments;
CREATE POLICY char_comments_insert ON public.social_character_comments
FOR INSERT TO authenticated
WITH CHECK (
  (SELECT auth.uid()) = user_id
  AND public.has_accepted_community_rules((SELECT auth.uid()))
  AND NOT public.social_is_suspended((SELECT auth.uid()))
  AND EXISTS (
    SELECT 1
    FROM public.character_social_profiles c
    WHERE c.character_id = social_character_comments.character_id
      AND c.user_id = (SELECT auth.uid())
      AND lower(coalesce(c.status,'')) <> 'archived'
  )
  AND EXISTS (
    SELECT 1 FROM public.social_character_posts p
    WHERE p.id = social_character_comments.post_id
      AND public.sinjira_can_social_interact((SELECT auth.uid()),p.user_id)
  )
);

DROP POLICY IF EXISTS char_comments_update ON public.social_character_comments;
CREATE POLICY char_comments_update ON public.social_character_comments
FOR UPDATE TO authenticated
USING ((SELECT auth.uid()) = user_id)
WITH CHECK (
  (SELECT auth.uid()) = user_id
  AND EXISTS (
    SELECT 1
    FROM public.character_social_profiles c
    WHERE c.character_id = social_character_comments.character_id
      AND c.user_id = (SELECT auth.uid())
      AND lower(coalesce(c.status,'')) <> 'archived'
  )
);

DROP POLICY IF EXISTS char_comments_delete ON public.social_character_comments;
CREATE POLICY char_comments_delete ON public.social_character_comments
FOR DELETE TO authenticated
USING ((SELECT auth.uid()) = user_id);

-- Likes personnage
DROP POLICY IF EXISTS char_likes_insert ON public.social_character_likes;
CREATE POLICY char_likes_insert ON public.social_character_likes
FOR INSERT TO authenticated
WITH CHECK (
  (SELECT auth.uid()) = user_id
  AND public.has_accepted_community_rules((SELECT auth.uid()))
  AND NOT public.social_is_suspended((SELECT auth.uid()))
  AND EXISTS (
    SELECT 1
    FROM public.character_social_profiles c
    WHERE c.character_id = social_character_likes.character_id
      AND c.user_id = (SELECT auth.uid())
      AND lower(coalesce(c.status,'')) <> 'archived'
  )
  AND EXISTS (
    SELECT 1 FROM public.social_character_posts p
    WHERE p.id = social_character_likes.post_id
      AND public.sinjira_can_social_interact((SELECT auth.uid()),p.user_id)
  )
);

DROP POLICY IF EXISTS char_likes_delete ON public.social_character_likes;
CREATE POLICY char_likes_delete ON public.social_character_likes
FOR DELETE TO authenticated
USING ((SELECT auth.uid()) = user_id);

-- Lecture optimisée de ces surfaces : même règle de cohorte, auth.uid() évalué une seule fois.
DROP POLICY IF EXISTS char_posts_read ON public.social_character_posts;
CREATE POLICY char_posts_read ON public.social_character_posts
FOR SELECT TO authenticated
USING (
  public.sinjira_can_social_interact((SELECT auth.uid()),user_id)
  AND NOT public.social_is_blocked((SELECT auth.uid()),user_id)
);

DROP POLICY IF EXISTS char_comments_read ON public.social_character_comments;
CREATE POLICY char_comments_read ON public.social_character_comments
FOR SELECT TO authenticated
USING (
  public.sinjira_can_social_interact((SELECT auth.uid()),user_id)
  AND NOT public.social_is_blocked((SELECT auth.uid()),user_id)
  AND EXISTS (
    SELECT 1 FROM public.social_character_posts p
    WHERE p.id=social_character_comments.post_id
      AND public.sinjira_can_social_interact((SELECT auth.uid()),p.user_id)
  )
);

DROP POLICY IF EXISTS char_likes_read ON public.social_character_likes;
CREATE POLICY char_likes_read ON public.social_character_likes
FOR SELECT TO authenticated
USING (
  public.sinjira_can_social_interact((SELECT auth.uid()),user_id)
  AND EXISTS (
    SELECT 1 FROM public.social_character_posts p
    WHERE p.id=social_character_likes.post_id
      AND public.sinjira_can_social_interact((SELECT auth.uid()),p.user_id)
  )
);
