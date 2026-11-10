# Projet Nova — P50V : dossier administrateur de protection de `main`

**16 octobre 2026 · Proposition contrôlée, NON APPLIQUÉE · Décision NO_GO**

## Constat GitHub actuel

La branche `main` du dépôt public partagé `M0rdr3x/BenoitCantin` est au commit `9ed5f70cbe7022f25a679346a1288701f3b09067`. L'API `GET /branches/main` signale `protected:false`, les checks requis sont vides et les rulesets accessibles sont absents. Le dossier [#135](https://github.com/M0rdr3x/BenoitCantin/issues/135) suit la correction serveur. La demande de vrais réviseurs pour Projet Nova reste suivie dans [#662](https://github.com/M0rdr3x/BenoitCantin/issues/662).

**Le modèle ci-joint n'est pas un ruleset GitHub installé.** Il s'agit d'un corps JSON de proposition, volontairement `enforcement: "disabled"`, nécessitant une intervention d'un administrateur dûment habilité.

## Trois checks effectivement admissibles comme candidats

Ces trois contrôles ont été vérifiés **sur une PR récente**, au commit `936e8ced1d2552eaaf72baaf2ec1667d3ee823de`. Chaque job s'est terminé en `success`, et les trois workflows de `main` s'exécutent sur les PR vers cette branche **sans filtre `paths:`**.

| Contexte requis exact | Workflow source | Exécution GitHub constatée | Application émettrice |
| --- | --- | --- | --- |
| `no-committed-secrets` | `.github/workflows/sinjira-secret-guard.yml` | `38991867366` | GitHub Actions, `15368` |
| `Contrat sécurité validation site` | `.github/workflows/validate-site.yml` | `38991867326` | GitHub Actions, `15368` |
| `Contrat sécurité CI navigateur` | `.github/workflows/e2e-site.yml` | `38991867343` | GitHub Actions, `15368` |

Le validateur P50V refuse une modification des octets des trois workflows sans réexamen. Il vérifie les **empreintes de blobs Git** des fichiers sources, leurs déclarations `pull_request`, l'absence de `paths` dans les déclencheurs et les noms de job affichés.

**Ne pas configurer comme checks requis globaux** des jobs à exécution conditionnelle, des noms génériques ambigus ou des workflows filtrés par `paths:` (notamment les workflows propres aux étapes P50T–P50V). Pour les checks exigés, préférer leurs contextes précis et sélectionner **GitHub Actions** comme source d'émission.

## Proposition de règles, à examiner dans la console d'administration

Le document `P50V_CANDIDAT_RULESET_MAIN_DESACTIVE.json` contient :
- `target: branch` limité à `refs/heads/main`, sans exception de branches et **sans bypass actor** préconfiguré;
- **pull request avant fusion** et **au moins une approbation de code**, avec rejet des approbations périmées après push, revue du dernier push par une autre personne et discussions résolues;
- `require_code_owner_review:false` **en phase initiale**, car la règle publique `CODEOWNERS` ne déclare que `* @M0rdr3x`. Ce choix évite de faire passer une approbation d'auteur unique pour une revue indépendante; le responsable pourra renforcer cette condition lorsque de véritables équipes ou propriétaires distincts seront désignés;
- interdiction de force-push (`non_fast_forward`) et de suppression de la branche (`deletion`);
- trois checks obligatoires avec origine `integration_id: 15368` et politique stricte de mise à jour de la base (`strict_required_status_checks_policy:true`);
- `enforcement:"disabled"` dans le fichier versionné : **ne jamais confondre ce fichier avec une protection active**.

Cette configuration est un **minimum technique à valider pour un dépôt commun**, pas une qualification du nombre de responsables juridiques ou politiques requis par Projet Nova. L'application du ruleset à `main` affecterait aussi SINJIRA. L'administrateur doit examiner les effets sur les mainteneurs, automatisations et procédures de livraison avant d'activer `active`.

## Procédure administrateur, limitée et vérifiable

1. Vérifier **qui possède réellement l'autorité d'administration** du dépôt et qui représente le projet politique; ces mandats sont à consigner hors du dépôt public.
2. Revoir les paramètres du candidat JSON et les fonctionnalités disponibles selon le compte GitHub, notamment l'obligation de PR, l'interdiction de bypass, la validité des méthodes de fusion et les vérifications exigées. Vérifier la configuration des trois workflows au **nouveau SHA** si `main` a changé.
3. Ouvrir le dépôt **Settings → Rules → Rulesets**; préparer un ruleset visant `main` avec les mêmes clauses. Commencer **désactivé**, ou en mode `evaluate` si GitHub le propose. Ne pas activer sans accepter les conséquences pour le dépôt entier.
4. Confirmer la liste des checks dans le menu GitHub et leur émetteur GitHub Actions; vérifier qu'aucune collision de noms n'affecte les décisions et que les checks émis sont récents.
5. Activer `active` uniquement après décision de l'administrateur et examen de l'impact. **Ce jalon ne déclenche aucune requête POST/PATCH vers les règles GitHub.**
6. Exécuter une **PR témoin** non fusionnée, sans approbation, puis avec changements demandés et avec CI manquante, pour prouver que les trois situations empêchent la fusion sur `main`. Une simple réponse `protected:true` ne prouve pas la validité de ces scénarios.
7. Relever `GET /branches/main` et les rulesets, vérifier que les règles sont réellement actives, qu'elles visent la branche voulue et qu'aucune exception cachée ne permet le contournement. Si la lecture détaillée renvoie 403 à ce connecteur, l'administrateur doit apporter sa propre constatation.
8. Mettre à jour l'issue **#135** avec les preuves techniques **non sensibles**. Maintenir l'issue **#662** ouverte tant que les réviseurs des PR657 et PR638 n'ont pas déposé des avis formels au SHA final.

## Ce que P50V ne fait pas

- n'applique **aucune règle** GitHub;
- ne modifie **aucun workflow déjà en vigueur** sur `main`;
- ne soumet **aucune revue** et ne désigne aucun réviseur;
- ne fusionne **aucune PR** et n'active aucun déploiement ou nouveau formulaire;
- ne prouve pas les qualifications, le mandat juridique, la confidentialité de la messagerie ou la conformité électorale;
- ne modifie pas V3.40 et ne lève aucune porte institutionnelle, financière ou juridique.

**PR640 demeure NON FUSIONNABLE, même après activation des protections.** Les PR636, PR638, PR655, PR657 et toutes les PR de contrôle demeurent soumises aux revues et autorisations distinctes.

## Références opérationnelles

- [GitHub — règles disponibles pour les rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [GitHub — API de création d'un ruleset](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)
- [GitHub — dépannage des checks obligatoires](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)
- [Issue #135](https://github.com/M0rdr3x/BenoitCantin/issues/135) · [Issue #662](https://github.com/M0rdr3x/BenoitCantin/issues/662)

**Sortie P50V : modèle prêt pour revue administrateur, validation hors ligne et rapport traçable, avec statut institutionnel `NO_GO`. La seule preuve de protection effective sera une configuration serveur activée et testée par l'administrateur.**
