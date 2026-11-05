# Projet Nova — site public sur benoitcantin.com

**URL publique :** https://www.benoitcantin.com/projets/projet-nova/

**Statut :** projet politique et institutionnel en développement — références publiques candidates, non adoptées.

Projet Nova est une démarche politique citoyenne québécoise en construction. Le site distingue les propositions politiques, les textes de référence candidats, les archives, les validations en cours et toute éventuelle activation future.

## Sources publiques prioritaires
- `official/reference/corpus.md` : architecture institutionnelle et corpus maître public;
- `official/reference/statuts.md` : statuts et gouvernance candidats du Parti Nova;
- `official/reference/programme.md` : programme public actuel;
- `data/sources.json` : manifeste des références et empreintes SHA-256;
- `document.html` : lecteur public permanent de ces références.

## Règles de publication
- La page `programme.html` et le Programme public permanent présentent les orientations politiques actuelles.
- `registre-conformite.html` indique les correctifs réalisés et les validations externes restantes.
- Les anciens PDF sont classés comme archives lorsqu’ils ne représentent plus la position courante.
- Aucun don, prêt, contribution politique ou adhésion officielle à un parti autorisé n’est recueilli sur ce site.
- Le formulaire externe de participation demeure suspendu tant que sa gouvernance des renseignements personnels n’est pas validée.

## Contrôle documentaire
Tout texte appelé à devenir officiel doit avoir un identifiant, une date, un statut, une autorité d’adoption, un journal de changements et une empreinte d’intégrité. Une page Web, une FAQ ou une brochure ne crée jamais une norme absente de la source adoptée.

## Études complémentaires Nova–Sinjira (3 novembre 2026)

Projet Nova demeure le **seul projet politique en activité** dans cette arborescence; SCQ est une référence historique, non une position en vigueur. **SINJIRA™** est un univers narratif distinct qui inspire certains principes de dignité, de preuve et de protection sans surveillance dans les études Nova.

L'architecture de travail `architecture-nova-sinjira.md` et sa page `architecture-nova-sinjira.html` sont accompagnées d'une page de mise en œuvre `mise-en-oeuvre-nova-sinjira.html` et de quatre dossiers candidats dans `official/working/` : plan d'exécution (IMP-001), protocole de santé RAMQ (SAN-001), cahier des charges des prestations (CON-001) et registre des arbitrages (DEC-001).

**Ces fichiers ne sont pas des sources officielles candidates du manifeste `data/sources.json`** : ils sont publiés pour discussion et examen externe. Leur publication ne déclenche aucune expérimentation, obligation, financement, changement de propriétaire ou modification constitutionnelle. Avant de les intégrer dans `official/reference/`, il faudrait une décision formelle, une nouvelle version datée, une validation pertinente et l'actualisation de l'empreinte SHA-256 du manifeste.

## Registre financier sectoriel (3 novembre 2026)

Le nouveau dossier `official/working/modele-financier-services-nova-sinjira-v1.md` documente la méthode de comparaison du coût public, du coût réel de production et du coût social partiel.

Les fichiers `data/reperes-financiers-nova-sinjira-2026.json` et `data/registre-donnees-services-nova-sinjira.json` séparent les repères budgétaires publics des **14 fiches de besoins en données**, dont les montants non vérifiés sont laissés à `null`.

Le site propose `comparateur-couts-services.html` (saisie locale sans tarifs par défaut) et `registre-donnees-nova-sinjira.html` (état de la donnée et références potentielles). Calcul : `assets/comparateur-financier-core.mjs` et `assets/comparateur-financier-ui.mjs`. Tests : `tests/comparateur-financier.test.mjs`, `tests/registre-donnees.test.mjs`. Commande depuis la racine du dépôt : `node --test projets/projet-nova/tests/*.test.mjs`.

La vérification continue est décrite dans `.github/workflows/nova-sinjira-finances-tests.yml` : lors des changements pertinents de code ou de données, GitHub Actions exécute les tests arithmétiques et les contrôles du registre. **La présence du workflow ne prouve pas encore la réussite d'une exécution sur GitHub Actions.**

