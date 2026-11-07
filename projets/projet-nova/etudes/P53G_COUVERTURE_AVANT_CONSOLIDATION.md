# P53G — Couverture des 1 343 organismes municipaux dans les comptes MAMH 2024

**État : observation historique non consolidée — aucun revenu fiscal supplémentaire garanti.**

Le [MAMH publie les comptes des organismes municipaux](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier), ainsi que les [données ouvertes des états financiers](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents). Une copie du CSV complet « Données réelles 2024 — Simple occurrence » (20 254 172 octets, SHA-256 `151c0a2b1fc0dfac8c8cc3dba04b74f5c49fbb98fdfd78251925959d1ad35fff`) a été téléchargée et contrôlée au moment de l'extraction. Elle n'est **pas** intégralement archivée sur GitHub : seuls les deux extraits sélectionnés sont disponibles et contrôlés par leur propre empreinte.

## Recettes brutes historiques des entités présentes dans le jeu de données

| Nature des organismes | Nombre | Revenus bruts CAD |
|---|---:|---:|
| Municipalités locales | 1 094 | 32 367 623 561 |
| MRC | 85 | 1 417 481 157 |
| Régies intermunicipales | 150 | 636 013 686 |
| Organismes publics de transport | 12 | 7 122 045 861 |
| Communautés métropolitaines | 2 | 120 512 321 |
| **Total avant toute élimination** | **1 343** | **41 663 676 586** |

Les **249 organismes supplémentaires** représentent **9 296 053 025 $ de recettes comptables brutes**. L'extrait P53G (`sources/P53G_MAMH_2024_249_ORGANISMES_COMPLEMENTAIRES.csv`) compte 249 lignes et 18 colonnes, soit 32 233 octets, SHA-256 `65e3bb97fd9a8bb3bfb16eef77f35036e60cb53a0796cdd491894ad7267db9b0`. Avec les 1 094 lignes P53E, il reconstitue les cinq catégories d'organismes et permet de vérifier pour les **1 343 lignes** l'égalité entre total des revenus et somme des douze catégories de recettes comptables.

Sur l'ensemble des 1 343 organismes, les **quotes-parts reçues** atteignent **3 148 209 097 $** et les **transferts reçus** **7 716 073 104 $**, soit **10 864 282 201 $ d'écritures à examiner**. Ce n'est **pas une somme à éliminer ou une économie** : les sources ne comportent pas d'appariements réciproques de dépenses et de recettes entre payeurs et bénéficiaires. Les rapports financiers peuvent déjà intégrer des organismes contrôlés, avec leurs propres éliminations comptables internes. <Voir les règles de présentation financière officielles : https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/formulaires-financiers>.

Le total de **41,664 milliards** ne peut être additionné aux recettes provinciales 2026‑2027 sans rapprocher les exercices, les compétences et les transferts. Les postes vides ne sont pas des recettes nulles constatées, et les montants négatifs sont conservés tels qu'ils sont enregistrés.

## Contrôle reproductible

```bash
python scripts/valider_couverture_organismes_nova_p53g.py --rapport p53g_bilan.json --export-csv p53g_recapitulatif_types.csv
python scripts/valider_couverture_organismes_nova_p53g.py --exiger-consolidation
```

Code **0** : couverture historique cohérente avec statut `NO_GO_AUTOMATIQUE`. Code **2** : incohérence de source, empreinte ou rapprochement. Code **3** : refus de certifier une consolidation non effectuée. Aucun taux Nova, rendement anti-évasion ou décision fiscale n'est adopté. La PR #673 reste en brouillon, les 20 preuves F01–F20 et les 1 320 inconnues financières restant à compléter.
