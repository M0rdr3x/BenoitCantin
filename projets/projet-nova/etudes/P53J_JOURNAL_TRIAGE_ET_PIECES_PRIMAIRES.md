# Projet Nova — P53J : journal de triage des contreparties municipales (exercice 2024)

**22 octobre 2026 — Projet de recherche, non certifié, non consolidé, non adopté.**
Suite de P53I, sans modifier ses fichiers et sans toucher à SINJIRA.

## Travail effectivement réalisé

P53J ajoute un contrôle reproductible sur les **1 344 organismes** de la sélection P53I issue du MAMH, publiée sous empreinte SHA-256 cef644e3f16ebea6bc727b009037638fa70443fe66fbeb55e4ac1e3cb1071213. Le programme vérifie les totaux bruts, les identifiants uniques, la présence de Saint-Valère (39135), la stabilité des **25 priorités P53H**, le maintien des valeurs négatives et la distinction entre case vide et montant nul.

Il génère un journal de 1 344 déclarants comprenant les revenus en quotes-parts, les transferts reçus et deux catégories de charges payées **sur la même ligne de déclarant**. Leur proximité visuelle ne signifie **jamais** une opération bilatérale. Tous les champs de payeur, bénéficiaire transactionnel, référence des deux écritures, contrôle de périmètre, visa indépendant et montant éliminable demeurent vides en l'absence de pièces. Le journal ne sera pas traité comme un grand livre d'opérations.

Le journal met en tête les 25 organismes déjà priorisés par P53H et signale séparément la municipalité ajoutée lors de P53I. La somme brute des flux reçus, les 2 526 339 827 CAD de quotes-parts payées et leur écart de 621 869 270 CAD ne deviennent **ni économie, ni revenu fiscal, ni élimination comptable**.

## Pièces primaires à solliciter avant tout rapprochement réel

Pour chaque flux priorisé : obtenir l'entente ou résolution autorisant la contribution, la facture ou l'appel de quote-part, les extraits du grand livre chez le payeur et le bénéficiaire avec identifiants et dates, les justificatifs de versement, l'exercice et les éventuelles écritures d'ajustement. Demander à chaque organisme le **périmètre consolidé**, la méthode comptable appliquée, les quotes-parts intragroupe déjà éliminées et la pièce montrant cette élimination. Vérifier le même montant, les signes, la période, la nature et l'identité juridique de chaque contrepartie. En cas d'ambiguïté, laisser le statut non apparié.

Les données sources municipales sont révisables. Les fichiers originaux intégraux ne sont pas présents dans Git : conserver les **originaux officiels** en stockage autorisé, avec horodatage, empreinte cryptographique, preuve d'origine et historique des corrections. Une nouvelle version doit faire l'objet d'une réconciliation distincte ; P53J ne prétend pas avoir téléchargé de nouveaux originaux.

## Critères bloquants pour une élimination admissible

Un futur rapprochement doit disposer simultanément : de deux pièces d'écritures authentifiées, des identifiants juridiques et comptables bilatéraux, de l'exercice et de la date, de la contrepartie exacte et de l'objet, des corrections et remboursements, de la détermination du périmètre consolidé, de l'absence d'élimination déjà constatée, d'un contrôle de doublons et de la revue signée d'un comptable indépendant. Même une correspondance mathématique parfaite demeure un **candidat**, pas un montant certifié.

L'analyse de consolidations doit suivre le [Manuel de la présentation de l'information financière municipale](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/manuel) et les [règles du périmètre comptable](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/normes-comptables). Ces règles indiquent que des organismes contrôlés sont déjà consolidés dans leurs états. Il faut éviter une seconde élimination.

## Commandes de contrôle

    python scripts/auditer_appariements_municipaux_nova_p53j.py --rapport p53j_bilan.json --export-csv p53j_journal_1344.csv
    python scripts/auditer_appariements_municipaux_nova_p53j.py --exiger-appariements

Le contrôle normal termine avec code 0 si les **fichiers dérivés** sont intègres; le contrôle exigeant des preuves termine avec **code 3 (REFUS)** tant que les contreparties ne sont pas authentifiées. Une source modifiée ou invalide produit code 2. Les sorties existantes ne sont jamais écrasées.

## Décision

**NO_GO_AUTOMATIQUE.** Zéro appariement transactionnel documenté; zéro élimination certifiée; aucun gain financier démontré; 20 preuves F01–F20 non validées; 1 320 montants Nova inconnus; zéro taux adopté; zéro avis indépendant signé. Aucune modification du régime fiscal, aucune fusion de la PR, aucune publication comme norme adoptée. Les sources 2024 ne sont pas additionnées à un budget provincial 2026–2027.
