# Projet Nova — site public sur benoitcantin.com

**URL publique :** https://www.benoitcantin.com/projets/projet-nova/

**Statut :** projet politique et institutionnel en développement — références publiques candidates, non adoptées.

Projet Nova est une démarche politique citoyenne québécoise en construction. Le site distingue les propositions politiques, les textes de référence candidats, les archives, les validations en cours et toute éventuelle activation future.

## Qualité du sondage et de la boussole (audit 2026-11-07)

**Objectif : tests complets et critères de réception prouvés avant toute affirmation « 100 % ».** Les deux pages ont été contrôlées en navigateur sans envoyer de bulletin. Le **questionnaire de la boussole (64 questions / 16 dimensions)** a passé les contrôles de cohérence des pôles et les premières étapes du parcours. Les **huit questions du sondage** correspondent exactement à leurs homologues GitHub, au bundle JS publié dans le dépôt et aux huit questions Supabase.

**Améliorations directement effectuées :** `assets/nova-civic-integrity.js` (contrôles purs des questions, poids et orientations); `assets/boussole-electorale.js` et `assets/sondage-citoyen.js` (validation obligatoire à la lecture); `sondage-citoyen.html` (progression accessible); `assets/sondage-citoyen.css` (style adapté) et chargements JS versionnés dans les deux pages. Le chargement des fiches partisanes refuse aussi un questionnaire non valide.

**Tests et sécurité :** `tests/nova-civic-integrity.test.mjs` déclare **35 tests**, `tests/nova-civic-scoring.test.mjs` en déclare **25** et `tests/nova-civic-readiness.test.mjs` en déclare **10**. Le moteur de calcul a reproduit à l'identique les résultats de **260 profils de test** comparés au précédent algorithme; leur suite Node CI complète reste à confirmer. La revue en lecture seule de Supabase constate **5 tables protégées par RLS** et sans privilèges SQL CRUD pour `anon` ou `authenticated`. Le RPC `nova_poll_submit` est exécutable uniquement par `service_role`. **Aucune soumission de production n'a été créée**; le sondage reste fermé, les comptes de votes et de publication sont à zéro. Les résultats publics restent cachés.

**Matrice de réception :** `data/validation-sondage-boussole-2026-11-07.json` — **5/12 contrôles attestés pour la boussole**, **6/11 pour le sondage**, le reste est en attente. **Rapport :** `official/working/audit-qualite-sondage-boussole-2026-11-07-v1.md`. Preuves de navigation non destructive : https://agent.tinyfish.ai/runs/59ec01c2-2ef7-407f-a5bd-20e52b7b64e4 (parcours court), https://agent.tinyfish.ai/runs/cd87d505-b0a4-4252-b23e-64309558e4e3 (Q01 à Q25, toutes passées) et https://agent.tinyfish.ai/runs/9ecee317-305e-469f-a6a5-223c2055fba3 (Q01/Q02 et réinitialisation).

**Parcours amélioré :** un bouton « Voir mon profil actuel (même incomplet) » permet maintenant de consulter les axes déjà renseignés sans imposer 64 clics; tout axe ayant moins de deux réponses principales reste sans score. Le moteur pur `scoreCompass` rejette les réponses et poids hors limites. Les huit textes du sondage sont désormais vérifiés contre un corpus canonique indépendant dans le contrôleur public.

**Déploiement réel distinct :** le bouton de profil partiel n'a **pas** été trouvé pendant la dernière vérification du site en ligne, même si les fichiers HTML/JS/CSS sont committés dans `main`. Le workflow `.github/workflows/deploy-netlify-staging.yml` impose un déclenchement manuel et des preuves de SHA, sans promotion en production. **La version publique récente n'est donc pas homologuée ni déclarée en production.** Le passage par la validation staging, les tests d'intégration et la promotion explicitement autorisée reste requis.

**Consentement et droit électoral :** la case de consentement du sondage exprime maintenant sa finalité, le caractère sensible des opinions, la publication conditionnelle de résultats agrégés et l'impossibilité de retirer un bulletin individuel après agrégation. Le rapport `official/working/controle-juridique-confidentialite-sondage-2026-11-07-v1.md` expose les références de la CAI et d'Élections Québec et les risques encore soumis à revue indépendante. Le sondage reste fermé.

**Vérification directe renforcée :** 70/70 cas des trois suites de tests ont aussi été rejoués avec succès dans un isolat V8 à partir des fichiers GitHub, avec émulation minimale des interfaces Node. **Ce n'est ni une exécution Node native ni une preuve d'un CI GitHub réussi**; il reste à obtenir les journaux d'exécution officiels, l'audit navigateurs et la validation du déploiement.

**Portes non franchies :** parcours complet de 64 questions jusqu'aux résultats, cas `skip` et importance, tests multi-navigateurs et accessibilité, publication incrémentale et confidentialité des lots, envois Turnstile anti-rejeu en préproduction, revue juridique et autorisation d'ouverture du sondage. La comparaison des partis demeure **désactivée** tant que la couverture documentaire et les revues indépendantes ne sont pas établies. La suite GitHub Actions n'est pas attestée réussie ni la dernière version HTML/JS confirmée déployée. Ne pas proclamer « 100 % ».

**Distinct du score politique G0.12 :** l'évaluation interne globale du programme demeure à **47/100**, sans rapport direct avec le nombre de tests ou de critères des deux outils.

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
- **Validation logicielle :** `assets/audit-completude-programme-core.mjs` et `tests/audit-completude-programme.test.mjs`. Douze contrôles Node sur le calcul, les 14 chantiers, les pondérations, les falsifications du statut et les priorités; **12/12 exécutés avec succès sous Node v26 dans un environnement externe**, et non dans GitHub Actions. Le journal est `data/rapport-test-completude-g0-12-2026-11-05.json`.
- **Points critiques :** financement des deux scénarios (Québec dans le Canada et Québec souverain), fiscalité à deux prélèvements non démontrée à l'équilibre, avis juridiques, transition constitutionnelle, budgets des 14 chantiers, évaluation indépendante, droits et protection de la main-d’œuvre, adoption statutaire et organisation électorale.
- **Références préservées :** `official/reference/programme.md`, `corpus.md`, `finances.md`, `statuts.md`, et `data/sources.json` n'ont pas été modifiés pour la phase G0.12. Le corpus technique V322 est un candidat non adopté, non un résultat normatif.
- **Loi électorale provinciale :** source et guides à jour sous `https://www.electionsquebec.qc.ca/`. Le dépôt ne contient pas de preuve confirmant une autorisation officielle du Parti Nova et ne doit donc pas la présumer.
- **Prochaine priorité :** dresser un **cadre fiscal et budgétaire consolidé sur dix ans** avec hypothèses explicites, puis les matrices juridiques et de transition pour rendre les mesures budgétables et soumises à un avis indépendant.

## G0.13 — Viabilité financière sur dix ans et deux statuts du Québec (5 novembre 2026)

**Source budgétaire actualisée :** Rapport préélectoral du ministère des Finances du Québec **d'août 2026**, plus récent que le budget de mars 2026. Les valeurs des cinq exercices **2026–2027 à 2030–2031** sont reprises comme **prévisions du gouvernement**, non comme budget approuvé du Projet Nova.

