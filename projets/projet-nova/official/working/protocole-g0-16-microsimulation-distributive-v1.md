# NOVA-FIN-G0.16 — Protocole de microsimulation distributive et de soutenabilité

**Projet :** Projet Nova — principes Sinjira de dignité, transparence, liberté, responsabilité et solidarité.  
**Date :** 6 novembre 2026. **Statut :** recherche technique non adoptée et non calibrée.  
**Score de programme : 47/100**, maintenu selon l'audit G0.12; **aucune donnée nouvelle ne justifie une hausse**. Le résultat G0.16 est un **plan vérifiable**, pas une simulation de la réforme.

## 1. Question décisionnelle

Une réforme fiscale Nova augmente-t-elle **réellement** le niveau de vie, sans diminuer l'accès aux services, les protections des travailleurs ni la soutenabilité financière de l'État? Comparer **deux statuts juridiques distincts** : `QUEBEC_CANADA` et `QUEBEC_SOUVERAIN`.

Ne jamais confondre baisse d'un impôt, baisse du coût total des ménages, variation du solde budgétaire et gain de bien-être. Ne pas supposer qu'une entreprise ne répercute aucune charge ou qu'une recette anti-évasion est automatiquement disponible.

## 2. Éléments mesurables

**Unité principale :** ménage, année homogène, décile de revenu disponible **équivalisé** (échelle d'équivalence et conventions à valider). Une base anonymisée et autorisée doit permettre une stratification par composition familiale, âge, région, logement, et situations de vulnérabilité. Les travailleurs autonomes sont identifiés sans les confondre avec les sociétés; l'**analyse des PME utilise une unité statistique distincte**.

Pour chacun des déciles 1–10 et des deux scénarios, documenter :
- revenu disponible de référence après impôts, cotisations et transferts;
- dépenses essentielles de référence (logement, alimentation, énergie, transport), avec méthode évitant un double comptage des taxes déjà incluses dans les prix;
- revenu disponible sous la mesure Nova, dépenses essentielles après éventuelles répercussions sur les prix, montant réellement restant;
- différence **en dollars constants**, distribution des pertes/gains, taille de l'échantillon, incertitude statistique et limites;
- effets sur droits acquis, coûts privés éventuels de services, temps d'accès, remboursements et prestations — sans convertir arbitrairement la qualité d'un service en dollars.

Le calcul unitaire est `reste_apres_essentiels = revenu_brut - impots - cotisations + prestations - depenses_essentielles`. Il ne constitue **pas** un modèle complet : il exige une base individuelle/agrégée adéquate, une unité de comparaison cohérente et un modèle de répercussion sur les prix. Les dépenses essentielles doivent intégrer de manière cohérente les taxes indirectes déjà payées et éviter tout double compte.

## 3. Deux scénarios et limites

### A. Québec dans le Canada

Analyser seulement les leviers de compétence provinciale et distinguer impôts fédéraux, transferts, municipalités, RRQ, RQAP, santé et médicaments. Le système à deux prélèvements demeure une hypothèse à auditer. Le maintien des autres prélèvements relève de leur régime juridique.

### B. Québec souverain

Reprendre les dépenses fédérales nécessaires, les prestations, le service de la dette, les actifs, la monnaie, les pensions, les recettes extérieures et les compétences transférées. **Les 33 046 M$ de transferts fédéraux prévus pour 2026–2027 ne sont pas automatiquement disponibles après souveraineté.** Ne jamais sommer les recettes fédérales théoriques sans intégrer les obligations correspondantes.

Les deux budgets devront être indépendamment équilibrés et soumis à des scénarios défavorables avant toute décision.

## 4. Préconditions et registres

Le plan `data/plan-microsimulation-g0-16.json` contient **20 cases de déciles prévus** (10 par statut), **aucun résultat chiffré**, et renvoie aux **15 preuves V01–V15** de G0.15, toutes encore à documenter. Le programme demeure évalué à **47/100**.

| Porte | Exigence | État |
| --- | --- | --- |
| P1 — Assiettes | Définition légale, rapprochement fiscal, calcul revenu personnes/sociétés | Non établi |
| P2 — Continuité | RRQ, RQAP, soins, médicaments, municipalités et écoles financés | Non établi |
| P3 — Données et vie privée | Sources autorisées, documentation, contrôles anti-réidentification | Non établi |
| P4 — Modèle | Période, unités, prix, inflation, taxes indirectes, échantillonnage, pondération | Non établi |
| P5 — Incidence | Déciles, ménages vulnérables, régions, PME, travail et services | Non établi |
| P6 — Double scénario | Compatibilité légale et budgets complets sur dix ans | Non établi |
| P7 — Vérification | Validation contradictoire et indépendante, publication des limites | Non établi |

**Données absentes = `null`, jamais zéro.** Aucun pourcentage de gagnants, taux Nova, effet budgétaire ou nouvelle économie n'est calculable aujourd'hui.

## 5. Calcul pédagogique strictement isolé

Le module `assets/g16-incidence-core.mjs` valide le plan et offre un calculateur **exclusivement synthétique**, exigeant explicitement le marqueur `SYNTHETIC_EXERCISE`. Le calcul illustre pourquoi une baisse d'impôt de 5 unités peut être compensée par une hausse de 5 unités de dépenses essentielles : le solde réellement disponible ne change pas. **Cet exercice n'utilise aucun contribuable réel et ne doit jamais être repris comme résultat Nova.**

La suite `tests/g16-incidence.test.mjs` rejette les valeurs inventées, déciles manquants, transferts souverains présumés, approbations non établies, calculs incomplets et conversions de données synthétiques en preuve.

## 6. Plan de collecte et validation

**G0.16a — cadrage terminé à l'état de protocole :** définitions, deux scénarios, dimensions, liste de variables et verrou de non-certification.

**G0.16b — à engager :** acquérir légalement des tableaux anonymisés ou des microdonnées autorisées; documenter définitions, millésimes, unités, base juridique et concordance avec les comptes publics. Les demandes G0.15 ne sont pas déclarées transmises.

**G0.16c — à conditionner aux preuves :** estimer effets statiques et comportements plausibles, intervalles d'incertitude, sensibilité aux hypothèses, hétérogénéité régionale, risques pour groupes vulnérables et budgets sur dix ans. Effectuer un audit indépendant des modèles, données et interprétations.

La **porte G0.16 n'est pas franchie**. Un document supplémentaire n'ajoute aucun point au 47/100 sans preuves et revue selon la grille G0.12.

## 7. Traçabilité

- Préparation G0.15 : `official/working/protocole-g0-15-ventilation-fiscale-et-incidence-v1.md`.
- Sources financières : `data/registre-assiettes-fiscales-g0-14-2026-2027.json` et `data/cadre-financier-g0-13-2026-2036.json`.
- Grille de complétude : `data/audit-completude-programme-nova-2026-11-05.json`.
- Source primaire : Rapport préélectoral, ministère des Finances, août 2026, https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf

**Les textes candidats** `official/reference/*` et le manifeste `data/sources.json` **ne sont pas modifiés**. Une adoption future impose compétence, consultation, délibération et preuve de financement.
