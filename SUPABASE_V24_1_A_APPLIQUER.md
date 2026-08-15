# Supabase — mise en service V24.1

Projet ciblé : `gpvivleexywljowcqkru`

La mise en ligne des fichiers GitHub n'exécute pas les migrations SQL ni les Edge Functions.

## Ordre

1. Vérifier/appliquer `supabase/migrations/20260814_sinjira_v24_foundation.sql`.
2. Appliquer `supabase/migrations/20260815_sinjira_v24_1_owner_and_live_fixes.sql`.
3. Redéployer l'Edge Function `submit-character-questionnaire` depuis `supabase/functions/submit-character-questionnaire/index.ts`.
4. Se déconnecter/reconnecter au compte AbyssTime puis tester : Mon personnage, Réseau personnage, Mes lectures, Licences, Jetons, Monde parallèle et Fracture Online.

## Ce que la migration V24.1 doit produire pour le propriétaire

- `AbyssTime` rattaché au UUID du compte `kingtyrano@gmail.com`.
- portrait `/assets/media/characters/abysstime.webp`.
- statut personnage `assigned`, visible au compte, placement `SINJIRA — Livre II (titre à confirmer)`.
- dernière soumission du questionnaire rattachée au personnage; anciennes soumissions archivées plutôt que supprimées.
- fiche `character_social_profiles` créée/réparée.
- accès testeur à tous les projets existants + trigger pour les futurs projets.
- entitlement sur tous les produits existants + trigger pour les futurs produits.
- tous les romans existants ajoutés à `reader_library` + trigger pour les futurs romans.
- Monde parallèle initialisé pour AbyssTime si la fondation V24 est présente.
- jetons illimités côté fonction serveur.
- RPC Fracture `create_fracture_party` et `join_fracture_party` corrigées.

## Courriel du Registre

Le questionnaire ne dépend plus de Formspree. L'enregistrement Supabase est le succès principal.

Un courriel peut être envoyé depuis le serveur seulement si les secrets suivants sont configurés :

- `RESEND_API_KEY`
- `REPORT_FROM_EMAIL`
- facultatif : `CHARACTER_REPORT_TO_EMAIL` (sinon `kingtyrano@gmail.com`)

Même sans courriel configuré, l'avis interne `admin_notifications` est enregistré après la migration V24.1.
