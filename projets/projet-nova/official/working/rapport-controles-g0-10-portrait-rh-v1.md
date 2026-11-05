# NOVA-SINJ-G0-SAN-017 — Rapport de vérification interne G0.10, données RH MSSS

**Date :** 4 novembre 2026  
**Projet :** Projet Nova  
**Statut :** revue technique interne d'une **transcription secondaire** du fichier MSSS officiel, sans certification indépendante ni validation des cellules originales.

## 1. Fait nouveau et origine du contenu
Le tableau « Feuille A - 2 » du XLSX officiel **Portrait du personnel des établissements publics et privés conventionnés du RSSS (2024–2025)** a été accessible par conversion d'un service de lecture du fichier en Markdown. La réponse de ce service indiquait **HTTP 200** et un type de contenu XLSX.

**Source directe du fichier :** https://cdn-contenu.quebec.ca/cdn-contenu/sante/documents/Systeme_et_services_de_sante/organisation-services/donnees-systeme-sante-quebecois-services/ressources-humaines/denombrement-et-remuneration-effectif-rsss-2024-2025.xlsx

Les octets originaux n'ont **pas été conservés avec empreinte SHA-256**. Le fichier n'a pas encore été ouvert dans un logiciel tableur pour établir les coordonnées exactes des cellules et comparer les valeurs une par une. Le niveau documentaire des procédures GitHub G0.7/G0.8 reste distinct : **L1–L2 original non attestés**.

## 2. Relevé descriptif de la transcription
- **18 régions sociosanitaires**, incluant les RSS 17 Nunavik et 18 Terres-Cries-de-la-Baie-James.
- **343 252 personnes** au 31 mars 2025 réparties dans les 18 RSS.
- **804 personnes** sur une ligne organisationnelle distincte `00 — Santé Québec`.
- **344 056 personnes**, total publié, réconcilié **exactement** avec les 18 RSS et Santé Québec.
- **336 730 personnes** au 31 mars 2024, repère historique dans le même tableau; aucune interprétation causale ou de tendance faite.
- **283 740 ETC rémunérés** 2024–2025, total publié.
- **283 738 ETC** lorsque l'on additionne les valeurs entières régionales et de Santé Québec, soit un **écart non résolu de 2 ETC**. Un arrondi est plausible, mais non démontré sur les cellules originales.

Les données sont archivées comme **transcription structurée provisoire** dans :
`data/portrait-rh-msss-g0-10-2024-2025.json` et
`data/portrait-rh-msss-g0-10-2024-2025.csv`.

### Deux confusions particulièrement dangereuses
Les données portent sur des **personnes salariées et cadres du périmètre MSSS** et des **ETC calculés sur les heures rémunérées**, non sur le nombre total de professionnels de santé québécois ni les heures cliniques de première ligne réellement disponibles. Elles excluent notamment certains professionnels rémunérés par la RAMQ.

La ligne `00 — Santé Québec` **n'est pas une région sociosanitaire**. Son effectif n'a pas été attribué silencieusement à une RSS.

## 3. Vérifications effectivement exécutées
Les fichiers GitHub `assets/g10-rh-official-portrait-core.mjs`, `data/portrait-rh-msss-g0-10-2024-2025.json`, leur CSV associé, la page publique HTML, le jeu de tests Node et la configuration CI ont été relus par un vérificateur JavaScript V8.

**Résultat : 29 / 29 assertions fonctionnelles et de cohérence réussies** lors de cette intervention.

Elles vérifient notamment : 18 RSS, RSS 17/18, total 344 056, somme 343 252 + 804, total ETC 283 740, écart documenté 2, repère historique 336 730, absence de fausse empreinte SHA-256, absence de certification indépendante, absence d'ETP clinique chiffré, blocage des valeurs altérées, correspondance des 18 lignes CSV/JSON, total distinct du siège, tableau HTML, présence du lien CSV et déclenchement CI par changements de fichiers.

**Les 11 tests Node** de `tests/g10-rh-official-portrait.test.mjs` sont enregistrés mais **leur exécution de bout en bout sur GitHub Actions n'a pas été confirmée**. Les 29 contrôles ne sont pas une exécution de la suite complète Node.

## 4. Limites et actions indispensables
1. Obtenir la copie binaire originale avec empreinte SHA-256 et horodatage.
2. Confirmer les en-têtes et les coordonnées des cellules de **Feuille A - 2** pour les 18 RSS et la ligne 00.
3. Examiner le motif exact de l'écart de 2 ETC au lieu de forcer une somme.
4. Vérifier les définitions et exclusions MSSS de la version du classeur et documenter les modifications de structure autour de 2024–2025.
5. Faire valider indépendamment la transcription et la méthode avant de qualifier les effectifs de **certifiés**.
6. Préparer une source distincte pour les professionnels directement rémunérés RAMQ et les heures cliniques réellement disponibles. Les ETC du MSSS ne mesurent **pas** automatiquement l'accès aux consultations.

## 5. Statut décisionnel
**Utilisation descriptive :** possible avec mention explicite **« transcription secondaire non certifiée »** et source complète.  
**Validité de la copie binaire :** non démontrée.  
**ETC rémunérés comme ETP cliniques :** **interdit**.  
**Coût par consultation et économies :** **non établis**.  
**G0 : NON FRANCHIE.**  
**Pilote, contrat, budget ou réduction de main-d'œuvre : aucun autorisé.**

Ce rapport constitue une **vérification interne de cohérence**, non une attestation indépendante du MSSS, de Santé Québec ou de la RAMQ.
