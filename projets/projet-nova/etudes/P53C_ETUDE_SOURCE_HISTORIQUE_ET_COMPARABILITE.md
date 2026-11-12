# Projet Nova — P53C : acquisition du CSV original ARC 2024 et séparation des périmètres

**21 octobre 2026 | Preuve documentaire historique, non une adoption fiscale ou une projection 2026-2027.**

## 1. Fichier réellement acquis

Le **CSV original de l'Agence du revenu du Canada**, tableau 3 de l'édition 2026 pour l'année d'imposition 2024, a été reçu en conservant ses octets *windows-1252*. Le fichier est archivé dans cette PR :

- `projets/projet-nova/etudes/sources/P53C_ARC_TBL03_2024_FR_ORIGINAL.csv`
- URL de publication : https://www.canada.ca/content/dam/cra-arc/prog-policy/stats/itstb-sipti/2024/tbl03_fr.csv
- Catalogue du gouvernement ouvert : https://open.canada.ca/data/fr/dataset/66e95b48-3ac3-414f-ae54-2c4e21105dda
- Version de publication : **édition 2026, données de 2024**, traitement des déclarations jusqu'au **30 novembre 2025**; mise à disposition du catalogue le **25 février 2026**.
- Empreinte du **CSV original** (SHA-256) : `a1df2cf1600809f3e2274ad8f6348263080437cfaeb5ed7e86efb24d628cacf1`.
- Taille : **1 059 octets**, encodage `windows-1252`. Stockage comme blob Git binaire pour **éviter toute réécriture UTF-8** qui changerait l'empreinte.
- Licence annoncée dans le catalogue : **Licence du gouvernement ouvert – Canada**. Attribution à l'Agence du revenu du Canada; ne pas sous-entendre que l'ARC soutient le Projet Nova.

La ligne du Québec dans le CSV a été **recoupée visuellement dans le tableau PDF officiel**, page 1 : https://www.canada.ca/content/dam/cra-arc/prog-policy/stats/itstb-sipti/2024/tbl03_fr.pdf. Le PDF est consultable à sa source mais ses octets n'ont pas été archivés ou authentifiés ici. Ce recoupement n'est **pas un audit comptable externe**.

## 2. Observation chiffrée réelle, année 2024 seulement

| Tranche de revenu imposable fédéral | Impôt fédéral net, **milliers de $** |
|---|---:|
| 55 867 $ ou moins | 5 564 856 |
| 55 867 $ à 111 733 $ | 16 863 643 |
| 111 733 $ à 173 205 $ | 7 303 699 |
| 173 205 $ à 246 752 $ | 3 310 900 |
| 246 752 $ et plus | 10 506 796 |
| **Total officiel Québec** | **43 549 895** |

La somme des cinq tranches est **43 549 894 milliers de dollars**, soit une différence de **1 000 $** avec le total officiel, imputable aux arrondis que l'ARC signale pour son tableau. Converti correctement, le **total historique publié** est **43 549,895 M$** (soit **43,549895 G$**).

Il s'agit de l'**impôt fédéral net des déclarations de particuliers selon la province d'imposition**; pas des rentrées de trésorerie fédérales collectées au Québec en 2026‑2027, pas de la TPS, des sociétés, des douanes, des accises ou des transferts fédéraux. Les assiettes, frontières statistiques, traitements ultérieurs et remboursements peuvent différer.

L'inventaire P53A de **166 492 M$** de recettes provinciales 2026‑2027 reste distinct : **aucune somme interannuelle n'est affichée comme total consolidé**. La fiche E01 contient une observation historique utilisable *pour recherche*, pas une recette P53A 2026-2027 chiffrée. **F02 reste non validée.**

## 3. Municipalités : acquis documentaire limité, données non acquises

Le tableau Statistique Canada **10-10-0020-01** (finances des municipalités et administrations publiques locales; annuel, M$; série jusqu'à 2024) est identifié :

- Tableau : https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1010002001
- Source ZIP officielle prévue : https://www150.statcan.gc.ca/n1/tbl/csv/10100020-fra.zip
- Métadonnées de licence libre : https://open.canada.ca/data/en/dataset/b28ce95f-a075-4ea9-89b9-ca955f94689d

Au moment de l'acquisition, le téléchargement a retourné une **réponse HTML d'indisponibilité** à la place du ZIP. Il serait incorrect d'attribuer à cette page un SHA-256 du jeu de données, de prétendre avoir lu le tableau 2024 Québec ou d'inventer des recettes. **E04 et E05 demeurent sans montant**, en attente d'une vraie copie ZIP vérifiable et d'une extraction contrôlée des champs `REF_DATE`, `GEO`, classifications des recettes, unités, statuts et suppressions. Distinguer stocks et flux; les données nationales, la propriété scolaire et les transferts ne se combinent pas sans harmonisation.

## 4. Prochaines décisions utiles

1. Réessayer le ZIP StatCan depuis un réseau fonctionnel ou son API, enregistrer la version binaire et son SHA-256; relever les lignes Québec 2024 documentées.
2. Valider l'année, l'unité et le statut statistique des recouvrements, puis enregistrer les sous-catégories municipales **sans** inventer les montants 2026-2027.
3. Ne rapprocher les administrations qu'après une **table de passage commune** qui traite les transferts et la différence entre prévisions provinciales 2026‑2027, statistiques d'impôt 2024 et finances municipales 2024.
4. Faire examiner indépendamment les preuves de F02/F04, les recettes, les coûts des services et les droits sociaux.

Le contrôle local `scripts/valider_donnees_sources_nova_p53c.py` doit vérifier le SHA-256 **des vrais octets CSV**, la ligne Québec, les six valeurs, la différence d'arrondi, le lien avec les neuf lacunes P53A et le maintien de l'absence de consolidation.

```bash
python scripts/valider_donnees_sources_nova_p53c.py --rapport p53c_bilan.json --export-csv p53c_quebec_2024.csv
python scripts/valider_donnees_sources_nova_p53c.py --exiger-consolidation
```

Code 0 = preuves historiques techniquement recoupées avec **NO_GO_AUTOMATIQUE**. Code 2 = source incohérente ou contrefaite. Code 3 = refus de consolider des sources d'années/périmètres différents sans certification humaine. Aucun montant Nova, taux ou avis externe n'est adopté. La PR #673 reste en brouillon et `main` inchangée.
