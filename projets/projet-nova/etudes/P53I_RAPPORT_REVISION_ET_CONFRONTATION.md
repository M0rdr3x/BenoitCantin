# Projet Nova — P53I : contrôle des versions et pièces de charges municipales (2024)

**22 octobre 2026 — Acquisition documentaire et comparaison comptable, non approbation de la réforme Nova.**

## Changement effectivement identifié dans la source officielle

Le MAMH avertit que les [rapports financiers municipaux](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier) et les fichiers de [Données Québec](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents) peuvent être mis à jour et corrigés après transmission.

Deux téléchargements du **même fichier de l'exercice 2024** ont produit des versions différentes. La première, consultée le 21 octobre, avait **1 343 organismes**, 20 254 172 octets et SHA-256 `151c0a2b1fc0dfac8c8cc3dba04b74f5c49fbb98fdfd78251925959d1ad35fff`. La nouvelle, obtenue le **22 octobre 2026**, compte **1 344 organismes**, 20 268 526 octets et SHA-256 `fa310f380e295ae359a2aafe83beb1dd45cd4888571e133398ad51f4b7db8c43`.

Les **1 343 codes d'organismes** précédents sont encore présents : **aucun montant, nom, type ou champ n'a changé dans les 18 colonnes de l'extraction antérieure**. Un organisme **Saint-Valère**, code `39135` (municipalité locale), a été ajouté. Le code vérifie cette absence de révision par comparaison de chacune des 18 colonnes. Cela **ne garantit pas** que les milliers d'autres colonnes du fichier brut sont inchangées.

| Saint-Valère, compte 2024 ajouté | CAD |
|---|---:|
| Revenus totaux | 2 951 221 |
| Taxes | 2 276 820 |
| Taxes foncières (incluses dans taxes) | 2 069 797 |
| Transferts reçus | 503 955 |
| Quotes-parts reçues | 0 |
| Charges de quotes-parts à des organismes municipaux | 165 346 |

**La nouvelle ligne ne représente pas nécessairement une croissance économique** : il s'agit d'abord d'une **mise à jour de couverture statistique**.

## Nouveau contrôle : charges pouvant correspondre à des flux reçus

Le dictionnaire officiel des 8 003 entrées contient désormais cinq codes de **charges par objets — contributions à des organismes** qui ont été sélectionnés, avec les valeurs de **tous les 1 344 organismes** de la nouvelle source :

| Charge MAMH — réalisations 2024 | Code | Total signé (CAD) |
|---|---|---:|
| Organismes municipaux — quotes-parts | `CRIIX00681` | 2 526 339 827 |
| Organismes municipaux — transferts | `CRIIX00682` | 53 587 714 |
| Organismes municipaux — autres | `CRIIX00683` | 254 824 938 |
| Autres organismes — transferts | `CRIIX00685` | 386 907 793 |
| Autres organismes — autres | `CRIIX00686` | 816 798 326 |

Ces postes concernent le **côté payeur** à partir d'une classification des charges, mais ne comportent **aucune identité du bénéficiaire transaction par transaction**. La somme de **2 526 339 827 $** de quotes-parts versées à des organismes municipaux ne peut pas être automatiquement mise en correspondance avec **3 148 209 097 $ de quotes-parts reçues** par les organismes de l'extraction. L'écart arithmétique de **621 869 270 $** ne constitue ni une perte, ni une erreur, ni une économie, ni un montant à éliminer : les périmètres consolidés, les flux d'autres types et les écritures réciproques demeurent inconnus.

Les comptes 2024 actualisés sur les 1 344 organismes totalisent **41 666 627 807 $ de revenus comptables bruts**, dont **17 339 561 033 $ de taxes**, **3 148 209 097 $ de quotes-parts reçues** et **7 716 577 059 $ de transferts reçus**. Ces catégories sont comprises dans le total de revenus; elles ne doivent pas y être ajoutées une deuxième fois. Certains comptes ont déjà été consolidés à l'intérieur des organismes déclarants.

## Traçabilité des fichiers

Les fichiers complets MAMH (20,3 Mo et 1,75 Mo pour le dictionnaire) ont été **téléchargés et hachés**, mais leurs octets intégraux **ne sont pas archivés dans Git**. La PR contient deux **extractions dérivées versionnées et contrôlables** :

- `sources/P53I_MAMH_2024_1344_RECETTES_CHARGES_SELECTION.csv` — 1 344 organismes, les 18 champs antérieurs et cinq charges nouvelles; SHA-256 `cef644e3f16ebea6bc727b009037638fa70443fe66fbeb55e4ac1e3cb1071213`.
- `sources/P53I_MAMH_2024_DICTIONNAIRE_CHARGES.json` — 5 codes officiels des charges; SHA-256 `5ed56370bc00cd4752d3982958236093d1803e60331251afb76a24f87856ab10`.

Les 1 343 observations précédentes restent **intactes et vérifiables** dans P53E et P53G; P53I crée un nouveau point de comparaison. Un contrôle futur doit refaire le téléchargement et signaler toute différence d'empreinte et toute modification de ligne avant mise à jour des tableaux.

## Décision

**Aucune charge n'est une élimination prouvée. Aucun taux Nova n'est sélectionné.** Il manque des justificatifs de payer/bénéficiaire, la consolidation des périmètres MRC/municipalités, la comparaison des comptes provinciaux et fédéraux de même exercice, la certification indépendante et les 20 preuves F01–F20. Les **1 320 valeurs financières Nova restent inconnues**.

Commande de vérification locale : `python scripts/auditer_revision_et_charges_municipales_nova_p53i.py --rapport p53i_bilan.json`. Le mode `--exiger-appariements` doit sortir avec le code 3. La PR #673 reste brouillon, sans fusion ni publication de politique fiscale adoptée.
