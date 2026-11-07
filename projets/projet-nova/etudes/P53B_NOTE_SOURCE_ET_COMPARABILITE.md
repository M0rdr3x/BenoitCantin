# Projet Nova — P53B : sources fédérales, locales et barèmes de cotisations

**20 octobre 2026 — inventaire primaire enrichi, aucune recette extérieure certifiée, aucun taux Nova adopté.**

## Changement concret depuis P53A

P53A contenait 21 montants de recettes du budget du **gouvernement du Québec 2026-2027** et neuf lacunes hors périmètre. P53B a recherché neuf pages de sources officielles permettant d'instruire chacune des lacunes E01–E09. Les **trois systèmes contributifs RRQ, AE, RQAP** ont des barèmes 2026 publiés, avec neuf taux individuels enregistrés et plafonds vérifiables.

**Important :** connaître le taux d'un régime n'établit pas son revenu total, car assiette, cotisants, exemptions, allocations territoriales et prestations sont distincts. Ces paramètres ne permettent pas de chiffrer les neuf lacunes en millions de dollars, ni de compléter le modèle décennal.

## Données effectivement relevées auprès des institutions en 2026

| Cotisation 2026 | Salarié | Employeur | Travailleur autonome / seconde tranche |
|---|---:|---:|---|
| RRQ — première tranche (jusqu'à 74 600 $ de gains, exemption 3 500 $) | 6,30 % | 6,30 % | seconde cotisation 4 % chacun entre 74 600 et 85 000 $ |
| Assurance-emploi au Québec (jusqu'à 68 900 $ de rémunération assurable) | 1,30 % | 1,82 % | statut et assiette propres au programme |
| RQAP | 0,430 % | 0,602 % | travailleurs autonomes : 0,764 % |

Vérifications arithmétiques contrôlables :
- RRQ 2026, tranche principale : (74 600 − 3 500) × 6,30 % = **4 479,30 $**, pour la cotisation maximale d'un salarié ou employeur sur cette tranche.
- RRQ seconde tranche : (85 000 − 74 600) × 4 % = **416 $** par côté.
- AE 2026 Québec : 68 900 × 1,30 % = **895,70 $** pour le salarié et 68 900 × 1,82 % = **1 253,98 $** pour l'employeur.
- RQAP 2026 : cotisations maximales publiées de **442,90 $ salarié**, **620,06 $ employeur** et **786,92 $ autonome**; les plafonds de rémunération doivent être vérifiés selon le régime concerné.

Sources officielles :
- RRQ : https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/calcul-des-retenues-et-des-cotisations/cotisations-au-rrq/maximum-des-gains-admissibles-et-taux-de-cotisation/
- AE 2026 : https://www.canada.ca/fr/emploi-developpement-social/programmes/assurance-emploi/ae-liste/rapports/cotisation/taux2026.html
- RQAP 2026 : https://www.quebec.ca/entreprises-et-travailleurs-autonomes/administrer-gerer/embauche-gestion-personnel/assurance-parentale/taux-cotisations

La présence d'autres règles, exclusions, exemptions, situations interprovinciales et catégories de travailleurs empêche d'utiliser ces simples barèmes comme simulation personnalisée certifiée.

## Années : comparer ce qui est comparable

La publication de l'ARC sur l'impôt fédéral net, édition 2026, porte sur **l'année d'imposition 2024** (traitements jusqu'au 30 novembre 2025). Elle permet une extraction *ultérieure* par province et tranche; aucun fichier CSV source n'a été récupéré, haché et recoupé dans P53B. La somme Québec 2024 ne serait en outre **pas** un chiffre pour l'exercice budgétaire québécois 2026-2027. Une conversion de période et une vérification de couverture seraient nécessaires.

- ARC, tableaux de revenus : https://www.canada.ca/fr/agence-revenu/programmes/a-propos-agence-revenu-canada-arc/statistiques-revenu-statistiques-tps-tvh/statistiques-impot-particuliers-tranche-imposition/statistiques-impot-particuliers-tranche-imposition-edition-2026-annee-imposition-2024.html
- ARC, statistiques T1 : https://www.canada.ca/fr/agence-revenu/programmes/a-propos-agence-revenu-canada-arc/statistiques-revenu-statistiques-tps-tvh/statistiques-finales-t1/annee-imposition-2024.html

Les statistiques municipales **10-10-0020-01** sont des comptes annuels par province, avec période la plus récente observée **2024** sur la page consultée et diffusion le 21 novembre 2025. Les rapports financiers des organismes municipaux du Québec présentent aussi des données **2024** et des corrections ultérieures possibles. Ni ces données ni leurs totaux n'ont été importés ici; il reste à filtrer correctement les catégories de taxes et à dédupliquer les transferts.

- Statistique Canada : https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1010002001
- MAMH : https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier?annee=2023&organisme=31122

## Neuf lacunes et chemins de preuve

E01 doit utiliser les données fédérales nettes par province, mais sans confondre province d'imposition et province de résidence. E02 (TPS), E03 (douanes) et E09 (accises) nécessitent des sources propres aux taxes concernées et des règles territoriales explicites — les données de déclarations T1 ou de paie ne peuvent servir à attribuer la TPS ou les droits de douane au Québec.

E04 et E05 nécessitent une ventilation entre taxes foncières, tarification, ventes de services et transferts reçus, puis l'élimination des flux entre administrations lors de la consolidation. E06–E08 nécessitent les recettes totales par régime *et* les prestations/droits correspondants; les barèmes ne constituent pas des montants agrégés.

## Méthode de consolidation future

Pour chaque montant chiffré obtenu, exiger : année, territoire, type de flux, nature taxe/cotisation/transfert/redevance, administration collectrice, administration bénéficiaire, classification statistique, devise et unité, source primaire et date de consultation, éventuelles révisions, double-compte neutralisé et revue indépendante. Ne pas mélanger années d'imposition 2024, statistiques municipales 2024 et prévisions budgétaires 2026-2027 sans modèle temporel indépendant.

Les taux 2026 **ne sont pas les deux taux Nova**. La « taxe anti-paradis fiscaux » et le taux général sur le revenu demeurent à définir juridiquement et à chiffrer après calcul des dépenses nécessaires.

`python scripts/valider_sources_recettes_nova_p53b.py --rapport p53b_bilan.json --export-csv p53b_neuf_lacunes.csv`

`python scripts/valider_sources_recettes_nova_p53b.py --exiger-consolidation`

Le code 0 valide uniquement la cohérence des références et plafonds sous **NO_GO_AUTOMATIQUE**, 2 rejette les faux montants ou faux liens, 3 refuse de simuler une consolidation nationale accomplie. La PR #673 demeure brouillon; pas de modification `main`, SINJIRA, ni d'autorisation politique ou financière.
