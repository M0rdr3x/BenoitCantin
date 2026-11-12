# P56D — Flux entre l'État du Québec et les municipalités : consolidation, droits et financement

**7 novembre 2026 — Étude technique candidate, non adoptée, non certifiée.**  
**Objectif :** compléter P56C par un registre des obligations et un contrôle des transferts entre périmètres comptables, sans les transformer en économies fictives. Les 600 montants P52B et 720 incidences P52D restent inconnus. **P55N : 53 % estimatifs (fourchette 45–60 %).**

## 1. Motif comptable, juridique et économique

Les [Comptes publics du Québec, volumes 1 et 2](https://www.quebec.ca/gouvernement/finances-publiques/budget-comptes-publics/comptes-publics/volumes-comptes-publics) n'ont pas la même population ni les mêmes règles de présentation. Le **volume 1** consolide les entités contrôlées par le gouvernement et élimine les opérations internes; le **volume 2** présente notamment les autorisations budgétaires du fonds général et des fonds spéciaux et peut présenter des flux qui disparaissent lors de la consolidation.

Les [organismes municipaux consolident leur propre périmètre](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/normes-comptables). Ils disposent aussi de [sources légales de fiscalité foncière, de tarification et de redevances](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/fiscalite/encadrement), qui **ne sont pas automatiquement supprimées** par un projet de réforme provinciale.

Le [Budget du Québec 2026-2027, section F.73](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf) décrit **environ 1,7 G$ par année de transferts fiscaux aux municipalités**, dont le partage de la croissance d'un point de TVQ. Il distingue ces transferts de ceux visant les infrastructures. Ce montant est un **ordre de grandeur tiré de la présentation budgétaire de mars 2026**, pas un résultat 2026-2027 audité, pas la somme de toute la fiscalité municipale, ni une recette supplémentaire disponible pour Nova. Le montant n'est pas injecté dans P52B.

## 2. Trois notions différentes à ne jamais mélanger

1. **Compte de l'État du Québec :** une aide versée du gouvernement provincial à une municipalité qui ne fait pas partie du périmètre consolidé demeure une **dépense provinciale**.
2. **Vue analytique élargie Québec + municipalités :** le même transfert est une opération interne et s'élimine **uniquement dans ce regroupement hypothétique**. Les dépenses réelles de la municipalité envers des fournisseurs, le personnel et les habitants ne disparaissent pas.
3. **Économie réelle :** exige une diminution documentée du coût net de ressources utilisées, sans réduction du service ou du personnel protégé ni transfert de charge vers un autre organisme, avec une preuve indépendante. **L'élimination comptable seule vaut zéro comme preuve d'économie.**

La vue provinciale et la vue analytique élargie de l'exemple ne constituent pas une nouvelle convention officielle des Comptes publics. La classification réelle des organismes et des régimes fiduciaires doit être effectuée sur les listes et rapports de la bonne année, notamment [le périmètre comptable et les fiduciaires](https://www.quebec.ca/gouvernement/finances-publiques/budget-comptes-publics/comptes-publics/perimetre-comptable-fiduciaires-gouvernement).

## 3. Exemple exclusivement fictif de rapprochement

Le fichier P56D_EXEMPLE_FICTIF_FLUX_INTERENTITES_2026_2027.json contient **12 flux fictifs** et **9 entités fictives ou catégories analytiques**. Aucun montant n'a été observé dans les comptes publics. Il simule un transfert provincial de **100 M$** à une municipalité, les achats et salaires de cette municipalité, un apport fédéral fictif, un emprunt et un fonds interne affecté.

| Vue sur les mêmes 12 flux fictifs (M$) | État québécois fictif | Ensemble Québec + municipalités fictif |
|---|---:|---:|
| Revenus externes observés dans l'exemple | 40,00 | 250,00 |
| Dépenses externes observées dans l'exemple | 155,00 | 167,00 |
| Solde arithmétique partiel de l'exemple | −115,00 | +83,00 |
| Transferts internes éliminés du seul périmètre considéré | 30,00 | 142,00 |
| Emprunt séparé des recettes opérationnelles | 20,00 | 20,00 |
| **Économie réelle certifiée** | **Inconnue** | **Inconnue** |

Ces **soldes incomplets** ne décrivent ni les finances du Québec ni celles d'une ville. Ils n'ont pas la même portée, ne sont pas comparables à un taux de taxe et ne démontrent aucun surplus de l'État. Le transfert provincial de 100 M$ est une dépense dans la première vue, mais une élimination dans la seconde — **il n'est une économie dans aucune des deux**. Le transfert à un fonds affecté est interne à la première vue, mais le fonds n'est pas pour autant disponible pour financer une suppression d'impôt.

Si un montant fictif manque, le rapport renvoie des **totaux nuls au sens informatique (null), jamais zéro**. Les écritures de dette ou d'emprunt sont classées séparément et ne financent pas le budget courant comme recettes fiscales.

## 4. Registre des 18 obligations non chiffrées

Le document P56D_REGISTRE_OBLIGATIONS_MUNICIPALES_SOCIALES_ET_SERVICES.json trace **18 obligations candidates à examiner** avec sources de cadrage, preuve manquante et statut non démontré. Les catégories incluent la fiscalité foncière, les transferts aux municipalités, l'eau, les routes et transports, les services d'urgence, les dettes municipales, le logement, la santé, l'éducation, la recherche, les pensions, l'assurance parentale, les accidents du travail, l'assurance-emploi fédérale, les aides temporaires aux entreprises, les fonds spéciaux, les transferts fédéraux et les nouvelles fonctions souveraines hypothétiques.

**Chaque coût net reste null.** Le registre ne prétend pas connaître la contribution de chaque régime ou le coût d'une éventuelle reprise d'obligation fédérale. Une preuve de droit acquis ou de dette sociale ne peut être remplacée par une URL générique.

## 5. Commande, garde-fous et décision

Fichiers :
- projets/projet-nova/etudes/P56D_EXEMPLE_FICTIF_FLUX_INTERENTITES_2026_2027.json
- scripts/consolider_flux_interentites_nova_p56d.py
- scripts/tests/test_consolider_flux_interentites_nova_p56d.py
- projets/projet-nova/etudes/P56D_REGISTRE_OBLIGATIONS_MUNICIPALES_SOCIALES_ET_SERVICES.json
- .github/workflows/validate-nova-p56d.yml
- cette note.

Exécution : 
\`\`\`bash
python scripts/consolider_flux_interentites_nova_p56d.py \
  --entree projets/projet-nova/etudes/P56D_EXEMPLE_FICTIF_FLUX_INTERENTITES_2026_2027.json
\`\`\`

Une demande \`--exiger-faisabilite\` refuse l'autorisation (code 3); aucun rapport existant n'est écrasé. Un contrat, une rente, un transfert, une recette fiscale ou un droit social ne peut être « effacé » par écriture comptable. Le script refuse la modification des entités, de leur classement, de la nature des flux ou d'une provenance fictive. Aucune preuve réelle n'est obtenue ni certifiée par la réussite d'un test.

## 6. Étapes pour une réconciliation réelle et une meilleure complétude

| Identifiant | Preuve à obtenir | Critère de validation |
|---|---|---|
| D-R01 | Inventaire 2025-2026 des entités de l'État et des municipalités, y compris organismes contrôlés | Périmètres, entités, versions, méthodes de consolidation authentifiés |
| D-R02 | Sommaire des transferts fiscaux municipaux et comptes municipaux audités | Rapprochement par année, destinataire, contrepartie, usage et source |
| D-R03 | Détail des crédits et transferts municipaux du gouvernement | Réconciliation volume 1 / volume 2 / municipal sans compter une opération deux fois |
| D-R04 | États et obligations des fonds spéciaux et régimes sociaux | Restrictions légales, passifs, obligations futures et disponibilités certifiés |
| D-R05 | Service de dette locale/provinciale, finances d'infrastructure | Dette, intérêts, remboursements, financements et actifs séparés |
| D-R06 | Fiscalité foncière, scolaire et tarification municipale | Garantie du financement des services et de l'autonomie locale sous réforme |
| D-R07 | Analyse de pouvoir d'achat, services, salaires, droits acquis | Aucun transfert de coût caché vers ménages, travailleurs ou municipalités |
| D-R08 | Avis indépendants financier, juridique, municipal et actuariel | Rapports signés, réserves explicites et corrections suivies |

**Prochaine étape candidate : P56E**, obtenir les lignes officielles des transferts municipaux et les comptes municipaux 2025-2026 au bon périmètre, puis produire un tableau de contreparties traçable. Les études provinciales (Québec dans le Canada) et souveraines doivent toujours être traitées séparément.

**P55N = 53 % estimatifs, sans revalorisation.** Les 600 inconnues P52B, 720 incidences P52D et vingt preuves fiscales P52A restent ouvertes. La réussite du modèle ne justifie aucun taux Nova, aucune abolition, aucun nouveau financement, aucune diminution d'emploi ni aucune déclaration de programme entièrement financé.

**Décision maintenue : NO_GO_AUTOMATIQUE.** Aucun changement du programme public, de SINJIRA ou de la branche main; aucune fusion de la PR, aucune dépense, aucun contact extérieur.
