# NOVA-SINJ-G0-SAN-018 — G0.11 : rapprochement de la copie XLSX originale avec le portrait RH du MSSS

**Date :** 5 novembre 2026  
**Projet :** Projet Nova — Santé, accès aux soins et protection des effectifs  
**Statut :** vérification technique de source et de cellules, non certification statistique institutionnelle.  
**Porte G0 :** **NON FRANCHIE**. Aucun pilote, budget, transfert ou suppression de poste n'est autorisé.

## 1. Évolution par rapport à G0.10

La phase G0.10 disposait d'une **transcription secondaire Markdown** de la « Feuille A - 2 » du portrait public 2024–2025 du MSSS, sans octets XLSX conservés. Ses nombres de personnes concordaient exactement avec le total publié; ses valeurs entières d'équivalents temps complet (ETC) présentaient toutefois un **écart apparent de 2 ETC** entre le total affiché et la somme des lignes arrondies.

**G0.11 apporte une vérification différente et plus forte :** la copie **binaire originale** a été récupérée le 5 novembre 2026 dans un environnement distant de vérification externe. Le conteneur ZIP, les feuilles OOXML et les cellules originales de la « Feuille A - 2 » ont été lus directement. Une seconde exécution réelle d'un programme Node.js a recoupé ces cellules avec les valeurs G0.10 et l'empreinte attendue.

### Pièce source

- Producteur : ministère de la Santé et des Services sociaux (MSSS), Québec.
- Fichier : https://cdn-contenu.quebec.ca/cdn-contenu/sante/documents/Systeme_et_services_de_sante/organisation-services/donnees-systeme-sante-quebecois-services/ressources-humaines/denombrement-et-remuneration-effectif-rsss-2024-2025.xlsx
- Période du portrait : 2024–2025; dénombrement de personnes au 31 mars 2025.
- Octets reçus : **139 566**.
- Empreinte SHA‑256 calculée sur les octets reçus : `8d65573b2f0bf0a935a58c75ba1b4b76050a08b902760f7a03b3cae0cdb86219`.
- Archive ZIP : **61 parties**, test CRC réussi.
- Classeur : **7 feuilles** identifiées par `xl/workbook.xml` et `xl/_rels/workbook.xml.rels`.
- Source précise des nombres : **« Feuille A - 2 »**, `xl/worksheets/sheet4.xml`.

**Frontière de preuve :** l'empreinte identifie la copie **reçue**. Il ne s'agit **pas d'une signature cryptographique émise par le gouvernement**. La copie binaire a été accessible et inspectée dans l'environnement externe, mais **elle n'a pas été déposée dans le dépôt GitHub**, ni archivée comme artefact vérifié d'un workflow GitHub Actions.

## 2. Cellules exactes utilisées

| Domaine | Références de cellules originales | Observation |
| --- | --- | --- |
| Libellés des 19 lignes | `A5:A23` | Ligne `00` Santé Québec, puis RSS `01` à `18` |
| Personnes au 31 mars 2025 | `B5:B23` | 19 valeurs entières, une personne dédoublonnée selon la méthode MSSS |
| Personnes au 31 mars 2024 | `C6:C23` | 18 valeurs régionales; pas de ligne Santé Québec 2024 |
| Total personnes 2025 | `B24` | **344 056** |
| Total personnes 2024 | `C24` | **336 730** |
| ETC rémunérés 2024–2025 | `B51:B69` | 19 valeurs **avec décimales dans le XLSX**, affichées arrondies en table |
| Total ETC rémunérés | `B70` | **283 739,959 environ**, affiché **283 740** |

Les 18 RSS ont **343 252** personnes au 31 mars 2025. La ligne organisationnelle `00 — Santé Québec` comporte **804** personnes. Le total est exact :

**343 252 + 804 = 344 056 personnes.**

Les RSS 17 (Nunavik) et 18 (Terres-Cries-de-la-Baie-James) sont incluses dans ce dénombrement RH. Cela ne change rien au fait que l'enquête ISQ d'affiliation 2025 avait un **champ géographique différent** et les excluait.

## 3. Résolution démontrée de l'écart ETC

L'ancienne apparente incohérence ne constitue **pas** deux ETC « manquants ».

- La cellule `B70` contient `283739.95899999997` dans sa représentation numérique XML, soit **283 739,959 ETC** à la précision utile.
- La somme des 19 valeurs **non arrondies** `B51:B69` est `283739.95899999999944` dans cette représentation.
- L'écart entre somme brute et total brut est d'environ **0,00000000003 ETC**, une variation de représentation en virgule flottante, nettement inférieure à la tolérance fixée de **0,00000001 ETC**.
- L'arrondi du **total brut** donne **283 740 ETC**.
- La somme des **19 entiers affichés après arrondi individuel** donne **283 738 ETC**.

