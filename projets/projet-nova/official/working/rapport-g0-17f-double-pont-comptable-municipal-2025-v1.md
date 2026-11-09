# Projet Nova–Sinjira — G0.17f : rapprochement de fonctionnement, investissement et trésorerie d'une municipalité réelle

**Date : 8 novembre 2026 — Étude technique de Port-Daniel–Gascons (code 02047), exercice clos le 31 décembre 2025.**  
**Préparation interne Nova–Sinjira : 47/100, soit 53 points restant à valider.**

**Portée :** un exemple municipal officiel, **pas** une généralisation financière au Québec, une vérification de taux d'impôt Nova, une certification du programme ou une enquête portant sur des irrégularités.

## 1. Résultat nouveau : trois comptes qu'on ne peut pas confondre

Les travaux G0.16r avaient relevé les grands postes des états financiers 2025, avec un auditeur ayant formulé **une opinion avec réserve**. G0.17e a isolé les subventions d'investissement TECQ des dépenses régulières de salaire et d'entretien. G0.17f franchit un niveau de détail supplémentaire en reconstruisant, à partir du **rapport financier 2025 officiel**, les **résultats détaillés de fonctionnement et d'investissement**, leur **conciliation à des fins fiscales**, le **tableau des immobilisations par fonction**, la **répartition des dépenses par objet**, puis **l'état des flux de trésorerie**.

**Source primaire :** [MAMH — Rapport financier 2025 et autres documents, Port-Daniel–Gascons](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2025-et-autres-02047.pdf). Pages PDF indexées : **3** (auditeur), **7** (résultats), **8** (situation), **10** (trésorerie), **26** (détail des revenus), **27** (charges par fonction), **28** (fonctionnement à des fins fiscales), **29** (investissement à des fins fiscales) et **30** (charges par objets). Les pages ont été étudiées à partir du texte diffusé par le navigateur de recherche; **la capture d'image du PDF a échoué en raison d'un « cache miss »**. Les chiffres recoupent également le registre G0.16r, mais les pièces bancaires sous-jacentes ne sont pas dans notre dossier.

**Réserve de l'auditeur, Raymond Chabot Grant Thornton, 8 juin 2026 :** les obligations de mise hors service d'immobilisations n'ont pas été évaluées ni comptabilisées et leur incidence demeure non quantifiée. C'est **une réserve concernant les comptes municipaux**, et non un audit ni une accusation sur Nova ou un projet d'infrastructure particulier.

## 2. Deux origines de revenus reconnus, mais pas deux caisses distinctes

Le rapport 2025 affiche **25 730 544 $ de revenus comptabilisés**. La ventilation du tableau S12 distingue :

| Revenus 2025 | Montant reconnu |
| --- | ---: |
| Taxes de fonctionnement | 4 525 681 $ |
| Compensations tenant lieu de taxes | 63 631 $ |
| **Transferts affectés au fonctionnement** | **724 172 $** |
| Services rendus | 363 935 $ |
| Imposition de droits | 51 824 $ |
| Amendes et pénalités | 952 $ |
| Revenus d'intérêts | 39 303 $ |
| Autres revenus | 161 174 $ |
| **Total des revenus de fonctionnement** | **5 930 672 $** |
| **Transferts et revenus d'investissement** | **19 799 872 $** |
| **Total des revenus municipaux reconnus** | **25 730 544 $** |

**Contrôle :** 5 930 672 + 19 799 872 = **25 730 544 $**. Les transferts reconnus s'élèvent à 724 172 + 19 799 872 = **20 524 044 $**.

L'expression « revenus reconnus » décrit une **constatation comptable**, **pas la réception bancaire des subventions**. Les montants d'investissement ne doivent pas être crédités au budget ordinaire des employés pour conclure artificiellement à l'équilibre. Les données de la municipalité ne prouvent **aucun versement TECQ ni PRIMEAU précis** à une facture ou à un projet.

## 3. Résultat de fonctionnement et conciliation fiscale

Les charges comptables 2025 sont de **7 021 908 $**, ventilation complète ci-dessous :

