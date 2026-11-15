# Projet Nova — G0.16j | Coûts réellement constatés des services municipaux

**Version de travail : 7 novembre 2026**  
**Préparation globale du programme : 47/100 (53 points restants selon le dernier audit G0.12).**  
**Statut : concordance documentaire historique, non adoption et non viabilité financière démontrée.**

## 1. Progrès substantiel depuis G0.16i

Les étapes G0.16h et i ont ajouté les recettes municipales 2024 puis une analyse purement arithmétique de suppression hypothétique de taxes. **G0.16j établit maintenant où se retrouvaient réellement les dépenses des services locaux**, ce qui était indispensable pour élaborer les garanties de continuité voulues par Nova.

Le document primaire est le **[rapport financier consolidé 2024 — sommation des municipalités locales](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/rapports_financiers_organismes_municipaux/2024/RAP_financier_2024_sommation_municipalites_locales.pdf)** du ministère des Affaires municipales et de l'Habitation (MAMH), consulté aux **pages PDF 7 (S7, p. 3), 51 (S28, p. 47), 52 (S28, p. 48)**. Les pages **S28 sont explicitement indiquées « Non audité »**.

La sommation rassemble **1 056 municipalités locales** au 17 mars 2026. Elle ne couvre pas toutes les collectivités ni toutes les formes d'organismes municipaux du Québec, et ne prouve pas que le groupe de municipalités comparé est rigoureusement constant entre 2023 et 2024. Les montants ci-dessous sont des **dépenses réelles enregistrées en dollars de leurs exercices respectifs**, sans correction de prix ni projection.

## 2. Ventilation exhaustive des fonctions pour les municipalités incluses

