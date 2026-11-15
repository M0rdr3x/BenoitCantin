# NOVA-SINJ-G0-SAN-009 — Rapport de vérification technique du dossier RH G0.6

**Date :** 3 novembre 2026  
**Projet :** Projet Nova  
**Statut :** vérification interne de la méthode, non certifiée extérieurement, sans effet juridique ou opérationnel.  
**Objet :** contrôler les représentations des 18 régions, les exclusions et les comparaisons d'ETP.  

## 1. Matériel inspecté
Les fichiers du dépôt GitHub `M0rdr3x/BenoitCantin` ont été récupérés dans leur version principale lors de cette intervention :
- `data/registre-rh-regional-g0-6-sante.json`
- `data/portrait-regional-g0-sante-2025.json`
- `assets/g06-capacite-rh-core.mjs`
- `capacite-rh-g0-6-sante.html`

Le module de contrôle a été exécuté dans un environnement JavaScript V8 isolé. Des scénarios artificiels ont servi à évaluer l'arithmétique et les refus. **21 vérifications fonctionnelles sur 21 ont réussi**.

Les tests Node sont également enregistrés sous `tests/g06-capacite-rh.test.mjs` et le workflow `.github/workflows/nova-sinjira-finances-tests.yml` a été mis à jour. **Aucune exécution réussie de GitHub Actions n'est confirmée par ce rapport** et les 21 vérifications ne constituent pas une exécution de la suite Node entière.

## 2. Assertions internes obtenues (21/21)
1. 18 RSS au registre.
2. 18 régions sans données RH chiffrées extraites.
3. Aucune série de coût RH validée.
4. Concordance des valeurs contextuelles d'affiliation ISQ avec G0.4.
5. Aucun ETP régional, effectif ou coût unitaire fictif.
6. Déplacement de 10 ETP entre opérateurs : variation totale 0 dans l'exemple.
7. Départ public -10 et arrivée chez autres opérateurs +10 se compensent.
8. Aucune économie ni nombre de consultations additionnelles imputés au transfert.
9. Exemple fictif avec cinq ETP réellement ajoutés : différence arithmétique +5 uniquement.
10. Rejet d'un ETP `null` dans le calcul de comparaison.
11. Rejet d'ETP négatifs.
12. Rejet d'une unité « personnes » dans un calcul d'ETP.
13. Rejet d'une comparaison sur périodes déclarées incompatibles.
14. Rejet d'un périmètre exposé aux doubles comptes non maîtrisés.
15. Rejet d'une prétendue preuve RH incomplète sans audit ni référence de fichier.
16. Onze mesures RH définies.
17. Quatre sources documentaires distinctes.
18. Page Web : dix-huit lignes RSS affichées.
19. Page Web : onze mesures et deux cartes de garanties représentées.
20. Page Web : 54 cellules RH « non obtenu » (trois colonnes × dix-huit régions).
21. Page HTML dotée de ses fermetures structurantes.

## 3. Limites importantes
- Le XLSX officiel 2024–2025 du personnel public et privé conventionné a été **repéré mais non téléchargé** (échec de téléchargement), donc ses données, tableaux, feuilles et totaux n'ont pas été inspectés.
- Les données St@tRAMQ ne sont pas extraites pour cette phase.
- La structure R22 n'est pas exhaustive de l'ensemble des soignants et exclut les professionnels rémunérés directement par la RAMQ ainsi que certains établissements privés conventionnés.
- La catégorie administrative de personnel « présent » ne décrit pas nécessairement les heures de soins réellement disponibles.
- Les conversions d'ETP doivent être fondées sur une définition de temps de travail, de profession, de lieu de soin, de période et d'exclusions, non sur un ratio arbitraire.
- Les nombres 80, 20, 70, 30 et 5 utilisés dans les tests sont **des nombres fictifs** pour valider l'identité comptable. Ils ne décrivent aucune région ni aucun opérateur du Québec.
- Ni la page Web sur le domaine public ni une exécution de CI GitHub Actions n'ont pu être confirmées depuis l'environnement de vérification.
- Aucune évaluation médicale, financière, éthique ou juridique indépendante n'a encore été réalisée.

## 4. Statut décisionnel et périmètre
**G0 : NON FRANCHIE**.  
**Aucune donnée RH régionale certifiée**.  
**Aucun transfert de personnel, aucune réduction d'emplois et aucune dépense autorisés**.  
**Aucune économie calculée ou annoncée**.  
**Documents officiels candidats du Projet Nova : non modifiés**.

La décision éventuelle de procéder à un pilote ou à des changements de prestation reste soumise à la revue indépendante, aux exigences institutionnelles et aux consentements/permissions légales pertinents.

**Ce rapport atteste uniquement les contrôles internes exécutés sur les fichiers de cette intervention; il ne représente pas une validation par le MSSS, Santé Québec ou la RAMQ.**
