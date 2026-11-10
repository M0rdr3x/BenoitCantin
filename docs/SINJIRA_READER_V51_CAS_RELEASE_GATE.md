# SINJIRA — V51, correctif CAS de synchronisation de lecture : protocole de livraison contrôlée

**Travail de développement daté du 9 novembre 2026 — PR en attente de revue.**

## Pourquoi V51 ?

Le banc **V50** a reproduit sur PostgreSQL fictif une perte logique : un ancien appareil sauvegardait la **page 13** par `UPSERT`, et écrasait une nouvelle **page 42** sauvegardée par un autre appareil du même compte. Le verrou de requêtes local `progressQueue` et la comparaison préalable d'horodatages ne garantissent pas un verrou interappareils. Le risque est **reproduit en laboratoire**, pas une perte d'utilisateur réel observée en production.

La V51 prépare **une correction réelle de code et de schéma** dans cette PR, mais **aucune migration de production n'est appliquée et aucune réception réelle n'est donnée**.

## Architecture proposée

- **Nouvelle migration additive** `supabase/migrations/20261110011500_sinjira_reader_progress_revision_cas_v51.sql` : ajoute `revision bigint NOT NULL DEFAULT 0` à `public.sinjira_reader_library` sans réécrire les progressions historiques, avec contrainte de non-négativité.
- **Nouvelle fonction SQL** `public.sinjira_reader_save_progress_cas(novel,revision_attendue,page,pourcentage,ratio)`, créée en `SECURITY DEFINER`, `search_path` vide et avec `auth.uid()` **obligatoire**. L'appelant ne fournit aucun `user_id`. Chaque requête vise uniquement son propre `user_id` et le roman demandé, sans texte de roman ni identifiant d'une autre personne.
- **Première sauvegarde** : `revision_attendue=NULL` signifie que la ligne n'existe pas; `INSERT ... ON CONFLICT DO NOTHING` refuse le deuxième appareil qui arrive avec une ancienne hypothèse. **Sauvegarde existante** : `UPDATE ... WHERE revision=revision_attendue` sous verrou transactionnel PostgreSQL, suivi de `revision=revision+1`. Un conflit répond `result_status='conflict'` et retourne seulement sa propre progression; il n'écrit rien.
- **Suppression du contournement** : retrait des `GRANT INSERT, UPDATE` directs à `anon`, `authenticated` et `PUBLIC`. C'est une modification importante : les **anciens clients** qui utilisent encore l'`UPSERT` perdent leur droit d'écriture. Le protocole de déploiement **doit** coordonner la disponibilité de la nouvelle version et contrôler toute autre application de sauvegarde.
- **Liseuse principale** `assets/js/sinjira-liseuse-v26.js` : retire les deux UPSERT anciens (dont le repli après erreur `scroll_ratio`), lit `revision` en même temps que la page, appelle la fonction CAS, garde localement une progression si V51 n'est pas disponible et **n'écrase jamais automatiquement un conflit**. L'horloge de l'appareil ne décide plus de la priorité d'écriture en base.
- **Chemin historique de bibliothèque** `assets/js/sinjira-reader-progress-v24-4-61.js` : remplace aussi l'UPSERT direct par un appel CAS et refuse de présenter un conflit comme une sauvegarde réussie.

### Risque de déploiement : anciens clients

L'application de V51 avant la disponibilité de nouveaux clients arrêtera les enregistrements cloud via les anciens chemins. La publication du nouveau client **avant V51** n'enregistrera plus dans le cloud et devra **conserver localement les positions**, avec message explicite. **Ne pas fusionner ou publier isolément** sans plan de bascule et retour arrière validé. Faire l'inventaire de tous les autres clients et extensions qui appellent `sinjira_reader_library` directement avant de révoquer les privilèges.

Une fenêtre de transition contrôlée peut devoir être annoncée aux lecteurs : **aucune sauvegarde silencieusement perdue ni prétention que le cloud fonctionne**, une vérification d'accès, et le maintien de la sauvegarde locale doivent être observés sur le véritable parcours.

## Recette obligatoire

**Laboratoire (automatisé, non certificatif)** :

`tests/security/sql/test_sinjira_reader_v51_cas.sql` applique d'abord V32 via la fixture V48 (comptes fictifs A et B, RLS), puis V51, et contrôle :

- migration additive préservant les anciennes pages, `scroll_ratio` et dates;
- RPC exécutable par `authenticated` mais non par `anon`, plus absence de droit `INSERT,UPDATE` directs;
- sauvegarde **page 42** avec révision 0 → 1, tentative ancienne **page 13** avec révision 0 → **conflit**, puis page 43 avec révision 1 → 2;
- une nouvelle ligne ne peut pas être écrasée par un second appel initial;
- refus des pages ou ratios invalides, lecture privée du compte A par B interdite;
- exécution **répétée de la migration** sans changement des marque-pages ni de leurs horodatages et sans doublon de contrainte;
- validation statique des deux clients sans `UPSERT` résiduel et absence de secret ou lien à une vraie base.

**Étape de préproduction indispensable (non faite par cette PR)** : initialiser une base de test fidèle aux politiques de production et au catalogue des romans, vérifier le comportement réel de Supabase Auth/JWT, des rôles et des lecteurs, tester la première création en simultané, deux sessions différentes du même compte, les erreurs réseau et la révocation de session. Faire auditer le choix `SECURITY DEFINER`, les GRANT, la politique RLS, la table de livres, le périmètre des droits d'achat et toute possibilité de contournement via d'autres RPC.

**Déploiement approuvé (non réalisé)** : établir une liste complète des consommateurs SQL et du client historique, prévenir des dégradations transitoires, protéger les versions PWA en cache, prévoir le retour arrière qui préserve la nouvelle colonne `revision`, obtenir sauvegarde/résolution des droits, appliquer **uniquement la migration revue** dans le mécanisme de déploiement autorisé, purger les versions dangereuses du cache ou les bloquer au serveur, puis publier la nouvelle interface. Réaliser ensuite la recette sur **deux appareils réels**, une seule identité autorisée et uniquement des livres de test.

## Critères de refus de lancement

- Tant que V32 et V51 ne sont pas attestées en production, `reader_v32_prod` reste **OPEN**.
- Tant qu'une sauvegarde A → B → A réelle, l'anti-écrasement, la révocation des autres clients et la gestion des conflits n'ont pas été vérifiés, `reader_two_devices` reste **OPEN**.
- Les tests GitHub, même verts, **ne valident pas** une mutation de la base Supabase réelle, ni les droits des clients, ni l'absence de pertes avec des téléphones déconnectés.
- Aucun score de programme, aucun GO, aucune date de fin ne change à la suite de cette PR.

## État global au 8 novembre 2026

**SINJIRA™** : maturité pondérée estimée **66,5 % (±10 points)**, **13/13 portes de lancement ouvertes**.  
**Projet Nova politique** : 47 points sur 100, cible de planification proposée du 31 décembre 2027, non garantie.  
**Nova–Sinjira services publics** : 14 secteurs et aucun taux autonome certifiable.  
**Boussole électorale** : 9 critères sur 12; **sondage** : 6 critères sur 11, fermé.

**Références GitHub** : issue P0 <https://github.com/M0rdr3x/BenoitCantin/issues/945>, banc précédent <https://github.com/M0rdr3x/BenoitCantin/pull/944>, et registre central <https://github.com/M0rdr3x/BenoitCantin/issues/840>. Pas de fusion avant revue de sécurité et de l'ordre d'exploitation.