- **Premier exercice (millions CAD) :** revenus **168 389**, dont transferts fédéraux **33 046**; dépenses **171 597**; provision **2 000**; déficit comptable **–5 208**; déficit budgétaire après Fonds des générations **–7 690**.
- **Source publique :** `https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf`, tableau pluriannuel; valeurs recoupées dans la présentation de la Province du Québec déposée à la SEC. Les années **2031–2036** ne figurent pas dans cette prévision de cinq ans et restent `null`.
- **Données :** `data/cadre-financier-g0-13-2026-2036.json` regroupe les prévisions gouvernementales (5 exercices), les cinq années hors source et **deux scénarios Nova distincts** (`QUEBEC_CANADA` et `QUEBEC_SOUVERAIN`) dont les postes non évalués demeurent `null` pendant les dix ans.
- **Écarts futurs du rapport officiel :** **1 850 M$ en 2028–2029** et **2 000 M$ par an en 2029–2031** encore à résorber; ils sont présentés comme hypothèses conditionnelles, non comme des économies réalisées.
- **Politique de deux prélèvements :** impôt sur les revenus et mesure ciblant l'évasion et les paradis fiscaux **sans taux, assiette et rendement démontrés**; ne pas assimiler les revenus autonomes aux seuls impôts ni présumer la conservation des transferts fédéraux après souveraineté.
- **Méthode :** `official/working/cadre-financier-g0-13-scenarios-protocole-v1.md`. L'analyse impose droit, assiettes, coûts de services, monnaie, dettes et actifs, prestations, droits des nations autochtones, pouvoir d'achat et protection des travailleurs.
- **Page de consultation :** `viabilite-financiere-g0-13.html`; **contrôle automatisé :** `assets/g13-fiscal-readiness-core.mjs`; **tests :** `tests/g13-fiscal-readiness.test.mjs`.
- **Exécution des tests :** **16/16 réussis sous Node v26.12.1 dans un environnement externe**, rapport `data/rapport-tests-g0-13-finances-2026-11-05.json`. L'exécution des GitHub Actions de ce changement et le déploiement public ne sont pas vérifiés.
- **Avancement du programme : 47/100, inchangé** (grille G0.12). Construire un tableau ne constitue pas une validation indépendante de la viabilité fiscale. Le cadre de mars reste un repère historique; les références candidates `official/reference` et `data/sources.json` ne sont pas modifiés.

