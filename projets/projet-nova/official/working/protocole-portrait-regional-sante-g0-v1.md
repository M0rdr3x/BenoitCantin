# NOVA-SINJ-G0-SAN-004 — Portrait régional de l'accès aux soins (G0.3)

**Projet :** Projet Nova — étude Nova–Sinjira  
**Date :** 3 novembre 2026  
**Statut :** référence analytique **partielle**, non adoptée; porte G0 **non franchie**.  
**Objet :** établir un découpage géographique fiable avant de comparer la qualité et le coût complet de la première ligne. Aucune sélection de région pilote ni réallocation budgétaire.

## 1. Trois références officielles à respecter

1. **ISQ — 2 novembre 2026, Enquête québécoise sur l'utilisation des services de santé et des services sociaux 2025.** L'enquête couvre les adultes de 18 ans et plus vivant en logement non institutionnel selon son plan d'enquête; elle **exclut les RSS 17 et 18**. Affiliation provinciale déclarée : **82 %**. Source : https://statistique.quebec.ca/fr/document/utilisation-services-sante-et-services-sociaux/publication/utilisation-services-sante-sociaux-premiere-ligne-2025
2. **ISQ — Communiqué Panorama des régions, 2 novembre 2026.** L'organisme signale un taux d'affiliation **inférieur au reste du Québec à Montréal** et **supérieur au reste du Québec** au Bas-Saint-Laurent, au Saguenay–Lac-Saint-Jean, dans Lanaudière, au Nord-du-Québec et en Gaspésie–Îles-de-la-Madeleine. Le communiqué ne donne pas les taux numériques de toutes les RSS dans le corps du texte. Source : https://statistique.quebec.ca/fr/communique/portrait-multithematique-regions-vieillissement-population-main-oeuvre-transport-electrique
3. **Gouvernement du Québec — Structure du réseau.** Le réseau est organisé en **18 régions sociosanitaires**; ce découpage **n'est pas celui des 17 régions administratives**, ni des réseaux territoriaux de services (RTS). Source : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/systeme-quebecois-de-sante-et-de-services-sociaux/structure-systeme-sante-services-sociaux-quebec

## 2. Résultat régional utilisable à ce stade
Les **six différences qualitatives rapportées dans le communiqué** peuvent être publiées comme observations **relatives au reste du Québec**, sans inventer des taux non lus et sans classer les régions :

| RSS | Territoire | Indication officielle du communiqué | Taux exact validé dans la table régionale |
| --- | --- | --- | --- |
| 06 | Montréal | **Inférieure** au reste du Québec | **Non extrait** |
| 01 | Bas-Saint-Laurent | **Supérieure** au reste du Québec | **Non extrait** |
| 02 | Saguenay–Lac-Saint-Jean | **Supérieure** au reste du Québec | **Non extrait** |
| 10 | Nord-du-Québec | **Supérieure** au reste du Québec | **Non extrait** |
| 11 | Gaspésie–Îles-de-la-Madeleine | **Supérieure** au reste du Québec | **Non extrait** |
| 14 | Lanaudière | **Supérieure** au reste du Québec | **Non extrait** |

Le communiqué ne signale pas dans son texte une différence pour les **dix autres régions incluses** dans l'enquête. **Ce silence ne prouve ni une égalité, ni un écart non significatif** : il faut lire les tableaux, tester les comparaisons et consulter les notes méthodologiques.

Les RSS **17 (Nunavik)** et **18 (Terres-Cries-de-la-Baie-James)** sont **hors champ de cette enquête**. Cela ne signifie aucunement que leurs habitants sont sans service ou que le besoin y est inexistant; toute réforme nationale doit obtenir des preuves territoriales adaptées et respecter les compétences et les partenaires autochtones concernés.

## 3. Statut des classeurs ISQ : accessibles dans le catalogue, mais non analysés
La page ISQ **Utilisation des services de santé et services sociaux** affiche, à la date de vérification :
- recueil XLSX provincial 2025, daté du 2 novembre 2026;
- recueil XLSX provincial et régional 2025, daté du 2 novembre 2026;
- méthodologie et questionnaire d'enquête, datés du 2 novembre 2026.

Catalogue : https://statistique.quebec.ca/fr/document/utilisation-services-sante-et-services-sociaux  
Adresse de fichier régional indiquée par le lien de l'ISQ : https://statistique.quebec.ca/fr/fichier/utilisation-services-sante-services-sociaux-2025-tableaux-rss.xlsx

**Accès technique du 3 novembre 2026 :** le téléchargement de ce XLSX a échoué depuis l'environnement d'analyse utilisé. **Aucune feuille, ligne, colonne, valeur régionale ou intervalle d'incertitude de ce fichier n'a été inspecté ni présenté comme validé.**

