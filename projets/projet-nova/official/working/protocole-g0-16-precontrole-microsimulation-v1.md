# NOVA — G0.16, précontrôle pour une future microsimulation distributive
**Date : 6 novembre 2026** · **Statut : NON AUTORISÉE** · **Programme : 47/100 (inchangé)**

## Rôle
Ce dossier est un **contrôle préparatoire de complétude et de cohérence**, et non une microsimulation,
une approbation du budget, un avis juridique, un chiffrage de taxes ou une réforme.
Il prolonge G0.14 (catégories de recettes) et G0.15 (preuves V01–V15).
Le registre canonique est \`data/matrice-preuves-g0-15-fiscalite.json\` ; les inconnues restent \`null\`.

## Porte G0.16 vérifiable
\`assets/g016-microsimulation-gate-core.mjs\` lit deux fichiers immuables :
le registre G0.15 et l'audit G0.12 de 47/100.
Il vérifie exactement 15 identifiants et leurs familles, les totaux officiels de référence,
l'absence de taux, rendements, budgets et autorisations revendiqués sans preuve,
ainsi que la traçabilité minimale des pièces accompagnées d'une revue déclarée.
Il ne télécharge ni information personnelle, ni données de ménage.

**À la date du contrôle : 0 / 15 preuves déclarées entièrement revues**.
Ces « zéro » expriment l'absence de preuve **confirmée dans ce registre**, pas l'absence
d'études dans le monde réel. Aucune des 15 lignes ne doit être considérée acquise par
simple publication d'un lien ou changement de booléen.

### Étapes obligatoires avant simulation
1. V01–V04 : obtenir des ventilations de recettes réconciliées aux budgets primaires,
   sans transformer automatiquement droits, permis, redevances et dividendes en taxes supprimables.
2. V05–V06 : documenter les véritables bases légales des revenus imposables, crédits,
   exclusions et risques de double compte. Un montant de recettes fiscales n'est **pas** l'assiette.
3. V07–V10 : démontrer la continuité des régimes RRQ, RQAP, santé, médicaments, école et municipalités,
   en préservant les droits des personnes et les fonds affectés.
4. V11 : chiffrer **uniquement un rendement net additionnel** de la lutte contre l'évasion,
   après compétences, recouvrements déjà inclus et coûts de contrôle; valeur courante inconnue.
5. V12–V13 : documenter données de ménages, déciles, statuts résidentiels, régions,
   salaires, PME, emploi et hypothèses macroéconomiques. Ne charger que des jeux agrégés
   ou synthétiques tant que la gouvernance des données individuelles n'est pas approuvée.
6. V14–V15 : établir **deux scénarios séparés** (Québec dans le Canada et Québec souverain),
   comprenant droits, fonctions, dette, monnaie, pensions, transferts, 10 années de budget,
   dépenses de transition, risques et scénarios de stress.

### Interdits et décisions hors automatisation
- Ne jamais inférer un taux d'impôt, un financement acquis ou des avantages nets
  d'une simple agrégation ou d'un taux de recouvrement supposé.
- La réussite d'une vérification locale ne certifie **jamais** une source, l'indépendance
  réelle du contrôleur, un équilibre budgétaire ou la capacité d'appliquer une loi.
- Un résultat \`EXTERNAL_APPROVAL_REQUIRED\` est seulement une invitation à une
  **revue humaine indépendante** ; \`simulation_authorized\` reste toujours \`false\`.
- Ne pas augmenter 47/100 sans un nouvel audit pondéré, traçable et documenté,
  sans modifier unilatéralement les références officielles candidates.

## Test technique
Exécuter : \`node --test projets/projet-nova/tests/g016-microsimulation-gate.test.mjs\`.
Le workflow « Nova-Sinjira — vérifications financières » exécute ce test au sein
de la suite. Il couvre inventaire, doublons, sources trompeuses, faux taux,
faux points supplémentaires et fausses approbations.

**Suite de travail :** acquérir des sources officielles authentiques, définir les
responsables, exiger revues juridiques, actuarielles et financières indépendantes,
puis seulement établir une simulation reproductible par ménage et par scénario
avec les incertitudes et effets distributifs visibles.
