# Projet Nova — P52B : mode d'emploi du simulateur fiscal à données manquantes explicites

**Version :** P52B-1 · **Date :** 18 octobre 2026 · **Statut :** étude technique candidate, non adoptée · **Décision : NO_GO**

## 1. Objet et portée

Cette simulation opérationnalise [l'étude de faisabilité P52A](./P52A_FAISABILITE_FISCALE_DEUX_REGIMES.md), sans adopter un taux fiscal, abolir un prélèvement, publier une réforme ni garantir de résultat. Elle sépare les deux régimes constitutionnels et trois trajectoires de prudence sur **dix exercices annuels** (début 2027 à 2036 inclus). L'outil ne touche à aucun site, formulaire, compte de contribuable ou système de paiement.

Le modèle de référence contient uniquement les **montants déjà présentés par le cadre financier public Nova du 26 août 2026** : revenus consolidés 166,492 G$, dépenses consolidées 170,757 G$, service de la dette indicatif 10,268 G$ et dette nette de départ utilisée 245,335 G$. Ces chiffres restent **non certifiés**. La différence arithmétique de **-4,265 G$** n'est **pas** présentée comme le solde budgétaire officiel du Québec, et le service de la dette n'est jamais ajouté automatiquement une deuxième fois.

## 2. Organisation des données

Fichier source : `P52B_GABARIT_MODELE_DECENNAL.json`. Le gabarit possède **60 lignes** : deux régimes × trois trajectoires × dix exercices. Chaque ligne a :

- cinq postes de recettes nettes : impôt sur les revenus, récupération additionnelle anti-évasion, revenus non fiscaux, transferts fédéraux nets, autres prélèvements provinciaux résiduels;
- six postes de dépenses nettes **mutuellement exclusifs par construction de l'inventaire futur** : services existants hors dette et municipalités, service de la dette, transferts municipaux, nouvelles fonctions souveraines, coûts de transition, provision de crise;
- des références sources pour **chaque montant** présent, y compris le zéro;
- des entrées distinctes pour le solde budgétaire antérieur et le ratio dette nette / PIB, nécessaires aux conditions de prudence;
- quatre déclarations de périmètre : réconciliation des postes, incidence sur les ménages, protection emplois/services et exhaustivité des prélèvements.

**Champ `null` = inconnu, jamais zéro présumé.** Les montants sont des **chaînes décimales en milliards de dollars canadiens**, pas des nombres JSON flottants. Exemple : `"12.500"` indique 12,5 G$; un champ sans source de provenance n'est pas recevable.

Le seul montant rempli par défaut est `anti_evasion_additionnelle_nette: "0"`, avec la provenance `HYPOTHESE_PRUDENTE_ZERO_NON_CERTIFIEE`. Cela signifie **absence de rendement supplémentaire présumé**, non absence d'évasion fiscale ni une prévision de produit fiscal. Un montant positif de ce poste exige un futur protocole certifié; il est refusé par la version P52B.

## 3. Régimes et scénarios : contraintes explicites

**Québec dans le Canada** : la simulation couvre les recettes et charges de l'État québécois; elle ne suppose pas la disparition des impôts, TPS ou droits fédéraux. Même si les recettes provinciales sont modélisées avec deux prélèvements principaux, il ne faut **jamais annoncer deux taxes au total dans toute l'économie québécoise** sur la seule base de pouvoirs provinciaux.

**Québec souverain** : la simulation ne part pas du principe que les recettes fédérales actuelles sont automatiquement transférées ou que les fonctions de défense, frontières, monnaie, pensions, diplomatie et systèmes administratifs sont gratuites. Chaque entrée demeure inconnue jusqu'à preuve documentaire.

Les trajectoires **centrale, prudente et stress** contiennent les mêmes catégories de données et doivent être remplies **séparément** : on ne déduit pas le scénario prudent du scénario central par une réduction arbitraire en pourcentage. Les années 1, 3, 5 et 10 doivent être examinées, avec l'ensemble des dix années pour continuité.

## 4. Formules et garde-fous

Sur **une ligne annuelle entièrement documentée seulement** :

`recettes_nettes = somme(des 5 postes de recettes)`

`depenses_nettes = somme(des 6 postes de dépenses)`

`solde_simule = recettes_nettes - depenses_nettes`

La validité de l'addition repose sur une réconciliation indépendante de l'inventaire : **un même poste ne peut exister dans deux catégories**. Le script ne peut pas auditer la réalité économique d'une classification à partir du seul nom du champ.

La condition de prudence financière est cumulative : **solde budgétaire précédent non négatif et dette nette au plus de 45 % du PIB**. Le calcul d'une année ne dispense jamais d'examiner les engagements pluriannuels, le revenu disponible, les services, l'emploi, les municipalités, la concurrence internationale et la légalité de l'instrument fiscal.

Si un montant, une source, une année, une trajectoire ou une compétence est absent, l'outil refuse toute projection annuelle complète. Si toutes les données sont présentes, il peut produire un **calcul conditionnel à auditer**, et non un budget certifié ni un taux adopté. La présence de prélèvements provinciaux résiduels non nuls interdit de qualifier la simulation de modèle provincial à deux prélèvements.

## 5. Commandes, codes de sortie et interprétation

Depuis la racine du dépôt, pour produire un rapport local non nominatif :

```bash
python scripts/evaluer_transition_fiscale_nova_p52b.py \
  --gabarit projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json \
  --registre projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json \
  --rapport p52b_rapport_local.json
```

Mode de contrôle strict, qui **doit échouer avec code 3** avec le gabarit initial :

```bash
python scripts/evaluer_transition_fiscale_nova_p52b.py \
  --gabarit projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json \
  --registre projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json \
  --exiger-completude --rapport p52b_rapport_strict_local.json
```

Les codes `0` (rapport généré), `2` (fichier ou données invalides) et `3` (complétude refusée) sont **des résultats logiciels**, jamais une décision démocratique. Même avec un code `0`, le rapport contient `NO_GO_AUTOMATIQUE` et `publication_autorisee:false`.

## 6. Ce que la première exécution doit démontrer

Au point de départ, **600 entrées financières sont inconnues** sur les 60 exercices-scénarios (10 postes par ligne; la récupération anti-évasion additionnelle est connue comme hypothèse conservatrice de zéro). Les **20 preuves P52A restent non validées**. Il n'existe aucune projection annuelle calculable dans le gabarit initial, aucun taux prescrit et aucune décision d'adoption.

Le nombre 600 décrit les entrées encore à documenter du **gabarit**, pas « 600 preuves juridiques manquantes »; les vingt exigences de fond P52A constituent un registre distinct.

## 7. Règles de validation indépendante

Une candidature future au statut `VALIDE` dans le registre P52A doit être accompagnée d'une preuve indépendante documentaire vérifiable et de son responsable habilité; **un simple mot `VALIDE` ne suffit pas**. Les montants demandent aussi leurs références et doivent être rapprochés du bon périmètre comptable. La présente version refuse de publier automatiquement, même en cas de remplissage intégral.

Les documents source prioritaires **`official/reference/programme.md` et `official/reference/finances.md` restent inchangés**; une hypothèse P52B ne remplace ni leur statut ni leur règle de prudence. Aucun taux « nécessaire » ne peut être défini sans simulations par revenus des personnes, profits des entreprises, répercussions, droits acquis et obligations souveraines.

## 8. Travail restant pour la décision réelle

Le registre P52A requiert des analyses de fiscalistes, finances publiques, droit constitutionnel, finances municipales, droit commercial, répartition des revenus et protection des données. Il faut particulièrement valider les limites des pouvoirs provinciaux, la reprise des charges fédérales, la non-confusion entre impôts, taxes, cotisations et vrais frais, les résultats pour ménages modestes et PME, ainsi que les coûts de transition.

Le dépôt partagé avec SINJIRA ne peut subir de changement de sécurité ou de publication par ce modèle. Les blocages humains de la [PR672](https://github.com/M0rdr3x/BenoitCantin/pull/672), les [issues #135](https://github.com/M0rdr3x/BenoitCantin/issues/135) et [#662](https://github.com/M0rdr3x/BenoitCantin/issues/662) restent entiers. **PR640 : NE PAS FUSIONNER.**

**Statut : simulation conditionnelle, non adoptée, non certifiée, NO_GO d'activation.**
