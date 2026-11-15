# Projet Nova–Sinjira — G0.16p : deuxième contrôle territorial des taxes municipales 2026

**8 novembre 2026 · Rapport de travail non adopté · Score de préparation 47/100, 53 points restant à obtenir.**

## Périmètre

La phase G0.16o vérifiait Warwick. Cette phase ajoute **Laval** et **Gatineau**, déjà présentes dans le portefeuille de sept projets PRIMEAU étudié en G0.16n. Les données officielles concernent la fiscalité municipale 2026 et non la viabilité de la fiscalité Nova. Trois villes ne constituent pas un échantillon représentatif du Québec.

## Taux officiels et unités

| Ville | Composante | Valeur 2026 | Unité et restriction |
| --- | --- | ---: | --- |
| Warwick | Foncière générale résiduelle | 0,575 | $ / 100 $ de valeur foncière; autres taxes possibles (G0.16o) |
| Laval | Foncière générale de base | 0,4973 | $ / 100 $ de valeur foncière |
| Laval | Spéciale eau et eaux usées de base | 0,0111 | $ / 100 $ de valeur foncière |
| Laval | Spéciale ARTM de base | 0,0825 | $ / 100 $ de valeur foncière |
| Laval | Générale, immeubles de 6 logements et plus | 0,6629 | $ / 100 $ de valeur foncière; autre catégorie |
| Gatineau | Résidentielle ordinaire | variable | selon unité de voisinage, PAS de taux unique |
| Gatineau | Générale, 6 logements et plus | 6,964 | $ / 1 000 $ de valeur foncière |
| Gatineau | Transport collectif | 1,417 | $ / 1 000 $ de valeur foncière |
| Gatineau | Service de la dette, nouvelle ville | 0,830 | $ / 1 000 $ de valeur foncière |
| Gatineau | Matières résiduelles | 178,83 | $ par logis; conditions applicables |

**Sources primaires :** [Laval, tableau des taux 2026, page imprimée 73](https://www.laval.ca/wp-content/uploads/2026/02/evolution-taux-taxation-tarification.pdf); [Gatineau, budget 2026, section « Taux de taxes »](https://www.gatineau.ca/docs/guichet_municipal/administration_municipale/budget/budget_2026/budget.fr-CA.pdf); [Gatineau, taxation par unité de voisinage](https://www.gatineau.ca/taxes/). Pour Laval, le tableau PDF a été inspecté visuellement. Pour Gatineau, le texte du PDF a été lu, mais la capture visuelle du grand fichier a échoué : **vérification visuelle indépendante non attestée**.

## Exemples et limites

À Laval, les trois composantes « de base » retenues totalisent **0,5909 $ par 100 $ d'évaluation**; sur une propriété **fictive** évaluée à **300 000 $**, le sous-total de ces seules composantes vaut **1 772,70 $**. Les autres taxes, charges particulières et tarifs ne sont pas inclus : **ce n'est ni une facture complète ni une économie promise**.

Gatineau publie un **modèle de résidence médiane à 454 600 $ de valeur étalée** dans son budget 2026 : résidentiel **2 374,83 $**, transport **644,17 $**, matières résiduelles **178,83 $**, dette **377,32 $**, soit **3 575,15 $** pour ces rubriques. Des taxes sectorielles peuvent s'ajouter. **Ce modèle municipal n'est pas un paiement attesté d'un ménage**, et le taux résidentiel ordinaire reste spécifique à l'unité de voisinage.

Le sous-total fictif de Laval, le sous-total fictif de Warwick en G0.16o (**2 328,45 $** à 300 000 $) et le modèle médian de Gatineau sont **incomparables** en raison du type de propriété, des assiettes, des services inclus et des valeurs foncières. Les présenter comme des « économies » serait trompeur.

## Preuves toujours absentes

1. Taxation 2026 détaillée de Port-Daniel–Gascons, et taux par secteur.
2. Table des unités de voisinage de Gatineau et classification d'un bien particulier.
3. Pièces de paiements de subventions PRIMEAU, et non seulement annonces et engagements.
4. Décaissements d'emprunts, service de la dette et échéances réelles.
5. Comptes de taxes anonymisés, rôle, desserte et revenus des ménages représentatifs.
6. Coût complet de l'eau, entretien des installations, obligations envers les employés.
7. Microsimulation distributive au niveau des ménages (propriétaires et locataires).
8. Audit juridique des compétences et audit financier externe.

Ces absences signifient **non vérifié**, pas **zéro paiement** ni **zéro dette**.

## Verrou sur la réforme proposée

La suppression ou le remplacement des taxes locales exige une analyse des compétences et une compensation budgétaire intégrale. Dans le **Québec au Canada**, aucune décision provinciale ne modifie unilatéralement les compétences fédérales; il faut vérifier les pouvoirs municipaux et les emprunts. Dans le **Québec souverain**, il faut traiter séparément actifs, dettes, transferts, pensions et engagements sans présumer de recettes fédérales.

Les deux cadres sur dix ans dans `data/comparaison-taxes-municipales-g0-16p-2026.json` laissent **toutes les recettes et dépenses non prouvées à `null`**. Les salariés, les services essentiels, les populations vulnérables et la continuité de l'approvisionnement ne peuvent être sacrifiés pour déclarer artificiellement une baisse de taxes.

## Livrables et décision

- Registre : `data/comparaison-taxes-municipales-g0-16p-2026.json`.
- Vérificateur : `assets/g016p-local-taxes-core.mjs`.
- Suite de contrôles : `tests/g016p-local-tax-crosscheck.test.mjs`.

**G0.16p : preuves des barèmes locaux accrues, mais aucune facture individuelle réelle, aucun paiement PRIMEAU et aucun budget Nova équilibré certifié. Score : 47/100 inchangé.**

**Suite G0.16q :** constituer un registre des preuves de trésorerie et des obligations d'emprunt, obtenir les pièces publiques disponibles, puis préparer la comparaison distributive par unité de référence homogène.
