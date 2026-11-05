# NOVA-SINJ-G0-SAN-016 — G0.10 : premier portrait RH régional chiffré, provenance provisoire et vérification

**Projet :** Projet Nova — capacité des services de santé  
**Date :** 4 novembre 2026  
**Statut :** résultat descriptif provisoire de source gouvernementale, **non certifié indépendamment**, hors programme normatif.  
**Décision :** G0 **NON FRANCHIE**; aucun financement, licenciement, transfert de personnel, changement de couverture ou pilote autorisé.

## 1. Résultat nouveau et ce qui a été réellement obtenu

Pour la première fois dans ce chantier RH, le contenu du classeur gouvernemental du MSSS **« Portrait du personnel des établissements publics et privés conventionnés du réseau de la santé et des services sociaux (2024-2025) »** a pu être **lu par le service de conversion Firecrawl**, qui a renvoyé une transcription Markdown des feuilles du fichier XLSX officiel avec une réponse HTTP 200 et le type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

- **Classeur officiel :** https://cdn-contenu.quebec.ca/cdn-contenu/sante/documents/Systeme_et_services_de_sante/organisation-services/donnees-systeme-sante-quebecois-services/ressources-humaines/denombrement-et-remuneration-effectif-rsss-2024-2025.xlsx
- **Catalogue public :** https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-humaines
- **Partie utilisée :** « Feuille A - 2 » — sections « Nombre de personnes au 31 mars » et « Nombre d'ETC par année financière ».
- **Production des données selon le classeur :** mars 2026, à partir des données annuelles sur les cadres et salariés du réseau.
- **Copie binaire dans le dépôt :** aucune; **SHA‑256 du classeur original : inconnu**; **références Excel absolues de chaque cellule : non vérifiées**.

La distinction est fondamentale : **une transcription par un service externe n'est pas une copie XLSX reçue et authentifiée au moyen d'une empreinte.** Les portes L1 et L2 de l'outil G0.7/G0.8 restent non attestées dans le dépôt. Cependant, il existe désormais un **ensemble de nombres descriptifs provisoires** correctement sourcés, au lieu d'un inventaire sans aucun chiffre.

## 2. Trois nombres à distinguer

| Grandeur source MSSS | Valeur | Périmètre et prudence |
| --- | ---: | --- |
| **Personnes au 31 mars 2025, total** | **344 056** | 18 RSS et ligne organisationnelle Santé Québec (« 00 ») |
| **Personnes réparties parmi les 18 RSS** | **343 252** | 18 régions sociosanitaires; ne représente pas les médecins payés RAMQ et toute la première ligne |
| **Personnes de la ligne Santé Québec « 00 »** | **804** | Ligne distincte, **pas une 19e région** |
| **ETC rémunérés 2024–2025, total publié** | **283 740** | Ensemble du personnel du périmètre; **pas les ETP cliniques présents** |
| **Somme des ETC entiers affichés pour les 18 RSS et Santé Québec** | **283 738** | **Écart de 2** par rapport au total source; ne pas corriger silencieusement |
| **Personnes au 31 mars 2024, total publié** | **336 730** | Référence historique; ne pas extrapoler un gain clinique ou causal |

Les sommes des personnes **2025** se réconcilient exactement : **343 252 + 804 = 344 056**. Les valeurs des **18 RSS** couvrent bien les RSS **17 Nunavik** et **18 Terres-Cries-de-la-Baie-James**, même si celles-ci étaient exclues de l'enquête ISQ EQUSSSS 2025, étude **différente**.

**Avertissement ETC :** l'écart de **2 ETC** peut être compatible avec des nombres entiers arrondis indépendamment, mais cette explication n'a pas été confirmée dans les cellules originales. Le total publié est conservé tel quel, ainsi que la somme recalculée et la différence. Aucun rapprochement exact des ETC ne peut être déclaré validé à ce stade.

## 3. Définitions issues de la source — conserver les nuances

### « Nombre de personnes »
La source définit le nombre de personnes dans le réseau au **31 mars**, avec au moins une heure rémunérée ou non dans les **trois mois suivant la fin de l'exercice** pour 2018–2019 et les exercices ultérieurs. Les personnes occupant plus d'un emploi au 31 mars sont comptées **une seule fois**, en priorisant le statut d'emploi (temps complet régulier, temps partiel régulier, temps partiel occasionnel), puis l'ETC selon la définition de la source.

