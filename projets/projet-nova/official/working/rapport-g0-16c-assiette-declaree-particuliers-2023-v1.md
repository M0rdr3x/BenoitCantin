# NOVA-FIN-G0.16c — Assiette déclarée des particuliers et distribution fiscale 2023

**Projet Nova — recherche non normative | 7 novembre 2026 | Avancement : 47/100, inchangé.**

## 1. Objet et statut de preuve

La phase G0.16b documentait le revenu des **ménages** après impôt ajusté (ISQ, 2023), ainsi que leurs dépenses **moyennes** (Statistique Canada, 2023). Ces sources ne donnent pas la **base imposable** des particuliers.

La phase G0.16c ajoute une **véritable mesure historique du revenu imposable déclaré**, publiée par le **ministère des Finances du Québec** pour l'année d'imposition **2023**. Elle distingue les revenus, les déductions, l'impôt avant crédits, les crédits et l'impôt payable. Il s'agit de la **base du régime fiscal en vigueur en 2023**; **elle ne constitue pas** une simulation de la réforme Nova, une base actualisée à 2026 ni une prévision de recettes.

### Références gouvernementales primaires

- Tableau **A.7**, *Principales composantes de la déclaration de revenus — 2023* : https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-comp-impot.asp
- Tableau **A.3**, *Répartition du revenu total et de l'impôt à payer par quintile — 2023* : https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/resume.asp
- Tableau détaillé **4**, *Statistiques fiscales selon la tranche de revenu total — 2023* (totaux des nombres de déclarants) : https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/tableau-4.asp
- Publication gouvernementale des statistiques fiscales 2023, **13 février 2026** : https://www.quebec.ca/nouvelles/actualites/details/statistiques-fiscales-des-particuliers-annee-dimposition-2023-68514

**Traçabilité :** consultation des tableaux publics HTML; fichiers Excel/PDF originaux **non importés**, absence d'une seconde contre-vérification indépendante signée. Fichier machine : `data/assiette-fiscale-particuliers-g0-16c-2023.json`.

## 2. Comptabilité de la déclaration, année d'imposition 2023

Tous les montants sont en **millions de dollars courants**, publiés et arrondis par le ministère.

| Composante | M$ |
| --- | ---: |
| Revenu total déclaré | **427 915** |
| Déductions relatives au revenu net | −40 892 |
| Revenu net | **387 023** |
| Déductions relatives au revenu imposable | −14 761 |
| **Revenu imposable déclaré** | **372 261** |
| Impôt calculé sur le revenu imposable | 62 148 |
| Crédits d'impôt non remboursables appliqués | −21 358 |
| **Impôt à payer** | **40 790** |
| Crédits d'impôt remboursables appliqués | −9 305 |
| **Impôt à payer moins crédits remboursables** | **31 485** |

**Rapprochement :** 427 915 − 40 892 = 387 023; 387 023 − 14 761 = 372 262, soit **1 M$ d'écart de présentation** avec 372 261 M$ publiés (arrondis indépendants); 62 148 − 21 358 = 40 790; 40 790 − 9 305 = 31 485. Le **taux moyen d'imposition de 9,5 %** rapporté par le ministère est défini comme impôt à payer divisé par **revenu total**, *non revenu imposable*.

Les contributions et cotisations sociales et le fonctionnement des crédits ne se déduisent pas intégralement de cette seule table. Il serait techniquement erroné d'utiliser le quotient `31 485 / 372 261` comme taux d'impôt proposé par Nova.

**Nombre total de déclarants : 7 220 140**, dont **4 910 844 imposables** et **2 309 296 non imposables** (tableau 4). Ces nombres décrivent des déclarants, pas des ménages; ils ne permettent pas à eux seuls de reconstituer toutes les familles ou obligations fiscales.

## 3. Répartition par quintile des contribuables — année 2023

Les quintiles sont calculés selon le **revenu total déclaré des contribuables**, et non selon les déciles des **ménages** de l'ISQ.

