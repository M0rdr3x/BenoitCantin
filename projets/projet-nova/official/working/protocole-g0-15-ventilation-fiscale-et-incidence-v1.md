# NOVA-FIN-G0.15 — Vérifier les deux prélèvements avant de fixer un taux

**Projet :** Nova–Sinjira | **Date :** 5 novembre 2026  
**Statut :** recherche candidate, non adoptée. **Préparation : 47/100, inchangée**. Aucune taxe abolie, aucun taux ni rendement nouveau établi.

## Point de départ contrôlé

G0.14 reprend les prévisions du gouvernement québécois pour 2026–2027 : **135 343 M$** de revenus autonomes, **33 046 M$** de transferts fédéraux, soit **168 389 M$** au total. Ce n'est pas un budget Nova. Les **65 640 M$** tirés des catégories actuelles d'impôts des particuliers et des sociétés ne sont **pas** le montant des revenus imposables.

La politique envisagée comprend l'imposition des revenus des personnes et entreprises, ainsi qu'une mesure contre les paradis fiscaux. Avant d'affirmer qu'il s'agit de « deux taxes », il faut décider si la seconde est réellement un impôt juridiquement autonome ou seulement un mécanisme de contrôle d'une dette fiscale déjà due. Son rendement net additionnel reste **inconnu**.

## Travaux requis et pièces à produire

| Code | Volet | Pièce de preuve obligatoire |
| --- | --- | --- |
| V01–V04 | Ventilation | Ventiler taxes à la consommation, droits/permis/redevances, revenus divers et impôts des sociétés, par compte, loi et exercice |
| V05–V06 | Assiettes | Définir le revenu imposable de chaque personne et le bénéfice imposable de chaque entreprise; pertes, crédits, dividendes, pensions, exclusions et doubles comptes |
| V07–V10 | Protection sociale | Rapports de financement RRQ, RQAP, santé/médicaments, écoles et municipalités, droits acquis et remplacement financé |
| V11 | Paradis fiscaux | Compétence, assiette autonome éventuelle, recouvrements déjà inclus, coûts d'enquête et rendement **net** |
| V12–V13 | Incidence | Microsimulations par décile, famille, âge, région, statut de logement, PME, travailleurs, emplois et prix |
| V14 | Statut du Québec | Compétences distinctes Québec au Canada / Québec souverain, fonctions et transferts fédéraux à reprendre |
| V15 | Budget | Scénarios de dix ans, continuité des services, réserves, dette, transition, stress-tests, audit externe |

Chaque pièce doit préciser **la source primaire, la date, le périmètre, les unités, la légalité, le contrôleur et les lacunes**. Les données inconnues demeurent `null`, jamais zéro.

## Classification juridique préalable

Aucune famille de recettes ne peut être simplement renommée « taxe » ou « recette libre ». Séparer : impôts généraux, cotisations affectées, redevances de ressources, droits réglementaires et tarifs, revenus des entreprises publiques, transferts et postes mixtes. Les catégories **6 484 M$** de droits/permis/redevances et **15 790 M$** de revenus divers nécessitent une ventilation documentée.

Le **FSS** dépend notamment de rémunérations et de la masse salariale. Les cotisations du **RRQ** financent un régime public contributif avec droits à prestations. Le **RQAP** est soutenu par un fonds fiduciaire alimenté par salariés, autonomes et employeurs. Les recettes de ces dispositifs ne peuvent être déclarées librement réaffectables. Les recettes municipales et impôts fédéraux sont séparés.

## Test de pouvoir d'achat Nova–Sinjira

Pour chaque groupe de ménages, comparer **en dollars constants** les impôts et cotisations actuels, les prélèvements simulés, les crédits et transferts, les coûts du logement, de l'énergie et du transport, les frais privés et les services réellement conservés. Afficher les **gagnants et les perdants**, pas seulement la moyenne. Préserver l'emploi, les recours, la dignité et la vie privée; une économie comptable qui transfère une facture au citoyen n'est pas un gain social.

Pour le scénario souverain, ne pas reconduire automatiquement les **33 046 M$** de transferts fédéraux et ne pas compter des impôts fédéraux additionnels sans reprendre aussi les obligations correspondantes.

## Porte de validation

**G0.15 reste NON FRANCHIE** tant que V01–V15 ne sont pas documentées et revues indépendamment. Aucun nouveau taux, aucun budget Nova certifié, aucune loi ni réforme fiscale autorisée. Le prochain instrument possible est une **microsimulation G0.16**, après validation des assiettes et du statut juridique des flux. La matrice JSON dédiée porte toutes les preuves comme non acquises.

## Sources

- Budget 2026–2027, rapport préélectoral : https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf
- FSS : https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/calcul-des-retenues-et-des-cotisations/cotisation-de-lemployeur-fss/cotisation-au-fss-ce-que-vous-devez-savoir/
- RRQ : https://www.retraitequebec.gouv.qc.ca/fr/programmes/regime-rentes-quebec
- RQAP : https://www.quebec.ca/gouvernement/ministeres-organismes/conseil-gestion-assurance-parentale/mission-mandats/fonds-dassurance-parentale
- Évasion : https://www.revenuquebec.ca/fr/une-mission-des-actions/assurer-la-conformite-fiscale/evasion-fiscale/quest-ce-que-levasion-fiscale/

**Protection documentaire :** `official/reference/*` et `data/sources.json` inchangés.
