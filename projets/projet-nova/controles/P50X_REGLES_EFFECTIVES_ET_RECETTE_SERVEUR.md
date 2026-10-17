# Projet Nova — P50X : preuve des règles GitHub réellement applicables

**17 octobre 2026 · Dossier technique de lecture seule · Aucune fusion ou publication autorisée**

## 1. Situation de départ

Le [modèle P50V, PR 664](https://github.com/M0rdr3x/BenoitCantin/pull/664), est un JSON `enforcement: disabled` validé par des tests. Le [précontrôle P50W, PR 665](https://github.com/M0rdr3x/BenoitCantin/pull/665), a confirmé 9 checks réellement réussis sur les PR 636, 638 et 664 au SHA attendu. Ni un modèle JSON ni neuf succès de CI ne constituent une **protection serveur effective**.

Relevé initial sur `main` au SHA `9ed5f70cbe7022f25a679346a1288701f3b09067` :
- `GET /branches/main` : `protected: false`, aucun check requis;
- `GET /rulesets?includes_parents=true` : aucun ruleset visible;
- détail de la branch protection par l'intégration courante : 403, permissions insuffisantes;
- la preuve d'un rejet effectif de merge **n'existe pas**;
- [#135](https://github.com/M0rdr3x/BenoitCantin/issues/135) suit la protection serveur; [#662](https://github.com/M0rdr3x/BenoitCantin/issues/662) suit la désignation des réviseurs indépendants.

## 2. Nouveau contrôle P50X

`scripts/audit_nova_effective_rules_p50x.py` relève ces trois sources GitHub, sans mutation :

1. `GET /repos/M0rdr3x/BenoitCantin/branches/main` — SHA exact et indicateur de protection;
2. `GET /repos/M0rdr3x/BenoitCantin/rulesets?includes_parents=true`, suivi d'un `GET /rulesets/{id}` pour tout ruleset actif — paramètres réellement installés, conditions sur `main`, blocages d'historique, de suppression, de revue et de CI;
3. `GET /repos/M0rdr3x/BenoitCantin/rules/branches/main` — **règles actives effectivement applicables** à la branche, même lorsque configurées à d'autres niveaux. Les règles `disabled` et `evaluate` ne sont pas comptées comme actives.

Un refus de lecture (403 ou autre) ne devient **jamais une preuve positive**. L'API GitHub peut masquer `bypass_actors` aux accès sans droit de modification de ruleset : toute absence de ce champ est un **état non attesté**, contrairement à une liste vide explicitement fournie par une autorité habilitée.

Le script contrôle le modèle P50V par son nom et le commit exact déjà validé, puis demande la présence réelle des quatre catégories de règles : PR, checks exigés, absence de force-push et interdiction de suppression. La règle de PR doit exiger une approbation, le dernier push par une autre personne, le rejet des approbations périmées et la résolution des conversations. Les checks exigés doivent inclure `no-committed-secrets`, `Contrat sécurité validation site` et `Contrat sécurité CI navigateur`, chacun émis par **GitHub Actions (app 15368)**, avec une politique stricte.

**Le script n'active aucune règle, n'effectue aucune fusion et renvoie toujours `NO_GO_AUTOMATIQUE`.**

## 3. Deux résultats distincts dans GitHub Actions

Le workflow `validate-nova-p50x.yml` contient :
- **relevé-documentaire** : compilation, 20 tests hors réseau puis observation des trois API en lecture seule. Le job peut réussir en constatant l'absence de protection : il prouve uniquement l'exactitude de l'observation;
- **porte-administrateur-bloquante** : échec de sortie **3** attendu si `main` n'est pas protégée, si le ruleset n'est pas actif et conforme au candidat, si les exceptions ne sont pas vérifiables ou si les règles effectives sont inaccessibles/incomplètes. Si ces informations deviennent visibles et conformes, cette porte peut réussir **sans autoriser une fusion ni une publication**.

**Important :** le workflow P50X est déclenché sur certains chemins seulement. Il ne faut pas le rendre requis globalement pour toutes les PR : sur une PR hors de ces chemins, il pourrait manquer et bloquer arbitrairement le dépôt.

Les rapports JSON non nominatifs sont conservés sept jours. Ils ne contiennent aucun compte d'utilisateur, jeton, courriel ni donnée issue de la messagerie.

## 4. Dernière preuve qui ne peut pas être fabriquée par la CI

Une fois le ruleset activé par **l'administrateur réellement habilité**, trois situations doivent être vérifiées directement dans GitHub avec une **PR témoin non fusionnée** :

- PR sans approbation : vérifier la mention « fusion bloquée » malgré les checks réussis;
- modification après une approbation : vérifier que la revue antérieure ne suffit plus et qu'une nouvelle approbation est exigée;
- check requis non satisfait : vérifier que la fusion reste bloquée, sans déclencher un déploiement.

Ces essais doivent être organisés par les mainteneurs pour éviter de fusionner accidentellement une PR témoin. Les permissions effectives, les éventuels bypass administrateur et les impacts sur les livraisons **SINJIRA et Projet Nova** sont à confirmer dans l'interface d'administration.

Une lecture `protected: true`, même assortie de règles actives, **ne remplace pas ces tests de refus réel**. GitHub peut également cacher des exceptions au lecteur; un administrateur devra alors confirmer les détails par une preuve non sensible.

## 5. Priorités après P50X

| Priorité | Preuve demandée | Responsable |
| --- | --- | --- |
| A | Protection serveur réellement installée, avec règles adaptées au dépôt partagé | Administrateur habilité — issue #135 |
| B | Exceptions de contournement et permissions effectivement vérifiées | Administrateur habilité |
| C | Trois essais de blocage réels, sans fusion | Mainteneur responsable |
| D | Revues de code PR657 et PR638 sur les SHA finaux, puis chaîne PR655 → PR636 | Réviseurs mandatés — issue #662 |
| E | Habilitations institutionnelles, obligations électorales et protection des données | Autorités/professionnels qualifiés |

**PR 640 : NE PAS FUSIONNER.** Aucun nouveau flux de signature, adhésion, don, paiement, formulaire ou collecte. Les statuts Projet Nova V3.40 et les portes W0/W1/W2–W4, E26, pouvoirs et finances ne changent pas.

**Décision P50X : contrôle technique uniquement; maintien strict du NO_GO institutionnel et de publication.**

### Références techniques

[GitHub REST API — Repository rulesets](https://docs.github.com/en/rest/repos/rules) décrit le recensement des rulesets, leur configuration, le GET des règles applicables à une branche et les limites de visibilité du champ `bypass_actors`.
