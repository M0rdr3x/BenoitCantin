# SINJIRA™ — Fracture V40 : politique de soupçons par humain

**Objet :** corriger une limite de V39 sans trancher les décisions éditoriales de l'issue [#857](https://github.com/M0rdr3x/BenoitCantin/issues/857).

## Pourquoi V40 existe

V39 valide une liste commune `eligibleTargets` de sièges autorisés à être soupçonnés. Cette seule liste **ne peut pas interdire à chaque humain de se soupçonner lui-même**, puisque le numéro de siège interdit varie avec l'auteur du bulletin. V40 ajoute donc la validation **par humain**, avant d'appeler le dépouillement V39 inchangé.

## Contrat

- Un appel unique du futur serveur fournit les bulletins **complets**, ordonnés par ronde puis par humain/siège de numéro 1 à `humans`, ainsi que les politiques approuvées.
- `allowSelfSuspicion` est un booléen **obligatoire** : `false` interdit, pour chaque humain de numéro `h`, le choix du siège `h`; `true` l'autorise.
- `allowAbstention` et `eligibleTargets` restent obligatoires et sont vérifiés par V39. L'abstention représentée par `null` n'est jamais accordée automatiquement.
- En Solo et Duo, aucun siège invisible n'ajoute de bulletin. Les sièges invisibles peuvent être des cibles seulement si `eligibleTargets` les inclut.
- Le module accepte la configuration standard 1–20 humains ou Express 13–20 humains et délègue à V39 le contrôle du nombre total de rondes.
- La fonction retourne la structure agrégée et gelée de V39, **sans ajouter les bulletins individuels**.

## Chaînage complet des votes privés (V39 → V38)

La fonction `fracturePreparePrivateFinalDecisionV40` reçoit, **exclusivement côté serveur**, les soupçons de chaque ronde, les bulletins d'accusation finale et les politiques de jeu approuvées. Elle :

1. vérifie l'auto-soupçon selon `allowSelfSuspicion` pour chaque humain et le dépouillement V39 (rondes complètes, abstention, cibles admissibles);
2. transmet la liste réelle des cumuls `suspicionTotals` à V38 (aucune valeur de remplacement);
3. vérifie les accusations finales individuelles, les sièges et les égalités;
4. renvoie uniquement une **structure privée** contenant le décompte des soupçons et celui des accusations, jamais les bulletins initiaux.

Ce chaînage est un contrat technique entre modules. **Il n'authentifie pas les bulletins, ne publie pas les résultats et n'attribue aucun bonus de points** : la politique officielle du score final demeure à arbitrer dans #857. Si V38 signale un départage au hasard requis, la décision reste en attente d'un tirage authentique et auditable réalisé par le futur serveur.

## Confidentialité et limites

Ce code ne réalise **aucune authentification**. Un appelant non fiable peut forger `humans`, `roundBallots`, les politiques ou l'ordre des sièges; tout cela doit être validé par l'API avec JWT/session, contrôle des joueurs, RLS, séparation des rôles et transactions. Le module n'est pas destiné à être exécuté dans un navigateur avec des bulletins d'autrui. Même un cumul agrégé peut révéler des secrets (particulièrement à 1 joueur) : il demeure privé jusqu'à la révélation autorisée.

Ne pas en déduire que les soupçons de soi-même sont officiellement permis ou interdits : **seul le responsable peut fixer le booléen approuvé**, et ce choix est suivi dans #857. De même, V40 ne modifie ni le score V35 ni les accusations V38.

## Vérifications et livraison

Les tests V40 couvrent l'interdiction/autorisation explicite de l'auto-soupçon, le premier/dernier joueur, Solo, Duo, Express, entrées invalides, abstentions et confidentialité, ainsi que la compatibilité avec V39 et le **chaînage confidentiel V39 → V38** (sélection, départage, bulletins invalides et absence de bonus). Le workflow dédié exécute V39, V40 et la régression officielle V36 avec le vrai code du dépôt.

**Livraison limitée à la couche de règles pures** : pas de Supabase, migration, activation multijoueur, lecture de données réelles ou publication côté client. L'intégration serveur et les tests multicomptes ne sont pas achevés.

[Suivi global #826](https://github.com/M0rdr3x/BenoitCantin/issues/826) — maturité estimée SINJIRA inchangée à environ 67 % tant que ces fonctionnalités ne sont pas vérifiées en production.
