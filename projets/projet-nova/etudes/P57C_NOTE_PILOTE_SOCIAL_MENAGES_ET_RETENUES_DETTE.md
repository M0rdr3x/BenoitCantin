# Projet Nova — P57C : banc d'essai du crédit pour solidarité, plafonds familiaux et protections contre les retenues pour dette

**Date : 8 novembre 2026 · Québec dans le Canada · Statut : simulation fictive non représentative · `NO_GO_AUTOMATIQUE`.**

## 1. Résultat et décision concernée

Le Projet Nova envisage de simplifier les prélèvements sans réduire les droits acquis, le revenu disponible ni la continuité des services. Pour défendre cette promesse, il faut identifier les règles qui peuvent occasionner une **perte de liquidités** ou une **suppression indirecte de prestations**. P57A a apporté la preuve du traitement comptable du crédit de solidarité en 2025-2026; P57B a fixé les trois composantes (TVQ, logement, villages nordiques) et les cadences du cycle **juillet 2026 à juin 2027**.

**P57C est un premier outil exécutable**, qui vérifie des seuils, génère les mois théoriques de versement d'un crédit fictivement déjà déterminé et établit si le **plafond de retenue de 50 % pour dette envers l'État** est explicitement applicable. **Il ne calcule pas le montant d'un crédit, n'attribue aucun droit et n'est pas une microsimulation statistique représentative.**

### Sources officielles

