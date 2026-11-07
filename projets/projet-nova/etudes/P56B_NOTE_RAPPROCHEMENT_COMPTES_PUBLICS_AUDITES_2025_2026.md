# Projet Nova — P56B : rapprochement des versions des comptes du Québec, exercice 2025-2026

**Date : 7 novembre 2026. Statut : étude de vérification documentaire candidate, non adoptée. Décision : `NO_GO_AUTOMATIQUE`.**

## Objectif

Le travail P56A a établi **600 valeurs financières inconnues** dans les 60 lignes du modèle P52B (2027-2036, deux régimes constitutionnels, trois trajectoires). P56B doit commencer à **rassembler de véritables données financières officielles**, en vérifiant à quoi chaque valeur correspond, et surtout **ne pas les introduire directement comme projections**.

Une source officielle récente, fondamentale, est désormais disponible : les **Comptes publics 2025-2026, volume 1**, publiés en juillet 2026, contenant les états financiers consolidés du Québec audités avec une opinion du Vérificateur général du Québec. Les chiffres officiels audités ne doivent pas être confondus avec les **résultats préliminaires publiés le 11 juin 2026**. L'opinion de l'auditeur porte sur les états financiers gouvernementaux, **pas sur la fiscalité ni sur le projet Nova**.

## Sources primaires et pages vérifiables

