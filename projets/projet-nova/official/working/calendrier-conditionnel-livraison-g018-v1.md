# Projet Nova — G0.18 : calendrier conditionnel de clôture

**Version de travail du 8 novembre 2026, non adoptée ni contractuelle.** Le score du programme est **47/100** selon l'audit interne du 5 novembre ; **53 points restent à obtenir**. La maturité rédactionnelle approximative de **75 %** ne constitue pas une certification.

## La réponse à « quand le programme sera-t-il terminé ? »

- **Cible de gestion proposée : 31 décembre 2027**, sous réserve d'obtenir les moyens, données, expertises, consultations et décisions nécessaires.
- **Date de fin estimable sur preuves : indéterminée (`null`)**. Les mandats et budgets d'étude ne sont pas attribués.
- **Date de fin certifiée : indéterminée (`null`)**. Même l'achèvement rédactionnel du programme ne crée pas un État souverain.

**2028 ou au-delà reste possible** si une étude de soutenabilité, un examen juridique ou une consultation exige une révision. L'objectif de fin 2027 est une hypothèse de planification, jamais une promesse.

## Sept jalons dépendants

| Jalon | Date cible non approuvée | Dépendances | Pièces nécessaires |
| --- | --- | --- | --- |
| M01 — Mandats, gouvernance, financement des analyses | 31 décembre 2026 | — | Décideur habilité, réviseurs et budget |
| M02 — Assiettes et 15 dossiers fiscaux V01–V15 | 31 mars 2027 | M01 | Sources primaires, périmètres, contrôles des transferts |
| M03 — Droits, compétences et 24 contextes juridiques | 31 mars 2027 | M01 | Avis contradictoires et voies de recours |
| M04 — Transition souveraine et continuité | 30 juin 2027 | M02, M03 | Dette, actifs, pensions, monnaie, traités et obligations |
| M05 — Quatorze dossiers sectoriels | 30 juin 2027 | M01 | Finances, RH, sécurité, accès territorial et effets sociaux |
| M06 — Deux budgets décennaux et audits indépendants | 30 septembre 2027 | M02, M03, M04, M05 | 20 exercices-scénarios, 15 preuves fiscales et avis externes |
| M07 — Consultations, corrections et adoption | 31 décembre 2027 | M06 | Décisions des autorités compétentes et audit final |

Le **chemin critique structurel** est M01 → M02/M03 → M04 → M06 → M07, avec un chantier M05 parallèle. Une objection sur les compétences fiscales, les droits ou la transition peut forcer à redéfinir plusieurs phases. Les dates ne représentent pas des durées contractualisées.

## Conditions réelles de clôture

Le contrôle existant `assets/closure-gate-programme-core.mjs` établit **sept portes cumulatives** : (1) 100/100 à l'audit, (2) dix domaines complets, (3) quatorze secteurs validés, (4) quinze preuves fiscales homologuées indépendamment, (5) vingt exercices-scénarios audités sur dix ans pour deux contextes, (6) revues indépendantes et (7) adoption formelle. **Au 8 novembre : 0/7 franchie.**

Le cadre financier du gouvernement du Québec propose cinq exercices de référence de 2026–2027 à 2030–2031 : il ne constitue **ni les budgets Nova ni un rendement garanti des deux prélèvements**. Les cinq exercices de référence suivants, la recette additionnelle contre les paradis fiscaux et de nombreux coûts souverains restent non chiffrés. Les transferts fédéraux du contexte provincial ne sont pas automatiquement reconduits dans le contexte souverain.

## Risques de retard

1. Données fiscales, municipales ou gouvernementales impossibles à comparer : conserver les inconnues à `null`, ne pas inventer de taux.
2. Avis juridiques contradictoires : modifier ou abandonner une mesure, puis la réexaminer.
3. Mandats, financement ou réviseurs indépendants indisponibles : ne pas déclarer un jalon achevé.
4. Non-soutenabilité des deux prélèvements : maintenir la continuité des services, du revenu et des salariés et suspendre le calendrier de remplacement.
5. Consultation ou adoption non obtenue : revoir la proposition et publier les objections.

## Contrôle et statut

Le registre `data/calendrier-conditionnel-g018-2026-11-08.json` conserve les jalons, dépendances, cibles et risques. Le moteur `assets/calendrier-conditionnel-g018-core.mjs` vérifie les incohérences structurelles : la déclaration « terminé » exige mandat, financement, preuve, décision et étapes préalables. **Ce logiciel ne vérifie pas l'authenticité d'un avis et ne certifie jamais la fin du programme** ; `date_de_fin_certifiee` reste `null`.

Les archives historiques du SCQ et les références candidates du Projet Nova restent distinctes; ce dossier n'adopte aucune loi, aucun statut partisan et aucun budget.

**Décision G0.18 : 47/100 maintenus. Fin 2027 = cible non garantie. Fin vérifiable = encore inconnue.**
