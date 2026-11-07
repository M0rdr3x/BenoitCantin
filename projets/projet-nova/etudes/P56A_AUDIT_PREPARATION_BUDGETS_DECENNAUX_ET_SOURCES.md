# Projet Nova — P56A : audit de préparation des budgets décennaux 2027–2036

**7 novembre 2026 — étude de contrôle, non adoptée et non certifiée.**  
**Périmètre :** deux cadres constitutionnels distincts (Québec dans le Canada; Québec souverain hypothétique), trois trajectoires (central, prudent, stress), exercices 2027–2036 inclus.

## 1. Décision méthodologique

Le modèle décennal **existe déjà** sous P52B. Nous **n'en créons pas un deuxième**, qui risquerait d'inventer une série fiscale et d'introduire des doublons. P56A effectue un **audit indépendant de lisibilité et de complétude technique** du gabarit P52B, en réutilisant ses validations de périmètre et le registre P52A. Ce n'est pas un audit comptable indépendant.

Le fichier source de référence reste `projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json`. Son programme actuel est `scripts/evaluer_transition_fiscale_nova_p52b.py`. La nouvelle commande est `scripts/auditer_preparation_budget_decennal_nova_p56a.py`. Aucun des fichiers d'entrée existants n'est modifié.

## 2. Constat quantifié sur le modèle P52B actuel

