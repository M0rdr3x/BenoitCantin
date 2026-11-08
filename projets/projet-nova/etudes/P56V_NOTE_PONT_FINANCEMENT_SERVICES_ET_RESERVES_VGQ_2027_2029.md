# Projet Nova — P56V : pont de financement 2027–2029 et test de continuité des services

**8 novembre 2026 — Étude de risque et dossier de décision du programme candidat. Statut : `NO_GO_AUTOMATIQUE`.**

## 1. Décision à éclairer

L'objectif du Projet Nova est une fiscalité à deux prélèvements, davantage de revenu disponible, le maintien de la main-d'œuvre et des services publics. Cette réforme ne serait financièrement responsable que si les revenus de remplacement, les coûts des services, les crédits et prestations des ménages et les effets sur les entreprises étaient vérifiés **avant** de supprimer une recette existante.

Les études P56P à P56U ont établi le cadre public de référence, trois scénarios statiques et les premières lignes sectorielles de dépenses. P56V met ces données en regard pour les **deux exercices communs 2027-2028 et 2028-2029**, et ajoute une réserve majeure signalée par la Vérificatrice générale du Québec : le cadre public repose déjà sur des réductions ou ralentissements d'activités. **Le coût budgété actuel n'est pas la preuve que les besoins de services seraient intégralement couverts.**

## 2. Les sources et leurs limites