- [Revenu Québec — calcul du crédit d'impôt pour solidarité](https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/calcul-du-credit-dimpot-pour-solidarite/) : revenu familial de la déclaration **2025**, situation du **31 décembre 2025**, trois composantes et tableau du revenu familial maximal, **sauf règles spécifiques pour les villages nordiques**.
- [Revenu Québec — versements de juillet 2026 à juin 2027](https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/versement-du-credit-dimpot-pour-solidarite/) : versement **annuel** jusqu'à 240 $, **trimestriel** de 241 $ à 799 $ et **mensuel** à partir de 800 $.
- [Revenu Québec — limites à la saisie d'un crédit pour payer une dette envers l'État](https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/situations-limitant-lutilisation-de-vos-versements-pour-payer-une-dette-a-letat/) : si le revenu familial ayant servi au calcul est **au plus 26 190 $** pour le cycle **juillet 2026 à juin 2027**, Revenu Québec utilise **au maximum 50 % de chaque versement** pour payer une dette envers l'État. La limite de 50 % s'applique également aux personnes bénéficiant de l'**aide financière de dernier recours**, selon les dispositions publiées.
- [Revenu Québec — conditions d'admissibilité](https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/conditions-a-remplir/) : la résidence au Québec, la situation de la personne, sa déclaration et la demande complète comptent aussi. **Un revenu inférieur au plafond ne prouve pas l'admissibilité.**

Le simulateur ne remplace pas les annexes fiscales ni l'outil officiel de calcul.

## 2. Règles de seuil : séparer filtrage et attribution du droit

Pour ce cycle **2026-2027**, le tableau général du revenu familial maximal est :

| Situation familiale au 31 décembre 2025 | Maximum général | Enfants admissibles |
|---|---:|---|
| Personne sans conjoint | **64 545 $** | Aucun ajout sans statut de famille monoparentale |
| Famille monoparentale | **64 545 $** | **+2 634 $ par enfant** |
| Couple | **70 395 $** | **+2 634 $ par enfant** |
| Résidence principale en village nordique | **Tableau général non applicable** | Cas spécifique requis |

La comparaison de revenu est **indicative** : si le revenu familial atteint le maximum général, il n'y a normalement pas de droit selon ce tableau; s'il est inférieur, les autres conditions doivent toujours être vérifiées. Pour les villages nordiques, **le simulateur ne réutilise pas ce plafond**, car le régime prévoit une composante et des règles particulières.

Le programme utilise un **montant fictif déjà inscrit sur un avis hypothétique** uniquement pour déterminer la cadence de versement; il ne prétend **pas** produire ce montant à partir du revenu et des paramètres officiels. Un cas de **0 $** sous le seuil signifie simplement **aucun crédit fictif attribué dans cet essai**, pas une preuve qu'une personne réelle est inadmissible.

## 3. Dix cas entièrement fictifs

Tous les revenus et crédits ci-dessous sont **des valeurs d'essai**, non des exemples de véritables bénéficiaires ni des résultats prévus sous Nova. Aucune donnée nominative n'est utilisée.

| Cas | Hypothèse illustrative | Crédit annuel fictif | Résultat contrôlé |
|---|---|---:|---|
| **C01** | Personne seule, revenu 20 000 $, dette envers l'État | 1 200 $ | Versements mensuels; retenue au plus **600 $ au total** si 50 % de chaque versement, jamais une retenue présumée |
| **C02** | Famille monoparentale, 1 enfant, revenu 30 000 $ | 799 $ | Versements trimestriels, **3** avant fin mars, **1** en avril |
| **C03** | Couple, revenu 75 000 $ | 0 $ | Plafond familial ordinaire dépassé, aucun versement illustré |
| **C04** | Personne seule, revenu **26 190 $**, dette envers l'État | 240 $ | Versement annuel; protection de **50 %** applicable au seuil inclusivement |
| **C05** | Personne seule, revenu **26 191 $**, dette envers l'État | 800 $ | Mensuel; plafond de 50 % **non établi par ces critères**, ce qui **n'autorise pas** une retenue de 100 % |
| **C06** | Résidence en village nordique, revenu 75 000 $ | 600 $ | Règle générale de plafond **non appliquée**, échéances trimestrielles fictives |
| **C07** | Personne seule, aide financière de dernier recours, revenu 15 000 $, dette | 799 $ | Limitation de 50 %; borne illustrative de retenue de **399,50 $** sur le crédit fictif |
| **C08** | Personne seule, revenu 30 000 $ | 0 $ | Revenu sous plafond ne suffit pas à garantir un crédit |
| **C09** | Couple, revenu **70 395 $** exactement | 0 $ | Seuil général atteint; la règle de seuil n'est pas un taux |
| **C10** | Famille monoparentale avec un enfant, revenu **67 179 $** | 0 $ | Plafond indicatif augmenté de **2 634 $** atteint |

**Important :** la borne maximale de retenue calculée est un **plafond**, pas une prédiction de la somme réellement retenue. Le montant versé par Revenu Québec dépend de l'avis, de la créance, de la situation réelle, des règles applicables et des dates. La borne cumulée indicative n'a de sens que si **le même plafond de 50 %** s'applique à chaque versement de ce crédit. Dans les cas où la limitation n'est pas prouvée par les critères étudiés, **le programme laisse la borne inconnue**.

## 4. Contrôle de continuité entre les deux exercices

Le programme vérifie les cycles **juillet 2026–juin 2027** sans les confondre avec les exercices comptables du gouvernement :

| Cadence de crédit hypothétiquement déterminé | Juillet 2026–mars 2027 | Avril–juin 2027 |
|---|---:|---:|
| Annuelle | 1 | 0 |
| Trimestrielle | 3 | 1 |
| Mensuelle | 9 | 3 |

Ces nombres sont des **occurrences de versements planifiés**, pas une preuve de paiement individuel ni une méthode d'imputation comptable des droits constatés. Les délais de traitement, l'absence d'annexe D ou les informations manquantes peuvent modifier le moment où une personne reçoit effectivement le crédit.

## 5. Portée pour la réforme du Projet Nova

Avant d'adopter un système fiscal à deux prélèvements, il faudra vérifier :

1. **La protection du revenu disponible réel**, après prélèvements, transferts, logement et changements des prix.
2. **La continuité des versements** malgré le changement des systèmes fiscaux, en particulier pour les ménages modestes.
3. **La protection contre les retenues excessives**, sans transformer les crédits sociaux en moyen de financer artificiellement le programme.
4. **L'équivalence des droits** associés à la TVQ, au logement et au coût de la vie nordique, indépendamment du nom du prélèvement supprimé.
5. **La concordance comptable** pour ne pas ajouter en 2027 des crédits déjà inscrits dans les charges du régime actuel.
6. **La séparation des deux régimes constitutionnels** : les prestations, compétences et transferts du Québec souverain restent à chiffrer séparément.

Les **dix cas fictifs ne comptent pour aucune des 720 incidences P52D manquantes**. Sans vraie distribution par bénéficiaires et assiettes, il serait trompeur de leur attribuer un coût global ou une conclusion « la population sera plus riche ».

## 6. Utilisation du contrôleur et validation

Le jalon comprend un registre JSON, un programme Python sans dépendances externes, des tests d'erreurs de données, une note et un workflow GitHub.

```bash
python scripts/simuler_continuite_sociale_menages_synthetiques_nova_p57c.py \
  --pilote projets/projet-nova/etudes/P57C_PILOTE_MENAGES_SYNTHETIQUES_SOLIDARITE_2026_2027.json \
  --p57b projets/projet-nova/etudes/P57B_SOLIDARITE_VERSEMENTS_2026_2027_ET_VERROU_PROTECTION_TVQ.json \
  --p57a projets/projet-nova/etudes/P57A_RECONCILIATION_CREDITS_2025_2026_COMPTES_PUBLICS_VOL1.json \
  --p56o projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json \
  --barometre projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json
```

Le contrôleur refuse de déclarer une microsimulation Nova certifiée, et il **n'écrase jamais un rapport existant**.

## 7. Ce qui débloquera le programme vers 100 %

Les prochaines preuves utiles sont des **statistiques publiques réellement agrégées** ou des sources anonymisées légalement accessibles, **sur le même exercice et la même population** : revenus nets, droits par composante, statut familial, région, assistance sociale, retenues éventuelles et dates de versements. Ces données alimenteraient un **modèle distributif et budgétaire** validé pour 2027-2028.

**Baromètre inchangé : 53 % estimés, 47 points estimés restants.** Aucune des dix portes de clôture n'est démontrée. Les **600 cellules P52B, 720 incidences P52D et 20 preuves P52A** restent ouvertes. Aucune modification de `main` ni de SINJIRA; `NO_GO_AUTOMATIQUE`.
