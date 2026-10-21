# Projet Nova — P53E : recettes municipales réelles 2024, extraction reproductible

**21 octobre 2026 · Données primaires officielles téléchargées · Observations historiques, NON budget 2026‑2027, NON certification de réforme Nova.**

## Avancement substantiel

Les deux sources du ministère des Affaires municipales et de l'Habitation (MAMH) ont été **téléchargées et hachées** :
- [Données réelles 2024, Simple occurrence](https://mamh.gouv.qc.ca/fichiersdonneesouvertes/Données-réelles-2024-SimpleOccurrence.csv) : **20 254 172 octets**, SHA-256 `151c0a2b1fc0dfac8c8cc3dba04b74f5c49fbb98fdfd78251925959d1ad35fff`.
- [Données réelles 2024, Description poste](https://mamh.gouv.qc.ca/fichiersdonneesouvertes/Données-réelles-2024-DescriptionPoste.csv) : **1 749 357 octets**, SHA-256 `23cd037a93d0ea7a8acd21a768838df8b6cd6a88d827778be68ee82f5186f542`.
- [Catalogue source Données Québec](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents). Licence indiquée **CC BY 4.0**, attribution au MAMH.

**Limite d'archive :** les fichiers complets (20,3 Mo et 1,75 Mo) ne sont **pas** copiés dans Git. Le dépôt contient une **extraction des 1 094 organismes classés « Municipalité locale »**, 15 champs financiers sélectionnés, et un extrait codifié de leur dictionnaire. Les SHA-256 des originaux sont des empreintes observées lors de leur téléchargement; l'intégrité de l'extraction peut être vérifiée directement dans Git. Les mises à jour quotidiennes nécessitent de télécharger à nouveau et de dater chaque nouvelle version.

## Méthodologie

1. Décoder le CSV original UTF-8 avec BOM, **1 343 lignes d'organismes, 7 336 colonnes**.
2. Filtrer strictement `type_org = Municipalité locale` : **1 094 comptes, 1 094 codes `cod_geo` distincts**. Les **249 autres organismes** (MRC, régies, organismes de transport, communautés métropolitaines) ne sont pas additionnés.
3. Relier chaque code à la table de **8 003 entrées** du dictionnaire, en retenant `CRIIX00016`, `CRIIX00018` et `CRIIX00405` à `CRIIX00417`.
4. Calculer les sommes **en dollars canadiens, sans flottants** ni arrondis avant la sommation, et compter les champs vides séparément.
5. Reproduire pour chaque municipalité l'identité de poste : total des revenus `CRIIX00405` = somme des douze catégories `CRIIX00406…CRIIX00417`, sans double ajout des catégories parents et enfants. Les blancs contribuent 0 **uniquement à ce contrôle d'addition**, sans transformer une non-déclaration en recette certifiée égale à zéro.
6. Conserver les autres administrations hors périmètre : aucun total municipal sectoriel Québec **consolidé avec les MRC et organismes** ne peut être déduit de ces seules lignes.

## Observations du périmètre « municipalités locales » — 2024

| Poste comptable MAMH | Total historique en dollars |
|---|---:|
| `CRIIX00016` — Taxes sur la valeur foncière (toutes catégories) | **15 085 531 572** |
| `CRIIX00018` — Taxe foncière générale (incluse dans la ligne précédente) | 13 325 713 274 |
| `CRIIX00406` — Taxes municipales, toutes catégories | **17 337 284 213** |
| `CRIIX00409` — Transferts | 5 376 508 934 |
| `CRIIX00405` — Revenus totaux | **32 367 623 561** |
| Différence arithmétique revenus moins taxes moins transferts | **9 653 830 414** |

Vérification complète : `17 337 284 213 + 5 376 508 934 + 9 653 830 414 = 32 367 623 561` **sans double compte interne dans cette vue**.

**Ne pas additionner** 15,086 G$ aux 17,337 G$ : le premier poste est inclus dans le second. Le montant de 9,654 G$ recouvre des flux *autres que taxes et transferts*, notamment des compensations tenant lieu de taxes, quotes-parts, services rendus, droits, amendes, intérêts et divers; **certaines quotes-parts sont susceptibles de circuler entre administrations**. Il ne constitue donc **pas** des recettes nouvelles nettes consolidées ni un montant automatiquement disponible pour une réforme à deux prélèvements.

Le poste foncier `CRIIX00016` contient une **valeur manquante** pour le code municipal `45080`, Saint-Benoît-du-Lac : 1 093 valeurs non vides sur 1 094 organismes. Ce blanc **n'est pas recodé comme zéro**. Le total de 15 085 531 572 $ décrit strictement **les valeurs observées**.

## Situation des lacunes E04 / E05

- **E04 (foncier municipal)** : montant historique directement calculé et traçable pour les 1 093 lignes renseignées, **pas une recette 2026‑2027 certifiée**.
- **E05 (autres revenus locaux)** : les revenus 2024 peuvent être ventilés par codes, mais il reste à neutraliser les quotes-parts entre municipalités/MRC, les compensations et les transferts entre administrations. La différence de 9,654 G$ est une **catégorie comptable brute**, pas le total E05 net intergouvernemental.
- **F04** : pas d'avis indépendant signé, pas de preuve fiscale globale validée; les autres dépenses locales, la répartition des compétences et la continuité des services doivent être vérifiées.

Il ne faut pas additionner **32,368 G$ en 2024** aux **166,492 G$ du budget provincial 2026‑2027**, ni aux **43,550 G$ d'impôt fédéral net des particuliers en 2024** (P53C). Ces sommes ont des définitions, années, entités bénéficiaires et transferts différents.

## Restitution et contrôle

- `sources/P53E_MAMH_2024_MUNICIPALITES_LOCALES_SELECTION.csv` : 1 094 lignes du fichier 2024 du MAMH, conservées avec codes municipaux, libellés et champs sélectionnés.
- `sources/P53E_MAMH_2024_DICTIONNAIRE_SELECTION.json` : description officielle de 15 codes.
- `P53E_PREUVES_HISTORIQUES_MUNICIPALES.json` : SHA-256, agrégats, périmètres, contrôles des blancs et dépendances.
- `scripts/valider_recettes_municipales_nova_p53e.py` : recalcul indépendant à partir de l'extraction Git et refus des conclusions non certifiées.

Exécution prévue :

```bash
python scripts/valider_recettes_municipales_nova_p53e.py --rapport p53e_bilan.json
python scripts/valider_recettes_municipales_nova_p53e.py --exiger-consolidation
```

Le mode ordinaire retourne 0 uniquement si l'extraction et le dictionnaire sont intègres **avec décision `NO_GO_AUTOMATIQUE`**. Le mode strict retourne 3, car la preuve F04, la consolidation nationale, les recettes 2026‑2027 et les validations humaines ne sont pas obtenues. Les erreurs de source ou de calcul produisent 2.

**Pas de taux Nova adopté, pas de financement public promis sans étude, pas de fusion de PR #673, pas de changement de `main` ou SINJIRA.**