| Dépenses consolidées | 2024 (M$) | 2023 (M$) |
| --- | ---: | ---: |
| Administration générale | 3 441,813 | 3 115,735 |
| Sécurité publique | 4 510,159 | 4 218,785 |
| Transport | 8 699,354 | 8 336,293 |
| Hygiène du milieu | 4 178,810 | 3 889,761 |
| Santé et bien-être | 599,704 | 519,888 |
| Aménagement, urbanisme et développement | 1 368,708 | 1 236,665 |
| Loisirs et culture | 3 813,614 | 3 569,751 |
| Réseau d'électricité | 409,672 | 398,862 |
| Frais de financement | 1 332,061 | 1 181,428 |
| Effet net des opérations de restructuration | 13,064 | 1,881 |
| **Total exact (avant l'arrondi du tableau)** | **28 366,959822** | **26 469,048805** |

Le rapprochement dans `data/ventilation-charges-municipales-g0-16j-2024.json` est effectué **en dollars entiers**. La somme des dix fonctions est exactement **28 366 959 822 $ pour 2024** et **26 469 048 805 $ pour 2023**, identiques à l'état général du MAMH et aux montants déjà consignés dans G0.16h. Les éventuels écarts de la version arrondie à trois décimales ne doivent pas remplacer ce rapprochement exact.

**Méthode de non-double-compte :** les frais de financement, ainsi que les dépenses des sous-catégories décrites ci-dessous, sont **déjà inclus dans les totaux**. Ne pas leur ajouter à nouveau des montants de routes, d'eau, d'incendie ou de dette.

## 3. Services municipaux concrets : sous-postes du total, et non nouvelles charges

Des sous-totaux de services spécifiques ont été calculés à partir des lignes S28 et rapprochés de leurs catégories principales :

| Sous-ensemble précis de dépenses | 2024 | 2023 | Inclus dans |
| --- | ---: | ---: | --- |
| Approvisionnement, traitement et distribution d'eau potable; traitement et réseaux d'eaux usées | **2 519,427 M$** | **2 363,826 M$** | Hygiène du milieu |
| Voirie municipale et déneigement | **3 711,874 M$** | **3 639,527 M$** | Transport |
| Services incendie, premiers répondants et autres activités incendie | **1 533,112 M$** | **1 439,147 M$** | Sécurité publique |

Le rapprochement est exact en dollars pour chacun des sous-ensembles.

**Échantillons de postes individuels 2024 :**
- Approvisionnement et traitement de l'eau potable : **587 281 926 $**;
- Distribution de l'eau potable : **766 770 167 $**;
- Traitement des eaux usées : **564 654 613 $**;
- Réseaux d'égouts : **600 720 086 $**;
- Voirie municipale : **2 551 882 022 $**;
- Déneigement : **1 159 992 215 $**;
- Police : **2 769 781 797 $**;
- Transport en commun : **4 187 478 816 $**;
- Logement social : **399 545 604 $**.

Ces chiffres **ne constituent pas un niveau de service minimal légalement requis, un budget 2026 ou un montant permettant d'abolir une taxe**. Certains investissements, obligations futures, actifs, concessions, retraites et flux interadministratifs doivent être vérifiés séparément.

## 4. Contrôles de cohérence inter-documents

G0.16j conserve trois niveaux **distincts** :

1. **Sources historiques MAMH** : 2023 et 2024, y compris toutes les fonctions et 34 postes supplémentaires de sécurité, transport, environnement et bien-être.
2. **Test de sensibilité G0.16i** : les hypothèses de retraits de recettes fiscales de 2024 sont arithmétiques; un déficit reconstitué n'est **pas** un déficit politique prédit.
3. **Budgets futurs Nova** : vingt exercices séparés, de **2026–2027 à 2035–2036**, pour **Québec au Canada** et **Québec souverain**. Les dépenses, recettes de remplacement, transferts, coûts des droits des travailleurs et soldes restent **`null`**, sans approbation.

Il serait incorrect d'additionner « 2,519 G$ d'eau » à « 4,179 G$ d'hygiène du milieu » ou « 3,712 G$ de routes/déneigement » à « 8,699 G$ de transport » : les premiers montants sont inclus dans les seconds.

Le système de recettes municipales, les règles scolaires et la fiscalité fédérale ne sont pas interchangeables. Pour le Québec souverain, toute répartition de dette et reprise de compétences exige un budget légal et financier autonome.

## 5. Politique de continuité recommandée pour examen, non adoptée

La garantie Nova devrait lier toute décision de réforme fiscale à **des preuves de fonctionnement des services dans chaque territoire**, notamment :
- maintien de l'approvisionnement en eau et de l'assainissement, avec données sur l'état des installations;
- sécurité incendie, sécurité civile et continuité des transports et du déneigement;
- entretien des infrastructures et planification des besoins d'investissement;
- respect des emplois locaux, contrats, conventions, pensions et autres droits acquis;
- financement du service de la dette et comptabilisation des transferts entre administrations;
- indicateurs d'accès, de qualité et de couverture pour les municipalités éloignées et vulnérables.

La méthode proposée est de comparer les résultats **avant/après par service, territoire et catégorie de contribuables**, en produisant des effets distributifs, sans retirer des emplois pour produire des économies artificielles. Ce sont des critères de préparation, non des décisions d'un gouvernement.

## 6. Prochain travail G0.16k : combler les données de continuité et obtenir les revues

Six conditions restent ouvertes :
1. Obtenir des données financières 2025/2026 réellement comparables pour les services municipaux;
2. Rapprocher les comptes des municipalités absentes, MRC, régies, transports et autres entités;
3. Définir le coût futur du maintien des services et le niveau de qualité à atteindre;
4. Éliminer les doubles comptes des transferts et rattacher correctement les obligations du personnel, des retraites et de dette;
5. Construire et financer deux modèles budgétaires décennaux distincts;
6. Obtenir les avis juridiques, financiers et sociaux indépendants, les mécanismes de recours et l'approbation politique.

Aucune de ces conditions ne peut être déclarée remplie par la simple présence d'un tableau historique.

## 7. Preuves techniques et verdict

- `data/ventilation-charges-municipales-g0-16j-2024.json` : 10 catégories majeures, 34 détails, trois sous-ensembles calculés, deux exercices et deux scénarios constitutionnels non chiffrés.
- `assets/g016j-municipal-services-core.mjs` : contrôle des données exactes, des rapprochements, des sources, des sous-totaux et des interdictions de financement ou de validation fictifs.
- `tests/g016j-municipal-services.test.mjs` : **38 tests déclarés et 38 réussis en rejeu JavaScript isolé**; cela n'atteste **pas** une exécution GitHub Actions/Node native.
- Pages PDF identifiées et vérifiées visuellement : **7, 51 et 52**.

**Décision G0.16j :** rapprochement historique des charges **documenté**; coûts futurs et possibilité d'une réforme fiscale **non démontrés**. L'adoption et l'audit indépendant manquent. Le score du programme reste **47/100**; aucun changement aux textes candidats `official/reference/*` ou au manifeste `data/sources.json`.
