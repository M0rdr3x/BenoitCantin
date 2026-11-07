# NOVA-FIN-G0.16b — Premiers repères publics pour le revenu et le coût de la vie

**Projet :** Projet Nova | **Date de vérification :** 7 novembre 2026  
**Statut :** note de recherche technique, **non normative**. Aucun budget, taux ou gain de revenu Nova n'est validé.  
**Avancement du programme :** **47/100** selon l'audit G0.12 du 5 novembre 2026; aucune révision de la grille n'est justifiée par ces deux transcriptions.

## 1. Objet

L'étape G0.16a a défini une structure de simulation à dix déciles pour deux scénarios : Québec **dans le Canada** et Québec **souverain**. Avant de la calibrer, G0.16b identifie des données historiques réelles et exige une séparation stricte des **unités statistiques**, des **millésimes**, des **conventions de revenu** et des **niveaux de preuve**.

**Résultat vérifié à cette étape :** deux repères descriptifs de 2023 (revenu ajusté et dépenses moyennes) transcrits depuis deux pages officielles publiées sur le Web; deux catalogues additionnels identifiés; **aucune microdonnée**, aucune estimation individuelle et aucun modèle distributif financé.

## 2. ISQ — limites supérieures des déciles, après impôt ajusté, Québec 2023

**Source directe :** https://statistique.quebec.ca/fr/produit/tableau/limite-superieure-deciles-revenu-repartition-menages-deciles-type-revenu-menage-revenu-ajuste-taille-menage  
**Institution :** Institut de la statistique du Québec (adaptation de l'Enquête canadienne sur le revenu 2023 de Statistique Canada).  
**Mise à jour de la source :** 20 octobre 2025. **Vérifiée sur la page le :** 7 novembre 2026.  
**Variable :** « Revenu après impôt », ajusté selon la racine carrée de la taille du ménage. Le revenu après impôt est le revenu total du ménage moins les impôts fédéral et provincial, selon la note de l'ISQ.

| Décile | Limite supérieure publiée | Unité |
| --- | ---: | --- |
| D1 | 25 500 $ | CAD courants 2023, revenu ajusté |
| D2 | 32 300 $ | idem |
| D3 | 39 400 $ | idem |
| D4 | 45 700 $ | idem |
| D5 | 52 200 $ | idem |
| D6 | 58 800 $ | idem |
| D7 | 66 800 $ | idem |
| D8 | 77 300 $ | idem |
| D9 | 94 900 $ | idem |
| D10 | **Non chiffrée (x)** | ne pas remplacer par zéro ou une estimation |

**Ce que ce tableau ne montre pas :** un revenu moyen par décile, les assiettes imposables Nova, les cotisations sociales individualisées, les dépenses essentielles des mêmes ménages ou les revenus de 2026. Une **limite supérieure** de décile n'est pas une « famille type » et ne peut être insérée comme revenu représentatif dans une simulation.

## 3. Statistique Canada — dépenses des ménages québécois, 2023

**Source directe :** https://www150.statcan.gc.ca/n1/daily-quotidien/250521/t001a-fra.htm  
**Institution :** Statistique Canada, Enquête sur les dépenses des ménages, 2023; publié le 21 mai 2025; vérifié le 7 novembre 2026.

| Indicateur | Résultat publié |
| --- | ---: |
| Dépenses moyennes des ménages en biens et services, Québec | **65 344 $** |
| Part du logement | **27,1 %** |
| Part du transport | **16,9 %** |
| Part de l'alimentation | **17,3 %** |

Ces parts concernent les **dépenses provinciales moyennes** et **non** les dépenses d'un ménage appartenant à D1, D5 ou D10. Il est interdit de multiplier mécaniquement chaque seuil de décile ISQ par les parts de dépenses StatCan : les deux publications ne sont pas une base appariée, et revenu ajusté par équivalent-personne ≠ dépenses par ménage brut. Les taxes indirectes peuvent déjà figurer dans les prix; elles ne doivent pas être comptées deux fois.

## 4. Catalogues publics complémentaires identifiés — fichiers non importés

- **Statistiques fiscales des particuliers (année d'imposition 2023)** : ministère des Finances du Québec, https://www.quebec.ca/gouvernement/ministeres-organismes/finances/publications . Le catalogue annonce une table XLSX. **Aucun octet, aucune feuille ni empreinte SHA-256 n'a été extrait** dans cette étape.
- **Revenu disponible par habitant des régions et MRC, année 2024** : ISQ, https://statistique.quebec.ca/fr/document/revenu-disponible-par-habitant-regions-administratives-et-mrc . Il s'agit d'un indicateur **par habitant**, non d'une distribution du revenu ajusté des ménages; les valeurs régionales ne sont pas intégrées au registre.

Le cadre financier G0.13–G0.14 utilise par ailleurs les **prévisions publiques 2026–2027** du rapport préélectoral d'août 2026. Ce millésime budgétaire est distinct des observations sociales 2023 et des observations régionales 2024.

## 5. Portes méthodologiques fermées

| Preuve manquante | Pourquoi elle est requise |
| --- | --- |
| Assiettes des personnes et entreprises vérifiées | Un décile de revenu après impôt n'indique pas le montant légalement taxable ni la distribution de profits |
| Contributions et prestations RRQ/RQAP/santé | Garantir droits acquis, financement des obligations et revenu réellement disponible |
| Dépenses par décile et composition | Évaluer le reste à vivre sans attribuer artificiellement une moyenne provinciale |
| Équivalences et années harmonisées | Corriger tailles des ménages, inflation, fiscalité et définition du revenu |
| Effet sur prix et salaires | Modéliser l'incidence de la suppression ou du maintien des impôts indirects |
| Québec au Canada vs Québec souverain | Séparer compétences, recettes, coûts et responsabilités fédérales à reprendre |
| Accès autorisé aux données détaillées et revue indépendante | Prévenir réidentification et conclusions politiques non justifiées |

## 6. Contrôle de qualité et intégrité

Les sources, périodes, unités, neuf seuils numériques ISQ et valeurs de dépenses StatCan sont conservés dans `data/reperes-publics-g0-16b-2023.json`.

Le code `assets/g016b-public-benchmarks-core.mjs` refuse les transcriptions altérées, une valeur numérique inventée pour D10, la fusion par décile des deux sources, les changements de statut et les gains fiscaux artificiels. Les tests de non-régression figurent dans `tests/g016b-public-benchmarks.test.mjs`.

**La transcription est effectuée à partir des pages Web publiques** : les tableaux originaux complets, leurs fichiers binaires et leurs métadonnées de chaîne de collecte ne sont pas archivés dans cette étape; **aucune contre-vérification signée par un second analyste n'est acquise**.

## 7. Suite opérationnelle : G0.16c

1. Importer, sous un protocole d'intégrité traçable, les tableaux détaillés du ministère des Finances concernant les revenus imposables, déductions et crédits, sous réserve des conditions d'accès.
2. Établir les définitions communes : unité ménage/personne/entreprise, période, échelle d'équivalence, impôts et cotisations, prix, prestations, taille des échantillons.
3. Obtenir les distributions de dépenses par revenu, selon des sources autorisées, avec indicateurs de précision et règles anti-réidentification; **ne pas déduire les dépenses par décile de la moyenne provinciale**.
4. Couvrir les quinze preuves V01–V15 de G0.15 par des travaux vérifiables et soumettre la méthode à une validation indépendante.
5. Après seulement, produire des **scénarios exploratoires explicitement hypothétiques**; aucune annonce fiscale ou suppression de prélèvements avant examen juridique, budgétaire et démocratique.

**Statut de clôture :** premiers repères documentaires obtenus; **G0.16b non calibrée**, **G0.16 non franchie**, aucune estimation de gain/pouvoir d'achat Nova, **score 47/100 maintenu**.

Les documents `official/reference/*` et le manifeste `data/sources.json` restent des références séparées et ne sont pas modifiés par cette recherche.