Ces études **ne sont ni une simulation officielle du budget, ni des économies réalisées, ni des règlements adoptés**. Aucun de ces nouveaux fichiers n'est inclus au manifeste des quatre références candidates `data/sources.json`. Toute incorporation éventuelle requiert validation, versionnement, nouvelle empreinte et autorité de décision identifiée.

## Diagnostic sectoriel G0 — santé (3 novembre 2026)

- Dossier de référence **non normatif** : `official/working/diagnostic-g0-sante-premiere-ligne-v1.md`.
- Données de diagnostic et état des neuf preuves manquantes : `data/diagnostic-g0-sante-premiere-ligne-2025.json`.
- Présentation publique : `diagnostic-g0-sante.html`.
- Validation automatisée : `tests/diagnostic-g0-sante.test.mjs`, incluse dans le workflow de tests Nova–Sinjira.
- L'enquête ISQ menée en **2025**, publiée le **2 novembre 2026**, étudie les adultes visés par son périmètre; elle ne fournit ni prix par consultation ni comparaison causale des opérateurs. Les indicateurs administratifs 2024 ne sont pas directement comparables au sondage 2025.
- **Porte G0 non franchie**; aucune expérimentation autorisée, aucun budget engagé, aucune économie démontrée.
- Ce dossier n'intègre pas automatiquement le Corpus maître, le Programme, les Statuts ni le Cadre financier officiels candidats.

Le plan `data/plan-acquisition-donnees-g0-sante.json` organise les neuf preuves manquantes par interlocuteurs institutionnels possibles. Les demandes sont **préparées mais non transmises**; les tests vérifient ce statut. Aucun accès à un dossier médical individuel ou à une donnée personnelle n'est autorisé.

## Protocole G0.2 — dictionnaire des indicateurs (3 novembre 2026)

Le dossier `official/working/protocole-indicateurs-et-acces-donnees-g0-sante-v1.md` distingue **attitration**, **demande**, **rappel GAP**, **rendez-vous attribué** et **consultation réellement effectuée**, avec définitions et limites documentées par le gouvernement du Québec.

Le registre `data/dictionnaire-indicateurs-g0-sante.json` présente **15 indicateurs**, dont **4 valeurs observées dans l'enquête ISQ 2025** et **11 valeurs absentes/indicateurs à construire**. La page `indicateurs-g0-sante.html` l'expose avec des notes méthodologiques, sans classement régional inventé. Les fichiers de tableaux XLSX ISQ, dont la disponibilité est attestée, **n'ont pas encore été analysés** et ne sont pas reproduits.

Trois modèles de correspondance existent sous `official/working/modeles-demandes-donnees-g0-sante-v1.md` pour l'ISQ, la RAMQ et Santé Québec : **aucune demande n'a été envoyée**. Les demandes de documents administratifs et tout accès à des renseignements de santé sont soumis aux règles et autorisations applicables.

Les tests intégrés dans `tests/diagnostic-g0-sante.test.mjs` vérifient l'absence de coûts fictifs et de conclusion causale, la présence des sources et la différence entre les rappels et les consultations. **Aucune exécution CI réussie n'est certifiée par le simple ajout des tests.**

## G0.3 — Étape historique de repérage du portrait régional

Le premier inventaire G0.3 a recensé les **18 régions sociosanitaires**, les RSS 17 et 18 exclues de l'enquête, ainsi que six différences qualitatives signalées par le communiqué ISQ du 2 novembre 2026. **À cette étape historique**, aucun taux régional exact n'était encore extrait. Cet ancien constat **a été dépassé par G0.4** grâce à la lecture du PDF officiel.

Le protocole initial `official/working/protocole-portrait-regional-sante-g0-v1.md` est conservé pour la traçabilité historique et renvoie désormais au protocole G0.4.

## G0.4 — Taux régionaux exacts issus du Panorama ISQ 2026

