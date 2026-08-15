# SINJIRA™ V24.1 — correctifs après essais réels

Correctifs intégrés :

- restauration/synchronisation du personnage **AbyssTime** pour `kingtyrano@gmail.com` ;
- rattachement de la dernière soumission du Registre au personnage propriétaire ;
- accès propriétaire permanent à tous les projets, romans et produits ;
- Jetons SINJIRA™ illimités pour le compte propriétaire (affichage ∞ et bypass serveur prévu) ;
- correction de `Cannot read properties of null (reading 'map')` dans **Mes lectures** ;
- correction SQL de Fracture Online : `column reference "party_code" is ambiguous` ;
- navigation du compte qui se replie sur plusieurs lignes sur grand écran et masque la barre horizontale sur mobile ;
- Monde parallèle ne reste plus bloqué sur « Chargement… » si la migration n'est pas installée ;
- Registre : retour à un questionnaire plus riche inspiré de V23, mais sans les dilemmes difficiles et avec une seule question libre finale ;
- le Registre ne dépend plus de Formspree : le dossier est la source de vérité Supabase, une notification interne admin est créée, et le courriel passe par le service serveur s'il est configuré ;
- page 404 modernisée et redirection de plusieurs anciennes routes SINJIRA™.

## Important

Le ZIP GitHub met à jour le **frontend et le code Supabase**, mais GitHub Pages ne peut pas modifier la base Supabase tout seul.
Après l'upload GitHub, appliquer les migrations dans `supabase/migrations/`, notamment :

1. `20260814_sinjira_v24_foundation.sql` si elle n'a pas encore été appliquée ;
2. `20260815_sinjira_v24_1_owner_and_live_fixes.sql` ;
3. redéployer `submit-character-questionnaire`.

Tant que ces étapes serveur ne sont pas faites, le navigateur peut afficher la nouvelle interface mais les données de production ne seront pas réparées.
