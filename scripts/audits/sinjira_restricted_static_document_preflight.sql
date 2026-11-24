-- SINJIRA — prévol documentaire P0, lecture seule, exécutable dans SQL Editor
-- Ne retourne ni identité, ni URL, ni chemin ni métadonnée de contenu.
-- À rejouer avant toute publication/migration du catalogue documentaire.
-- Une entrée restreinte munie d'une URL statique doit être clarifiée :
-- soit le document est public et ses métadonnées doivent l'indiquer,
-- soit il doit être migré vers un stockage effectivement privé.
-- NOTE : une URL publique GitHub/CDN passée n'est pas rendue privée par
-- l'effacement d'une entrée SQL ou par l'absence dans le nouvel artefact.

WITH restricted AS (
  SELECT d.status, d.access_level, d.external_url, d.storage_bucket, d.storage_path
  FROM public.documents AS d
  JOIN public.projects AS p ON p.id = d.project_id
  WHERE nullif(btrim(d.external_url), '') IS NOT NULL
    AND (d.access_level <> 'public' OR p.visibility <> 'public')
)
SELECT
  count(*)::int AS restricted_static_url_count,
  count(*) FILTER (WHERE status = 'approved')::int AS approved_restricted_static_url_count,
  count(*) FILTER (WHERE status = 'archived')::int AS archived_restricted_static_url_count,
  count(*) FILTER (WHERE storage_bucket IS NOT NULL AND storage_path IS NOT NULL)::int
    AS records_with_storage_location
FROM restricted;

-- Contrôle reproductible de la collision avec les cinq PDF de jeu de
-- l'allowlist publique étudiés le 21/11/2026 (réviser lors de tout changement).
-- Les chemins sont déjà présents dans le dépôt GitHub PUBLIC ; aucune URL
-- de stockage privée ni URL de jeton signé n'est jamais exportée.
WITH game_public_pdf(path) AS (
  VALUES
  ('/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Feuille_de_fin_de_partie_Interactive.pdf'),
  ('/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf'),
  ('/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fiche_Joueur_Interactive.pdf'),
  ('/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fracture_du_Reseau_Mere_Fiche_Joueur_Web.pdf'),
  ('/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Mode_Solo_3_Joueurs_Interactive.pdf')
),
restricted AS (
  SELECT d.status,d.external_url
  FROM public.documents AS d
  JOIN public.projects AS p ON p.id=d.project_id
  WHERE nullif(btrim(d.external_url),'') IS NOT NULL
    AND (d.access_level <> 'public' OR p.visibility <> 'public')
)
SELECT status, count(*)::int AS public_pdf_catalog_conflicts
FROM restricted AS r
JOIN game_public_pdf AS a ON a.path = r.external_url
GROUP BY status
ORDER BY status;