- [Rapport préélectoral 2026 du ministère des Finances](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf), publié **17 août 2026**, tableau 2, page imprimée 17 (revenus, dépenses, dette, provisions, soldes); tableau 25, page imprimée 81 (portefeuilles 2025-2026 à 2028-2029). Les montants sont ceux du **gouvernement actuel**, pas de Nova.
- [Vérificateur général du Québec, communiqué du 17 août 2026](https://www.vgq.qc.ca/fr/communique/C2026-3). Le VGQ juge globalement plausibles, au **10 juillet 2026**, les hypothèses et les prévisions pour **2026-2027 à 2028-2029**. Il précise cependant que ce jugement **n'évalue pas la qualité, la quantité ou l'adéquation des services**.
- Le VGQ estime des **efforts budgétaires d'au moins 2 G$ en 2027-2028 et d'au moins 3 G$ en 2028-2029**, associés à la réduction ou à la fin d'activités/programmes. **En 2028-2029, un écart à résorber de 1,85 G$ pourrait aussi s'ajouter** aux efforts. Ces montants ne constituent pas une évaluation de politiques Nova et ne sont pas nécessairement des postes additionnels au cadre financier publié.

L'avis du VGQ vise **la plausibilité du cadre du gouvernement**, non la viabilité d'une réforme fiscale Nova. Le mandat du VGQ n'authentifie ni nos calculs Python ni un budget souverain.

## 3. Deux exercices avec finances et services rapprochés

**Toutes les sommes sont exprimées en millions de dollars canadiens (M$).**

| Rubrique du régime actuel | 2027-2028 | 2028-2029 |
|---|---:|---:|
| Revenus consolidés | 174 225 | 178 844 |
| Dépenses de portefeuilles | 165 049 | 166 666 |
| Service de la dette, hors portefeuilles, mais inclus dans le total | 10 870 | 11 402 |
| Total des dépenses hors provision | **175 919** | **178 068** |
| Provision pour éventualités | 1 500 | 1 500 |
| Versements au Fonds des générations | 2 501 | 2 626 |
| Écart à résorber du plan gouvernemental | 0 | 1 850 |
| Solde budgétaire au sens de la Loi, **avec** résorption prévue | **−5 695** | **−1 500** |
| Solde sans présumer la résorption de l'écart | **−5 695** | **−3 350** |
| Sous-total santé + éducation + supérieur + famille (**déjà inclus**) | **120 433** | **123 776** |
| Sous-total de sept grands portefeuilles (**déjà inclus**) | **140 657** | **142 894** |
| Efforts budgétaires **minimum estimés** par le VGQ | au moins **2 000** | au moins **3 000** |

**Trois précautions comptables :**

1. Les sous-totaux de quatre ou sept portefeuilles sont inclus dans les dépenses de portefeuilles. Ils ne doivent pas être additionnés une seconde fois.
2. Le service de la dette est déjà compris dans le total de **175 919 M$** ou de **178 068 M$**. Les provisions et le Fonds des générations ont des traitements distincts dans le calcul du solde au sens de la Loi.
3. Les efforts budgétaires d'au moins **2 000 M$ et 3 000 M$** recensés par le VGQ **ne doivent pas être ajoutés** aux dépenses de portefeuilles comme si c'était un nouveau coût de Nova, ni soustraits des dépenses comme de nouvelles économies Nova. Ils constituent des **risques de capacité de service et de soutenabilité** à documenter au niveau des programmes.

Le chiffre des efforts ne prouve ni un licenciement précis, ni une réduction de tel service particulier : la ventilation de ces efforts par programme est encore manquante. Une hypothèse de **maintien intégral des services** exigerait de vérifier quelles activités sont déjà menacées ou sous-financées dans le point de départ.

## 4. Les trois stratégies de P56S, comparées avec les contraintes des services

**L'effet ci-dessous est une soustraction statique de recettes provinciales existantes, toutes les autres hypothèses du gouvernement actuel étant maintenues.** Il ne s'agit pas de la réforme Nova adoptée.

| Exercice et stratégie | Recettes supprimées dans le test (M$) | Solde au sens de la Loi **sans remplacement ni résorption non démontrée** |
|---|---:|---:|
| 2027-2028 — S1 continuité provisoire | 0 | **−5 695** |
| 2027-2028 — S2 test illustratif 25 % | 10 718,75 | **−16 413,75** |
| 2027-2028 — S3 test illustratif 100 % | 42 875 | **−48 570** |
| 2028-2029 — S1 continuité provisoire | 0 | **−3 350** |
| 2028-2029 — S2 test illustratif 25 % | 11 042,25 | **−14 392,25** |
| 2028-2029 — S3 test illustratif 100 % | 44 169 | **−47 519** |

Le test à 25 % est une **sensibilité arithmétique**, pas un calendrier de mise en œuvre ni un taux d'imposition. Le test à 100 % ne retire que les **trois rubriques déjà étudiées** — taxes à la consommation, cotisations FSS, taxe scolaire — et **non** toutes les catégories de prélèvements. La TPS et les autres impôts fédéraux ne sont pas supprimables par une simple décision provinciale.

Pour 2028-2029, la différence de **1 850 M$** entre les soldes avec et sans résorption illustre le risque de considérer un ajustement annoncé comme déjà réalisé. Ce montant ne peut être considéré comme une économie disponible pour Nova.

**Aucune de ces simulations ne comprend une recette Nova effectivement établie, un revenu anti-paradis fiscaux certifié, un taux candidat, les conséquences sur le revenu disponible des ménages, les coûts de transition ou les besoins réels supplémentaires de services.** Ces données demeurent inconnues, non nulles.

## 5. Examen d'une condition fondamentale : maintenir les services publics

La garantie proposée dans le chapitre P56U doit être démontrée au moyen d'une analyse *service par service*. Pour chaque mission, le dossier doit établir :

- les obligations légales, les bénéficiaires, le besoin observé et la capacité minimale attendue;
- les crédits budgétaires, les paiements, les transferts entre organismes et les coûts d'investissements;
- les effectifs, la rémunération, les conditions de travail et les effets sur l'emploi;
- les activités ou budgets soumis aux efforts gouvernementaux déjà anticipés par le VGQ;
- la source de financement prévue sous chaque option fiscale et sa sensibilité aux aléas;
- les compensations nécessaires pour protéger les familles, les aînés, les PME et les ménages modestes;
- les avis juridiques et comptables contradictoires et les décisions formelles.

**Une somme globale de 165,049 G$ n'est pas, à elle seule, un certificat de continuité des services.**

## 6. Différence entre Québec dans le Canada et Québec souverain

Le rapprochement chiffré P56V porte **exclusivement sur le Québec dans le Canada**. Les transferts fédéraux qui figurent dans la base publique ne sont pas des ressources automatiquement conservées dans un budget souverain.

Un budget de **Québec souverain hypothétique** devrait étudier les recettes fiscales relevant éventuellement de nouvelles compétences ainsi que les dépenses pour la défense, les frontières, les pensions, la dette, les actifs, les administrations et les négociations. **Toutes ces valeurs Nova restent inconnues et ne sont pas substituées par les données provinciales.**

## 7. Dix preuves à obtenir pour débloquer la suite

Le fichier P56V suit dix besoins de preuve, notamment :

1. La définition des **assiettes de revenus et des bénéfices** soumises aux deux prélèvements.
2. Les **services à maintenir et les besoins actuellement non financés**.
3. Les charges réelles de main-d'œuvre et de continuité des effectifs.
4. L'incidence sur les ménages par **décile, région et composition familiale**.
5. Les coûts du régime souverain, ses compétences et ses engagements.
6. La réconciliation des transferts municipaux et scolaires.
7. Les **budgets 2027-2036**, sur deux régimes et trois scénarios.
8. La ventilation des **efforts budgétaires minimum signalés par le VGQ**.
9. Les **avis indépendants signés**.
10. La consultation et l'approbation formelle des textes politiques candidats.

Ces dix pièces demeurent **non démontrées** dans ce jalon. Le programme ne peut pas être déclaré complet sur la base de la rédaction d'un chapitre ou du succès des tests informatiques.

## 8. Travail intégré dans GitHub

Ce jalon contient une base structurée `P56V_PONT_FINANCEMENT_SERVICES_OPTIONS_FISCALES_VGQ_2027_2029.json`, un vérificateur `scripts/verifier_pont_financement_services_nova_p56v.py`, des tests de non-régression et une validation GitHub.

Le vérificateur compare les deux exercices des registres P56P, P56S, P56T et P56O, recalculant **six scénarios comptables**. Il bloque une annonce de budget financé lorsque les données de remplacement, de protection des ménages, de continuité des services ou de contre-expertise sont manquantes. **Il ne certifie pas les publications externes ni la politique Nova.**

### Suite ciblée : P56W

La prochaine étape consiste à produire **une matrice de décision et de preuves pour 2027-2028**, avec responsables, coût estimé de validation et interdictions de mise en œuvre, pour diriger les efforts vers les données et les avis indépendants qui manquent le plus. La décision de suppression ou de substitution d'un prélèvement doit rester bloquée tant que la couverture financière et les droits ne sont pas prouvés.

**Avancement : 53 % estimés, 47 points estimés restants.** Les 600 valeurs budgétaires P52B, 720 incidences P52D, 20 preuves fiscales P52A et dix portes P56O demeurent ouvertes. Aucun taux Nova ni budget souverain n'est certifié. `NO_GO_AUTOMATIQUE`.

Aucune fusion dans `main`; SINJIRA inchangé. Demande de fusion #673 en brouillon.
