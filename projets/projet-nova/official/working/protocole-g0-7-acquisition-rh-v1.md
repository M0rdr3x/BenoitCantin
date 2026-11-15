# NOVA-SINJ-G0-SAN-010 — G0.7 : protocole d'acquisition et de traçabilité du classeur RH public

**Date :** 4 novembre 2026  
**Projet :** Projet Nova — volet technique de la première ligne  
**Statut :** protocole de travail, **non adopté et non validé par le MSSS/Santé Québec/RAMQ**.  
**Porte :** G0 **NON FRANCHIE**. Aucune autorisation de pilote, aucun financement, aucun emploi modifié.

## 1. Résultat réel de cette étape
La page officielle du Québec, mise à jour le **27 avril 2026**, répertorie un fichier XLSX intitulé **« Portrait du personnel des établissements publics et privés conventionnés du réseau de la santé et des services sociaux (2024-2025) »**, d'environ **136 Ko**. Selon sa description, il présente une répartition par sous-catégories, statuts d'emploi et régions, ainsi que des éléments de rémunération.

Catalogue : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-humaines

Lien officiel du fichier :
https://cdn-contenu.quebec.ca/cdn-contenu/sante/documents/Systeme_et_services_de_sante/organisation-services/donnees-systeme-sante-quebecois-services/ressources-humaines/denombrement-et-remuneration-effectif-rsss-2024-2025.xlsx

**Tentatives au 4 novembre 2026 :**
- le catalogue et le lien XLSX sont accessibles comme références;
- l'outil de lecture Web ne renvoie pas d'octets pour ce type de fichier;
- le téléchargement par le service de transfert du conteneur a échoué;
- la connexion directe a échoué lors de la résolution DNS depuis l'environnement de travail.

Par conséquent, **aucun octet du classeur n'a été obtenu**, aucune feuille n'a été inspectée, aucun chiffre régional n'a été extrait ni rapproché. Les 18 lignes RH du registre `data/registre-rh-regional-g0-6-sante.json` restent **non renseignées**. Cette situation ne prouve pas que les données ne sont pas disponibles pour les organismes eux-mêmes.

## 2. Échelle d'acquisition et portes documentaires

| Niveau | Condition | État vérifié |
| --- | --- | --- |
| **L0 — Source identifiée** | Institution, titre, période, lien HTTPS et description publique | **Oui** |
| **L1 — Octets obtenus** | Téléchargement valide, taille limitée, HTTP 200, SHA-256 et rapport de réception | **Non** |
| **L2 — Structure vérifiée** | Annuaire ZIP/XLSX, fichier workbook et feuilles présents, non chiffré, sans doublon de chemin; revue des feuilles et unités | **Non** |
| **L3 — Grain de données vérifié** | RSS versus établissement, année, profession, salariés, statuts, heures, dénominateurs, totaux et exclusions | **Non** |
| **L4 — RH réconciliées** | Couverture R22, privés conventionnés, St@tRAMQ, chevauchements, ETP cliniques de première ligne | **Non** |
| **L5 — Examen indépendant** | Revue méthodologique, financière, juridique et des droits/conditions de travail | **Non** |

**Règle bloquante :** le fait qu'un fichier ait passé L1–L2 ne suffit jamais pour lui attribuer des chiffres de personnel certifiés ni pour déclarer G0 franchie.

## 3. Nouvelle procédure GitHub Actions, volontaire uniquement

Workflow ajouté : `.github/workflows/nova-g07-acquisition-rh.yml`.

Il ne s'exécute **que par `workflow_dispatch`**, depuis le menu GitHub **Actions**, sur choix explicite d'un opérateur ayant les permissions du dépôt. Il n'y a **ni tâche quotidienne ni envoi programmé**, ni extraction de données personnelles.

Lorsqu'il est déclenché :
1. récupère les sources du dépôt en **lecture seule**, avec Node 22;
2. exécute les tests de sécurité et de validité du mécanisme;
3. tente un téléchargement HTTPS de l'URL officielle, avec une liste d'hôtes limitée au CDN gouvernemental, sans domaine tiers;
4. impose une limite de taille de **5 Mo**, un délai d'attente et un nombre limité de redirections;
5. inspecte les en-têtes et l'annuaire central du conteneur ZIP/XLSX, notamment `[Content_Types].xml`, `xl/workbook.xml` et les chemins `xl/worksheets/sheet*.xml`; refuse chemins dangereux, doublons d'entrées et entrées chiffrées;
6. conserve la **taille**, l'empreinte **SHA‑256**, l'URL source, la date UTC, le type de contenu, l'ETag et le Last-Modified lorsqu'ils existent;
7. produit `source-audit.json` et, **seulement en cas de succès**, le classeur `rh-rsss-2024-2025-source.xlsx` dans un artefact GitHub Actions conservé **14 jours**.

