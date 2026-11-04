# P55J — Rapprochement des périmètres consolidés et du résultat fiscal 2024

**4 novembre 2026 — rapprochement arithmétique vérifiable sur deux pages du rapport public officiel, sans authentification de version ni certification financière.**

## Sources exactes et nature du contrôle

[Ville de Québec — Rapport financier 2024](https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf), organismes 23027, captures visuelles dans le lecteur Web :
- **PDF index 6, page imprimée 7** : « Renseignements financiers consolidés — Sommaire des variations budgétaires sur les résultats », section explicitement **non auditée**. Elle donne la ventilation budget/réalisations et les éléments de conciliation fiscale.
- **PDF index 12, page imprimée 13** : « Sommaire des résultats à des fins fiscales consolidés », colonnes distinctes « Administration municipale », « Organismes contrôlés et partenariats », « Total consolidé ». Sa note 1 précise que le **total consolidé exclut les opérations entre l'administration et les organismes contrôlés**; la note 2 exclut les opérations entre compétences d'agglomération et compétences locales du chiffre d'administration.

**Nouvel acquis par rapport à P55I :** les **deux pages ont été effectivement examinées visuellement**, leurs colonnes sont lisibles et les montants P55I concordent. Cela n'est **pas** une comparaison de la copie complète avec les empreintes historiques P54Q/P55H, ni une attestation de l'origine des octets, ni un examen complet des notes de consolidation.

## Résidus de périmètre à expliquer

Chaque résidu est calculé : **total consolidé − administration municipale − organismes contrôlés/partenariats**. Tous les montants en dollars canadiens. Les négatifs sont des différences de périmètre, **pas des économies**.

| Poste | Administration municipale | Organismes et partenariats | Consolidé | Résidu calculé |
|---|---:|---:|---:|---:|
| Revenus de fonctionnement | 2 008 356 306 | 354 693 719 | 2 186 607 854 | −176 442 171 |
| Revenus d'investissement | 152 907 248 | 110 071 948 | 262 872 891 | −106 305 |
| **Revenus totaux** | **2 161 263 554** | **464 765 667** | **2 449 480 745** | **−176 548 476** |
| Charges | 1 920 652 747 | 365 431 466 | 2 107 478 001 | −178 606 212 |
| Excédent des activités | 240 610 807 | 99 334 201 | 342 002 744 | **+2 057 736** |
| Fonctionnement avant conciliation | 87 703 559 | −10 737 747 | 79 129 853 | +2 164 041 |
| Éléments de conciliation fiscale | 10 556 966 | 42 376 268 | 50 206 104 | −2 727 130 |
| Excédent de fonctionnement à des fins fiscales | 98 260 525 | 31 638 521 | 129 335 957 | −563 089 |

Exemple : `2 449 480 745 − 2 161 263 554 − 464 765 667 = −176 548 476`. L'identité des soldes est conservée : `−176 548 476 − (−178 606 212) = +2 057 736`.

**Interprétation impérative :** la note 1 du rapport explique qu'il existe des opérations neutralisées dans les totaux consolidés. Le résidu calculé peut comprendre divers effets de consolidation et reclassements. **Aucun chiffre ci-dessus ne permet d'attribuer la totalité du résidu à une écriture particulière, au RTC, à la SOMHAC, ni à une économie réalisable.** Une telle qualification exige les états détaillés, les écritures de consolidation, les comptes réciproques, le périmètre des entités et la contre-revue d'un CPA.

## Passage du résultat comptable au résultat fiscal

L'excédent comptable de l'exercice n'est **pas** équivalent à la trésorerie disponible ni à un gain budgétaire récurrent.

| Pont, 2024 | Budget | Réalisations |
|---|---:|---:|
| Excédent comptable de l'exercice | 400 167 919 | 342 002 744 |
| Moins revenus d'investissement | −403 091 050 | −262 872 891 |
| **Fonctionnement avant conciliation fiscale** | **−2 923 131** | **79 129 853** |
| Plus éléments de conciliation fiscale | +2 923 131 | +50 206 104 |
| **Excédent fiscal de fonctionnement** | **0** | **129 335 957** |

Sur les variations budget → réalisations, l'identité complémentaire est :
`82 052 984 + 47 282 973 = 129 335 957`.

Le sommaire de la page 7 signale que la conciliation fiscale comprend notamment des affectations et le remboursement du capital de la dette; la variation de 47,3 M$ mentionne notamment le recours à des excédents affectés et certaines corrections de valeur. Il serait donc **erroné de dire que 129,34 M$ peut immédiatement être dépensé ou redistribué à la population**, sans examen des fonds réservés, des affectations, des obligations et des dépenses associées.

## Portée dans le Projet Nova

P55J fournit un **rapprochement documenté de huit postes et un pont fiscal reproductible**, pas un calcul d'économie. Le code `scripts/rapprocher_perimetres_et_conciliation_nova_p55j.py` :
- verrouille les huit lignes et leurs quatre colonnes, plus les références de pages;
- vérifie les égalités de chaque périmètre (revenus, charges, excédent, conciliation et solde fiscal);
- recontrôle les totaux du module P55I et les deux chemins de calcul du résultat fiscal;
- expose publiquement les résidus calculés **sans fausse attribution**;
- interdit toute qualification `GO`, tout transfert aux tiers et toute certification financière.

```bash
python scripts/rapprocher_perimetres_et_conciliation_nova_p55j.py \
  --bilan-public /hors_git/p55j_bilan.json \
  --table-public /hors_git/p55j_tableau.json
```

Le programme **ne télécharge aucun fichier** et ne recueille aucune donnée nominative. Il conserve la distinction entre **publication Web lisible visuellement** et **preuve d'édition locale authentifiée**. La correspondance avec les copies historiques reste à établir par P55H/P55G, puis par revue humaine. Les résidus ne sont pas des corrections comptables authentifiées.

## Travail humain réellement requis

Le dossier à examiner doit contenir le détail des opérations réciproques entre entités, les modalités de consolidation et de contrôle, les contraintes d'affectation des excédents, et une qualification de la récurrence ainsi que des effets sur les emplois, les services et le pouvoir d'achat. **Ne pas additionner des montants de deux périmètres ou deux exercices.**

Conserver les quatre dossiers P54E et la date probable ouverts, 40 tâches P54N, dix blocages P54O, 96 P54B et huit P54C non attestés; deux mandats comptable/juridique non signés; aucune économie certifiée. Maintenir les régimes distincts « Québec au Canada » et « Québec souverain hypothétique ».

**Décision : `NO_GO_AUTOMATIQUE`. Aucun contact, aucune dépense ou transmission externe, aucun changement SINJIRA, aucune fusion `main`.**
