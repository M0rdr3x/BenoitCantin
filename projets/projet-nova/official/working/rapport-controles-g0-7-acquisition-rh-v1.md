# NOVA-SINJ-G0-SAN-011 — Contrôle interne du dispositif d'acquisition RH G0.7

**Date :** 4 novembre 2026  
**Projet :** Projet Nova  
**Type :** vérification technique interne des fichiers du dépôt.  
**Certification externe, CI exécutée et téléchargement du XLSX :** **non confirmés**.

## 1. Périmètre de la vérification
Les contrôles ont utilisé les versions lues dans GitHub des fichiers :
- `assets/g07-rh-acquisition-core.mjs`,
- `data/registre-acquisition-rh-g0-7.json`,
- `data/registre-rh-regional-g0-6-sante.json`.

Les fonctions JavaScript ont été exécutées dans un environnement V8 isolé avec archives ZIP **entièrement synthétiques** ne contenant aucun tableau de paie ni aucun fichier officiel. Après correction d'un mécanisme de décodage compatible avec cet environnement, **10 vérifications sur 10 ont réussi**.

## 2. Vérifications fonctionnelles réussies (10/10)
1. Le manifeste de provenance G0.7 est structurellement cohérent.
2. Le résumé documentaire conserve **zéro** région avec valeur RH validée.
3. L'absence du fichier `xl/workbook.xml` est bloquante.
4. La duplication d'une entrée de l'archive est refusée.
5. Une prétendue autorisation de pilote invalide un manifeste.
6. Une empreinte SHA‑256 affichée sans téléchargement réel invalide le manifeste.
7. Un conteneur ZIP **fictif** avec inventaire minimal cohérent est accepté au seul niveau de structure.
8. Une archive fictive tronquée est refusée.
9. Un conteneur fictif avec chemin dupliqué est refusé.
10. Un conteneur fictif avec chemin transversal `../` est refusé.

Un premier passage de l'essai dans V8 avait relevé l'absence de `TextDecoder` dans cet environnement. Le code a été modifié pour utiliser le décodeur UTF‑8 de Node lorsqu'il est disponible et un repli ASCII strict sur les noms de fichiers d'une archive fictive. Les 10 contrôles ci-dessus ont ensuite réussi.

## 3. Ce qui n'a PAS été vérifié
- Aucun **octet XLSX 2024–2025** n'a été obtenu au cours de la phase.
- Le script `scripts/g07-acquerir-rh-officiel.mjs` ne s'est pas exécuté avec succès contre le CDN gouvernemental.
- Les **10 tests Node** de `tests/g07-acquisition-rh.test.mjs` sont enregistrés, mais leur exécution de bout en bout n'a pas été attestée depuis GitHub Actions.
- Les définitions, valeurs, feuilles, périodes, totaux et périmètres du classeur officiel n'ont pas été contrôlés par des humains ou par la procédure d'extraction.
- Aucune comparaison de capacité clinique, aucun effectif régional, aucun coût réel et aucun changement de main-d'œuvre ne sont évalués ou approuvés.
- Les autorisations institutionnelles, les droits de diffusion et les impacts sur les travailleurs nécessiteront des examens spécifiques.

## 4. Protection de la décision
Le système reconnaît seulement les états :
`NOT_ACQUIRED`, `DOWNLOAD_BLOCKED`, `ACQUIRED_UNINTERPRETED`.

**L'état `ACQUIRED_UNINTERPRETED` ne signifie pas que les valeurs de personnel sont vérifiées.** Même après récupération du fichier officiel, il faudra une analyse distincte des feuilles, des périodes, des données géographiques et des professions. Il n'existe dans cette phase **aucune transition automatique vers la certification d'ETP ou l'approbation G0**.

## 5. Résultat
**Audit technique interne : 10/10 réussis.**  
**Acquisition du classeur : toujours `DOWNLOAD_BLOCKED`.**  
**ETP régionaux certifiés dans Nova : aucun.**  
**Statut de la porte G0 : NON FRANCHIE.**  
**Dossier officiel candidat : non modifié.**

**Ce rapport ne vaut pas audit de la source gouvernementale et ne valide pas une politique de santé.**
