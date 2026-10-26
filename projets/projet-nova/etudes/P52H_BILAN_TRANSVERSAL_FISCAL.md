# Projet Nova — P52H : bilan transversal de préparation de la réforme fiscale

**19 octobre 2026 · Analyse technique candidate · Non adoptée · Aucune publication ou collecte · NO_GO**

## 1. Décision à éclairer

Le Projet Nova étudie une fiscalité à deux prélèvements principaux : un impôt sur les revenus et une mesure contre le transfert abusif de bénéfices. Pour permettre un choix éclairé, il faut démontrer **simultanément** la faisabilité budgétaire et juridique, les effets distributifs, la protection des services et le traitement des responsabilités publiques. Le succès d'un seul calcul, ou d'une seule suite de tests, n'établit pas ces conditions.

**P52H réunit les travaux P52A à P52G dans un seul contrôle en lecture locale**. Ce programme recalcule les quatre objets comptables à partir de leurs fichiers sources :
- **P52A** — vingt justificatifs légaux, budgétaires et sociaux à obtenir;
- **P52B** — deux régimes, trois trajectoires et dix années, soit soixante exercices-scénarios;
- **P52C** — concordance arithmétique des 21 postes de recettes 2026-2027, sans assimilation à un budget souverain ni à une estimation de rendement d'un nouvel impôt;
- **P52D/E/F** — quarante-deux situations de ménages et d'entreprises non représentatives, détection des pertes et des facteurs non fiscaux;
- **P52G** — confidentialité : le rapport final utilise une liste blanche d'agrégats, jamais les données, montants, catégories ou sources de cas individuels.

La méthode confronte les sorties directement calculées plutôt que de croire un fichier de résultat déjà écrit. Elle refuse un désaccord de périmètre, un budget modifié ou une conclusion de représentativité que les travaux antérieurs ne permettent pas.

## 2. État documenté au départ

| Porte d'examen | Ce que nous savons | Ce qui n'est pas démontré |
| --- | --- | --- |
| Compétence fédérale/provinciale | Deux statuts constitutionnels séparés dans le gabarit | Accord ou compétence nouvelle; aucune souveraineté acquise |
| Recettes publiques | 21 postes et des soldes rapprochés arithmétiquement à la prévision 2026-2027 | Certification indépendante et recettes futures de l'impôt envisagé |
| Viabilité décennale | 60 exercices-scénarios structurés | **600 montants** encore inconnus dans la grille P52B |
| Incidence sur les personnes | 30 cas de ménages non représentatifs | Données permettant les calculs et leur projection à la population |
| Incidence sur l'activité économique | 12 cas d'entreprises non représentatifs | Charges, répercussion sur prix et salaires, financement des services |
| Ensemble des cas P52D | 42 cas; règles de calcul et contrôles existants | **720 montants** encore inconnus |
| Avis de fond P52A | 20 exigences inventoriées | **20 pièces indépendantes** non attestées |
| Non-appauvrissement | Aucun cas calculable au départ | **Aucun constat possible de zéro perte**, encore moins pour le Québec entier |
| Autorisation | Documentation interne candidate | Aucune adoption, loi, fusion ou publication permise |

### L'interprétation de « zéro perte constatée » est essentielle

P52E retourne actuellement zéro cas identifié avec perte parce qu'**aucun cas du gabarit n'est calculable**. Ce zéro est un **compteur d'observations**, et **non** une preuve que la réforme ne peut appauvrir personne. P52H formule explicitement : `AUCUN_CAS_EVALUABLE_PAS_ZERO_PERTE_DEMONTREE`.

Même lorsque des cas seraient renseignés à l'avenir, leurs résultats resteraient limités à des **hypothèses non représentatives**, sans pondération démographique ni causalité. Des hausses du prix du logement, des changements de services ou des effets indirects sur les salaires ne peuvent pas être inférés de ces cas.

## 3. Hiérarchie des décisions

La décision finale ne peut jamais sortir automatiquement d'un programme. Les portes encore nécessaires sont :

