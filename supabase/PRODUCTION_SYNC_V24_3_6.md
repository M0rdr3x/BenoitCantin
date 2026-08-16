# SINJIRA™ — Synchronisation Supabase production V24.3.6

Projet Supabase : `gpvivleexywljowcqkru`

## Pourquoi Fracture et certains écrans restent « À synchroniser »

Les fichiers de migration sont dans GitHub, mais GitHub Pages ne peut pas modifier PostgreSQL. Tant que les migrations ne sont pas appliquées au projet Supabase de production, les tables/RPC V24 n'existent pas réellement dans la base utilisée par le site.

## Ordre obligatoire

Dans Supabase → SQL Editor, appliquer **dans cet ordre** :

1. `supabase/migrations/20260814_sinjira_v24_foundation.sql`
2. `supabase/migrations/20260815_sinjira_v24_1_owner_and_live_fixes.sql`
3. `supabase/migrations/20260815_sinjira_v24_3_1_owner_repair_and_fracture_access.sql`
4. `supabase/migrations/20260815_sinjira_v24_3_6_server_marker_and_project_identity.sql`

Ensuite exécuter :

- `supabase/VERIFICATION_PRODUCTION_V24_3_6.sql`

La première colonne `server_version` doit retourner `24.3.6` et les contrôles essentiels doivent être à `true`.

## Ce que cette synchronisation débloque

- Coffre privé (`private_profiles`)
- Relations privées
- AbyssTime + fiche sociale
- Monde parallèle / état persistant
- Droits propriétaire complets
- Jetons propriétaire illimités côté serveur
- Catalogue/licences Fracture
- Création et jonction des parties Fracture
- Fiches privées de partie et rapports de fin de partie
- Marché V24 en mode préparé
- Diagnostic Administration → État du système

## Edge Functions

Après les migrations, redéployer au minimum les versions présentes dans le dépôt si elles ne sont pas déjà en production :

- `submit-character-questionnaire`
- `admin-license-codes`
- `redeem-license-code`

Les fonctions administratives existantes (`admin-console`, `admin-reports`, etc.) restent contrôlées par l'onglet **État du système**.

## Identifiant de projet

L'administration affiche désormais **Identifiant du projet** au lieu de `Slug`.

Pour Fracture :

- Identifiant visible : `Fracture du Réseau-Mère`
- Identifiant technique interne / URL : `fracture-du-reseau-mere`

Le second reste caché à l'usage normal afin de ne pas casser les URLs, licences et données existantes.
