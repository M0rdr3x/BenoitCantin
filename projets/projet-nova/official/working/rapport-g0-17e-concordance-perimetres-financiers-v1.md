# Projet Nova — G0.17e : concordance comptable entre municipalités, eau et budget provincial

**Date du relevé : 8 novembre 2026.**  
**Document de contrôle de sources existantes, non adopté, non audité indépendamment.**  
**Score du Projet Nova : 47/100 (53 points manquants), sans changement.**

## 1. Pourquoi cette concordance est indispensable

Le programme propose d'étudier **un prélèvement sur le revenu des particuliers et des entreprises** ainsi qu'un **mécanisme contre les paradis fiscaux**. L'objectif d'alléger la charge sur les ménages ne pourra être évalué tant que les recettes municipales supprimées, les services à maintenir, les transferts et les droits sociaux ne seront pas rapprochés selon leurs dates et leurs périmètres.

La présente phase compare des **informations historiques et prévisionnelles déjà documentées dans le dépôt**. Elle **n'ajoute aucun nouveau poste de fiscalité Nova et ne calcule aucun taux**.

## 2. Quatre catégories comptables à ne jamais fusionner silencieusement

| Série | Année et périmètre | Montants présentement disponibles | Interprétation possible |
| --- | --- | --- | --- |
| Services d'eau municipaux | 2023, réseaux étudiés par le MAMH | Revenus affectés ~**2,4 G$** ; coût économique complet moyen ~**6,0 G$** | L'écart de **3,6 G$** est une différence indicative de couverture du coût complet, **pas** un déficit de trésorerie |
| Organismes municipaux | 2024, organismes municipaux consolidés | Revenus ~**31,3 G$** dont transferts ~**7,4 G$** | Recettes locales historiques; les transferts internes doivent être neutralisés lors d'une consolidation |
| Gouvernement du Québec, comptes publics | 2025–2026, réalisé et consolidé | Recettes **160 428 M$**, dépenses **165 930 M$**, solde **−5 502 M$** | Réalisations provinciales, **pas** budget municipal 2024 ni budget Nova |
| Gouvernement du Québec, rapport préélectoral | 2026–2027 à 2030–2031, prévisions provinciales | Recettes, dépenses, transferts et provision projetés sur **5 exercices** | Prévisions du gouvernement en place, non des recettes acquises au Projet Nova |

Sources internes : `data/g017c-recettes-municipales-2024-et-couts-eau-2023.json`, `data/comptes-publics-reels-g0-15-v02-v03-2025-2026.json`, `data/cadre-financier-fiscal-g0-16v-aout-2026.json` et `data/cadre-financier-g0-13-2026-2036.json`. Chaque source renvoie à sa publication officielle et comporte des réserves de vérification. La source brute CSV municipale n'a pas encore été importée; les données sont donc maintenues au statut de **repère public non certifié pour la réforme**.

## 3. Répartition des 31,3 G$ municipaux de 2024

| Recettes arrondies, G$ | Valeur |
| --- | ---: |
| Foncier municipal | 15,0 |
| Transferts gouvernementaux | 7,4 |
| Ventes de biens et services | 3,2 |
| Tarification | 2,2 |
| Droits de mutation | 1,3 |
| Autres recettes | 2,2 |
| **Total historique** | **31,3** |

Le simple calcul `31,3 - 7,4 = 23,9 G$` donne des **recettes municipales hors transferts approximatives**, non une nouvelle assiette fiscale du Québec.

Si les propositions de réforme visaient simultanément à remplacer tout le foncier municipal et les droits de mutation : `15,0 + 1,3 = 16,3 G$` représente **l'ordre de grandeur historique brut de deux catégories de recettes à protéger ou remplacer en 2024**. Ce n'est **ni un coût net de 2026**, ni une créance supplémentaire à additionner automatiquement à la province, ni la preuve que ces deux catégories peuvent toutes deux disparaître légalement. Les dépenses et compensations correspondantes doivent être évaluées à périmètre constant, sans supprimer ni doubler les crédits déjà compris.

