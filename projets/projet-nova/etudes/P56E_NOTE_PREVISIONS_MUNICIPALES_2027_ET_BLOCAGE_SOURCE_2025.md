# P56E — Enveloppes municipales publiées pour 2027 et protocole de contreparties

**7 novembre 2026 · Étude candidate, non adoptée et non certifiée · NO_GO_AUTOMATIQUE.**

## 1. Périmètre et nouvel élément de preuve

Le jalon P56D a construit un protocole de consolidation sur des **flux fictifs** et répertorié 18 obligations municipales et sociales. P56E ajoute des **enveloppes financières publiques effectivement publiées**, mais les maintient au niveau de preuve exact : **prévisions du gouvernement pour l'année civile 2027**, non versements exécutés ni revenus comptabilisés par les municipalités. Il ne faut pas confondre une nouvelle donnée sourcée avec la conclusion selon laquelle la réforme fiscale Nova est viable.

Le ministère des Affaires municipales et de l'Habitation publie sur la page officielle [Préparation du budget municipal 2027](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/preparation-budget), mise à jour le **26 octobre 2026**, les montants estimés à partir de données connues en septembre 2026. Il précise expressément que les versements réels pourraient varier. Les municipalités bénéficiaires ne doivent pas déposer de demande pour ces programmes : les sommes sont calculées et versées par les autorités aux bénéficiaires admissibles.

### Enveloppes prévisionnelles publiées

| Programme | Année civile 2027, millions CAD | Réserve |
|---|---:|---|
| Répartition de la croissance d'une partie de la TVQ | **821,0** | Soumise à la formule et aux indices de vitalité/éloignement |
| Compensations pour les terres publiques | **25,8** | Réparties selon les terres publiques admissibles |
| Partage des revenus des redevances sur les ressources naturelles | **38,0** | En faveur des MRC admissibles |
| Péréquation | **67,0** | Pour les municipalités à potentiel fiscal limité |
| **Sous-total documenté de ces quatre programmes seulement** | **951,8** | **Ne représente pas tous les transferts municipaux** |

Les quatre montants sont des **enveloppes prévues**, pas le total de l'aide municipale, ni une dépense confirmée, ni une recette additionnelle d'une nouvelle taxe. **Aucun montant n'est importé** dans les prévisions P52B 2027–2036. Une **année civile 2027** n'est pas automatiquement interchangeable avec l'**exercice budgétaire provincial 2027–2028**.

Pour la croissance de TVQ, la même source indique une répartition prévisionnelle **93,5 % au volet I et 6,5 % au volet II pour 2027**. Sur l'enveloppe de 821,0 M$, l'application purement arithmétique de ces parts donne 767,635 M$ et 53,365 M$. Ces montants de volet ne sont ni un montant réellement versé à une municipalité ni une estimation des revenus de Nova.

Les **compensations tenant lieu de taxes pour les immeubles parapublics** constituent une autre rubrique : la source explique que leurs montants municipaux 2027 ne pourront être calculés qu'après réception des données nécessaires. Elles **ne sont pas comprises** par hypothèse dans les 951,8 M$.

## 2. Pourquoi il manque encore les contreparties financières

La seconde source officielle, [Rapport financier des organismes municipaux](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier), précise que les rapports sont transmis annuellement, peuvent être corrigés et que la base de données ouverte est mise à jour quotidiennement. **Ce n'est pas une autorisation d'inventer une réception comptable correspondant au budget provincial.**