**Cause vérifiée :** l'arrondi indépendant de chaque ligne explique entièrement les deux ETC d'écart dans les valeurs affichées. Le contrôleur ne doit **plus** qualifier cette différence de « non résolue ». Il doit néanmoins préserver la distinction entre **somme des entiers affichés** et **somme des valeurs originales**.

## 4. Contrôles reproductibles inscrits dans le dépôt

- `data/preuve-binaire-rh-msss-g0-11-2024-2025.json` : date, URL, SHA‑256, taille, 19 lignes, coordonnées précises, valeurs entières et décimales, totaux, tolérance et limites.
- `assets/g11-rh-evidence-core.mjs` : relecture du contrat, détection des doublons/mauvaises coordonnées et des fausses validations, comparaison au jeu G0.10; lecteur de cellules et chaînes partagées XML.
- `assets/g08-rh-workbook-inspector.mjs` : nouvelle lecture ciblée des seules pièces XML autorisées, dans les bornes ZIP/CRC et de taille existantes.
- `scripts/g11-verifier-original-rh-officiel.mjs` : sur une copie acquise par G0.7, recalcule SHA‑256, vérifie les métadonnées G0.8 et rapproche les cellules originales `A5:C24`, `B51:B70` avec les 19 lignes et totaux.
- `tests/g11-rh-original-cells.test.mjs` : **15 tests**, dont un nouveau test de régression sur les cellules XLSX vides autofermées.
- `.github/workflows/nova-g07-acquisition-rh.yml` : G0.11 ajouté **après** les contrôles G0.7–G0.9, toujours **manuel**, en **lecture seule**, sans commit automatique; le rapport `g11-original-cell-evidence-audit.json` est conservé dans l'artefact temporaire lorsqu'exécuté.

## 5. Exécution réelle observée

Le 5 novembre 2026, dans un **environnement Node.js v26.12.1 distant et temporaire**, les composants G0.7 à G0.11 ont été récupérés depuis GitHub et **57 tests Node ont été exécutés avec succès (57/57)**. Le script `scripts/g11-verifier-original-rh-officiel.mjs` a été exécuté directement sur le XLSX officiel reçu : **code de sortie 0**, statut `ORIGINAL_CELLS_MATCH_REVIEW_PENDING`, 19 lignes rapprochées, totaux et arrondis vérifiés.

Le premier essai en conditions réelles avait détecté un défaut de lecture lié aux cellules vides autofermées. Il a été corrigé, testé, puis la suite complète et la vérification du vrai XLSX ont été relancées avec succès.

**Attention :** cette exécution est extérieure au pipeline GitHub Actions et n'est **pas** une validation indépendante par le MSSS, Santé Québec ou la RAMQ. Les journaux de GitHub Actions ne sont pas attestés.

## 6. Précautions sociales, cliniques et financières

La source mesure des **personnes couvertes par le dénombrement salarié et cadres** et des **ETC rémunérés**. Le portrait exclut notamment les professionnels payés par la RAMQ, la main-d'œuvre indépendante et d'autres catégories prévues dans les définitions du MSSS.

**Les ETC rémunérés ne sont pas des ETP cliniques effectivement disponibles en première ligne.** Les valeurs ne permettent pas à elles seules de calculer des consultations obtenues, un délai de rendez-vous, un coût par épisode, des économies ou la capacité nette de nouveaux services.

Aucun transfert vers un opérateur privé, public ou coopératif ne peut être justifié par ces seuls chiffres. Les travailleurs et les territoires doivent être protégés, et la RAMQ ainsi que les droits d'accès restent des conditions institutionnelles distinctes.

## 7. Ce qu'il reste à vérifier avant une décision

1. Conserver durablement une copie binaire conforme aux droits de diffusion et sa SHA‑256 avec journal d'acquisition.
2. Confirmer la version du classeur et, si possible, confronter l'empreinte à un registre de publication du MSSS.
3. Obtenir un examen indépendant des définitions, du périmètre, des chiffres transcrits et des sources d'heures cliniques.
4. Séparer les ETC rémunérés, les personnes en emploi, les heures de prestation directe et les professionnels rémunérés par la RAMQ.
5. Préparer des données réellement comparables par région et par besoin **avant** de considérer un pilotage de réforme.

**État G0.11 : vérification technique originale positive; certification clinique, financière et institutionnelle toujours absente; G0 NON FRANCHIE.**
