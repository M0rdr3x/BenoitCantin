# P55T — Un premier cas témoin officiel 2026 pour mesurer un éventuel gain de revenu disponible

**7 novembre 2026 — document candidat, non adopté.** Ce jalon intègre un **repère public actuel** dans le dispositif d'incidence P55S, au lieu de remplir les cas P52D avec des montants supposés. Il ne propose aucun taux d'impôt pour le Projet Nova et **n'augmente pas** automatiquement la complétude estimée à 53 %.

## 1. Cas documenté par le gouvernement du Québec

Le gouvernement du Québec, dans [« Estimer le revenu disponible »](https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible), page publique mise à jour le **17 juin 2026**, décrit une **personne vivant seule, ayant un revenu de 50 000 $**, dont le revenu disponible **augmente de 847 $ entre 2025 et 2026**, compte tenu des changements de taxes, aides, cotisations et indexations. Il s'agit d'un **exemple gouvernemental du régime actuel**, **pas d'un calcul Nova** ni d'une moyenne de tous les Québécois.

| Éléments du changement 2025 → 2026 présentés par le gouvernement | Gain affiché |
|---|---:|
| Versement spécial 2026 pour l'épicerie et l'énergie | **100 $** |
| Allocation canadienne pour l'épicerie et les besoins essentiels | 358 $ |
| Diminution des cotisations | 72 $ |
| Indexation du régime fiscal du Québec | 166 $ |
| Indexation du régime fiscal fédéral | 150 $ |
| **Somme des cinq montants affichés** | **846 $** |
| **Gain total indiqué par le gouvernement** | **847 $** |
| **Écart de présentation non expliqué dans la page** | **1 $** |

**Ne pas remplacer le gain officiel de 847 $ par 846 $** et ne pas attribuer l'écart de 1 $ à une raison non prouvée. Un écart d'arrondi est plausible, mais **la source consultée ne donne pas d'explication**; le champ reste expressément « non expliqué ».

Le **versement spécial de 100 $ est ponctuel pour 2026** et soumis à l'admissibilité indiquée par le gouvernement. La composante de **358 $** reflète une modification des prestations fédérales, qui comporte une architecture de versements récurrents **et ponctuels**; sa récurrence globale ne doit pas être présumée. Ce gain comparatif **n'est pas nécessairement reproductible** pour un autre ménage, une autre année, ou un éventuel système Nova.

La page publique ne donne pas, pour cet exemple, **un tableau complet et individualisé des huit champs P52D** « actuel » et « proposé », ni le **revenu disponible annuel absolu 2025 ou 2026**, ni le revenu imposable déclaré, les impôts définitifs ou le détail des crédits et cotisations. Ces champs demeurent **`null` dans P52D**. La classification « personne seule à revenu moyen » est un **rapprochement candidat**, pas une classification statistique attestée.

## 2. Référence réglementaire réelle : taux marginaux 2026

Dans le Québec au sein du Canada, une simulation sérieuse doit appliquer **deux systèmes fiscaux et leurs crédits**, sans confondre les seuils **marginaux** avec un taux d'imposition réel.

| Tranche de revenu **imposable** (2026) | Taux marginal Québec |
|---|---:|
| 0 $ à 54 345 $ | 14 % |
| Plus de 54 345 $ à 108 680 $ | 19 % |
| Plus de 108 680 $ à 132 245 $ | 24 % |
| Plus de 132 245 $ | 25,75 % |

Source : [Revenu Québec — Principaux changements pour 2026](https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/employeur-principaux-changements-2026/). Le **montant personnel de base de 18 952 $** est un **montant de crédit applicable selon les règles fiscales**; ce n'est ni une cotisation, ni un revenu garanti, ni une franchise permettant d'appliquer directement un taux unique.

| Tranche de revenu **imposable** (2026) | Taux marginal fédéral |
|---|---:|
| 0 $ à 58 523 $ | 14 % |
| Plus de 58 523 $ à 117 045 $ | 20,5 % |
| Plus de 117 045 $ à 181 440 $ | 26 % |
| Plus de 181 440 $ à 258 482 $ | 29 % |
| Plus de 258 482 $ | 33 % |

