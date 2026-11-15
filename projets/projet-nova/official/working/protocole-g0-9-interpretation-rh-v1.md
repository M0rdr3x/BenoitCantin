# NOVA-SINJ-G0-SAN-014 — G0.9 : mappage statistique et réconciliation des effectifs

**Projet :** Projet Nova — santé et capacité des services  
**Date :** 4 novembre 2026  
**Statut :** protocole de recherche **non adopté**. Aucun coût ni ETP régional certifié; aucune décision de financement ou de prestation autorisée.  
**Porte :** G0 **NON FRANCHIE**.

## 1. Le problème à résoudre

Une archive Excel valide sur le plan technique ne prouve pas que ses données puissent être additionnées. Un même classeur peut contenir **lignes détaillées, sous-totaux, totaux provinciaux, professions qui se chevauchent, géographies administratives et valeurs supprimées**. Une extraction sans vérification de ces facteurs risque de surévaluer le personnel disponible.

La phase G0.9 sépare quatre opérations :

1. **Provenance :** fichiers d'octets du portail officiel et empreintes SHA‑256 de leur copie reçue.
2. **Structure :** feuilles et relations OOXML vérifiées en G0.8 (niveau documentaire L2).
3. **Mappage sémantique :** interprétation humaine des en-têtes, unités, catégories, dates, codes géographiques, totaux et cellules supprimées.
4. **Rapprochement :** construction d'agrégats comparables **uniquement après** validation des cellules, des grains et des exclusions. Cette opération n'est pas effectuée en l'absence de fichier réel.

**État concret au 4 novembre 2026 :** le portrait RH 2024–2025 du Québec est référencé sur sa page officielle mais son téléchargement direct a échoué. Aucun chiffre régional du classeur n'a été importé. Le registre G0.9 décrit **18 RSS, 13 contrôles de qualité, zéro effectif et zéro ETP validés**. Ce n'est pas un dénombrement réel de zéro travailleur.

Source : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-humaines

## 2. Chaîne opérationnelle après obtention du vrai classeur

Le workflow manuel `.github/workflows/nova-g07-acquisition-rh.yml` exécute, dans cet ordre :

1. tests de méthodes G0.7, G0.8 et G0.9;
2. téléchargement officiel G0.7 avec HTTP, domaine autorisé, taille contrôlée, SHA‑256, inventaire et rapport `source-audit.json`;
3. vérification G0.8 : CRC, composants OOXML, relations, feuilles et dimensions — sans interpréter les chiffres;
4. **nouvelle action G0.9 :** `scripts/g09-generer-paquet-revue-rh.mjs`, qui recontrôle le SHA‑256 du XLSX sur disque et les noms/dimensions des feuilles, puis génère `g09-review-package.json` pour la revue humaine;
5. conservation des rapports et de la copie source dans un artefact GitHub Actions de **14 jours**, sans commit automatique.

Le paquet G0.9 contient seulement :
- identité et empreinte du fichier;
- liste des feuilles et leurs dimensions déclarées;
- champs de mappage à remplir après étude du classeur;
- aucun chiffre de personnel, aucune cellule de salaire ni donnée personnelle;
- les mentions explicites `g0_passed:false`, `pilot_authorized:false` et `values_interpreted:0`.

Le workflow est **à déclenchement manuel** et ne s'est pas exécuté de façon confirmée lors de cette phase. Il ne peut pas se déclarer réussi seulement parce que le code a été commité.

## 3. Les 13 contrôles de réconciliation

| Code | Contrôle | Interdiction ou critère |
| --- | --- | --- |
| PROV | Fichier, source et SHA‑256 | Aucune valeur sans copie de la source réellement acquise |
| SHEET | Feuille, plage et cellule | Chaque statistique doit se rattacher à un emplacement du fichier |
| GEO | Région sociosanitaire versus région administrative | Conversion et table de concordance interdites sans référence appropriée |
| PERIOD | Périodes de référence | 2024–2025 ne décrit pas la disponibilité des ETP en novembre 2026 |
| UNIT | Unités | Personnes ≠ heures ≠ ETP ≠ dollars |
| ROLE | Détail, sous-total et total provincial | Ne jamais additionner un sous-total avec ses détails |
| DUP | Double comptage | Les mêmes cellules et grains conceptuels sont bloquants |
| SUPP | Suppression statistique | Valeur confidentielle/manquante = `null`, jamais zéro |
| ZERO | Zéro vérifié | Accepter 0 seulement s'il est réellement présent et interprété |
| RAMQ | Couverture des professionnels RAMQ | Ne pas additionner aux salariés R22 sans méthode de concordance |
| CASEMIX | Affectation réelle en première ligne | Effectif d'établissement ne prouve ni consultation ni disponibilité clinique |
| AUDIT | Revue indépendante | Audit des agrégats, notes, exclusions et incertitudes avant toute publication |
| DECISION | Gouvernement et droits | Aucun script ne peut approuver un pilote, un budget ou une diminution du personnel |

