# P54T — Conservation durable des bilans P54P à octets identiques

**Projet Nova, 24 octobre 2026.** Les deux PDF institutionnels de 2024 ont été techniquement acquis durant le [workflow P54P #40151185184](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40151185184). L'artefact [#12583661231](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40151185184/artifacts/12583661231) contient deux bilans JSON publics : un bilan neutre et le résultat de cinq offsets lexicaux reproduits sur les textes normalisés NFKC.

## Problème de durée de conservation

Les artefacts GitHub Actions expirent. P54T conserve dans la branche les **deux fichiers publics d'origine**, avec leurs octets, tailles et empreintes SHA-256 identiques aux pièces archivées observées par P54R.

| Fichier figé | Taille | SHA-256 |
|---|---:|---|
| p54p_avant_acquisition.json | 795 octets | 73856ddd9284acec7a0a5edcf538ff5f7c387ab28429e736cfeb85a1c92914dd |
| p54p_reproduction_conditionnelle.json | 2 631 octets | ebfae307f375519b5921358af70b624991f9a3f6a383eb91139d64c399620fb1 |

Le chemin versionné est projets/projet-nova/etudes/p54t_archive_durable_p54p/. Le ZIP historique de 1 533 octets a une empreinte documentée d87562662c4c82176e02bdcb28035bb704f2734eb998e0161ef17a21e268c42e, mais **P54T ne télécharge, ne recompose ni ne relit ce ZIP**. Son objectif est de rendre vérifiables les deux bilans internes de manière indépendante de la rétention Actions. Leur SHA identique ne signifie pas que l'émetteur institutionnel a signé ces fichiers.

## Cinq offsets observés, aucune anomalie monétaire

| Référence | Page index PDF zéro | Offset / longueur NFKC |
|---|---:|---:|
| P54E-V-001, Ville | 102 | 2359 / 2364 |
| P54E-M-001, MAMH | 162 | 18 / 2439 |
| Année/date probable non certifiée, MAMH | 162 | 2420 / 2439 |
| P54E-M-002, MAMH | 162 | 2430 / 2439 |
| P54E-M-003, MAMH | 162 | 2436 / 2439 |

Ces offsets sont des indices de caractères du texte pypdf normalisé NFKC, **pas des coordonnées visuelles du PDF**. Les quatre dossiers restent INDETERMINE; l'observation de date reste probable et non attestée. Aucun montant, jeton brut, texte source, contexte privé ni identité n'est ajouté aux fichiers figés.

## Vérificateur et commandes

Le programme scripts/verifier_archive_publique_figee_nova_p54t.py recharge P54R et P54P, contrôle les deux fichiers figés sur les octets, reconstitue la structure exacte des bilans, et exige les cinq offsets de référence. Il refuse toute altération, absence de fichier, lien symbolique ou prétention de certification.

Bilan initial sans relecture d'octets :

    python scripts/verifier_archive_publique_figee_nova_p54t.py --bilan p54t_initial.json

Relire et vérifier réellement les deux JSON figés :

    python scripts/verifier_archive_publique_figee_nova_p54t.py --verifier-fichiers-figes --bilan p54t_relecture.json

Tester le refus d'une certification financière ou professionnelle fictive :

    python scripts/verifier_archive_publique_figee_nova_p54t.py --verifier-fichiers-figes --exiger-certification

Retour 0 : validation structurelle seulement. Retour 2 : source incohérente ou fichier invalide. Retour 3 : prétention de certification rejetée.

## Limites probatoires et conservation

La conformité SHA-256 démontre l'identité des **octets des bilans conservés** aux empreintes P54R documentées; elle ne certifie pas la provenance légale, l'exactitude d'une interprétation, l'identité des émetteurs, ni une nouvelle lecture des deux PDF dans ce jalon.

P54S est le dispositif distinct de relecture du ZIP d'origine via l'API GitHub, s'il demeure disponible. P54T relit les deux bilans dans Git, même si cet artefact expire. Ces tâches ne représentent pas deux contre-expertises indépendantes.

La prochaine action ayant valeur documentaire est de faire qualifier les cinq observations sur les originaux et les contextes pertinents par une personne habilitée, avec contre-revue. Les 96 contrôles P54B et huit contrôles P54C restent ouverts. Aucune double comptabilisation Ville–RTC–SOMHAC n'est recevable; continuité de l'emploi et des services et séparation des scénarios constitutionnels restent impératives.

**NO_GO_AUTOMATIQUE** : aucune économie certifiée, aucun avis professionnel obtenu, aucune décision automatique. La PR #673 demeure en brouillon, sans fusion dans main ni modification SINJIRA.
