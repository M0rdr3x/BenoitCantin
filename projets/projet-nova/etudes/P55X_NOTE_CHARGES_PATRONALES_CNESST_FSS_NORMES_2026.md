# P55X — Charges patronales 2026 : FSS, normes du travail et CNESST

**7 novembre 2026 · Étude candidate, non adoptée.** Suite de P55W : calculer les charges patronales FSS et normes du travail sous hypothèses explicites, sans inventer la prime CNESST ni une économie Nova.

## Sources et portée

- [Revenu Québec, principaux changements 2026](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/employeur-principaux-changements-2026/) : FSS jusqu'à 1 M$ de masse salariale totale = **1,65 %** (catégorie générale) ou **1,25 %** (primaire/manufacturier); secteur public et masse ≥ 7,8 M$ = **4,26 %**. Au milieu : taux en points de pourcentage = **1,2662 + 0,3838 × masse en M$** (général), ou **0,8074 + 0,4426 × masse en M$** (primaire/manufacturier). Congés/exemptions particuliers non simulés.
- [Revenu Québec, cotisation aux normes du travail](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/calcul-des-retenues-et-des-cotisations/cotisation-relative-aux-normes-du-travail/) : **0,06 %** de rémunération assujettie, au plus **103 000 $ par personne en 2026**, avec employeurs légalement exemptés.
- [Revenu Québec, masse salariale totale](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/calcul-des-retenues-et-des-cotisations/cotisation-de-lemployeur-fss/masse-salariale-totale/) : les employeurs associés comptent dans le taux FSS, même si la cotisation porte sur une autre assiette.
- [CNESST, tarification](https://www.cnesst.gouv.qc.ca/fr/demarches-formulaires/employeurs/assurance-sante-securite-travail/tarification/taux-prime) : taux par unité ou personnalisé/rétrospectif; le [taux moyen 2026 de **1,54 $/100 $**](https://www.cnesst.gouv.qc.ca/fr/demarches-formulaires/employeurs/assurance-sante-securite-travail/tarification/annexes-tableaux/taux-moyen-prime) **n'est pas le taux d'une PME donnée**.

**Périmètre exclusivement : Québec au sein du Canada, année 2026.** Aucun barème fictif de Québec souverain n'est déduit de ces taux.

## Scénario synthétique non représentatif

Employeur fictif général non exonéré, dix salariés identiques avec salaire entièrement admissible de 50 000 $ chacun, année complète, personnes de 18 à 64 ans, un seul employeur, pas d'employeur associé, cotisation aux normes applicable. Ces conditions ne sont pas prouvées pour une PME réelle.

| Poste patronal | Montant calculé |
|---|---:|
| Masse salariale fictive | 500 000,00 $ |
| RRQ, RQAP, assurance-emploi (P55W), 10 × 4 140,50 $ | **41 405,00 $** |
| FSS général : 500 000 × 1,65 % | **8 250,00 $** |
| Normes : 500 000 × 0,06 % | **300,00 $** |
| **Somme partielle de ces cinq composantes** | **49 955,00 $** |
| Prime individuelle CNESST | **Inconnue** |
| Autres contributions/avantages et coût patronal complet | **Inconnus** |
| Variation attribuable à Nova | **Inconnue** |

Dans le cas alternatif fictif d'un employeur primaire/manufacturier **non exonéré**, FSS = **6 250,00 $** et somme partielle = **47 955,00 $**. Il ne s'agit pas de gains du Projet Nova.

## Exigences et protections

Les neuf points **X01–X09**, consignés dans le registre JSON, exigent la qualification juridique de l'employeur et des exemptions, sa décision de tarification CNESST, les salaires assurables, l'ensemble des obligations patronales, le maintien financé des droits RRQ/RQAP/AE/SST, puis une comparaison avant/après intégrant emploi, prix et pouvoir d'achat ainsi que des avis indépendants signés. Ne jamais confondre économies de trésorerie privées et économies du budget public; ne pas multiplier l'exemple par un nombre de PME inconnu.

Le script `scripts/calculer_charges_employeur_nova_p55x.py` impose une confirmation explicite des hypothèses, préserve `null` pour CNESST/coût complet/variation Nova et refuse la certification automatique (code 3). Exemple :

```bash
python scripts/calculer_charges_employeur_nova_p55x.py --salaire 50000.00 --effectif 10 --secteur general --hypotheses-confirmees --bilan-public /hors_git/p55x_exemple.json
```

**P55N demeure 53 % estimatifs (45–60 %).** Les 600 inconnues P52B et 720 inconnues P52D ne sont pas comblées. **NO_GO_AUTOMATIQUE**; aucun mandat, collecte, dépense, taux Nova adopté, économie certifiée, réduction d'emploi/service, fusion dans `main` ou changement SINJIRA.
