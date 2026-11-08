# Sécurité Edge — dette historique de lecture HTTP entière

## Objet

Le scanner `scripts/validate_edge_raw_body_regressions.py` contrôle
**toutes les fonctions Edge** du dépôt, sans appeler Supabase ni lire des
données de comptes. Toute nouvelle lecture complète `await req.text()` ou
`await req.json()` non inscrite au registre est une erreur CI. Un fichier
historique ne peut pas multiplier ses lectures sans faire échouer la CI.

Un registre de 16 fonctions source encore concernées définit un
**plafond de dette technique**, pas une liste d'autorisations de sécurité :
- admin-analytics, admin-console, admin-license-codes, admin-reports,
  admin-sinjira-v18 et admin-social-v20;
- delete-player-account, fracture-engine-gateway, life-story-export;
- redeem-license-code, revoke-my-contributions, security-context;
- send-player-sheet, submit-character-questionnaire;
- submit-fracture-endgame et submit-game-contribution.

Les corrections #822 et #823 réduisent déjà ce nombre dans leurs branches
candidates. Une réduction ne doit jamais être annulée lors des futures PR.
Une migration ne pourra être qualifiée de terminée que lorsque toutes ces
fonctions utiliseront des lecteurs bornés **pendant** le transfert, et que
leur version **réellement déployée** sera recontrôlée.

## Contrat CI

- Entrées : `supabase/functions/*/index.ts`, garde UTF-8 strict et
  refus de symlinks et de sources surdimensionnées.
- Régressions : nouvelle fonction utilisant une lecture intégrale = ECHEC;
  deuxième lecture intégrale dans une fonction historique = ECHEC;
  lecture progressive `readLimitedUtf8Body` = acceptée.
- Déclencheurs : PR et push pertinents via
  `.github/workflows/edge-inventory-source-integrity.yml`.
- Aucun secret, JWT, migration, vote, donnée utilisateur ou appel HTTP
  n'est nécessaire.

## Limites importantes

Une expression régulière statique ne remplace ni l'analyse sémantique ni
un audit de flux réel. Elle ne détecte pas toutes les formes indirectes
de lecture, n'impose pas de délai maximal d'upload et ne limite pas le
nombre de requêtes simultanées. Une ligne historique encore tolérée
reste un **risque à corriger**.

Les trois fonctions publiques `get-document-url`,
`send-game-report`, `life-story-delivery` disposent déjà du lecteur
borné dans GitHub, mais leur **déploiement Supabase reste en retard**.
Voir les issues #702, #704 et #713 pour les règles de promotion,
la protection anti-abus et les dépendances SQL.
