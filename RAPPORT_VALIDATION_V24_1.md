# SINJIRA™ V24.1 — Rapport de validation

Date de préparation : 2026-08-14

## Correctifs ciblés

- Compte propriétaire `kingtyrano@gmail.com` / `AbyssTime` : accès total prévu côté interface ET côté serveur.
- Jetons du propriétaire : illimités; `spend_sinjira_tokens()` ne débite jamais le propriétaire.
- Personnage AbyssTime : migration de resynchronisation avec portrait, statut `assigned`, visibilité, fiche sociale et note Livre II.
- Réseau personnage : message explicite si la migration V24.1 n'est pas encore appliquée.
- Mes lectures : correction du crash `Cannot read properties of null (reading 'map')`, avec compatibilité avec un ancien schéma `reader_library`.
- Fracture Online : correction SQL de l'ambiguïté `party_code` dans les RPC de création/jonction de partie.
- Monde parallèle : plus de chargement infini; état/fallback explicite si le backend V24.1 manque.
- Registre : retour à un questionnaire plus complet de type V23, mais simplifié et principalement à choix; suppression des longues questions/dilemmes difficiles.
- Registre : Formspree retiré du flux de soumission. Supabase est la source de vérité.
- Notification questionnaire : avis interne admin; courriel serveur facultatif avec Resend si configuré.
- Navigation du compte : suppression de la grosse barre de défilement horizontale sur ordinateur; scroll discret conservé sur mobile.
- 404 : ajout de redirections pour plusieurs anciennes routes SINJIRA™.

## Validation statique

- 10 modules JavaScript modifiés vérifiés avec `node --check` : OK.
- Edge Function TypeScript : analyse TypeScript effectuée; uniquement les imports Deno/Supabase non résolus hors runtime Deno ont été signalés, aucune erreur syntaxique locale détectée.
- Audit des zones actives `index.html`, `compte/`, `projets/sinjira/`, `admin/sinjira/` : 0 référence locale manquante sur 1 238 références contrôlées.
- Registre : aucune dépendance Formspree dans le formulaire ou son JavaScript.
- Registre : aucune question de dilemme lourd détectée dans la nouvelle version.

## Important — GitHub ne modifie pas Supabase

Après la mise à jour GitHub, appliquer côté Supabase dans cet ordre :

1. `supabase/migrations/20260814_sinjira_v24_foundation.sql` si elle n'a pas déjà été appliquée.
2. `supabase/migrations/20260815_sinjira_v24_1_owner_and_live_fixes.sql`.
3. Redéployer `supabase/functions/submit-character-questionnaire/`.

Sans les étapes 1-2, le frontend peut afficher les nouveaux messages de diagnostic, mais il ne peut pas créer/restaurer les lignes de base de données du personnage, des droits, du Monde parallèle ou corriger les RPC Fracture.
