# P55Q — Premières assiettes imposables historiques vérifiées du Québec

**5 novembre 2026 — étude candidate, deux années d’imposition distinctes, sans taux Nova proposé.**

## Décision à éclairer

Après P55O et P55P, les prévisions du budget du Québec donnent un **montant de recettes**, mais non les **revenus imposables sur lesquels une nouvelle structure fiscale pourrait éventuellement s’appuyer**. Le jalon P55Q introduit deux véritables sources statistiques publiques de revenu imposable — **sans les additionner**, puisqu’elles ne décrivent **pas la même année** et ne constituent pas une assiette harmonisée du régime projeté.

## Source A : particuliers, année d'imposition 2023

[Ministère des Finances du Québec, Statistiques fiscales des particuliers 2023, tableau A.7](https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-comp-impot.asp). [Communiqué officiel de publication, 13 février 2026](https://www.quebec.ca/nouvelles/actualites/details/statistiques-fiscales-des-particuliers-annee-dimposition-2023-68514).

| Élément de la déclaration, tous les particuliers | Montant |
|---|---:|
| Déclarations produites | **7 220 140 contribuables** |
| Revenu total | **427 915 M$** |
| Déductions relatives au revenu net | 40 892 M$ |
| Revenu net | 387 023 M$ |
| Déductions relatives au revenu imposable | 14 761 M$ |
| **Revenu imposable 2023** | **372 261 M$** |
| Impôt sur le revenu imposable (avant crédits) | 62 148 M$ |
| Crédits non remboursables | 21 358 M$ |
| Impôt à payer | 40 790 M$ |
| Crédits remboursables | 9 305 M$ |
| Impôt à payer moins crédits remboursables | 31 485 M$ |

**Note de précision :** les valeurs sont publiées **arrondies au million**. Ainsi, `387 023 − 14 761 = 372 262`, alors que la somme officielle du revenu imposable est **372 261 M$**. L'écart de **1 M$** tient à la présentation arrondie. Un contrôle rigoureux ne doit **ni inventer une correction ni remplacer silencieusement l'un des totaux**.

Le revenu total, le revenu net, le revenu imposable, l'impôt calculé et l'impôt effectivement à payer sont **cinq concepts distincts**. Aucune identité entre le revenu imposable 2023 et les recettes d'impôt prévues au budget **2026–2027** ne peut être présumée.

## Source B : sociétés, année d'imposition 2021

[Ministère des Finances du Québec, Statistiques fiscales des sociétés, année d'imposition 2021](https://www.quebec.ca/gouvernement/finances-publiques/revenus/donnees-fiscales/statistiques-fiscales-societes).

| Élément des statistiques des sociétés | Montant |
|---|---:|
| Déclarations de revenus traitées | **564 599** |
| **Revenu imposable attribué au Québec** | **95 784 M$** |
| Revenu imposable mondial des sociétés présentes au Québec | 231 518 M$ |
| Impôt québécois sur le revenu des sociétés | 10 000 M$ |
| Cotisations des sociétés au Fonds des services de santé | 5 327 M$ |
| Total impôts et cotisations | 15 327 M$ |
| Crédits d'impôt | 2 468 M$ |
| Impôts et cotisations nets des crédits | 12 860 M$ |
| Sociétés n'ayant pas d'impôt sur le revenu à payer | **322 020** |

**Distinction essentielle :** le revenu imposable **mondial** ne constitue **pas** l'assiette taxable par Québec. Le Québec ne peut pas présumer imposer la totalité des 231 518 M$ mondiaux. Le revenu imposable attribué aux activités réalisées au Québec était de **95 784 M$ en 2021**, et non une prévision pour 2026 ou 2027.

Le calcul arrondi `15 327 − 2 468 = 12 859 M$` diffère de **1 M$** du total officiel publié de **12 860 M$**. Cela illustre encore les effets d'arrondissement; le programme accepte uniquement une tolérance d'un million pour ce type de contrôle d'agrégats.

## Trois années à ne pas amalgamer

| Série utilisée | Année ou période | Nature |
|---|---|---|
| Statistiques fiscales des sociétés | **2021** | Revenu imposable attribué au Québec et impôt constaté |
| Statistiques fiscales des particuliers | **2023** | Revenu imposable déclaré et impôts de l'année d'imposition |
| Budget du Québec P52C / P55P | **2026–2027** | **Prévisions** de recettes du système actuel |

**Il est formellement interdit de calculer une assiette commune en faisant `372 261 + 95 784`**, parce que les années sont différentes, les définitions fiscales sont distinctes et les effets d'un éventuel nouvel impôt ne sont pas définis.

De même, les **65 327 M$ de prévisions actuelles** (impôt particuliers et sociétés 2026–2027) ne sont **pas** le produit des bases historiques ci-dessus au moyen d'un taux unique déterminable. La réserve de risque budgétaire **40 731 M$** de P55P ne devient donc **pas** un taux à appliquer aux revenus imposables historiques.

## Travaux requis pour proposer des taux responsables

Les dix dossiers Q01–Q10 du référentiel encadrent : l'harmonisation des années, les statistiques par revenus et régions, les sociétés par taille/secteur, la compétence législative provinciale et fédérale, les mécanismes d'une éventuelle transition constitutionnelle, la définition des assiettes et crédits de Nova, le financement municipal, les effets sur les ménages/entreprises, la fiscalité anti-paradis et la validation professionnelle externe.

**Ce qui est réellement gagné à P55Q :** des **repères historiques fiables et datés**, utiles à la préparation de la modélisation. Les **600 montants P52B restent inconnus**, le modèle décennal ne calcule aucun taux fiable, les économies de P55P ne sont pas démontrées et le **baromètre global P55N reste à 53 %** (appréciation éditoriale, non certification).

## Contrôles et décision

`scripts/controler_assiettes_historiques_nova_p55q.py` vérifie les montants source, les années, les effets d'arrondissement, les 30 protections anti-amalgame et le chaînage aux évaluations P55P, P55O et P55N. Exécution sans accès réseau, sans données personnelles et sans remplacement de valeurs inconnues :

```bash
python scripts/controler_assiettes_historiques_nova_p55q.py \
  --bilan-public /hors_git/p55q_bilan_public.json \
  --table-public /hors_git/p55q_table_public.json
```

L'option `--exiger-taux-demontre` renvoie volontairement un refus **3**. Les contrôles ne certifient pas une politique publique, n'inventent ni recette anti-évasion ni taxe fédérale abolie et n'annoncent aucune réduction d'emploi, de service ou de pouvoir d'achat.

**Statut : `NO_GO_AUTOMATIQUE`.** Le programme reste candidat, deux régimes constitutionnels distincts, SINJIRA inchangé, aucun contact, mandat, dépense ni fusion dans `main`.
