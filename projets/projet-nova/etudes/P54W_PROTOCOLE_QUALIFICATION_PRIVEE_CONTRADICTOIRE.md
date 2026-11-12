# P54W — Qualification humaine locale contradictoire, sans certification

**Projet Nova — 25 octobre 2026.** Protocole de préparation de revue, sans mandat attribué, examinateur authentifié ni avis signé.

## Chaîne vérifiable et limites

P54P a réellement reproduit cinq positions sur deux PDF 2024 dont les tailles et empreintes historiques SHA-256 correspondaient : [Actions #40151185184](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40151185184). P54T conserve les deux bilans publics figés et P54U produit cinq repères. P54V est l'outil local hors Git permettant une nouvelle extraction des originaux et la production de cinq fiches contextuelles confidentielles.

P54W **ne relit pas les PDF originaux** : il accepte exclusivement, dans un espace privé, une fiche P54V dont les métadonnées correspondent aux positions et classifications P54T, et vérifie la concordance de chaque jeton avec son extrait. Cela ne démontre pas l'authenticité institutionnelle de la fiche P54V : même un fichier structurellement cohérent pourrait avoir été fabriqué. Seule une véritable révision sur les originaux par une personne habilitée peut qualifier les observations.

## Cinq cas de qualification non finale

| Référence | Source et page index zéro | Position dans texte NFKC | Qualification |
|---|---|---:|---|
| P54E-V-001 | Ville de Québec 102 | 2359 | Indéterminée |
| P54E-M-001 | MAMH 162 | 18 | Indéterminée |
| P54O-DATE-001 | MAMH 162 | 2420 | Date/année probable, non confirmée |
| P54E-M-002 | MAMH 162 | 2430 | Indéterminée |
| P54E-M-003 | MAMH 162 | 2436 | Indéterminée |

Ces positions sont des **offsets du texte Unicode NFKC** et non des coordonnées visuelles, des montants ou des preuves d'anomalies comptables. La cinquième observation n'est pas un cinquième dossier P54E.

## Double examen uniquement déclaratif

P54W distingue deux rôles de saisie : lecteur et contre-lecteur. Un code pseudonyme ne prouve pas l'identité, l'indépendance ou l'habilitation. Le formulaire interdit les noms, notes libres, numéros de permis, textes et jetons bruts. Les types déclarables sont indéterminé, date possible, folio possible, référence normative possible, identifiant possible, valeur non monétaire possible et montant potentiel **non attesté**.

Une mention d'examen doit correspondre au contrôle « qualifier la nature sur pièce ». Les déclarations « aucune revue », « revue partielle », « double revue » n'ont aucune portée certifiante. Les suspensions dominent, puis les contradictions déclarées (y compris deux qualifications incompatibles), puis les réserves. Aucune qualification ne devient finale automatiquement.

Les huit contrôles P54V — source originale, offset, page visuelle, nature, distinction date/folio/référence/valeur, unité/exercice/colonne si pertinent, réserves et contre-revue distincte — servent de cadre, non de certificat.

## Confidentialité et usage

Les deux fichiers P54V et P54W doivent rester **hors dépôt**, avec des droits 0600, et sans lien symbolique. P54W lie sa propre fiche privée aux octets de P54V par SHA-256, sans exposer cette empreinte dans le rapport public. Les originaux, extraits et identifiants personnels ne sont jamais admis dans un artefact GitHub. CI n'utilise que des données factices.

Générer un bilan public vierge :

    python scripts/qualifier_occurrences_privees_nova_p54w.py --bilan-public p54w_bilan_neutre.json

À partir d'une fiche P54V locale réellement créée avec les PDF hors Git :

    python scripts/qualifier_occurrences_privees_nova_p54w.py --fiche-privee-p54v /espace_prive/p54v.json --modele-prive /espace_prive/p54w.json

Après intervention humaine, classer uniquement les déclarations documentaires :

    python scripts/qualifier_occurrences_privees_nova_p54w.py --fiche-privee-p54v /espace_prive/p54v.json --revues-privees /espace_prive/p54w.json --bilan-public p54w_bilan_public.json

Vérifier le refus de clôture automatique :

    python scripts/qualifier_occurrences_privees_nova_p54w.py --exiger-cloture

Codes : **0** = formulaire techniquement recevable; **2** = données et sécurité refusées; **3** = impossibilité de clôture automatique. Aucun code ne signifie que des spécialistes ont effectivement examiné les pièces.

## Portée et garanties

Les cinq observations ne sont pas qualifiées humainement. Les quatre dossiers P54E, 40 tâches P54N, dix blocages P54O, 96 vérifications P54B et huit P54C demeurent ouverts. Aucun gain nouveau ne peut être inféré d'écritures déjà éliminées en consolidation Ville–RTC–SOMHAC. Les emplois et services sont protégés, et les scénarios Québec au Canada / Québec souverain hypothétique restent distincts.

**NO_GO_AUTOMATIQUE** : aucune signature professionnelle authentifiée, aucune économie certifiée, aucun contact avec un ordre, aucune transmission, aucune fusion main et aucune action SINJIRA.
