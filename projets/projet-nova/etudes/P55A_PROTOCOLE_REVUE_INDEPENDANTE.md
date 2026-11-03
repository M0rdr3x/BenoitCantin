# P55A — Passation contrôlée vers expertise indépendante (3 novembre 2026)

**Statut : préparation non certifiante.** P54Z a réussi ses 40 tests synthétiques ([GitHub Actions #41738233729](https://github.com/M0rdr3x/BenoitCantin/actions/runs/41738233729)), mais cela ne constitue aucune validation financière ou juridique. Le présent jalon ne mandate aucun expert et ne communique avec aucune institution.

## Objet et chaîne de références

P55A reprend **cinq observations historiques 2024** (quatre dossiers P54E et une occurrence de date/année probable) et les **40 contrôles préparatoires P54Z**; il définit **dix exigences par observation, soit 50 positions** pour une future revue sur pièces. Les références et les contrôles ne sont pas des montants; aucun chiffre ne doit être calculé à partir des seuls offsets NFKC.

Les dix exigences concernent : (1) provenance/intégrité des originaux; (2) conservation et intégrité hors dépôt; (3) droits d'accès et restrictions; (4) mandat écrit et périmètre de la mission; (5) qualification et indépendance du professionnel; (6) conflits d'intérêts; (7) vérification visuelle sur les pages et comparaison avec NFKC; (8) contradictions et réserves; (9) consolidation Ville de Québec–RTC–SOMHAC; (10) impacts sur les emplois, les services et le pouvoir d'achat.

## Fonctionnement technique et protection des personnes

- **Source obligatoire** : la fiche privée P54Z en lecture seule, hors dépôt, avec permissions `0600` et sans lien symbolique; sa structure est vérifiée et son SHA-256 est inscrit uniquement dans la future fiche P55A privée.
- **Création locale** : `python scripts/preparer_revue_independante_nova_p55a.py --declarations-p54z /hors-git/p54z.json --creer-modele-prive /hors-git/p55a.json`.
- **Contrôle local** : `python scripts/preparer_revue_independante_nova_p55a.py --declarations-p54z /hors-git/p54z.json --relecture-locale /hors-git/p55a.json --bilan-public bilan_p55a.json`.
- **Vocabulaire fermé** : `NON_INSTRUIT`, `PREPARE_NON_ATTESTE`, `RESERVE`, `SUSPENDU`. Un dossier ne peut déclarer une préparation P55A que si ses huit contrôles P54Z préalables sont tous déclarés préparés. Cette double préparation ne vaut toujours pas attestation.
- Les fichiers privés ne doivent contenir **ni noms ni coordonnées ni signatures ni références à des fichiers contenant des données personnelles**, ni observations textuelles libres. La matrice publique ne contient que des compteurs globaux, et ne révèle ni SHA privé ni numéro d'observation.
- En présence d'une suspension dans P54Z ou P55A, la suspension est **conservée**. Un rapport complet ne permet ni fermeture, ni transmission ni GO automatique. Une attestation d'expert, ses habilitations, conflits d'intérêts, mandat, méthodes et observations doivent être examinés par une autorité humaine compétente, dans un circuit documentaire séparé et légal.

## Exigences réelles d'expertise hors application

Un mandat indépendant recevable devrait préciser la compétence juridique/comptable, le périmètre, le cadre normatif applicable, les obligations de confidentialité, la disponibilité des originaux, la chaîne de garde des documents, l'absence ou la gestion des conflits d'intérêts, une procédure contradictoire et une signature vérifiable. **Aucun de ces faits n'est attesté dans ce jalon.** Les deux régimes (Québec au Canada et souverain hypothétique) demeurent distincts.

**Verrous conservés :** quatre dossiers P54E ouverts, une occurrence de date non qualifiée, 40 tâches P54N, 10 blocages P54O, 96 comparabilités P54B et huit contrôles P54C non attestés; aucune économie certifiée. Les éliminations comptables Ville–RTC–SOMHAC ne sont jamais comptées deux fois. Aucun licenciement, aucune dégradation des services et aucun transfert de charges caché ne peuvent être légitimés par cette étude. Aucune modification des normes officielles, de la fiscalité, de SINJIRA ou de la branche `main`.

**Décision permanente de cet outil : `NO_GO_AUTOMATIQUE`.**
