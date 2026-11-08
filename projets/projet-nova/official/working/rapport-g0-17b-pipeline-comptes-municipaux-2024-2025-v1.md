# Projet Nova–Sinjira — G0.17b : préparer un import reproductible des comptes municipaux réels

**8 novembre 2026 · Dossier de travail · Score de complétude interne : 47/100, soit 53 points à valider.**
**État : infrastructure de contrôle des données produite et testée. Les fichiers officiels 2024–2025 ne sont pas encore importés; aucun nouvel agrégat provincial ou municipal n'est certifié.**

## 1. Objectif

Le Projet Nova–Sinjira souhaite garantir les services municipaux et scolaires tout en étudiant un système de deux prélèvements. Pour le faire de façon rigoureuse, il faut connaître les dépenses réelles par mission et leur financement, en distinguant les transferts entre administrations et les revenus véritablement extérieurs au périmètre consolidé.

Les travaux G0.16w–G0.16z ont déjà établi un cadre fiscal et une liste de conditions d'arrêt. G0.17a a montré qu'un PDF ministériel pouvait renvoyer une **édition 2024 en rendu visuel** et une **édition 2025 en extraction textuelle**; les deux séries n'ont donc pas été comparées. G0.17b refuse de régler cette anomalie par un chiffre supposé. Il prépare plutôt l'**import et le contrôle à partir des données brutes**, année par année.

## 2. Fichiers publics et statut de l'accès

Source du MAMH : [Données Québec — Rapport financier des organismes municipaux et autres documents connexes](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents), catalogue modifié le **7 novembre 2026**, licence **CC-BY 4.0**.

Les ressources identifiées couvrent :

| Exercice | Fichier de données | Autres ressources obligatoires | Statut dans G0.17b |
| --- | --- | --- | --- |
| **2024** | **Données réelles 2024 — Simple occurrence, CSV** | Description des postes 2024, formulaire codifié 2024, organismes absents 2024 | Fichier identifié; **non téléchargé** |
| **2025** | **Données réelles 2025 — Simple occurrence, CSV** | Description des postes 2025, formulaire codifié 2025, organismes absents 2025 | Fichier identifié; téléchargement direct **échoué** |

Le [lien de ressource 2025 vérifié](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents/resource/24af5b06-089a-44a6-9adf-eddcb9a266a4) désigne un CSV diffusé par **mamh.gouv.qc.ca**, avec un identifiant de ressource stable **24af5b06-089a-44a6-9adf-eddcb9a266a4**, mais son URL peut renvoyer un fichier mis à jour. La [description des postes 2025](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents/resource/9648e3aa-2ada-4c72-bcb2-340d4b58eb51) est une autre ressource, à récupérer séparément.

Dans cet environnement, une tentative de téléchargement du CSV 2025 a échoué pour **résolution DNS**; l'ouverture du fichier via le navigateur de recherche échoue pour **type binaire non pris en charge**. Le [guide MAMH de mai 2025](https://www.donneesquebec.ca/recherche/dataset/20673c5c-f672-4387-ae9d-378ac6fa8be0/resource/3212100b-f281-439b-9c65-511b568e0e27/download/gui_donneesquebec2025_vf.pdf) a été étudié sous forme de texte, mais sa capture d'image PDF a échoué. Ces limites sont inscrites dans le registre et ne sont pas contournées par la fabrication de données.

**Conséquence : les vrais chiffres agrégés 2024 et 2025 restent à calculer.** La disponibilité d'une page de catalogue ne remplace pas la lecture des octets CSV.

## 3. Méthode d'interprétation des comptes

Le guide MAMH précise que les fichiers « Simple occurrence » comportent une ligne par organisme et des **colonnes associées à des codes de postes comptables**. Ces codes doivent être rapprochés du **formulaire codifié de l'exercice choisi** et de la **description des postes**. On ne peut donc pas attribuer un sens arbitraire à un champ numérique.

Avant une agrégation municipale :

1. **Figer les fichiers originaux** : conserver leur nom, leur URL de ressource, la date de récupération et une empreinte **SHA-256**. Une mise à jour du MAMH peut changer les résultats sans changer le titre de la ressource.
2. **Identifier les organismes** : les municipalités locales doivent rester distinctes des MRC, régies, communautés métropolitaines, organismes de transport, agglomérations et données ventilées. Les codes géographiques doivent rester des chaînes pour préserver les zéros initiaux.
3. **Sélectionner les bons comptes** : uniquement les postes dont le code et la description sont validés **pour chaque exercice**. Il faut distinguer le **réel**, le **budget**, les comptes **intégraux**, et les annexes d'agglomération.
4. **Inclure les listes d'absence** : une municipalité sans rapport dans le fichier n'a pas nécessairement zéro revenu ou zéro dépense. La population couverte doit être mesurée.
5. **Vérifier les doublons et les décimales** : un identifiant répété peut gonfler un total; les valeurs doivent être converties sans arrondi caché, en cents exacts, avec rejet des caractères ambigus.
6. **Comparer seulement à périmètre égal** : même organisme, mêmes rubriques et définitions, mêmes types de comptabilisation et périodes. Une différence de codes doit recevoir une décision de concordance explicite.
7. **Réconcilier les transferts internes** : les transferts gouvernement provincial → municipalité doivent être identifiés sur les deux côtés et annulés une seule fois pour le calcul consolidé. L'annulation comptable n'élimine ni le besoin de financement ni la dépense effective du service.
8. **Séparer les exercices civils des exercices provinciaux** : le rapport municipal est établi sur l'année civile; les comptes provinciaux utilisent un exercice financier différent. La consolidation demande un tableau de passage, non une addition directe.