Le traitement du réseau d'eau fournit un deuxième avertissement : les **2,4 G$ de recettes affectées en 2023** peuvent recouper les recettes municipales de foncier et de tarification; les **3,6 G$ d'écart économique de couverture** ne peuvent pas être additionnés au **16,3 G$** comme « déficit budgétaire de 2026 ». Le coût complet de 6,0 G$ inclut aussi des besoins moyens d'investissement sur dix ans.

## 4. Seuils provinciaux sous hypothèses — pas de recettes Nova

Les montants ci-dessous sont **des calculs à partir des prévisions provinciales d'août 2026**, en millions de dollars canadiens. Formule : `dépenses prévues incluant intérêts + provision - autres recettes supposées maintenues - transferts fédéraux prévus`. Le modèle de référence part de l'hypothèse de **dépenses inchangées** et ne finance pas une réforme des revenus municipaux ni les nouvelles compétences d'un pays souverain.

| Exercice | Seuil conditionnel de prélèvements provinciaux (M$) | Avec versements au Fonds des générations (M$) |
| --- | ---: | ---: |
| 2026–2027 | 112 369 | 114 851 |
| 2027–2028 | 114 162 | 116 663 |
| 2028–2029 | 114 994 | 117 620 |
| 2029–2030 | 117 225 | 120 015 |
| 2030–2031 | 121 230 | 124 159 |
| 2031–2032 à 2035–2036 | **Inconnu** | **Inconnu** |

Pour 2026–2027 : `171 597 + 2 000 − 28 182 − 33 046 = 112 369 M$`. Le seuil est un **besoin comptable provincial conditionnel**, pas une estimation du rendement des deux prélèvements Nova. Les **33 046 M$** de transferts fédéraux prévus appartiennent au scénario **Québec dans le Canada**. Ils ne sont **pas conservés automatiquement** dans le scénario souverain. Les obligations fédérales qui seraient reprises doivent être budgétées séparément, avec les recettes, la dette, les pensions, les droits et les effets économiques correspondants.

## 5. Ce que vérifie le logiciel G0.17e

Le module `assets/g017e-cross-scope-reconciliation-core.mjs` et les tests `tests/g017e-cross-scope-reconciliation.test.mjs` :

- recalculent **31,3 G$** de recettes municipales historiques, **23,9 G$** hors transferts et l'exposition brute de **16,3 G$** si deux catégories fiscales étaient remplacées;
- conservent distinct l'écart de coût complet de l'eau de **3,6 G$** pour 2023, sans le transformer en déficit de caisse;
- recalculent les **cinq** seuils provinciaux et leurs versements au Fonds des générations, en contrôlant leur cohérence entre deux registres existants;
- vérifient le solde réel provincial **−5 502 M$** pour 2025–2026 sans le confondre avec une prévision 2026–2027;
- refusent de remplacer les années non documentées par des zéros ou de déclarer des montants fiscaux Nova certifiés.

Ces contrôles **ne constituent pas un rapprochement entre tous les livres comptables originaux**, une analyse juridique de chaque taxe, un audit externe ni un modèle de l'incidence sur le revenu des ménages.

## 6. Étapes nécessaires avant d'annoncer une baisse d'impôts soutenable

1. Récupérer et figer les fichiers MAMH 2024 et 2025, leur dictionnaire comptable, la liste des organismes absents et les empreintes SHA-256.
2. Séparer municipalités locales, MRC, régies, transport et organismes déjà consolidés; établir les rapprochements pour **un même exercice comptable**.
3. Évaluer quels prélèvements sont remplaçables en droit et comment maintenir les services, la dette, les retraites, les conventions collectives et les effectifs réels.
4. Démontrer l'assiette imposable des personnes et des entreprises, ainsi que la recette **nette additionnelle réellement attribuable** à un mécanisme anti-paradis fiscaux.
5. Produire les deux **budgets décadaires** avec scénarios adverses, les faire revoir indépendamment et enregistrer les décisions.

**Décision :** la nouvelle concordance améliore la qualité du diagnostic, mais n'établit ni la viabilité d'un taux fiscal Nova ni un bilan souverain audité. **La grille reste à 47/100.**