- **2 régimes × 3 trajectoires × 10 exercices = 60 lignes annuelles.**
- **11 postes financiers par ligne = 660 montants théoriques.**
- **600 montants actuellement inconnus (`null`)**; ils ne peuvent être calculés comme zéro.
- **60 hypothèses prudentes à zéro** pour le seul poste de récupération anti-évasion additionnelle : ce ne sont ni des recettes confirmées ni une preuve d'absence d'évasion.
- **240 déclarations de validation non remplies** (60 lignes × quatre garde-fous : périmètre, incidence des ménages, emplois/services, inventaire des prélèvements).
- **120 conditions de prudence budgétaire non renseignées** (solde de l'année précédente et ratio dette nette/PIB).
- **20 preuves fiscales P52A toujours non validées.**
- **0 année-scénario complètement renseignée**; aucun solde annuel complet, aucune comparaison décennale complète.
- **0 preuve d'expertise indépendante ou de faisabilité certifiée.**
- Évaluation interne inchangée **P55N : 53 %**, fourchette prudente 45–60 %.

La somme des dépenses et des recettes du *modèle Nova de travail* 2026–2027 constitue uniquement un **écart arithmétique de −4,265 G$** (166,492 G$ − 170,757 G$). **Cet écart n'est pas le solde budgétaire officiel.** Les dépenses de 170,757 G$ comprennent déjà, dans cette présentation, un service indicatif de la dette de 10,268 G$ : P56A interdit d'en déduire un besoin additionnel de 10,268 G$. Ces valeurs ne sont pas rapprochées des versions officielles à jour et ne servent **pas** de ligne 2027–2036.

## 3. Sources officielles identifiées — pas de chiffres transposés sans rapprochement

Les sources listées ci-dessous sont des sources de vérification future, **pas des avis indépendants signés sur Nova** :

1. [Ministère des Finances — Budget du Québec 2026–2027](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf) : structure comptable, revenus/dépenses, traitements de la dette et hypothèses.
2. [Publications du ministère des Finances](https://www.quebec.ca/gouvernement/ministeres-organismes/finances/publications) : **rapport préélectoral 2026** et outil de simulation dont un amendement est signalé au **3 septembre 2026**; **rapport sur la situation financière du premier trimestre 2026–2027** daté du **25 septembre 2026**.
3. [Comptes publics du Québec](https://www.quebec.ca/gouvernement/finances-publiques/budget-comptes-publics/comptes-publics/volumes-comptes-publics) : données consolidées réellement constatées, entités, fonds spéciaux, différence entre solde budgétaire et résultat comptable.
4. [Résultats préliminaires de 2025–2026](https://www.quebec.ca/nouvelles/actualites/details/rapport-sur-la-situation-financiere-du-quebec-resultats-preliminaires-de-2025-2026-71070) : **préliminaires**, à ne pas appeler « audités ».

**Alerte temporelle :** le budget initial, l'outil préélectoral amendé, le premier trimestre et les comptes audités n'ont ni la même date, ni les mêmes hypothèses, ni nécessairement le même périmètre. Il faut rapprocher chaque poste et documenter tout reclassement, sans assembler des chiffres de versions différentes.

## 4. Deux cadres juridiques et comptables à ne jamais mélanger

### Québec dans le Canada

Les recettes et dépenses québécoises sont étudiées dans les pouvoirs provinciaux. Les **impôts fédéraux, la TPS, les droits de douane et les prestations fédérales ne disparaissent pas par simple décision provinciale**. Les transferts du gouvernement fédéral reçus par Québec ne doivent pas être comptés une seconde fois en recettes consolidées. Les dépenses gouvernementales, fonds spéciaux et municipalités exigent élimination des opérations intragroupe et preuve de financement des services. Le slogan « deux taxes pour toute l'économie » ne peut donc être certifié sur ce périmètre.

### Québec souverain hypothétique

Les recettes fédérales éventuellement transférables, les impôts, les actifs/passifs, la monnaie, les prestations de pension, l'administration des frontières, la diplomatie, les douanes et la défense sont **inconnus tant que la chaîne juridique et financière ne les établit pas**. Le simple retrait d'un transfert fédéral ou ajout d'une dépense fédérale ne constitue pas un budget de souveraineté. Les coûts de transition, de l'endettement et du maintien des droits doivent être scénarisés avec réserves et hypothèses contradictoires.

## 5. Document d'entrée obligatoire pour chaque poste

Le registre `P56A_REGISTRE_SOURCES_ET_POSTES_DECENNAUX.json` énumère les **22 couples régime–poste** (11 × 2), la preuve requise et les dossiers P52A associés. Pour qu'un champ passe de `null` à un chiffre, il faut au minimum : unité, exercice, périmètre institutionnel, valeur nette ou brute explicitée, type de source (budget initial, rapport préélectoral, situation provisoire, comptes audités, estimation candidate), page/table/date, sens de l'opération, contrepartie intergouvernementale, cohérence avec les postes voisins et révision indépendante.

Les sources en ligne ne sont **pas authentifiées par le script** : même une URL crédible ne constitue pas une certification. Une case `true` saisie par un opérateur n'a aucune valeur de rapport professionnel. Les données confidentielles de contribuables, entreprises ou salariés ne doivent pas être versées au dépôt.

## 6. Garde-fous et exécution

```bash
python scripts/auditer_preparation_budget_decennal_nova_p56a.py \
  --gabarit projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json \
  --registre projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json
```

La commande produit une ventilation des manques par **année, régime et poste** et 60 tableaux annuels contrôlables. Le mode `--exiger-budget-certifie` rend un **code de sortie 3** : aucune preuve indépendante ne permet d'autoriser un budget. Un rapport existant ne sera pas écrasé. Le script ne remplit aucun montant et ne déclenche aucun traitement externe.

**Plan de clôture de N01** : (i) rapprocher le modèle Nova avec les sources officielles et les mises à jour 2026; (ii) établir une nomenclature consolidée sans doubles comptes; (iii) obtenir les assiettes fiscales et conséquences sur ménages/entreprises; (iv) chiffrer droits acquis, services et transition, séparément par régime; (v) produire trois jeux de projections de 10 ans avec stress et dette; (vi) obtenir des audits indépendants contradictoires et une décision formelle.

## 7. Décision et suite

Le jalon **P56A est un audit de la structure et des manques**, pas un premier « budget complet ». Les **600 inconnues P52B** et les **720 incidences P52D** restent non levées. Aucune économie candidate 2,49 / 1,26 / 0,38 G$ ne devient une économie certifiée par ce travail.

La prochaine étape **P56B** devrait traiter l'extraction et le rapprochement des **données officielles sourcées** (budget, préélectoral corrigé, comptes publics et état trimestriel), en documentant précisément les dates et le périmètre de chaque série. Il faut préférer cette preuve documentaire aux nouveaux calculateurs purement fictifs.

**Décision : `NO_GO_AUTOMATIQUE`.** Aucun taux adopté, aucune abolition fiscale, aucune protection des emplois ou services levée, aucune nouvelle dépense, aucun contact externe, aucune fusion dans `main`, aucune modification de SINJIRA ni de contenu public.
