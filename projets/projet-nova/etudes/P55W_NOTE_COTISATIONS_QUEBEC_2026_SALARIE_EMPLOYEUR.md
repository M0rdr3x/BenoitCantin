# P55W — Cotisations réellement prévues par les barèmes 2026, sous hypothèses salariales explicites

**7 novembre 2026 — étude arithmétique candidate, non adoptée.** Progrès de l'analyse d'incidence du Projet Nova : pour un **salaire admissible supposé**, calculer les cotisations **du salarié et de l'employeur**, en distinguant ce que les régimes actuels financent. Le programme **ne propose pas leur abolition** sans preuve du financement des prestations correspondantes.

## 1. Sources réglementaires québécoises et fédérales

- [Revenu Québec, *Principaux changements pour 2026*](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/employeur-principaux-changements-2026/) : RRQ, **exemption annuelle 3 500 $**, gains admissibles jusqu'à **74 600 $**, taux **6,30 %**, deuxième tranche jusqu'à **85 000 $** au taux de **4 %**. Pour le RQAP : salaire assurable au plus **103 000 $**, taux salarié **0,430 %**, employeur **0,602 %**.
- [Agence du revenu du Canada, *Taux de cotisation à l'assurance-emploi et maximums — Québec, 2026*](https://www.canada.ca/fr/agence-revenu/services/impot/entreprises/sujets/retenues-paie/retenues-paie-cotisations/assurance-emploi-ae/taux-cotisation-a-ae-maximums.html) : rémunération assurable maximale **68 900 $**, taux salarié **1,30 %**, employeur **1,82 %**.
- [Revenu Québec, *Exemption générale relative au RRQ*](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/calcul-des-retenues-et-des-cotisations/cotisations-au-rrq/exemption-generale/) : l'exemption annuelle s'applique sous réserve de modalités de paie particulières. Le calculateur suppose une **année complète de travail continu**, sans réduction de l'exemption.

Ces informations ont été examinées sur les **pages HTML officielles**. Le modèle n'est pas un bulletin de paie certifié et ne vérifie pas périodiquement les changements de loi. Les taux s'appliquent uniquement à **2026 au Québec dans le Canada**.

## 2. Hypothèses obligatoires pour interpréter les résultats

Le salaire saisi est supposé **entièrement admissible aux trois régimes**; le salarié a **18 à 64 ans**, travaille **toute l'année** pour **un seul employeur**, reçoit la totalité de ce salaire au Québec, sans exemption, élection, congé ou autre traitement spécial. Si ces conditions ne sont pas réunies, il faut utiliser les tables légales propres au dossier plutôt que le montant P55W. Le programme distingue **les retenues calculées annuellement** des montants de retenue par période, dont les arrondis et modalités peuvent différer.

**Exclusions matérielles :** impôts fédéraux et québécois sur les revenus, crédits et prestations, Fonds des services de santé (FSS) de l'employeur, cotisations relatives aux normes du travail et à la CNESST, autres charges d'entreprise. Le total employeur P55W n'est donc **pas le coût complet de l'emploi** et les totaux salariés ne constituent pas un revenu disponible.

## 3. Exemple arithmétique : salaire admissible de 50 000 $ en 2026

| Cotisation | Part du salarié | Part de l'employeur |
|---|---:|---:|
| RRQ : (50 000 − 3 500) × 6,30 % | **2 929,50 $** | **2 929,50 $** |
| RQAP : salaire × 0,430 % / 0,602 % | **215,00 $** | **301,00 $** |
| Assurance-emploi : salaire × 1,30 % / 1,82 % | **650,00 $** | **910,00 $** |
| **Total des trois régimes seulement** | **3 794,50 $** | **4 140,50 $** |

Les montants sont **conditionnels à un emploi admissible de 50 000 $**, **pas le montant observé dans le cas officiel P55T**. Le cas gouvernemental d'une personne seule ayant **50 000 $ de revenu annuel** n'établit ni que les 50 000 $ sont entièrement du salaire assurable, ni l'âge, ni les exemptions particulières, ni les composantes manquantes des huit champs d'incidence. P55W **ne remplit donc pas artificiellement** le dossier incomplet P55V ni les `null` de P52D.

## 4. Méthode de calcul et plafonds

Pour le RRQ, à un salaire admissible annuel `S` :

```text
RRQ (salarié ou employeur) =
  6,30 % × max(0, min(S, 74 600) − 3 500)
  + 4,00 % × max(0, min(S, 85 000) − 74 600)
```

Le RRQ plafonne donc à **4 895,30 $** pour chaque partie lorsque le salaire admissible dépasse le dernier plafond. Le RQAP utilise respectivement **0,430 %** et **0,602 %** sur `min(S, 103 000)`; l'assurance-emploi applique **1,30 %** et **1,82 %** sur `min(S, 68 900)`. Les cotisations de chaque programme sont arrondies au cent avant addition.

**Plafonds des trois cotisations combinées :** **6 233,90 $ salarié** et **6 769,34 $ employeur** dans ce modèle simplifié. Ce sont des plafonds arithmétiques des seules trois composantes, non des maxima de tous les prélèvements obligatoires.

## 5. Pourquoi ce calcul compte pour la proposition « deux prélèvements »

Le programme Nova cherche à réduire les charges sans appauvrir les citoyens ni fragiliser les prestations. **Une cotisation sociale n'est pas une économie publique automatiquement disponible.** Le RRQ, le RQAP et l'AE sont associés à des droits, prestations et mécanismes de financement. Les retirer, les intégrer à une autre recette ou les reprendre en scénario souverain exige une étude actuarielle, des dispositions légales et un budget de remplacement.

Le modèle ne confond jamais **charge du salarié**, **charge de l'employeur**, **impôt sur le revenu**, **dépense publique**, ni **bénéfice sur le pouvoir d'achat**. Aucune économie, aucun nouveau taux Nova et aucun rendement anti-paradis fiscaux n'est affirmé. Les **600 postes inconnus P52B** et les **720 valeurs inconnues P52D** restent visibles. **Score P55N : 53 % estimatifs, inchangé.**

### Contrôle reproductible

```bash
python scripts/calculer_cotisations_salariales_nova_p55w.py \
  --salaire 50000.00 \
  --bilan-public /hors_git/p55w_bilan_exemple.json
```

Le programme exige une chaîne monétaire décimale explicite, arrondit indépendamment chacune des trois cotisations, teste les exemptions et les plafonds, protège les rapports existants contre l'écrasement et refuse toute déclaration de faisabilité automatique avec `--exiger-faisabilite` (code **3**). Les actions probantes **W01 à W08** restent ouvertes, notamment les exemples salariaux anonymisés, l'incidence des PME, le traitement des impôts et prestations, la préservation des régimes et les avis indépendants signés.

**Statut : `NO_GO_AUTOMATIQUE`**, PR en brouillon, aucune politique adoptée, aucun changement de SINJIRA ou de la branche `main`, aucun contact externe ou dépense.
