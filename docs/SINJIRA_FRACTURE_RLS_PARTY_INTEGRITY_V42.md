# SINJIRA V42 — Confinement des mises à jour Fracture entre parties

**Statut : CANDIDAT UNIQUEMENT, NO_GO production.**  
Suite logique de l'audit V41 : [PR #874](https://github.com/M0rdr3x/BenoitCantin/pull/874), [issue #872](https://github.com/M0rdr3x/BenoitCantin/issues/872).

## Risque confirmé dans les métadonnées de production

Les tables `public.fracture_endgame_reports` et `public.fracture_player_documents` ont actuellement une politique RLS `UPDATE` qui vérifie seulement respectivement `owner_user_id = auth.uid()` et `user_id = auth.uid()`. Le **nouveau `party_id`** n'est pas contrôlé dans `WITH CHECK`, tandis que les politiques `INSERT` comprennent les contraintes nécessaires.

Une ligne appartenant à l'utilisateur pourrait donc en principe être déplacée vers une autre partie existante sans la même autorisation, **sous réserve** des clés étrangères, contraintes, droits et chemins SQL réels. Aucun test offensif n'a été réalisé sur la production; la possibilité d'exploitation n'est pas attestée par cet audit seul.

## Correctif proposé, strictement limité

`scripts/proposals/sinjira_fracture_v42_rls_update_candidate.sql` ne modifie que **deux politiques existantes** :

- *Rapport de fin de partie* : `WITH CHECK` exige toujours l'identité du propriétaire **et** une `fracture_parties.id` dont `owner_user_id` est ce même utilisateur.
- *Document de joueur* : `WITH CHECK` exige toujours le propriétaire du document **et** son appartenance à la partie cible vérifiée par le helper `sinjira_rls_internal.is_fracture_party_member` déjà employé par la politique `INSERT`.

Les clauses `USING` de départ ne sont pas élargies. La proposition ne modifie ni les autorisations `SELECT`, ni les politiques `INSERT`/`DELETE`, ni les privilèges, fonctions, comptes, jeux ou bonus.

**Limite métier explicite :** le déplacement vers *une autre partie déjà autorisée* reste possible. Cette proposition contrôle l'accès à la destination, **pas** l'immuabilité absolue du `party_id`, du siège du document ou la cohérence métier complète des formulaires. Ces décisions doivent être revues séparément.

## Vérification totalement isolée

La CI utilise un service PostgreSQL 17 temporaire, sans identifiants de production. `tests/security/sql/test_fracture_rls_v42.sql` construit une miniature du schéma et deux utilisateurs **fictifs** A et B, puis applique le candidat uniquement dans cette base éphémère.

Les cas vérifient les modifications de son propre document/rapport, le refus d'un transfert vers la partie de l'autre utilisateur, le refus de la réattribution du propriétaire, le maintien de l'édition entre parties dont l'utilisateur possède effectivement les droits et le refus de toute modification par l'autre compte. Des tests Python limitent la portée du candidat.

Les échecs d'autorisation attendus sont capturés explicitement et le test global échoue si un transfert interdit réussit. La réussite de ces tests ne prouvera pas que les fonctions et politiques complexes de la production sont identiques à cette maquette.

## Processus obligatoire avant application réelle

1. Faire revoir les deux politiques originales, les procédures de création des documents, les triggers et les effets sur les utilisateurs existants. Vérifier aussi l'absence de voie alternative `SECURITY DEFINER`.
2. Exécuter les tests sur une vraie copie **isolée** du schéma et ajouter les essais multicomptes par API, en particulier sur les anciens documents et les contraintes de sièges invisibles.
3. Une fois le correctif accepté, **créer une vraie migration via la procédure Supabase CLI prescrite**, inscrire la migration dans le registre protégé du dépôt et sélectionner son déploiement ciblé; ne jamais copier ce candidat dans un `db push` global.
4. Exiger le prévol distant en lecture seule, les secrets uniquement dans l'Environment de production autorisé, la confirmation explicite, le plan de retour arrière et les vérifications post-application.
5. Le moteur réseau Fracture reste **NO_GO** jusqu'au règlement des autres blocages V41, notamment #857 (+3 vs +5, méthode de score), les sièges humains invisibles et les tests de session révoquée.

**Cette PR ne modifie ni la production Supabase ni le site public.** La maturité globale SINJIRA reste estimée à 66,5 % ≈ 67 % (±10 points); un candidat SQL n'est pas une fonctionnalité livrée.
