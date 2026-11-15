# NOVA-SINJ-FIN-001 — Modélisation financière comparée des services publics
Version de travail 1.0 — 3 novembre 2026  
**Statut :** méthode et prototype non certifiés, sans résultats de coûts sectoriels réels. Ni économies acquises, ni promesses fiscales, ni lancement de prestation.  
**Projet politique :** Projet Nova. L'esprit SINJIRA™ constitue un cadre d'examen humain, sans être une source autonome de droit ni un programme politique distinct.

## 1. Question économique à résoudre
Pour une population, un territoire, une qualité, une complexité de cas et un horizon identiques : quel est le coût de trois modes de prestation possibles? (1) service public actuel **et son amélioration raisonnablement faisable**, (2) prestataire privé agréé, (3) coopérative ou organisme sans but lucratif. Les options ne sont pas des catégories de qualité : elles sont des structures organisationnelles à évaluer.

Un service plus rapide mais plus cher, ou moins cher mais moins sûr, ne peut pas être déclaré « plus efficace » sans un arbitrage transparent des résultats et des coûts.

## 2. Références vérifiées et limites
### Budget du Québec — mars 2026, exercice 2026–2027
Montants en **millions de dollars** dans le Plan budgétaire, tableau F.2 :
- Revenus consolidés : **166 492**.
- Dépenses de portefeuilles : **160 489**.
- Service de la dette : **10 268**.
- Dépenses consolidées : **170 757**.
- Provision pour éventualités : **2 000**.
- Solde comptable avec provision : **–6 265**.
- Versements au Fonds des générations : **2 347**.
- Solde budgétaire au sens de la loi : **–8 612**.
Source primaire : https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf (section F).

Contrôle : 166 492 – 170 757 – 2 000 = –6 265; –6 265 – 2 347 = –8 612. Il s'agit de prévisions budgétaires publiées en mars 2026, **pas de comptes exécutés**.

### RAMQ — exercice 2024–2025
- Coût des programmes administrés par la RAMQ : **14 232 millions $**.
- Rémunération des médecins, services médicaux : **8 662 millions $**.
- Médicaments et services pharmaceutiques : **4 469 millions $**.
- Autres programmes : **1 101 millions $**.
Source primaire : https://www.ramq.gouv.qc.ca/fr/donnees-statistiques/ramq-quelques-chiffres .

**Attention :** le coût de programmes RAMQ ne représente ni l'intégralité des dépenses de santé ni une somme additive au budget consolidé provincial. Le paiement de la RAMQ n'est pas le coût total de chaque épisode clinique et il peut y avoir des chevauchements entre dépenses d'organismes.

### Comparabilité hospitalière
L'ICIS emploie un coût par cas pondéré pour tenir compte des différences de ressources requises selon les patients. Les tableaux publics ne suffisent pas, à eux seuls, à démontrer les économies d'une réforme d'exploitation.
Source : https://www.cihi.ca/fr/indicateurs/cout-dun-sejour-standard-a-lhopital-cssh (mise à jour mai 2026, données 2020–2024).

### État des connaissances sur le privé en santé
La revue du CIRANO du 18 septembre 2026 conclut qu'il est difficile d'établir une supériorité générale du privé en coût, attente et qualité; elle signale notamment des risques sur l'accès et l'équité. Ce résultat motive une **comparaison conditionnelle par service**, plutôt qu'une projection chiffrée globale.
Source : https://cirano.qc.ca/index.php/fr/sommaires/2026PR-10 .

Les repères précités sont transcrits avec leurs périodes et périmètres dans `data/reperes-financiers-nova-sinjira-2026.json`. **Aucun coût fictif d'un service n'a été injecté dans l'outil de calcul.**

## 3. Définition des trois dimensions de coût
**A. Coût réel de prestation (ressources)** : rémunération, fournitures, maintenance, logistique, immobilier, soutien, technologie et autres ressources effectivement utilisées; la dépréciation / annuité du capital doit être distincte, sans double compte.

**B. Coût annuel pour le payeur public** : montant réellement versé/imputé pour chaque épisode comparable + coûts publics additionnels de réglementation/administration + coûts de complications et aval supportés par l'État + dépenses annualisées de transition et de réserve. Le tarif facturé n'est pas nécessairement égal au coût de production.

