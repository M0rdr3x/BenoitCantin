# P53F — Rapprochement des quotes-parts et transferts municipaux, 2024

Source : [MAMH, données réelles 2024](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents) et [manuel comptable](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/manuel). Observations historiques, uniquement les **1 094 municipalités locales**.

| Poste distinct | Montant signé CAD |
|---|---:|
| Taxes CRIIX00406 | 17 337 284 213 |
| Quotes-parts CRIIX00408 | 846 987 123 |
| Transferts CRIIX00409 | 5 376 508 934 |
| Autres catégories (différence) | 8 806 843 291 |
| **Revenus totaux CRIIX00405** | **32 367 623 561** |

Les **6 223 496 057 $ de quotes-parts et transferts** sont des écritures candidates à apparier. **Aucune opération n'a été rapprochée de sa contrepartie payeuse. Aucune élimination n'est certifiée.** Le montant à retrancher reste **inconnu**, et non zéro.

Les quotes-parts comprennent 39 montants négatifs, 298 zéros et 627 blancs; les transferts comportent un montant négatif et neuf blancs. Les comptes sont additionnés avec leur signe, sans confondre un champ vide avec un zéro déclaré.

Les taxes foncières de 15 085 531 572 $ sont incluses dans le total des taxes. Parmi les autres catégories figurent les compensations (1 001 301 216 $) et les services rendus (4 241 481 713 $) : ils peuvent comprendre des paiements publics et ne sont pas assimilés à des ressources nettes.

Avant toute élimination, exiger : identification du payeur, du bénéficiaire, de l'exercice, du poste comptable symétrique, du montant signé, d'une pièce originale et d'un contrôle indépendant. Sans transaction réciproque, une soustraction constituerait une hypothèse sans preuve.

Les chiffres **2024** ne sont pas comparables directement au budget provincial **2026‑2027** ni aux impôts fédéraux de P53C. Ils excluent MRC, régies et transports publics; la consolidation de toutes les administrations n'est pas effectuée.

Exécuter : `python scripts/auditer_flux_interadministrations_nova_p53f.py --rapport p53f_bilan.json --export-csv p53f_journal.csv`; le mode `--exiger-appariements` doit refuser la certification avec code 3. La décision reste `NO_GO_AUTOMATIQUE`. Les 20 preuves F01–F20 et les 1 320 paramètres financiers Nova restent non validés.
