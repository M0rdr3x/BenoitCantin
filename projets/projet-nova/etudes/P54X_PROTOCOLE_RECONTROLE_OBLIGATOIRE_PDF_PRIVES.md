# P54X — Verrou de relecture : deux PDF originaux requis avant les déclarations P54W

**Projet Nova — 26 octobre 2026.** Mesure de contrôle renforcée, distincte des opérations d'authentification professionnelle. Elle interdit d'utiliser une fiche contextuelle P54V simplement déclarée comme preuve que les originaux ont effectivement été lus à cette étape.

## Constat et solution technique

Les workflows P54V et P54W ont été validés après réparation d'une fixture de test qui remplaçait temporairement les références PDF tout en appelant la configuration historique P54R. La correction des tests restaure leur isolation : elle ne modifie ni les empreintes historiques ni le texte des originaux.

Les fiches P54V contiennent des extraits **strictement privés**. P54W peut valider leur cohérence de structure, leurs positions et leur lien SHA-256 avec les déclarations d'examen; il ne peut pas, à lui seul, prouver que la fiche provenait de PDF réellement présents. **P54X exige donc une nouvelle lecture physique locale des deux PDF avant d'accepter une revue P54W.**

## Entrées obligatoires ensemble

1. **PDF Ville de Québec 2024** (copie locale autorisée hors Git, SHA-256 historique P54D).
2. **PDF MAMH 2024** (copie locale autorisée hors Git, SHA-256 historique P54D).
3. **Fiche privée P54V**, déjà préparée et protégée en mode 0600.
4. **Fiche privée P54W**, également en mode 0600, avec déclarations liées à la fiche P54V par son SHA-256 calculé.

Ces quatre entrées sont indivisibles. Le programme réutilise la sécurité de P54Q pour refuser les chemins doubles, les liens symboliques et les fichiers PDF situés dans Git. Il appelle ensuite P54V pour vérifier **les octets des deux PDF**, les empreintes SHA historiques, le registre P54T figé et la reproduction des cinq positions NFKC, puis reconstruit les cinq fiches contextuelles **en mémoire**.

La fiche P54V reçue est comparée entièrement à la fiche reconstruite, y compris les extraits et les jetons, **sans les imprimer**. Une différence, un PDF absent ou modifié, un accès public à une fiche privée, une référence d'observation différente ou une déclaration P54W mal liée provoque le refus.

La réussite technique valide l'intégrité et la cohérence d'un ensemble de fichiers à un instant donné. Elle **n'authentifie pas l'émetteur institutionnel**, ne démontre pas l'identité du lecteur et n'établit pas que le texte est une différence monétaire.

## Bilan public autorisé et confidentialité

Le bilan public contient uniquement les références des cinq dossiers/observations (quatre dossiers P54E et la date probable P54O), les états de revue *déclaratifs*, le nombre d'originaux techniquement relus et les avertissements institutionnels. Les jetons, extraits, PDF originaux, empreintes privées, noms des lecteurs et chemins locaux ne sont pas copiés dans la sortie ou les artefacts CI.

Une contre-lecture sous deux pseudonymes différents ne constitue pas une preuve d'indépendance. Une qualification « montant potentiel non attesté » n'est **pas** un montant certifié; une suspension ou contradiction signalée reste prioritaire.

## Commandes

Produire un bilan neutre dans CI ou sans pièces privées :

    python scripts/reverifier_originaux_avant_revue_nova_p54x.py --bilan-public p54x_bilan_neutre.json

Dans un espace privé autorisé contenant réellement les quatre fichiers :

    python scripts/reverifier_originaux_avant_revue_nova_p54x.py --pdf-ville /espace_prive/ville_2024.pdf --pdf-mamh /espace_prive/mamh_2024.pdf --fiche-privee-p54v /espace_prive/p54v.json --revues-privees-p54w /espace_prive/p54w.json --bilan-public p54x_bilan_agrege.json

Les quatre fichiers privés ne doivent pas être joints à une demande de fusion, téléversés dans GitHub Actions ou communiqués à des destinataires non habilités. Le programme ne requiert ni clé GitHub ni réseau.

Démontrer le refus explicite de clôture :

    python scripts/reverifier_originaux_avant_revue_nova_p54x.py --exiger-cloture

**Codes de sortie :** 0 = bilan neutre ou contrôle documentaire cohérent; 2 = source, contrôle ou chemin refusé; 3 = refus de clôture fictive. Aucun code ne constitue une signature professionnelle.

## État des travaux hors logiciel

Les cinq observations lexicales restent à qualifier par des personnes habilitées; quatre dossiers P54E restent ouverts et une année/date probable reste indéterminée professionnellement. Les 40 tâches P54N et dix blocages P54O demeurent à instruire; les 96 contrôles P54B et huit contrôles P54C ne deviennent pas des vérifications accomplies par l'exécution de P54X.

Les écritures Ville–RTC–SOMHAC déjà éliminées ne peuvent être recomptées comme une nouvelle économie. Maintien des emplois et services, et séparation permanente du scénario Québec au Canada et du scénario de souveraineté hypothétique.

**NO_GO_AUTOMATIQUE :** aucune signature authentifiée, aucune décision institutionnelle, aucun montant ou économie certifié, aucune fusion de main et aucune modification SINJIRA.