**Étape G0.14 :** définir la classification juridique des recettes (revenus des particuliers et entreprises, TVA/TVQ, cotisations, redevances, tarifs, bénéfices des sociétés d'État, transferts fédéraux et taxes municipales), construire des assiettes défendables, documenter l'incidence distributive, puis seulement tester des taux et la soutenabilité de scénarios complets.

## G0.14 — Cartographie des recettes et examen d'un système à deux prélèvements (5 novembre 2026)

**Programme : 47/100, inchangé**, tant que les dépenses, les recettes sous réforme et les assiettes ne sont pas démontrées. G0.14 ne fixe aucun taux et ne revendique aucune économie nouvelle.

- **Registre de travail :** `data/registre-assiettes-fiscales-g0-14-2026-2027.json`, neuf familles de recettes gouvernementales 2026–2027, six régimes ou compétences à distinguer, deux trajectoires constitutionnelles et sept études à mener.
- **Rapprochement officiel :** huit catégories provinciales = **135 343 M$** de revenus autonomes; **33 046 M$** de transferts fédéraux, ensemble **168 389 M$**. Source : Rapport préélectoral d'août 2026 et tableau G0.13, non budget Nova.
- **Sensibilité arithmétique uniquement :** santé FSS **9 538 M$** + foncier scolaire **1 301 M$** + taxes à la consommation **30 682 M$** = **41 521 M$** de recettes exposées à examiner. Dans un calcul artificiellement figé sans compensation, le solde budgétaire serait **−49 211 M$** plutôt que **−7 690 M$**. Ce chiffre **n'est pas** une prévision de la réforme Nova et conserve temporairement les droits et redevances mixtes (6 484 M$).
- **Deux prélèvements envisagés :** définir un impôt sur les revenus des particuliers et entreprises et préciser si le deuxième « prélèvement anti-paradis fiscaux » est réellement une assiette additionnelle légale ou un mécanisme de conformité de l'impôt sur les revenus. Rendement net additionnel `null`, taux `null`, budget Nova `null`.
- **Protection des régimes :** taxes municipales et fédérales, RRQ, RQAP, assurance médicaments, droits et redevances de ressources et dividendes des sociétés publiques ne sont pas automatiquement des taxes provinciales supprimables ni des recettes provinciales libres.
- **Québec souverain :** aucune hypothèse de conservation des **33 046 M$** de transferts fédéraux; fonctions à reprendre, pensions, monnaie, dette, actifs et recettes complémentaires à évaluer.
- **Protocole :** `official/working/protocole-g0-14-recettes-et-deux-prelevements-v1.md`; **page publique :** `deux-prelevements-g0-14.html`; **contrôle :** `assets/g14-fiscal-assiettes-core.mjs`; **tests Node :** `tests/g14-fiscal-assiettes.test.mjs` (16 cas). **16/16 tests Node réussis** en environnement externe (Node.js v26.12.1), sans preuve de réussite GitHub Actions. Rapport : `official/working/rapport-controles-g0-14-assiettes-fiscales-v1.md`. Ces contrôles ne certifient pas la viabilité de la politique fiscale.
- **Sources de droit et fiscalité :** ministères du Québec, Revenu Québec et documentation municipale. La compatibilité juridique de la réforme proposée demeure **non examinée par un spécialiste indépendant**.
- **Étape G0.15 :** mettre en œuvre la ventilation des prélèvements mixtes, la définition juridiquement utilisable de l'assiette « revenu », les fonds sociaux et l'analyse distributive avant de proposer un taux.

Le programme, le corpus, le cadre financier et les statuts de référence candidats, ainsi que `data/sources.json`, ne sont pas modifiés par cette étude.

## G0.15 — Ventilation fiscale, fonds sociaux et incidence distributive (5 novembre 2026)

**Suite de G0.14 :** protocole documentaire de quinze preuves fiscales V01–V15, **sans chiffres inventés, sans nouvelle taxe adoptée et sans suppression de recettes**.

- **Dossier technique :** `official/working/protocole-g0-15-ventilation-fiscale-et-incidence-v1.md`; ventilation impôts/cotisations/redevances, définition du revenu des personnes et des entreprises, protections RRQ/RQAP/FSS, mécanismes anti-paradis fiscaux et effets distributifs sur les ménages.
- **Registre JSON :** `data/matrice-preuves-g0-15-fiscalite.json`; quinze preuves toutes `A_DOCUMENTER`, aucune demande transmise, aucun rendement net ni taux chiffré.
- **Portes de validation :** budgets distincts Québec au Canada/Québec souverain, avis juridiques et financiers indépendants, maintien des services, droits sociaux et travailleurs.
- **Statut :** **G0.15 NON FRANCHIE**; préparation **47/100**, inchangée. Les textes de référence candidats et le manifeste `data/sources.json` sont conservés.
- **Étape suivante :** G0.16, microsimulation distributive et de soutenabilité **seulement après collecte et validation des assiettes**.

## G0.16 — Microsimulation distributive à données non calibrées (6 novembre 2026)

**Préparation : 47/100, inchangée; aucune réforme fiscalement certifiée.** La phase G0.16 crée une structure de calcul et de vérification, **pas** un résultat sur les ménages.

- **Protocole :** `official/working/protocole-g0-16-microsimulation-distributive-v1.md` (question économique, hypothèses, droits, populations, risques et preuves).
- **Plan JSON :** `data/plan-microsimulation-g0-16.json` : deux contextes juridiques distincts, dix déciles par contexte, 15 préconditions G0.15 et aucune valeur distributive imputée; tous les résultats inconnus sont `null`.
- **Contrôleur :** `assets/g16-incidence-core.mjs` : refuse faux résultats, transferts fédéraux souverains présumés, changements de score non justifiés, faux statuts de revue et doublons de déciles.
- **Tests Node :** `tests/g16-incidence.test.mjs`; le calcul facultatif est **synthétique et non réutilisable comme donnée politique**.
- **Étape suivante :** sources vérifiées et autorisées (G0.16b), puis microsimulation calibrée et audit externe (G0.16c), **uniquement si les portes de données, droits et fiscalité sont satisfaites**.
- **Contrôle documentaire complémentaire :** `assets/g016-microsimulation-gate-core.mjs` et `tests/g016-microsimulation-gate.test.mjs` vérifient les 15 preuves V01–V15 (actuellement 0/15), refusent les fausses certifications et ne peuvent jamais autoriser une simulation. Le score de 47/100 reste inchangé. La page publique `avancement-programme-nova.html#precontrole-g016` affiche ce verrou.
- **Statut :** G0.16 **NON FRANCHIE**, aucune adoption, aucun taux, aucun budget ou gain Nova établi. `official/reference/*` et `data/sources.json` restent inchangés.

**Feuille de route du programme complet :** `official/working/feuille-route-completude-47-100-nova-v1.md` distingue les **47 points documentés** et les **53 points manquants** selon les dix pondérations de G0.12. Aucun gain de points automatique, ni adoption présumée.

## G0.16b — Premiers repères officiels de revenu et de dépenses (7 novembre 2026)

**Avancement : 47/100 inchangé, G0.16 toujours NON FRANCHIE.** Une première transcription documentaire de deux sources historiques 2023 est enregistrée; **aucune microsimulation ni économie fiscale Nova n'est autorisée**.

- **ISQ / Enquête canadienne sur le revenu 2023 :** limites supérieures D1–D9 du **revenu après impôt ajusté selon la taille du ménage**, avec D10 non chiffré dans le tableau. Il s'agit de seuils de déciles, pas de revenus moyens, de revenus imposables ou de valeurs 2026.
- **Statistique Canada / Enquête sur les dépenses des ménages 2023 :** dépenses moyennes québécoises **65 344 $**, parts logement **27,1 %**, transport **16,9 %**, alimentation **17,3 %**. Ce ne sont pas des dépenses par décile et ces deux publications **ne sont pas appariables** à l'échelle des ménages.
- **Registre descriptif :** `data/reperes-publics-g0-16b-2023.json`, deux sources transcrites, deux catalogues à examiner, aucune donnée personnelle ni assiette fiscale calculée.
- **Rapport méthode / limites :** `official/working/rapport-g0-16b-reperes-publics-revenu-depenses-v1.md`.
- **Contrôles :** `assets/g016b-public-benchmarks-core.mjs` et `tests/g016b-public-benchmarks.test.mjs` empêchent les mutations des résultats, la confusion des millésimes et les affirmations prématurées de gains.
- **Suite :** obtenir des données de revenu imposable, de dépenses ventilées et de continuité des protections sociales, vérifier les quinze preuves V01–V15 et faire examiner la méthode par des spécialistes indépendants avant toute calibration.

Les quatre références candidates de `official/reference/*` et `data/sources.json` ne sont pas modifiées par cette recherche.

## G0.15 — Repérage des sources officielles (7 novembre 2026)

- **11/15 exigences** ont au moins une piste de source publique consignée, pour **15 candidatures de liens officiels** (dont certaines références réutilisées pour plusieurs exigences). Les quatre autres n'ont pas encore de piste enregistrée.
- **0/15 preuves validées** : une référence publique ne garantit ni ventilation complète, ni base d'imposition démontrée, ni revue indépendante.
- Registre `data/reperage-sources-officielles-g0-15-2026-11-07.json` : liens, périodes, limites et contrôle de provenance par V01–V15.
- Test `tests/g015-sources-officielles.test.mjs` : 15 identifiants, contrôle HTTPS et domaines publics attendus, rejet des certifications et rendements fiscaux fictifs.
- **Nouveaux candidats V04/V06/V13 :** source officielle des sociétés 2021 ajoutée après G0.16d; les trois pistes restent historiques, non auditées et non assimilées à des preuves validées.
- **Affichage public :** `avancement-programme-nova.html#sources-fiscales-g015` ; aucun gain du score de complétude sans dossier probant et réévaluation G0.12.

## G0.16c — Revenu imposable et incidence fiscale réellement déclarés (7 novembre 2026)

**Programme : 47/100, inchangé.** À la suite des repères sociaux de G0.16b, des **données fiscales provinciales observées pour 2023** sont transcrites directement depuis trois tableaux HTML du ministère des Finances du Québec.

- **Source A.7 :** revenu total déclaré **427 915 M$**, revenu net **387 023 M$**, revenu imposable **372 261 M$**, impôt sur le revenu imposable **62 148 M$**, crédits non remboursables appliqués **21 358 M$**, impôt à payer **40 790 M$**, crédits remboursables appliqués **9 305 M$** et impôt moins crédits remboursables **31 485 M$**. Arrondi de 1 M$ possible entre revenu net, déductions et revenu imposable. Taux moyen officiel 9,5 % = impôt à payer / revenu **total**.
- **Source tableau 4 :** **7 220 140** déclarants, dont **4 910 844 imposables** et **2 309 296 non imposables**.
- **Source A.3 :** cinq quintiles de **contribuables** classés par revenu total; le cinquième quintile porte **50,10 % du revenu** et **69,41 % de l'impôt à payer**. Ne pas confondre ces quintiles avec les dix déciles de **ménages** de l'ISQ.
- **Données :** `data/assiette-fiscale-particuliers-g0-16c-2023.json`.
- **Rapport de provenance, rapprochements et limites :** `official/working/rapport-g0-16c-assiette-declaree-particuliers-2023-v1.md`.
- **Contrôleur et tests :** `assets/g016c-tax-base-core.mjs` et `tests/g016c-tax-base.test.mjs` : résistent aux changements non sourcés de montants, dates, quintiles, taux et autorisations.

**Portée :** données historiques de déclarations 2023, **pas** revenus autonomes prévus en 2026–2027, pas assiette Nova, pas impôt fédéral ou des sociétés complet, pas revenus de lutte anti-paradis fiscaux. L'acquisition des sources et une contre-expertise restent nécessaires; l'existence d'une base historique améliore l'étude documentaire de V05, mais **les quinze preuves G0.15 demeurent non franchies**. Aucun taux Nova ni économie de dépense publique démontrés.

**Suite G0.16d :** obtenir ventilation des déductions/crédits, données fiscales des sociétés avec millésimes distincts, distributions de dépenses et effet sur les ménages; rapprocher les deux budgets à dix ans puis auditer indépendamment les hypothèses. Les fichiers candidats `official/reference/*` et `data/sources.json` ne sont pas modifiés.

## G0.16d — Première assiette observée des sociétés et séparation du FSS (7 novembre 2026)

**Programme : 47/100, inchangé.** La source publique du **ministère des Finances du Québec**, statistiques fiscales des sociétés de l'**année d'imposition 2021** (page actualisée le 7 octobre 2026), est transcrite, sans prétendre produire un taux Nova ou un budget financé.

- **Assiettes distinctes :** revenu imposable des sociétés au Québec **95 784 M$**; salaires soumis au FSS **155 850 M$**. La deuxième assiette n'est pas un profit imposable.
- **Prélèvements :** impôt sociétés **10 000 M$** + cotisations FSS **5 327 M$** = **15 327 M$**; crédits d'impôt **2 468 M$**, total net publié **12 860 M$** (différence d'arrondi de 1 M$).
- **Déclarations :** **564 599** sociétés, dont **542 249 petites**, **14 858 moyennes** et **7 492 grandes**; leurs prélèvements totalisent respectivement **4 095**, **2 560** et **8 672 M$**.
- **Registre :** `data/assiette-societes-g0-16d-2021.json`; contrôleur `assets/g016d-corporate-base-core.mjs`; tests `tests/g016d-corporate-base.test.mjs`.
- **Rapport détaillé :** `official/working/rapport-g0-16d-assiettes-et-prelevements-societes-2021-v1.md`.
- **Limites :** les sociétés 2021, les particuliers 2023 et les prévisions 2026–2027 sont de **périodes et populations différentes**; les données T2 fédérales de l'ARC ne contiennent pas l'impôt provincial des sociétés québécoises.
- **Preuves :** éclairage documentaire partiel sur **V04/V06/V13**, toujours **`A_DOCUMENTER`** dans le registre G0.15. **0/15 preuves entièrement validées indépendamment**, aucun nouveau taux, aucun coût de remplacement des cotisations ni financement souverain établi.