Une source qui existe en ligne **n'équivaut pas** à un jeu de données importé, calculé et réconcilié. Ne pas transformer la mention d'un lien en contrôle qualité réussi.

## 4. Contrat d'extraction du XLSX régional — à appliquer quand disponible

### Grain
Une ligne exploitable pour analyse comprend : `source_file_version`, `sheet_name`, `cell_address`, `indicator_code`, `survey_year=2025`, `rss_code` (01–16 ou agrégat Québec), `estimate`, `unit`, `sample_size`, `coefficient_variation`, `confidence_interval`, `denominator`, `flags`, `notes`, `extraction_date`.

### Contrôles bloquants
1. **Intégrité du fichier** : référence, auteur, date de téléchargement, empreinte SHA-256 des octets, version et permis de citation.
2. **Bonne feuille** : identifier l'indicateur d'affiliation (médecin/GMF/IPS), et non médecin individuel seulement.
3. **Bonne population** : personnes de 18 ans et plus dans le champ de l'enquête; aucun recodage en population générale.
4. **Bonne géographie** : région sociosanitaire, pas région administrative ou RTS; 17 et 18 doivent rester hors champ.
5. **Unités** : pourcentages 0–100; ne pas interpréter un pourcentage comme une fraction 0–1 sans métadonnées.
6. **Incertitude** : relever les drapeaux de précision (*, **, confidentialité), intervalles et tests pertinents; supprimer la mise en rang si l'analyse ne permet pas une distinction fiable.
7. **Dénominateur et pondération** : ne pas additionner ou moyenner sans poids les proportions régionales pour reconstruire le 82 % provincial.
8. **Provenance de chaque ligne** : numéro de table, feuille, cellule, titre et notes, pour audit externe.
9. **Comparabilité** : lire les changements de concept (lieu d'affiliation vs consultation effective) et les différences de période avant confrontation à la RAMQ.
10. **Réconciliation** : rapprocher la valeur provinciale du même tableau avant toute utilisation des chiffres régionaux. Si les concepts diffèrent, cesser la comparaison plutôt que forcer la concordance.

## 5. Décisions de G0 interdites ou conditionnées
- **Interdit :** calculer des économies ou un effet causal privé/public à partir d'un pourcentage d'affiliation.
- **Interdit :** classer les RSS par efficacité médicale tant que les coûts, cas complexes, besoins non satisfaits, effectifs et délais effectifs ne sont pas documentés.
- **Interdit :** utiliser l'absence des RSS 17 et 18 dans l'enquête pour les exclure de l'obligation d'équité et de continuité.
- **Conditionné :** tout projet de pilote nécessite accord légal/clinique, consultation, éthique et capacité de retrait, en plus des portes G0–G4.
- **Conditionné :** interpréter le taux d'affiliation avec les informations sur le recours réel, la continuité, les besoins et la sécurité.

## 6. Registre de preuve
Fichier source contrôlable : `data/portrait-regional-g0-sante-2025.json`.

| Contrôle | État au 3 novembre 2026 |
| --- | --- |
| Géographie de 18 RSS | **Référencée et contrôlée** |
| Exclusions RSS 17/18 | **Vérifiées dans l'enquête** |
| Affiliation provinciale de 82 % | **Reprise du fait saillant ISQ** |
| Six différences régionales signalées | **Reprises du communiqué ISQ** |
| 16 pourcentages régionaux et incertitudes | **Inconnus dans le fichier Nova** |
| Extraction vérifiable du XLSX ISQ | **Non réalisée** |
| Coût et qualité comparatifs par RSS | **Non disponibles** |
| Classement des régions / choix d'un pilote | **Non réalisé / non autorisé** |

## 7. Étapes d'analyse suivantes
**G0.3-A :** obtenir les deux XLSX ISQ et la méthodologie, en consignant les empreintes.  
**G0.3-B :** produire un tableau de 16 RSS avec notes de fiabilité et intervalles, sans forcer de comparaisons non étayées.  
**G0.3-C :** rapprocher, **sans les fusionner artificiellement**, les données d'enquête ISQ et les séries administratives RAMQ/Santé Québec sur les mêmes territoires et périodes.  
**G0.3-D :** travailler la participation territoriale, notamment les perspectives des régions exclues et des partenaires autochtones concernés.  
**G0.3-E :** seulement après les définitions et autorisations, évaluer le coût par épisode, la main-d'œuvre et la continuité en vue du passage G1.

**Le Projet Nova reste en diagnostic G0 partiel : aucune modification du programme, du cadre financier candidat, aucune clinique privée lancée et aucune économie fictive.**