**C. Coût social total** : ressources réelles de l'opérateur + annuité de capital + administration publique additionnelle + coût réel des complications/retours aux services + débours **additionnels** des citoyens + temps non rémunéré des proches converti par méthode explicite + transition et capacité de réserve.

Les taxes entre acteurs publics et privés et les bénéfices commerciaux peuvent être des transferts financiers plutôt que des consommations réelles de ressources; ils influencent le coût pour le payeur sans être assimilés automatiquement à une perte économique totale. Les bénéfices et les effets distributifs doivent être publiés séparément et discutés. Les coûts des usagers doivent être **incrémentaux** et non déjà compris dans le coût de production.

Le « coût social » ici est un **proxy partiel** des ressources valorisées, et non une analyse coûts-bénéfices exhaustive : effets sanitaires de long terme, externalités, effets distributifs et valeur du temps restent à compléter.

## 4. Variables dans le comparateur public
Chaque option est exprimée en **dollars canadiens de la même année**, volume annuel de services strictement équivalents, qualité comparable, même degré de gravité. Une ligne de coût unitaire est en $CA par épisode; une ligne fixe est en $CA par an.

| Identifiant technique | Variable à obtenir | Type |
| --- | --- | --- |
| paiementPublic | Paiement public ou coût budgétaire **imputé** par épisode; pour une option publique, inclure le coût de fonctionnement dans l'imputation | Unitaire |
| administrationPublique | Coût supplémentaire d'administrer et auditer le mode, hors tarif | Unitaire |
| coutAvalPublic | Coûts de complications, redirections et soins ultérieurs **non déjà inclus**, supportés par l'État | Unitaire |
| ressourcesReelles | Ressources réelles de production, excluant capital présenté à part | Unitaire |
| capitalAnnualise | Coût d'usage annuel du capital réparti entre épisodes, sans recomptabiliser intérêts/amortissements | Unitaire |
| fraisUsagers | Débours induits des usagers, non déjà comptés ailleurs | Unitaire |
| tempsProches | Valeur économique des heures supplémentaires des proches, méthode à publier | Unitaire |
| transitionAnnuelle | Quote-part annuelle des coûts de transition et de lancement | Fixe annuel |
| reserveAnnuelle | Financement annuel du maintien de la continuité, capacités de secours et sortie | Fixe annuel |

Le formulaire compare les mêmes **volumes de services** pour éviter les fausses économies dues à moins de patients traités. Une option incapable d'offrir la même capacité/qualité doit être analysée séparément avec un modèle de résultats, pas dans ce calculateur seulement.

### Formules
Pour un volume annuel V :
- **Coût payeur annuel** = V × (paiementPublic + administrationPublique + coutAvalPublic) + transitionAnnuelle + reserveAnnuelle.
- **Coût social partiel annuel** = V × (ressourcesReelles + capitalAnnualise + administrationPublique + coutAvalPublic + fraisUsagers + tempsProches) + transitionAnnuelle + reserveAnnuelle.
- **Écart** = coût de l'option examinée – coût de référence, à périmètre comparable. Un écart négatif n'est pas une économie attestée; il indique le résultat **des chiffres saisis**.
- **Par épisode** = coût annuel ÷ V, pour l'une ou l'autre perspective.

**Limite importante :** la rubrique coutAvalPublic est utilisée comme approximation d'un coût réel de ressources dans la formule sociale. Elle doit être remplacée par le coût économique aval observé si les prix, remboursements et ressources divergent. La formule doit être adaptée si des transferts, revenus, immobilisations déjà comptées ou autres postes se chevauchent. Les coûts du maintien du modèle public (public de secours) doivent être inclus dans le périmètre examiné si nécessaires à la proposition.

## 5. Conditions de validité — avant toute comparaison publique
Une fiche est recevable si :
1. La description du service/épisode est la même dans toutes les options.
2. Le volume, la qualité, l'horizon et la devise (année de prix) concordent.
3. La gravité/casemix est comparable ou ajustée selon une méthode justifiable, notamment la pondération hospitalière ICIS si pertinente.
4. Les coûts directs, indirects, immobiliers, de transition, de surveillance et d'aval sont traçables et sans double comptage.
5. Les obligations de la Loi canadienne sur la santé et de la loi québécoise applicable sont respectées.
6. Les effets sur la main-d'œuvre (départs, recrutement, formation, heures supplémentaires) dans **tous** les établissements concernés sont mesurés.
7. Les prix des contrats publics et les taux d'utilisation sont documentés, pas des offres hypothétiques présentées comme exécution.
8. Les conséquences pour les patients complexes, les zones rurales et les personnes vulnérables sont publiées.
9. L'évaluateur est indépendant et une méthode d'incertitude/sensibilité est annoncée.
10. Le décideur publie l'analyse défavorable comme l'analyse favorable et maintient les voies de plainte et de recours.