| Charge par fonction | Montant reconnu |
| --- | ---: |
| Administration générale | 1 175 575 $ |
| Sécurité publique | 557 471 $ |
| Transport | 1 586 898 $ |
| Hygiène du milieu | 1 201 826 $ |
| Santé et bien-être | 33 681 $ |
| Aménagement et développement | 288 714 $ |
| Loisirs et culture | 1 509 736 $ |
| Frais de financement | 668 007 $ |
| **Total** | **7 021 908 $** |

La même somme, **et non une dépense supplémentaire**, peut se répartir selon sa nature : **1 476 360 $ de rémunération**, **344 428 $ de charges sociales**, **2 280 274 $ de biens et services**, **668 007 $ de frais financiers**, **769 032 $ de quotes-parts**, et **1 483 807 $ d'amortissement**. Le **sous-total rémunération et cotisations patronales est de 1 820 788 $** : il est **déjà inclus dans les charges**, ne se rajoute donc pas une seconde fois, et ne devient pas une dépense admissible TECQ par le simple fait que la municipalité réalise des travaux.

Le pont fiscal S13 est :

```text
Revenus reconnus de fonctionnement                        5 930 672 $
Charges reconnues de l'exercice (amortissement compris)    7 021 908 $
Résultat de fonctionnement avant ajustements              -1 091 236 $
Ajouter amortissement non monétaire                       +1 483 807 $
Remboursement de dette retenu à des fins fiscales           -560 996 $
Affectations fiscales nettes                                +236 991 $
Excédent de fonctionnement à des fins fiscales               +68 566 $
```

**C'est un excédent calculé selon les règles fiscales municipales**, pas une preuve que **68 566 $ sont disponibles à la banque**. Le remboursement de dette **fiscal** de 560 996 $ fait partie de cette conciliation; il **ne doit pas être confondu ou additionné** au remboursement total de principal **au tableau de trésorerie** de 1 690 200 $.

## 4. Résultat d'investissement et décaissements : deux méthodes

L'annexe S14 ventile les **22 581 524 $** d'acquisitions d'immobilisations constatées en 2025, dont **21 542 601 $ sous la fonction « Hygiène du milieu »**, plus 678 478 $ en transport, 7 035 $ en santé et bien-être, 34 419 $ en aménagement et 318 991 $ en loisirs. **La rubrique environnementale ne permet pas d'attribuer toutes ces acquisitions au seul chantier de Gascons** sans grand livre et décomptes de travaux.

Le résultat fiscal d'investissement :

```text
Revenus d'investissement reconnus                          19 799 872 $
Acquisitions d'immobilisations constatées                 -22 581 524 $
Financement à long terme des activités d'investissement      +650 000 $
Affectations aux investissements                              +286 340 $
Déficit d'investissement à des fins fiscales               -1 845 312 $
```

La comptabilité des flux de trésorerie donne un **décaissement pour acquisitions de 16 969 080 $**, **différent** des acquisitions comptabilisées de 22 581 524 $. La conciliation entre les deux montants dans le dossier G0.16r est :

**22 581 524 $ d'acquisitions constatées − 5 612 444 $ de factures d'immobilisations non encore payées = 16 969 080 $ de décaissements d'acquisition.**

Les **5 612 444 $** sont une dette envers des fournisseurs, pas de la trésorerie libre. Le bilan inscrit aussi **22 138 647 $ d'ajouts d'immobilisations en cours**, dont la valeur doit être examinée avec le coût d'achèvement, les obligations et les dates de mise en service.

**Le déficit fiscal d'investissement de 1,845 M$ ne correspond pas au décaissement d'immobilisations de 16,969 M$, ni à un trou bancaire automatiquement financé par Nova.**

## 5. État des flux de trésorerie : identité vérifiable de 2025

| Flux réel de trésorerie, municipalité entière | 2025 |
| --- | ---: |
| Encaisse au 1er janvier | 549 175 $ |
| Flux nets des activités de fonctionnement | +2 095 979 $ |
| Paiements d'acquisition d'immobilisations | −16 969 080 $ |
| Flux nets de financement | +16 323 277 $ |
| **Variation nette de trésorerie** | **+1 450 176 $** |
| **Encaisse au 31 décembre** | **1 999 351 $** |

