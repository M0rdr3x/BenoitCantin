# Projet Nova — P52E : norme candidate de non-appauvrissement et test d'incidence des réformes fiscales

**18 octobre 2026 · ÉTUDE ET NORME CANDIDATES — NON ADOPTÉES · Aucune loi applicable · Aucun taux prescrit · NO_GO**

## 1. Problème à éviter

P52A définit l'objectif de deux prélèvements, P52B conserve une projection décennale sans valeurs inventées, P52C distingue les recettes publiques et P52D construit **42 cas conditionnels** (30 ménages, 12 entreprises) encore dépourvus de **720 montants**. Ces étapes ne prouvent pas qu'une réforme fiscale laisserait davantage d'argent aux ménages.

P52E fournit une **règle de vigilance** : toute proposition susceptible de diminuer le solde monétaire des ménages ou de transférer les charges vers les familles, les PME, les municipalités et les services doit être **identifiée, justifiée, corrigée ou expressément soumise à débat avant une décision publique**. Il ne s'agit ni d'un droit déjà en vigueur ni d'une promesse que zéro personne pourrait subir un coût dans toutes les circonstances. Une règle de ce type exige un instrument juridique et démocratique propre, un périmètre défini et des recours.

## 2. Texte normatif de travail — version non adoptée

**Principe P52E-1 — Analyse préalable obligatoire.** Toute réforme des impôts, taxes, cotisations, prestations et frais publics dans le périmètre de l'autorité compétente devrait faire l'objet d'une étude d'incidence ex ante : revenus, prestations, prélèvements, coûts de logement, consommation, services essentiels, emploi, PME, régions et municipalités.

**Principe P52E-2 — Prévention d'un appauvrissement caché.** Aucun responsable ne devrait présenter une économie ou un gain de revenu disponible comme acquis lorsqu'il résulte simplement d'un transfert de coûts, de la suppression implicite d'un service, d'une hausse de prix non mesurée ou d'un changement inexpliqué d'assiette ou de bénéficiaires. Les pertes ou risques doivent figurer explicitement dans le dossier de décision.

**Principe P52E-3 — Mesures d'atténuation examinables.** Lorsqu'une catégorie de ménages présente une perte monétaire — qu'elle soit fiscalement attribuable ou non — les décideurs devraient examiner des mesures ciblées et chiffrées (crédits/remboursements ou prestations légalement possibles, étalement des changements, garanties transitoires). Une mesure compensatrice **ne doit pas être considérée financée** sans source budgétaire et pouvoir juridique établis.

**Principe P52E-4 — Pouvoirs réellement détenus.** Dans le Québec demeurant au Canada, les impôts et prestations **fédéraux** ne peuvent pas être déclarés abolis par une loi fiscale québécoise. Dans un Québec souverain hypothétique, les conditions de continuité des droits, contrats, prestations, pensions, fiscalité internationale et institutions ne doivent pas être présumées déjà réalisées.

**Principe P52E-5 — Preuve contradictoire et recours.** Les modèles, hypothèses, catégories touchées, pertes possibles, coûts de correction, objections techniques et décisions devraient être publiés **seulement après approbation légitime**, sous réserve du secret fiscal et de la vie privée. Une éventuelle loi devrait prévoir la contestation des décisions individuelles, des délais, des motifs écrits et un contrôle indépendant.

**Principe P52E-6 — Pas de GO par algorithme.** Un score, une simulation positive ou une CI réussie ne remplace ni un audit indépendant, ni les consultations, ni le pouvoir du législateur, ni la protection des droits. Aucun résultat de P52E ne peut activer une réduction fiscale, percevoir un impôt ou promulguer une loi.

## 3. Mesures distinctes : solde monétaire et pouvoir d'achat