## 6. Analyses à produire par service après acquisition des données
### Format de fiche de service
- ID, intitulé, organisme responsable, région, début/fin, unité de service.
- Définition des cas, exclusions **médicales ou légales** et risque de sélection.
- Volume annuel par groupe de risque; capacité de pointe et qualité minimale.
- Mode actuel et amélioration publique raisonnable documentée.
- Hypothèses et coûts comptables pour les modes comparés, prix constants.
- Évolution des budgets et prix sur plusieurs années; investissements et coûts irrécupérables.
- Scénarios de demande, inflation, complexité, recrutement et temps d'arrêt.
- Indicateurs qualité : délais (médiane/p90), sécurité, plaintes, continuité, satisfaction, couverture territoriale, équité.
- Incidence sur travailleurs, usagers, municipalités, communautés autochtones concernés.
- Comptabilité des paiements, actifs, coûts réels et des effets de déplacement.
- Source pour chaque valeur, fiabilité, audit, date et droits de diffusion.
- Décision G0 à G4 avec justifications, mesures correctives et sortie.

### Échelle de travaux
**Pilotes de comparaison à délimiter** : soutien administratif / rendez-vous; services à domicile; certains services diagnostiques ou procédures planifiées juridiquement permis; entretien et infrastructure; technologies d'accès; transport local. Les chiffres spécifiques sont **inconnus à ce stade** : ne pas afficher d'économies.

## 7. Tests de sensibilité et robustesse
Réaliser au minimum les analyses *aucun changement*, **décalage des volumes**, inflation différentielle des coûts, hausse du coût de la main-d'œuvre, défaillance contractuelle, besoin additionnel en personnel public, sélection de cas, et conséquences de la perte de concurrence. Montrer l'intervalle et la sensibilité de l'écart; aucune extrapolation de cas limités à l'ensemble du Québec sans preuve représentative.

## 8. Articulation avec la fiscalité de Projet Nova
Aucune somme de résultats hypothétiques par service ne peut être utilisée pour financer des baisses d'impôts avant économies nettes démontrées, récurrentes, encaissées dans le bon périmètre et inscrites au budget après audit. Respecter le cadre financier officiel candidat actuel de Projet Nova et sa règle de prudence (équilibre préalable et dette nette de 45 % du PIB au plus avant une réduction fiscale majeure). Les montants RAMQ sont inclus dans des périmètres publics et ne sont pas des recettes libres nouvelles.

## 9. Code, tests et limites d'interface
- Calcul public : `assets/comparateur-financier-core.mjs`.
- Interface : `comparateur-couts-services.html`.
- Jeux d'essais **purement synthétiques et non représentatifs du Québec** : `tests/comparateur-financier.test.mjs`; exécuter `node --test projets/projet-nova/tests/comparateur-financier.test.mjs` à partir de la racine du dépôt.
- Le calcul se fait dans le navigateur, sans transmission volontaire de données à un serveur par cet outil; aucune conservation des saisies par le script.
- Le calcul ne vérifie ni sources fournies par les utilisateurs, ni efficacité causale, ni qualité clinique, ni conformité juridique; résultats **simulés, non certifiés**.

## 10. Références associées
- Architecture Nova–Sinjira 0.1.
- NOVA-SINJ-IMP-001 Plan d'exécution (G0 à G4).
- NOVA-SINJ-SAN-001 Protocole de santé RAMQ.
- NOVA-SINJ-CON-001 Cahier des charges.
- NOVA-SINJ-DEC-001 Registre de décisions.
- Projet Nova : `official/reference/finances.md` (document officiel candidat conservé).

**Il faudra confronter toute version calculée aux comptes sectoriels disponibles, à une expertise comptable et aux analyses juridiques avant de formuler une proposition financée.**
