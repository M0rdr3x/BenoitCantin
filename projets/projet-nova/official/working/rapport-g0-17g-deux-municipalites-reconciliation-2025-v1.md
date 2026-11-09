# Projet Nova–Sinjira — G0.17g : deux municipalités réelles, mêmes exercices et périmètres comptables différents

**8 novembre 2026 · Rapport de travail financier · Préparation interne du programme : 47/100, soit 53 points à valider.**

**Statut : deux états financiers municipaux de 2025 contrôlés, rapprochements arithmétiques et tests ajoutés à GitHub. Ceci n'est ni un échantillon statistiquement représentatif du Québec ni une preuve que le système fiscal Nova à deux prélèvements est financé.**

## 1. Pourquoi ce deuxième cas change la méthode

G0.17f a concilié les comptes 2025 de Port-Daniel–Gascons, une municipalité dont les revenus comptabilisés sont dominés par des transferts d'investissement. Si cette seule commune servait de point de départ aux taux de taxe Nova, la projection québécoise serait gravement biaisée.

G0.17g confronte ce cas au [**rapport financier consolidé 2025 de Saguenay, municipalité 94068**](https://ville.saguenay.ca/files/medias/La-ville-et-vie-d%C3%A9mocratique/Publications/Budget/Rapports-financiers-consolid%C3%A9s/Rapport-financier-2025-consolid%C3%A9-final.pdf), un ensemble beaucoup plus étendu, comprenant des organismes contrôlés et un réseau d'électricité. Le second document présente une **opinion d'audit non modifiée** datée du **2 juin 2026**, contre une **opinion avec réserve** pour Port-Daniel–Gascons le **8 juin 2026**. Ces opinions portent sur **les états financiers des municipalités**, pas sur les propositions politiques Nova.

Le [**rapport financier 2025 de Port-Daniel–Gascons, code 02047**](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2025-et-autres-02047.pdf) sert de premier cas, déjà réconcilié dans `data/g017f-rapprochement-municipal-fonctionnement-investissement-tresorerie-2025.json`.

### Sources et précision du contrôle visuel

Pour Saguenay, les tableaux des **résultats S7**, de la **situation financière S8** et de la **variation des actifs financiers nets S9** ont été consultés en **captures visuelles du PDF**, index de pages **6, 7 et 8**. Les tableaux de flux de trésorerie **S10**, de résultats fiscaux **S13–S14**, les charges par nature **S19** et l'opinion de l'auditeur ont également été étudiés **par texte extrait**; la capture de certaines pages a produit une erreur de cache. Les octets immuables du PDF et leur empreinte SHA-256 ne sont pas conservés. La donnée n'est pas présentée comme une vérification du grand livre municipal ni des relevés bancaires.

**La présentation 2024 comparative de Saguenay a été redressée (note 24).** Aucune croissance interannuelle ni classement de la qualité de gestion n'est affirmé dans cette phase.

## 2. Deux profils comptables pour 2025

| Indicateur sur les états 2025, dollars | Port-Daniel–Gascons | Saguenay |
| --- | ---: | ---: |
| Revenus totaux reconnus | **25 730 544** | **540 158 703** |
| Taxes reconnues | 4 525 681 | 317 831 049 |
| Transferts gouvernementaux reconnus | 20 524 044 | 64 741 160 |
| Charges comptables totales | 7 021 908 | 534 427 768 |
| Excédent comptable annuel | 18 708 636 | 5 730 935 |
| Revenus d'investissement reconnus | 19 799 872 | 15 361 442 |
| Excédent fiscal de fonctionnement | **68 566** | **14 079 053** |
| Excédent / déficit fiscal d'investissement | **−1 845 312** | **+4 755 759** |
| Trésorerie au 31 décembre | **1 999 351** | **188 577 717** |
| Dette financière nette au 31 décembre | 10 526 722 | 612 200 553 |

Le tableau **n'autorise pas** à comparer directement la productivité, la fiscalité par personne ou les performances de gestion : les villes n'ont ni la même taille, ni le même périmètre de consolidation, ni les mêmes activités. L'une comprend un réseau d'électricité et des organismes contrôlés, l'autre un contexte exceptionnel de financement d'immobilisations. Les effectifs, la population desservie et les services comparables ne sont pas normalisés.

## 3. La part des transferts : une information importante, pas un jugement

Chaque proportion est calculée **sur le total des revenus comptabilisés par la commune concernée**, et non sur le budget du Québec :

| Part des revenus comptabilisés en 2025 | Port-Daniel–Gascons | Saguenay |
| --- | ---: | ---: |
| Transferts gouvernementaux | **79,77 %** | **11,99 %** |
| Taxes | **17,59 %** | **58,84 %** |

Ces ratios se calculent notamment par **20 524 044 ÷ 25 730 544** et **64 741 160 ÷ 540 158 703**. Les valeurs ne mesurent **ni le taux de subvention marginal, ni les taxes Nova, ni les économies permises par une réforme**.

L'écart montre d'abord **l'importance du périmètre et du calendrier des immobilisations** : les grands transferts constatés à Port-Daniel–Gascons en 2025 rendent ses recettes totales fortement dépendantes de l'année d'investissement. La proportion ne permet pas de conclure que la municipalité dépend durablement des subventions dans la même mesure en exploitation, ni de généraliser à l'ensemble des régions.

Les transferts inscrits comme revenus **ne prouvent pas qu'ils ont été reçus à la banque**. Le registre 2025 des municipalités n'authentifie pas non plus un paiement spécifique TECQ ou PRIMEAU.

## 4. Saguenay : trois rapprochements indépendants à ne pas mélanger

### 4.1 Résultat comptable et résultat fiscal

Les **540 158 703 $ de revenus consolidés** et les **534 427 768 $ de charges** produisent un excédent comptable annuel de **5 730 935 $**.

Le tableau **S13** présente **15 361 442 $ de revenus d'investissement** à extraire pour le calcul du fonctionnement. L'opération est donc :

```text
Revenus de fonctionnement reconnus                  524 797 261 $
Charges comptables totales                         -534 427 768 $
Résultat avant conciliation à des fins fiscales      -9 630 507 $
Ajustements fiscaux nets                            +23 709 560 $
Excédent fiscal de fonctionnement                    14 079 053 $
```

L'annexe d'investissement **S14** se réconcilie séparément :

```text
Revenus d'investissement reconnus                    15 361 442 $
Acquisitions corporelles constatées                -110 900 628 $
Acquisitions de propriétés pour revente                -248 049 $
Prêts et participations                               -296 500 $
Financement à long terme d'investissement           +93 178 956 $
Affectations d'investissement                        +7 660 538 $
Excédent fiscal d'investissement                      +4 755 759 $
```

Ces résultats fiscaux ne sont **ni des sommes bancaires, ni des crédits libres et affectables à n'importe quelle dépense de Nova**.

### 4.2 Flux de trésorerie de l'ensemble consolidé

```text
Trésorerie au début de 2025                        157 390 687 $
Encaisse nette provenant du fonctionnement        +103 120 417 $
Encaisse nette liée aux investissements            -107 111 111 $
Encaisse nette des opérations de placement             +514 945 $
Encaisse nette provenant du financement             +34 662 779 $
Augmentation nette de trésorerie                     +31 187 030 $
Trésorerie finale au 31 décembre 2025               188 577 717 $
```

Le financement total se réconcilie par **148 121 000 $ d'émissions de dette − 116 699 801 $ de remboursement du capital + 3 204 602 $ de variation nette des emprunts temporaires + 36 978 $ de frais reportés = 34 662 779 $**.

Saguenay inscrit **110 900 628 $ d'acquisitions d'immobilisations à l'état des actifs nets** et **108 303 207 $ de décaissements pour acquisitions corporelles**, deux montants qui ne doivent pas être confondus. Le bilan S8 affiche **327 841 873 $ d'actifs financiers** et **940 042 426 $ de passifs**, soit une **dette financière nette de 612 200 553 $**.

La présentation d'un excédent annuel comptable, d'un excédent fiscal et d'une augmentation de trésorerie **ne permet pas de considérer les trois résultats comme trois sources de financement distinctes**.

## 5. Ce que cette étape apporte concrètement au financement Nova

Le Projet Nova souhaite construire un modèle à **deux prélèvements**, avec continuité des services, protections de main-d'œuvre et amélioration du revenu disponible. Ces deux municipalités démontrent pourquoi ce modèle ne doit pas être fondé sur un taux unique déduit de quelques observations locales :

1. **Distinguer recettes courantes et recettes d'investissement.** Des transferts d'immobilisation reconnus en comptabilité ne financent pas nécessairement les salaires, l'entretien et la dette ordinaire.
2. **Respecter le périmètre comptable.** Une ville consolidée avec réseau d'électricité, organismes contrôlés et services particuliers n'est pas directement comparable à une commune de taille différente.
3. **Comparer à population et fonctions similaires seulement.** Il faut les bases de population officielles, les exclusions et le dictionnaire de comptes du même millésime avant de produire des coûts par personne ou des moyennes territoriales.
4. **Neutraliser les doubles comptes publics.** Un transfert d'un gouvernement vers une municipalité reste un coût réel pour le payeur et une recette pour le receveur; il doit être éliminé une seule fois dans une consolidation du secteur public.
5. **Mesurer les financements effectivement versés.** Engagement, revenu reconnu, facture, somme retenue, paiement effectué et encaissement ne sont pas synonymes.
6. **Démontrer les deux scénarios indépendamment.** Dans le Canada, les compétences fiscales fédérales et provinciales se distinguent; dans le Québec souverain, recettes nationales, dette, contrats, pensions et programmes fédéraux appellent des accords et des budgets explicites.

**Aucune des deux municipalités ne fournit, à elle seule, l'assiette complète de prélèvement des ménages ou des entreprises du Québec.** Les revenus supposés d'un mécanisme anti-paradis fiscaux ne sont pas déduits de leur bilan. Leur comparaison ne démontre **ni un rendement d'impôt Nova ni une économie nette**.

## 6. Registre, vérifications et travail réellement restant

- `data/g017g-deux-municipalites-finances-auditees-2025.json` : 2025, deux communes de périmètres différents, sources, auditeurs, résultats fiscaux, flux de caisse, dette et composition descriptive des recettes.
- `assets/g017g-two-municipalities-audit-core.mjs` : rapproche les montants 2025 à leurs états, contrôle les flux de trésorerie et bloque les conclusions nationales, les taux fiscaux et les classements non fondés.
- `tests/g017g-two-municipalities-audit.test.mjs` : **89 tests de calcul et de portée réussis par rejeu JavaScript/V8 isolé**. Une exécution native GitHub Actions est à distinguer de cette validation locale; même un succès de tests natifs ne vaut **pas audit indépendant du programme Nova**.

**Six portes de preuve demeurent ouvertes** : téléchargement des fichiers MAMH originaux 2024 et 2025 et de leurs dictionnaires, harmonisation des périmètres municipaux et organismes contrôlés, contrôle des versements et recettes de même exercice, identification des populations et services comparables, chiffrage décennal des opérations et actifs, et revue indépendante des budgets et compétences pour les deux statuts constitutionnels.

**Décision G0.17g :** deuxième cas réel ajouté, états annuels et trésorerie de Saguenay rapprochés, ratios de recettes calculés sans extrapolation. La grille interne reste à **47/100 — 53 points restant à valider**, faute de financement décennal complet, de données municipales exhaustives et de vérifications externes.

**Suite G0.17h :** importer les fichiers MAMH originaux et contrôler la cohérence de deux exercices et des périmètres des organismes; développer ensuite une population de communes représentative avant les calculs de taux Nova, avec démonstration des services et salaires protégés.
