# Projet Nova–Sinjira — G0.17c : recettes municipales réelles et protection du financement des services d'eau

**8 novembre 2026 · Rapport financier de travail · Score de préparation interne : 47/100 (53 points restant à valider).**

**Statut :** deux sources gouvernementales historiques identifiées, calculs de concordance réalisés et garde-fous programmés. Aucune démonstration de viabilité du système fiscal Nova à deux prélèvements, aucune approbation juridique ni certification indépendante.

## 1. Faits nouveaux utiles pour la réforme Nova

La phase G0.17b a préparé un outil d'importation des données financières municipales réelles 2024–2025, mais elle n'a pas pu télécharger les CSV. G0.17c ajoute **deux références directes et publiques du ministère des Affaires municipales et de l'Habitation (MAMH)** qui permettent de mieux circonscrire les ressources municipales à protéger.

- [Dossier MAMH rendu public le 18 juin 2026, DAI-2026-030](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/demande_acces/2026/DAI_2026-030_cout_gestion_infrastructure.pdf) : présentation statistique des **revenus consolidés réels des organismes municipaux pour 2024**, issue de leurs rapports financiers.
- [MAMH, Rapport annuel de l'usage de l'eau potable 2023, publié en 2025](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/infrastructures/strategie_quebecoise_eau_potable/RAP_usage_eau_potable_2023.pdf) : revenus affectés et **coût complet annuel moyen** estimé des réseaux d'eau, incluant les besoins de maintien et de rattrapage des actifs.

**Limites documentaires importantes :** le premier PDF (environ 18,8 Mo) a été analysé par extraction textuelle, mais sa capture visuelle a échoué parce que le fichier dépasse la limite du navigateur de recherche. Les chiffres doivent encore être rapprochés des fichiers CSV comptables originaux. Le second PDF a été lu textuellement et une capture de sa page imprimée **21** (index PDF **20**) a confirmé le mode de calcul du coût total de l'eau et son chiffre de **6 G$**; la capture de la page imprimée 14 sur les 40 % de couverture n'a pas abouti. Cela n'est **pas un audit financier externe**.

## 2. Revenus réels des organismes municipaux en 2024

La présentation MAMH indique **31,3 G$ de revenus consolidés en 2024** pour les organismes municipaux du Québec. Les composantes sont arrondies au dixième de milliard :

| Provenance du revenu municipal | 2024, milliards $ | Traitement dans Nova |
| --- | ---: | --- |
| Taxes sur la valeur foncière | **15,0** | Ressource à remplacer si supprimée, sans interrompre les services |
| Transferts gouvernementaux | **7,4** | Recette locale, mais flux interne à neutraliser dans un consolidé gouvernement + municipalités |
| Ventes de biens et services | **3,2** | Recette réelle à qualifier, qui n'est pas automatiquement un impôt |
| Tarification | **2,2** | Distinction juridique entre prix du service et prélèvement fiscal |
| Droits de mutation immobilière | **1,3** | Recette à remplacer si la réforme l'abolit |
| Autres sources locales | **2,2** | Ventilation comptable nécessaire avant de présumer son maintien |
| **Total** | **31,3** | **Recettes municipales historiques, non recettes additionnelles Nova** |

**Vérification :** `15,0 + 7,4 + 3,2 + 2,2 + 1,3 + 2,2 = 31,3` G$. En excluant **uniquement** les transferts gouvernementaux comme flux potentiellement interne au périmètre Québec + municipalités, on obtient **23,9 G$ de recettes municipales autonomes approximatives**, dans les catégories affichées. Le document donne une part officielle des revenus autonomes de **76,5 %**, avec un léger écart de ratio calculé possible parce que les valeurs du tableau sont arrondies. Il indique que la taxe foncière comptait pour **47,8 % des recettes municipales** de 2024.

L'exercice ne signifie **pas** que 15 G$ de revenus fonciers seraient automatiquement supprimables sans compensation, ni que les 7,4 G$ de transferts doivent être ajoutés aux recettes fiscales provinciales. Il ne prouve pas non plus une recette fiscale Nova en 2026. **Les frais d'utilisation, tarifs et droits doivent être qualifiés au regard du projet politique à deux prélèvements, et les différents paliers de compétence doivent rester distincts.**

## 3. Réseaux d'eau : la couverture du coût complet reste très partielle en 2023

Le rapport MAMH sur la **Stratégie québécoise d'économie d'eau potable** s'appuie sur **669 bilans municipaux** sur **849 municipalités concernées**, représentant environ **96 % de la population desservie par des réseaux d'eau potable**. La méthode est donc plus représentative de la population desservie que d'un échantillon uniforme de petites et grandes municipalités; elle ne couvre pas tous les services des municipalités ni toutes les populations.

Le rapport présente pour **2023** :

| Indicateur pour les services d'eau | Montant approximatif |
| --- | ---: |
| Revenus affectés aux services d'eau | **2,4 G$** |
| Coût complet moyen des services d'eau | **6,0 G$** |
| Couverture des coûts complets | **40 %** |
| Portion des coûts complets non couverte par les revenus affectés, à titre indicatif | **3,6 G$** |

