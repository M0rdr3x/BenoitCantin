# NOVA-SINJ-G0-SAN-013 — Rapport de vérification interne G0.8 (classeur RH)

**Date :** 4 novembre 2026  
**Projet :** Projet Nova  
**Statut :** preuve technique **interne**, non audit externe.  
**Portée :** méthode de contrôle ZIP et OOXML, pas évaluation du contenu statistique du classeur gouvernemental.

## 1. Matière inspectée
Le fichier `assets/g08-rh-workbook-inspector.mjs` a été récupéré depuis le dépôt GitHub avec son module G0.7 dépendant. La partie JavaScript du code a été chargée dans un environnement V8 et exercée avec des **conteneurs ZIP synthétiques, en mode « stockage non comprimé »**, générés en mémoire sans données RH.

**Résultat : 9 vérifications fonctionnelles sur 9 réussies** à cette date.

Un second jeu de **11 tests Node 22** a été enregistré sous `tests/g08-rh-workbook-inspector.test.mjs`. Il teste notamment des entrées XML **compressées DEFLATE** grâce au module Node `zlib`. **L'exécution complète de ces 11 tests dans GitHub Actions n'est pas confirmée**. Ne pas confondre une définition de test et son exécution réussie.

## 2. Vérifications réalisées dans V8 (9/9)
1. Un fichier ZIP fictif cohérent permet d'extraire uniquement le nom de feuille et sa dimension, en statut `L2_STRUCTURE_SEULEMENT`.
2. Une valeur fictive `99999999` incluse dans le XML d'une cellule ne se retrouve **pas** dans le rapport de métadonnées.
3. Une archive sans les relations du classeur est refusée.
4. Une relation externe est refusée.
5. Une déclaration XML d'entité externe est refusée.
6. Un composant macro/VBA est refusé.
7. Une dimension de feuille mal formée est refusée.
8. Un ZIP tronqué est refusé.
9. Aucune valeur d'ETP ou d'effectif régional n'est déclarée vérifiée.

Les fichiers tests sont synthétiques : **aucun classeur officiel de 2024–2025 n'a été inspecté**. Le contrôle V8 n'a pas exécuté les chemins de décompression DEFLATE de Node; ces chemins font l'objet du jeu de tests Node à vérifier dans GitHub Actions.

## 3. Gestion des risques et limites
- L'inspecteur contrôle la structure et certaines protections d'intégrité, **pas la conformité complète au standard OOXML**, l'authenticité du producteur, la sécurité antivirus, ni les données financières.
- Le SHA-256 enregistré à l'acquisition prouve une empreinte de copie; sans signature ou registre officiel de hachage, il n'est **pas une preuve indépendante de provenance gouvernementale**.
- L'analyse des lignes et cellules, notes, types de personnel, unités, totaux et géographies reste une étape **distincte** nécessitant un vrai fichier et une validation de comparabilité.
- Le téléchargement du fichier officiel n'a pas abouti depuis l'environnement d'analyse; aucun `source-audit.json` d'exécution réussie n'est attesté.
- Les workflows ont été **modifiés et enregistrés** dans GitHub, mais le résultat d'une exécution CI ou d'un déclenchement manuel reste à confirmer.
- Aucun ETP clinique, taux de présence, coût de service ou mouvement net de personnel n'est établi par la structure d'un fichier.

## 4. Décision
**Niveau documentaire confirmé : L0 (source officielle identifiée).**  
**L1–L5 : non franchis dans le dossier.**  
**Résultat interne du mécanisme : 9/9 sur les fixtures ZIP stockées.**  
**Exécution de la suite Node (11 tests compressés notamment) : non confirmée.**  
**Effectifs et ETP régionaux certifiés : aucun dans le dossier Nova.**  
**Porte G0 : NON FRANCHIE.**  
**Pilote, financement et réduction d'emploi : non autorisés.**

Le présent rapport est un **journal de vérification interne**; il n'est pas une approbation par le gouvernement du Québec, le MSSS, Santé Québec ou la RAMQ.
