# SINJIRA™ — Fracture du Réseau-Mère : moteur de règles V36

**Édition de référence : Déduction simplifiée** (voir `projets/sinjira/jeux/fracture-du-reseau-mere/regles.html`).

## Situation et portée

Le moteur de parties Web historique est **suspendu** : ses règles ne sont plus conformes à l'édition actuelle.
Le module `assets/js/sinjira-fracture-mechanics-v36.mjs` est une **brique métier pure, sans accès serveur ni interface publique**. Il ne met pas le lobby en service et n'autorise aucune diffusion d'informations privées.

En particulier, la PR V36 ne modifie ni Supabase, ni les droits, ni l'indexation, ni la page publique `jouer.html`.

## Contrats vérifiés par le code

- **Participants** : 1–20 humains; Solo/Duo utilisent 3 sièges, autres groupes un siège par humain.
- **Identités de faction** : uniquement le *nombre* de sièges Résistance/Réseau-Mère selon la table officielle des 3–20 sièges. Le module **ne crée, ne distribue, ne publie ni ne conserve aucune identité secrète**.
- **Cartes Opération** : exactement 90 cartes, dont 45 par faction; par faction 30 × 1 point, 12 × 2 points, 3 × 3 points.
- **Distribution** : 3 cartes par siège; chaque siège conserve exactement 2 cartes distinctes et défausse la troisième.
- **Centre** : 2N cartes *exactement* avant deux passages, sans aucune carte supplémentaire en règle standard. Chaque siège reçoit une carte par passage; 0 carte restante.
- **Score de ronde** : seules les cartes récupérées marquent, pour la faction indiquée sur leur face, indépendamment de l'identité du siège.
- **Solo/Duo** : chaque siège invisible est contrôlé par un humain. En Duo, le contrôle du siège 3 alterne chaque ronde, selon le Premier joueur choisi.
- **Express** : six rondes uniquement à partir de 13 humains; dix rondes dans les autres configurations.

Les cartes et choix sont fournis aux fonctions de manière explicite; la brique métier ne décide **jamais** à la place du joueur quelles cartes conserver ou tirer. Aucun bot autonome, modèle prédictif ou choix automatique n'est introduit.

## Contraintes de sécurité avant un futur mode Web

1. Les mains et les identités secrètes seront conservées côté serveur et jamais envoyées à un autre joueur. Le seul fait que le module soit pur **ne constitue pas une frontière de sécurité**.
2. Toute action de siège doit être rattachée par le serveur à un compte autorisé et au siège contrôlé pour la ronde (notamment le siège invisible du Duo).
3. Le choix de cartes doit utiliser une source d'aléa adaptée et une politique d'audit; ce module n'offre **aucun tirage aléatoire ni mélange automatisé**.
4. La persistance, les invitations, l'expiration, les changements de compte et la gestion de concurrence demandent des tests multijoueurs et RLS réels.
5. Le calcul final des scores, les rapports, les Preuves, les soupçons et les accusations finales doivent être entièrement alignés et validés avant toute réouverture de `jouer.html`.
6. Une partie physique utilisant les règles officielles reste distincte d'un jeu Web ouvert au public.

## Scénarios de vérification

Le fichier `tests/games/test_fracture_mechanics_v36.mjs` vérifie les 90 cartes, toutes les tailles de table, les sièges invisibles Solo/Duo, les limites Express, les cartes défaussées, les choix sans doublon, les deux passages, les scores et les entrées invalides.

Les tests sont nécessaires, mais ne remplacent **pas** des playtests physiques, l'arbitrage éditorial des règles, ni la certification de sécurité d'un futur service multijoueur.

## Lien avec le programme complet

Feuille de route : `docs/SINJIRA_PROGRAMME_AVANCEMENT_2026-11-07.md`, suivi GitHub [#826](https://github.com/M0rdr3x/BenoitCantin/issues/826). La V36 constitue une étape préparatoire au moteur Fracture, **pas la livraison du jeu multijoueur**. Le pourcentage global ne doit pas augmenter tant que les critères de mise en production ne sont pas remplis.