1. **Droit et compétences.** Préciser les assiettes réelles; séparer compétences québécoises, fédérales, municipales et obligations d'un éventuel nouvel État.
2. **Budget et dette.** Authentifier les tableaux, obtenir données de référence à jour, vérifier l'équilibre budgétaire antérieur et le ratio dette nette / PIB, puis construire des prévisions auditées année par année.
3. **Incidence distributive.** Données adaptées à la population québécoise, impact par niveau de revenu, régions, situations familiales, retraités, PME et grandes entreprises, avec protection des données.
4. **Services, emploi et municipalités.** Évaluer les répercussions, sans compter comme économie un coût simplement transféré aux citoyens.
5. **Expertise contradictoire et adoption.** Avis indépendants, objections documentées, revue démocratique, puis décision juridique compétente. Une CI verte ne tient pas lieu d'avis.

Une preuve juridiquement ou financièrement absente n'est **jamais fabriquée à partir d'une valeur fictive**. Les vingt pièces P52A ne sont pas réputées obtenues par leur seule déclaration dans un JSON.

## 4. Confidentialité et limites des calculs

Le script `scripts/auditer_preparation_fiscale_nova_p52h.py` appelle les calculateurs existants P52B, P52C, P52D et P52E et les confronte. Le rapport JSON ne retient que :
- des **comptes globaux** de données et preuves manquantes;
- le nombre de cas, années et trajectoires;
- un libellé prudent sur les pertes non observables ou observées seulement dans les cas fictifs;
- des **codes de blocage non nominatifs**;
- les indicateurs `NO_GO_AUTOMATIQUE`, `publication_autorisee:false` et `fusion_autorisee:false`.

Il exclut les montants ou revenus par ménage et entreprise, leurs noms ou catégories, différences financières par cas, justificatifs, URLs de provenance particulières et objets de microdonnées. **Un rapport agrégé n'est pas une certification juridique d'anonymisation**; aucune donnée fiscale privée ne doit être déposée dans GitHub.

L'audit contrôle les documents locaux et **ne réalise aucun appel réseau ni modification de configuration de GitHub**. Il n'atteste pas une expertise juridique, une certification du budget, l'authenticité de tous les documents externes ou la représentativité d'un échantillon.

## 5. Comment exécuter P52H

Depuis la racine du dépôt :

```bash
python scripts/auditer_preparation_fiscale_nova_p52h.py \
  --rapport p52h_resume_local.json
```

Le contrôle strict, qui **doit renvoyer le code 3**, n'est pas un mécanisme de promulgation :

```bash
python scripts/auditer_preparation_fiscale_nova_p52h.py \
  --exiger-preparation --rapport p52h_refus_local.json
```

Les sorties sont `0` = rapport technique créé (même si les blocages persistent), `2` = entrée invalide ou illisible, `3` = le contrôle strict refuse la préparation. Les deux modes conservent la décision `NO_GO_AUTOMATIQUE`.

Le workflow `.github/workflows/validate-nova-p52h.yml` exécute les tests unitaires du module, compare les compteurs attendus, confirme le refus strict, conserve brièvement **un rapport uniquement agrégé**, avec `contents:read` et sans déploiement.

## 6. Résultat et étape suivante

P52H produit une **liste des preuves manquantes à combler**, pas un taux d'imposition, une suppression de taxe ou un niveau de vie garanti. L'ordre rationnel des travaux suivants est : faire vérifier indépendamment le rapprochement budgétaire, inventorier précisément les prélèvements et transferts réellement modifiables, obtenir les assiettes fiscales détaillées puis concevoir des scénarios représentatifs et protecteurs.

La PR673 demeure une **proposition en brouillon**; les documents `official/reference` ne sont pas amendés. Les revues humaines [issue #662](https://github.com/M0rdr3x/BenoitCantin/issues/662) et la protection de `main` [issue #135](https://github.com/M0rdr3x/BenoitCantin/issues/135) restent bloquantes. **PR640 : NE PAS FUSIONNER.**

**Décision : PAS DE GO FINANCIER OU CONSTITUTIONNEL. ÉTUDE À AUDITER.**
