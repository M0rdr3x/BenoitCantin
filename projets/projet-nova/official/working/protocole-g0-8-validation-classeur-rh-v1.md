# NOVA-SINJ-G0-SAN-012 — Validation du classeur RH officiel et préparation de l'analyse régionale (G0.8)

**Projet :** Projet Nova — Santé et capacité de service  
**Date :** 4 novembre 2026  
**Statut :** protocole de contrôle et d'extraction conditionnelle, **non adopté, non approuvé par les autorités**.  
**Porte de décision :** G0 **NON FRANCHIE**.

## 1. Résultat confirmé et limite
La page officielle du gouvernement du Québec, mise à jour le **27 avril 2026**, référence le fichier **« Portrait du personnel des établissements publics et privés conventionnés du réseau de la santé et des services sociaux (2024-2025) »** (XLSX, 136 Ko).

- Catalogue officiel : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-humaines
- Source XLSX : https://cdn-contenu.quebec.ca/cdn-contenu/sante/documents/Systeme_et_services_de_sante/organisation-services/donnees-systeme-sante-quebecois-services/ressources-humaines/denombrement-et-remuneration-effectif-rsss-2024-2025.xlsx

À la date de ce rapport, l'URL est vérifiée via la page officielle et l'outil Web; la récupération des octets XLSX a **échoué** depuis les environnements de travail. **Aucun total régional, aucune feuille et aucune formule du classeur ne sont analysés.** Le registre demeure sans valeurs de personnel ni ETP.

## 2. Pourquoi G0.8 est un changement substantiel par rapport à G0.7

G0.7 contrôlait la **structure ZIP** de l'archive, sa taille, la source et son SHA‑256. G0.8 ajoute une **deuxième porte documentaire L2** avant de qualifier le classeur d'« acquis mais non interprété » :

- vérification des en-têtes ZIP **locaux et centraux**, des tailles et CRC-32 du contenu XML déclaré;
- refus des archives chiffrées, des chemins non sûrs, des doublons de pièces, des macros, ActiveX, liens externes et contenus incorporés;
- inspection de `[Content_Types].xml`, `xl/workbook.xml` et `xl/_rels/workbook.xml.rels`;
- identification et concordance des références internes des feuilles, de leurs noms, visibilité, chemins et dimensions déclarées;
- refus des `DOCTYPE`/`ENTITY` dans les parties XML lues;
- limites strictes de taille de l'archive et de ses parties XML, afin de réduire les risques d'archives malveillantes ou démesurées;
- rapport **uniquement sur la structure**, sans extraire les cellules de rémunération, les travailleurs, les épisodes de soins ou les coûts.

**Limite technique importante :** ce contrôle n'est pas un parseur OOXML complet, une analyse antivirus, une signature numérique gouvernementale, ni une validation de l'authenticité des statistiques. Un SHA‑256 prouve la stabilité d'une copie, pas que le producteur a signé les chiffres. Une inspection institutionnelle ou experte reste nécessaire.

## 3. Contrôle en deux temps des pièces de preuve

### Premier temps : réception du fichier
Le workflow existant `.github/workflows/nova-g07-acquisition-rh.yml` est **manuel seulement** et détient `contents: read`. Il doit maintenant satisfaire :
1. les tests G0.7 **et** les nouveaux tests G0.8;
2. le téléchargement HTTPS du CDN gouvernemental autorisé;
3. `readXlsxZipDirectory` pour l'inventaire de base;
4. `inspectOfficialRhWorkbook` pour le contrôle XML et la correspondance des feuilles;
5. `inspectAcquisitionManifest` avec les nouvelles métadonnées L2 obligatoires.

Les pièces créées seulement en cas de succès sont le classeur source et un rapport `source-audit.json` contenant : taille, SHA-256, date UTC, éventuels ETag/Last-Modified, noms et dimensions des feuilles, statuts des contrôles. L'artefact GitHub Actions expire après 14 jours. Aucun commit n'est généré.

Si la source ne passe pas L1/L2, le rapport doit la classer **`DOWNLOAD_BLOCKED`**, sans empreinte fictive, sans validation numérique et sans confirmation trompeuse.

### Deuxième temps : examen statistique et cartographie des cellules (conditionnel, ultérieur)
Le fichier doit être ouvert et examiné avec une méthode reproductible capable d'identifier les **cellules et en-têtes réels**. Sans cet examen, il est interdit de faire une conversion numérique.

