# P54U — Fiches ciblées de localisation des cinq occurrences

**Projet Nova — 24 octobre 2026.** Ce jalon transforme les cinq offsets documentés par P54P et figés dans P54T en fiches de travail destinées à une vérification humaine future. Il ne relit ni les PDF originaux, ni le ZIP GitHub historique.

## Source et valeur probante

Le workflow P54P #40151185184 a effectivement acquis les deux PDF publics 2024 de taille et SHA-256 correspondants, puis reproduit cinq positions du texte de page normalisé NFKC. Les deux bilans JSON publics de son artefact #12583661231 sont conservés dans le dépôt par P54T.

P54U appelle le vérificateur P54T sur **les octets des deux bilans JSON figés**, compare leurs empreintes SHA-256 et vérifie leur contenu par rapport aux schémas et offsets historiques. Il exige ce contrôle lors du run courant avant d'émettre des fiches. Il ne constitue ni une seconde acquisition des PDF, ni une contre-expertise indépendante.

## Les cinq fiches

| Repère | Source | Index PDF zéro | Offset / longueur NFKC | Nature indicative |
|---|---|---:|---:|---|
| P54E-V-001 | Ville de Québec | 102 | 2359 / 2364 | Indéterminée |
| P54E-M-001 | MAMH | 162 | 18 / 2439 | Indéterminée |
| P54O-DATE-001 | MAMH | 162 | 2420 / 2439 | Année/date probable non certifiée |
| P54E-M-002 | MAMH | 162 | 2430 / 2439 | Indéterminée |
| P54E-M-003 | MAMH | 162 | 2436 / 2439 | Indéterminée |

Les offsets correspondent à des indices de caractères **du texte extrait par pypdf 5.9.0 et normalisé Unicode NFKC**. Ils ne sont pas des coordonnées visuelles ou des montants. La cinquième occurrence ne devient ni une anomalie financière ni un cinquième dossier P54E.

## Travail humain ciblé : 25 positions non attestées

Chaque occurrence exige cinq actions complémentaires : vérifier la version PDF; refaire l'extraction NFKC; localiser visuellement le passage sur la page; qualifier la nature du jeton à partir de la pièce primaire; soumettre cette qualification à une contre-revue distincte.

Ces 25 positions sont un **mode d'emploi ciblé** et ne remplacent pas les 40 tâches P54N, les dix blocages P54O, les 96 contrôles P54B ni huit contrôles P54C. La nature des cinq observations demeure non certifiée, et aucune intervention professionnelle n'est réputée effectuée.

## Commandes

Bilan neutre sans nouvelle vérification d'empreintes :

    python scripts/preparer_feuilles_localisation_nova_p54u.py --bilan p54u_bilan_initial.json

Génération conditionnée à la vérification SHA-256 réelle des deux JSON P54T :

    python scripts/preparer_feuilles_localisation_nova_p54u.py --verifier-bilans-figes --fiches p54u_fiches.json --instructions p54u_instructions.md --bilan p54u_bilan.json

Refus explicite de toute transmission présumée :

    python scripts/preparer_feuilles_localisation_nova_p54u.py --exiger-remise

Codes de retour : 0, schémas et bilans cohérents sans aucune certification; 2, absence ou altération d'un bilan, incohérence, erreur de chemin; 3, refus d'une demande de remise automatique. Les sorties existantes, liens symboliques et collisions de chemin sont refusés.

## Confidentialité et limites d'usage

Ne publier aucun jeton exact, passage protégé, diagnostic privé, identité, permis ou signature. Les originaux doivent être examinés par des personnes habilitées dans un espace privé, avec contre-revue et traçabilité réelles. Toute hypothèse financière doit être établie séparément, sans double compte Ville–RTC–SOMHAC et sans remise en cause non fondée des emplois et services.

Conserver distincts le Québec au sein du Canada et le Québec souverain hypothétique. Aucun expert n'a été mandaté, aucune autorisation de remise n'a été obtenue, aucune économie n'est certifiée. Aucun des quatre dossiers P54E n'est clos.

**NO_GO_AUTOMATIQUE** : aucune transmission, aucune fusion vers main et aucune action SINJIRA.
