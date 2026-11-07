# Projet Nova — P53A : périmètres, recettes et coût de la réforme

**2026-10-20 — Étude provisoire et non certifiée.**

## Sources et chiffres

Les montants de P53A sont les **prévisions budgétaires du gouvernement du Québec pour 2026-2027**, édition de mars 2026 : [tableau 3, discours, p. 27](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf) et [tableau F.2, plan, p. F.9](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf). P52C et P52J en contiennent déjà les lignes, reprises sans chiffres nouveaux.

| Enveloppe budgétaire | M$ |
|---|---:|
| Impôts du Québec actuels : particuliers et sociétés | 65 327 |
| Cotisations santé, foncier scolaire et taxes à la consommation | 40 731 |
| Entreprises publiques, droits, permis, redevances et divers | 28 303 |
| Transferts fédéraux reçus par Québec | 32 131 |
| **Total prévu pour le gouvernement du Québec** | **166 492** |

**65 327 + 40 731 + 28 303 + 32 131 = 166 492 M$**. Ces partitions sont disjointes : ne pas additionner à nouveau les sous-totaux officiels. Les **26 349 M$ de taxes de vente ne représentent pas seulement la TVQ**. Les 28 303 M$ incluent de nombreux revenus qui **ne sont pas des impôts**. Les 40 731 M$ ne correspondent ni à un coût certain d'abolition ni à un gain de la réforme Nova : la décision et le financement des services restent à établir.

Les dépenses officielles prévues sont **170 757 M$**, dont déjà **10 268 M$ de service de la dette**. La provision de 2 000 M$ conduit au déficit comptable de **−6 265 M$**. Les versements de 2 347 M$ au Fonds des générations donnent le solde légal de **−8 612 M$**. Ces chiffres n'autorisent aucune projection automatique de revenu disponible supplémentaire.

## Neuf lacunes non chiffrées, et non égales à zéro

Le registre `P53A_LACUNES_HORS_PERIMETRE.json` énumère impôt fédéral sur le revenu, TPS, douanes, taxes foncières municipales, autres recettes locales, RRQ, assurance-emploi, RQAP et autres régimes, ainsi que les accises fédérales. Leurs montants restent `null` : **inconnus**, et non absents de l'économie. Une source candidate pour les administrations municipales est le [tableau Statistique Canada 10-10-0020-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1010002001); aucune valeur spécifique du Québec, année et classification n'en a encore été extraite ni certifiée. Les cotisations sociales comprennent des droits à prestations et ne se suppriment pas comme de simples lignes budgétaires sans coûts de remplacement.

## Deux scénarios distincts

- **Québec dans le Canada** : le Québec ne peut supprimer unilatéralement les impôts fédéraux, la TPS ni les douanes. Les taxes locales et autres prélèvements ont leur législation et leur financement. Les revenus des entreprises publiques ne deviennent pas automatiquement une nouvelle taxe Nova.
- **Québec souverain hypothétique** : aucune indépendance ni fiscalité nationale n'est acquise, et **32 131 M$ de transferts fédéraux ne sont pas garantis**. Les nouvelles compétences, obligations, dettes, institutions et recettes doivent être étudiées dans une transition juridiquement valide.

## Contrôles et prochaines preuves

L'inventaire lie 21 postes aux sources P52C/P52J, aux questions P52Z et aux preuves F01–F20. Les neuf lacunes imposent de documenter séparément période, administration, source primaire, classification fiscale ou contributive et prévention du double compte. Les assiettes du revenu, le rendement d'une mesure anti-paradis fiscaux, les taux, les économies publiques, les services protégés et les gains nets des ménages **ne peuvent pas être déduits des seuls budgets historiques**.

Commandes :

```bash
python scripts/auditer_inventaire_recettes_nova_p53a.py --rapport p53a_bilan.json --export-csv p53a_inventaire_30_postes.csv
python scripts/auditer_inventaire_recettes_nova_p53a.py --exiger-completude
```

Le succès technique ne signifie pas une adoption politique. **20 preuves non validées, 1 320 données financières Nova inconnues, aucune expertise indépendante certifiée.** La PR #673 reste en brouillon, sans changement de `main` ni de SINJIRA, et sous **NO_GO_AUTOMATIQUE**.
