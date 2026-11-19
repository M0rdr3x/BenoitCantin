-- P0 SINJIRA : inventaire en lecture seule des liens statiques non prives.
--
-- Executez MANUELLEMENT dans l'editeur SQL Supabase, avec une session admin
-- autorisee. Ne publiez pas les resultats et ne les copiez pas dans les logs CI.
-- Cette requete ne modifie aucun droit, objet ou fichier.
--
-- Un document reserve qui pointe vers une URL statique peut rester consultable
-- sans identite sur le CDN, meme si get-document-url refuse le lien.
-- Pour chaque ligne ci-dessous : verifier l'URL avec une session anonyme,
-- retirer l'artefact de l'hebergeur / purger son cache si necessaire,
-- migrer le contenu vers Storage prive et configurer les droits cote serveur.
--
-- IMPORTANT : ceci recense les references dans la BD, pas tous les fichiers
-- potentiellement deja publies sur GitHub Pages / Netlify / Vercel.
-- Les routes HTML peuvent n'etre que des interfaces publiques sans donnees
-- privees integrees. Auditer chaque page et ses appels API avant d'en conclure
-- a une fuite; ne pas migrer une route HTML comme si c'etait un PDF.
-- Les PDF restreints exigent un support prive et la suppression des copies
-- publiques lorsqu'une exposition est confirmee.

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

-- Identifiants uniquement : ne jamais exposer publiquement les URL suspectes.
SELECT
  d.id AS document_id,
  d.project_id,
  d.status AS document_status,
  d.access_level,
  p.visibility AS project_visibility,
  CASE
    WHEN d.external_url ~* '\\.pdf([?#].*)? THEN 'PROJECT_NOT_FOUND'
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
 THEN 'PDF_FILE'
    WHEN d.external_url ~* '\\.html?([?#].*)? THEN 'PROJECT_NOT_FOUND'
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
 THEN 'HTML_ROUTE'
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
