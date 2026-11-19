-- P0 SINJIRA : inventaire en lecture seule des liens statiques non prives.
--
-- Executer MANUELLEMENT dans l'editeur SQL Supabase avec une session admin
-- autorisee. Ne pas publier les resultats ni copier des URL dans les logs CI.
-- Cette requete ne modifie aucun droit, objet, compte ou fichier.
--
-- Une URL statique peut etre accessible sans identite sur le CDN, meme lorsque
-- get-document-url refuse le lien apres controle du niveau d'acces.
-- Pour chaque reference signalee, verifier en navigation anonyme si l'origine
-- et les caches CDN exposent le fichier. Retirer toute copie privee exposee.
--
-- IMPORTANT : l'inventaire ne constitue pas un scan de tous les fichiers
-- deja publies sur GitHub Pages, Netlify ou Vercel.
-- Une page HTML peut etre une simple interface publique sans contenu sensible;
-- verifier son HTML et ses API avant de conclure a une fuite. Ne pas migrer une
-- interface HTML comme s'il s'agissait d'un PDF confidentiel.
-- Un PDF restreint doit etre diffuse exclusivement en stockage prive signe.

BEGIN TRANSACTION READ ONLY;

SELECT
  COUNT(*) AS liens_statiques_total,
  COUNT(*) FILTER (
    WHERE d.access_level IS DISTINCT FROM 'public'
       OR p.visibility IS DISTINCT FROM 'public'
  ) AS liens_statiques_sur_documents_restreints,
  COUNT(*) FILTER (
    WHERE d.status = 'approved'
      AND (d.access_level IS DISTINCT FROM 'public'
           OR p.visibility IS DISTINCT FROM 'public')
  ) AS liens_restreints_approuves
FROM public.documents AS d
LEFT JOIN public.projects AS p ON p.id = d.project_id
WHERE NULLIF(btrim(d.external_url), '') IS NOT NULL;

-- Ne publier aucun chemin complet. La categorie aide a la remediation.
SELECT
  d.id AS document_id,
  d.project_id,
  d.status AS document_status,
  d.access_level,
  p.visibility AS project_visibility,
  CASE
    WHEN d.external_url ~* '\.pdf([?#].*)?$' THEN 'PDF_FILE'
    WHEN d.external_url ~* '\.html?([?#].*)?$' THEN 'HTML_ROUTE'
    ELSE 'OTHER_RESOURCE'
  END AS resource_kind,
  CASE
    WHEN p.id IS NULL THEN 'PROJECT_NOT_FOUND'
    WHEN d.access_level IS DISTINCT FROM 'public' THEN 'RESTRICTED_DOCUMENT_STATIC_LINK'
    ELSE 'NONPUBLIC_PROJECT_STATIC_LINK'
  END AS risk_code
FROM public.documents AS d
LEFT JOIN public.projects AS p ON p.id = d.project_id
WHERE NULLIF(btrim(d.external_url), '') IS NOT NULL
  AND (
    d.access_level IS DISTINCT FROM 'public'
    OR p.visibility IS DISTINCT FROM 'public'
  )
ORDER BY d.id
LIMIT 1000;

COMMIT;
