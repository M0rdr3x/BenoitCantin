# Projet Nova — P56F : transferts municipaux historiques, comparabilité et incident documentaire

**7 novembre 2026 — Étude technique candidate, non adoptée.**  
**Décision : `NO_GO_AUTOMATIQUE` — aucune hausse automatique du baromètre P55N.**

## 1. Avancement réel

Le baromètre de maturité du Projet Nova demeure **53 %**, fourchette 45–60 %. La politique des deux prélèvements proposée n'a toujours ni budget décennal démontré, ni taux adopté, ni avis indépendant signé. Les **600 montants P52B**, **720 montants d'incidence P52D** et vingt preuves fiscales P52A restent ouverts.

Le jalon P56E avait documenté des enveloppes **prévisionnelles et partielles pour l'année civile 2027**. P56F introduit une deuxième référence **réellement historique et issue de la documentation officielle**, distincte de cette prévision, et renforce la mise en quarantaine d'une source qui ne permet pas encore de certifier le millésime.

## 2. Base historique officielle sur les transferts municipaux, exercice 2023

Source : ministère des Affaires municipales et de l'Habitation, publication **« Le financement et la fiscalité des organismes municipaux au Québec », mars 2025**, rubrique « Transferts gouvernementaux — Transferts totaux aux organismes municipaux – 2023 ». [Consulter le rapport officiel](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/fiscalite/fiscalite_organismes_municipaux.pdf).

Le rapport précise : **données de 2023 compilées à partir des rapports financiers reçus jusqu'au 30 janvier 2025**. Il comprend des municipalités locales et des organismes supramunicipaux ou paramunicipaux, avec des particularités de consolidation; il ne représente pas l'ensemble des seuls transferts fiscaux de quatre programmes et n'atteste pas la ventilation dans les comptes provinciaux de P52B.

| Transferts aux organismes municipaux en 2023 | Montant (M$) | Part publiée |
|---|---:|---:|
| Transferts de droits, inconditionnels selon le cadre applicable | 763,6 | 12,3 % |
| Transferts relatifs aux ententes de partage de frais, conditionnels | 5 426,5 | 87,7 % |
| **Total historique agrégé** | **6 190,1** | **100 %** |

Les sous-catégories déjà incluses dans les **5 426,5 M$** comprennent notamment **2 118,4 M$** en transport collectif, **1 048,0 M$** en eau et égout et **869,2 M$** en réseau routier. **Ne pas les ajouter une seconde fois au total**; ces montants renseignent les services et infrastructures à protéger, mais ne constituent pas des engagements individualisés de Nova ni une projection future.

**Arithmétique interne :** 763,6 + 5 426,5 = 6 190,1 M$. Cette égalité prouve uniquement la concordance des totaux tels que publiés. Aucun audit externe du plan Nova n'en découle.

## 3. Pourquoi il serait incorrect de calculer une variation 2023 → 2027

P56E a établi un sous-total de **951,8 M$** pour **quatre enveloppes prévues pour 2027** : croissance de la TVQ, compensations terres publiques, partage de redevances sur les ressources et péréquation. Ces enveloppes **ne représentent pas tous les transferts aux municipalités** et sont des prévisions non encore payées. [Source — préparation du budget municipal 2027](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/preparation-budget).

| Propriété comparée | 2023 | 2027 |
|---|---|---|
| Année | Résultats historiques 2023, agrégés | Année civile prévisionnelle 2027 |
| Couverture | Ensemble de plusieurs transferts gouvernementaux selon le rapport 2025 | Seulement quatre programmes |
| Source | Compilation des rapports municipaux | Prévisions ministérielles |
| Écritures provinciales et municipales appariées | Non documentées dans Nova | Non documentées dans Nova |
| Comparaison de croissance valable | **Non** | **Non** |

**Interdiction :** ne pas calculer un pourcentage de hausse, baisse, déficit, épargne ou rendement Nova entre 6 190,1 et 951,8 M$. Une année de référence, un périmètre différent et des catégories inégales ne produisent pas une série temporelle comparable.

