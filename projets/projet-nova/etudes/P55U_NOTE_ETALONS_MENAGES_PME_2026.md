# P55U — Quatre ménages, une PME : premiers étalons publics d'incidence 2026

**7 novembre 2026 — complément N02 au dossier de complétude du Projet Nova. Statut : étude candidate non adoptée.**

## 1. Progrès vérifiable, sans gonfler le pourcentage

Le jalon P55T documentait **un cas gouvernemental actualisé en juin 2026**, concernant une personne seule avec **50 000 $ de revenu** et une variation annoncée de **847 $ de revenu disponible** entre 2025 et 2026. Mais **un seul ménage ne suffit pas à établir un effet distributif**, en particulier pour les personnes à faible revenu, les familles et les entreprises.

P55U extrait une **deuxième source officielle** couvrant **quatre profils de ménages** et **une PME**, avec une vérification des composantes. Il permet ainsi de préparer une comparaison de futurs scénarios, **sans calculer les politiques Nova à partir des seules variations annoncées par le gouvernement actuel**.

**Source :** [Le point sur la situation économique et financière du Québec — automne 2025](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Mise_a_jour_economique/2025/FR/AUTFR_lepointNov2025.pdf), **tableau B.8, page imprimée B.14**, et **tableau B.14, page imprimée B.28**, dépôt du **25 novembre 2025**. Les lignes pertinentes ont été examinées par extraction de texte officielle servie par le lecteur Web. La **capture visuelle du PDF a échoué (cache miss)** et **aucun SHA-256 d'un original local n'a été acquis**. La présence des montants dans les données récupérées ne vaut pas certification indépendante.

## 2. Les quatre ménages : effets de mesures existantes annoncées en novembre 2025

| Mesure (montants en dollars) | Personne seule, aide sociale | Travailleur seul, 50 000 $ | Parent seul, enfant de moins de 4 ans, 50 000 $ | Couple, deux jeunes enfants, 100 000 $ familiaux |
|---|---:|---:|---:|---:|
| Impôt sur le revenu | — | 87 | 87 | 115 |
| Prestations d'aide sociale | 192 | — | — | — |
| Crédit d'impôt pour la solidarité | 25 | 79 | 82 | — |
| Allocation famille | — | — | 115 | 168 |
| RRQ (réduction de cotisations) | — | 47 | 47 | 93 |
| RQAP (réduction de cotisations) | — | 32 | 32 | 64 |
| **Gain gouvernemental illustratif 2026** | **217** | **245** | **363** | **440** |

Les tirets « — » figurant dans le tableau de référence **ne sont pas interprétés comme des montants nuls certifiés**. Le modèle P55U les conserve en `null` (non applicable ou non chiffré **pour ce tableau seulement**), et additionne exclusivement les composantes effectivement renseignées de chaque colonne. Il vérifie :

- **217 = 192 + 25**;
- **245 = 87 + 79 + 47 + 32**;
- **363 = 87 + 82 + 115 + 47 + 32**;
- **440 = 115 + 168 + 93 + 64**.

Ces montants sont des **illustrations de l'indexation et de la baisse des cotisations du système québécois existant**, **pas des recettes Nova**, ni des gains individuels confirmés sur les déclarations futures. Le couple comporte **deux revenus de 50 000 $**, pas un seul; les enfants du profil familial sont âgés de moins de 4 ans.

## 3. Une PME illustrée : cotisations employeurs

**Tableau B.14, page B.28** : entreprise de **10 employés**, chacun rémunéré **55 000 $ par an**.

| Cotisation (dollars) | Barèmes 2025 | Barèmes 2026 | Réduction |
|---|---:|---:|---:|
| RRQ, part employeur | 27 810 | 27 295 | **515** |
| RQAP, part employeur | 3 806 | 3 311 | **495** |
| **Total** | **31 616** | **30 606** | **1 010** |

Ce montant est un **avantage illustratif de réduction des cotisations patronales dans le régime actuel**, et non une réduction budgétaire du gouvernement ou une économie démontrée par la fiscalité Nova. Il n'autorise pas une multiplication mécanique par toutes les PME du Québec, puisque les salaires, le nombre d'employés et les situations diffèrent.

## 4. Pourquoi il serait incorrect de soustraire 245 $ de 847 $

Le tableau de **novembre 2025** présentait un gain de **245 $** pour un travailleur seul gagnant 50 000 $, calculé dans le périmètre de l'indexation et des réductions de cotisations annoncées à cette date.

La [page gouvernementale « Estimer le revenu disponible » actualisée le 17 juin 2026](https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible), utilisée dans P55T, annonce **847 $** pour une personne vivant seule ayant un revenu de 50 000 $, **en considérant des mesures plus récentes**, dont des dispositifs fédéraux et un versement ponctuel québécois de 100 $. La somme de ses cinq composantes affichées demeure **846 $**, soit **1 $ de moins que le total officiel**, sans explication prouvée.

**Les deux publications portent sur des périmètres et des dates de mesures différents.** Leur différence arithmétique n'est donc **ni une estimation de l'effet d'une réforme Nova, ni une décomposition juridiquement et économiquement justifiée des changements du système**. Le code refuse explicitement le rapprochement comme une comparaison directe.

## 5. Ce qui manque réellement pour atteindre un programme financé et défendable

P55U fournit une **base de tests publics multi-profils**, mais pas encore des revenus disponibles complets « actuel » versus « Nova ». Il n'actualise **aucun** des **720 montants `null` de P52D**; les **600 montants `null` du budget décennal P52B** restent également inconnus. Il n'existe pas encore de preuve documentée qu'un taux fiscal unique sur les revenus accompagné d'un mécanisme anti-paradis fiscaux financerait le Québec dans le Canada, ni un éventuel Québec souverain, tout en protégeant les services.

Les **huit preuves U01–U08** restent ouvertes : harmoniser les définitions et mesures de 2026; construire les calculs complets pour familles et parents seuls; définir les assiettes Nova avec une revue professionnelle; disposer d'une distribution statistique régionale et par décile; étudier les effets prix; intégrer les entreprises et emplois; rapprocher les dépenses publiques; obtenir les contre-expertises signées.

Le premier critère qui permettra de relever les points « Fiscalité et financement » ou « Politiques sectorielles » ne sera **pas** l'ajout d'une étude, mais une **simulation actualisée et traçable** des ménages et entreprises, puis la démonstration de sa soutenabilité dans les deux budgets décennaux.

## 6. Reproduction et protections

```bash
python scripts/rapprocher_profils_officiels_nova_p55u.py \
  --bilan-public /hors_git/p55u_bilan_public.json
```

Le programme exige le détail exact des quatre colonnes et du tableau PME, refuse les altérations du gain de 245 $ ou de 847 $, interdit la déclaration d'une réforme calculée et vérifie le chaînage aux montants P55T. Le drapeau `--exiger-incidence-nova` doit produire le **code 3** : aucune incidence Nova n'est certifiée.

**Statut inchangé :** score P55N **53 % estimatifs**, programme candidat non adopté, `NO_GO_AUTOMATIQUE`, pas de réduction présumée des services ou emplois, pas de taux ni d'économie certifiés, SINJIRA inchangé, aucun contact, aucune dépense, aucune fusion vers `main`.
