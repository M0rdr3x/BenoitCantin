# NOVA-SINJ-G0-SAN-007 — Rapport de contrôles internes du dossier G0.5

**Date :** 3 novembre 2026  
**Projet :** Projet Nova  
**Statut :** vérification technique **interne, non indépendante**; ne constitue pas une certification juridique, financière, clinique, de sécurité ou de déploiement.  
**Dossier :** `NOVA-SINJ-G0-SAN-006` — matrice des exigences santé, 18 RSS × 8 dimensions.

## 1. Périmètre réellement testé
Les vérifications ci-dessous ont été exécutées dans un environnement JavaScript V8 isolé à partir des **contenus GitHub récupérés au cours de cette opération** :
- `assets/g0-sante-gate-core.mjs` : code de décision **bloquant par défaut**;
- `data/matrice-preuves-g0-5-sante.json` : 18 territoires, 8 dimensions, sources historiques isolées;
- `data/portrait-regional-g0-sante-2025.json` : chiffres régionaux G0.4;
- `preuves-g0-5-sante.html` : page de présentation.

Le contrôle a chargé le code `g0-sante-gate-core.mjs` comme fonctions JavaScript exécutables, puis a appliqué **16 assertions fonctionnelles** sur les valeurs et les scénarios de refus. Résultat : **16/16 assertions réussies** à cette date.

Les tests Node `tests/g0-sante-gate.test.mjs` ont été **enregistrés** sur la branche principale et inclus dans la configuration GitHub Actions, mais **aucune exécution complète de la suite Node dans GitHub Actions n'a été confirmée**. La consultation du statut GitHub associé au commit de test a rapporté **zéro statut individuel**; cela n'est ni un succès ni un échec des tests. Le clonage public depuis l'environnement de validation a échoué à la résolution DNS et n'a pas fourni de seconde exécution.

## 2. Les 16 assertions exécutées
1. Nombre total de territoires : **18**.
2. Nombre de territoires avec mesure régionale d'affiliation : **16**.
3. Nombre de régions hors champ de l'enquête ISQ : **2**.
4. Nombre d'exigences au total : **144**.
5. Nombre de cases de preuve validées dans le dossier : **0**.
6. Porte G0 : statut `NON_FRANCHI`.
7. Aucune décision ou autorisation budgétaire/pilote pour les 18 RSS.
8. Correspondance des identifiants RSS et taux régionaux d'affiliation du registre G0.4.
9. Une chaîne `VALIDEE_INDEPENDAMMENT` sans référence, période, méthode, lien de preuve et contrôleur est **rejetée**.
10. Une région avec une seule dimension complète de façon synthétique reste `NON_FRANCHI`.
11. Une région avec huit dimensions synthétiques complètes aboutit au maximum à `REVUE_FORMELLE_REQUISE`, **jamais à une autorisation**.
12. La page publique contient les **18** lignes RSS attendues.
13. La page publique contient les **8** catégories documentaires attendues.
14. La page publique comporte une mention de revue formelle.
15. Le catalogue de sources comporte **7** références institutionnelles distinctes.
16. Le plan de collecte comporte **8** tâches documentaires.

## 3. Limites et vérifications encore nécessaires
- **Aucun audit extérieur** des 16 taux régionaux PDF ISQ ou de la logique juridique; la source XLSX initiale n'est pas importée.
- **Aucune preuve régionale indépendante** sur les consultations effectivement réalisées, les ETP nets, les coûts complets, le case-mix, la qualité ou les conséquences pour les proches.
- **Aucune validation médicale ou contractuelle** par une institution compétente.
- **Aucun test navigateur visuel confirmé**, aucune validation indépendante du déploiement. L'URL publique `https://www.benoitcantin.com/projets/projet-nova/preuves-g0-5-sante.html` n'était **pas accessible** depuis l'outil de vérification externe à ce stade.
- **Aucune validation complète du workflow GitHub Actions**; cette dernière doit être constatée dans l'interface Actions ou ses journaux.
- Les tests automatiques garantissent la structure des données et certaines règles de contrôle. Ils **ne prouvent pas** la validité substantielle de futures pièces de preuve fournies.

## 4. Risques couverts par la méthode
- **Gravité élevée :** présenter l'attitration comme une consultation effectivement reçue.
- **Gravité élevée :** interpréter la provenance d'un fichier comme une série téléchargée et vérifiée.
- **Gravité élevée :** conclure à des économies à partir de paiements RAMQ partiels ou de main-d'œuvre non comparable.
- **Gravité élevée :** faire franchir automatiquement G0 par des champs de preuve simplement remplis.
- **Gravité élevée :** considérer le Nunavik et les Terres-Cries-de-la-Baie-James comme des valeurs nulles de services plutôt que des territoires hors champ de l'enquête.

## 5. Conclusion de contrôle

**Résultat interne :** 16/16 vérifications fonctionnelles passées sur l'état documentaire récupéré.  
**Certification indépendante :** absente.  
**Suite Node via GitHub Actions :** non confirmée.  
**Données territoriales de coûts comparatifs :** non reçues.  
**Autorisation de pilote :** aucune.  
**Passage de G0 :** **NON**.

Ce rapport est un **enregistrement de contrôle interne**, non une attestation par un auditeur externe. Il doit être réévalué si les sources, la méthode ou le code changent.