Le [Ministère des Finances du Québec](https://www.finances.gouv.qc.ca/ministere/outils_services/outils_calcul/revenu_disponible/) définit le revenu disponible en fonction des impôts, cotisations obligatoires et aides des **deux gouvernements**; son propre outil avertit qu'il ne couvre pas tous les types de revenus, déductions ni crédits.

Le gabarit P52D calcule une **différence monétaire annuelle par cas hypothétique**, à partir d'un nombre fini de postes. Il ne simule **ni inflation, ni coûts de logement, ni dégradation des services, ni incidence des taxes via les prix, ni distribution démographique**. L'expression « pouvoir d'achat des Québécois protégé » demeure donc **NON DÉMONTRÉE**, même si un ou plusieurs cas présentent une variation positive.

Pour un **ménage**, P52E classe :
- `DONNEES_MANQUANTES` : au moins un poste actuel ou proposé est inconnu;
- `CHANGEMENT_NON_FISCAL_A_ISOLER` : le revenu brut ou les prestations ont changé et la variation calculée n'est pas négative; **le gain apparent ne peut pas être attribué simplement à une baisse d'impôt**;
- `PERTE_AVEC_CHANGEMENT_NON_FISCAL_A_EXAMINER` : le revenu brut, les prestations ou certains postes opérationnels ont changé, **et le solde total du cas est négatif**. La perte doit être signalée même si sa cause fiscale ne peut pas être isolée;
- `PERTE_HYPOTHETIQUE_A_EXAMINER` : variation négative sur chiffres fictifs/non certifiés;
- `PERTE_MONETAIRE_A_CORRIGER` : variation négative dans un cas entièrement renseigné par des références documentaires (à **revérifier indépendamment**, pas un dommage individuel établi);
- `ILLUSTRATION_SANS_PERTE_A_CE_NIVEAU` et `PAS_DE_PERTE_DANS_CE_CAS_NON_REPRESENTATIF` : aucune perte dans ce **seul cas**, pas une garantie pour une région ou une population.

Pour une **entreprise**, une variation négative du solde opérationnel partiel déclenche une alerte `RISQUE_RESULTAT_ENTREPRISE` si les entrées sont documentaires, ou `PERTE_HYPOTHETIQUE_A_EXAMINER` si elles sont fictives. **Aucune perte d'emploi, augmentation de prix ou baisse de salaire n'est inférée automatiquement** d'un recul du solde de l'entreprise : ces effets demandent une analyse économique distincte.

## 3 bis. P52F — Ne pas masquer une perte par un changement non fiscal

**Défaut de la version précédente corrigé :** quand un salaire, une prestation, le chiffre d'affaires, un coût d'exploitation ou une subvention changeait entre les phases `actuel` et `propose`, le filtre classait uniquement le cas `CHANGEMENT_NON_FISCAL_A_ISOLER`. Même avec une **variation totale négative**, cette perte n'entrait pas dans le nombre de cas à risque de perte. Une simulation aurait donc pu paraître moins défavorable qu'elle ne l'était réellement.

P52F distingue deux obligations simultanées :

1. **Constater la perte monétaire dans le cas** : toute variation totale négative est signalée, y compris si un paramètre extérieur à la fiscalité a changé. Un ménage dont le revenu ou une prestation diminue, ou une entreprise dont le chiffre d'affaires se contracte, ne doit pas disparaître du registre des risques.
2. **Ne pas inventer l'attribution causale** : la variation est décomposée en **postes non fiscaux directement saisis** et **résidu des autres postes comptables**, pour chaque cas **entièrement renseigné seulement**. Le résidu n'est ni une estimation causale de la réforme ni une variation de pouvoir d'achat. Le rapport renvoie `null` pour ces éléments lorsqu'une seule donnée nécessaire manque.

Pour un ménage, les postes non fiscaux sont la variation du revenu brut et des deux catégories de prestations. Pour une entreprise, il s'agit du chiffre d'affaires, des coûts d'exploitation hors salaires, de la masse salariale et des subventions. **La différence entre variation totale et variation de ces postes n'est qu'un calcul additif**, jamais un effet fiscal isolé par une méthode économétrique. Les 42 cas restent fictifs ou non représentatifs tant que leurs entrées n'ont pas été auditées.

Le rapport comporte :
- `risque_de_perte_dans_ce_cas` pour chaque ménage/entreprise;
- `decomposition_comptable.variation_postes_non_fiscaux_cad`, `variation_autres_postes_comptables_cad` et `somme_verifiee`;
- `cas_avec_perte_et_variation_non_fiscale` et le compteur global de cas à risque.

**Aucun indicateur agrégé au Québec ne peut être calculé en additionnant ces cas** : ils n'ont aucun poids représentatif et ne couvrent pas les répercussions des politiques sur prix, logements, services, emplois ou fiscalité municipale. Aucun prélèvement, mesure compensatoire ou réduction de service n'est autorisé.

## 4. Méthode de validation technique

Script : `scripts/evaluer_garde_fous_revenu_nova_p52e.py`.

Le filtre **recalcule lui-même les 42 cas à partir du gabarit P52D**, plutôt que faire confiance à un rapport qui pourrait être obsolète ou altéré. Il vérifie les mêmes catégories, références et limites, et refuse de confondre les données documentaires et les hypothèses fictives. Pour les ménages, il compare les scénarios en tenant séparés les changements de revenu brut et de prestations; pour les entreprises, il isole également chiffre d'affaires, coûts d'exploitation, salaires et subventions.

Le rapport ne contient **aucune donnée personnelle ni pondération démographique**, car le gabarit n'en inclut pas. Il n'est pas destiné à recevoir des microdonnées privées identifiantes sur GitHub. Les cas de test contiennent exclusivement des valeurs fictives et explicitement signalées.

### Commandes

```bash
python scripts/evaluer_garde_fous_revenu_nova_p52e.py \
  --gabarit projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json \
  --rapport p52e_constat_local.json
```

Le mode suivant **doit retourner 3** à l'étape actuelle : les cas sont incomplets et aucune preuve de représentativité ou d'effets indirects n'a été établie.

```bash
python scripts/evaluer_garde_fous_revenu_nova_p52e.py \
  --gabarit projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json \
  --exiger-non-appauvrissement-demontre \
  --rapport p52e_refus_local.json
```

Les codes `0` (rapport produit), `2` (données invalides) et `3` (preuve de non-appauvrissement non obtenue) ne sont **jamais des autorisations légales**.

## 5. Critères de contrôle politique — tous non validés

| Porte | Preuve future nécessaire | Statut initial |
|---|---|---|
| E1 | Microdonnées québécoises légalement utilisables et échantillonnage représentatif, y compris les ménages sans déclaration standard | NON VALIDÉ |
| E2 | Impôts nets, cotisations, crédits et prestations réellement applicables avec vérification par fiscaliste | NON VALIDÉ |
| E3 | Taxes de consommation effectivement supportées par différents ménages, sans supposer leur transmission intégrale | NON VALIDÉ |
| E4 | Effets prix, inflation, logement et services essentiels à court et long terme | NON VALIDÉ |
| E5 | Effets sur emploi, salaires, petites entreprises, municipalités, régions et coût des services | NON VALIDÉ |
| E6 | Attribution causale crédible entre réforme fiscale et changements de revenus ou de prestations | NON VALIDÉ |
| E7 | Identification des cas perdants, mécanismes d'atténuation, coûts et voies de recours | NON VALIDÉ |
| E8 | Financement public des mesures de correction et maintien des seuils de prudence P52A | NON VALIDÉ |
| E9 | Compétence juridique, consultation et décision démocratique compétente | NON VALIDÉ |

Ces portes ne sont **pas** satisfaites par les 42 catégories génériques. Le calculateur public de revenu disponible et le [plan québécois de lutte contre la pauvreté et l'exclusion sociale 2024-2029](https://www.quebec.ca/gouvernement/ministeres-organismes/emploi-solidarite-sociale/publications/lutte-pauvrete-exclusion-sociale) fournissent un contexte, **sans approuver la norme P52E**.

## 6. Liens avec le financement et les autres travaux

P52B conserve **600 montants annuels inconnus** et P52A **20 preuves fiscales à obtenir**. P52C rapproche **21 postes budgétaires**, sans démontrer de nouvelles assiettes fiscales finançables. Les **720 inconnues** de P52D appartiennent à une **autre grille**, de comparaison entre catégories de ménages et d'entreprises : **ne pas les additionner comme s'il s'agissait de 1 320 preuves distinctes**.

Le résultat de P52E ne doit jamais être présenté comme un calcul de taux d'impôt ni comme une protection garantie. La politique « seulement deux prélèvements » reste **PROPOSITION**, avec distinction entre compétences provinciales et hypothèse souveraine.

La PR673 est en brouillon; les textes `official/reference` et pages publiques restent inchangés. Les revues et décisions administratives des [PR672](https://github.com/M0rdr3x/BenoitCantin/pull/672), [#135](https://github.com/M0rdr3x/BenoitCantin/issues/135) et [#662](https://github.com/M0rdr3x/BenoitCantin/issues/662) demeurent nécessaires. **PR640 : NE PAS FUSIONNER.**

**Décision P52E : DIAGNOSTIC NON REPRÉSENTATIF — AUCUN ÉTAT DE NON-APPAUVRISSEMENT PROUVÉ — NO_GO.**
