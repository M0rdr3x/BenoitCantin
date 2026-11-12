# Projet Nova — P50Z : preuve adversariale indépendante des PR témoins

**17 octobre 2026 · Correctif ciblé de P50Y · Décision NO_GO**

## Défaut identifié

La [PR667 — P50Y](https://github.com/M0rdr3x/BenoitCantin/pull/667) a livré un outil de recette pour trois PR témoins non fusionnées. Son vérificateur contrôlait le numéro, le HEAD, l'état ouvert, `draft:false`, `merged:false`, `mergeable:true` et `mergeable_state:blocked`, mais **ne vérifiait ni la branche cible, ni la nature de la PR témoin, ni ses fichiers réellement modifiés**. Un administrateur aurait donc pu associer au dossier une **vraie PR du projet bloquée pour une autre raison**, puis la traiter comme un essai de protection.

Ce défaut n'accordait pas de GO de publication, déjà explicitement interdit, mais il rendait **la preuve de recette potentiellement trompeuse**.

## Correctif logiciel soumis à une vraie revue

La [PR668 — P50Z](https://github.com/M0rdr3x/BenoitCantin/pull/668) est un **enfant en brouillon de PR667**. Elle renforce exactement les fichiers de P50Y, plutôt que créer une autre règle de contrôle non intégrée :

1. La PR témoin doit viser `main` du dépôt `M0rdr3x/BenoitCantin`, et provenir du même dépôt (pas d'un fork non contrôlé).
2. Le titre doit commencer par `[P50Y-CANARI:<identifiant du scénario>]`; la branche doit commencer par `test/p50y-<identifiant du scénario>-`.
3. Ses modifications doivent concerner **1 à 3 fichiers** sous `projets/projet-nova/controles/canaris/` uniquement, et être vérifiées par `GET /pulls/{numero}/files?per_page=100` à un nombre exhaustif correspondant au total déclaré par l'API.
4. Une vraie PR Projet Nova, un autre dépôt, une autre cible, un titre erroné, un inventaire incomplet ou la modification de HTML public ne peuvent plus servir de PR témoin.
5. Le caractère `blocked` ne prouve toujours **pas la cause du blocage**. L'administrateur doit continuer de vérifier réellement le refus dû aux règles de revue et de CI; la décision reste `NO_GO_AUTOMATIQUE`.

## Vérification indépendante sur des empreintes figées

| Version | Commit exact | Tests |
| --- | --- | --- |
| P50Y initial, PR667 | `0945b7c76941bbde35bab926b4bfdda0442ae62b` | 25 |
| P50Z corrigé, PR668 | `9e8d08b2a4d097e9609320cef5e9167ab3fe64bf` | 37 |

Le script `scripts/compare_nova_canary_safety_p50z.py` crée **neuf scénarios entièrement fictifs**, tous déclarés corrects par le validateur initial mais devant être rejetés par la version renforcée : mauvaise branche cible, autre dépôt cible, fork source, vraie branche de code, titre non témoin, mauvais scénario, fichier HTML public, zéro fichier et quatre fichiers.

Un contrôle négatif vérifie qu'une PR témoin **conforme** conserve le statut `DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT`, jamais un GO. Ainsi, le correctif n'interdit pas toute preuve légitime.

Le workflow `.github/workflows/validate-nova-p50z.yml` récupère les **deux commits immuables**, exécute leurs suites propres, compare les neuf sondes et conserve un rapport JSON non nominatif. Il n'a aucune permission de fusion, d'installation d'un ruleset ou d'accès aux données d'un utilisateur.

## Règles de gouvernance inchangées

- [#135 — protection effective de main](https://github.com/M0rdr3x/BenoitCantin/issues/135) : toujours à réaliser par une personne habilitée et à tester par trois vrais essais sans fusion.
- [#662 — réviseurs indépendants](https://github.com/M0rdr3x/BenoitCantin/issues/662) : toujours à désigner et à faire intervenir sur PR657 et PR638.
- PR668 est **non fusionnée**. Une éventuelle intégration dans la branche PR667 doit être approuvée par les responsables réellement habilités, puis testée sur les nouveaux SHA.
- Ce contrôle n'exécute aucune PR témoin, ne touche ni `main` ni le site et n'autorise aucun formulaire, paiement, don, adhésion, signature ou collecte.
- **PR640 : NE PAS FUSIONNER. Base maîtresse V3.40 et statuts institutionnels inchangés.**

**La conclusion technique de P50Z est vérifiable dans les journaux CI; elle ne doit pas être annoncée comme réussie avant l'exécution effective de GitHub Actions.**