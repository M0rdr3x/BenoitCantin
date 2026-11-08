# Projet Nova — G0.16o | Taxation municipale réellement réglementée en 2026 et preuve des versements

**Date : 7 novembre 2026 · Rapport de travail non adopté · Score global inchangé : 47/100, 53 points manquants.**

## 1. Progrès au-delà des seuls projets subventionnés

G0.16n comparait sept projets et leurs aides PRIMEAU, mais les sommes figurant dans les annonces n'attestaient **aucun versement de trésorerie** et les budgets locaux ne détaillaient pas la charge fiscale actuelle d'un ménage. La présente étape examine le **règlement annuel 2026 de Warwick**, déjà étudiée comme municipalité en G0.16m, et les conditions actuelles de réclamation du programme PRIMEAU.

**Documents primaires :** [Ville de Warwick, règlement 415-2025 — Taux de taxes et compensations, exercice 2026](https://villedewarwick.quebec/wp-content/uploads/2026/02/R415-2025-Taux-de-taxes-et-compensations-2026.pdf), adopté le 12 janvier et entré en vigueur le **14 janvier 2026**, ainsi que le [règlement 416-2025 — Tarification 2026](https://villedewarwick.quebec/wp-content/uploads/2026/02/R416-2025-Tarification-pour-lexercice-2026.pdf). Le premier fixe les taux fonciers, taxes spéciales et compensations et le second traite d'autres tarifs de services. Les PDF ont été **consultés en texte**, mais les captures visuelles du règlement ont été bloquées par un affichage de protection du site; **aucune vérification visuelle indépendante n'est revendiquée**.

## 2. Impôts fonciers et taxes spéciales : chiffres applicables par catégorie

Le taux foncier général de la **catégorie résiduelle résidentielle** (art. 2.1) est de **0,575 $ par 100 $ d'évaluation**. Il ne s'agit **pas de 0,575 % de revenu**, mais de 0,575 $ sur chaque 100 $ de **valeur inscrite au rôle foncier**.

### Taxes spéciales réglementées en 2026

| Article | Objet / secteur | Dollars par 100 $ d'évaluation |
| --- | --- | ---: |
| 3.1 | Assainissement des eaux usées — secteurs desservis | 0,101 |
| 3.2 | Quote-part des cours d'eau — exploitations agricoles enregistrées | 0,0155 |
| 3.3 | Taxe liée à l'emprunt 229-2017 — bassin de taxation particulier | 0,0056 |
| 3.4 | Emprunt caserne incendie 165-2012 — ensemble du territoire imposable | 0,0123 |
| 3.5 | Emprunt camion incendie 233-2017 — ensemble du territoire imposable | 0,0061 |
| 3.6 | Emprunt équipement incendie 305-2020 — ensemble du territoire imposable | 0,0035 |
| 3.7 | Mise à niveau accélérée du réseau routier — ensemble imposable | 0,025 |
| 3.8 | Emprunt 357-2022, aqueduc et égout sanitaire — propriétés desservies | 0,0114 |
| 3.9 | Emprunt 357-2022, voirie et égout pluvial — ensemble imposable | 0,0155 |

**Attention : tous ces taux ne s'appliquent pas à tous les immeubles.** Le type de propriété, sa catégorie au rôle, le bassin de taxation et l'accès aux réseaux déterminent les taux pertinents. Les autres règlements municipaux peuvent imposer des charges supplémentaires.

### Compensations locales sélectionnées (art. 5.1 et 6.1)

| Service (par unité résidentielle concernée) | Montant 2026 |
| --- | ---: |
| Aqueduc par logement | 102,00 $ |
| Égouts par logement | 31,25 $ |
| Collecte de matières résiduelles en zone urbaine | 283,00 $ |
| Collecte de matières résiduelles en zone rurale | 267,00 $ |

Ce sont les tarifs **publiés**, et non une somme réellement prélevée ou encaissée auprès d'un propriétaire précis. Le règlement décrit en outre d'autres catégories pour les commerces, installations agricoles et industries, et distingue la ville en zones rurale et urbaine.

## 3. Illustration reproductible, volontairement incomplète

Le contrôleur `assets/g016o-warwick-tax-core.mjs` permet uniquement un exercice portant la marque `SYNTHETIC_PARTIAL_EXAMPLE`. Son scénario standard est une **propriété fictive** de **300 000 $ au rôle**, en catégorie résidentielle résiduelle, **un logement** avec aqueduc, égouts et collecte urbaine.

| Élément sélectionné de l'illustration | Calcul | Somme |
| --- | --- | ---: |
| Taxe foncière générale et cinq taux spéciaux applicables à tous les immeubles imposables (art. 3.4 à 3.7 et 3.9) | 300 000 ÷ 100 × (0,575 + 0,0123 + 0,0061 + 0,0035 + 0,025 + 0,0155) | **1 912,20 $** |
| Aqueduc, égouts et collecte urbaine | 102 + 31,25 + 283 | **416,25 $** |
| **Sous-total fictif des catégories incluses** | 1 912,20 + 416,25 | **2 328,45 $** |

**Ce sous-total n'est ni une facture de taxes complète, ni une estimation moyenne pour Warwick, ni une facture réellement payée par un propriétaire**, car les taxes sectorielles et d'autres règlements sont volontairement exclus; l'évaluation foncière de 300 000 $ est inventée uniquement à des fins pédagogiques. Il ne dit **rien** du revenu du propriétaire ou du locataire et ne chiffre **aucune économie future Nova**.

### Point crucial : règlement d'emprunt 404-2025

Le [règlement 404-2025](https://villedewarwick.quebec/wp-content/uploads/2025/03/R404-2025-Emprunt-usine-eau-potable-et-filiere-traitement-version-finale.pdf), étudié en G0.16m, décrit un emprunt brut pour la nouvelle usine Gérard-Laroche et des mécanismes de taxation spéciale. **Le règlement annuel 415-2025 pour 2026 ne nomme pas explicitement l'emprunt 404-2025 dans la série de taux étudiés.**

Cela **ne signifie ni que le projet n'occasionnera jamais de taxe, ni qu'un taux précis de 2026 peut être inventé**. Il faut vérifier les autres règlements, les rôles, la dette réellement contractée, la date d'exigibilité et les documents financiers avant de produire une facture ou une projection. Le taux spécifique de 404-2025 reste **`null`**.

## 4. Versements PRIMEAU : la procédure officielle n'est pas une preuve de paiement

La [page officielle PRIMEAU 2023–2033](https://www.quebec.ca/habitation-territoire/infrastructures-municipales/programmes/eau-potable-eaux-usees/programme-infrastructures-municipales-eau-primeau) renvoie à son [guide d'août 2026](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/infrastructures/primeau/GUI_primeau_aout_2026.pdf), dont les sections **4.10–4.12** précisent le processus actuel de réclamation et de paiement (pages PDF 30 et 31, index 29 et 30) :

- le bénéficiaire doit **présenter des réclamations de dépenses** et justifier l'avancement des travaux;
- le Ministère peut approuver des réclamations partielles, **jusqu'à 90 %** de l'aide potentiellement versable sur les dépenses attestées, **ce qui n'est pas la preuve que 90 % a déjà été payé**;
- des **factures et attestations de dépenses payées** sont nécessaires à la réclamation finale;
- **certains projets** font l'objet d'une vérification finale plus poussée avec retenue de 10 %; la retenue n'est **pas automatiquement imposée à chaque dossier**;
- un versement initial **peut** être prévu par une convention d'aide financière, sans être garanti pour tous les projets.

**Application temporelle :** le guide d'août 2026 **ne remplace pas automatiquement les modalités contractuelles des aides attribuées en 2025**, notamment celles ayant conservé leurs modalités du sous-volet 1.2. Pour Warwick et les six autres cas, il faut consulter chaque convention et les réclamations pour connaître les obligations qui s'appliquent. Le guide d'août 2026 a été vérifié par texte extrait; sa capture d'écran PDF a échoué en raison d'une erreur de cache.

### Les six pièces qui manquent encore

Le registre décrit les documents nécessaires à une preuve réelle : **(1)** ordre de paiement ou transfert gouvernemental attesté; **(2)** encaissement au registre municipal ou relevé public; **(3)** factures finales par année et projet; **(4)** emprunt décaissé et calendrier de remboursement; **(5)** facture annuelle de taxes selon propriété et secteur; **(6)** preuves de maintien de l'emploi et de la qualité du service.

**Aucune de ces six preuves n'a été déclarée obtenue.** Cela ne veut pas dire que les paiements n'ont pas eu lieu : seulement que **l'étude actuelle ne les démontre pas**.

## 5. Conséquences pour la réforme fiscale Nova

Le Projet Nova propose de simplifier radicalement les prélèvements, avec une fiscalité sur le revenu et une approche contre les paradis fiscaux. Les exemples de Warwick montrent pourquoi il est indispensable de distinguer :

1. **Québec dans le Canada :** la fiscalité provinciale ne peut pas, par une simple déclaration, abolir les prélèvements municipaux ni modifier unilatéralement les compétences fédérales; les obligations de dette doivent rester financées.
2. **Québec souverain :** le partage des actifs, des dettes, des programmes et des obligations ne peut pas être présumé; il faut une analyse juridique et financière spécifique.
3. **Pouvoir d'achat :** la baisse d'un prélèvement ne protège personne si elle provoque une nouvelle tarification opaque, un sous-financement de l'eau ou un déplacement de coûts vers les ménages et les entreprises.
4. **Travailleurs :** assurer le financement des services, des conventions collectives, de la formation et de la retraite avant de promettre des gains.
5. **Crédibilité :** publier des budgets sur dix ans avec les données manquantes explicitement inconnues plutôt que de fournir un taux ou une économie imaginaires.

Le registre `data/taxes-warwick-2026-et-preuves-versements-g0-16o.json` contient les taux, les compensations, les limites de la méthode, un exemple fictif calculable et **deux scénarios sur dix exercices dont les montants restent `null`**. Le module `assets/g016o-warwick-tax-core.mjs` interdit les véritables factures inventées. La suite `tests/g016o-warwick-tax-and-grants.test.mjs` déclare **39 cas réussis lors d'un rejeu JavaScript isolé**; l'exécution native GitHub Actions n'est pas attestée.

**Verdict :** la fiscalité municipale effective est désormais documentée pour un exemple local réel en 2026, mais pas le fardeau individuel constaté ni les paiements de subventions, pas le financement d'une réforme à deux prélèvements et pas l'audit indépendant. **Score global inchangé : 47/100.**

**Suite G0.16p :** obtenir les règlements de taxation 2026, les rapports financiers et les pièces de versement disponibles pour Port-Daniel, Gatineau, Laval et La Doré; construire des comparaisons par rôle foncier et type de services, puis tester des effets distributifs sur des ménages types sans jamais les faire passer pour des factures réelles.
