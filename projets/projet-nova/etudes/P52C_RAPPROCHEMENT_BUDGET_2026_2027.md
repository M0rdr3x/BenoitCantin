# Projet Nova — P52C : rapprochement des prévisions 2026-2027 et des assiettes fiscales existantes

**18 octobre 2026 · Candidat de recherche non adopté · État : NO_GO**

## 1. Pourquoi ce rapprochement existe

Le modèle P52B conserve correctement **600 entrées financières inconnues** et un registre de **20 vérifications non obtenues**. Avant de les remplir, il faut une photographie contrôlable des recettes **effectivement prévues par l'État québécois** pour 2026-2027, tout en isolant ce qui ne constitue pas une taxe provinciale remplaçable.

Le présent jalon utilise deux sources **officielles publiées en mars 2026**, toutes deux relatives à des *prévisions*, non à des résultats audités :
- [Discours sur le budget 2026-2027, tableau 3, page 27](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf) — ventilation des revenus;
- [Plan budgétaire 2026-2027, tableau F.2, page F.9](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf) — recettes, dépenses et passage au solde budgétaire.

Le JSON `P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json` contient une **transcription locale** de 21 lignes officielles, leurs catégories, unités, documents et pages. Le vérificateur `scripts/rapprocher_budget_quebec_nova_p52c.py` contrôle les calculs et refuse les chiffres modifiés. **La comparaison des octets à l'original PDF et toute mise à jour budgétaire exigent toujours une vérification documentaire indépendante**; réussir les tests ne remplace pas cette lecture.

## 2. Rapprochement officiel de la prévision 2026-2027

| Agrégat et sous-agrégat | G$ prévus | Périmètre |
| --- | ---: | --- |
| Impôt des particuliers | 50,800 | Impôt québécois existant |
| Impôts des sociétés | 14,527 | Impôt québécois existant |
| **Total de ces deux impôts** | **65,327** | Ne constitue pas un rendement du nouveau programme Nova |
| Cotisations pour les services de santé | 9,412 | Autre prélèvement; à qualifier juridiquement |
| Impôt foncier scolaire | 1,311 | Autre prélèvement; à qualifier juridiquement |
| Taxes à la consommation — ensemble | 30,008 | Dont « taxes de vente » : 26,349 G$ |
| Revenus des entreprises gouvernementales | 5,853 | Revenus non assimilables automatiquement à un impôt |
| Droits, permis et redevances | 6,542 | Qualification juridique et économique nécessaire |
| Revenus divers | 15,908 | Qualification et sous-détails nécessaires |
| **Revenus autonomes** | **134,361** | Somme des catégories précédentes |
| Transferts fédéraux | 32,131 | **Pas une taxe provinciale** |
| **Revenus totaux** | **166,492** | Revenus gouvernementaux consolidés |

Le solde **69,034 G$** de revenus autonomes autres que les deux impôts sur les revenus actuels contient **à la fois d'autres prélèvements, des revenus non fiscaux et des éléments nécessitant classification**. Il **ne peut absolument pas** être présenté comme « 69,034 G$ de taxes abolissables ». 

Point critique : selon la note officielle du tableau 3, la catégorie « taxes de vente » ne désigne **pas uniquement la TVQ**. Elle englobe notamment la TVQ, la taxe sur les primes d'assurance, la taxe sur l'hébergement et le droit spécifique sur les pneus neufs. La catégorie ne peut donc pas être directement utilisée comme prévision des seules recettes de la TVQ.

## 3. La différence entre les trois soldes

En G$, à partir du tableau F.2 :

```text
Revenus totaux                                          166,492
Dépenses des portefeuilles                              160,489
Service de la dette                                      10,268
Dépenses totales = portefeuilles + dette                170,757

Écart arithmétique 166,492 - 170,757                     -4,265
Provision pour éventualités                              -2,000
Déficit comptable prévu                                  -6,265
Versements consacrés au Fonds des générations            -2,347
SOLDE BUDGÉTAIRE PRÉVU AU SENS DE LA LOI                 -8,612
```

Les montants officiels du cadre Nova **166,492 G$ de revenus, 170,757 G$ de dépenses et 10,268 G$ de dette** sont donc rapprochés exactement des tableaux de mars 2026, mais **ne certifient pas automatiquement les autres hypothèses Nova**. Le service de la dette est **déjà inclus** dans les dépenses totales. Le compter encore une fois produirait une conclusion erronée.