Le registre \`P56E_MATRICE_CONTREPARTIES_PREVISIONNELLES_ET_SOURCES.json\` définit **huit écritures candidates à rechercher** : pour chacun des quatre programmes, une écriture de dépense ou de transfert du Québec et une écriture de recette municipale ou MRC. Toutes les colonnes \`montant_reconcilie_mcad\`, pièces justificatives, dates et identifiants réels demeurent \`null\`.

Avant de constater un véritable rapprochement, obtenir les éléments suivants pour chaque programme : identité du payeur et du bénéficiaire, montant versé, type d'opération, date, exercice financier, convention d'affectation, écriture dans les comptes du gouvernement provincial, écriture dans les rapports municipaux, éventuels ajustements et liste de périmètre comptable.

**L'élimination d'un transfert dans un regroupement comptable n'est pas une économie.** Un transfert de province à municipalité reste normalement dans les dépenses provinciales si la municipalité est extérieure au périmètre consolidé provincial. Dans une vue analytique élargie contenant les deux entités, on pourrait éliminer les transactions réciproques **seulement après authentification de leurs écritures**. Le coût final du service et l'obligation de le rendre subsistent.

## 3. Anomalie bloquante du « Sommaire des transferts fiscaux 2025 »

La page gouvernementale [Encadrement du financement et de la fiscalité des municipalités](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/fiscalite/encadrement) propose un lien intitulé **Sommaire des transferts fiscaux 2025**. L'URL de cette ressource est :

\`https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/SOM_transferts_fiscaux.pdf\`

Au cours de la consultation automatisée du **7 novembre 2026**, les **résultats d'extraction textuelle décrivaient le millésime 2025**, alors que les **rendus visuels de certaines pages présentaient un tableau intitulé 2024**. Il peut s'agir d'un désaccord de version mis en cache par l'outil de lecture; ce constat **ne prouve pas** une erreur sur le site gouvernemental lui-même.

**Décision de qualité : aucune valeur de ce document n'entre dans P56E** avant récupération de la version binaire canonique, contrôle de la page de garde et de chaque page de données, empreinte SHA-256, date de réception, millésime et concordance texte/image, puis rapprochement des totaux de programmes. La discordance est tracée comme **source en quarantaine**, non comme série officielle confirmée.

## 4. Contrôles et fichiers créés

- \`P56E_REGISTRE_TRANSFERTS_MUNICIPAUX_2027_ET_VERIFICATION_SOURCES.json\` : **quatre enveloppes** et sources exactes, statut prévisionnel et anomalie 2025 en quarantaine.
- \`scripts/rapprocher_enveloppes_municipales_nova_p56e.py\` : vérification des sources, des dates, des quatre enveloppes, du sous-total, de la répartition TVQ, de l'absence de paiements réels présumés et du refus de certification.
- \`scripts/tests/test_rapprocher_enveloppes_municipales_nova_p56e.py\` : **38 tests** portant notamment sur les fausses recettes, années incompatibles, contreparties inventées, fausses validations et écrasement de rapports.
- \`P56E_MATRICE_CONTREPARTIES_PREVISIONNELLES_ET_SOURCES.json\` : deux lignes candidates par programme, sans montant de dépense ou recette attesté.
- \`.github/workflows/validate-nova-p56e.yml\` : vérification automatisée.
- Cette note.

**Commande depuis la racine GitHub :**

\`\`\`bash
python scripts/rapprocher_enveloppes_municipales_nova_p56e.py \
  --registre projets/projet-nova/etudes/P56E_REGISTRE_TRANSFERTS_MUNICIPAUX_2027_ET_VERIFICATION_SOURCES.json
\`\`\`

Le mode \`--exiger-certification\` doit échouer avec **code 3**. Les sorties n'écrasent pas de fichier existant; elles ne modifient pas les programmes officiels. Le modèle refuse de traiter un bénéficiaire, une pièce de paiement, une déclaration de source ou un montant réellement versé comme connu sans dossier séparé authentifié.

## 5. Suite pour un programme Nova réellement chiffré

**P56F devrait résoudre deux problèmes concrets** plutôt que créer de nouveaux scénarios fictifs :

1. **Source 2025 :** obtenir le document PDF canonique, le millésime et la somme exacte par programme, puis le comparer au sommaire des transferts 2024 et aux comptes municipaux.
2. **Contreparties 2027 :** sélectionner un jeu de rapports financiers municipaux de la bonne année et les relevés de paiements provinciaux; noter précisément chaque différence de calendrier et de périmètre; obtenir l'avis d'un comptable municipal sur les éliminations.

Après ces contrôles, des projections pour 2027–2036 pourraient commencer à être proposées **en séparant calendrier civil et exercice budgétaire provincial**, sans supprimer silencieusement impôt foncier, services d'eau, police, salaires ni dépenses d'entretien.

La fiscalité proposée de Nova reste conditionnelle, avec deux cadres constitutionnels distincts et des prestations préservées. Les **600 montants budgétaires P52B**, **720 incidences P52D**, **20 pièces P52A** et les avis indépendants demeurent ouverts.

**Complétude P55N : 53 % estimés**, fourchette 45–60 %. Aucune économie certifiée, aucun taux définitif adopté, aucune décision d'abolition fiscale, aucune publication de nouveau programme officiel, aucune fusion dans \`main\` et aucune modification de SINJIRA. **Décision : NO_GO_AUTOMATIQUE.**
