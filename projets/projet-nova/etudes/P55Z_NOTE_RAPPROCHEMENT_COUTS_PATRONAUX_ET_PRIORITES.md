# P55Z — Rapprochement prudent des charges patronales P55X et P55Y

**7 novembre 2026 · Étude technique candidate NON ADOPTÉE.** Le Projet Nova utilise une proposition de deux prélèvements à étudier pour deux cadres **mutuellement exclusifs** (Québec au sein du Canada et Québec souverain hypothétique). Le présent jalon est limité au système de prélèvements en vigueur au Québec **en 2026** et ne simule ni le régime souverain ni une économie attribuable à Nova.

## Pourquoi une jonction nouvelle est nécessaire

- P55W calcule conditionnellement RRQ, RQAP et assurance-emploi selon des hypothèses de salaire annuel cotisable.
- P55X ajoute les contributions employeurs au **FSS** et aux **normes du travail**, avec une assiette limitée et des exonérations non modélisées. Le montant de **49 955 $** pour une PME fictive de dix salariés à 50 000 $ est seulement un sous-total.
- P55Y simule la prime **CNESST** sur des unités de classification fictives; les taux inventés **1,50 $ et 3,00 $ par tranche de 100 $** ne sont pas des taux officiels de l'entreprise. Les données CNESST dépendent de la classification et de la tarification; un taux moyen provincial n'est pas un taux individuel.
- Les sous-totaux P55X et P55Y ne pouvaient pas être additionnés automatiquement : même une masse salariale égale ne prouve pas qu'il s'agit de la même population réelle ni d'assiettes juridiques comparables.

**P55Z** ajoute une jonction **uniquement fictive**, qui exige explicitement le même scénario inventé, la même population salariale fictive, une concordance déclarée des assiettes et l'égalité numérique des sommes salariales avant de permettre le calcul du sous-total commun. Il ne fait **aucune jonction de données réelles déclarées, mais non authentifiées**.

## Résultat arithmétique d'un unique scénario inventé

Le fichier P55Z_EXEMPLE_RAPPROCHEMENT_CHARGES_FICTIVES_2026.json contient volontairement un scénario unique : 10 emplois fictifs rémunérés chacun 50 000 $ pendant toute l'année, sans exemption, sous secteur FSS général, avec une masse salariale de 500 000 $. Les taux CNESST des deux unités sont **entièrement inventés** pour le test et leurs salaires assurables fictifs, **300 000 $ et 200 000 $**, couvrent la même population inventée.

| Poste sur ce scénario exclusivement fictif | CAD |
|---|---:|
| RRQ + RQAP + assurance-emploi (employeurs, P55X) | 41 405,00 $ |
| FSS, P55X | 8 250,00 $ |
| Normes du travail, P55X | 300,00 $ |
| **Cinq charges P55X, partielles** | **49 955,00 $** |
| **CNESST inventée P55Y** | **10 500,00 $** |
| **Six charges patronales, somme partielle fictive P55Z** | **60 455,00 $** |
| Salaires fictifs | 500 000,00 $ |
| **Salaires + six charges partielles fictives** | **560 455,00 $** |
| Charges de formation, assurances collectives, autres avantages et ajustements CNESST | **Inconnues** |
| **Coût complet réel de l'employeur** | **Inconnu** |
| **Variation de coûts ou économie due à Nova** | **Inconnue** |

Ce n'est **pas** une estimation de coût complet, ni un plan fiscal, ni une promesse de réduction des taxes. Le montant de 560 455 $ ne représente qu'une addition conditionnelle limitée aux postes connus de l'exemple fabriqué. Aucune extrapolation à la population des PME n'est admissible.

Si les salaires assurables P55Y sont inconnus, incomplets ou différents de la masse P55X, **la somme à six composantes est nulle au sens informatique (`null`) et non égale à zéro**, et le total salaire + charges reste inconnu.

## Sources de règles existantes (2026)