| Quintile | Tranche annuelle du revenu total | Part du revenu total | Part de l'impôt à payer |
| --- | --- | ---: | ---: |
| Q1 | Moins de 19 713 $ | 3,43 % | 0,03 % |
| Q2 | 19 713 $ à 34 580 $ | 8,91 % | 1,46 % |
| Q3 | 34 581 $ à 54 178 $ | 14,99 % | 8,64 % |
| Q4 | 54 179 $ à 82 785 $ | 22,57 % | 20,45 % |
| Q5 | 82 786 $ ou plus | 50,10 % | 69,41 % |

La somme des parts d'impôt est **99,99 %** en raison des arrondis publiés. Ce tableau fournit une preuve historique de la distribution de l'impôt **dans l'ancien régime**, mais **ne mesure pas** la redistribution potentielle, le rendement marginal ou les contribuables gagnants/perdants du Projet Nova.

## 4. Comparabilité : ce qui est strictement interdit

1. **2023 ≠ 2026–2027.** Le montant de 50 942 M$ d'impôt provincial des particuliers présenté dans le budget public prévisionnel 2026–2027 de G0.14 n'est **pas interchangeable** avec 40 790 M$ d'impôt dû sur les déclarations de 2023. Les périodes, périmètres, méthodes comptables et effets des crédits diffèrent.
2. **Particulier ≠ ménage.** Les cinq quintiles des déclarants ne se rapprochent pas directement des dix déciles de revenu disponible **équivalisé** des ménages de l'ISQ. Une jointure de rang Q1–Q5 à D1–D10 serait fallacieuse.
3. **Impôt à payer ≠ recette budgétaire nette libre.** On ne peut annoncer la suppression d'autres recettes sans vérifier les compétences, les fonds affectés et le financement des services.
4. **Base imposable 2023 ≠ assiette proposée.** Modifier déductions, crédits, comportements et règles de résidence change l'assiette future, et un taux unique ne reproduit pas nécessairement le rendement actuel.
5. **Québec au Canada ≠ Québec souverain.** La simulation souveraine doit inclure recettes et responsabilités fédérales, dette, pensions et continuité; les transferts fédéraux provinciaux ne sont pas acquis.
6. **Anti-paradis fiscaux :** aucun rendement **net additionnel**, hors double comptage et dépenses de conformité, n'a été certifié.

## 5. Avancement des quinze preuves de G0.15

La publication du revenu imposable agrégé 2023 et des crédits constitue **un progrès documentaire partiel pour V05** (assiette et crédits des particuliers). Cependant, V05 reste **`A_DOCUMENTER`** dans le registre officiel de preuves : la validation juridique du nouveau régime, les distributions fines, les rapprochements des périodes, les interactions sociales et la contre-expertise indépendante restent absents. **Les quinze preuves sont toujours non franchies**; ni G0.15 ni G0.16 ne sont déclarées réussies.

V06 (entreprises), V07–V10 (continuité sociale), V11 (recettes nettes anti-paradis fiscaux), V12–V13 (incidence), V14 (compétences) et V15 (budgets décennaux) demeurent indispensables.

## 6. Décision et suite professionnelle

**Travail effectivement terminé :** trois tableaux fiscaux publics 2023 consultés; onze grandeurs agrégées (dix montants et le taux moyen), trois nombres de déclarants et cinq quintiles consignés; contrôles de cohérence déterministes et cas de tests ajoutés.

**Étape suivante G0.16d :**
- recenser de façon traçable les catégories de **déductions et crédits** et leurs conditions d'accès; obtenir des ventilations par tranche de revenu et région;
- approfondir le **revenu imposable et le résultat fiscal des sociétés**, dont le dernier millésime identifié dans le catalogue du ministère est 2021, en signalant sa non-comparabilité temporelle;
- construire deux **comptes de financement public** intégrant transferts, dépenses, cotisations et droits acquis avant toute simulation des deux prélèvements Nova;
- faire vérifier les méthodes par des spécialistes indépendants avant de produire des scénarios distributifs et des taux.

**Décision :** aucune proposition de taux ou d'économie nouvelle; `null` pour tous les gains de ménages et recettes Nova; **47/100 conservé**. Les références candidates `official/reference/*` et `data/sources.json` restent inchangées.