## 4. Logiciel produit et garanties

**Moteur :** `assets/g017b-mamh-csv-import-core.mjs`.

Il offre :
- un lecteur CSV avec séparateurs, guillemets, virgules internes, fins de ligne Windows et caractères accentués;
- un parseur de montants en **cents canadiens exacts**, qui conserve `null` pour une valeur absente et refuse les formats numériques ambigus;
- un lecteur de postes muni d'un **filtre explicite de type d'organisme**, d'une vérification des codes, des définitions, du type « réel », du périmètre « intégral » et de la liste des organismes absents;
- une comparaison **2024–2025** limité aux communes effectivement présentes les deux années, avec la liste des organismes non appariés et interdiction de déclarer une agrégation provinciale lorsque la couverture, la provenance et les descriptions ne sont pas vérifiées.

**Commande locale :** `scripts/g017b-mamh-ingest.mjs`, qui lit des fichiers locaux, contrôle les descriptions de postes, calcule les SHA-256 d'origine, exige un mappage explicite et produit un **rapport JSON de diagnostic**. Elle ne fait **aucune collecte en ligne** ni aucune soumission administrative.

**Modèle de configuration :** `data/g017b-mamh-mapping-template.json`. Tous les noms de colonnes qui restent à relever dans les vrais fichiers sont marqués `A_VALIDER`, et la liste des postes reste volontairement vide : le code ne présume pas l'identité des champs ou des assiettes.

**Registre :** `data/g017b-mamh-municipal-ingestion-contract-2024-2025.json`, indiquant le catalogue, les pièces nécessaires, les tentatives d'accès, les limites connues et les éléments non certifiés.

### Exécution future, uniquement une fois les fichiers récupérés

À la racine `projets/projet-nova`, avec Node.js, après configuration des colonnes effectivement trouvées dans les CSV :

```bash
node scripts/g017b-mamh-ingest.mjs \
  --year2024 /chemin/mamh-reel-2024.csv \
  --year2025 /chemin/mamh-reel-2025.csv \
  --desc2024 /chemin/description-2024.csv \
  --desc2025 /chemin/description-2025.csv \
  --absent2024 /chemin/organismes-absents-2024.csv \
  --absent2025 /chemin/organismes-absents-2025.csv \
  --mapping data/g017b-mamh-mapping-template.json \
  --retrievedAt 2026-11-08 \
  --output /chemin/rapport-import-mamh.json
```

**Ce modèle de commande ne réussira pas sans remplir la correspondance des vrais en-têtes, des codes comptables et des descriptions.** Il n'est pas une preuve que les données ont déjà été importées. Le rapport généré ne constitue pas un audit indépendant et ne peut, seul, approuver une nouvelle politique fiscale.

## 5. Tests et limite financière

Les **52 tests structurels** disponibles dans `tests/g017b-mamh-csv-import.test.mjs` ont réussi en rejeu **JavaScript/V8 isolé** sur des **exemples fictifs**. Ils couvrent notamment les dates, valeurs absentes, doublons, colonnes incohérentes, changements de définitions, types d'organismes, sources non identifiées et interdiction de calculer des totaux prétendument représentatifs.

L'exécution **native Node/GitHub Actions**, les jeux de données complets et leur revue statistique restent à confirmer.

**À ne surtout pas conclure :** les recettes municipales de 2024 et 2025 n'ont pas encore été sommées à partir des CSV originaux; aucun poste précis d'eau, routes, sécurité, éducation, santé ou fiscalité locale n'a été nouvellement certifié. Aucune simulation de taux des deux prélèvements Nova, de coût de souveraineté, de baisse d'impôt ou de gain de pouvoir d'achat ne peut être justifiée par cette phase.

## 6. Feuille de route utile pour G0.17c

Dès que les fichiers bruts et les descriptions correspondantes sont disponibles :
- exécuter la commande avec la correspondance des comptes;
- vérifier la couverture des municipalités locales et les organismes absents;
- rapprocher les totaux d'une sélection de municipalités avec leurs rapports financiers PDF audités;
- isoler les dépenses eau, voirie, sécurité, administration et service de la dette suivant les vrais codes;
- produire les comptes 2024–2025 à périmètre constant et réconcilier les transferts provinciaux;
- proposer une projection **à hypothèses affichées**, distincte pour Québec au Canada et Québec souverain;
- faire vérifier le tout par comptables, fiscalistes, juristes et spécialistes municipaux indépendants.

**Décision G0.17b : base technique créée et testée, mais analyse de fichiers officiels non réalisée en raison de l'accès aux CSV. Le score Nova–Sinjira demeure 47/100 (53 points à obtenir).**