Le workflow dispose uniquement de `permissions: contents: read`, ne fait **aucun commit**, n'actualise pas les 18 régions et n'assure **aucun traitement de microdonnées**. Un échec laisse un rapport `DOWNLOAD_BLOCKED` et un indicateur d'exécution en échec, non une réussite dissimulée.

**Important : ce nouveau workflow est présent dans le dépôt mais son exécution n'est pas confirmée au moment de ce document.** L'exécution réelle, ses journaux et tout artefact doivent être examinés avant d'affirmer que le XLSX a été téléchargé.

## 4. Contrat de contrôle avant toute interprétation
Après acquisition autorisée du fichier, la première inspection doit documenter :
- **provenance** : lien officiel, identifiant de source, SHA‑256, date de réception, taille, version et droit de reproduction;
- **feuilles et cellules** : noms exacts, dimensions, tableaux, en-têtes, notes méthodologiques, types de cellules et unités; conserver les références de feuille/cellule;
- **grain territorial** : région **sociosanitaire**, région administrative, établissement ou regroupement; ne jamais supposer une correspondance 1:1;
- **période** : exercice 2024–2025, dates et variantes de tableaux; ne pas convertir automatiquement ces chiffres en ressources de novembre 2026;
- **concept RH** : personnel en emploi, personnes présentes, heures rémunérées, heures réellement travaillées, temps complet/partiel, ETP, catégories et professions;
- **comptes de référence** : totaux provinciaux et régionaux, lignes « autres », doubles comptes et catégories hors établissement;
- **limites R22/EPC** : les professionnels rémunérés par la RAMQ ne figurent pas dans tous les indicateurs de personnel salarié, et certaines données d'EPC sont manquantes;
- **confidentialité** : agréger les faibles effectifs, ne pas publier de données de paie individuelles et obtenir des permissions spécifiques pour toute donnée protégée;
- **validation** : inspecteur, source, contrôles automatisés reproductibles, incertitudes et évaluation indépendante.

Un tableau ne devient **une donnée exploitable pour G0.5** qu'après une revue qui identifie l'unité et son périmètre. Les colonnes `employment_count`, `present_count`, `etp_clinical_first_line` et `unit_cost_complete` du registre RH restent `null` dans l'intervalle.

## 5. Contrôle du traitement politique et financier
**Interdictions de calcul :**
- ne pas additionner les personnes salariées et les professionnels rémunérés à l'acte comme s'il s'agissait d'ETP;
- ne pas assimiler les personnes administrativement présentes aux heures cliniques disponibles;
- ne pas calculer une productivité de soins à partir d'un effectif sans épisode clinique correspondant;
- ne pas déduire une économie d'un transfert public–privé sans coûts de transition, équipe d'origine, qualité, personnel et financement complet;
- ne pas utiliser l'absence des RSS 17 et 18 dans l'enquête ISQ 2025 pour leur attribuer un effectif égal à zéro.

**Aucun registre rempli ne déclenche automatiquement une politique.** Les références officielles candidates du Projet Nova ne sont pas modifiées par ce protocole.

## 6. Fichiers G0.7

- `data/registre-acquisition-rh-g0-7.json` — état réel des tentatives (initialement `DOWNLOAD_BLOCKED`), dates, preuves et absences explicites;
- `assets/g07-rh-acquisition-core.mjs` — validateur du rapport et de l'inventaire ZIP;
- `scripts/g07-acquerir-rh-officiel.mjs` — procédure de téléchargement HTTPS à limite de taille;
- `.github/workflows/nova-g07-acquisition-rh.yml` — déclenchement volontaire et artefacts;
- `tests/g07-acquisition-rh.test.mjs` — cas positifs, erreurs, fichier faux/tronqué, interdictions de conclusions;
- `acquisition-rh-g0-7-sante.html` — état public documentaire, sans statistiques de personnel inventées.

## 7. Prochain passage de contrôle, sans confondre étude et décision
Une fois un fichier effectivement obtenu et vérifié, la phase G0.8 pourra décrire **les tableaux et leur population réelle**, réaliser les contrôles de qualité, calculer uniquement les agrégats que les données autorisent et produire un registre par RSS et période avec incertitudes. La conversion en ETP de première ligne demandera des heures cliniques et une méthode indépendante, potentiellement indisponibles dans le fichier source.

**Résultat à date :** source connue, téléchargement non confirmé, import de ressources humaines nul; G0 n'est pas franchie. Le dossier vise une réforme mieux informée, pas un effet d'annonce.
