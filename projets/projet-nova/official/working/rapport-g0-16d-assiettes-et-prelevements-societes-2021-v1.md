# NOVA-FIN-G0.16d — Assiette des sociétés, FSS et traitement des crédits

**Projet :** Nova–Sinjira | **Date :** 7 novembre 2026 | **Statut :** étude descriptive, non normative, non auditée indépendamment.  
**Préparation globale : 47/100** d'après G0.12; **53 points non acquis**. Ne pas déduire de nouveaux points du seul ajout de ce dossier.

## 1. Premier résultat : mesurer trois assiettes ou recettes distinctes

Le ministère des Finances du Québec a publié un **sommaire officiel** des déclarations fiscales des sociétés dont l'année d'imposition s'est terminée en **2021**. Cette page, dernière mise à jour le 7 octobre 2026, permet d'isoler une base de profit imposable provincial, les salaires soumis au Fonds des services de santé (FSS) et les flux d'impôt sur le revenu des sociétés.

**Source primaire (tableaux HTML publics)** : https://www.quebec.ca/gouvernement/finances-publiques/revenus/donnees-fiscales/statistiques-fiscales-societes

| Grandeur du régime existant | Montant 2021 | Signification |
|---|---:|---|
| **Revenu imposable des sociétés au Québec** | **95 784 M$** | Assiette provinciale de l'impôt sur le revenu des sociétés |
| **Salaires assujettis au FSS** | **155 850 M$** | Assiette d'une **cotisation employeur distincte** |
| Impôt provincial sur le revenu des sociétés | 10 000 M$ | Prélèvement sur le revenu des sociétés |
| Cotisation des sociétés au FSS | 5 327 M$ | Financement associé à la cotisation employeur |
| **Total impôt des sociétés + FSS** | **15 327 M$** | Somme de deux instruments, **pas** un seul impôt sur les bénéfices |
| Crédits d'impôt des sociétés | −2 468 M$ | Réduction de recettes dans le résumé |
| **Impôts et cotisations nets des crédits** | **12 860 M$** | Total publié, arrondi |

Les chiffres sont présentés en **millions de dollars de 2021**. Le calcul `15 327 - 2 468 = 12 859` diffère de **1 M$** du total officiel publié `12 860`, compte tenu des arrondis. La tolérance documentaire du contrôle est d'un million.

**Conséquence juridique :** la vision Nova de « deux prélèvements » ne peut pas être évaluée simplement en transformant les **155 850 M$ de salaires** en base de revenu imposable, ou en supprimant **5 327 M$ de cotisations FSS** sans démontrer une continuité financière équivalente. Une cotisation sociale ou affectée doit être examinée selon sa compétence, sa fonction et les droits protégés.

## 2. Population et répartition par taille

**564 599 déclarations de revenus des sociétés** ont été traitées en 2021.

| Type de société selon la source | Déclarations | Impôt sociétés M$ | FSS M$ | Impôt + FSS M$ |
|---|---:|---:|---:|---:|
| Petites | 542 249 | 2 922 | 1 173 | 4 095 |
| Moyennes | 14 858 | 1 525 | 1 035 | 2 560 |
| Grandes | 7 492 | 5 553 | 3 119 | 8 672 |
| **Ensemble** | **564 599** | **10 000** | **5 327** | **15 327** |

Les grandes entreprises apportent **56,6 %** de l'ensemble impôt sociétés + FSS publié, mais elles ne représentent que **1,3 %** des sociétés déclarantes (parts arrondies). **322 020 sociétés (57,0 %) n'avaient pas d'impôt sur leur revenu à payer**, tandis que **239 628 (42,4 %) n'avaient ni impôt sur le revenu ni cotisation au FSS à payer**. Il ne faut pas confondre ces deux sous-populations.

**Pourquoi ces données sont utiles à Nova :** comparer les effets pour les PME, les entreprises sans profit taxable, les entreprises employeuses et les grands groupes. Une réforme du FSS touche d'abord une **base salariale**, et ses effets éventuels sur l'emploi, les salaires, l'investissement et les services financés doivent être étudiés indépendamment.

## 3. Références ne portant pas sur la même chose

