# Projet Nova — G0.19 : pont financier et verrou de preuve des deux scénarios

**Situation examinée au 8 novembre 2026 · Rapport de travail créé le 9 novembre 2026.**  
**Statut : comparaison de sources existantes, aucune fiscalité NOVA chiffrée, aucun programme adopté.**

## 1. Décision sommaire

**Projet Nova demeure à 47/100**, dont **3/16 pour FINANCES**. Le programme envisagé repose sur la simplification en deux mécanismes — prélèvements sur les revenus des particuliers et des entreprises et dispositif de lutte contre les paradis fiscaux — mais ni l'assiette nette, ni les taux, ni le produit additionnel anti-évasion, ni l'abandon des taxes actuelles ne sont validés. Les deux mécanismes devront également être qualifiés juridiquement : une pénalité ou une mesure anti-évasion n'est pas automatiquement un second impôt autonome.

**Conclusion du pont G0.19 : NO-GO.** Il y a **5 exercices de référence gouvernementaux disponibles sur 10**, et **0 budget annuel complet Projet Nova validé sur les 20 exercices-scénarios** (dix ans × deux contextes constitutionnels). Ce constat ne veut pas dire « aucun travail fait » : de nombreux textes et sources existent, mais ils ne constituent pas des budgets certifiés.

## 2. Point de départ, en M$ CA (prévisions du gouvernement du Québec pour 2026–2027)

| Nature | Montant | Interprétation correcte |
| --- | ---: | --- |
| Impôt des particuliers | 50 942 | Recette estimée selon lois existantes, **pas une assiette fiscale** |
| Impôts de sociétés agrégés | 14 698 | À décomposer avant de fixer tout taux Nova |
| Fonds des services de santé | 9 538 | Financement et effets sur l'emploi à protéger |
| Foncier scolaire | 1 301 | Distinct des taxes municipales |
| Taxes de consommation | 30 682 | Enveloppe hétérogène, à décomposer juridiquement |
| **Cinq catégories fiscales précédentes** | **107 161** | Revenus existants, pas rendement NOVA |
| Droits, permis et redevances | 6 484 | Mélange fiscal/non fiscal |
| Revenus divers | 15 790 | Statut et disponibilité à confirmer |
| Entreprises du gouvernement | 5 908 | Recettes d'entreprises publiques, non un nouvel impôt |
| **Trois autres recettes précédentes** | **28 182** | Conservation **supposée**, non certifiée |
| Transferts fédéraux actuels | 33 046 | Hypothèse du Québec **dans le Canada uniquement** |
| **Recettes provinciales totales** | **168 389** | Prévision gouvernementale, pas recette Nova |
| Dépenses gouvernementales y compris dette | 171 597 | Contient le service de la dette |
| Réserve pour éventualités | 2 000 | Nécessaire au pont comptable |
| Fonds des générations | 2 482 | À distinguer du solde comptable |
| **Solde comptable** | **−5 208** | 168 389 − 171 597 − 2 000 |
| **Solde après Fonds des générations** | **−7 690** | −5 208 − 2 482 |

Sources réconciliées : `data/registre-assiettes-fiscales-g0-14-2026-2027.json`, `data/cadre-financier-fiscal-g0-16v-aout-2026.json`, `data/g016z-financement-consolide-et-protections-2026-2036.json`. Les montants sont tirés des références publiques gouvernementales déjà identifiées dans ces registres. **Ce pont n'est pas une nouvelle validation indépendante des PDF d'origine.**

## 3. Sensibilités mécaniques : attention à ne pas les annoncer comme une proposition budgétaire

Sous les seules hypothèses **gelées** de dépenses inchangées, de conservation de **28 182 M$** d'autres recettes et de **33 046 M$** de transferts fédéraux au Québec **dans le Canada** :

- Recettes touchées par le retrait hypothétique **FSS + foncier scolaire + consommation** : **41 521 M$**. Avec le déficit budgétaire préexistant de 7 690 M$, la nécessité mécanique pour retrouver le solde budgétaire légal nul serait **49 211 M$**. Ce n'est ni une perte nette démontrée ni un projet d'abolition validé.
- Besoin conditionnel de produit fiscal total provincial pour le solde comptable nul : **112 369 M$** ; en conservant aussi le versement au Fonds des générations : **114 851 M$**. Ce sont des besoins de trésorerie sous hypothèses, **pas des recettes Nova prouvées, des taux ou des assiettes imposables**.
- Scénario de stress **retirant simplement 33 046 M$ de transferts fédéraux sans modifier le reste** : **145 415 M$** de besoin conditionnel comptable. **Ce chiffre n'est PAS le budget d'un Québec souverain**, car le partage des recettes et fonctions fédérales, la dette, les pensions, la diplomatie, la défense, les relations et accords avec les Premières Nations, les coûts de transition et les négociations restent sans estimation vérifiée.

