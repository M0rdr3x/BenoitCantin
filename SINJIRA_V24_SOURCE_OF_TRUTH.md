# SINJIRA™ V24 — Source of Truth

## Version publique
- Marque affichée : **SINJIRA™**
- Domaine actuel : `www.benoitcantin.com`
- Portail SINJIRA™ : `/projets/sinjira/`
- Administration canonique : `/admin/sinjira/`

## Accueil
L'accueil principal présente seulement les projets actifs :
- SINJIRA™
- Projet Nova

## Portes principales SINJIRA™
1. Romans
2. Jeux
3. Registre des Consciences
4. Communauté

Le Codex, le Monde parallèle et le Marché sont accessibles depuis les portails SINJIRA™/Communauté plutôt que de surcharger l'accueil principal.

## Livre I
- Titre : `SINJIRA — Livre I : La Cendre du Jugement`
- Couverture Web officielle V24 : `assets/media/sinjira-livre-1-cover.webp`
- Démo publique : `projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf`
- Le PDF maître intégral corrigé reste hors du dépôt public.

## Comptes
- Authentification : Supabase Auth
- Profil communautaire historique : `profiles` / `social_profiles`
- Profil privé V24 : `private_profiles`
- Relations privées : `family_relationships`
- Brouillon questionnaire rapide : `character_questionnaire_drafts`
- Confidentialité : `privacy_settings`
- Notifications : `notification_preferences`

## Personnages
- Une demande/personnage par compte selon la logique existante.
- Le questionnaire V24 est court et principalement à choix.
- L'IA de création est désactivée (`manual_only: true`).
- Aucun brouillon ne devient canonique automatiquement.

## Monde parallèle
Fondation V24 :
- `parallel_cycles`
- `parallel_missions`
- `parallel_responses`
- `parallel_character_state`

Le moteur fonctionne d'abord de façon manuelle. L'automatisation IA viendra après la finalisation du site.

## Marché
Fondation V24 : `market_listings`, `market_favorites`.
Règles retenues :
- particuliers : 0 % de commission SINJIRA™;
- 0 $ = don réellement gratuit;
- 0–20 $ : aucune consommation de jeton;
- >20 $ : 1 jeton lors de l'activation commerciale;
- entreprises : modèle commercial à décider séparément.

## Jetons
Grand livre : `token_ledger`.
Aucune écriture directe du navigateur.
Aucun pay-to-win.
Aucun transfert entre utilisateurs vivants.
Les achats de jetons restent désactivés en V24.

## Licences physiques
- Lots : `license_batches`
- Empreintes : `activation_codes`
- Activations : `license_redemptions`
- Droits : `user_entitlements`
- Génération : Edge Function `admin-license-codes`
- Activation membre : Edge Function `redeem-license-code`
- Secret requis : `SINJIRA_LICENSE_PEPPER`

Les codes bruts ne sont retournés qu'une seule fois au moment de la génération.

## IA
État V24 : **OFF**.
Le site doit fonctionner sans OpenAI ou autre fournisseur d'IA.