- **Source :** Institut de la statistique du Québec, *Panorama des régions du Québec 2026*, chapitre 8, https://statistique.quebec.ca/fr/fichier/panorama-des-regions-du-quebec-2026-sante.pdf , **tableau 8.1 page imprimée 144** et **tableau 8.3 page imprimée 146**, publié le 2 novembre 2026.
- **Registre :** `data/portrait-regional-g0-sante-2025.json` : **16 taux numériques d'affiliation**, lieux habituels de suivi des affiliés et démarches vers l'urgence au dernier besoin semi-urgent/non urgent (avec les dénominateurs distincts), 2 RSS hors champ, 0 coût régional.
- **CSV :** `data/portrait-regional-g0-sante-2025.csv`, 18 RSS avec codes préservés `RSS-01` à `RSS-18`, source identifiée et champs manquants laissés vides.
- **Page :** `portrait-regional-g0-sante.html`, tableau source et avertissements sur la confusion possible entre affiliation et accès effectif.
- **Méthode courante :** `official/working/protocole-portrait-regional-sante-g0-v2.md` (NOVA-SINJ-G0-SAN-005), qui remplace l'analyse qualitative v1 pour les faits disponibles.
- **Tests :** `tests/portrait-regional-g0-sante.test.mjs` et fichier GitHub Actions `.github/workflows/nova-sinjira-finances-tests.yml` : vérifications locales automatisables des 16 valeurs, écarts significatifs rapportés, nombres 0–100, catégories de lieux avec tolérance d'arrondi, flags de précision, concordance CSV/JSON et statut non décisionnel.
- **Statut du XLSX :** le classeur régional ISQ est référencé mais **n'a pas été téléchargé**. Les chiffres G0.4 viennent du **PDF**, pas d'un import Excel. Les effectifs, les intervalles de confiance régionaux, la comparaison des coûts et l'audit externe restent indisponibles.
- **Interprétation :** affiliations, endroits habituels de suivi et démarches vers l'urgence utilisent des populations différentes. Les variations observées ne prouvent aucune causalité ni supériorité de gestion. Nunavik et Terres-Cries-de-la-Baie-James ne sont pas couverts par l'enquête; leur obligation d'accès n'en est pas diminuée.
- **Gouvernance :** G0 **non franchie**, aucune région pilote désignée, aucun contrat, économie ou traitement de données de patient autorisé. Les quatre références candidates et leurs empreintes dans `data/sources.json` ne sont pas modifiées.

## G0.5 — Accès effectif, main-d'œuvre et coûts complets (3 novembre 2026)

