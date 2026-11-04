# NOVA-SINJ-G0-SAN-005 — Portrait régional vérifiable des soins de première ligne (G0.4)

**Projet :** Projet Nova — démarche analytique Nova–Sinjira  
**Version :** 2.0, 3 novembre 2026  
**Statut :** résultats publics transcrits et contrôlés en interne, **non audités indépendamment**; dossier de travail non adopté.  
**Porte de décision :** G0 **non franchie**. Aucun pilote, aucune réaffectation, aucune privatisation et aucune économie autorisés.

## 1. Origine exacte des 16 chiffres : source disponible et méthode

**Source primaire officielle :** Institut de la statistique du Québec, *Panorama des régions du Québec, édition 2026*, chapitre 8, « Besoins de consultation en services de santé et en services sociaux », publication du **2 novembre 2026**, document autonome :
https://statistique.quebec.ca/fr/fichier/panorama-des-regions-du-quebec-2026-sante.pdf .

- **Tableau 8.1, page imprimée 144, page PDF 13/17 (index 12)** : 16 taux régionaux d'affiliation, trois endroits habituels de suivi pour les **personnes affiliées**, ainsi que les indications de significativité et de précision.
- **Tableau 8.3, page imprimée 146, page PDF 15/17 (index 14)** : démarches déclarées pour obtenir une consultation lors du **dernier** besoin de santé **semi-urgent ou non urgent**, pour les adultes concernés.
- **Population :** personnes de 18 ans et plus vivant en logement non institutionnel dans le champ de l'EQUSSSS 2025. Enquête menée du **6 janvier au 11 mai 2025** auprès de **9 391 personnes**, excluant la RSS **17 (Nunavik)** et la RSS **18 (Terres-Cries-de-la-Baie-James)**.
- Le classeur XLSX détaillé https://statistique.quebec.ca/fr/fichier/utilisation-services-sante-services-sociaux-2025-tableaux-rss.xlsx reste **non récupéré et non analysé**. Les chiffres ci-dessous proviennent **du PDF, pas d'un prétendu import XLSX**.
- **Méthode de transcription :** lecture du tableau textuel indexé du PDF, contrôle de l'ordre des 16 RSS, rapprochement des pourcentages d'affiliation avec le texte analytique et des indicateurs de somme de lieux (arrondis); contrôle des marques (+), (−), * et **. L'outil de capture visuelle du PDF n'a pas pu accéder au fichier (cache indisponible) : une vérification visuelle humaine et un audit externe restent souhaitables avant décision de politique.

Le fichier `data/portrait-regional-g0-sante-2025.json` documente les pourcentages, leur provenance, les mises en garde et les données absentes. Les **coûts**, **effectifs régionaux**, **intervalles de confiance** et **qualité clinique** ne sont pas tirés de ce tableau et restent inconnus.

## 2. Tableau des 16 taux régionaux d'affiliation (tableau 8.1)

Pourcentage d'adultes déclarant une affiliation à un médecin de famille, un GMF ou une IPS en 2025.

| RSS | Territoire | Taux | Différence statistique rapportée versus reste du Québec |
| --- | --- | ---: | --- |
| 01 | Bas-Saint-Laurent | 88,9 % | Supérieure (+) |
| 02 | Saguenay–Lac-Saint-Jean | 87,6 % | Supérieure (+) |
| 03 | Capitale-Nationale | 82,9 % | Aucune différence signalée |
| 04 | Mauricie et Centre-du-Québec | 85,1 % | Aucune différence signalée |
| 05 | Estrie | 79,3 % | Aucune différence signalée |
| 06 | Montréal | 77,1 % | Inférieure (−) |
| 07 | Outaouais | 85,8 % | Aucune différence signalée |
| 08 | Abitibi-Témiscamingue | 80,0 % | Aucune différence signalée |
| 09 | Côte-Nord | 81,1 % | Aucune différence signalée |
| 10 | Nord-du-Québec | 88,8 % | Supérieure (+) |
| 11 | Gaspésie–Îles-de-la-Madeleine | 89,1 % | Supérieure (+) |
| 12 | Chaudière-Appalaches | 80,3 % | Aucune différence signalée |
| 13 | Laval | 84,8 % | Aucune différence signalée |
| 14 | Lanaudière | 87,2 % | Supérieure (+) |
| 15 | Laurentides | 79,8 % | Aucune différence signalée |
| 16 | Montérégie | 83,9 % | Aucune différence signalée |
| **QC** | **Ensemble des adultes visés du Québec** | **82,0 %** | Référence, pas dix-septième RSS |

**Seuil statistique des marques (+)/(−) : 5 %**, comparaison de la région au **reste du Québec**. Une absence de (+)/(−) signifie que le tableau ne signale pas de différence statistiquement significative à ce seuil pour cette variable; cela ne veut pas dire égalité des régions. Ne pas recalculer de test sans données d'enquête et plan d'échantillonnage.

## 3. Deux autres lectures du même corpus (dénominateurs différents)

