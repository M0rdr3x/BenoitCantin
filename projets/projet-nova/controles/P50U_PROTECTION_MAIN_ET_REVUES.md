# Projet Nova — P50U : protection de main, séparation des pouvoirs et revues indépendantes

**16 octobre 2026 — Dossier d'exécution et de décision humaine — NO_GO**

## 1. Pourquoi P50U est nécessaire

P50Q et P50R ont validé les correctifs sur des versions figées. P50S a montré l'absence de reviews, et P50T a correctement fait échouer sa porte humaine, tout en réussissant les tests logiciels. Il reste un risque de gouvernance beaucoup plus direct : **la branche principale peut ne pas empêcher des changements non revus**.

Une procédure documentaire, un `CODEOWNERS` ou un workflow qui échoue *après une PR* ne constitue **pas**, en lui-même, une règle serveur empêchant de fusionner. P50U vérifie donc l'état réel de `main` avant de préparer sa sécurisation par un administrateur habilité.

## 2. Preuves recueillies dans GitHub le 16 octobre 2026

| Objet | Valeur directement constatée | Portée |
| --- | --- | --- |
| `GET /repos/M0rdr3x/BenoitCantin/branches/main` | `protected: false` | **Aucune protection de branche active déclarée par cette API** |
| Même endpoint, `protection.enabled` | `false` | Confirmation du constat |
| `required_status_checks` | `enforcement_level: off`, `checks: []`, `contexts: []` | **Aucun contrôle CI requis par cette protection** |
| `GET /repos/.../rulesets?includes_parents=true` | `[]` | Aucun ruleset visible |
| `.github/CODEOWNERS` sur `main` | règle générale `* @M0rdr3x` | **Un seul propriétaire désigné**, pas deux réviseurs indépendants |
| `GET /repos/.../branches/main/protection` | 403 pour le connecteur | Les détails administratifs de cette route ne sont **pas accessibles** |
| Commit `main` | `9ed5f70cbe7022f25a679346a1288701f3b09067` | Source figée de l'observation |
| [Issue #135](https://github.com/M0rdr3x/BenoitCantin/issues/135) | Ouverte | Problème de protection **déjà enregistré** dans le dépôt |
| [Issue #662](https://github.com/M0rdr3x/BenoitCantin/issues/662) | Ouverte, non assignée | Désignation et mandat réels de relecteurs indépendants |

**Conclusion technique :** sur les surfaces GitHub lisibles, `main` n'est actuellement pas protégée. L'absence d'accès à l'endpoint détaillé 403 ne doit pas être utilisée pour minimiser ce fait, puisque l'endpoint de branche confirme explicitement `protected:false`.

### Risque de monopole de revue

Le fichier `CODEOWNERS` ne compte qu'un compte associé à la règle `*`. Cela ne prouve **ni** que ce compte est le seul collaborateur du dépôt, **ni** qu'une deuxième personne qualifiée existe, **ni** qu'une règle GitHub oblige le propriétaire à approuver. Ce défaut interdit d'affirmer qu'une double revue indépendante est en place.

Le dépôt sert aussi à d'autres travaux que Projet Nova, dont SINJIRA. Toute modification globale des règles de `main` doit être coordonnée avec les responsables de l'ensemble du dépôt.

## 3. Ordonnance destinée à l'administrateur habilité — pas de modification automatique

1. Répondre dans la **[question #135](https://github.com/M0rdr3x/BenoitCantin/issues/135)**, déjà ouverte, en confirmant si les protections GitHub de `main` peuvent être activées. Éviter un doublon de suivi.
2. Dans **GitHub → Settings → Rules → Rulesets** ou **Settings → Branches**, créer une règle visant **`main`** : pull request obligatoire, approbation(s) préalable(s) de personnes autorisées, interdiction des mises à jour directes non autorisées, absence de force-push et de suppression de la branche.
3. Prévoir au minimum une **revue indépendante de l'auteur** et une nouvelle approbation si le code change; choisir le nombre exact d'approbations avec la gouvernance réelle. Une approbation par une personne ayant un conflit d'intérêts ne constitue pas automatiquement un contrôle indépendant.
4. Ne sélectionner comme **checks requis à l'échelle du dépôt** que des checks stables effectivement émis pour **toutes** les PR visées. L'issue #135 mentionne comme candidats `no-committed-secrets`, `Contrat sécurité validation site` et `Contrat sécurité CI navigateur`. Les noms et la présence doivent être **revérifiés avec l'administrateur** avant configuration.
5. **Ne pas rendre obligatoire globalement** un workflow restreint par `paths:` (comme les contrôles spécifiques P50T/P50U) : il manquerait sur des PR sans fichier concerné et risquerait de bloquer de manière incohérente le dépôt.
6. Faire un test de contrôle sur une **PR de démonstration non fusionnée** : vérifier qu'une revue manquante et un check requis manquant empêchent réellement la fusion, puis qu'une validation réclamée après une modification redevient nécessaire.
7. Faire confirmer les règles avec un **GET GitHub actualisé**, enregistrer les paramètres généraux non sensibles et ajouter une clôture vérifiable à l'issue #135. Ne pas publier des informations d'accès, secrets ni identités privées.
8. **Ne pas interpréter l'activation de protections techniques comme une décision de publier Projet Nova** : les habilitations juridiques, la confidentialité réelle des courriels et le plan de retour arrière doivent suivre leur contrôle autonome.

**L'assistant et le pipeline P50U n'éditent pas les règles d'administration de GitHub.** Les permissions de ce connecteur ne donnent pas ici accès à la création ou modification des protections; l'administrateur réel doit appliquer la règle dans GitHub.

## 4. Revues humaines prioritaires : tâche de suivi #662

L'issue [#662](https://github.com/M0rdr3x/BenoitCantin/issues/662) est dédiée à la **désignation et au mandat effectifs** des réviseurs de deux PR essentielles, sans assignee inventé.

| PR | Décision à rendre par un réviseur compétent | SHA du correctif à revoir |
| --- | --- | --- |
| [657](https://github.com/M0rdr3x/BenoitCantin/pull/657) | Scanner de participation : URI encodées, liens de paiements et faux positifs, limites statiques | `f67abe43b7223d0f59ee1efb6cf883d558eddfb5` |
| [638](https://github.com/M0rdr3x/BenoitCantin/pull/638) | Identité publique : Projet Nova, futur Parti Nova seulement conditionnel, statuts non adoptés et manifeste | `e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e` |

Après ces deux revues, les dépendances PR655, PR636 et la simulation PR659 pourront être examinées par les responsables habilités. Il faut **refaire les tests et revues** si un SHA change; la CI P50R ne prouve rien sur de nouveaux octets.

**La PR 640 est réservée aux expériences de validation. NE PAS FUSIONNER.**

## 5. Nouveau contrôle automatique P50U

Le script `scripts/audit_nova_protection_main_p50u.py` lit :
- `GET /branches/main` et sa réponse `protected`, `required_status_checks`;
- la liste des rulesets visibles et activés;
- la règle globale du fichier public `.github/CODEOWNERS`, **en ne publiant que le nombre de comptes**.

La GitHub Action P50U se décompose volontairement en :
1. **Audit documentaire** : tests unitaires, lecture API réelle, rapport JSON non nominatif conservé 7 jours; le job doit réussir s'il observe correctement la situation, même défavorable.
2. **Verrou constatant un défaut de protection** : **échec explicite** tant que la protection serveur reste absente. Cette CI ne rend toutefois pas `main` protégée par elle-même et n'est pas à configurer comme check global requis en raison de son filtre `paths:`.

Tout retour d'erreur des API doit mener à un état inconnu bloquant, pas à une validation par défaut. La sortie du contrôle conserve `NO_GO_AUTOMATIQUE`, même si les règles deviennent conformes : la revue indépendante et les pouvoirs restent des décisions humaines.

## 6. Portes de décision et clôture P50U

| Condition | État au 16 octobre 2026 |
| --- | --- |
| Existence d'une protection serveur empêchant une fusion non revue | **NON** selon les API accessibles |
| Contrôles de statut obligatoires sur `main` | **AUCUN** |
| Propriétaire(s) CODEOWNERS indépendants pour Projet Nova | **NON ATTESTÉ(S)** |
| Responsable réellement habilité à imposer la protection | **À CONFIRMER** |
| Demandes de revue et approbations PR657 et PR638 | **ABSENTES** |
| Compatibilité technique P50Q/P50R | **VÉRIFIÉE sur les SHA passés** |
| Autorisation institutionnelle de publication | **NO_GO** |

P50U ne doit pas être considéré comme une excuse pour remettre les correctifs en production. La **prochaine action humaine décisive** est l'application et la vérification de la protection serveur de `main` via l'issue #135, ainsi que la nomination de vrais réviseurs via l'issue #662. La base V3.40, les W0/W1/W2–W4, les preuves électorales et financières et les interdictions de collecte restent inchangées.

*Aucune opération de fusion, de déploiement, de collecte ou de modification des permissions GitHub n'est autorisée par ce document.*
