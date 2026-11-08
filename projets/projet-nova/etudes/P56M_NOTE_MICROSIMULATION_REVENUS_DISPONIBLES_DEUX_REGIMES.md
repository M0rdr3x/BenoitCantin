# Projet Nova — P56M : première architecture exécutable de comparaison du revenu disponible

**7 novembre 2026. Étude technique candidate; projet non adopté. Statut : `NO_GO_AUTOMATIQUE`.**

## 1. Objet, portée et définition

Le Projet Nova souhaite limiter sa fiscalité proposée à deux piliers, dans la mesure de leur légalité et de leur viabilité, tout en préservant **l'argent disponible pour les citoyens**, les emplois, le financement des services publics et les droits acquis. La diminution d'un taux nominal ou du nombre de taxes **ne suffit pas** à prouver cette amélioration.

L'étape P56L avait relevé, pour les déclarants québécois ayant moins de 30 000 $ de revenu total en 2023, **285 M$ d'impôt à payer et 4 201 M$ de crédits remboursables**, soit un solde agrégé **−3 916 M$**. Ce sont des statistiques fiscales historiques de déclarants, **pas le revenu disponible de ménages**, ni une somme pouvant être retirée pour financer une réforme.

Pour P56M, la définition opérationnelle est inspirée des [règles de l'outil gouvernemental *Estimer le revenu disponible*](https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible) et de [SimulRevenu](https://www.simulrevenu.gouv.qc.ca/Simulation/Disponible) : revenus marchands + prestations et crédits remboursables reçus − impôts nets et cotisations obligatoires. Une seconde mesure de **trésorerie après dépenses essentielles** soustrait logement, alimentation, transport, garde, médicaments et énergie, en tenant compte des prix toutes taxes comprises.

**Ces deux mesures sont distinctes.** La [définition macroéconomique du revenu disponible de l'Institut de la statistique du Québec](https://statistique.quebec.ca/fr/produit/publication/revenu-disponible-par-habitant-2024-quebec-et-regions) ne déduit pas les dépenses de consommation des ménages, et elle **n'intègre pas** les services sociaux en nature (soins médicaux et éducation). Ces services doivent être financés dans le **budget public P52B** et ne constituent pas une économie du ménage simplement parce qu'ils n'apparaissent pas sur sa déclaration fiscale.

Les paramètres fiscaux applicables à une simulation réelle varieront selon les années, l'âge, la famille, la résidence, les revenus de placement, les crédits et les autres mesures. Le calculateur gouvernemental officiel lui-même signale que ses cas types n'incluent pas toutes les catégories de revenus et déductions. **Le programme P56M ne prétend donc pas remplacer un logiciel de déclaration d'impôt, un actuaire ni un modèle de microsimulation représentatif.**

## 2. Un modèle séparant contributions, transferts et coût de la vie

Les quatre catégories sont définies une seule fois dans `P56M_CADRE_MICROSIMULATION_REVENUS_MENAGES_2027_2036.json` :

| Groupe | Contenu | Protection anti-double comptage |
|---|---|---|
| **Revenus marchands** | salaires, travail autonome net, placements, pensions privées, autres revenus | les prestations ne sont pas ajoutées aux salaires |
| **Prestations et crédits remboursables** | soutiens Québec/fédéral, crédits remboursables des deux paliers | un crédit remboursable ne diminue pas encore l'impôt net déclaré |
| **Prélèvements obligatoires** | impôts provinciaux et fédéraux nets de crédits non remboursables, RRQ, assurance-emploi, RQAP, RAMQ, retraites obligatoires, autres prélèvements | les crédits non remboursables ne sont pas ajoutés comme prestations |
| **Dépenses essentielles** | logement payé, alimentation, transport, garde, médicaments, énergie, autres besoins | les taxes de consommation payées, comprises dans les prix TTC, **ne sont pas soustraites une seconde fois** |

Le **revenu disponible** précède la déduction des dépenses de consommation. La mesure « reste après dépenses essentielles » représente un flux de trésorerie conventionnel distinct. Les paiements de capital hypothécaire sont traités comme sorties de trésorerie, **pas comme dépenses économiques de même nature que le loyer**. Il faudra harmoniser ces concepts au moment de choisir les indicateurs publics.

Pour comparer les régimes, l'année de référence, la composition du ménage et l'unité de prix doivent être identiques. Une comparaison de 2027 à 2036 exige une inflation explicite, des hypothèses sur l'évolution des revenus et une quantification des interventions publiques. Rien de cela n'est encore estimé par P56M.

## 3. Huit profils, deux régimes, dix années

Le cadre définit **huit profils méthodologiques** : personne seule à faible revenu, salarié vivant seul, famille monoparentale, couple salarié avec deux enfants, personne retraitée seule, personne ayant des besoins liés au handicap, travailleur autonome seul et couple retraité. Il distingue deux hypothèses constitutionnelles :

- **Québec dans le Canada** : la comparaison porte sur les mesures provinciales envisageables; l'impôt fédéral et la contribution d'assurance-emploi ne peuvent être supprimés unilatéralement par la province. Le simulateur fictif préserve ces deux lignes pour empêcher la présentation trompeuse d'une réforme « québécoise » qui abolirait des prélèvements fédéraux.
- **Québec souverain hypothétique** : la comparaison doit intégrer revenus fiscaux et aides fédérales transférés, dépenses des nouvelles compétences, pensions, dette, ententes et conséquences de la transition. Rien n'est réputé acquis; le simulateur reste un exercice arithmétique étiqueté fictif.

**8 profils × 2 régimes × 10 années = 160 unités de comparaison à documenter.** Ce chiffre exprime une couverture de conception, **non un échantillon de 160 ménages**, non une nouvelle série P52D et non 160 résultats calculés. Les huit profils ne sont pas représentatifs par eux-mêmes; aucun poids statistique, décile, région ni montant fiscal futur n'est inventé. Une simulation de PME exige des données supplémentaires et un autre module.

## 4. Exemples fictifs de cohérence — pas de promesses aux citoyens

Le programme `scripts/simuler_revenu_disponible_menages_nova_p56m.py` accepte un exercice **explicitement fictif et autorisé** et fait le bilan d'une paire *référence / réforme candidate* pour **la même année et le même ménage**.

Les tests utilisent notamment un cas **totalement fictif** où :
- la baisse d'impôt provincial est de **600 $**;
- un crédit remboursable provincial diminue de **1 300 $**;
- les autres entrées et les coûts essentiels restent identiques.

**Variation fictive : 600 − 1 300 = −700 $**, soit une perte de trésorerie de 700 $ pour le ménage test. La « compensation minimale » de **700 $** est seulement la différence arithmétique nécessaire pour ramener son flux de trésorerie au niveau du cas fictif de référence : **ce n'est pas un montant budgété, un versement recommandé ni un droit individuel réel**.

Un autre test augmente fictivement de 500 $ les dépenses essentielles du candidat : la variation de trésorerie devient **−1 200 $**, tandis que la variation du revenu disponible avant dépenses reste **−700 $**. Cette distinction interdit de masquer une détérioration du pouvoir d'achat derrière une baisse nominale d'impôt.

Le calculateur refuse l'utilisation de nombres négatifs dans ses champs simplifiés, les entrées flottantes ambiguës, les montants absents remplacés arbitrairement par zéro, le changement de revenu marchand sans modèle comportemental, les fonctions fédérales supprimées dans le cadre du Québec provincial, la double soustraction des taxes de vente et toute déclaration automatique de certification. Un résultat numériquement positif dans un exercice fictif ne devient jamais une preuve de gain.

Les besoins de simulation complexes (déficit d'entreprise individuelle, déductions et cotisations variables, gains en capital, enfants en garde partagée, et personnes avec différents statuts de résidence) **restent hors périmètre** de ce prototype simple et doivent être traités dans les futures étapes, plutôt que d'être transformés en zéros.

## 5. Conditions avant d'annoncer qu'une réforme améliore le niveau de vie

Le registre contient **dix portes de preuve**, toutes **non satisfaites** : vérification de chaque entrée et année; protection des crédits remboursables; droit fédéral; inflation et prix; représentativité et pondérations; profils vulnérables; charge fiscale et emplois des PME et sociétés; financement intégral des services; budgets 2027–2036 des deux régimes; revue indépendante et consultation.

Il faudra alors publier pour chaque région et décile les **gagnants, les perdants, les compensations et les coûts budgétaires** avec des intervalles de sensibilité, sans cacher les effets redistributifs. Les ménages modestes, les aînés, les enfants et les personnes handicapées doivent être explicitement inclus. Les protections ne peuvent être « atteintes » par un test logiciel réussi.

## 6. Livrables et reproduction

- `projets/projet-nova/etudes/P56M_CADRE_MICROSIMULATION_REVENUS_MENAGES_2027_2036.json` : méthodologie, séries à renseigner, huit profils, deux régimes, dix règles de publication.
- `scripts/simuler_revenu_disponible_menages_nova_p56m.py` : validation des profils et calculateur d'exercices **fictifs uniquement**, avec vérification du millésime P56L et du baromètre P55N.
- `scripts/tests/test_simuler_revenu_disponible_menages_nova_p56m.py` : 55 tests, dont protections contre les fausses économies, la perte de crédit, les zéros inventés et les compétences fédérales fictives.
- `.github/workflows/validate-nova-p56m.yml` : tests P56L et P56M sur la branche de revue.
- Cette note.

Commande de contrôle (sans exercice fictif) :

```bash
python scripts/simuler_revenu_disponible_menages_nova_p56m.py \
  --cadre projets/projet-nova/etudes/P56M_CADRE_MICROSIMULATION_REVENUS_MENAGES_2027_2036.json \
  --p56l projets/projet-nova/etudes/P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json \
  --barometre projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json
```

Un exercice fictif exige à la fois un fichier `--exercice` portant expressément le statut `EXERCICE_FICTIF_SANS_POUVOIR` et l'option `--autoriser-exercice-fictif`. L'option `--exiger-microsimulation-certifiee` refuse la demande (code de sortie 3). Les rapports existants ne sont jamais écrasés.

## 7. Suite de développement prioritaire : P56N

Constituer un **jeu de situations familiales documentées**, basé sur les cas types des calculateurs publics, en conservant les paramètres, limites de méthode, périodes et pièces justificatives; élargir ensuite aux sources publiques de microdonnées ou tableaux de revenus **disponibles par ménage et par région**. Ajouter au modèle un traitement des pertes d'entreprise, de la garde d'enfants et des prestations variables. Passer de l'exercice fictif à une mesure réelle **uniquement après** harmonisation des données et vérification professionnelle.

Le financement des **services municipaux, santé, éducation, sécurité, pensions, logements et emplois** reste une porte indépendante dans chaque régime. Les **600 montants P52B**, **720 incidences P52D** et **20 preuves P52A** restent ouverts. **Score interne : 53 %, fourchette 45–60 %.**

Aucune adoption de taux, aucune économie certifiée, aucune modification de `main` ou de SINJIRA, aucune fusion de la demande de revue #673. **Décision : `NO_GO_AUTOMATIQUE`.**