**Précision fondamentale :** les **6 G$** représentent le coût de fonctionnement **plus des besoins moyens d'investissement calculés sur dix ans**, dont le maintien, le rattrapage et l'amélioration des infrastructures. Le calcul arithmétique **6,0 − 2,4 = 3,6 G$** est donc un **écart approximatif de couverture du coût économique complet**, et **non un déficit bancaire réellement constaté en 2023**, une facture exigible ni un besoin budgétaire établi pour 2026.

Selon le MAMH, les recettes affectées à l'eau en 2023 provenaient approximativement de la **taxe foncière (50 %)**, de la **tarification non volumétrique (36 %)**, de la **tarification volumétrique (7 %)** et des **autres recettes (7 %)**. Ces catégories font déjà partie des finances municipales et ne doivent **pas être additionnées comme une nouvelle recette de 2,4 G$** aux 31,3 G$ de l'année 2024. Il faut aussi distinguer les composantes historiques et les différences de période.

## 4. Implications opérationnelles pour les deux prélèvements Nova

Le Projet Nova–Sinjira recherche une simplification profonde avec **un prélèvement sur le revenu des personnes et des entreprises** et **un mécanisme contre les paradis fiscaux**, en évitant les contre-tarifs et en protégeant les travailleurs.

La réforme **ne peut pas présenter l'abolition des taxes foncières, des droits de mutation et des prélèvements liés à l'eau comme une économie nette** sans expliquer :

1. **Comment les dépenses locales continuent d'être financées**, y compris eau potable, assainissement, routes, sécurité incendie, administration, dette, entretien, investissement et réparations urgentes.
2. **Comment les municipalités reçoivent effectivement les ressources nécessaires** : assiette légale, mécanisme de transfert, obligations de maintien des services, calendrier de versement et transparence des comptes.
3. **Comment éviter de financer deux fois le même transfert** : la somme provinciale versée apparaît comme revenu local, mais doit être éliminée une fois dans la consolidation, sans supprimer le service réel.
4. **Comment définir les deux taxes sans cacher une troisième taxe** dans un tarif, droit ou redevance. Un prix réel payé pour un service peut avoir un statut juridique différent d'un impôt; la classification doit être faite **poste par poste**, et les effets sur les ménages doivent être mesurés.
5. **Comment maintenir la valeur des actifs et les emplois existants**. Les 6 G$ de coûts complets historiques des services d'eau incluent des besoins que l'on ne peut faire disparaître par une décision fiscale.
6. **Comment traiter le Québec souverain séparément** : les transferts fédéraux actuels ne sont pas une recette automatiquement transférable, et les obligations de dette, de pensions et de financement national doivent être chiffrées.

Le chiffre conditionnel de **112,369 G$ de recettes fiscales provinciales de remplacement** calculé en G0.16v pour 2026–2027 **ne contient pas une preuve de financement net des municipalités**. On ne doit **ni lui ajouter naïvement 31,3 G$ de recettes municipales de 2024**, ni le soustraire de ces recettes : les exercices, les périmètres et les transferts diffèrent. Le chiffre de **145,415 G$** du stress provincial sans transfert fédéral n'est pas le coût d'un Québec souverain.

## 5. Vérifications informatiques et état des travaux

- `data/g017c-recettes-municipales-2024-et-couts-eau-2023.json` : ressources officielles, tableau historique des six catégories de recettes, couverture du coût des réseaux d'eau, différences de millésime et deux scénarios non financés.
- `assets/g017c-municipal-water-finance-core.mjs` : refuse la transformation des observations de 2023–2024 en recette fiscale Nova de 2026; ne présente pas le 3,6 G$ indicatif comme un déficit de caisse.
- `tests/g017c-municipal-water-finance.test.mjs` : **48 tests réussis au rejeu JavaScript/V8 isolé**, y compris les contrôles de totaux, de dates, de catégories, de transferts internes, de scénarios constitutionnels et de maintien du score. L'exécution native GitHub Actions n'est pas attestée.

Les **données brutes CSV complètes** du MAMH pour **2024 et 2025 n'ont pas encore été téléchargées et rapprochées** dans cette phase. La bonne prochaine étape reste d'importer ces données avec le lecteur de G0.17b, contrôler les rubriques et la couverture, puis développer les simulations de protection des ménages et des services **avec audit indépendant**.

## 6. Décision G0.17c et programme à 100 %

G0.17c enrichit **substantiellement** l'évaluation des contraintes municipales avec des données publiques historiques. Elle ne démontre pas que les prélèvements Nova produiront les recettes nécessaires, et elle n'achève aucun audit indépendant des deux scénarios constitutionnels. **La grille de préparation du projet reste donc à 47/100, soit 53 points à justifier.**

**Suite G0.17d :** chercher les données de coûts des services d'eau plus récentes, importer les CSV municipaux au périmètre comptable adéquat, produire la liste des obligations réellement financées et présenter un budget local consolidé distinguant recettes externes, transferts internes et services à protéger. Aucun taux, nouvelle économie ou date de fin de l'ensemble du programme ne doit être annoncé sans les pièces requises.