Source : [Agence du revenu du Canada — taux et tranches fédérales 2026](https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/taux-imposition-tranches-revenu/annee-en-cours.html).

**Particularité québécoise à ne pas oublier :** l'[abattement d'impôt du Québec](https://www.canada.ca/fr/ministere-finances/services/publications/depenses-fiscales/2026/partie-4.html) correspond à **16,5 % de l'impôt fédéral de base exigible**, selon les règles applicables; il ne signifie pas 16,5 % du salaire brut. L'addition des taux marginaux bruts Québec et fédéral **ne donne pas l'impôt net d'une personne**. Les crédits, les cotisations sociales, les prestations et le revenu imposable doivent être déterminés.

Le script propose uniquement, en mode **arithmétique de contrôle**, un calcul progressif **avant crédits, abattement et cotisations**, sur **un revenu imposable explicitement entré comme test**. Ainsi, si l'on saisit fictivement **50 000 $ de revenu imposable**, chacun des deux barèmes affiche **7 000 $ avant crédits** sur la première tranche; **ce n'est pas l'impôt réellement à payer** d'une personne gagnant 50 000 $ de salaire brut. Ce calcul est réservé aux tests du barème, et aucun résultat fiscal personnel n'est inféré du seul revenu de l'exemple officiel.

## 3. Comment ce nouveau repère pourra servir au Projet Nova

La méthode proposée exige de comparer, pour un **même ménage et une même année**, les prestations réellement admissibles, les impôts fédéral et provincial, les cotisations, les frais pertinents, les taxes supportées et la valeur de la continuité des services. Une réforme ne pourra être qualifiée de protectrice du pouvoir d'achat qu'après avoir démontré sa cohérence **pour les ménages modestes, les familles, les personnes retraitées et les PME**, et testé les effets sur les prix.

Ce repère explique pourquoi la promesse « deux prélèvements = automatiquement plus d'argent dans chaque poche » **ne serait pas une conclusion démontrée**. Dans le Québec au Canada, l'impôt fédéral subsiste; dans un Québec souverain hypothétique, les règles, les prestations et les compétences fiscales devraient être refondées et financées selon un processus légal.

Le modèle P52D compte toujours **720 valeurs inconnues**; P52B compte toujours **600 montants financiers inconnus**. Le gain gouvernemental de 847 $ ne renseigne aucune de ces **1 320 valeurs**, puisqu'il décrit une variation publique limitée et **pas les composantes complètes d'une situation proposée par Nova**.

## 4. Actions probantes restantes

Les huit actions **T01–T08** demeurent ouvertes : détail de la paie, cotisations, crédits et prestations du témoin; explication à vérifier de l'écart de 1 $; caractère ponctuel ou récurrent des aides; abattement et crédits fédéraux; représentativité par décile et région; séparation des mesures actuelles et des propositions Nova; coûts des services en nature et des prix; et contre-expertise indépendante signée.

**Aucune donnée personnelle n'est requise ni extraite.** Aucune promesse de gain, aucune économie nouvelle, aucune base fiscale harmonisée et aucun taux Nova ne résultent de ce jalon.

### Vérification locale et automatisée

```bash
python scripts/valider_temoin_revenu_disponible_2026_nova_p55t.py \
  --bilan-public /hors_git/p55t_bilan_public.json
```

Ce validateur contrôle les sources déclarées, les cinq gains affichés, leur écart, les barèmes courants, les protections et le chaînage aux montants inconnus P55S. Il ne télécharge aucune page ou donnée personnelle, et ne modifie ni P52D ni le programme public.

L'option `--exiger-simulation-nova` produit un **refus 3**. La suite de tests contient des cas limites de seuils et des tentatives explicites de substitution du gain officiel, d'invention de revenus disponibles ou de suppression de protections.

**Décision : `NO_GO_AUTOMATIQUE`.** Programme non adopté, score de maturité estimatif **53 %**, pas de diminution d'emplois ou de services, pas de modification SINJIRA, pas de dépense ni de contact externe, pas de fusion de la PR dans `main`.