- **Dossier technique non normatif :** `official/working/protocole-g0-5-preuve-capacite-sante-v1.md` (NOVA-SINJ-G0-SAN-006).
- **Matrice des preuves par RSS :** `data/matrice-preuves-g0-5-sante.json` (18 RSS × 8 dimensions = **144 éléments de preuve**; **0 indépendamment validé** dans le dossier Nova).
- **Contrôleur déterministe et bloquant par défaut :** `assets/g0-sante-gate-core.mjs`. Les preuves incomplètes restent `NON_FRANCHI`. Huit preuves complètes ne peuvent déclencher qu'une `REVUE_FORMELLE_REQUISE`, **jamais une autorisation de pilote, de budget ou de privatisation**.
- **Tests :** `tests/g0-sante-gate.test.mjs` couvre complétude, 18 RSS, exclusions, fausses validations, aucun pilote automatique, et l'isolement des références historiques provinciales. La configuration GitHub Actions est mise à jour; son exécution effective ne doit pas être supposée.
- **Présentation :** `preuves-g0-5-sante.html`, accessible depuis le diagnostic, la page régionale, le registre, la conformité, la bibliothèque et l'accueil.
- **Rapport interne :** `official/working/rapport-controles-g0-5-sante-v1.md` : 16/16 contrôles exécutables réussis dans un environnement V8 sur les fichiers récupérés; aucune certification indépendante, aucun journal CI complet ni déploiement public vérifiés.
- **Sources vérifiées :** pages publiques du gouvernement du Québec et de la RAMQ concernant les accès à la première ligne, la performance du GAP, les données RH 2024–2025, St@tRAMQ et les statistiques sur demande. Les fichiers XLS/XLSX listés n'ont **pas** été importés ni convertis en chiffres régionaux inventés.
- **Données historiques nationales :** 36 % de consultation en clinique à l'intérieur de 36 h, 84 % d'attitration, 79,5 % de rétention 0–12 mois des nouvelles embauches dans le réseau, **exercice 2024–2025 seulement**, publiées par le tableau stratégique gouvernemental. Ne pas les comparer directement aux 82 % de l'enquête ISQ 2025 ni aux 16 RSS de G0.4.
- **Priorités de collecte :** huit tâches `Q01–Q08`, toutes `NON_ENTAME`. Les demandes documentaires préexistantes `M01–M09` et les trois lettres modèles sont toujours **non transmises**.
- **Règles :** pas de données personnelles de santé ni de microdonnées sans autorisations, pas de coûts inventés, pas de déplacement ignoré des ETP publics, pas d'exclusion des RSS 17/18 du droit d'être considérées. **G0 non franchie**.
- Les références officielles candidates du programme, du corpus, des statuts et des finances restent inchangées et les empreintes de `data/sources.json` ne sont pas modifiées.

## G0.6 — Personnel, ETP et capacité clinique (3 novembre 2026)

- Dossier de travail, **non normatif** : `official/working/protocole-g0-6-capacite-personnel-sante-v1.md` (NOVA-SINJ-G0-SAN-008).
- Registre des 18 RSS : `data/registre-rh-regional-g0-6-sante.json`, 11 définitions et 4 familles de sources, **aucune donnée RH régionale chiffrée importée ou validée**.
- Page pédagogique : `capacite-rh-g0-6-sante.html`, avec périmètres et un exemple fictif qui montre qu'un déplacement de dix ETP ne crée pas d'ETP net.
- Contrôle de cohérence : `assets/g06-capacite-rh-core.mjs`, exige la même unité clinique, le même territoire, des périodes comparables et un chevauchement contrôlé; ne prétend mesurer aucune productivité ni économie.
- **Rapport interne :** `official/working/rapport-controles-g0-6-capacite-rh-v1.md` : 21 vérifications fonctionnelles exécutées et réussies, sans certification externe, sans accès au XLSX de 2024–2025 et sans confirmation de déploiement public.
- Tests : `tests/g06-capacite-rh.test.mjs`, intégrés à la configuration `.github/workflows/nova-sinjira-finances-tests.yml` sans supposer l'exécution de GitHub Actions.
- **Source officielle existante mais non téléchargée :** classeur MSSS `Portrait du personnel des établissements publics et privés conventionnés ... (2024–2025)` depuis `https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-humaines`. Tentative de téléchargement échouée. Aucun chiffre provincial ou régional issu du XLSX n'est fabriqué.
- **Définitions distinctes :** personnel ayant un lien d'emploi, personnel présent (R22), heures pertinentes, ETP clinique, professionnels rémunérés par la RAMQ (St@tRAMQ), heures supplémentaires obligatoires. Les professionnels rémunérés par la RAMQ et certains EPC ne font pas partie du même périmètre R22.
- **Aucune addition** d'effectifs, de professionnels RAMQ et d'ETP sans méthode de dédoublonnage et période homogène. Les RSS 17 et 18 restent exclues **de l'enquête ISQ 2025**, mais non des recherches RH possibles.
- **État :** G0 non franchie, aucun chiffrage unitaire, transfert de personnel, contrat, changement d'emploi ou budget adopté. Le corpus, le programme, les statuts, les finances candidats et le manifeste `data/sources.json` restent inchangés.

## G0.7 — Acquisition contrôlée du XLSX RH (4 novembre 2026)

