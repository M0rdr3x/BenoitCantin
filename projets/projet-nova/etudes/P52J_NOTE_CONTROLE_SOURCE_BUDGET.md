# Projet Nova — P52J : relecture primaire du budget 2026-2027 et rapprochement des 39 montants

**19 octobre 2026 — Étude candidate, lecture documentaire assistée, NON CERTIFIÉE, NON ADOPTÉE, NO_GO.**

## 1. Progrès réel depuis P52I
P52I recense huit **pistes** officielles sans attestation indépendante. P52J prend deux documents primaires du ministère des Finances du Québec et relève les montants de leurs tableaux publiés, en préservant des mentions d'origine et la distinction entre **preuve de la référence publique** et **preuve de la réforme Nova**.

La lecture ciblée de documents primaires réalisée au cours de la préparation de ce jalon confirme visuellement :
- 21 lignes de revenus et huit sous-totaux/agrégats du **Discours sur le budget 2026-2027**, tableau 3, page imprimée **27**, index PDF **29**;
- dix agrégats signés du **Plan budgétaire 2026-2027**, tableau **F.2**, page imprimée **F.9**, index PDF **277**.

Les URLs exactes, pages, unités, valeurs et limites sont figées dans `P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json`. Il s'agit d'une **relecture assistée à partir d'originaux publics**, **pas** d'une signature d'un réviseur externe, d'un PDF archivé/horodaté ou d'un audit comptable. Aucune donnée par ménage ni ligne fiscale personnelle n'est recueillie.

**Sources officielles utilisées :**
- https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf — tableau 3, p. 27;
- https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf — tableau F.2, p. F.9.

## 2. Recoupements et signaux d'alerte

La transcription primaire figée est vérifiée par `scripts/controler_relecture_budget_nova_p52j.py` face à `P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json` et à l'état **non validé** de F09 dans P52A et P52I.

- Les **21 lignes** de recettes, leur **ordre**, leurs identifiants, leurs unités et les **8 agrégats** doivent correspondre exactement; aucune moyenne, tolérance silencieuse ou correspondance par seul libellé n'est admise.
- Les **10 lignes** du tableau F.2 sont conservées **avec leur signe imprimé**. Les dépenses et ajustements négatifs du document primaire ne doivent pas devenir des revenus; la conversion vers les dépenses positives dans P52C est explicite.
- Sont recalculés les sommes par groupes de taxes/revenus, les revenus totaux, les dépenses et la transition entre écart comptable brut, provision, déficit comptable et solde au sens de la Loi sur l'équilibre budgétaire.
- Les **transferts fédéraux** restent distincts des impôts provinciaux, les **recettes d'entreprises publiques** ne sont pas des impôts sur le revenu, et la catégorie **taxes de vente** (26 349 M$) **n'est pas assimilable à la seule TVQ**.

### Contrôle explicite du déficit (millions CAD)
```text
Revenus totaux                              166 492
Dépenses des portefeuilles                 -160 489
Service de la dette                         -10 268
Écart arithmétique avant provision           -4 265
Provision pour éventualités                  -2 000
Déficit comptable                            -6 265
Fonds des générations                        -2 347
Solde budgétaire au sens de la Loi           -8 612
```
Ne pas compter une deuxième fois le service de la dette; ne pas présenter **−4 265 M$** comme le déficit légal **−8 612 M$**. Ces données sont des **prévisions de mars 2026**, pas les réalisations finales, et n'intègrent pas automatiquement les administrations municipale ou fédérale.

## 3. Ce que le contrôle permet de conclure
**Oui :** la version actuelle de P52C concorde avec les montants des deux tableaux primaires relevés, et le rapprochement mécanique détecte des altérations. Une lecture des chiffres officiels est désormais traçable dans le code et la transcription. Une personne peut refaire le relevé en suivant page et tableau.

**Non :** le recoupement local, même avec tous les tests au vert, ne vaut pas une **attestation humaine indépendante**. Il ne confirme ni l'actualité du PDF après la lecture, ni sa chaîne d'archivage cryptographique, ni les recettes nettes d'une taxe contre les paradis fiscaux. Il ne valide pas les taux, une fiscalité à deux prélèvements, une économie nette, l'absence de pertes individuelles ou les finances d'un Québec souverain.

En conséquence, **F09 conserve `NON_VALIDE`**, et les 19 autres pièces F01–F20 aussi. Les **600 montants décennaux**, les **720 montants de cas** et la nécessité d'une vraie étude de représentativité restent inchangés.

## 4. Étapes humaines obligatoires avant toute décision de fond
1. **Comptable public externe mandaté :** obtenir et conserver les deux PDF originaux, calculer leurs empreintes SHA-256, inscrire version, date de récupération, tableau, page et méthode de vérification. Refaire le double relevé en indépendance de la transcription P52C/P52J; signer les réserves.
2. **Expert en finances publiques :** rapprocher prévisions de mars 2026, mises à jour subséquentes et comptes réels, sans substituer une année à une autre. Documenter la consolidation des municipalités et du fédéral et les contreparties.
3. **Juriste fiscal :** attester séparément les compétences fiscales du Québec au Canada (et les limites TPS/douanes/fédérales), la conception de deux prélèvements, les droits des contribuables et le droit applicable à une souveraineté seulement hypothétique.
4. **Économiste indépendant avec accès légal aux données :** exécuter et vérifier les 60 trajectoires annuelles et étudier la distribution des effets sur les ménages et les entreprises, y compris les pertes potentielles.
5. **Autorité démocratique compétente :** décider après avis et consultation, selon les procédures du projet. Une réussite GitHub Actions n'autorise jamais à elle seule une adoption, une fusion ni une publication programmatique.

## 5. Contrôle logiciel et prochaine suite
Le validateur n'accède à aucun service externe, refuse toute déviation des pièces, rejette les faux statuts d'approbation, établit ses agrégats par une liste blanche et **ne donne jamais de GO**. Son code de sortie : **0** = transcription techniquement cohérente, **2** = défaut, **3** = preuve indépendante toujours requise lorsque `--exiger-attestation`.

**P52K envisagé :** préparer une chaîne de contrôle de version et d'évidence (empreintes SHA-256 de PDF acquis légalement, attestations humaines, mises à jour, conflits d'intérêts, corrections datées) puis seulement des estimations représentatives. Sans données et relecteurs, ne pas simuler leur existence.

**Gouvernance :** PR #673 reste en brouillon; pas de fusion de #640, pas de changement à SINJIRA; issues #135 (protection de main) et #662 (revues indépendantes) toujours prioritaires.