- [Revenu Québec — principaux changements 2026](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/employeur-principaux-changements-2026/) : taux RRQ/RQAP et seuils de FSS.
- [Revenu Québec — cotisation relative aux normes du travail](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/calcul-des-retenues-et-des-cotisations/cotisation-relative-aux-normes-du-travail/) : cotisation de 0,06 % sous conditions et exceptions applicables.
- [CNESST — taux de prime](https://www.cnesst.gouv.qc.ca/fr/demarches-formulaires/employeurs/assurance-sante-securite-travail/tarification/taux-prime) : taux propres aux unités de classification et décision de tarification.
- [Agence du revenu du Canada — assurance-emploi, taux 2026](https://www.canada.ca/fr/agence-revenu/services/impot/entreprises/sujets/retenues-paie/retenues-paie-cotisations/assurance-emploi-ae/taux-cotisation-a-ae-maximums.html) : hypothèses de cotisation applicables au Québec.

Ces références sont des sources de règles, **pas** des pièces comptables propres à une entreprise ni des expertises indépendantes du Projet Nova.

## Ce que le programme de contrôle réalise

- Calcul déterministe en sous-processus local, réutilisant les scripts P55X et P55Y **sans fusionner leurs champs par simple nom**.
- Refus d'année autre que 2026, d'un contexte souverain, d'un dossier non fictif ou d'une population non déclarée identique.
- Refus de certification automatique (`--exiger-faisabilite` : sortie code 3); jamais de GO.
- Propagation des données absentes en `null`; protection contre l'écrasement des bilans.
- Suite de **30 tests synthétiques** et workflow GitHub Actions. La réussite technique ne vaut pas une preuve de coût, une authentification ni un audit professionnel.

Commande d'exemple :

```bash
python scripts/consolider_charges_employeur_nova_p55z.py --entree projets/projet-nova/etudes/P55Z_EXEMPLE_RAPPROCHEMENT_CHARGES_FICTIVES_2026.json
```

## Lacunes prioritaires pour augmenter réellement le score P55N

| Étape | Preuves attendues | Statut |
|---|---|---|
| Z01 | Relevés de paie anonymisés représentatifs par secteur et profil; assiettes RRQ/RQAP/AE/FSS/normes/CNESST réconciliées | NON OBTENU |
| Z02 | Décisions CNESST, modes de tarification, plafonds, ajustements et paiement final réel | NON OBTENU |
| Z03 | Financement de tous les droits, rentes, indemnités et prestations maintenu avec ou sans réforme fiscale | NON DÉMONTRÉ |
| Z04 | Coûts et contributions des PME intégralement ventilés, effets sur prix, emploi et salaires | NON DÉMONTRÉ |
| Z05 | Comparaison avant/après des ménages, entreprises, régions et déciles avec sources et taux de remplacement candidate | NON DÉMONTRÉ |
| Z06 | **Deux budgets décennaux** cohérents, distincts et renseignés (Québec dans le Canada / scénario souverain) | NON DÉMONTRÉ |
| Z07 | Contrôle de la légalité provinciale et de la faisabilité d'une transition souveraine | NON DÉMONTRÉ |
| Z08 | Avis signés et contradictoires de fiscalistes, actuaires, juristes et comptables | NON OBTENU |

Le prochain jalon devrait s'attaquer d'abord à **N01 — budgets décennaux** et **N02 — incidence des deux prélèvements**, au lieu de multiplier les exemples fictifs. Le code P55Z sert à **sécuriser la méthode**, non à produire de nouvelles preuves financières. Les 600 inconnues de P52B, les 720 inconnues de P52D, les protections du pouvoir d'achat, des emplois et des services demeurent inchangées.

**Score P55N : 53 % (fourchette 45–60 %)**, sans hausse automatique par nombre de fichiers ou de tests. Aucune économie certifiée ni taux Nova adopté, aucune dépense ou contact extérieur, aucune modification de SINJIRA ou de la branche main. **Décision : NO_GO_AUTOMATIQUE.**