**État vérifié :** le gouvernement du Québec répertorie le XLSX public `Portrait du personnel des établissements publics et privés conventionnés (2024–2025)`, 136 Ko environ; son téléchargement depuis les environnements de travail a **échoué**. Aucun chiffre RH ne peut donc être attribué aux 18 RSS à partir de ce XLSX. Cette situation est consignée et ne signifie pas qu'il n'existe aucun personnel dans les régions.

- **Page G0.7 :** `acquisition-rh-g0-7-sante.html`, bilan des portes documentaires L0–L5, avec seulement L0 confirmé.
- **Protocole :** `official/working/protocole-g0-7-acquisition-rh-v1.md`, provenance, permissions, schéma et précautions.
- **Registre des tentatives :** `data/registre-acquisition-rh-g0-7.json` initialement `DOWNLOAD_BLOCKED`, aucune empreinte ni feuille XLSX inventée.
- **Validation pure :** `assets/g07-rh-acquisition-core.mjs` — inventaire central ZIP/XLSX sans décompression ni extraction de données de personnel, empreinte et provenance obligatoires pour une acquisition réussie.
- **Script de téléchargement volontaire :** `scripts/g07-acquerir-rh-officiel.mjs` — HTTPS officialisé, hôte CDN gouvernemental autorisé, limite 5 Mo, SHA‑256, date UTC et rapport de contrôles; sortie dans artefact et non dans le dépôt.
- **Workflow manuel :** `.github/workflows/nova-g07-acquisition-rh.yml`. Déclencheur **`workflow_dispatch` seulement**, `contents: read`, conservation d'artefacts 14 jours, pas de commit automatique. **N'a pas été exécuté ni attesté réussi à cette date.**
- **Tests d'intégrité :** `tests/g07-acquisition-rh.test.mjs` : 10 cas prévus sur l'inventaire ZIP, faux/invalides, interdiction de chiffres et blocage du statut non acquis.
- **Rapport interne :** `official/working/rapport-controles-g0-7-acquisition-rh-v1.md` : 10/10 contrôles de structure exécutés dans V8 avec ZIP synthétiques; aucune analyse du XLSX officiel ni exécution complète de GitHub Actions attestée.
- **Suite test générale :** surveillance des fichiers G0.7 ajoutée à `.github/workflows/nova-sinjira-finances-tests.yml`; l'ajout ne certifie aucun résultat CI.
- **Étape de reprise :** dans GitHub Actions, sélectionner **Projet Nova G0.7 — audit source RH officielle**, puis **Run workflow**. Vérifier les journaux et l'artefact `source-audit.json`, ainsi que les octets XLSX si valides. Ne pas actualiser `registre-rh-regional-g0-6-sante.json` sans inspecter les feuilles, régions, périodes, professions, unités, doubles comptes et droits de diffusion.

**Restrictions permanentes :** aucune donnée individuelle de salaire ou de patient, aucun ETP de première ligne inféré des personnes rémunérées RAMQ, aucun effet financier garanti, aucune autorisation automatique de pilote, aucun changement aux documents officiels candidats ou au manifeste `data/sources.json`.

## G0.8 — Audit des métadonnées du classeur RH (4 novembre 2026)

**État documenté :** fichier XLSX gouvernemental de la période **2024–2025** repéré; **octets non obtenus**. L'URL officielle et le catalogue sont confirmés, mais aucune feuille, donnée RH ni valeur d'ETP n'a été lue dans cette intervention.

