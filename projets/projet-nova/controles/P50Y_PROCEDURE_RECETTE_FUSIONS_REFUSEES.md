# Projet Nova — P50Y : procès-verbal de recette serveur et sortie des blocages administratifs

**17 octobre 2026 · Exécution réservée à un administrateur habilité · NO_GO**

## 1. Constat de départ vérifié

Le dernier relevé GitHub indique `main` au SHA `9ed5f70cbe7022f25a679346a1288701f3b09067`, `protected:false`, zéro required check et aucun ruleset actif. Les PR 638, 640, 657, 664, 665 et 666 demeurent ouvertes en brouillon et non fusionnées. Les issues [#135](https://github.com/M0rdr3x/BenoitCantin/issues/135) et [#662](https://github.com/M0rdr3x/BenoitCantin/issues/662) sont ouvertes : elles suivent respectivement l'activation effective d'une protection de branche et la désignation de réviseurs indépendants.

P50V ([PR 664](https://github.com/M0rdr3x/BenoitCantin/pull/664)) contient un modèle de ruleset **désactivé**. P50W ([PR 665](https://github.com/M0rdr3x/BenoitCantin/pull/665)) confirme les checks obligatoires candidats sur trois PR. P50X ([PR 666](https://github.com/M0rdr3x/BenoitCantin/pull/666)) constate que les protections attendues **ne sont pas installées**. P50Y prépare une **vraie recette d'acceptation par l'administrateur**, sans imaginer qu'elle a eu lieu.

## 2. Mesures préalables obligatoires

1. Confirmer les habilitations et l'organisation responsable du dépôt **partagé avec SINJIRA**, la disponibilité d'une autre personne autorisée à approuver une PR et les conséquences de l'obligation de revue. Une protection imposant l'avis d'une personne qui n'existe pas peut bloquer toutes les fusions.
2. Examiner la proposition P50V et les règles applicables à `main`. Exiger une PR, la suppression des approbations devenues périmées après push, une revue du dernier push par un autre auteur et la résolution des conversations. Interdire les suppressions et les force-push.
3. Vérifier les contextes universels exacts et leur émetteur : `no-committed-secrets`, `Contrat sécurité validation site`, `Contrat sécurité CI navigateur`; **GitHub Actions app 15368**. Ne pas rendre requis globalement les workflows P50T–P50Y filtrés par `paths:`.
4. Appliquer les règles dans **Settings → Rules → Rulesets** ou la protection de branche, **uniquement avec l'accord exprès de l'administrateur**. Vérifier le champ `bypass_actors` dans les permissions administratives réellement accessibles et les exceptions éventuelles, y compris celles des administrateurs.
5. Ne pas activer le modèle `enforcement:"disabled"` directement à partir du dépôt comme si ce fichier constituait déjà une règle serveur. Confirmer `protected:true` et les règles effectives **après** activation, avant la recette des refus.

Aucune des mesures ci-dessus n'a été effectuée automatiquement dans P50Y. Le présent document ne donne pas l'autorisation de changer la configuration du serveur.

## 3. Les trois expériences de refus de fusion à exécuter

Créer **trois PR témoins distinctes** sur une branche sans donnée personnelle ni secret, sous l'autorité de l'administrateur. Elles devront être **ouvertes et prêtes pour revue** (`draft:false`), sans fusion. Les garder séparées des véritables PR du Projet Nova et de SINJIRA. Ne jamais cliquer sur « Merge ».

**Identification contrôlée du périmètre des PR témoins (durcissement P50Z)** :
- branche source **dans le même dépôt** : `test/p50y-<identifiant>-<suffixe>`, avec exactement l'identifiant du scénario (`sans_revue`, `approbation_perimee`, `check_non_satisfait`) ;
- titre commençant par `[P50Y-CANARI:<identifiant>]` et branche cible `main` **du même dépôt** ;
- seules **1 à 3 modifications** de fichiers sous `projets/projet-nova/controles/canaris/`; aucun HTML public, workflow, configuration, manifeste ou fichier de données réels modifiés par les essais ;
- le validateur lit la **liste exhaustive des fichiers via l'API GitHub** : un inventaire paginé, incomplet ou de taille inattendue provoque un refus ;
- les PR historiques (notamment **#640**, #636, #638, #657) ne sont **jamais des PR témoins**, même si elles sont bloquées par GitHub.

Ces contraintes empêchent qu'un blocage accidentel d'une véritable PR du Projet Nova soit présenté comme la réussite d'un essai de protection. Elles n'autorisent ni la création de PR témoins par le pipeline ni une fusion.

| Essai | Conditions à établir | Refus attendu |
| --- | --- | --- |
| `sans_revue` | Les trois checks requis passent; aucun avis `APPROVED` valide sur le HEAD | La fusion reste bloquée **par manque d'approbation**, et non simplement parce que la PR est en brouillon ou en conflit |
| `approbation_perimee` | Une revue a été approuvée, puis un commit inoffensif a été ajouté | Le serveur exige une **nouvelle approbation**; l'ancienne ne permet plus la fusion |
| `check_non_satisfait` | PR sans données sensibles, avec un check requis réellement non satisfait et les revues requises déjà résolues | La fusion reste bloquée **à cause du check requis**, non d'une absence simultanée de revue |

L'administrateur doit vérifier la **raison** du blocage dans l'interface GitHub et ses règles, pas seulement la présence de l'état `mergeable_state:"blocked"`. Un conflit Git, une PR en brouillon ou une autre règle peuvent provoquer un blocage sans démontrer la bonne protection. Les PR témoins ne doivent jamais être fusionnées. Les fermer lorsque les preuves ont été examinées, selon la politique de conservation des journaux.

### Données à consigner, sans renseignements privés

Le fichier [`P50Y_PROCES_VERBAL_RECETTE_A_COMPLETER.json`](./P50Y_PROCES_VERBAL_RECETTE_A_COMPLETER.json) commence avec les trois expériences **non effectuées**. Il demande, pour chacune : numéro de la PR témoin, SHA testé, URL de la PR, constat booléen du blocage, confirmation booléenne de l'examen par le responsable habilité et URL GitHub de preuve associée (PR ou Actions). Ne pas renseigner un champ par anticipation.

Il comporte également trois déclarations qui nécessitent une réelle décision humaine :
- `protection_serveur_confirmee_par_admin` : les règles sont réellement installées et actives;
- `bypass_et_permissions_examines` : toutes les voies de contournement pertinentes ont été vérifiées;
- `relecteur_independant_disponible` : au moins une autre personne apte et habilitée à approuver le code est confirmée.

Les mandats, noms personnels, captures internes sensibles, clés et permissions secrètes ne doivent **pas** être déposés dans le dépôt public. Employer au besoin un registre interne distinct; seuls les constats non nominatifs sont destinés à cette proposition.

## 4. Validateur P50Y et vérification après activation

Le script `scripts/validate_nova_admin_canaries_p50y.py` effectue deux modes :
- **Mode normal sans réseau** : vérifie la structure de la grille de recette, trois identifiants uniques, les SHA valides, les URL du dépôt correct, la présence des observations humaines déclarées et la séparation entre preuve incomplète et dossier déclaré complet.
- **Mode `--live` en lecture seule** : interroge `GET /pulls/{number}` pour chacune des trois PR indiquées et vérifie l'état ouvert, `draft:false`, `merged:false`, le SHA du HEAD, `mergeable:true` (absence de conflit) et `mergeable_state:"blocked"`. Les erreurs et les écarts sont conservés comme obstacles.

Exemple de commande **uniquement après** installation des règles et constitution des PR témoins :

```bash
GITHUB_TOKEN=*** python scripts/validate_nova_admin_canaries_p50y.py \
  --dossier projets/projet-nova/controles/P50Y_PROCES_VERBAL_RECETTE_A_COMPLETER.json \
  --live --rapport p50y_resultat_local.json
```

Ne pas inscrire un jeton réel dans un fichier, une issue ou une ligne de commande partagée. Le token `GITHUB_TOKEN` doit être fourni par l'environnement et disposer uniquement d'un accès **lecture** aux PR publiques. Si le dépôt change de SHA ou si une PR témoin change, reprendre le contrôle à zéro.

**Durcissement P51A — corroboration indépendante du motif de refus** : le mode `--live` relève également les revues GitHub par `GET /pulls/{n}/reviews` et les checks du HEAD par `GET /commits/{sha}/check-runs`. Les données du rapport ne contiennent **que des agrégats**, jamais les noms des réviseurs.

- **`sans_revue`** : aucune revue substantielle soumise et **trois checks universels réussis** sur le HEAD. Une CI échouée invalide cet essai, car le refus pourrait provenir de la CI.
- **`approbation_perimee`** : une approbation antérieure d'une autre personne est observée sur un ancien SHA, **aucune approbation en cours** sur le HEAD et les **trois checks réussis**. L'administrateur doit confirmer dans l'interface l'ordre des commits et la véritable expiration de la revue. **Une revue marquée `DISMISSED` ne suffit pas à elle seule à prouver qu'elle était initialement `APPROVED` : une revue demandant des modifications peut également être écartée. Dans ce cas, conserver le scénario `RECETTE_REQUISE` jusqu'à obtention d'une preuve historique fiable, sans déduire une ancienne approbation du seul statut `DISMISSED`.**
- **`check_non_satisfait`** : une approbation indépendante valide sur le HEAD et **au moins un des trois checks requis non réussi ou manquant**. Une approbation d'auteur ou de bot ne suffit pas; un check émis par une autre application n'est pas accepté.

Le contrôle **refuse les listes paginées/incomplètes**, les checks homonymes multiples, les mauvais SHA et les checks hors de GitHub Actions `15368`. La présence d'un check manquant n'atteste pas, à elle seule, qu'une règle serveur l'exige : **la preuve administrateur reste obligatoire**.

**Important :** le mode `--live` refuse désormais les PR qui ne ciblent pas `main`, n'ont pas l'identifiant de scénario dans le titre et la branche, ou modifient des fichiers hors du répertoire de recette. Même un dossier rempli et un `mergeable_state:"blocked"` confirmé par API ne certifient **pas** la cause du refus. Une observation indépendante dans l'interface d'administration est obligatoire. Le programme renvoie toujours `NO_GO_AUTOMATIQUE` et n'émet jamais un GO institutionnel.

## 5. Interprétation de la CI P50Y

Le workflow proposé exécute **25 tests adversariaux** et confirme que la grille initiale affiche `RECETTE_REQUISE` pour chacun des trois essais. Un statut vert de ce workflow signifiera que **l'outil de recette fonctionne**, **pas** que les trois essais ont été effectués.

P50Y ne change aucune protection ni configuration GitHub et ne doit pas être ajouté comme check global obligatoire parce qu'il a des filtres `paths:`.

## 6. Décision et responsable suivant

Ne clore [l'issue #135](https://github.com/M0rdr3x/BenoitCantin/issues/135) qu'après activation réelle des protections et confirmation par l'administrateur des trois refus de fusion **sans fusion de PR témoin**. Ne clore [l'issue #662](https://github.com/M0rdr3x/BenoitCantin/issues/662) qu'après réception des vrais avis indépendants sur PR 657 et PR 638, avec vérification des nouveaux SHA si des changements surviennent.

Une protection réussie de `main` et des approbations de code ne suffisent **toujours pas** à établir le mandat légal, la conformité électorale, la protection de la messagerie ni l'autorisation de publication du Projet Nova. La base V3.40, toutes les portes institutionnelles et le verrou des flux de collecte demeurent inchangés.

**Statut : NO_GO. PR 640 : NE PAS FUSIONNER. Aucun déploiement, formulaire, paiement, don ou signature activé.**