La phase G0.16c documente les revenus imposables des **particuliers de 2023** (`372 261 M$`) et leurs impôts. Ce n'est ni la même population, ni la même année, ni le même mécanisme que l'assiette provinciale des **sociétés de 2021** (`95 784 M$`). Il est **interdit** d'additionner ces deux assiettes pour calculer un taux global de « taxe Nova » sur l'ensemble de la population.

Le cadre G0.14 établit des **prévisions budgétaires publiques 2026–2027**, dont les recettes autonomes et fédérales prévues. Ces recettes ont une autre période et une autre base de comptabilité.

L'**Agence du revenu du Canada** publie des données **T2 des sociétés pour 2019–2024** (données arrêtées au 30 juin 2026) :
https://www.canada.ca/fr/agence-revenu/programmes/a-propos-agence-revenu-canada-arc/statistiques-revenu-statistiques-tps-tvh/statistiques-societes-t2/tableaux-statistiques-societes-annees-imposition-2019-2024.html

L'ARC précise que l'**impôt provincial des sociétés du Québec n'est pas compris** dans les montants de l'impôt total à payer des tableaux T2 fédéraux. Les montants ne peuvent pas servir à remplacer l'impôt des sociétés calculé par Revenu Québec. Aucune valeur numérique T2 fédérale n'est transcrite dans ce dossier.

Les rapports complets PDF/XLSX des sociétés 2021 et les définitions de taille n'ont **pas été importés ni contre-vérifiés séparément** au stade de ce dossier. Les données de ce travail sont limitées aux tables sommaires visibles sur la page officielle.

## 4. Intégrité des preuves et portes bloquantes

Le registre `data/assiette-societes-g0-16d-2021.json` consigne les valeurs de référence, la répartition, les périodes, la provenance et les **gains Nova encore inconnus** (`null`). La fonction `assets/g016d-corporate-base-core.mjs` contrôle les sommes, les chiffres de source, la séparation des bases, la traçabilité et le score; les tests sont `tests/g016d-corporate-base.test.mjs`.

| Preuve G0.15 liée | Apport réel de G0.16d | Encore indispensable |
| --- | --- | --- |
| **V04 — Impôts sociétés** | Ventilation agrégée impôt/FSS/crédits 2021 | Comptes actuels, déductions, crédits remboursables, affectations, droits |
| **V06 — Entreprises** | Assiette du revenu imposable + masse salariale FSS 2021 | Pertes, dividendes, reports, assiettes 2026, incidence des réformes |
| **V13 — PME / travail** | Déclarations et prélèvements par catégorie de taille | Salaires, heures, emploi, prix, petites entreprises et travailleurs autonomes |

**Aucune de ces trois preuves n'est validée indépendamment** : les éléments partiels ne suffisent pas à remplir tout leur champ. Les **15 fiches** de `data/matrice-preuves-g0-15-fiscalite.json` restent **`A_DOCUMENTER`**; G0.15/G0.16 ne sont **pas franchies**.

Aucun montant de « recettes de paradis fiscaux », taux uniforme d'imposition, coût de remplacement du FSS, gains des ménages, économies publiques ou budget souverain n'est déduit de ces données.

## 5. Étape suivante — G0.16e, étude de soutenabilité

1. **Harmoniser les millésimes** : obtenir les données des sociétés actualisées, tableaux bruts avec empreintes d'intégrité et comptabilité de revenus 2026–2027, avec ajustements explicites.
2. **Décomposer légalement** la base des entreprises : pertes, report de déficits, dividendes, crédits, exemptions, liens de groupe et règles fiscales internationales.
3. **Protéger financement et droits du FSS** : préciser affectation, charges reprises, risque de transfert des coûts et prévention d'un double compte des recettes.
4. **Comparer deux scénarios complets** : Québec au Canada vs Québec souverain, avec obligations fédérales, transferts, pensions et dettes séparés.
5. **Évaluer emploi et pouvoir d'achat** des PME, salariés, ménages et régions sur données adaptées et autorisées; soumettre des scénarios de sensibilité à revue indépendante.

**Décision :** aucune nouvelle taxe fixée, aucune abolition déclarée, aucune reprise de fonctions souveraines financée, **score 47/100 inchangé**. Les références candidates `official/reference/*` et le manifeste `data/sources.json` restent inchangés.