Le registre `data/registre-rapprochement-rh-g0-9.json` contient les treize contrôles, leur statut et les 18 régions. Les valeurs numériques RH restent toutes `null`.

## 4. Distinguer détail et total

Exemple **strictement fictif**, utilisé pour expliquer le risque (aucune observation québécoise) :

- Ligne « infirmières » : **12 personnes**
- Ligne « préposés » : **8 personnes**
- Ligne « total catégorie de personnel » : **20 personnes**

Le total est déjà la somme des deux groupes. **12 + 8 + 20 = 40 est un double comptage.** L'agrégat correct dans cet exemple artificiel serait **20**, mais seulement si les catégories sont mutuellement exclusives et les définitions cohérentes.

Dans le registre, les rôles possibles sont `DETAIL`, `SUBTOTAL`, `PROVINCIAL_TOTAL`, `HEADING`, `SUPPRESSED` et `NOTE`. Seules les lignes `DETAIL` entièrement cartographiées peuvent être admises comme **candidates de revue**; le contrôleur ne produit **aucune somme officielle automatique**.

## 5. Format minimal de chaque cellule statistique proposée

Une éventuelle ligne numérique doit avoir les champs :

`sheet_name`, `cell_ref`, `source_sha256`, `row_role`, `rss_id`, `source_geography`, `unit`, `measure_id`, `profession_group`, `source_period`, `population_scope`, `value`, `zero_explicitly_observed`, `human_mapping_checked`, `primary_document_checked`, `reviewer`, `mixed_population_excluded`, `is_aggregate_of_other_selected_rows`.

Le moteur `assets/g09-rh-reconciliation-core.mjs` refuse notamment :
- une cellule référencée deux fois;
- un grain conceptuel répété (même RSS, mesure, unité, profession, période et population);
- un code RSS erroné ou une région administrative prise pour une RSS;
- une unité inconnue ou une valeur négative/non finie;
- un zéro non explicitement observé;
- une donnée supprimée présentée comme chiffre;
- une empreinte qui ne correspond pas à celle du fichier acquis;
- un détail faisant double emploi avec un sous-total;
- une valeur sans preuve d'examen du fichier et de la catégorie concernée.

**Limite capitale :** ces contrôles vérifient les champs renseignés et la cohérence de la méthode; ils ne prouvent pas que les commentaires humains, la répartition des professions ou les totaux sont exacts. Une personne compétente doit vérifier le contenu réel et documenter les vérifications; une certification indépendante demeure distincte.

## 6. Aucun calcul d'ETP ni classement des régions

Le tableau 2024–2025 porte sur le personnel d'établissements publics et privés conventionnés; il ne représente pas d'office les heures cliniques de première ligne et n'inclut pas tous les professionnels rémunérés par la RAMQ selon les mêmes définitions.

Même avec des effectifs validés, le Projet Nova ne pourrait pas automatiquement :
- calculer des ETP cliniques, des consultations additionnelles ou un délai réel de consultation;
- attribuer une hausse de personnel à un changement de mode d'exploitation;
- comparer les coûts complets d'épisodes assurés;
- recommander un transfert public–privé, une réduction de salaires ou un licenciement;
- appliquer un classement d'efficience aux RSS 17 et 18 ou à toute autre région.

G0.9 ne certifie pas les statistiques : il prépare une procédure reproductible permettant **d'étudier les données sans inventer leurs valeurs**.

## 7. Travaux vérifiables qui restent à accomplir

1. Déclencher manuellement le workflow G0.7/G0.8/G0.9 dans GitHub et en vérifier les journaux.
2. Si le fichier est acquis, récupérer l'artefact signé par GitHub Actions et vérifier son SHA‑256 local.
3. Examiner la fiche G0.9, les feuilles réelles, les en-têtes et toutes les notes de bas de page.
4. Documenter les cellules candidates et leurs rôles, les unités et les géographies.
5. Rejeter les doublons, sous-totaux superposés, valeurs supprimées et regroupements ambigus.
6. Obtenir une validation humaine puis indépendante, faire vérifier la confidentialité et le droit de diffusion.
7. Seulement ensuite, décider si la source autorise un **dénombrement** par RSS — sans l'assimiler automatiquement à un ETP clinique.

**État final :** méthode d'extraction contrôlée disponible, source XLSX non obtenue, zéro chiffre régional RH importé, G0 **NON FRANCHIE**. Aucun document officiel candidat du programme Nova n'est modifié par cette étude.