Les obligations envers les travailleurs, les ménages et les services publics doivent être protégées. La promesse de ne pas appliquer de contre-tarifs n'est pas un poste de recette.

## 4. Deux scénarios × dix ans, sans inventer les cinq années manquantes

| Période | Québec au Canada | Québec souverain hypothétique |
| --- | --- | --- |
| **2026–2027 à 2030–2031** | Prévisions gouvernementales de référence pour 5 ans, mais **aucun solde Nova complet attesté** | Même source provinciale utilisée comme **comparateur seulement**; transferts fédéraux non présumés et fonctions nationales non chiffrées |
| **2031–2032 à 2035–2036** | **Aucune prévision officielle comparable dans cette série**, cases conservées `null` | Idem; aucun transfert, taux, coût national ou balance inventés |

Les 20 états budgétaires Nova annuels restent ouverts dans `data/cadre-financier-g0-13-2026-2036.json`, `data/cadre-financier-fiscal-g0-16v-aout-2026.json` et `data/g016z-financement-consolide-et-protections-2026-2036.json`. Un solde positif calculé à partir de prévisions officielles provinciales **ne devient pas un budget Nova**, et une certification du vérificateur général sur les comptes publics existants **n'est pas l'audit indépendant de Nova**.

## 5. Distinguer exercice réalisé, prévision et niveau municipal

- **2025–2026 réalisé** : recettes provinciales 160 428 M$, dépenses 165 930 M$, solde comptable **−5 502 M$** d'après les comptes publics consignés dans `data/comptes-publics-reels-g0-15-v02-v03-2025-2026.json`.
- **2026–2027 projeté** : recettes 168 389 M$, dépenses 171 597 M$ avant la provision pour éventualités. **Ne pas additionner l'exercice réel à la prévision**.
- **Municipalités 2024** : environ **31,3 G$** de revenus des organismes municipaux consolidés, dont **7,4 G$ de transferts gouvernementaux**. Impossible d'additionner cette enveloppe au budget provincial d'un autre exercice sans rapprocher les transferts internes et les périmètres.
- **Eau 2023** : environ **2,4 G$ de recettes** contre **6,0 G$ de coût économique complet**, incluant des besoins d'investissements; l'écart **3,6 G$ n'est pas un déficit budgétaire annuel encaissable**. Son année et son périmètre sont différents.

Le rapprochement des CSV municipaux originaux MAMH **2024–2025** et la preuve de neutralisation des transferts internes restent à obtenir. Suivi : [issue #906](https://github.com/M0rdr3x/BenoitCantin/issues/906).

## 6. Conditions vérifiables pour avancer réellement

1. **Décomposer légalement toutes les catégories** de recettes, identifier ce qui demeure un impôt, une cotisation affectée, une redevance ou un dividende; lister précisément les prélèvements qu'une province peut modifier sans toucher aux impôts fédéraux.
2. **Établir les assiettes fiscales imposables** séparément des recettes existantes et la distribution des revenus des ménages et sociétés. Simuler le régime de Nova, ses coûts d'administration, l'évitement et les mesures anti-paradis fiscaux **nets des chevauchements**.
3. **Garantir le financement** des municipalités, réseaux d'eau, écoles, santé, pensions RRQ et RQAP sans effacer les droits acquis, sans licenciements supposés automatiques et sans doubler les transferts.
4. **Construire 10 budgets annuels** cohérents pour chaque scénario : dépenses/recettes, réserve, dette, investissement, transition, sensibilité à la croissance, inflation et récession; compléter les années 2031–2036 avec une méthode publique, marquées *projection propre à Nova* et jamais *prévision officielle*.
5. **Obtenir les avis indépendants** de droit, de finances publiques, de droits sociaux et de compétence constitutionnelle; consulter les parties concernées puis seulement envisager l'adoption formelle.

**Verrou : aucune suppression de taxe, aucun taux « deux prélèvements », aucun gain chiffré ni score supplémentaire Nova n'est autorisé par ce rapport.**

## 7. Outil technique reproductible

Le contrôleur pur `assets/g019-two-budget-reconciliation-core.mjs` recoupe **7 registres** en lecture seule. Il exécute les rapprochements de catégories, les cinq années de références, les dix exercices de chacun des deux scénarios, les comptes réalisés et les périmètres municipaux. Les **16 tests adversariaux** de `tests/g019-two-budget-reconciliation.test.mjs` doivent refuser la falsification de recettes, de transferts, d'années futures, de taux et de soldes.

Une CI « verte » signifie **cohérence de la copie du registre**, non certification des chiffres gouvernementaux, des lois, de la viabilité de Nova ou de la souveraineté.

**Décision au 8 novembre : 47 %, finances 3/16, 20 soldes Nova annuels non attestés, NO-GO de complétude.**