Le chiffre **−4,265 G$** ne doit plus être qualifié de solde budgétaire officiel; c'est seulement une différence arithmétique **avant** provision et versements au Fonds des générations.

## 4. Limites constitutionnelles et fiscales

Pour le **Québec dans le Canada**, le tableau de 166,492 G$ décrit les revenus du gouvernement du Québec. Les **32,131 G$ de transferts fédéraux** sont des revenus reçus du Canada, pas des impôts québécois à abolir. Les recettes fiscales fédérales perçues auprès des Québécois ne figurent pas comme revenus propres du gouvernement provincial dans ce tableau. Les cotisations locales et municipales ne sont pas toutes détaillées ici.

Pour un **Québec souverain hypothétique**, la prévision provinciale ne constitue ni la recette fiscale ni le budget d'un nouvel État : transférer des compétences suppose des obligations, actifs, dettes, mécanismes monétaires, accords et régimes de recettes à établir. Aucun transfert fédéral existant ne doit être automatiquement présumé remplaçable dollar pour dollar.

Pour **l'objectif des deux prélèvements**, les 65,327 G$ d'impôts personnels et des sociétés sont une référence de départ des recettes actuelles, pas l'assiette potentielle ni le taux nécessaire du futur impôt sur tous les revenus. Sans assiettes détaillées, comportement des contribuables, transition et incidence sur les entreprises et ménages, **aucun nouveau taux fiable ne peut être calculé**.

## 5. Compatibilité stricte avec le modèle P52B

Le référentiel P52C est une **annexe de réconciliation 2026-2027**, antérieure au premier exercice du gabarit décennal. Le programme de vérification :
- exige **21 catégories connues**, leurs valeurs exactes en millions de dollars et leurs deux références officielles;
- reconstitue les sous-totaux, les recettes autonomes et les transferts, les trois soldes, et la concordance avec les **trois agrégats correspondants** du gabarit P52B;
- distingue **revenus des entreprises gouvernementales**, **autres droits/redevances**, **impôts sur le revenu** et **transferts fédéraux**, sans les renommer tous « taxes »;
- refuse les montants en nombre flottant, la mauvaise page, la mauvaise catégorie, les doubles comptes de service de la dette, les faux soldes légaux et les prétentions d'adoption;
- **n'écrit aucune valeur** dans les 60 exercices-scénarios 2027-2036 de P52B : **les 600 inconnues demeurent inconnues**;
- produit un rapport agrégé, jamais une promesse de rendement anti-évasion, d'abolition, de fiscalité nouvelle ni une preuve que le programme est financé.

### Exécution depuis la racine du dépôt

```bash
python scripts/rapprocher_budget_quebec_nova_p52c.py \
  --referentiel projets/projet-nova/etudes/P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json \
  --gabarit projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json \
  --rapport p52c_rapport_local.json
```

Le contrôle `--exiger-financement` renvoie **3** : disposer d'une photographie officielle des recettes et dépenses du Québec **ne finance pas** la transition vers deux prélèvements. Le code `0` signifie seulement que le rapprochement arithmétique a fonctionné, `2` indique des données invalides. **Tous les rapports P52C maintiennent `NO_GO_AUTOMATIQUE`.**

## 6. Prochaine phase substantielle : impact distributif et remplacement de recettes

Avant d'évaluer des taux, établir :
1. assiettes fiscales **réelles par type de revenu**, particuliers et sociétés, et effets des exemptions/crédits;
2. ventilation des taxes de vente, cotisations obligatoires, droits et revenus divers **sans doubles comptes**;
3. répartition fédéral / provincial / municipal et incidences en revenu disponible par type de ménage et de PME;
4. dépenses incompressibles, obligations contractuelles, services et dépenses de transition, selon le régime constitutionnel;
5. validation **indépendante** des 20 preuves P52A et scénarios des dix exercices P52B;
6. séparation des revenus existants du **gain additionnel** contre les paradis fiscaux, qui reste estimé à zéro dans le modèle prudent tant qu'aucune estimation indépendante n'existe.

P52C n'est pas un exercice de propagande ni un chiffrage électoral : c'est une étape de rapprochement afin que les propositions futures soient contrôlables par des personnes qualifiées.

**Statut P52C : RAPPROCHEMENT DOCUMENTAIRE PARTIEL / AUDIT INDÉPENDANT À OBTENIR / AUCUNE LOI, TAXE, FUSION, PUBLICATION OU COLLECTE AUTORISÉE. PR640 : NE PAS FUSIONNER.**