Chaque table retenue nécessitera une fiche structurée :
- `workbook_sha256`, `sheet_name`, `table_title`, `cell_range`, `notes`;
- `measure_id`, `source_unit`, `numerator_denominator`, `employment_status`;
- `profession_group`, `geography_type`, `rss_code` lorsqu'applicable;
- `period_start`, `period_end`, `population`, `scope_included_excluded`;
- `aggregate_validated`, `comparison_allowed`, `privacy_review`, `independent_reviewer`.

Le document statistique pourrait indiquer des **personnes par catégorie et statut**, mais la réalité de cette colonne doit être vérifiée. Il n'y a pas de garantie que la source contienne les heures cliniques nécessaires aux **ETP de première ligne**, les affectations en GMF, les effectifs nets transférés, les chiffres des professionnels rémunérés par la RAMQ ou des coûts par épisode.

Ne pas calculer `ETP = nombre de personnes`, ni `temps présent = soins dispensés`. Ne pas ajouter l'effectif des professionnels rémunérés par la RAMQ au personnel R22 sans méthode d'exclusion des doubles comptes et alignement des professions.

## 4. Treize critères de qualité avec statut traçable

Le fichier `data/registre-verification-classeur-rh-g0-8.json` recense **13 critères**, dont seul le premier est identifié à partir de la page officielle; les autres restent bloqués jusqu'à obtention et examen des octets :

| Code | Domaine |
| --- | --- |
| SRC-01 | Origine officielle, période, droits |
| ZIP-02 | Intégrité ZIP et SHA-256 |
| XML-03 | Feuilles et relations OOXML |
| SCH-04 | Schéma, lignes, colonnes, unités |
| GEO-05 | RSS versus autres périmètres géographiques |
| PER-06 | Exercice 2024–2025 versus observation actuelle |
| RHU-07 | Distinction personnes, présence, heures, ETP |
| COV-08 | Couverture et exclusions R22, privés et RAMQ |
| DUP-09 | Doubles comptes et totaux de regroupements |
| PRI-10 | Confidentialité et petits effectifs |
| REC-11 | Réconciliation avec totaux source |
| ETP-12 | Preuve indépendante d'ETP cliniques première ligne |
| APR-13 | Revue professionnelle indépendante et approbation formelle |

Le registre couvre **18 RSS** de suivi, sans supposer que toutes les données de la source ont ce découpage. Toutes les colonnes RH restent `null`, pas zéro. Les taux d'affiliation régionaux ISQ 2025 peuvent rester présents à titre de **contexte**, mais ne valident pas les effectifs 2024–2025.

## 5. Critères de refus et de divulgation
- **Sécurité** : fichier sans source officielle, non XLSX, mal structuré, chiffré ou présentant des relations externes => **rejet de l'import**.
- **Qualité** : métadonnées de feuilles sans évaluation des en-têtes ou unités => **aucun chiffre exportable**.
- **Géographie** : regroupements non comparables, lignes de totaux, géographies manquantes => **pas d'attribution aux RSS**.
- **Calendrier** : dénombrement 2024–2025 et enquête ISQ 2025 ≠ même observation clinique; **pas de série de 2026 extrapolée**.
- **Personnel** : salariés de certains établissements ≠ professionnels RAMQ ≠ ETP cliniques; **pas de calcul d'une hausse nette sans preuve d'heures et de transferts**.
- **Finances** : salaires et rémunération ≠ coût complet des consultations; **aucune économie ni transfert approuvé**.
- **Confidentialité** : aucune donnée nominative de rémunération ou de santé publiée; protection des petites cellules et permission de diffusion à vérifier.
- **Gouvernance** : un fichier structurément valide ne permet pas de passer G0. Une revue clinique, financière, humaine et juridique est obligatoire.

## 6. État et suite logique
**État au 4 novembre 2026 :** source officielle identifiée, XLSX non obtenu, inspection L2 du fichier réel non réalisée, 13 critères identifiés, 18 RSS en attente et zéro ETP vérifié.

**G0.9, après obtention réelle :** inspecter les feuilles et les dimensions documentaires, définir précisément les séries agrégées utilisables, contrôler les notes, les suppressions, les totaux et les partitions par période. S'il manque les heures cliniques, ne pas calculer d'ETP : documenter cette impossibilité et préparer une demande d'information administrative ciblée.

**Le projet demeure à l'étape de la preuve; aucune modification du programme candidat, des lois proposées ni du budget n'est autorisée.**