**Conciliation du financement :** +650 000 $ d'émissions à long terme − 1 690 200 $ de remboursements du principal + 17 429 000 $ de variation nette des emprunts temporaires − 65 523 $ de variation des frais reportés = **16 323 277 $**.

Le solde d'emprunts temporaires est passé de **1 142 000 $ fin 2024** à **18 571 000 $ fin 2025**. Le bilan comptable affiche **31 671 634 $ d'actifs financiers**, **42 198 356 $ de passifs**, soit **10 526 722 $ de dette financière nette**. Des **créances totalisant 29 672 283 $**, dont **28 617 428 $ sur le gouvernement du Québec**, ne sont **pas de la trésorerie disponible**.

Le niveau d'emprunts et de créances souligne pourquoi le suivi de projets doit **séparer engagements, factures, versements, encaissements et échéances**. Aucune conclusion de fraude, d'économie, d'insolvabilité ou de défaillance d'un projet particulier ne découle à elle seule de ces agrégats.

## 6. Application professionnelle à la réforme Nova

Ces données réelles conduisent à **six règles non négociables** pour préparer une fiscalité à deux prélèvements :

1. **Budget de fonctionnement distinct de l'investissement.** Les recettes affectées à l'investissement ne paient pas automatiquement les salaires permanents, l'entretien ou la dette.
2. **Gestion des actifs et de la main-d'œuvre.** Les coûts de cycle de vie, les réparations, les effectifs, les obligations de retraite et la réserve d'audit sur les obligations de mise hors service doivent être chiffrés, et jamais supposés nuls.
3. **Source de financement confirmée.** Chaque revenu fiscal, transfert fédéral ou provincial et subvention TECQ/PRIMEAU doit avoir un statut distinguant l'annonce, l'engagement, la reconnaissance comptable et l'argent reçu.
4. **Comptabilité sans double compte.** Les fonctions et les natures de charges sont deux vues des mêmes dépenses; les transferts entre administrations doivent être rapprochés et neutralisés une seule fois dans un bilan consolidé.
5. **Régimes constitutionnels distincts.** Le Québec dans le Canada ne peut abolir seul les impôts fédéraux; le Québec souverain doit chiffrer les recettes, responsabilités nationales, dette, pensions et accords, sans préjuger du maintien des transferts.
6. **Aucune hausse du score sur une documentation supplémentaire seule.** Seules des assiettes réelles, des coûts complets, des flux prouvés et des revues indépendantes peuvent fermer les critères financiers.

Le **rapport municipal 2025 ne fournit pas le budget total du Québec**, et **ses montants ne peuvent être appliqués par multiplication à toutes les communes**. Le projet gouvernemental Nova sur dix ans, dans ses deux variantes, reste **sans soldes budgétaires vérifiés**.

## 7. Livrables, preuve logicielle et prochaine étape

- `data/g017f-rapprochement-municipal-fonctionnement-investissement-tresorerie-2025.json` : revenus par affectation, charges par fonction et nature, conciliation fiscale, capital et flux de trésorerie, bilan, réserves et dix exercices de modèle Nova sans chiffres inventés.
- `assets/g017f-municipal-two-ledger-core.mjs` : contrôle des identités de deux rapprochements, des charges, des créances, de la dette, des limites de source et des points de validation.
- `tests/g017f-municipal-two-ledger.test.mjs` : **76 tests** sur la provenance et les rapprochements, dont les cas de rejet des faux versements, de l'excédent fictivement encaissé et des budgets Nova inventés. Le résultat du test doit être distingué de la certification des finances; l'exécution native GitHub Actions est un contrôle technique distinct.

**Décision G0.17f :** premier rapprochement complet **fonctionnement / investissement / fiscalité municipale / trésorerie** construit avec une source publique officielle, pour un cas réel limité. **Le programme Nova–Sinjira reste à 47/100, 53 points à obtenir.**

**Suite G0.17g :** obtenir, quand disponibles, les fichiers de comptes réels MAMH 2024/2025, les déclarations de coûts d'eau 2024 et les justificatifs de subventions et d'actifs pour produire un modèle de fonctionnement et d'investissement **à périmètre constant sur dix ans**, puis l'examiner avec un spécialiste indépendant.