**Étape G0.16e :** actualiser la série fiscale des sociétés, vérifier pertes/crédits et assiettes légales, comptabiliser séparément les cotisations et services, harmoniser les dates et produire ensuite un dossier de soutenabilité à deux statuts constitutionnels. Les fichiers `official/reference/*` et `data/sources.json` restent inchangés.

## G0.16e — Pont financier multi-millésimes et soutenabilité à démontrer (7 novembre 2026)

**Programme : 47/100, inchangé; aucune nouvelle taxe chiffrée ni réforme certifiée.** L'étape G0.16e relie six montants hétérogènes en indiquant explicitement leur année, type (assiette, masse salariale, recette prévisionnelle), périmètre et source afin de **bloquer tout calcul de taux Nova à partir de chiffres incomparables**.

- **2021, sociétés :** revenu imposable québécois **95 784 M$** et salaires soumis au FSS **155 850 M$** (bases distinctes).
- **2023, particuliers :** revenu imposable déclaré **372 261 M$**; ne pas additionner avec les assiettes des sociétés de 2021.
- **2026–2027, prévisions gouvernementales :** impôt des particuliers **50 942 M$**, impôts des sociétés agrégés **14 698 M$**, cotisations santé **9 538 M$**; ce sont des **recettes prévues sous les lois existantes, non des assiettes fiscales**.
- **Budget gouvernemental 2026–2027 :** revenus **168 389 M$**, dépenses totales **171 597 M$**, provision pour éventualités **2 000 M$**, versements Fonds des générations **2 482 M$**, solde budgétaire **−7 690 M$**; **ce n'est pas un budget Nova**.
- **Stress arithmétique, pas prévision :** retrancher seulement FSS, foncier scolaire et consommation (**41 521 M$**) sans compensation porterait le solde figé à **−49 211 M$**. Aucun retrait de recettes n'est adopté ou réputé légal.
- **Continuité non démontrée :** RRQ, RQAP, FSS, médicaments, éducation, municipalités, travailleurs et dette ont des fiches de financement/avis juridiques encore **`null`**.
- **Deux trajectoires distinctes de dix ans (Canada et souveraineté) :** tous les bilans Nova sont **`null`**; les transferts fédéraux ne sont pas automatiquement maintenus dans le second scénario.
- **Registre :** `data/pont-financier-g0-16e-2021-2026.json`; **contrôleur :** `assets/g016e-financial-bridge-core.mjs`; **tests :** `tests/g016e-financial-bridge.test.mjs`; **rapport :** `official/working/rapport-g0-16e-pont-financier-et-viabilite-v1.md`.

**Décision :** G0.16e **non franchie**, **0/15 preuves fiscales validées indépendamment**, et **47/100** maintenu. Prochaine phase : harmoniser les millésimes, revoir assiettes/crédits/pertes, quantifier la continuité juridique et sociale et auditer séparément les deux budgets sur dix ans. `official/reference/*` et `data/sources.json` restent inchangés.

## G0.16f — Continuité financière des régimes sociaux et de la santé (7 novembre 2026)

**Programme 47/100, inchangé.** Les données publiques du RRQ, du RQAP, de la RAMQ et du financement général de la santé ajoutent des précisions aux risques de la réforme fiscale envisagée, **sans démontrer qu'une substitution des cotisations serait viable**.

- **RRQ 2026 :** exemption 3 500 $, MGA 74 600 $, MSGA 85 000 $; cotisations **6,3 % salarié + 6,3 % employeur** sur la première tranche et **4 % + 4 %** sur la tranche supplémentaire. Le résumé de l'évaluation actuarielle spéciale indique une marge financière du régime de base réduite à **0,12 point**; aucune réforme Nova n'est évaluée actuariellement.
- **RQAP 2026 :** cotisations **0,430 % salariés**, **0,602 % employeurs**, **0,764 % autonomes**; financement par un **fonds fiduciaire non budgétaire**. Les responsabilités du Conseil de gestion ont été transférées à **Retraite Québec le 1er mai 2026**.
- **RAMQ 2024–2025 :** financement publié **14 542 M$**, dont **8 937 M$ FSS**, **4 354 M$ Fonds d'assurance médicaments**, **1 250 M$ autres** (écart d'arrondi 1 M$); coûts de programmes **14 232 M$**. Ces postes ne décrivent pas l'ensemble du réseau ni un surplus disponible.
- **Système de santé 2024 :** environ **81 G$** de dépenses totales dont environ **59 G$** publiques, périmètre plus large à **ne pas additionner** directement à la RAMQ. Les 8 937 M$ de financement RAMQ FSS 2024–2025 ne sont pas les 9 538 M$ de cotisations santé prévues dans les finances gouvernementales 2026–2027.
- **Registre :** `data/continuite-regimes-g0-16f-2024-2026.json`; **contrôleur :** `assets/g016f-social-continuity-core.mjs`; **tests :** `tests/g016f-social-continuity.test.mjs`; **rapport :** `official/working/rapport-g0-16f-protection-regimes-et-sante-v1.md`.
- **Décision :** V07–V09 restent **`A_DOCUMENTER`**, les coûts de remplacement et avis juridiques sont inconnus, **0/15 preuves G0.15 validées indépendamment**, aucune abolition des cotisations ni nouvel impôt approuvés. G0.16f **NON FRANCHIE**.

**Étape suivante :** consolider les comptes des fonds sociaux et coûts de santé (2024–2026), puis documenter éducation et fiscalité municipale (V10) et soumettre un scénario de continuité à revue juridique, actuarielle et financière indépendante avant de toucher aux prélèvements.

