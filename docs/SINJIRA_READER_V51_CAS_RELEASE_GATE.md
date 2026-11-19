# SINJIRA — V51, correctif CAS de synchronisation de lecture : protocole de livraison contrôlée

**Travail de développement daté du 9 novembre 2026 — PR en attente de revue.**

## Pourquoi V51 ?

Le banc **V50** a reproduit sur PostgreSQL fictif une perte logique : un ancien appareil sauvegardait la **page 13** par `UPSERT`, et écrasait une nouvelle **page 42** sauvegardée par un autre appareil du même compte. Le verrou de requêtes local `progressQueue` et la comparaison préalable d'horodatages ne garantissent pas un verrou interappareils. Le risque est **reproduit en laboratoire**, pas une perte d'utilisateur réel observée en production.

La V51 prépare **une correction réelle de code et de schéma** dans cette PR, mais **aucune migration de production n'est appliquée et aucune réception réelle n'est donnée**.

## Architecture proposée

- **Nouvelle migration additive** `supabase/review-candidates/20261110011500_sinjira_reader_progress_revision_cas_v51.sql` : ajoute `revision bigint NOT NULL DEFAULT 0` à `public.sinjira_reader_library` sans réécrire les progressions historiques, avec contrainte de non-négativité.
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

**Concurrence réellement simultanée dans le laboratoire** : le script `scripts/test_sinjira_reader_v51_concurrent_local.sh`, lancé après la fixture SQL V51, démarre **deux connexions PostgreSQL indépendantes en arrière-plan** pour le même compte fictif, le même livre et la même révision attendue. Il exige **exactement un `saved` et un `conflict`**, puis vérifie une révision unique 3 et l'absence de modification du compte B. Le contrôle porte sur la sérialisation réelle PostgreSQL et n'équivaut toujours pas à deux appareils avec réseau ou authentification Supabase.

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

## Correctif V51.1 — homologation des droits sur le roman avant CAS (18 novembre 2026)

**Statut : correctif en PR #947 / NON FUSIONNÉ / NON APPLIQUÉ À SUPABASE.** Le code candidat V51 original vérifiait `auth.uid()` et l'existence de `sinjira_novels.id`, sans vérifier le droit de lecture. La fonction `SECURITY DEFINER` pouvait donc enregistrer une progression pour un titre non attribué. Ce rapport décrit une **lacune d'autorisation du code candidat**, pas une fuite constatée en production.

**Changement apporté à la migration candidate :** avant toute insertion, mise à jour ou lecture du conflit CAS, exiger (1) `sinjira_novels.status='published'` et (2) une habilitation serveur actuelle : propriétaire `is_sinjira_owner(auth.uid())`, administrateur `is_sinjira_admin(auth.uid())` ou attribution `user_entitlements(user_id,product_id)` liée à un `products.active=true`. La règle est alignée sur `supabase/functions/get-novel-file-url/index.ts`. Les titres inconnus, non publiés, sans licence, désactivés et révoqués retournent tous le même `result_status='unavailable'`, sans titre, progression ou horodatage. Aucun marque-page ne doit être écrit par ce chemin en cas de refus.

**Preuves de schéma consultées en lecture seule, sans modification de base :** Supabase `public.sinjira_novels.status/product_id`, `public.products.id/active`, `public.user_entitlements.user_id/product_id`, et fonctions `public.is_sinjira_owner(p_user_id uuid)` / `public.is_sinjira_admin(p_user_id uuid)`. Les RLS des tables métier ne dispensent pas du contrôle dans une fonction `SECURITY DEFINER`.

**Tests ajoutés en laboratoire PostgreSQL jetable :** comptes fictifs A/B, titre autorisé publié, roman publié non attribué, roman annoncé malgré attribution, produit inactif, UUID inconnu, révocation d'un droit après une sauvegarde existante, absence de modification de la page/révision/date lors du refus, et permissions administrateur/propriétaire sur un roman publié. Les anciens tests CAS page 42 contre page 13, appels concurrents, privilèges, comptes séparés et migration répétée sont conservés. **Les tests GitHub doivent réussir sur le nouveau SHA; ce paragraphe ne prétend pas qu'ils ont réussi.**

**Risques et décisions restant à homologuer avant GO :** révocation concurrente à l'écriture, fonctionnement réel des deux fonctions d'administration sous Supabase Auth/JWT, changement de statut ou produit, lien entre droit d'enregistrer et droit de télécharger le fichier intégral, lecture des anciens marque-pages d'un titre révoqué, test d'adversaire sur un vrai environnement de préproduction, approbation humaine de la migration, plan pour les anciens clients UPSERT et recette réseau de deux appareils. La vérification sur la base Supabase de production n'a été qu'une inspection de métadonnées en lecture seule : ni DDL, ni migration, ni données d'utilisateurs n'y ont été modifiées.

**NO-GO conservé** pour `reader_v32_prod`, `reader_two_devices` et la plateforme SINJIRA; aucune date de livraison ni augmentation du 66,5 % ±10 points.

## V51.2 — sérialisation des droits et de la sauvegarde CAS