- **Page de suivi :** `audit-classeur-rh-g0-8-sante.html`, treize critères et six niveaux documentaires (L0 seul confirmé).
- **Contrat qualité :** `data/registre-verification-classeur-rh-g0-8.json`, **18 RSS** et **13 contrôles**; toutes les valeurs RH demeurent `null`.
- **Inspecteur Node 22 :** `assets/g08-rh-workbook-inspector.mjs`, vérifie ZIP/CRC, XML du classeur, relations internes, noms, dimensions, absence de macros, relations externes et fichiers incorporés suspects. Il **n'extrait aucune valeur de cellule**, aucun ETP ni salaire.
- **Tests :** `tests/g08-rh-workbook-inspector.test.mjs`, onze scénarios sur des archives XLSX **synthétiques**, notamment métadonnées valides, fichiers tronqués, chemins liés, CRC, macros et XML potentiellement dangereux.
- **Rapport de contrôle interne :** `official/working/rapport-controles-g0-8-validation-rh-v1.md` : 9/9 scénarios V8 exécutés sur des ZIP synthétiques non comprimés. Les 11 tests Node du dépôt, dont les scénarios DEFLATE, ne sont pas encore attestés comme exécutés.
- **Acquisition G0.7 renforcée :** `scripts/g07-acquerir-rh-officiel.mjs` impose désormais `inspectOfficialRhWorkbook` avant d'enregistrer la source et ajoute `xlsx_metadata` au rapport; `assets/g07-rh-acquisition-core.mjs` rejette un manifeste prétendument acquis sans contrôle L2. Le registre G0.7 reste `DOWNLOAD_BLOCKED`.
- **Workflow manuel :** `.github/workflows/nova-g07-acquisition-rh.yml` doit désormais exécuter les tests G0.7 et G0.8 avant toute tentative de téléchargement; **aucune exécution réussie n'est confirmée** par le seul ajout de cette configuration. Le workflow a uniquement `contents: read`, ne commit pas et conserve les artefacts au maximum 14 jours.
- **Méthode :** `official/working/protocole-g0-8-validation-classeur-rh-v1.md` (NOVA-SINJ-G0-SAN-012); vérification future des en-têtes, unités, territoires, périodes, doubles comptes, données supprimées et examen indépendant avant toute interprétation.
- **Gouvernance :** une copie SHA‑256 et des métadonnées OOXML cohérentes ne certifient pas les valeurs et ne peuvent déclencher ni ETP, ni économies, ni pilote. La source 2024–2025 n'est pas automatiquement représentative des effectifs de 2026. Aucune donnée personnelle de salarié ou patient n'est importée.
- **Préservation :** références candidates du programme, du corpus, des finances et des statuts ainsi que le manifeste `data/sources.json` **inchangés**.

## G0.9 — Revue des données RH et contrôle du double comptage (4 novembre 2026)

- **Source officielle référencée mais non acquise :** le fichier gouvernemental `Portrait du personnel ... (2024–2025)` est listé sur Québec.ca; le téléchargement direct reste bloqué. Aucun dénombrement régional ni ETP n'a été extrait.
- **Page G0.9 :** `rapprochement-rh-g0-9-sante.html`, explication des 13 contrôles et 18 RSS. Toutes les valeurs régionales RH sont « non disponibles » et non zéro.
- **Registre :** `data/registre-rapprochement-rh-g0-9.json`, treize contrôles (source, feuille/cellule, géographie, période, unité, rôle détail/sous-total, doublons, suppression, zéro réel, RAMQ, première ligne, revue indépendante, autorité).
- **Nouveau moteur de rapprochement :** `assets/g09-rh-reconciliation-core.mjs`, qui vérifie les références de cellules, les grains conceptuels, les doublons, les valeurs supprimées, l'empreinte source et les revues humaines. Il ne réalise **aucune somme officielle automatique** et retourne toujours `ready_for_release:false`.
- **Paquet de revue :** `scripts/g09-generer-paquet-revue-rh.mjs`. Il exige un fichier G0.7/G0.8 réellement obtenu, revérifie son SHA‑256 et sa liste de feuilles, puis produit `g09-review-package.json` sans cellule ni montant de personnel.
- **Tests :** `tests/g09-rh-reconciliation.test.mjs` contient dix scénarios synthétiques sur les contrôles de mappage et de refus.
- **Rapport interne :** `official/working/rapport-controles-g0-9-rapprochement-rh-v1.md`, 23/23 contrôles fonctionnels exécutés avec des données synthétiques; la suite Node, le téléchargement et le déploiement restent non confirmés. Le workflow manuel `.github/workflows/nova-g07-acquisition-rh.yml` exécute les tests G0.7/G0.8/G0.9 puis, **seulement après téléchargement réussi**, produit un paquet G0.9 comme artefact temporaire de 14 jours. La réussite GitHub Actions n'est pas attestée.
- **Protocole :** `official/working/protocole-g0-9-interpretation-rh-v1.md` (NOVA-SINJ-G0-SAN-014), méthode de revue des tableaux et des sous-totaux avant tout calcul d'effectif.
- **Contraintes :** personnel salarié R22 ≠ professionnels rémunérés RAMQ ≠ ETP cliniques; un pourcentage ISQ 2025 ≠ dénombrement RH 2024–2025. Une valeur manquante ou supprimée reste `null`, zéro n'est accepté que lorsqu'observé. Les 18 RSS et catégories d'établissement doivent être confirmées, pas inférées.
- **Gouvernance :** G0 **non franchie**; aucune réforme, aucune économie et aucun budget autorisés. Les références officielles candidates et les empreintes du manifeste `data/sources.json` restent inchangées.

