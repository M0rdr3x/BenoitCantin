# Projet Nova — P52D : évaluer les conséquences fiscales pour les ménages et les entreprises

**18 octobre 2026 · Étude candidate, non adoptée · Aucun taux, aucun avantage promis · NO_GO**

## 1. Pourquoi ce module existe

Le rapprochement P52C établit les catégories de recettes prévues par le Québec pour l'exercice 2026-2027; il **ne démontre pas** quelles personnes gagneraient du revenu ou seraient pénalisées par une transformation vers deux prélèvements. La somme des impôts des particuliers et sociétés **65,327 G$** ne renseigne ni les crédits, ni les prestations, ni la charge effective d'un ménage ou d'une PME.

P52D crée une grille de comparaisons **individualisées par catégorie de situation**, mais **sans microdonnées réelles, sans hypothèse de population et sans revenu représentatif inventé**. Les résultats de ce gabarit ne peuvent pas être extrapolés aux ménages québécois, ni servir à annoncer des économies sur l'ensemble du territoire.

## 2. Sources de méthode — ne pas transformer une moyenne canadienne en ménage québécois

- [Ministère des Finances du Québec — estimer le revenu disponible](https://www.finances.gouv.qc.ca/ministere/outils_services/outils_calcul/revenu_disponible/) : pour le revenu disponible, il faut tenir compte des impôts, cotisations obligatoires et aides gouvernementales **fédérales et québécoises**; l'outil public ne tient lui-même pas compte de toutes les situations, déductions et catégories de revenus.
- [Revenu Québec — taux marginaux 2026](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/taux-dimposition/) : les taux marginaux 14 %, 19 %, 24 % et 25,75 % s'appliquent aux **tranches** de revenu imposable; **aucun de ces taux ne peut être multiplié par le revenu brut pour déterminer l'impôt net réel**.
- [Statistique Canada — tableau 36-10-0587-01, revenus et consommation par quintile](https://www150.statcan.gc.ca/n1/en/catalogue/3610058701) : le tableau national ne permet pas, tel quel, d'affecter un revenu représentatif à chacun des ménages du Québec. Sa méthode et sa couverture géographique doivent être vérifiées avant toute application provinciale.
- [Statistique Canada — revue 2025/2024 par quintile](https://www150.statcan.gc.ca/n1/daily-quotidien/260413/t002a-fra.htm) : valeurs canadiennes, **non transposées ici au Québec**.

Ces références sont une **méthode de recherche**, et ne contiennent pas les données individuelles de P52D.

## 3. Périmètre analytique : 42 cas, 720 entrées inconnues

La grille comporte **deux régimes constitutionnels × trois trajectoires** centrale/prudente/stress, avec dans chaque combinaison :

**Cinq situations de ménages non représentatives** :
1. personne seule à revenu modeste;
2. famille avec enfants;
3. famille monoparentale;
4. personne retraitée;
5. personne seule à revenu moyen.

**Deux types d'entreprises non représentatives** :
1. PME;
2. grande entreprise.

Cela donne **30 cas de ménages et 12 cas d'entreprises**, chacun comparant `actuel` et `propose`. Il y a **huit postes par phase ménage**, **dix postes par phase entreprise**, donc **720 montants** encore à renseigner dans le gabarit initial. Les intitulés n'établissent aucune valeur de salaire, coût ou impôt.

Les montants sont en **dollars canadiens annuels par cas**, au format de chaîne décimale jusqu'à deux décimales, jamais en nombre flottant JSON. `null` signifie « inconnu », et **n'est jamais un zéro**. Une valeur connue doit être accompagnée d'une source `document_public` ou d'une **hypothèse explicitement non certifiée** pour une simple illustration. Aucun identifiant de contribuable ou dossier fiscal réel n'est demandé.

## 4. Ménages : trois calculs à ne pas confondre

Chacune des phases exige les composantes suivantes : revenu brut, prestations fédérales, prestations québécoises ou de l'État envisagé, impôt fédéral, impôt provincial ou de l'État, cotisations obligatoires, prélèvements municipaux directs et taxes de consommation effectivement supportées.

Calcul conditionnel :

```text
Solde après prélèvements directs
  = revenu brut + prestations fédérales + prestations Québec/État
  - impôt sur le revenu fédéral - impôt Québec/État
  - cotisations obligatoires - prélèvements municipaux directs

Solde après taxes de consommation supportées
  = solde après prélèvements directs - taxes consommation supportées

Variation par cas
  = solde proposé après taxes conso - solde actuel après taxes conso
```

**Précision essentielle :** le *solde après prélèvements directs* n'est **pas** annoncé comme l'indicateur statistique officiel de revenu disponible; les charges municipales sont traitées ici comme charges monétaires dans un modèle simplifié. Le *solde après taxes de consommation* **n'est pas une mesure officielle du pouvoir d'achat** : il manque encore les autres dépenses de consommation, les comportements, l'inflation, la répercussion des prix, le logement et les variations de prestations.

La variation calculée **n'est pas une preuve causale** que la réforme explique tout le changement. Une économie fiscale peut être compensée par un coût de consommation plus élevé, une prestation perdue ou un transfert de charge municipale.

## 5. Entreprises : charges directes et résultat partiel

Chaque phase d'entreprise comporte : chiffre d'affaires, coûts d'exploitation hors salaires, masse salariale, impôt fédéral, impôt Québec/État, cotisations employeur, prélèvements municipaux, taxes de consommation non récupérables, subventions reçues et charge additionnelle anti-évasion **seulement si réellement applicable et documentée**.

```text
Solde opérationnel partiel
  = chiffre d'affaires
    - coûts hors salaires - salaires
    - impôt fédéral - impôt Québec/État
    - cotisations employeur - prélèvements municipaux
    - taxes consommation non récupérables
    - charge anti-évasion applicable + subventions reçues
```

Ce **solde partiel** ne doit pas être présenté comme un bénéfice comptable normé, un revenu imposable, un flux de trésorerie exact ni un résultat économique total. Les cotisations sociales sont distinguées de l'impôt sur le revenu et les subventions sont des transferts à documenter, pas des recettes fiscales. **La charge contre l'évasion n'est pas une taxe supposée pour chaque entreprise**; elle reste inconnue dans le gabarit.

Une simulation doit examiner séparément les ménages et les entreprises, car les coûts des entreprises peuvent être répercutés aux consommateurs ou salariés; les deux effets ne doivent pas être additionnés comme s'ils étaient indépendants.

## 6. Deux régimes constitutionnels : garde-fous

**Québec dans le Canada :** un changement de fiscalité **purement provincial** ne peut pas réduire de lui-même l'impôt fédéral des particuliers ou sociétés ni les prestations fédérales. Si les deux phases contiennent ces composantes, elles doivent être identiques, faute de quoi P52D rejette le cas. Les variations fédérales indépendantes nécessiteraient un modèle distinct et des sources spécifiques.

**Québec souverain hypothétique :** le modèle ne remplace aucune entrée fédérale par zéro automatiquement. Toute reprise de prestation, toute abolition/remplacement de contribution ou tout changement de compétence doit être renseigné avec une preuve juridique et comptable. **La souveraineté n'est ni reconnue ni réalisée par ce gabarit.**

Pour les deux régimes : protection du pouvoir d'achat, main-d'œuvre locale, services publics et municipalités, aides aux entreprises temporaires, discipline budgétaire et absence de contre-tarifs de représailles dans les pouvoirs disponibles restent des **objectifs à auditer**, pas des résultats déjà prouvés.

## 7. Utilisation et codes de sortie

Depuis la racine du dépôt :

```bash
python scripts/comparer_incidence_fiscale_nova_p52d.py \
  --gabarit projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json \
  --rapport p52d_rapport_local.json
```

Contrôle strict sur le même fichier, qui **doit renvoyer le code 3**, car les 720 montants sont inconnus :

```bash
python scripts/comparer_incidence_fiscale_nova_p52d.py \
  --gabarit projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json \
  --exiger-completude --rapport p52d_rapport_strict_local.json
```

Codes : `0` = rapport techniquement généré; `2` = fichier invalide ou absent; `3` = entrées encore inconnues en mode strict. **Aucun de ces codes ne permet une fusion, une réforme, un taux adopté ou une publication.**

Les tests peuvent employer des chiffres entièrement **fictifs**, uniquement pour confirmer l'arithmétique, sans les introduire dans le gabarit officiel. Même si tous les montants d'un cas fictif sont renseignés, le résultat est étiqueté `ILLUSTRATION_NON_CERTIFIEE` avec `attribution_causale_demontree:false`.

## 8. Décisions et preuves encore nécessaires

- Données agrégées québécoises **par quintile/décile et situation familiale**, avec couverture et méthode de pondération; consentement/licence et protection de la vie privée pour toute donnée de cas;
- Microsimulation fédérale et québécoise des crédits, prestations, retenues et déductions, **séparément par année**;
- Incidence de la taxe à la consommation dans les dépenses et de l'inflation, sans double comptage des taxes comprises dans les prix;
- Comptabilité des PME et grandes sociétés, charges patronales, crédits, pertes et répercussions des coûts;
- Effets municipaux, fonciers et scolaires; services de proximité et redistribution;
- Cohérence avec le modèle P52B décennal, les 20 preuves P52A et le rapprochement officiel P52C, **sans transformer les cas fictifs en recettes publiques agrégées**;
- Avis juridique et examen indépendant avant tout chiffrage ou proposition normative.

**Le dépôt, la branche `main`, le site et les documents `official/reference` ne sont pas modifiés par ce volet. P52D reste un outil candidat en PR brouillon. PR640 : NE PAS FUSIONNER. NO_GO.**
