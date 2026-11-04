# P55I — Premier rapprochement chiffré budget-réalisations 2024, Ville de Québec

**Date de travail : 4 novembre 2026. Nature : base factuelle publique et rapprochement arithmétique, pas audit ni économie du Projet Nova.**

## Source et traçabilité

Publication officielle : [Ville de Québec, Rapport financier 2024](https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf), « Renseignements financiers consolidés — Sommaire des variations budgétaires sur les résultats », **page imprimée 7, page PDF indexée 6**. Le rapport identifie ce sommaire comme **non audité**.

Le rapport reprend également les quatre montants **réalisés en 2024** dans son « Sommaire des résultats à des fins fiscales consolidés » (page imprimée 13, page PDF indexée 12), soit 2 186 607 854 $, 262 872 891 $, 2 107 478 001 $ et 342 002 744 $. Cette seconde présentation est une **cohérence interne au même rapport**, non une confirmation indépendante par un autre organisme.

Les quatre lignes ci-dessous ont été **recopiées à partir de l'extraction de texte officielle consultable en ligne**. Les tentatives de capture visuelle via le navigateur et de récupération des octets dans le conteneur n'ont pas abouti. Par conséquent, **ni la mise en page des quatre chiffres, ni l'édition octet à octet, ni la signature de l'émetteur n'ont été revérifiées localement lors de P55I**. Les références SHA-256 historiques de P54Q demeurent inchangées. L'analyse n'est pas une expertise.

## Tableau de rapprochement

| Poste, exercice 2024 | Budget ($ CA) | Réalisations ($ CA) | Écart réel moins budget ($ CA) | Interprétation interdite |
|---|---:|---:|---:|---|
| Revenus de fonctionnement consolidés | 2 089 556 928 | 2 186 607 854 | +97 050 926 | Recette supérieure ≠ nouvelle économie |
| Revenus d'investissement consolidés | 403 091 050 | 262 872 891 | −140 218 159 | Recette inférieure ≠ coût compressible |
| Charges consolidées | 2 092 480 059 | 2 107 478 001 | +14 997 942 | Charge supérieure ≠ gaspillage démontré |
| Excédent de l'exercice | 400 167 919 | 342 002 744 | −58 165 175 | Écart d'excédent ≠ économie réalisable |

**Contrôles arithmétiques :**

- Budget : `2 089 556 928 + 403 091 050 − 2 092 480 059 = 400 167 919`.
- Réalisations : `2 186 607 854 + 262 872 891 − 2 107 478 001 = 342 002 744`.
- Variation : `97 050 926 − 140 218 159 − 14 997 942 = −58 165 175`.

Les variations publiées arrondies au dixième sont, dans le même ordre : **+4,6 %, −34,8 %, +0,7 %, −14,5 %**. Le script P55I recalcule ces proportions sur les entiers pour éviter de sommer des pourcentages de bases différentes.

## Explications fournies par le rapport — à ne pas remplacer par des hypothèses

La Ville attribue notamment les revenus de fonctionnement supérieurs aux droits de mutation immobilière, à l'aide ponctuelle aux transports collectifs, à certaines redevances et à des contributions ciblées. Elle précise que plusieurs de ces recettes supplémentaires sont **compensées par des charges correspondantes**. Les revenus d'investissement inférieurs sont reliés au report de la constatation de transferts de projets subventionnés. Les charges plus élevées sont notamment attribuées à des mesures de développement local et à des réparations/traitements de matières résiduelles occasionnés par des arrêts non planifiés au complexe de valorisation énergétique.

Ces explications sont **celles de la publication**; leur ventilation et leur caractère récurrent ou exceptionnel doivent encore être examinés, sur pièces et avec les notes du rapport. Il serait incorrect d'attribuer mécaniquement les 14,998 M$ de dépassement à des compressions réalisables, ou les 97,051 M$ de revenus additionnels à une marge fiscale permanente.

**Autres exclusions maintenues :** le redressement de **1 825 176 $** est un ajustement comparatif d'exercice antérieur dans le tableau des dépenses mixtes, distinct de ces quatre lignes, et ne constitue pas un gain de 2024. Les éliminations de consolidation déjà comptabilisées entre Ville, RTC et SOMHAC ne deviennent pas de nouvelles économies.

## Portée technique

Fichiers de P55I :
- `P55I_REFERENTIEL_ECARTS_BUDGET_REALISATION_2024.json` — quatre lignes et identités immuables, source et limites de preuve.
- `scripts/rapprocher_sommaire_budgetaire_nova_p55i.py` — contrôles d'égalité exacts en dollars, contribution des charges de signe opposé, pourcentages à une décimale.
- `scripts/tests/test_rapprocher_sommaire_budgetaire_nova_p55i.py` — tests synthétiques de calculs et de refus de faux gains.
- `.github/workflows/validate-nova-p55i.yml` — validation en CI sans fichiers PDF privés.

Exécuter depuis la racine du dépôt, avec Python et les dépendances déjà utilisées par P54Q :

```bash
python scripts/rapprocher_sommaire_budgetaire_nova_p55i.py \
  --bilan-public /hors_git/p55i_bilan.json \
  --table-public /hors_git/p55i_tableau.json
```

Le programme n'accède à aucun site Internet et n'utilise aucune pièce privée. Il garantit **la cohérence du calcul sur les quatre données recopiées**, pas l'identité octet des PDF. Un tableau modifié, une addition inexacte, un doublon de poste ou un chemin de sortie existant entraîne un refus. `--exiger-certification` renvoie volontairement le code **3**.

## Critères pour une véritable économie future

Un gain ne pourrait être retenu qu'après identification **des crédits réellement accessibles**, des services rendus, du coût net après mesures transitoires, des flux interorganismes éliminés, de la récurrence, de l'impact sur les recettes/dépenses connexes, de l'autorité juridique nécessaire, et d'une contre-vérification indépendante. Ce calcul doit être fait **séparément** pour le Québec dans le Canada et pour un Québec souverain hypothétique.

**État conservé :** quatre dossiers P54E et une observation de date probable non clôturés; 40 tâches P54N, dix blocages P54O, 96 P54B et huit P54C sans attestation; aucun mandat professionnel signé; aucune économie certifiée; aucune réduction d'effectifs ni de services publics autorisée par ces chiffres. Préservation du pouvoir d'achat. Aucune modification SINJIRA ni fusion dans `main`.

**Décision : `NO_GO_AUTOMATIQUE`.**