## G0.10 — Première transcription régionale chiffrée MSSS (4 novembre 2026)

**Nouveauté réelle :** une conversion secondaire du XLSX officiel MSSS `Portrait du personnel des établissements publics et privés conventionnés du RSSS (2024–2025)` a rendu lisible sa **Feuille A - 2**. Le parseur a servi le contenu du XLSX via HTTPS, mais **les octets originaux n'ont toujours pas été conservés localement, aucun SHA-256 n'a été obtenu et aucune adresse de cellule originale n'a été auditée**. Cela ne fait pas passer automatiquement L1/L2 des contrôles G0.7/G0.8, mais permet une **transcription descriptive provisoire sourcée**.

- **Données descriptives provisoires :** `data/portrait-rh-msss-g0-10-2024-2025.json`, avec 18 RSS et les valeurs de personnes au 31 mars 2025, personnes au 31 mars 2024 et ETC rémunérés en 2024–2025, conservées séparément.
- **Contrôle de totaux personnes :** 18 RSS **343 252** + ligne organisationnelle Santé Québec (00) **804** = total source **344 056 personnes** au 31 mars 2025; **somme exacte**.
- **ETC rémunérés :** le total source est **283 740 ETC** en 2024–2025, alors que la somme des entiers régionaux transcrits et de la ligne Santé Québec est **283 738** : **écart de 2 ETC documenté sans correction artificielle**; cause éventuelle d'arrondi à vérifier. **ETC rémunérés ≠ ETP cliniques disponibles**.
- **Portée statistique :** salariés et personnel d'encadrement de certains établissements publics et privés conventionnés et de Santé Québec, excluant notamment les professionnels directement rémunérés par la RAMQ, la main-d'œuvre indépendante et le privé non conventionné. Les RSS **17 Nunavik** et **18 Terres-Cries-de-la-Baie-James** sont couvertes dans ce portrait RH, même si elles étaient hors champ de l'enquête ISQ 2025 (source et population différentes).
- **Page consultable dans le dépôt :** `portrait-effectifs-rh-g0-10-sante.html`, avec l'ensemble des 18 lignes, la ligne Santé Québec, les deux totaux et les réserves.
- **Protocole :** `official/working/protocole-g0-10-portrait-rh-msss-v1.md` (NOVA-SINJ-G0-SAN-016).
- **Validateur de transcription :** `assets/g10-rh-official-portrait-core.mjs`, exige 18 RSS distinctes, la somme des personnes exacte, l'écart ETC de 2 visible et les marqueurs `independent_audit:false`, `clinical_fte:null` et aucune permission.
- **Tests :** `tests/g10-rh-official-portrait.test.mjs`, onze cas (incluant la correspondance CSV/JSON) sur les erreurs de total, régions, statuts et faux ETC cliniques; les données et le fichier sont suivis par la configuration CI. Ne pas confondre contrôles V8 locaux et tests GitHub Actions complets.
- **Rapport de contrôle interne :** `official/working/rapport-controles-g0-10-portrait-rh-v1.md` documente **29/29 contrôles V8 réussis** sur la transcription JSON, le CSV, les sommes et les garde-fous; les 11 tests Node complets demeurent non attestés par GitHub Actions.
- **CSV détaillé :** `data/portrait-rh-msss-g0-10-2024-2025.csv` (18 RSS, ligne 00 Santé Québec et total publié), chiffres de source sans certification complète.
- **Préservation des phases G0.6–G0.9 :** les champs certifiés demeurent **`null`**, car la transcription secondaire G0.10 n'est pas une validation originale de L1/L2. Les registres antérieurs pointent vers le nouveau fichier dans `g10_secondary_rh_portrait`. Les textes officiels candidats et le manifeste `data/sources.json` demeurent inchangés.
- **Pour certifier :** obtenir la copie binaire avec SHA-256, vérifier les cellules de la Feuille A - 2, résoudre l'écart de 2 ETC et faire confirmer le périmètre par un expert indépendant. **G0 NON FRANCHIE**, aucun pilote, transfert de personnel ni économie autorisés.

