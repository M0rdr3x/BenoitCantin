# Projet Nova — P56C : passage auditable entre les comptes publics et la nomenclature P52B

**7 novembre 2026 — étude technique candidate, non adoptée et non certifiée.**

## 1. Pourquoi ce jalon est nécessaire

Les comptes publics du Québec sont **consolidés** : ils éliminent les transactions entre les entités comprises dans le périmètre de l'État. Les données du volume 2, les budgets de ministères, les mouvements des fonds spéciaux et les transferts municipaux ne peuvent donc pas être additionnés à la somme du volume 1 sans reconstituer le périmètre et les éliminations. Le ministère explique explicitement ces divergences [dans son guide des volumes](https://www.quebec.ca/gouvernement/finances-publiques/budget-comptes-publics/comptes-publics/volumes-comptes-publics).

Les montants du **volume 1 des Comptes publics 2025-2026**, publiés le 17 juillet 2026, sont des chiffres **historiques audités**, non des prévisions 2027-2036 ni un budget du Projet Nova. Les travaux P56A et P56B ont respectivement établi 600 montants budgétaires P52B inconnus et rapproché le budget initial, le résultat préliminaire et les comptes audités 2025-2026. P56C ajoute une **ventilation de provenance**, sans inventer les montants manquants.

**Source primaire, [Comptes publics 2025-2026, volume 1](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Comptes-publics/FR/CPTFR_vol1-2025-2026.pdf)** : PDF page index 11 pour le sommaire de la page imprimée 5; PDF index 18 pour la ventilation des revenus « impôt sur le revenu et les biens » en page imprimée 12. Les pages PDF sont indiquées sous leur **indice numérique commençant à zéro** dans le registre.

## 2. Tableau des recettes historiques auditées 2025-2026

**Unités : millions de dollars canadiens (M$).**

| Sous-poste observé | M$ | Catégorie cible P52B envisagée, sans imputation |
|---|---:|---|
| Impôt des particuliers | 48 969 | Impôt sur les revenus (piste de travail; crédits à concilier) |
| Impôts des sociétés | 14 599 | Impôt sur les revenus (piste de travail; assiette à concilier) |
| Cotisations pour les services de santé | 9 304 | Autres prélèvements existants, droits à financer |
| Impôt foncier scolaire | 1 243 | Autres prélèvements existants, fiscalité scolaire à financer |
| **Sous-total « impôt sur le revenu et les biens »** | **74 115** | **Le total groupé ne s'ajoute pas aux quatre composantes !** |
| Taxes à la consommation | 29 639 | Autres prélèvements provinciaux existants |
| Droits, permis et redevances | 6 708 | À ventiler entre revenus non fiscaux et prélèvements obligatoires |
| Revenus divers | 14 922 | À ventiler; ne pas les dire tous disponibles en liquidités |
| Revenus des entreprises du gouvernement | 5 241 | Revenus non fiscaux possibles; résultats nets ≠ encaisse disponible |
| Transferts fédéraux | 29 803 | Transferts reçus dans le Québec actuel, non acquis en souveraineté |
| **Total consolidé des recettes** | **160 428** | **Correspondance vérifiée, montant historique seulement** |

**Point décisif :** les impôts des particuliers et des sociétés totalisent **63 568 M$**, pas 74 115 M$. Les **10 547 M$** d'écart correspondent aux **cotisations santé de 9 304 M$** et à l'**impôt foncier scolaire de 1 243 M$**. Aucun de ces montants ne démontre qu'un nouvel impôt sur le revenu pourrait financer le système entier. Les crédits d'impôt remboursables et les dépenses fiscales compliquent encore la comparaison des assiettes.

## 3. Tableau des dépenses historiques auditées 2025-2026

| Poste observé | M$ | Qualification |
|---|---:|---|
| Dépenses des portefeuilles | 155 782 | Santé, éducation, autres, incluant transferts de périmètres différents : impossible de verser le total dans « services hors dette et municipalités » |
| Service de la dette | 10 148 | Déjà inclus dans le total des dépenses |
| **Dépenses totales consolidées** | **165 930** | **Somme vérifiée : 155 782 + 10 148** |
| **Solde comptable** | **−5 502** | **160 428 − 165 930**, non équivalent au solde budgétaire de la Loi sur l'équilibre budgétaire |

