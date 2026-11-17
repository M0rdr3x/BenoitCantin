# Projet Nova — P50W : précontrôle réel avant application de la protection GitHub

**16 octobre 2026 · Modèle P50V NON activé · Aucune décision de fusion ni publication**

## Pourquoi ce contrôle est utile

La PR [#664 — P50V](https://github.com/M0rdr3x/BenoitCantin/pull/664) fournit un modèle JSON désactivé de protection de `main`, une validation statique et un dossier administrateur. La PR [#663 — P50U](https://github.com/M0rdr3x/BenoitCantin/pull/663) a confirmé le défaut serveur : `main.protected=false`, 0 check requis, aucun ruleset actif visible. Les issues [#135](https://github.com/M0rdr3x/BenoitCantin/issues/135) (protection effective de la branche) et [#662](https://github.com/M0rdr3x/BenoitCantin/issues/662) (véritables réviseurs) demeurent **ouvertes**.

La question P50W est plus opérationnelle : les trois checks que le modèle entend imposer sont-ils **effectivement émis par GitHub Actions, sur des PR actuellement en brouillon, au commit exact** ? Sans cette preuve, l'activation de checks requis pourrait verrouiller les PR ou accepter une provenance ambiguë.

## Observations directes au départ du jalon

| PR d'échantillon | SHA vérifié | `no-committed-secrets` | `Contrat sécurité validation site` | `Contrat sécurité CI navigateur` |
| --- | --- | --- | --- | --- |
| #636, participation | `6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb` | succès | succès | succès |
| #638, identité | `e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e` | succès | succès | succès |
| #664, modèle de règles | `d8acb58c2829cf990d7c77614b3f640369fdbdca` | succès | succès | succès |

Les **9 check-runs** ont été constatés dans `GET /commits/{sha}/check-runs`, de l'application **GitHub Actions `15368`**, au `status=completed` et `conclusion=success`.

Les deux méthodes sélectionnées dans le modèle (`merge` et `squash`) correspondent aussi à des options de fusion activées sur ce dépôt. Les pages et les PR ne sont pas modifiées par ce relevé.

**Limite essentielle :** neuf succès sur trois PR ne garantissent pas les futures PR. Les jobs universels et leur déclenchement doivent être revérifiés à l'activation effective des rulesets. L'obtention d'un `APPROVED` sur une PR ne certifie pas le mandat de gouvernance d'un réviseur.

## Périmètre du script P50W

Le script `scripts/preflight_nova_ruleset_p50w.py` :
1. récupère le modèle désactivé P50V à son SHA immuable, **sans déclencher d'activation**;
2. vérifie `main`, le SHA attendu, son statut `protected` et les rulesets visibles;
3. vérifie que les PR de test #636, #638 et #664 sont toujours ouvertes, en brouillon et sur le SHA exact;
4. vérifie que les PR prioritaires #657 et #638 n'ont pas changé de SHA ou d'état;
5. relève **les nombres seulement** de demandes et de revues GitHub des deux PR prioritaires, sans conserver d'identifiants des personnes;
6. refuse toute preuve ambiguë : checks d'une autre application, mauvaise empreinte Git, statut `skipped`, check absent ou émis deux fois sous le même contexte;
7. maintient la décision `NO_GO_AUTOMATIQUE`, avec `ruleset_installe_par_ce_controle=false`, que les neuf checks réussissent ou non.

Le workflow P50W réalise une exécution en lecture seule avec `contents:read`, `checks:read` et `pull-requests:read`. Il produit un rapport JSON non nominatif, conservé au maximum **7 jours**. Le validateur dispose de **20 tests fictifs** et d'une preuve opérationnelle qui doit être examinée dans les journaux GitHub Actions.

## Risques de verrouillage et mesures obligatoires

**Un ruleset correct ne suffit pas si aucun autre contributeur habilité ne peut approuver une PR.** Le fichier `.github/CODEOWNERS` affiche un seul compte propriétaire. Ce fait ne prouve pas qu'aucune autre personne n'ait accès au dépôt, mais les deux revues prioritaires sont toujours à obtenir. Avant activation, l'administrateur doit vérifier des personnes réelles, distinctes de l'auteur, dotées de la compétence et des droits nécessaires.

Un administrateur autorisé doit ensuite :
1. consulter l'issue **#135** et le modèle P50V pour confirmer les droits de gestion et les conséquences sur **SINJIRA autant que sur Projet Nova**;
2. vérifier la disponibilité des réviseurs et leur mandat dans l'issue **#662**, hors du dépôt pour les documents sensibles;
3. vérifier les noms de jobs et leur émetteur (`integration_id=15368`) au moment de la configuration;
4. préparer et appliquer le ruleset serveur **seulement après décision expresse**; ne pas exiger globalement une CI filtrée par `paths:`;
5. tester dans GitHub, **sans fusion**, qu'une PR sans revue, une PR avec nouvelle modification et une PR avec check manquant ne peuvent pas passer;
6. relever après activation `main.protected`, les rulesets effectivement actifs, les exceptions et le refus réel des merges non conformes;
7. reprendre P50W et vérifier qu'il ne confond pas l'existence de checks avec des approbations ou un GO institutionnel.

GitHub documente la structure des règles et l'option `integration_id` des required status checks : [REST API — Repository Rulesets](https://docs.github.com/en/rest/repos/rules) et [Available Rules for Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

## Décisions et suite

**P50W ne remplace ni P50U ni P50T.** Il complète l'analyse de risque avant activation en confirmant les neuf checks réels sur des SHA précis. La prochaine opération permettant de franchir un véritable obstacle appartient à l'administrateur du dépôt et aux réviseurs habilités : **activer la protection serveur après essai contrôlé et obtenir les revues formelles.**

Aucune création de ruleset serveur, fusion, déploiement, collecte, donation, demande d'adhésion, signature ou émission d'une autorisation juridique. Le périmètre institutionnel V3.40 et toutes ses portes reste inchangé. **PR #640 : NE PAS FUSIONNER.**

**Décision : NO_GO — modèle P50V désactivé, et `main` encore dépourvue de protection serveur au dernier relevé.**