Les fichiers de référence candidats `official/reference/*` et `data/sources.json` ne sont pas modifiés.

## G0.16g — Protection des écoles, municipalités, travailleurs et dette (7 novembre 2026)

**Évaluation de préparation du programme : 47/100, sans changement.** À la suite des chantiers G0.16e/f, ce dossier réunit des sources financières et juridiques sur les **écoles, les municipalités, la main-d'œuvre et le service de la dette**, pour éviter qu'une réforme fiscale à « deux prélèvements » reporte ses coûts sur les citoyens, salariés et municipalités.

- **Taxe scolaire :** le rapport préélectoral d'août 2026, rapproché dans G0.14, prévoit **1 301 M$ en 2026–2027**. Cette recette **n'est ni un impôt foncier municipal ni le budget total de l'éducation**; aucun financement de remplacement Nova n'est démontré.
- **Municipalités :** les séries MAMH/Données Québec et la [ressource CSV agrégée 2024 pour tout le Québec](https://www.donneesquebec.ca/recherche/dataset/profil-financier-des-municipalites-locales/resource/5dec077d-4ef9-4e22-99e9-0c4f3a6dd52d) sont identifiées, mais le CSV n'a **pas été importé ni consolidé**. L'UMQ évoque **70 % de revenus municipaux provenant de la taxe foncière**; c'est une affirmation de l'association, non une mesure de financement Nova auditée. **Aucun montant fiscal municipal global n'est ajouté ou inventé**.
- **Droits et travail :** continuité à documenter pour les enseignants, employés des services publics, conventions collectives, pensions, eau, voirie, sécurité incendie et services locaux, sans économies de main-d'œuvre fictives.
- **Dette :** les dépenses gouvernementales de service de dette **2026–2027 sont de 10 516 M$** (G0.14) et le ratio officiel de dette nette au 31 mars 2026 est de **38,1 % du PIB**. Ce sont des mesures distinctes; le service est déjà dans les dépenses du gouvernement, donc **aucun double comptage**.
- **Compétences :** la Loi constitutionnelle de 1867, notamment 92(2), 92(3), 92(8) et 93, impose de distinguer l'administration provinciale, la fiscalité locale et les obligations scolaires; la souveraineté exige un compte séparé de dette et de fonctions héritées.
- **Livrables vérifiables :** `data/continuite-territoriale-g0-16g-education-municipalites-dette.json` (11 sources, 9 obligations et 2 scénarios), `assets/g016g-territorial-continuity-core.mjs` (contrôles fail-closed), `tests/g016g-territorial-continuity.test.mjs` (**42 cas déclarés et rejoués en JavaScript isolé**) et `official/working/rapport-g0-16g-financement-ecoles-villes-emploi-dette-v1.md` (rapport et plan de travaux).
- **Limites :** G0.15 V10, V14 et V15 restent à documenter; aucune révision juridique ou budgétaire indépendante, aucun taux de taxe proposé, et **G0.16g non franchie**. Les 42 cas ont été rejoués dans un environnement JavaScript compatible avec les assertions Node, **pas dans un CI GitHub Actions attesté**.

**Suite logique :** extraire et rapprocher les profils financiers municipaux 2024–2025, établir les crédits/obligations scolaires, chiffrer les droits des salariés et les échéances de dette pour chaque statut du Québec et faire auditer deux budgets décennaux. Aucune loi ni référence candidate `official/reference/*` n'est modifiée.

## G0.16h — Recettes fiscales municipales réellement observées en 2024 (7 novembre 2026)

**Préparation du programme : 47/100 inchangé.** G0.16h ajoute, pour la première fois dans le dossier, une **sommation chiffrée officielle des comptes municipaux de 2024**, lue et vérifiée directement dans les pages **S7 / 3** et **S27 / 35** du [rapport MAMH 2024](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/rapports_financiers_organismes_municipaux/2024/RAP_financier_2024_sommation_municipalites_locales.pdf).

- **Sommation partielle de 1 056 municipalités locales, au 17 mars 2026** : certaines municipalités et collectivités sont absentes; la section de ventilation des taxes est marquée **« Non audité »**. Cette source n'est **pas exhaustive** de tous les organismes municipaux.
- **Recettes fiscales locales 2024 :** **17 188 134 046 $**, dont **14 970 167 302 $** de taxes sur la valeur foncière, **2 199 032 000 $** de taxes/compensations/tarifications sur une autre base et **18 934 744 $** de taxes d'affaires; les trois chiffres se réconcilient exactement.
- **Comptes consolidés observés :** **32 109 026 468 $ de recettes**, **28 366 959 822 $ de charges** et **3 742 066 646 $ d'excédent lié aux activités**. Les transferts et frais de financement sont déjà compris dans les totaux : aucun double comptage.
- **Rapports de parts dérivées (pas des pourcentages publiés par le MAMH) :** foncier = **87,10 % de toutes les taxes municipales** ou **46,62 % de toutes les recettes**; toutes les taxes = **53,53 % des recettes**. Ces définitions **diffèrent** du cadrage de l'UMQ selon lequel la taxe foncière contribue à 70 % des revenus municipaux.
- **Données 2023 :** la même sommation contient les chiffres comparatifs; l'évolution calculée des taxes de **2023 à 2024 est de 6,88 %**, sans attribuer cette variation à une cause politique ou présumer un périmètre annuel constant.
- **Attention :** taxe foncière **municipale de 2024** ≠ taxe **scolaire provinciale prévue 2026–2027 (1 301 M$)**. Ni l'une ni l'autre n'est un budget Nova. Le fichier antérieurement répertorié `PF-2024-2024-Prov.csv` contient des **indicateurs/ratios**, pas cette ventilation monétaire; il n'a pas été importé comme preuve.
- **Livrables :** `data/finances-municipales-g0-16h-2024.json`, `assets/g016h-municipal-finance-core.mjs`, `tests/g016h-municipal-finance.test.mjs` (**32 cas, 32 réussis en rejeu V8 isolé, et non CI Node certifié**) et `official/working/rapport-g0-16h-finances-municipales-observees-2024-v1.md`.
- **Décision :** recettes de référence désormais chiffrées, **mais compensation fiscale municipale 2026, financement des services et impacts sur les personnes restent inconnus**; G0.16h n'homologue aucune réforme ni aucun taux d'impôt. V10/V14/V15 G0.15 restent à documenter.

**Suite G0.16i :** obtenir les fichiers comptables municipaux détaillés, harmoniser 2024–2026, intégrer les transferts inter-administrations et calculer avec un auditeur les besoins de compensation pour chacun des deux statuts constitutionnels. Les références candidates `official/reference/*` et `data/sources.json` ne sont pas modifiées.

## G0.16i — Stress historique des taxes municipales et continuité des services (7 novembre 2026)

**Programme : 47/100, inchangé.** La suite G0.16i utilise la sommation 2024 du MAMH, issue de G0.16h (**1 056 municipalités locales, couverture non exhaustive, détails fiscaux marqués non audités**), pour calculer quatre scénarios **purement arithmétiques, sans politique adoptée ni prévision 2026**.

| Sensibilité sur les comptes **2024** à dépenses et autres revenus gelés | Taxes hypothétiquement retirées | Solde comptable mécanique |
| --- | ---: | ---: |
| Aucun retrait (référence enregistrée) | 0,000 G$ | **+3,742 G$** |
| Taxes foncières générales seules | 13,215 G$ | **−9,473 G$** |
| Toutes taxes sur valeur foncière | 14,970 G$ | **−11,228 G$** |
| Toutes taxes municipales | 17,188 G$ | **−13,446 G$** |

- **Ne jamais additionner les scénarios :** taxes générales ⊂ taxes sur valeur foncière ⊂ toutes taxes municipales. Les recettes de remplacement sont **inconnues**. Aucun solde du tableau n'est un **déficit prévisionnel Nova**.
- **L'excédent 2024 de 3,742 G$ est comptable**, pas une réserve de liquidités ou des économies disponibles; les transferts internes et frais financiers sont déjà dans les comptes.
- **Nouveau contrôle des années :** le [catalogue MAMH des profils municipaux](https://www.donneesquebec.ca/recherche/dataset/profil-financier-des-municipalites-locales), actualisé le **5 novembre 2026**, distingue les comptes **2024** et les données **2025 d'évaluation foncière**; ces dernières ne représentent **pas** des recettes fiscales 2025. Aucun budget 2025 n'est fabriqué.
- **Continuité obligatoire :** sept catégories de services et droits (eau, voirie, sécurité, transports, aménagement, emplois/pensions, dette) ont des coûts et financements de remplacement **`null`**. Les **deux scénarios décennaux** 2026–2036 comportent **20 années sans bilan Nova chiffré**.
- **Livrables GitHub :** `data/risque-transition-taxes-locales-g0-16i-2024.json`, `assets/g016i-local-tax-stress-core.mjs`, `tests/g016i-local-tax-stress.test.mjs` (**38/38 tests réussis en rejeu isolé V8, non certifiés dans GitHub Actions**) et `official/working/rapport-g0-16i-soutenabilite-taxes-municipales-v1.md`.
- **Décision :** G0.16i documente les risques arithmétiques d'un changement fiscal, mais **n'homologue pas une loi, un taux, une économie ou un financement de remplacement**. La revue juridique, la réconciliation par municipalité et le budget indépendant restent à faire; **47/100 inchangé**.

**Suite logique G0.16j :** rapprocher les municipalités/organismes manquants, mesurer le coût réel et la continuité de chaque service, vérifier les transferts internes et bâtir des budgets à dix ans distincts pour Québec dans le Canada et Québec souverain. Les documents normatifs candidats `official/reference/*` restent inchangés.

## G0.16j — Dépenses municipales 2024 : eau, routes, incendie et autres services

**Préparation du programme : 47/100, inchangée (53 points à obtenir).** G0.16j poursuit l'analyse G0.16h/i avec les **dépenses réellement enregistrées**, à partir des pages **S7 p. 3 et S28 p. 47–48** du [rapport consolidé MAMH 2024](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/rapports_financiers_organismes_municipaux/2024/RAP_financier_2024_sommation_municipalites_locales.pdf).

- **Dépenses consolidées enregistrées en 2024 : 28 366 959 822 $** dans 1 056 municipalités incluses, comparées à **26 469 048 805 $ en 2023**. Le total est rapproché exactement au moyen de **10 catégories comptables**.
- **Eau potable, eaux usées et égouts : 2 519 426 792 $** en 2024; **voirie et déneigement : 3 711 874 237 $**; **sécurité incendie : 1 533 111 877 $**. Ces montants sont des **sous-postes inclus dans les dépenses existantes**, et ne s'y ajoutent jamais. Les **34 postes détaillés** ont été rapprochés des fonctions correspondantes dans les deux exercices.
- **Source et portée :** les pages de détail **S28 indiquent « Non audité »**; la sommation de 1 056 municipalités n'est pas exhaustive, et un inventaire des MRC/régies, des régions et des transferts internes est requis. **2024 ≠ financement garanti de 2026–2036.**
- **Cohérence budgétaire :** les **frais de financement de 1 332 060 734 $** sont déjà dans le total des dépenses. Le stress fiscal 2024 de G0.16i est une simple soustraction arithmétique; aucune dépense des services ne peut être présentée comme une économie automatique lorsqu'une recette fiscale est retirée.
- **Livrables :** `data/ventilation-charges-municipales-g0-16j-2024.json` (10 fonctions, 34 lignes, 2 exercices et 20 années de budgets futurs non renseignées), `assets/g016j-municipal-services-core.mjs`, `tests/g016j-municipal-services.test.mjs` (**38 tests réussis sur 38 lors d'un rejeu V8 isolé, sans attestation GitHub Actions**) et `official/working/rapport-g0-16j-services-municipaux-charges-observees-2024-v1.md`.
- **Verdict :** données historiques des fonctions municipales désormais vérifiables, **mais garanties financières, répartition locale, effets sur les travailleurs, projections de recettes et avis indépendants encore absents**. Aucun prélèvement supprimé ni loi adoptée; **G0.16j non franchie comme porte de viabilité financière**.

**Suite logique G0.16k :** construire un référentiel de continuité par fonction et municipalité, rapprocher la main-d'œuvre, les actifs, les financements et les échéances sur dix ans, puis obtenir les avis juridique et financier indépendants. Le score **47/100** n'augmente pas avec la rédaction de fichiers.

## G0.16k — Réseaux d'eau : état des actifs, incertitude et financement à établir (7 novembre 2026)

**Préparation globale du programme : 47/100, 53 points manquants.** G0.16k étend G0.16j avec les conclusions du [Portrait des infrastructures en eau des municipalités du Québec — 2025 (CERIU, soutien du MAMH)](https://ceriu.qc.ca/system/files/2026-03/Portrait_infrastructures_eau_municipalites_Quebec-2025.pdf), après contrôle visuel de son sommaire exécutif.

- **Patrimoine d'eau estimé : 197,6 G$ de valeur de remplacement (2025)** pour **101 105 km de conduites et 10 659 ouvrages** : stock de reconstruction théorique, **pas une dépense annuelle ni un plan de travaux Nova**. La valeur comprend généralement la remise à niveau de la chaussée à la largeur de la tranchée.
- **État des actifs :** 67 % en bon/très bon état, 23 % acceptable et 10 % mauvais/très mauvais. Les classes D/E valent **20,6 G$ à remplacer intégralement au prix de 2025**, mais **des réparations moins coûteuses peuvent être appropriées** : ne pas transformer les 20,6 G$ en budget immédiatement requis.
- **Qualité de la donnée :** environ **75 % de la valeur (147,9 G$)** repose sur l'âge ou l'appréciation d'acteurs municipaux, et non sur une mesure de terrain. Le CERIU s'appuie sur **938 municipalités ayant transmis des données depuis 2014**, dont **666 ont actualisé leurs données en 2025**, avec extrapolations. Ce périmètre **diffère des 1 056 municipalités** des comptes MAMH 2024.
- **Dépenses annuelles à ne pas ajouter au patrimoine :** **2 519 426 792 $** d'eau, égouts et eaux usées observés **en 2024** dans G0.16j; ni le montant 2024 ni la valeur du patrimoine 2025 ne mesurent, à eux seuls, le besoin de rénovation 2026–2036.
- **PGA-Eau :** le [gouvernement invite les municipalités à s'engager dans la démarche d'ici le **31 décembre 2026**](https://www.quebec.ca/habitation-territoire/infrastructures-municipales/plan-gestion-actif-pga/eau). **Engagement ≠ plan complet adopté**, et l'ouverture de futurs financements ne peut être présumée.
- **Livrables :** `data/continuite-actifs-eau-g0-16k-2025.json` (cinq types d'actifs, sept risques, six preuves manquantes et deux cadres décennaux sans recettes fictives), `assets/g016k-water-assets-core.mjs`, `tests/g016k-water-assets-continuity.test.mjs` (**37/37 tests réussis en rejeu isolé V8, non certifiés sur GitHub Actions**) et `official/working/rapport-g0-16k-actifs-eau-financement-continuite-v1.md`.
- **Verdict :** preuve des risques de continuité améliorée, mais coûts d'entretien, recettes de remplacement, obligations des employés et budgets sur dix ans **non chiffrés ni audités indépendamment**. Aucune réforme fiscale ni loi adoptée; **47/100 inchangé**.

**Suite G0.16l :** recenser les plans PGA-Eau effectivement déposés et les inspections, rapprocher actifs/échéances/dépenses/financements par collectivité, puis faire vérifier un programme décennal de réhabilitation compatible avec la protection des salariés et le pouvoir d'achat des ménages. Les fichiers candidats `official/reference/*` ne sont pas modifiés.

## G0.16l — Aides à l'eau : PGA-Eau, PRIMEAU et TECQ (7 novembre 2026)

**Préparation globale : 47/100, 53 points manquants.** Après le patrimoine G0.16k, cette phase documente **les conditions réelles de financement**, pour ne pas assimiler les enveloppes publiques annoncées à de l'argent attribué à une municipalité ou au Projet Nova.

- **PGA-Eau :** [MAMH — préparer un plan](https://www.quebec.ca/habitation-territoire/infrastructures-municipales/plan-gestion-actif-pga/eau) : engagement initial **invité pour le 31 décembre 2026**, comprenant une résolution et une transmission; ce n'est **pas** un PGA complet. Suivi annuel prévu dès 2028, actualisation du plan dès 2030.
- **PRIMEAU 2023–2033 :** [programme MAMH](https://www.quebec.ca/habitation-territoire/infrastructures-municipales/programmes/eau-potable-eaux-usees/programme-infrastructures-municipales-eau-primeau) : **2,4 G$ d'enveloppe annoncée**, appel du **31 août au 30 octobre 2026 clos** (volet 1, priorités 1 à 4), volet 2 fermé aux nouvelles demandes; sélection soumise aux critères, à l'avancement et aux fonds disponibles.
- **TECQ 2024–2028 :** [programme MAMH](https://www.quebec.ca/habitation-territoire/infrastructures-municipales/programmes/eau-potable-eaux-usees/programme-transfert-infrastructures-eau-collectives-quebec-tecq-2024-2028) : **plus de 3,3 G$ annoncés sur cinq ans**, contributions Canada + Québec, sous conditions. Mise à jour annuelle de la programmation entre **le 1er octobre et le 15 février**, résolution et approbation requises.
- **Financement :** une **enveloppe ≠ admissibilité ≠ demande déposée ≠ aide promise ≠ paiement constaté**. Aucune de ces enveloppes n'est un revenu Nova et les financements fédéraux ne sont pas automatiquement transposables au scénario souverain.
- **Livrables :** `data/financement-eau-g0-16l-pga-primeau-tecq-2026.json` (9 étapes, 2 programmes, 2 budgets distincts de 10 ans **non chiffrés**, aucun projet local fictif), `assets/g016l-water-funding-core.mjs` (contrôle des règles et calculs **synthétiques seulement**), `tests/g016l-water-funding.test.mjs` (**40 tests réussis en rejeu JavaScript isolé, CI Node non attestée**) et `official/working/protocole-g0-16l-eau-financement-preuves-pga-primeau-tecq-v1.md`.
- **Décision :** mécanismes existants mieux documentés, mais **zéro attribution municipale spécifique vérifiée**, aucun plan PGA-Eau local homologué et aucun financement de rénovation à dix ans validé. **G0.16l non franchie comme porte de viabilité financière; score toujours 47/100**.

**Suite G0.16m :** collecter des projets municipaux réellement documentés, rapports d'inspection, décisions de subventions, coûts et échéanciers, puis consolider un programme de maintien des services auditable sans prélèvement caché.

## G0.16m — Premier financement municipal réel vérifié : Warwick (7 novembre 2026)

**Programme : 47/100, 53 points manquants.** Contrairement aux seules enveloppes théoriques répertoriées en G0.16l, cette étape examine un projet municipal réel : la **nouvelle usine d'eau potable Gérard-Laroche à Warwick**. **Il ne s'agit pas d'un projet Nova**, mais d'une étude de cas sur les preuves à exiger avant toute réforme fiscale.

- **Aide confirmée :** le gouvernement du Québec a accordé **14 668 901 $** de PRIMEAU à Warwick en 2025 pour une assiette maximale admissible de **15 440 948 $**, [confirmée dans une liste ministérielle](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/demande_acces/2025/DAI_2025-082_subventions_primeau_2023_2033.pdf) et une [annonce officielle](https://www.quebec.ca/nouvelles/actualites/details/le-gouvernement-du-quebec-accorde-plus-de-146-m-a-warwick-63958). **Aide accordée ≠ subvention effectivement versée**, non attestée dans cette étude.
- **Ligne du [PTI 2026–2028 de Warwick](https://villedewarwick.quebec/wp-content/uploads/2025/12/Programme-triennal-des-immobilisations-2026-2027-2028.pdf) : 20 074 664 $** pour la construction programmée en 2026, répartis exactement en **14 668 901 $ PRIMEAU + 336 823 $ fonds d'eau + 5 068 940 $ emprunt inscrit**. C'est une programmation annuelle, **pas** le coût global certifié du projet.
- **[Règlement 404-2025](https://villedewarwick.quebec/wp-content/uploads/2025/03/R404-2025-Emprunt-usine-eau-potable-et-filiere-traitement-version-finale.pdf) : 27 988 101 $** de dépenses et un emprunt brut décrétés pour la construction **et des équipements**; le règlement mentionne une **taxe spéciale sur les immeubles desservis par l'aqueduc**. **Ne pas additionner les budgets 2025 et 2026**, ni assimiler l'autorisation d'emprunt à une dette effectivement tirée.
- **Engagements ministériels :** **9 779 266 $** pour 2025–2026 et **4 889 635 $** pour 2026–2027, totalisant les **14 668 901 $** promis, [dans la liste officielle](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2025/LIS_engagements_juin_2025.pdf). Ce calendrier d'engagements **ne démontre pas les paiements de trésorerie**.
- **Livrables :** `data/cas-municipal-reel-g0-16m-warwick-eau-2025-2026.json` (sept sources publiques, une étude de cas, six preuves encore manquantes), `assets/g016m-real-municipal-case-core.mjs`, `tests/g016m-real-municipal-case.test.mjs` (**39 tests réussis en rejeu V8 isolé, pas de certification CI Node**) et `official/working/rapport-g0-16m-premier-cas-municipal-reel-warwick-v1.md`.
- **Limites :** versements PRIMEAU, dette résiduelle, coût final, maintien du service, effets sur les ménages et statut du chantier au 7 novembre 2026 **non vérifiés**; les PDF municipaux ont été consultés en texte public sans contrôle visuel indépendant complet. **Aucune recette n'a été attribuée à Nova** et aucun taux d'impôt n'est proposé.

**Suite G0.16n :** comparer d'autres cas municipaux publics de régions et de tailles différentes, puis obtenir dépenses finales, versements, financement réellement tiré, état des ouvrages et impact sur les citoyens avant d'auditer la fiscalité à deux prélèvements. **Score 47/100 inchangé.**

## G0.16n — Sept projets PRIMEAU de sept régions, second dossier local de taxation (7 novembre 2026)

**Préparation globale : 47/100 inchangé.** Après Warwick en G0.16m, l'étape G0.16n établit une comparaison **raisonnée et non représentative** de **sept projets de sept régions**, sur les **pages 4–5 de la [liste officielle MAMH PRIMEAU du 8 octobre 2025](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/demande_acces/2025/DAI_2025-082_subventions_primeau_2023_2033.pdf)**, inspectées visuellement.

- **Portefeuille sélectionné :** maxima admissibles **188 322 869 $**; aides inscrites **156 721 180 $**; différence arithmétique **31 601 689 $**, **qui ne mesure pas les coûts locaux finaux ni la charge des citoyens**. Warwick n'est compté qu'une fois. Les communes sont Warwick, Gatineau, Laval, Port-Daniel–Gascons, L'Île-d'Anticosti, Val-d'Or et La Doré.
- **Règle de preuve :** le *maximum admissible* du ministère n'est pas le coût total du chantier; l'aide inscrite n'est **pas un versement**; les dates prévisionnelles de la liste de 2025 ne prouvent pas l'achèvement en novembre 2026. L'échantillon n'est **pas représentatif des municipalités du Québec**.
- **Second dossier financier municipal :** le [conseil de Port-Daniel–Gascons, procès-verbal du 9 juin 2025](https://munpdg.ca/wp-content/uploads/2025/07/proces-verbal-de-la-seance-ordinaire-du-9-juin.pdf), règlement **2025-01**, décrit une dépense estimée de **56 596 000 $** financée dans le règlement par **42 302 472 $ PRIMEAU + 14 293 528 $ d'emprunt autorisé sur 40 ans**. Le règlement prévoit une taxation spéciale générale sur une portion de l'emprunt et des compensations par secteur desservi; **ni les montants annuels par ménage ni l'encours réel de dette ne sont vérifiés**.
- **Limites :** le PDF du conseil a pu être lu en texte public, mais sa capture visuelle a échoué; la confirmation ministérielle et la somme du règlement ne remplacent pas le grand livre ni un audit indépendant. **Ne pas additionner le coût du règlement au maximum admissible** : unités, dates et périmètres différents.
- **Livrables :** `data/comparatif-cas-reels-primeau-g0-16n-2025.json`, `assets/g016n-multiregion-primeau-core.mjs`, `tests/g016n-multiregion-primeau.test.mjs` (**43 tests réussis en rejeu JavaScript V8 isolé; CI Node non certifiée**) et `official/working/rapport-g0-16n-comparatif-regional-primeau-port-daniel-v1.md`.
- **Décision :** deux dossiers de financement local (Warwick et Port-Daniel), sept aides localisées vérifiables, **zéro versement réel audité dans cet échantillon**, aucun budget à deux taxes certifié. **Score 47/100 inchangé.**

**Suite G0.16o :** rechercher versements effectifs, dépenses finales, encours de dette et taux de taxation locale; relier les protections des travailleurs et la continuité de l'eau à deux budgets décennaux audités. Les textes candidats `official/reference/*` restent inchangés.

## G0.16o — Vrais taux municipaux 2026 et exigences de preuve des versements (7 novembre 2026)

**Préparation du programme : 47/100, 53 points non démontrés.** Après sept cas d'aides PRIMEAU G0.16n, ce chantier examine pour la première fois la fiscalité **effectivement réglementée en 2026** dans l'une des municipalités étudiées, **Warwick**, ainsi que les règles de réclamation de subvention.

- **Règlement municipal [415-2025 — Exercice 2026](https://villedewarwick.quebec/wp-content/uploads/2026/02/R415-2025-Taux-de-taxes-et-compensations-2026.pdf), en vigueur depuis le 14 janvier 2026 :** taux foncier résidentiel de base **0,575 $ par 100 $ d'évaluation** (pas de revenu); taxes spéciales liées à la sécurité incendie, aux routes, aux emprunts, aux réseaux et à l'assainissement **selon la catégorie de propriété et le secteur desservi**.
- **Compensations de services publiées :** **102 $ d'aqueduc** et **31,25 $ d'égout par logement** concerné; collecte de matières résiduelles **283 $ en zone urbaine** ou **267 $ en zone rurale**. Les montants appartiennent aux tarifs réglementaires et non aux paiements déjà encaissés par la Ville.
- **Exemple strictement fictif et incomplet :** propriété résidentielle d'une unité évaluée **300 000 $**, avec service d'eau, égout et collecte urbaine : **1 912,20 $** pour le taux général et cinq taux spéciaux universels, plus **416,25 $** de compensations sélectionnées, soit un **sous-total de 2 328,45 $**. Les taxes sectorielles, les autres règlements et les éventuelles obligations du projet 404-2025 **ne sont pas inclus**. **Ne jamais citer 2 328,45 $ comme une vraie facture, la facture totale ou un gain Nova.**
- **Règlement d'emprunt de la nouvelle usine 404-2025 :** non mentionné explicitement parmi les taux du règlement annuel de taxation consulté; **ce silence ne prouve pas l'absence de charge future ou la suppression d'une taxe**. Le taux propre au projet est inconnu.
- **[Guide officiel PRIMEAU 2023–2033 d'août 2026](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/infrastructures/primeau/GUI_primeau_aout_2026.pdf) :** réclamations partielles **jusqu'à 90 % de l'aide potentiellement versable**, analyse des dépenses et preuves de paiement avant approbation finale, éventuelles retenues sur certains dossiers. **Plafond de réclamation ≠ paiement avéré.** Les conventions plus anciennes (p. ex. Warwick 2025) doivent être examinées individuellement.
- **Sources et contrôles :** `data/taxes-warwick-2026-et-preuves-versements-g0-16o.json`, `assets/g016o-warwick-tax-core.mjs`, `tests/g016o-warwick-tax-and-grants.test.mjs` (**39 tests initiaux réussis en rejeu V8 isolé, sans certification CI GitHub**) et `official/working/rapport-g0-16o-taxation-warwick-2026-et-preuves-versements-v1.md`. Les PDF municipaux et le guide ont été lus en texte; les captures visuelles n'ont pas pu être validées.
- **Verdict :** les règles fiscales locales 2026 sont sourcées, **mais aucune facture citoyenne réelle ni aucun virement PRIMEAU individualisé n'est vérifié**, et les deux budgets décennaux demeurent sans recette de remplacement. **G0.16o ne franchit pas la porte de viabilité; score toujours 47/100.**

**Suite G0.16p :** étendre à d'autres municipalités et à leurs taux de taxation 2026, recouper les prêts réellement décaissés, réclamations et paiements de subventions, puis établir les effets sur les ménages et les services à l'aide de données vérifiées avant toute proposition de taux Nova.

## Validation externe requise
Le caractère « document de référence » ne remplace jamais les validations juridique, financière, électorale, cybersécurité ou accessibilité requises.

## Traçabilité
Les anciennes versions retirées du site actif restent conservées dans l’historique Git. Elles servent à retracer l’évolution du projet, mais ne sont pas des sources publiques prioritaires.