## 4. Incident documentaire : Sommaire des transferts fiscaux « 2025 »

La [page officielle d'encadrement de la fiscalité municipale](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/fiscalite/encadrement) présente un **« Sommaire des transferts fiscaux 2025 »**. L'URL associée est :
`https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/SOM_transferts_fiscaux.pdf`.

Lors de la consultation du 7 novembre 2026, l'**extraction textuelle indexée** pour cette même URL décrivait **2025**, alors que les **captures visuelles renvoyées par l'outil PDF** montraient les tableaux de **2024**, avec leurs valeurs de 2024. Ces réponses peuvent être issues de versions mises en cache différentes. Cela **ne démontre pas une erreur sur le site du ministère** et ne permet pas d'affirmer lequel des deux documents était le binaire canonique à la date considérée.

Une tentative de récupérer indépendamment le PDF original et de vérifier son empreinte numérique n'a pas abouti. **Aucun fichier binaire local canonique ni empreinte SHA-256 n'est disponible dans le projet P56F.**

**Contrôle P56F :** conserver l'incident en quarantaine, garder le montant 2025 à `null`, refuser toute importation en compte 2025 et ne pas déduire un taux de croissance. La résolution exige récupération canonique, date, empreinte SHA-256, inspection page par page, confrontation texte/image du **même binaire**, comparaison avec le document 2024 distinct et, si besoin, confirmation ministérielle.

## 5. Nouveaux contrôles techniques et limites de preuve

- `P56F_REFERENCES_MUNICIPALES_2023_2027_ET_QUARANTAINE_2025.json` : référence officielle 2023, prévisions 2027 et état de l'incident 2025;
- `scripts/verifier_provenance_transferts_municipaux_nova_p56f.py` : rapprochement sur des chaînes décimales exactes; réutilise le contrôle P56E, refuse les faux chiffres 2025, l'addition entre années et la validation automatique;
- `scripts/tests/test_verifier_provenance_transferts_municipaux_nova_p56f.py` : 40 tests, incluant soustraction des preuves inventées, faux millésimes, faux taux de croissance, fausses contreparties et écrasement de rapports;
- `.github/workflows/validate-nova-p56f.yml` : vérification P56E et P56F à chaque changement.

Commande :
```bash
python scripts/verifier_provenance_transferts_municipaux_nova_p56f.py \
  --historique projets/projet-nova/etudes/P56F_REFERENCES_MUNICIPALES_2023_2027_ET_QUARANTAINE_2025.json \
  --previsions projets/projet-nova/etudes/P56E_REGISTRE_TRANSFERTS_MUNICIPAUX_2027_ET_VERIFICATION_SOURCES.json
```

`--exiger-faisabilite` doit retourner le code 3. Les rapports existants ne sont pas écrasés. Les valeurs connues ne servent pas à remplir artificiellement les années 2027–2036 du modèle P52B, et la réussite de la CI ne constitue pas un audit de comptes municipaux ni une certification fiscale.

## 6. Suite professionnelle pour augmenter réellement la complétude

**P56G à privilégier :** établir un **tableau de provenance entre un rapport municipal transmis, sa recette de transfert et la dépense provinciale correspondante**, avec années et écritures réelles. À ce jour, les preuves de cette paire de transactions ne figurent pas dans le dépôt. Il faut aussi obtenir une version canonique sans ambiguïté du sommaire 2025 avant toute nouvelle série temporelle.

Les priorités de fond restent : financer toutes les fonctions municipales et provinciales, préserver la main-d'œuvre, les services, les prestations et le pouvoir d'achat, puis obtenir les calculs décennaux, scénarios constitutionnels séparés et avis juridiques, comptables et actuariels indépendants.

**Statut : `NO_GO_AUTOMATIQUE`.** Pas de taux Nova adopté, pas de fausse économie, pas d'activation publique, pas de fusion de la PR, pas de modification de `main` ou de SINJIRA.
