# Projet Nova — P56L : distribution des crédits remboursables et protections vérifiables du pouvoir d'achat

**7 novembre 2026 — Étude de données fiscales publiques, non proposition normative, non adoptée.**  
**Décision : `NO_GO_AUTOMATIQUE` · Maturité P55N : 53 % estimés, fourchette 45–60 %.**

## 1. Pourquoi P56L était indispensable

Les jalons P56J et P56K ont mis en évidence les **recettes historiques qu'une simplification fiscale risquerait de supprimer** et ont commencé à tracer les assiettes du revenu des particuliers (2023), des sociétés (2021) et le coût des dépenses fiscales (2025). Or, ces séries ne démontrent **aucune hausse du revenu disponible des ménages** sous le Projet Nova. Un taux de taxe plus faible peut coexister avec une perte de crédits remboursables, de prestations ou de services.

P56L construit donc une **base de référence 2023 réellement publiée**, permettant d'isoler les crédits selon six tranches de revenu total et la concentration de l'impôt par quintile de **personnes ayant produit une déclaration**. Les données sont des agrégats fiscaux provinciaux, **pas une microsimulation et pas des ménages**.

Sources primaires :
- [Ministère des Finances du Québec — tableau A.14, Répartition de l'impôt à payer et des crédits remboursables par tranche de revenu total, 2023](https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-impot-a-payer.asp)
- [Ministère des Finances du Québec — tableau A.3, revenu total et impôt à payer par quintile de déclarants, 2023](https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/resume.asp)
- [P56K — historique fiscal des particuliers, sociétés et crédits](P56K_ASSIETTES_PARTICULIERS_SOCIETES_CREDITS_SOURCES_OFFICIELLES.json)

## 2. Résultats officiels par tranche de revenu total — 2023

**Montants en millions CAD**, chiffres publiés arrondis.

| Revenu total annuel du déclarant | Revenu total | Impôt à payer | Crédits remboursables | Impôt à payer − crédits |
|---|---:|---:|---:|---:|
| Moins de 10 000 $ | 2 532 | 2 | 777 | **−775** |
| 10 000 à 19 999 $ | 12 615 | 10 | 1 118 | **−1 108** |
| 20 000 à 29 999 $ | 26 507 | 273 | 2 306 | **−2 033** |
| 30 000 à 49 999 $ | 59 789 | 2 816 | 2 275 | **541** |
| 50 000 à 99 999 $ | 159 483 | 14 365 | 2 145 | **12 220** |
| 100 000 $ ou plus | 166 989 | 23 324 | 683 | **22 640** |
| **Total publié** | **427 915** | **40 790** | **9 305** | **31 485** |

La somme des montants de crédits remboursables par tranche est **9 304 M$**, contre **9 305 M$ au total publié**. Le calcul `23 324 − 683` donne **22 641 M$**, alors que le solde publié pour cette tranche est **22 640 M$**. Le montant d'impôt avant les crédits non remboursables donne également un écart de **1 M$** lorsqu'on additionne les six classes. **Ces écarts reflètent l'arrondissement du tableau officiel : il est interdit de modifier les lignes sources pour les faire disparaître.**

### Ensemble des déclarants ayant déclaré moins de 30 000 $ de revenu total

| Indicateur, 2023 | Montant |
|---|---:|
| Revenu total des trois tranches | **41 654 M$** |
| Impôt à payer | **285 M$** |
| Crédits remboursables | **4 201 M$** |
| **Solde fiscal agrégé (impôt − crédits)** | **−3 916 M$** |
| Part des crédits remboursables de l'ensemble du tableau | **45,1 %** |

**Interprétation admissible :** le régime fiscal provincial observé comportait des crédits remboursables importants destinés à des personnes appartenant à ces classes de revenu total. Une réforme les supprimant sans contrepartie peut retirer un soutien essentiel au pouvoir d'achat.

**Ce que les chiffres ne démontrent pas :** qu'un même déclarant a reçu la moyenne du groupe; que les 4,201 G$ sont tous de l'aide en espèces; que ces personnes forment des ménages distincts; que leurs revenus après l'ensemble des transferts et impôts fédéraux sont connus; que tous seraient perdants ou gagnants sous un taux Nova. Les montants ne sont pas des « dépenses libérables » pour financer une réduction fiscale.

## 3. Quintiles de déclarants, toujours 2023

Le tableau A.3 classe les contribuables par **revenu total individuel** et les partage en cinq groupes de même nombre de déclarants :

| Quintile de déclarants | Revenu total de 2023 | Part du revenu total | Part de l'impôt à payer |
|---|---|---:|---:|
| Q1 | Moins de 19 713 $ | 3,43 % | 0,03 % |
| Q2 | 19 713 à 34 580 $ | 8,91 % | 1,46 % |
| Q3 | 34 581 à 54 178 $ | 14,99 % | 8,64 % |
| Q4 | 54 179 à 82 785 $ | 22,57 % | 20,45 % |
| Q5 | 82 786 $ et plus | 50,10 % | 69,41 % |

Ces **quintiles ne sont pas les six tranches A.14** et ne peuvent pas être reliés mécaniquement ligne à ligne. Ils ne fournissent ni crédits remboursables par quintile, ni le revenu disponible des ménages, ni l'incidence de la taxe à la consommation. Les pourcentages sont arrondis et peuvent totaliser 99,99 % plutôt que 100 %.

## 4. Dix conditions minimales de protection avant d'adopter un taux Nova

Le registre P56L documente dix exigences **non encore démontrées**, pour les deux situations constitutionnelles : maintien ou remplacement intégralement compensé des crédits remboursables pertinents; mesure du revenu disponible après impôts provinciaux et fédéraux, crédits, prestations et cotisations; effets des taxes à la consommation sur les prix sans supposer une répercussion totale; effets sur familles, personnes seules, aînés, personnes handicapées et autres catégories; financement des services; distinction entre déclarants et ménages; incidence sur PME, grandes entreprises et salariés; respect des compétences constitutionnelles; assiettes et comportements projetés sur 2027–2036; revue indépendante et consultation.

Une norme de protection du pouvoir d'achat ne pourra être déclarée **réalisée** sur la seule base d'une variation d'impôt. Le calcul devra présenter la différence **après** toutes les taxes, crédits, transferts et variations de prix, par décile de ménages et région, y compris les perdants éventuels, ainsi que le coût d'une compensation. L'absence de perdants n'est pas présumée; elle doit être mesurée, puis les arbitrages annoncés clairement.

## 5. Limites juridiques, financières et statistiques

**Québec dans le Canada :** la TPS et les impôts fédéraux demeurent hors du pouvoir d'abolition unilatérale du Québec. Les cotisations sociales, le FSS, les recettes scolaires et les ressources municipales sont à qualifier et à financer selon leur droit applicable. Une baisse d'impôt provincial pourrait ne pas produire un gain de revenu disponible si crédits ou services disparaissent.

**Québec souverain hypothétique :** impossible de présumer qu'un transfert fédéral historique constitue un revenu acquis après indépendance, ni de soustraire d'emblée les pensions, frontières, obligations de dette et fonctions à reprendre. Les données 2023 des particuliers ne définissent pas l'assiette imposable future de ce scénario.

**Entreprises :** les dernières statistiques fiscales des sociétés retenues dans P56K concernent **2021**, quatre ans avant le portrait de dépenses fiscales 2025 et deux ans avant les données des particuliers 2023. Une société non imposable sur son revenu n'est pas forcément exonérée de toute cotisation ou de tout paiement. Un simulateur commun ne peut être construit sans harmonisation des exercices, assiettes et statuts des entreprises.

## 6. Livrables vérifiables du jalon P56L

- `P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json` : tableau officiel A.14, quintiles A.3, anomalies normales d'arrondis, agrégat inférieur à 30 000 $, dix conditions et scénarios restant non chiffrés.
- `scripts/auditer_distribution_fiscale_et_protection_pouvoir_achat_nova_p56l.py` : contrôleur des **six tranches**, **cinq quintiles**, rapprochement P56K/P52B/P55N, refus des aides individuelles inventées et des taux non démontrés.
- `scripts/tests/test_auditer_distribution_fiscale_et_protection_pouvoir_achat_nova_p56l.py` : 50 tests couvrant corruption de montants, arrondis, omissions de crédits, faux revenus de ménage, fausses projections et erreurs de régimes.
- `.github/workflows/validate-nova-p56l.yml` : vérification de P56K et P56L dans la branche de travail.
- Cette note.

Commande depuis la racine du dépôt :

```bash
python scripts/auditer_distribution_fiscale_et_protection_pouvoir_achat_nova_p56l.py \
  --distribution projets/projet-nova/etudes/P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json \
  --p56k projets/projet-nova/etudes/P56K_ASSIETTES_PARTICULIERS_SOCIETES_CREDITS_SOURCES_OFFICIELLES.json \
  --gabarit projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json \
  --preuves projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json \
  --barometre projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json
```

L'option `--exiger-incidence-certifiee` doit échouer avec le code 3. Aucun fichier existant n'est écrasé. Les montants P52B (600 inconnus), les incidences P52D (720 inconnues) et les 20 preuves P52A ne sont pas modifiés : **aucune cellule de prévision ne reçoit un montant fictif**.

## 7. P56M : vraie microsimulation distributive, après obtention de données nécessaires

Établir un cadre commun **ménage-année**, distinguer composition et revenus des membres, impôts et cotisations des deux paliers, prestations et crédits remboursables, fiscalité municipale, dépenses de consommation et indices de prix, plus les coûts des services. Préparer des catégories ménage vivant seul, famille monoparentale, couple, retraité, ménage à faible revenu et entreprises de tailles différentes. Les taux candidats éventuels devront être présentés avec des élasticités et des marges d'erreur, **sans déduire une économie de la disparition d'une écriture comptable**.

Aucune adoption, aucun changement `main`, aucune modification de SINJIRA ni fusion de la demande de revue. **Score P55N : 53 % estimatifs, sans hausse automatique**. `NO_GO_AUTOMATIQUE`.