## G0.12 — Audit de complétude du programme (5 novembre 2026)

**État d'avancement estimé : 47/100 (47 %) vers un programme complet et applicable.** Il s'agit d'une **grille interne de maturité**, non d'une mesure scientifique ni d'un programme juridiquement ou financièrement certifié. La structuration/rédaction des orientations est appréciée à **environ 75 %**, mais ce second chiffre n'est pas audité indépendamment.

- **Page publique :** `avancement-programme-nova.html`. Barème détaillé, dix domaines, quatorze chantiers, priorités documentaires et statut non adopté.
- **Grille structurée :** `data/audit-completude-programme-nova-2026-11-05.json`. Somme des poids = 100, points accordés = 47; motivations par domaine et preuves sources, six décisions prioritaires.
- **Audit détaillé :** `official/working/audit-completude-programme-g0-12-v1.md`. Le score ne représente ni une autorisation du parti, ni un budget équilibré, ni le droit d'appliquer une réforme.
- **Validation logicielle :** `assets/audit-completude-programme-core.mjs` et `tests/audit-completude-programme.test.mjs`. Douze contrôles Node déclarés sur le calcul, les 14 chantiers, les pondérations, les falsifications du statut et les priorités; ne pas annoncer une exécution GitHub Actions sans journal.
- **Points critiques :** financement des deux scénarios (Québec dans le Canada et Québec souverain), fiscalité à deux prélèvements non démontrée à l'équilibre, avis juridiques, transition constitutionnelle, budgets des 14 chantiers, évaluation indépendante, droits et protection de la main-d’œuvre, adoption statutaire et organisation électorale.
- **Références préservées :** `official/reference/programme.md`, `corpus.md`, `finances.md`, `statuts.md`, et `data/sources.json` n'ont pas été modifiés pour la phase G0.12. Le corpus technique V322 est un candidat non adopté, non un résultat normatif.
- **Loi électorale provinciale :** source et guides à jour sous `https://www.electionsquebec.qc.ca/`. Le dépôt ne contient pas de preuve confirmant une autorisation officielle du Parti Nova et ne doit donc pas la présumer.
- **Prochaine priorité :** dresser un **cadre fiscal et budgétaire consolidé sur dix ans** avec hypothèses explicites, puis les matrices juridiques et de transition pour rendre les mesures budgétables et soumises à un avis indépendant.

## Validation externe requise
Le caractère « document de référence » ne remplace jamais les validations juridique, financière, électorale, cybersécurité ou accessibilité requises.

## Traçabilité
Les anciennes versions retirées du site actif restent conservées dans l’historique Git. Elles servent à retracer l’évolution du projet, mais ne sont pas des sources publiques prioritaires.
