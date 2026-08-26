# Projet Nova — Statut A1 documentaire

Date : 25 août 2026
Version : `A1-CANDIDATE-2026.08.25`

## État
Le Projet Nova est en **consolidation candidate A1**. Cette mention signifie qu’un effort de cohérence documentaire, de traçabilité, de contrôle de version et de gestion des risques est appliqué au corpus et au site public.

Elle ne signifie pas :
- qu’un parti politique est autorisé par Élections Québec;
- qu’une Constitution ou une loi proposée est en vigueur;
- que les Statuts candidats ont déjà été formellement adoptés par une instance fondatrice;
- qu’un modèle financier est certifié;
- qu’un système de vote Internet est homologué;
- qu’un audit juridique, financier, cybersécurité ou accessibilité externe est terminé.

## Hiérarchie publique A1
1. `official/a1/corpus-part-01.md` à `corpus-part-06.md` : **Corpus maître A1**, référence consolidée pour l’architecture proposée de l’État;
2. `official/a1/statuts.md` : **Statuts, gouvernance et conformité du Parti Nova A1**, référence candidate pour l’organisation politique;
3. `official/a1/programme.md` : **Programme public A1**, référence consolidée pour les orientations politiques destinées aux citoyens;
4. `data/a1-sources.json` : manifeste de version et empreintes SHA-256 des sources A1;
5. `constitution.html`, `programme.html`, `code-conduite.html`, `documents.html` et `registre-conformite.html` : portails et synthèses publiques dérivés des sources A1;
6. anciens PDF : **archives préparatoires ou historiques** conservées pour la traçabilité.

## Règle de priorité
En cas de divergence entre une ancienne publication et une source A1, la source A1 correspondante représente la consolidation publique la plus récente. Cette priorité est documentaire et politique; elle ne transforme pas la source en droit en vigueur.

## Règle de non-confusion
Une proposition, un pilote ou un document préparatoire ne peut être présenté comme mesure active. Toute activation future doit être identifiée, datée, justifiée et reliée à l’autorité compétente.

## Contrôle d’intégrité
Toute modification d’une source A1 exige une nouvelle empreinte SHA-256 dans `data/a1-sources.json`. Le contrôle automatisé doit échouer si une source, une empreinte, un lien critique ou une exigence de confidentialité n’est plus cohérent.
