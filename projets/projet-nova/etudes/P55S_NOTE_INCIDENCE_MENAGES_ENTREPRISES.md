# P55S — Cadre d'incidence du pouvoir d'achat et des entreprises : fin des comparaisons trompeuses

**6 novembre 2026 — étape N02 de la complétude, outil méthodologique non adopté et non certifié.**

## Problème concret

Le Projet Nova envisage une simplification radicale autour de deux prélèvements, dont l'impôt sur les revenus et un mécanisme à définir contre l'utilisation des paradis fiscaux. Une telle réforme ne peut pas être jugée exclusivement selon les impôts provinciaux annulés. **Le pouvoir d'achat dépend aussi des cotisations obligatoires, des transferts fédéraux et provinciaux, des prix et de la continuité des services publics.** Une entreprise doit aussi acquitter des coûts réels et peut transmettre certaines modifications de charges aux prix, salaires ou investissements.

Les statistiques fiscales historiques P55Q–P55R, et les montants exposés dans P55P, **ne disent pas quel ménage gagnerait réellement**. Il faut d'abord une méthode d'incidence, puis des données.

## Sources méthodologiques officielles et limites

- [Gouvernement du Québec — Estimer le revenu disponible](https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible) : notion de revenu disponible après impôts, cotisations et prestations québécoises et fédérales. Le ministère indique que ses résultats couvrent des situations courantes seulement, et excluent certaines catégories de revenus et crédits.
- [Institut de la statistique du Québec — Revenu disponible](https://statistique.quebec.ca/fr/document/revenu-disponible) : définition macroéconomique du revenu disponible.
- [ISQ — Évolution du revenu disponible par habitant en 2024](https://statistique.quebec.ca/fr/produit/publication/revenu-disponible-par-habitant-2024-quebec-et-regions) : les services publics **en nature** (soins et éducation) ne figurent pas dans ce revenu disponible; les différences de coût de la vie entre territoires ne sont pas mesurées par ce seul indicateur. **L'impôt sur la consommation supporté** ne doit pas être arbitrairement soustrait du revenu disponible pour prétendre reproduire cet indicateur officiel.
- [CFFP — Simulateur fiscal du Québec](https://cffp.recherche.usherbrooke.ca/outils-ressources/simulateur-fiscal-quebec/) : référence analytique extérieure de simulation des recettes fiscales et des effets sur divers ménages; ses résultats ne sont **pas automatiquement intégrés** au Projet Nova et les hypothèses doivent être revues.

**Attention aux niveaux de preuve :** ces pages publiques définissent des concepts et des méthodes. **Elles ne fournissent aucun montant de ménage du gabarit P52D** ni aucune autorisation légale de la proposition de deux prélèvements.

## Périmètre du modèle de couverture : données existantes dans la PR

Le gabarit `P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json` distingue :

| Dimension | Nombre |
|---|---:|
| Régimes constitutionnels | **2** — Québec dans le Canada; Québec souverain hypothétique |
| Trajectoires de chacun | **3** — centrale, prudente, stress |
| Catégories de ménages par trajectoire | **5** — personne modeste seule, famille avec enfants, famille monoparentale, personne retraitée, personne seule à revenu moyen |
| Catégories d'entreprises par trajectoire | **2** — PME et grande entreprise |
| Variables monétaires par situation de ménage | **8** |
| Variables monétaires par situation d'entreprise | **10** |
| Situations à comparer | **2** — système actuel, système proposé |
| **Valeurs ménages encore inconnues** | **480** |
| **Valeurs entreprises encore inconnues** | **240** |
| **Total des montants encore inconnus** | **720** |

**Recalcul indépendant de comptage :** 2 régimes × 3 trajectoires × 5 ménages × 2 situations × 8 champs = **480**, et 2 × 3 × 2 types d'entreprises × 2 situations × 10 champs = **240**. La CI exige que les `null` demeurent `null` tant qu'un dossier probant n'est pas approuvé. Aucun montant n'est remplacé par zéro, aucune situation fiscale n'est tenue pour « validée » par défaut. Les **600 montants P52B** de financement décennal restent également inconnus.

## Ce que calcule le prototype — et ce qu'il ne calcule pas

Le validateur `scripts/mesurer_couverture_incidences_nova_p55s.py` fournit deux fonctions sur **des entrées déclarées fictives, intégralement renseignées, non personnelles et non représentatives**. Il n'applique aucun barème fiscal ou crédit réel.

**Ménages — solde direct partiel illustratif :**

```text
revenu brut + prestations fédérales + prestations Québec/État
  − impôt fédéral sur le revenu − impôt provincial/État sur le revenu
  − cotisations obligatoires − prélèvements municipaux directs
= SOLDE DIRECT PARTIEL ILLUSTRATIF
```

Le modèle affiche séparément un **solde après les taxes à la consommation supportées**, uniquement pour visualiser une différence mécanique. **Ces résultats ne reproduisent pas le revenu disponible officiel** : le gabarit ne contient pas tous les loyers, frais de garde, intérêts, dépenses essentielles, ressources mixtes ou variations de prix. L'écart ne constitue **pas** une hausse garantie de pouvoir d'achat. Les services de santé et d'éducation rendus sans facturation directe doivent aussi être analysés **en nature**, hors du solde monétaire.

**Entreprises — flux simplifié fictif :**

```text
chiffre d'affaires − coûts d'exploitation hors salaires − salaires
  − impôt fédéral sur le revenu − impôt québécois/État
  − cotisations employeur − prélèvements municipaux
  − taxes à la consommation non récupérables + subventions reçues
  − charge additionnelle anti-évasion hypothétique
= FLUX SIMPLIFIÉ ILLUSTRATIF
```

Ce flux **n'est ni le bénéfice fiscal, ni le résultat selon les normes comptables, ni la trésorerie auditée**. Les effets de comportement, l'amortissement, les pertes, les taux de transfert aux prix, la rémunération du capital, l'accès aux services et les investissements demeurent inconnus.

Le validateur refuse les entrées monétaires absentes, les valeurs négatives, les nombres flottants arrondis arbitrairement, les champs supplémentaires et la tentative de calculer un « taux Nova » à partir d'exemples synthétiques. Les montants des exemples dans les tests ne sont **pas** des cas réels, des projections ou des recommandations de barème.

## Douze portes probantes à compléter (S01–S12)

1. **S01** : calculer le revenu disponible actuel selon la situation familiale, avec sources et limites.
2. **S02** : protéger le revenu net des ménages modestes, par décile et région, avec seuil de subsistance documenté.
3. **S03** : préserver le traitement exact des familles avec enfants et des familles monoparentales, prestations et crédits.
4. **S04** : vérifier le revenu des personnes retraitées, les pensions et le financement des services.
5. **S05** : analyser la répercussion sur les prix, y compris taxes à la consommation et cotisations.
6. **S06** : distinguer les PME et grandes entreprises, emplois, salaires, coûts et subventions.
7. **S07** : ne pas supprimer par décret provincial les obligations fédérales dans le Canada.
8. **S08** : maintenir les ressources et services municipaux, sans double compte.
9. **S09** : obtenir des données représentatives et des poids par ménage, région et niveau de revenus.
10. **S10** : prévoir les services en nature, leur qualité et la continuité.
11. **S11** : relier les simulations aux recettes et dépenses sur dix ans, sans rendement inventé contre les paradis fiscaux.
12. **S12** : soumettre le modèle à des contre-expertises juridiques, fiscales, comptables et économiques authentifiées.

**Critères de rejet prioritaires :** un seul ménage fictif gagnant ne prouve pas que tous les citoyens gagnent; le décalage d'une taxe vers des prix, loyers ou cotisations peut réduire un gain apparent; un bilan public ne peut pas considérer les 720 valeurs `null` comme connues; un modèle juridiquement non autorisé ne peut pas devenir une réforme adoptée.

## Usage et statut

```bash
python scripts/mesurer_couverture_incidences_nova_p55s.py \
  --bilan-public /hors_git/p55s_bilan_public.json
```

La sortie est un **bilan des valeurs manquantes**, pas une simulation réelle des ménages. `--exiger-incidence-validee` doit refuser l'attestation avec le code **3**. Aucun taux, revenu disponible nouveau, économie budgétaire ou gain sur le pouvoir d'achat ne résulte de P55S seul.

**Maturité globale estimée : 53 % (inchangée).** Le prototype accroît la qualité et la transparence de la méthode, pas encore la preuve d'exécution. Les deux scénarios constitutionnels demeurent distincts; services, emplois, PME et pouvoir d'achat protégés. Aucun contact, dépense, mandat, modification SINJIRA ni fusion `main`.

**Décision : `NO_GO_AUTOMATIQUE`.**
