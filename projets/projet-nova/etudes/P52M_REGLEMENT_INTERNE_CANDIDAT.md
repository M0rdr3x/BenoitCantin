# Projet Nova — P52M : mandats des comités et maîtrise des risques

19 octobre 2026 · Étude candidate, non adoptée · NO_GO.

## Objectif
Faire progresser les preuves F01–F20 de P52A à P52L vers des procédures crédibles de délibération et d'examen contradictoire. Les comités ci-dessous sont **proposés**, pas constitués. Aucune personne n'est nommée. Aucune expertise signée n'est inventée. La grille budgétaire décennale comporte encore 600 valeurs inconnues, et les cas d'incidence comportent 720 valeurs inconnues.

## Mandats

| Comité | Responsabilités | Preuves pilotées |
| --- | --- | --- |
| CJF | Juridique et fiscal | F01, F02, F03, F05, F06, F07 |
| CFP | Finances publiques | F04, F08, F09, F10, F13, F18 |
| CSD | Services, distribution et droits | F11, F12, F14, F20 |
| CTE | Transition et relations extérieures | F15, F16, F17 |
| CDE | Démocratie et éthique | F19 |

Chaque comité proposé comporte cinq sièges fonctionnels : présidence, rapporteur, méthode, droits et membre indépendant. Il doit inclure l'expertise appropriée et permettre la contre-expertise. Le cadre demande un minimum de trois participants admissibles, la présence de la présidence et du rapporteur, la récusation des personnes en conflit d'intérêts et une majorité des deux tiers des suffrages exprimés pour une orientation favorable. Pour un risque critique, il faut au moins quatre voix favorables; pour un risque élevé, trois. Ces seuils sont **des propositions internes de conception**, non des règles légales déjà en vigueur.

## Cartographie et avis croisés

Chaque exigence F01–F20 garde son statut BLOQUANT dans P52A. La matrice attribue provisoirement trois notes qualitatives — impact, incertitude, irréversibilité — de 1 à 4; une somme de 7–9 signifie ELEVE et 10–12 CRITIQUE. Les notes ne mesurent pas un risque réel observé et doivent être soumises à une critique indépendante avant adoption. Les avis croisés obligatoires figurent dans le registre. F20 est notamment examiné par le comité des droits avec avis du comité juridique et du comité démocratique.

## Séances fictives et refus d'approbation automatique

Le script audite des scénarios locaux, sans vérifier l'identité réelle des pseudonymes. Il empêche un déposant de voter, les doubles sièges, les récusés qui votent, les fausses majorités, les réserves bloquantes/majeures ouvertes et les avis croisés incomplets ou défavorables. Une réserve résolue ne l'est que sur déclaration : sa preuve et son historique doivent être vérifiés hors GitHub. Une opinion minoritaire, une contestation et un droit de réexamen doivent rester accessibles selon P52L.

Même si une séance fictive satisfait toutes les règles, le résultat final est **NO_GO_AUTOMATIQUE**. Aucune liste nominative, copie d'avis, signature, dossier fiscal personnel ou PDF original n'est déposée dans le dépôt. Un code 0 indique seulement que le dossier technique est cohérent; le code 3 signifie qu'une adoption n'est pas démontrée; le code 2 indique une incohérence.

## Responsabilités avant la tenue de vraies réunions

Un mandant humain habilité doit : définir la compétence juridique et le mandat de chaque comité; sélectionner des experts indépendants et documenter leur compétence; vérifier les déclarations de conflit et la récusation; conserver les preuves originales et les mandats signés hors dépôt; rédiger des procès-verbaux traçables y compris les désaccords et votes dissidents; prévoir audition, contestation, correction, accessibilité et respect des droits fiscaux et de la vie privée.

Le statut du Québec dans le Canada et une éventuelle souveraineté exigent des analyses distinctes, y compris le droit fédéral, les finances des municipalités, les transferts, les services, la dette et les fonctions nouvelles. La simulation d'une séance ne chiffre aucun impôt ni aucun gain de pouvoir d'achat.

## Fichiers
- projets/projet-nova/etudes/P52M_MANDATS_COMITES_ET_RISQUES.json
- projets/projet-nova/etudes/P52M_SEANCES_FICTIVES_VIDES.json
- projets/projet-nova/etudes/P52M_REGLEMENT_INTERNE_CANDIDAT.md
- scripts/auditer_deliberations_nova_p52m.py
- scripts/tests/test_auditer_deliberations_nova_p52m.py
- .github/workflows/validate-nova-p52m.yml

## Priorités ultérieures
Préparer P52N comme guide d'engagement de vrais experts et de consultation publique, sans désignation fictive ni coût inventé. Conserver PR #673 en brouillon; ne pas toucher à SINJIRA, à main ni à PR #640. Les issues #135 (protection de main) et #662 (revues réelles) restent prioritaires.
