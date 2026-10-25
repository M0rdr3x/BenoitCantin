# P54R — Provenance des cinq offsets P54P observés en CI

**Projet Nova — 24 octobre 2026.** Cette étape repose sur une observation réelle de GitHub Actions. Le workflow P54P a récupéré deux copies PDF publiques de taille et empreinte attendues et a reproduit les cinq positions. Le contrôle ne certifie ni la provenance institutionnelle des fichiers ni une anomalie comptable.

## Pièce consultée, résultats et empreintes

- [Workflow P54P #40151185184](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40151185184), job 121042887853.
- [Artefact P54P #12583661231](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40151185184/artifacts/12583661231).
- ZIP réellement téléchargé et examiné : 1 533 octets, SHA-256 d87562662c4c82176e02bdcb28035bb704f2734eb998e0161ef17a21e268c42e.
- Bilan initial p54p_avant_acquisition.json : 795 octets, SHA-256 73856ddd9284acec7a0a5edcf538ff5f7c387ab28429e736cfeb85a1c92914dd.
- Bilan final p54p_reproduction_conditionnelle.json : 2 631 octets, SHA-256 ebfae307f375519b5921358af70b624991f9a3f6a383eb91139d64c399620fb1.

Le bilan final confirme **deux copies PDF de SHA attendu** et **cinq positions lexicales reproduites**. Les journaux GitHub confirment le même résultat, mais proviennent de la même exécution CI : ce ne sont pas deux expertises indépendantes.

| Observation | Source | Page PDF (index zéro) | Offset NFKC | Longueur de page NFKC |
|---|---|---:|---:|---:|
| P54E-V-001 | Ville | 102 | 2359 | 2364 |
| P54E-M-001 | MAMH | 162 | 18 | 2439 |
| Date/année probable (index P54D 2) | MAMH | 162 | 2420 | 2439 |
| P54E-M-002 | MAMH | 162 | 2430 | 2439 |
| P54E-M-003 | MAMH | 162 | 2436 | 2439 |

Ce sont des indices dans le **texte pypdf==5.9.0 normalisé Unicode NFKC**, pas des coordonnées visuelles. Les jetons et le contexte restent absents des artefacts et du dépôt. La date probable n'est pas certifiée; les quatre autres occurrences restent INDETERMINE.

## Deux niveaux de preuve séparés

Le mode sans archive lit uniquement le registre de provenance. Il annonce cinq offsets de référence historiques mais **zéro offset revérifié dans cette exécution**.

Le mode avec archive recalcule le SHA-256 du ZIP, vérifie sa taille, contrôle que seuls les deux JSON attendus sont présents, limite les tailles des membres, refuse les chemins inattendus, puis rapproche les contenus avec le schéma fermé P54P et avec les cinq offsets attendus. La lecture se fait en mémoire sans extraction.

Commande après téléchargement local de l'artefact officiel :

    python scripts/verifier_provenance_artifact_nova_p54r.py --archive /chemin_prive/artefact_p54p.zip --bilan p54r_verification.json

Commande neutre :

    python scripts/verifier_provenance_artifact_nova_p54r.py --bilan p54r_bilan.json

Refus de certification :

    python scripts/verifier_provenance_artifact_nova_p54r.py --exiger-certification

Les codes de sortie 0, 2 et 3 représentent respectivement contrôle technique, refus technique et refus de certification. Une revérification de l'archive ne relit pas physiquement les deux PDF et ne représente pas une signature ou vérification de l'émetteur.

## Décisions interdites et étapes humaines

Les vérificateurs habilités devront encore examiner les cinq occurrences dans leur contexte et vérifier l'unité, l'année, la colonne et les périmètres appropriés. Les 96 vérifications P54B et huit contrôles P54C demeurent ouvertes. Aucune économie n'est déduite des éliminations Ville–RTC–SOMHAC déjà consolidées. Emplois et services protégés; analyses Québec dans le Canada / Québec souverain hypothétique séparées.

**NO_GO_AUTOMATIQUE** : 4 dossiers P54E ouverts, aucune économie certifiée, aucun avis professionnel authentifié, aucune modification SINJIRA et aucune fusion dans la branche principale.
