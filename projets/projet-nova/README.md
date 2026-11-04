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

## Validation externe requise
Le caractère « document de référence » ne remplace jamais les validations juridique, financière, électorale, cybersécurité ou accessibilité requises.

## Traçabilité
Les anciennes versions retirées du site actif restent conservées dans l’historique Git. Elles servent à retracer l’évolution du projet, mais ne sont pas des sources publiques prioritaires.