| Référence | Source | Date/statut | Pages |
|---|---|---|---|
| Q1 | [Comptes publics 2025-2026 — Volume 1](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Comptes-publics/FR/CPTFR_vol1-2025-2026.pdf) | Juillet 2026; états financiers audités | PDF p. 12 (page imprimée 5), PDF p. 15 (imprimée 8), PDF p. 14 (imprimée 7) |
| Q2 | [Rapport sur la situation financière, résultats préliminaires de 2025-2026](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapports_situation_financiere/TRIMFR_SIFIN_4T_25-26.pdf) | 11 juin 2026; non audité (information au 1er juin) | PDF p. 3 (imprimée 3), PDF p. 1 (faits saillants) |
| Q3 | [Publications du ministère des Finances](https://www.quebec.ca/gouvernement/ministeres-organismes/finances/publications) | Rapport préélectoral 2026 et outil de simulation **amendé le 3 septembre 2026**, à rapprocher ultérieurement | Catalogue public |
| Q4 | [Volumes des comptes publics](https://www.quebec.ca/gouvernement/finances-publiques/budget-comptes-publics/comptes-publics/volumes-comptes-publics) | Distinction volume 1 consolidé, volume 2 fonds général et fonds spéciaux | Catalogue public |

Les numéros PDF sont indiqués en base humaine dans la présente note; le jeu de données P56B utilise les **indices PDF informatiques commençant à zéro**, pour éviter toute ambiguïté.

## Tableau 1 : les différentes versions de 2025-2026, en millions de dollars

Les valeurs négatives indiquent un déficit ou des versements du Fonds des générations (en M$). Les **dépenses totales** sont exprimées comme valeurs positives.

| Indicateur 2025-2026 (M$) | Budget initial, tel que repris dans comptes audités | Résultats préliminaires juin 2026 | Comptes audités juillet 2026 |
|---|---:|---:|---:|
| Total des revenus | 156 342 | 161 113 | **160 428** |
| Total des dépenses | 165 772 | 166 009 | **165 930** |
| Provision pour éventualités du budget initial | 2 000 | Non reportée | Non reportée |
| Solde comptable | −11 430 | −4 896 | **−5 502** |
| Versements au Fonds des générations | −2 177 | −2 289 | **−2 289** |
| Solde au sens de la Loi sur l'équilibre budgétaire | −13 607 | −7 185 | **−7 791** |
| Dette nette en % du PIB au 31 mars 2026 | Non reprise dans cette sélection | 38,0 % | **38,1 %** |

Note de méthode : la colonne « Budget initial » est **reprise et, pour certaines catégories, reclassée** dans les comptes publics audités afin d'assurer la comparabilité. Il ne faut donc pas la présenter comme une transcription indépendante de toutes les pages du budget d'origine.

## Tableau 2 : écarts de versions, sans confusion avec une économie Nova

| Comparaison, sur le même exercice 2025-2026 | Différence |
|---|---:|
| Recettes, préliminaire vers audité | **−685 M$** |
| Dépenses, préliminaire vers audité | **−79 M$** |
| Solde comptable, préliminaire vers audité | **−606 M$** |
| Solde LEB, préliminaire vers audité | **−606 M$** |
| Solde comptable, budget initial vers audité | **+5 928 M$** |
| Solde LEB, budget initial vers audité | **+5 816 M$** |
| Ratio dette nette/PIB, préliminaire vers audité | **+0,1 point** |

Contrôles exacts :
- Préliminaire : 161 113 − 166 009 = **−4 896 M$**.
- Audité : 160 428 − 165 930 = **−5 502 M$**.
- Variation du solde : (−685) − (−79) = **−606 M$**.
- Budgété initial : 156 342 − 165 772 − 2 000 (provision) = **−11 430 M$**.
- Solde légal audité : −5 502 − 2 289 = **−7 791 M$**.

Le **service de la dette figure déjà dans les dépenses totales** : ne jamais l'ajouter encore une fois. Les **versements au Fonds des générations** distinguent le solde légal du solde comptable, sans constituer une nouvelle recette ou une économie automatique. Les **606 M$ d'écart** entre versions ne sont pas des économies publiques obtenues ou perdues par Nova.

## Registre et outil de contrôle

Fichiers ajoutés à la demande de fusion candidate :
- `projets/projet-nova/etudes/P56B_SNAPSHOTS_FINANCES_2025_2026_SOURCES_OFFICIELLES.json` : trois versions, sources exactes et indices de pages par métrique.
- `scripts/rapprocher_versions_finances_nova_p56b.py` : comparaison déterministe avec contrôle d'exercice, unité, source, statut, équations comptables et anti-doublon.
- `scripts/tests/test_rapprocher_versions_finances_nova_p56b.py` : tests reproductibles des chiffres et des refus.
- `.github/workflows/validate-nova-p56b.yml` : test automatique dans la branche candidate.
- Cette note.

Commande depuis la racine du dépôt :

```bash
python scripts/rapprocher_versions_finances_nova_p56b.py \
  --entree projets/projet-nova/etudes/P56B_SNAPSHOTS_FINANCES_2025_2026_SOURCES_OFFICIELLES.json
```

Un changement de millésime, statut audité/non audité, source officielle, page d'origine, formule ou périmètre est rejeté. **Le script authentifie les références structurées et vérifie les identités arithmétiques; il n'authentifie pas cryptographiquement les PDF ni l'ensemble des écritures gouvernementales.** Aucune déclaration d'adoption, d'efficacité fiscale ou de financement n'est déduite d'un test réussi. Un rapport existant n'est pas écrasé.

## Ce qui est obtenu, et ce qui reste ouvert

**P56B a établi un rapprochement documentaire précis pour l'exercice clos le 31 mars 2026, dans le Québec actuel.** Ce constat améliore la qualité des *sources de départ*; il n'établit pas la trajectoire financière 2027–2036.

Avant de renseigner une cellule P52B, il faudra :
1. sélectionner la **version comptable définitive** et fournir le tableau de passage à la nomenclature P52B;
2. rapprocher les années 2026-2027 avec les budgets, le rapport préélectoral, son outil amendé le 3 septembre, les rapports trimestriels et les nouvelles normes de présentation de la dette;
3. éliminer les écritures intragouvernementales et distinguer dette, service de la dette et provisions;
4. définir le scénario **Québec au sein du Canada** selon les compétences provinciales et, séparément, le scénario souverain hypothétique avec coûts, actifs, dettes, traités et droits acquis;
5. obtenir les études de rendement des deux prélèvements, les effets sur ménages/PME, la continuité des emplois et des services et les avis juridiques et actuariels signés.

**Niveau de maturité du programme : 53 % estimatif, fourchette 45–60 % (P55N), non revalorisé ici.** Les **600 valeurs budgétaires P52B** et **720 incidences P52D** demeurent inconnues; 20 preuves P52A doivent encore être vérifiées. Aucun taux fiscal proposé comme taux adopté, aucune somme d'économies certifiée, aucune modification au site public, à SINJIRA ou à `main`. **`NO_GO_AUTOMATIQUE`**.