Un contrôle d'habilitation sans verrou est insuffisant dans un scénario **révocation et sauvegarde concurrentes** : la sauvegarde pourrait lire une licence encore visible, la révocation pourrait devenir effective, puis la page pourrait être écrite après cette révocation. La migration candidate ajoute des verrous PostgreSQL `FOR SHARE` sur la ligne `sinjira_novels` publiée et, pour un accès par achat, les lignes `user_entitlements` et `products`. Les `DELETE` ou changements de statut/activité concurrents doivent être sérialisés vis-à-vis de la transaction de sauvegarde.

**Test automatisé de concurrence réel, sans réseau ni comptes utilisateurs :** dans `scripts/test_sinjira_reader_v51_concurrent_local.sh`, une première connexion PostgreSQL enlève l'attribution fictive du compte A et garde la transaction ouverte. Une seconde connexion tente une sauvegarde à la révision attendue; elle doit attendre la suppression puis répondre `unavailable`, sans changer la page 51/52, la révision 3 ou le compte B. Le test est distinct de la course initiale « deux appareils, une seule révision CAS » et s'exécute sur la **même base PostgreSQL jetable**.

**Limites / NO-GO :** ce scénario ne démontre pas encore la concurrence d'une révocation des rôles d'administration avec une sauvegarde ni l'isolation réelle sous les sessions Supabase/JWT. Les fonctions owner/admin, l'ordre de verrouillage, les transitions `published` et `products.active`, la politique métier de sauvegarde des marque-pages après remboursement, ainsi que le chemin de **lecture** des anciens marque-pages nécessitent une revue en préproduction. Aucun code SQL n'a été appliqué à Supabase, aucune modification de données réelles et aucune autorisation de publication.

## V51.3 — retrait de publication et désactivation produit concurrents

**Portée candidate, aucune migration de production.** La fonction CAS de V51.2 verrouille déjà le roman et, pour les droits d'achat, les lignes d'attribution et de produit. V51.3 ajoute au banc de concurrence PostgreSQL isolé deux scénarios de validation supplémentaires :

- **Produit inactivé pendant la sauvegarde** : une transaction commence `UPDATE products SET active=false` sur un produit fictif auquel le compte A est attribué. Avant son `COMMIT`, une autre connexion essaie de remplacer la progression existante du roman publié. Le résultat attendu est `unavailable`, et la page 12 / révision 0 doit rester intacte.
- **Roman dépublié pendant la sauvegarde** : une transaction commence `UPDATE sinjira_novels SET status='archived'` sur un roman fictif jusque-là publié. Une seconde connexion tente un CAS au même moment. Le résultat attendu est encore `unavailable`, sans changement de page ni de révision.

Les scénarios réutilisent l'hôte local `127.0.0.1`, la base jetable `sinjira_reader_v51_lab` et des UUID uniquement fictifs; ils n'accèdent jamais à Supabase hébergé. Un contrôle final vérifie également l'absence de modification de la progression du compte B.

**Ces nouveaux essais doivent être marqués PASS seulement après lecture du journal GitHub Actions sur le SHA correspondant.** Ils ne certifient pas le comportement d'une session Auth réelle, la révocation des rôles owner/admin, les clients hors ligne ni la migration de production. Les décisions de droits, l'audit RLS, la compatibilité des anciens lecteurs et les tests sur deux téléphones restent requis. **PR #947 DRAFT / NO-GO.**

## V51.4 — révocation concurrente des rôles owner et admin (18 novembre 2026)

**Correctif de la fonction CAS candidate, jamais appliqué sur la base Supabase hébergée.** Après les achats, statuts et produits (V51.2 / V51.3), le chemin privilégié `owner/admin` est désormais verrouillé. Auparavant, les fonctions `is_sinjira_owner(auth.uid())` et `is_sinjira_admin(auth.uid())` étaient appelées sans retenir la ligne du rôle pendant la transaction de sauvegarde. Une suppression du rôle pouvait donc devenir effective entre la vérification et l'écriture. V51.4 ajoute une requête `EXISTS` qui sélectionne la ligne correspondante de `public.internal_admin_users` avec `FOR SHARE OF staff`, tout en préservant les fonctions de contrôle de rôle existantes.

**Recette transactionnelle ajoutée dans la base PostgreSQL fictive `sinjira_reader_v51_lab`** : deux comptes de test sont respectivement `admin` et `owner`. Pour chacun, un roman publié dont l'accès n'est pas couvert par un achat actif est accessible uniquement grâce au rôle. Une transaction supprime le rôle et le garde non validé pendant trois secondes; une autre connexion tente en parallèle d'écraser le marque-page. Résultat exigé : réponse uniforme `unavailable` après retrait du rôle, page et révision intactes, autres comptes inchangés. Les anciens tests de droits d'achat et de catalogue restent exécutés.

**Limites importantes** : le PASS du banc local n'établit pas un PASS Supabase Auth réel, ni la révocation des JWT, la lecture ou le téléchargement des fichiers PDF par d'autres fonctions, ni la politique métier concernant le statut du contenu. L'intégration des branches PR #947 et #1000, l'absence de régressions sur `main`, la réception de deux appareils physiques et l'approbation des migrations demeurent nécessaires. **NO-GO production** maintenu.