Le solde légal après versements au Fonds des générations de **−7 791 M$** est conservé dans P56B et **n'est pas recompté** parmi les dépenses consolidées du tableau ci-dessus. De même, le service de la dette 2025-2026 ne peut être extrapolé à dix ans en multipliant par dix sans scénario de dette et de taux.

## 4. Distinctions de compétence et de financement

**Québec dans le Canada :** le gouvernement provincial ne peut pas abolir de façon unilatérale la TPS fédérale ou les impôts fédéraux. Les cotisations finançant des droits, les prélèvements scolaires, municipaux et les transactions intergouvernementales doivent être inventoriés avec incidence, bases et contreparties.

**Québec souverain hypothétique :** aucune quote-part de dette fédérale, aucun transfert de recettes, ni aucune prise en charge de prestations, fonctions ou conventions ne doit être considéré comme acquis; les négociations et instruments juridiques restent à examiner.

**Protection :** aucun gain comptable fictif ne doit se traduire par une réduction d'effectifs, de services, de rentes, de droits acquis ou de pouvoir d'achat. Les aides publiques aux entreprises sont étudiées comme mesures temporaires traçables plutôt que supprimées arbitrairement.

## 5. Livrables techniques et limites

- Table des **11 sous-postes sources sans doublons**, dont 9 postes de recettes et 2 postes de dépenses : `P56C_TABLE_PASSAGE_COMPTES_PUBLICS_VERS_P52B_2025_2026.json`.
- Auditeur : `scripts/rapprocher_comptes_publics_p52b_nova_p56c.py`, vérifiant les montants fixes, les pages, le périmètre, la répartition, les identités comptables, la concordance P56B et l'absence de transposition P52B. Les montants sont des **chaînes décimales** en M$.
- Tests : `scripts/tests/test_rapprocher_comptes_publics_p52b_nova_p56c.py` (42 cas couvrant les erreurs de double compte, de source, de millésime, de secteur et de certification).
- Workflow GitHub : `.github/workflows/validate-nova-p56c.yml`.

**Commande d'exécution depuis la racine du dépôt :**

```bash
python scripts/rapprocher_comptes_publics_p52b_nova_p56c.py \
  --table projets/projet-nova/etudes/P56C_TABLE_PASSAGE_COMPTES_PUBLICS_VERS_P52B_2025_2026.json \
  --snapshots projets/projet-nova/etudes/P56B_SNAPSHOTS_FINANCES_2025_2026_SOURCES_OFFICIELLES.json \
  --gabarit projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json \
  --registre projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json
```

Le mode `--exiger-budget-certifie` échoue avec le **code 3**, même quand tous les contrôles d'arithmétique réussissent. L'outil **ne modifie aucun gabarit**, refuse les données publiques altérées, exige le régime québécois actuellement observé, et n'écrit pas par-dessus un rapport existant. **Une signature professionnelle sur la réforme Nova n'est pas inventée par ce contrôle.**

## 6. Prochaines preuves nécessaires avant toute hausse du 53 %

**Étape P56D candidate :** obtenir une véritable ventilation *officielle source par source* des sous-postes mixtes, avec une matrice d'élimination interorganismes, obligations municipales et scolaires, fonds sociaux, transferts et actifs de sociétés d'État. Vérifier la base fiscale brute/nette et les crédits fiscaux, distinguer le résultat comptable des liquidités et relier la preuve à une seule année, puis construire des hypothèses 2027-2036 explicitement sourcées et sensibles aux chocs.

Les **600 montants P52B**, **720 incidences P52D** et **20 preuves P52A** restent ouverts. Le score estimatif **P55N reste 53 % (fourchette 45–60 %)** : les 11 montants historiques réconciliés n'ont pas renseigné les projections 2027–2036 ni fait financer Nova.

**Aucune nouvelle taxe ni suppression d'impôt n'est adoptée.** Aucun contact extérieur, dépense, publication normative, changement SINJIRA, modification de la branche `main` ou fusion de la PR. **Décision : `NO_GO_AUTOMATIQUE`.**
