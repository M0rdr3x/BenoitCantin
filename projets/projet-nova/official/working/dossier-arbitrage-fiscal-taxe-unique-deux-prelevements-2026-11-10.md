# Projet Nova — Dossier d'arbitrage fiscal : « taxe unique » et « deux prélèvements »
**Statut : candidature de travail — 10 novembre 2026 — AUCUNE DÉCISION ADOPTÉE**

**Question à trancher :** Comment harmoniser les propositions historiques de taxe unique présentes dans plusieurs documents SCQ avec l'orientation plus récente du Projet Nova qui mentionne un prélèvement sur le revenu et un mécanisme contre les paradis fiscaux, tout en garantissant la légalité, le financement des services et la protection des ménages et des travailleurs ?

Ce document est une **fiche de décision**, pas une loi, une réforme annoncée ni une validation économique. La [question P0 est suivie dans l'issue #957](https://github.com/M0rdr3x/BenoitCantin/issues/957). La divergence documentaire ne permet **pas** de déclarer les anciens textes en vigueur, les textes nouveaux adoptés ou l'une des alternatives juridiquement faisable.

## 1. Périmètre, sources et limites

- Programme politique : dernier audit interne au 5 novembre 2026 **47/100**, dont **3/16 en finances**. Maturité de rédaction séparée, non homologuée.
- Référence de gouvernance : [bilan des quatre chantiers, PR #954](https://github.com/M0rdr3x/BenoitCantin/pull/954).
- Référence budgétaire existante : [programme financier P52, PR #673](https://github.com/M0rdr3x/BenoitCantin/pull/673), qui décrit déjà **2 régimes × 3 trajectoires × 10 exercices = 60 exercices-scénarios**. **Ne pas reproduire un second modèle budgétaire concurrent.**
- Finances municipales : [PR #898](https://github.com/M0rdr3x/BenoitCantin/pull/898), [issue #906](https://github.com/M0rdr3x/BenoitCantin/issues/906). Les profils agrégés des municipalités et les comptes de l'ensemble des organismes ne sont **pas le même périmètre**.
- Revue juridique à compléter : [PR #890](https://github.com/M0rdr3x/BenoitCantin/pull/890).
- Proposition ancienne d'une « taxe unique » : les **articles précis**, leurs versions et l'auteur de leur adoption doivent encore être identifiés et vérifiés dans les documents historiques. **Aucune concordance article par article certifiée n'est versée ici.**

Le registre machine correspondant, en lecture seule, est [arbitrage-fiscal-concordance-2026-11-10.json](../../data/arbitrage-fiscal-concordance-2026-11-10.json). Les champs inconnus restent `null`; leur absence n'est pas un zéro financier.

## 2. Clarification indispensable : une taxe, deux taxes ou une taxe et un contrôle ?

Il est prématuré d'annoncer « seulement deux taxes » sans définir les termes. Les questions de classification à soumettre à des fiscalistes et juristes incluent :

1. **Impôt ou prélèvement sur le revenu** : définition de l'assiette, particuliers et personnes morales, résidence, progressivité, crédits, retenues, exemption et mécanismes de redistribution.
2. **Mesure anti-paradis fiscaux** : vise-t-elle un impôt autonome, une assiette intégrée, une cotisation, une pénalité, la déclaration de bénéficiaires effectifs, l'échange d'informations ou un recouvrement de créances existantes ? La sanction et le recouvrement ne sont **pas automatiquement** une nouvelle source de recettes permanentes.
3. **Impôts et taxes d'autres administrations** : dans le Québec actuel au sein du Canada, certaines compétences et certains prélèvements appartiennent au palier fédéral; un projet provincial ne peut pas annoncer leur abolition par sa seule volonté. Il faut examiner aussi les sources de financement municipal et les affectations spéciales.
4. **Tarifs, droits et contributions** : préciser si la proposition les abolit, les maintient, les remplace ou les requalifie. Éviter de transférer des charges aux usagers en appelant cela une diminution des taxes.
5. **Québec souverain éventuel** : décrire la transition fiscale proposée, sans supposer que les négociations sur la dette, les actifs, les pensions, la monnaie, le commerce ou les traités sont terminées.

## 3. Alternatives à analyser contradictoirement

| Option candidate | Hypothèse à tester | Principal risque | Statut |
| --- | --- | --- | --- |
| **A. Taxe unique** | Conservation de la rédaction historique après définition d'une assiette et des recettes de remplacement | Incapacité de financer l'ensemble des services / incompatibilité de compétences | Non adoptée |
| **B. Revenu + mécanisme distinct** | Un prélèvement sur le revenu et un mécanisme anti-paradis fiscaux juridiquement qualifié séparément | Rendement incertain du second outil, double comptage et effet sur les entreprises | Non adoptée |
| **C. Revenu avec anti-évitement intégré** | Un impôt sur le revenu avec règles de conformité et de récupération, sans présumer une deuxième assiette fiscale autonome | Recouvrement exagéré, assiette insuffisante ou incohérence avec les anciens textes | Non adoptée |

Ces alternatives sont **un ensemble de questions**, pas un menu approuvé. Le choix final exige avis qualifiés, consultation et décision traçable.

## 4. Matrice à remplir avant toute recommandation de taux

Les deux contextes doivent posséder des dossiers **distincts** et non interchangeables :

| Contrôle obligatoire | Québec au Canada | Québec souverain hypothétique |
| --- | --- | --- |
| Compétence pour chaque prélèvement et transfert fiscal | Avis indépendant manquant | Avis indépendant manquant |
| Recettes réellement perçues et assiettes vérifiées | Sources et rapprochement manquants | Hypothèses de transition à établir |
| Dépenses publiques, santé, logement, éducation et municipalités | Budget complet non certifié | Budget complet non certifié |
| Prestations, pensions, dette, intérêts et engagements | Examen indépendant manquant | Partage et continuité à négocier |
| Main-d'œuvre québécoise et garanties de continuité | Étude d'impact manquante | Étude d'impact manquante |
| Revenus disponibles des ménages par décile et région | Simulation non homologuée | Simulation non homologuée |
| Risques de ralentissement, inflation, recettes insuffisantes | Trois trajectoires à auditer | Trois trajectoires à auditer |
| Consentement démocratique, publication et recours | Consultation non reçue | Consultation non reçue |

### Comptabilité : conditions anti-double-comptage

- Distinguer recette brute, recette nouvelle **nette**, transfert entre administrations et économie de dépense récurrente; documenter l'administration et l'exercice.
- Rapprocher les taxes municipales potentiellement remplacées et le financement des services locaux. Aucun montant municipal ancien ne devient automatiquement une nouvelle charge provinciale.
- Séparer les exercices comptables 2024, 2025 et les budgets prévisionnels 2026–2027 et au-delà; distinguer les années de prix.
- Mesurer le financement de la transition, y compris les systèmes, la formation, les contrats, les réserves et la réversibilité; ne pas déduire des économies du simple retrait d'une ligne budgétaire.
- Classer toute recette spéculative de lutte anti-évasion comme **inconnue / non garantie**, jusqu'à preuve d'assiette, droits de perception et rendement indépendant.
- Produire une incidence **après impôt, transferts et panier essentiel**, y compris les ménages pauvres et les régions éloignées. L'objectif d'amélioration du pouvoir d'achat ne constitue pas une économie mesurée.

## 5. Protocole de décision : quatre portes successives

**D0 — Concordance documentaire.** Indexer article par article les propositions anciennes et nouvelles, leurs dates, versions et statuts. Livrable : matrice contrôlable, lignes discordantes signalées. Relecteur : responsable documentaire indépendant. **État : ouvert.**

**D1 — Légalité et classification.** Obtenir des avis distincts pour les deux régimes et chaque option; expliciter les compétences, droits et recours. Livrable : analyse juridique avec limites et objections. Relecteurs : fiscaliste et juriste sans mandat auto-certificatif. **État : ouvert.**

**D2 — Financement et incidence.** Reprendre le modèle P52 existant; établir 60 exercices-scénarios, vérifier les données fiscales et municipales 2024–2025, les assiettes, les investissements, la dette, l'impact ménage et les risques défavorables. Relecteurs : économiste/actuaire/comptable indépendants, selon le poste. **État : ouvert.**

**D3 — Consultation, arbitrage et harmonisation.** Soumettre des alternatives équitables, enregistrer les objections, documenter un organe compétent, une décision datée et une version. **Seulement ensuite**, proposer la concordance de textes constitutionnels, législatifs ou de vulgarisation. **État : ouvert.**

**Responsabilités non encore mandatées.** Le registre ne désigne aucun expert réel et n'invente ni signature ni échéance. Les quatre portes sont des **conditions de traitement du conflit**, non des points de complétude supplémentaires.

## 6. Résultat vérifiable de cette étape

Le contrôleur `scripts/audit-arbitrage-fiscal-2026-11-10.mjs` vérifie que trois alternatives et deux régimes sont présents, que les 60 exercices restent **à auditer**, que les examens indépendants et décisions n'ont pas été inventés, et que **l'incrément de score reste nul**. Les tests Node essayent volontairement de falsifier ces champs.

Cela fournit un **cadre professionnel de décision** mais ne démontre pas encore l'équilibre des finances. L'état de référence reste **Projet Nova 47/100, finances 3/16**. **Fin 2027** n'est qu'une cible de préparation du programme; **aucune date de fin ou d'adoption certifiée** n'existe.
