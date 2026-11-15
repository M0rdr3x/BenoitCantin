# NOVA-SINJ-G0-SAN-015 — Rapport de vérification interne G0.9, réconciliation RH

**Date :** 4 novembre 2026  
**Projet :** Projet Nova  
**Statut :** contrôle technique interne, sans certification extérieure.  
**Objet :** vérifier les règles de mappage et de refus de statistiques RH incomparables.

## 1. Constat principal
La page gouvernementale référence le portrait RH 2024–2025, mais **l'accès aux octets XLSX échoue toujours** depuis l'environnement d'analyse. Aucun effectif régional ni ETP clinique réel n'est extrait; les séries RAMQ et les salariés R22 demeurent conceptuellement distincts.

Un nouveau mécanisme prépare seulement un **paquet de revue des feuilles** après acquisition officielle validée L2. Il refuse de publier automatiquement toute valeur numérique.

## 2. Contrôles effectivement exécutés
Le moteur JavaScript `assets/g09-rh-reconciliation-core.mjs` a été chargé et exercé dans un environnement V8 isolé, sur le registre réel non chiffré G0.9 et des objets de test **intégralement fictifs**.

**Résultat : 23 vérifications internes sur 23 réussies.**

Les assertions ont confirmé :
- 18 RSS et 13 critères présents, aucune donnée réelle RH extraite;
- refus de préparer un paquet à partir de la source `DOWNLOAD_BLOCKED`;
- possibilité de produire un paquet sans chiffres à partir d'un manifeste L2 **fictif** bien formé;
- aucune publication ni approbation automatique, y compris pour une cellule fictive revue;
- détection de deux références à la même cellule, ainsi que d'un grain conceptuel en doublon;
- exclusion d'une ligne de sous-total de la liste des détails;
- refus de valeurs supprimées publiées sous un chiffre;
- refus d'un zéro non attesté et distinction d'un zéro synthétique explicitement vérifié;
- refus des codes RSS invalides, des régions administratives prises pour des RSS et des unités inconnues;
- refus d'empreintes source incohérentes ou d'une revue humaine manquante;
- existence de dix tests Node déclarés et d'un workflow manuel relié au paquet G0.9.

**Ces 23 vérifications ne sont pas une exécution de la suite Node.** Les dix tests enregistrés dans `tests/g09-rh-reconciliation.test.mjs` et les autres tests G0.7–G0.8 doivent encore être confirmés dans GitHub Actions. Le contrôleur ne certifie pas une relecture humaine future simplement parce qu'un champ est rempli.

## 3. Contraintes toujours ouvertes
1. Aucun octet du portrait RH officiel 2024–2025 obtenu ni hachage SHA-256 réel.
2. Aucun `g09-review-package.json` issu du classeur gouvernemental réel.
3. Aucun mappage effectif des en-têtes, cellules, unités, professions, régions et totaux.
4. Aucun contrôle externe des données ni confirmation des droits de publication.
5. Aucun recoupement de la population des établissements avec les professionnels rémunérés RAMQ.
6. Aucun ETP clinique net, coût par épisode ou effet d'une réorganisation calculé.
7. Aucune confirmation de déploiement de la nouvelle page sur le domaine public.

## 4. Statut et suite
**Niveau documentaire actuel : L0 — source identifiée**. Les niveaux L1–L5 restent non franchis.
**G0 : NON FRANCHIE.** Aucun pilote, financement ou réduction d'effectif approuvé.
Le projet doit acquérir le fichier, vérifier les feuilles et effectuer une revue statistique indépendante avant toute production de chiffres réels.

**Ce rapport ne vaut pas autorisation de réforme ni validation par le gouvernement du Québec, Santé Québec, le MSSS ou la RAMQ.**
