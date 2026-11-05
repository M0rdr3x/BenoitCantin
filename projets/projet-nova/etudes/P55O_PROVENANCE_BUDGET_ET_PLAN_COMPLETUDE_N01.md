# P55O — Première priorité du programme : couvrir le financement 2027–2036

**5 novembre 2026 — résultat vérifiable sur les gabarits GitHub, sans estimation arbitraire de recettes.**  
Ce dossier met en œuvre **N01**, la première priorité du baromètre P55N. Le jalon **ne fait pas monter le score estimatif de 53 %** : il organise les preuves à obtenir avant de calculer les taux, le déficit éventuel ou le gain de pouvoir d'achat.

## Faits effectivement vérifiés dans le modèle

Source : `P52B_GABARIT_MODELE_DECENNAL.json`, validée par `scripts/evaluer_transition_fiscale_nova_p52b.py`.

| Paramètre | Résultat |
|---|---:|
| Régimes constitutionnels | 2 — Québec dans le Canada; Québec souverain hypothétique |
| Trajectoires | 3 — central, prudent, stress |
| Exercice de départ | 2027–2036 inclus, 10 ans |
| Couples régime × trajectoire × exercice | **60** |
| Postes de recettes inconnus par couple | 4 |
| Postes de dépenses inconnus par couple | 6 |
| **Total de recettes inconnues** | **240** |
| **Total de dépenses inconnues** | **360** |
| **Total de montants inconnus** | **600** |
| Exercice-scénario dont le solde fiscal Nova est calculable | **0 sur 60** |
| Hypothèses de recettes anti-évasion additionnelles à « 0 » non certifié | **60** |
| Pièces de faisabilité fiscale P52A à valider indépendamment | **20** |

Le `"0"` du poste anti-évasion est **une hypothèse de prudence**, pas une recette constatée de zéro ni une preuve de recouvrement. Les dix postes `null` par exercice demeurent **inconnus**; ils ne sont ni interpolés ni estimés par le code. Il manque donc **100 montants par scénario décennal** et **300 par régime constitutionnel**, à la date de cette photographie.

## Premier point de comparaison, et ses limites

Le référentiel P52C, établi à partir des prévisions de [Québec, Budget 2026–2027](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf), recopie en **millions de dollars** :

| Recette du budget actuel 2026–2027 | Prévision |
|---|---:|
| Impôt des particuliers | 50 800 M$ |
| Impôt des sociétés | 14 527 M$ |
| **Ensemble de ces deux lignes** | **65 327 M$** |
| Taxes de vente, **agrégat et non TVQ seule** | 26 349 M$ |
| Cotisations pour services de santé | 9 412 M$ |
| Impôt foncier scolaire | 1 311 M$ |

**Lecture essentielle :** ces montants sont des **prévisions du système actuel**, non des recettes automatiquement transférables au Projet Nova et non des recettes prouvées d'un impôt unique futur. La somme 65 327 M$ **n'est pas une assiette taxable**; on ne peut pas la diviser par un taux pour déduire le taux requis. Le budget public n'a pas été audité par P55O et ces lignes ne remplacent aucun poste `null` de P52B. Les taxes de vente sont un **agrégat** et ne peuvent pas être intégralement déclarées TVQ.

## Les dix postes financiers à rendre calculables

| Code | Donnée manquante par exercice-scénario | Dossier à obtenir |
|---|---|---|
| O01 | Impôt sur les revenus net | Assiettes personnelles/entreprises, crédits et effets de conformité |
| O02 | Revenus non fiscaux nets | Dividendes, redevances, revenus affectés et consolidation |
| O03 | Transferts fédéraux nets | Ententes applicables au Québec dans le Canada; hypothèses négociées distinctes pour la souveraineté |
| O04 | Autres prélèvements provinciaux nets | Inventaire juridique et financement de remplacement, pas suppression automatique |
| O05 | Services publics existants | Santé, éducation, justice, logement, réseaux, effectifs et coûts de continuité |
| O06 | Service de la dette | Échéances et charge nette, sans ajouter deux fois la dette |
| O07 | Transferts municipaux nets | Municipalités, RTC, SOMHAC, fonds affectés et écritures réciproques |
| O08 | Nouvelles fonctions souveraines | Compétences fédérales potentielles, responsabilités et coûts négociés |
| O09 | Coûts de transition nets | Systèmes, actifs, contrats, personnel, installations, mécanismes de continuité |
| O10 | Provision de crise | Scénarios de stress, liquidités prudentes et continuité des services |

Les fiches O01–O10, dans le référentiel JSON, précisent **la nature des pièces**, les restrictions d'interprétation et les contrôles nécessaires. Ce ne sont **pas dix valeurs obtenues**, mais dix **familles de données** à instruire et à décliner sur six trajectoires décennales.

## Séquence méthodologique et protection des citoyens

1. **Réconcilier le budget de référence P52C** avec les compétences et catégories qui resteront sous le scénario Québec au Canada : les prélèvements fédéraux et les recettes municipales ne peuvent pas être supprimés d'un trait de plume provincial.
2. **Définir l'assiette et les garanties** du prélèvement unique sur les revenus : personnes, entreprises, crédits et minimum vital. Le mécanisme « anti-paradis fiscaux » exige une base juridique et un recouvrement distinct sans recettes supposées.
3. **Établir les coûts de tous les services à maintenir**, avec le financement municipal et des organismes, les réserves affectées, les pensions et les engagements. Aucune réduction d'effectifs ni compression des services n'est financée par des « éliminations » qui existent déjà en consolidation.
4. **Construire séparément les scénarios constitutionnels** et leurs responsabilités; vérifier les coûts de transition et les effets sur la dette et le pouvoir d'achat.
5. **Renseigner chaque champ avec la provenance et la date**, examiner les hypothèses contradictoires, puis seulement calculer les soldes et tester différents taux. Le passage à zéro de `null` exige une preuve explicite.
6. **Vérifier l'incidence P52D** : 720 montants par cas demeurent non renseignés, avec impossibilité actuelle de démontrer un effet général sur le pouvoir d'achat.

## Comment utiliser P55O

```bash
python scripts/auditer_couverture_financement_nova_p55o.py \
  --bilan-public /hors_git/p55o_bilan.json \
  --table-public /hors_git/p55o_table.json
```

Le programme lit en mode local, sans réseau, **P52A, P52B, P52C et P55N**. Il contrôle la structure, les années, les montants manquants, la prudence anti-évasion, l'état des 20 preuves fiscales et la distinction avec les cinq lignes du budget 2026–2027. Toute modification de données sources doit entraîner une **réévaluation explicite du diagnostic**; elle ne fait pas automatiquement monter le pourcentage du programme. Les sorties neutres ne copient aucun cas de ménage et n'ouvrent aucun accès aux données privées.

Avec `--exiger-financement-demontre`, la commande doit renvoyer **3**. Tout écart d'intégrité ou de nombre de champs retourne **2**.

### Porte de décision

**N01 est entamée, mais pas remplie.** Aucun taux, montant d'économie ou budget décennal vérifié n'est annoncé; aucun revenu fiscal additionnel de lutte anti-évasion n'est certifié. Les emplois, services, engagements et le pouvoir d'achat restent protégés. Les deux statuts constitutionnels ne sont jamais fusionnés.

**Statut : `NO_GO_AUTOMATIQUE`.** Ni modification du programme public adopté/non adopté, ni dépense, ni contact externe, ni changement SINJIRA, ni fusion dans `main`.