### « Équivalent temps complet (ETC) »
Le MSSS utilise le nombre d'heures **rémunérées** sur la durée annuelle d'un poste à temps complet, en tenant compte de certaines vacances, journées fériées, autres congés rémunérés et temps supplémentaire pris en congé compensé, **à l'exclusion des heures supplémentaires payées** selon la formule du classeur.

**ETC rémunéré n'est pas un ETP de première ligne clinique disponible, ni une personne physiquement présente pendant une consultation.**

### Population couverte
Le document cible le personnel salarié et d'encadrement du réseau, y compris les établissements publics et privés conventionnés et Santé Québec en 2024–2025. Il **exclut notamment** les professionnels directement rémunérés par la RAMQ, la main-d'œuvre indépendante, des organismes communautaires, le privé non conventionné, le MSSS et ses organismes distincts et le personnel des centres de recherche.

### Géographie
Le tableau reprend les **18 RSS**, avec Mauricie et Centre-du-Québec regroupés au **04** et la région administrative du Nord-du-Québec distinguée en RSS **10**, **17**, **18**. Le « 00 — Santé Québec » est une **ligne organisationnelle**, à ne pas affecter arbitrairement à une RSS.

## 4. Vérifications réalisées et non réalisées

**Réalisation technique interne :**
- lecture de la sortie de parsing du classeur XLSX officiel;
- identification de « Feuille A - 2 » et des **18 codes RSS**;
- extraction des champs « personnes au 31 mars 2025 », « personnes au 31 mars 2024 » et « ETC 2024–2025 »;
- réconciliation **exacte du total des personnes 2025**, avec ligne 00 explicitement séparée;
- documentation **sans correction artificielle** de l'écart de 2 ETC;
- création d'un registre structuré `data/portrait-rh-msss-g0-10-2024-2025.json` contenant source, définitions, 18 observations, totaux et limites;
- contrôle automatique `assets/g10-rh-official-portrait-core.mjs` interdisant les chiffres sans périmètre ou les fausses certifications d'ETP cliniques.

**Non réalisé :**
- récupération d'un fichier original archivé avec SHA‑256;
- vérification cellule par cellule dans Excel par un second opérateur;
- revue méthodologique indépendante des chiffres publiés par le MSSS et de l'écart ETC;
- validation de présence réelle, d'heures cliniques, d'accès à la consultation, de réorientation ou de coût par épisode;
- dédoublonnage avec les professionnels rémunérés RAMQ;
- audit des changements organisationnels entre 2024 et 2025;
- exécution confirmée de toute la suite Node dans GitHub Actions.

## 5. Conditions d'utilisation de ces chiffres dans Nova
1. **Utilisation admissible :** portrait descriptif provisoire des salariés et cadres couverts par le fichier MSSS, avec période, unité et source explicitement affichées.
2. **Interdiction de conversion :** ne pas substituer ce dénombrement ou les ETC rémunérés à des ETP cliniques réellement présents dans la première ligne.
3. **Interdiction de classement d'accès :** une RSS possédant davantage de salariés bruts n'offre pas nécessairement de meilleurs soins; besoins, population et établissements diffèrent.
4. **Interdiction de fusion artificielle :** ne pas joindre aux taux d'affiliation EQUSSSS, aux professionnels RAMQ ou aux paiements hospitaliers sans périmètre réconcilié.
5. **Aucune politique automatique :** ni baisse du nombre d'emplois, ni pilotage privé, ni économies ou budgets approuvés ne découlent de ces données.

## 6. Étapes pour sortir du statut provisoire

1. Exécuter le workflow manuel `nova-g07-acquisition-rh.yml`, ou obtenir autrement le fichier original par un canal autorisé, puis conserver **SHA‑256, taille, horodatage et copie**.
2. Comparer les 18 codes, les en-têtes et les cellules de « Feuille A - 2 » à la transcription provisoire, en conservant les **coordonnées de cellules**.
3. Vérifier si l'écart de 2 ETC provient effectivement de l'arrondi des valeurs publiées, ou d'une erreur de transcription ou d'une autre règle comptable. Corriger seulement avec preuve.
4. Revoir avec les experts les notions de personnes, nombre d'emplois, ETC rémunérés et heures cliniques disponibles; vérifier la couverture des autres modes d'emploi.
5. Soumettre les chiffres et les limites à un audit indépendant avant de considérer la série **certifiée** et avant toute étude de décision.

**Décision actuelle :** G0 **NON FRANCHIE**. Les données G0.10 représentent une avancée descriptive réelle, mais non une preuve de capacité clinique ni une autorisation politique.