### 3.1 Lieu habituel de suivi parmi les personnes affiliées — tableau 8.1
Dans l'ensemble du Québec, parmi les personnes affiliées, la part déclarant un suivi habituel en **clinique médicale/clinique IPS/GMF/CLSC** est **85,1 %**, en **hôpital ou autre endroit** **7,8 %**, et dans une **clinique privée** **7,1 %**. Les trois catégories s'additionnent à environ 100 % (écarts d'arrondis possibles).

À titre d'illustrations descriptives :
- **Montréal** : 80,3 % suivi en clinique/GMF/CLSC, 10,9 % à l'hôpital ou ailleurs, 8,9 % en clinique privée.
- **Côte-Nord** : 73,6 % suivi en clinique/GMF/CLSC, 20,6 % à l'hôpital ou ailleurs, 5,9 % en clinique privée (cette dernière estimation porte un astérisque `*` de prudence).
- **Nord-du-Québec** : 80,2 % en clinique/GMF/CLSC, 17,9 % à l'hôpital ou ailleurs, 2,0 % en clinique privée; l'estimation privée porte `**`, imprécise et indicative.

**Ne pas déduire du mot « clinique privée » le mode de paiement des soins, la participation à la RAMQ, la nature juridique du professionnel, le tarif par acte ou les bénéfices.** Il s'agit d'un lieu de suivi **déclaré** par les personnes affiliées, et non d'une analyse comptable des cliniques.

### 3.2 Démarche « être allé(e) à l'urgence » — tableau 8.3
L'enquête a demandé les démarches lors du **dernier besoin de consultation** d'une personne ayant eu besoin de consulter **pour elle-même**, pour un problème **semi-urgent ou non urgent**, au cours des 12 derniers mois. Plusieurs démarches étaient possibles.

| Territoire | « Être allé(e) à l'urgence » | Qualité publiée |
| --- | ---: | --- |
| Nord-du-Québec | **41,5 %** | (+), pas de marque CV |
| Côte-Nord | **31,0 %** | (+), pas de marque CV |
| Bas-Saint-Laurent | **21,3 %** | (+), `*` prudence |
| Montréal | **10,0 %** | Pas de différence signalée |
| Ensemble du Québec | **11,1 %** | Référence |

**Ces pourcentages ne sont ni un taux annuel de passages aux urgences, ni des visites comptabilisées, ni une preuve que l'affiliation a provoqué ou empêché ces démarches.** Ils ne peuvent pas être soustraits à un indicateur d'urgence tiré d'un autre sous-échantillon ou d'une autre enquête.

### 3.3 Lecture stratégique, sans inférence causale
**Le Nord-du-Québec illustre le risque d'un indicateur unique : affiliation 88,8 %, mais démarche vers une urgence 41,5 % au dernier besoin semi-urgent ou non urgent chez le sous-groupe considéré.** Les deux pourcentages ont **des populations et événements de référence différents**. L'écart ne mesure pas une conversion ou une cause et ne constitue pas un score de qualité. La disponibilité de ressources et les parcours de soins doivent être étudiés avant toute conclusion.

## 4. Mises en garde statistiques et géographiques
- `*` indique un coefficient de variation compris entre **15 % et 25 %** : interpréter avec prudence.
- `**` indique un coefficient de variation **supérieur à 25 %** : estimation imprécise, présentée à titre indicatif.
- `(+)`/`(−)` indique une différence significative au seuil de **5 %**, d'une RSS **versus reste du Québec** (dans l'enquête).
- La part provinciale **82,0 %** résulte de l'estimation d'enquête; ne pas l'obtenir par moyenne non pondérée des 16 proportions.
- Les **effectifs par RSS**, poids d'enquête, intervalles de confiance et microdonnées **ne sont pas extraits de ce PDF**. Ne pas créer d'intervalles artificiels, de rangs d'efficacité ou de tests maison.
- **Nunavik et Terres-Cries-de-la-Baie-James : hors champ de l'enquête**, pas hors des obligations de continuité des services ou des processus adaptés de consultation.
- **18 RSS ≠ 17 régions administratives**. Le découpage diffère pour la Mauricie/Centre-du-Québec et les frontières de l'Estrie/Montérégie.
- Les **indicateurs d'attitration administratifs** Santé Québec/RAMQ et **le rappel GAP** mesurent d'autres événements et ne peuvent être comparés sans dictionnaire et rapprochement.

## 5. Qualité et audit du jeu Nova
**Niveau de granularité :** une ligne = une région sociosanitaire, référencée par code 01 à 18. Pour les régions 17 et 18, les valeurs restent `null` avec la raison `HORS_CHAMP_ENQUETE`.

**Vérifications désormais réalisables :**
1. Unicité de 18 codes; 16 lignes observées et 2 hors enquête.
2. Pourcentages 2025 entre 0 et 100, une décimale, source table 8.1.
3. Conformité des **5 marques positives et de la marque négative Montréal** pour l'affiliation.
4. Qualité des trois lieux habituels : somme approximativement 100 % avec tolérance d'arrondi.
5. Marque de prudence `*` ou `**` conservée par indicateur.
6. Table 8.3 : pourcentage des démarches d'urgence publié pour chaque RSS; sources et dénominateurs distincts.
7. Aucun tarif régional, effectif clinique, intervalle de confiance ni effet de privatisation imputé.
8. Aucune décision G0 automatiquement franchie; aucune région pilote désignée.

**Limites de qualité résiduelles :** lecture visuelle du PDF non disponible par l'outil de capture; extraction XLSX pas réalisée; statut des informations **contrôlées en interne à partir des tableaux publics, sans certification indépendante**.

## 6. Blocage G0 et suite logique G0.5
Pour proposer des comparaisons d'efficacité :
- obtenir les tableaux XLSX complets de l'ISQ si besoin de notes, effectifs et intervalles, en conservant leurs empreintes et versions;
- établir l'accès **effectivement reçu**, et non seulement l'affiliation ou une démarche;
- disposer de **coûts complets par épisode et opérateur**, avec périmètre homogène, imputation des frais et ajustement à la complexité;
- documenter les **ETP nets** et les effets de déplacement de personnel;
- sécuriser les données, valider les fondements légaux et les limites des demandes de documents existants;
- prévoir une évaluation indépendante et un mécanisme de plainte et de sortie.

**Conclusion : les 16 taux d'affiliation sont désormais sourcés et transcrits, contrairement au statut G0.3. G0 n'est toujours pas franchie, faute de coûts, de qualité clinique, de délais réellement obtenus et de garanties évaluées.**
