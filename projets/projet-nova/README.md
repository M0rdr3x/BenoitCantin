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

## G0.3 — Portrait régional de l'accès aux soins (3 novembre 2026)

- Page publique proposée : `portrait-regional-g0-sante.html`.
- Registre structuré : `data/portrait-regional-g0-sante-2025.json` (18 régions sociosanitaires, 16 incluses dans l'EQUSSSS 2025, 2 exclues, 6 différences relatives rapportées par l'ISQ, **0 taux régional numérique importé**).
- Méthode et contrôle de provenance : `official/working/protocole-portrait-regional-sante-g0-v1.md`.
- Contrôles automatisables : `tests/portrait-regional-g0-sante.test.mjs`, exécutables avec les autres tests Nova–Sinjira et déclarés au workflow GitHub Actions.
- Sources : communiqué et faits saillants de l'ISQ du **2 novembre 2026**; découpage officiel des **18 régions sociosanitaires** du Québec, distinct des régions administratives.
- Le fichier XLSX régional de l'ISQ est référencé et téléchargeable en principe, mais **il n'a pas pu être téléchargé ni analysé ici**. Les pourcentages exacts, tailles d'échantillon et incertitudes par RSS demeurent `null` dans le registre; aucune comparaison de coût ou choix de région pilote n'en découle.
- Les RSS **17 (Nunavik)** et **18 (Terres-Cries-de-la-Baie-James)** sont hors champ de l'enquête, **pas hors champ des obligations de santé publique et d'équité**.
- Ce dossier constitue une étude partielle **non normative**; la porte G0 reste **non franchie**. Aucune modification des quatre références candidates du manifeste officiel.

## Validation externe requise
Le caractère « document de référence » ne remplace jamais les validations juridique, financière, électorale, cybersécurité ou accessibilité requises.

## Traçabilité
Les anciennes versions retirées du site actif restent conservées dans l’historique Git. Elles servent à retracer l’évolution du projet, mais ne sont pas des sources publiques prioritaires.
