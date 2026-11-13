# Boussole électorale Nova — Contrôle de séparation entre relecture IA et attestation indépendante

**9 novembre 2026 — Rapport de revue de sources du dépôt, sans certifier le contenu des URL externes.**

## Résultat déterminant

L'inventaire historique contient **64 questions**, **16 dimensions**, **22 formations ou entrées historiques dont un projet futur**, et **140 fiches documentaires candidates**. Les **140 fiches portent actuellement `finalizable:true` et `secondIndependentReview.status="completed"`**, mais leurs `secondIndependentReview.reviewer` sont **tous attribués à ChatGPT**, sous diverses formulations.

Cette information documente un **travail de deuxième lecture automatisée**, pas un **avis humain contradictoire indépendant et signé**. Le nom historique du champ `secondIndependentReview` est trompeur lorsqu'il est utilisé comme un tampon d'indépendance. Les fiches sont donc **pré-codées**, et non reçues comme positions définitivement attestées par un expert externe.

**État des preuves observées dans ces corpus : 140 deuxièmes lectures IA consignées, 0 attestation humaine indépendante exploitable par ce contrôle.** Le zéro est le résultat du manque de **pièces d'attestation externe dans ce corpus**, et ne constitue pas une affirmation selon laquelle aucun humain n'a jamais relu quoi que ce soit ailleurs.

## Conséquence pour la boussole et les partis

Le registre `data/boussole-partis-2026.json` garde **`comparisonEligible:false` pour les 22 entrées**, et **`positions:{ }`** pour chacune. Aucune recommandation électorale, aucun classement global, aucune similitude parti–citoyen et aucun affichage de comparaison partis ne sont permis par cette correction.

Le changement de l'écran public `assets/boussole-electorale.js` n'altère **aucune des 140 opinions provisoires** : il remplace les étiquettes « fiches finalisées » par « fiches pré-codées », distingue la **relecture par IA** de l'**attestation humaine indépendante** et rappelle la désactivation de la comparaison des formations. Ce changement est **en PR** et n'est pas déclaré déjà déployé.

Une URL commençant par `https://` n'est pas la preuve que la page existe encore, qu'elle contient la citation alléguée ni qu'elle établit la position exacte du parti pour la formulation donnée. Les dates `checkedAt` sont historiques : un contrôle automatisé de structure de liens **ne vaut pas nouvelle vérification factuelle des pages en novembre 2026**.

## Critères de réception pour `COMPASS_DOCUMENTARY_VALIDATION`

1. **Référentiel démocratique** : reprendre la liste et le statut légal de chaque formation avec des sources contemporaines d'Élections Québec; conserver séparément les partis retirés et les futurs projets non autorisés. Les comptes et les noms du registre d'octobre 2026 demeurent des **photographies datées**, non une attestation de statut légal au 9 novembre.
2. **Lecture primaire** : pour chaque couple question–formation qu'on voudrait finaliser, vérifier la page, le document ou la déclaration primaire, ses auteurs, dates, extraits pertinents, contexte, traduction éventuelle et historique des mises à jour. Archiver la preuve de manière licite avec référence vérifiable; pas de citation longue non autorisée.
3. **Double codage indépendant** : deux vérificateurs **humains** identifiables pour l'audit, sans conflit d'intérêts, rendent leur jugement séparément avant confrontation; journal des divergences, accord et mécanisme d'arbitrage. Une simple deuxième passe de ChatGPT ne répond pas à ce critère.
4. **Règles de neutralité** : une source absente ou ambiguë reste inconnue/ambiguë; ne pas déduire une position du nom du parti, de son idéologie, du nombre de liens ou d'une déclaration sans correspondance exacte avec la question. Préserver les positions contradictoires.
5. **Attestation et versions** : décision d'approbation humaine datée, lien d'élément source, copie/version du corpus et commit GitHub précis, traçabilité des désaccords et des contestations. La revue externe du travail doit être **séparée du dépôt**; un drapeau dans un JSON ne suffit pas.
6. **Activation indépendante** : **aucun changement** de `comparisonEligible` ou `positions` avant la réception écrite, les contrôles d'accessibilité/navigateurs et la confirmation de la version réellement déployée.

## Dispositif de contrôle livré

- `assets/nova-compass-review-gate-core.mjs` : réconciliation structurelle des quatre corpus; compte les secondes lectures ChatGPT, les fiches déclarées `finalizable` et les URL structurellement sûres; rejette les faux classements et les matrices incohérentes; **ne délivre jamais une attestation indépendante à partir d'une donnée auto-déclarée**.
- `tests/nova-compass-review-gate.test.mjs` : 13 scénarios de base et adversariaux, notamment une modification fictive du champ `reviewer` pour se faire passer pour un expert externe.
- `tests/nova-compass-ui-review.test.mjs` : 5 tests de lisibilité du statut public et de désactivation du classement des partis.
- `.github/workflows/validate-nova-civic-poll.yml` : exécution de ces tests dans le même pipeline que les contrôles de la boussole et du sondage, en lecture seule.

Les tests structurels ne vérifient ni le contenu des pages politiques externes ni l'authenticité de l'identité d'un réviseur; ils ne constituent pas une revue indépendante.

**Statuts de référence du 8 novembre 2026 préservés :** boussole **9/12 critères de réception (75 %)**, dont `COMPASS_DOCUMENTARY_VALIDATION=PENDING` ; sondage **6/11 (54,5 %)** et fermé; Projet Nova politique **47/100** ; Nova–Sinjira sans taux autonome; SINJIRA™ produit **66,5 % ±10 points** de maturité estimée. **Aucune date de fin certifiable pour la boussole.**

**Décision documentaire : NO-GO pour l'homologation de comparaison partis; poursuite de la collecte d'avis externes.**
