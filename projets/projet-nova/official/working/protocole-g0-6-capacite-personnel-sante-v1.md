# NOVA-SINJ-G0-SAN-008 — G0.6 : capacité de soins, effectifs et ETP nets

**Date :** 3 novembre 2026  
**Projet :** Projet Nova  
**Statut :** document de travail non adopté, non certifié indépendamment.  
**Porte :** G0 non franchie. Aucun projet pilote, contrat de prestation, transfert d'emploi ni économie approuvés.

## 1. Objectif
Établir combien de **ressources cliniques réellement disponibles en première ligne** un territoire possède et ce qui change réellement quand une activité est réorganisée, sans déplacer les coûts, le fardeau ou les travailleurs.

Il faut distinguer :
1. **Personnes ayant un lien d'emploi** (personnel en emploi);
2. **Personnes considérées présentes à une période de paie**, concept administratif avec exclusions;
3. **Heures effectivement travaillées dans des soins de première ligne**;
4. **ETP cliniques effectivement disponibles**, à construire à partir d'heures et d'un dénominateur normalisé;
5. **Professionnels rémunérés par la RAMQ**, série distincte : leur nombre n'est pas une mesure automatique des ETP ou du temps de pratique;
6. **Main-d'œuvre nette sur le territoire** après transferts entre organismes, et non gain apparent d'un seul prestataire.

## 2. Sources de preuve disponibles et limites réelles

### A — Portrait ministériel 2024–2025 : salariés et établissements
La page gouvernementale `Données sur les ressources humaines du réseau` offre un classeur **« Portrait du personnel des établissements publics et privés conventionnés du réseau de la santé et des services sociaux (2024-2025) »**, 136 Ko, avec sous-catégories, statuts d'emploi, régions et renseignements de rémunération.

Page officielle, mise à jour le 27 avril 2026 : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-humaines

Fichier repéré : https://cdn-contenu.quebec.ca/cdn-contenu/sante/documents/Systeme_et_services_de_sante/organisation-services/donnees-systeme-sante-quebecois-services/ressources-humaines/denombrement-et-remuneration-effectif-rsss-2024-2025.xlsx

**État de la collecte au 3 novembre 2026 :** source publique trouvée, mais **téléchargement direct échoué**, donc aucun fichier ni aucune feuille XLSX analysés dans cette phase. **Aucun effectif régional numérique publié dans le registre Nova**. Le lien ne suffit pas à établir une capacité médicale ou un ETP en première ligne.

### B — Définitions RH de Santé Québec : banque R22 et GESTRED
La page de méthodologie officielle précise :
- Le **personnel en emploi** est une mesure de personnes salariées et de cadres ayant un lien d'emploi, comptées selon l'emploi principal.
- Les séries R22 RH mentionnées excluent les **médecins résidents**, les **professionnels rémunérés par la RAMQ** et le **personnel de recherche**.
- Certaines données d'établissements privés conventionnés **ne sont pas intégrées**.
- Les périodes de paie sont de **14 jours** et les dates peuvent varier d'une année à l'autre.
- **Personnel présent = personnel en emploi − personnel absent**, selon la même période et les mêmes exclusions.
- L'indicateur de personne « absente » n'est pas égal à toutes les heures d'absence : une personne qui a travaillé au moins une demi-journée pendant la période peut être comptée présente. Le nombre de personnes présentes ne représente donc pas nécessairement les **heures de prestation clinique disponibles**.
- Le temps supplémentaire obligatoire est compilé manuellement par les établissements et la complétude varie; ne pas assimiler absence de déclaration à zéro.
- Un départ d'un établissement peut être une entrée dans un autre : mesurer séparément le **mouvement d'organisation** et le **mouvement net du territoire**.

Source : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/performance-reseau-sante-services-sociaux

### C — Statistiques des professionnels payés par la RAMQ
Le gouvernement renvoie à **St@tRAMQ** pour des tableaux sur les médecins omnipraticiens, spécialistes et d'autres professions, notamment ventilables selon la région sociosanitaire.

**Limite :** rémunération par la RAMQ, activité clinique totale, temps de pratique et ETP équivalent ne sont pas synonymes. La disponibilité de données ne prouve ni un temps plein ni un nombre net de nouvelles consultations. Une partie de la pratique clinique et de l'emploi salarié peut relever de périmètres différents. Aucune somme inter-fichiers sans concordance documentée.

Source d'entrée : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-humaines

### D — Banque RH R25 : confidentialité
Le répertoire ministériel décrit R25 comme une banque de caractéristiques et de rémunération des personnels pouvant contenir des renseignements personnels.

**G0.6 ne demande aucun accès individuel** à cette banque et ne permet pas de profilage de travailleurs. Utiliser d'abord des tableaux publics et agrégés, avec suppressions adaptées.

Source : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/sources-donnees-metadonnees-msss

## 3. Règles opérationnelles de dénombrement

| Mesure | Unité de base | Peut être additionnée avec | Interdiction |
| --- | --- | --- | --- |
| Personnel en emploi, R22 | **Personnes** selon emploi principal et champ R22 | Même définition, même source, même date et périmètre sans chevauchement | Ajouter des médecins payés RAMQ comme s'il s'agissait du même indicateur |
| Personnel absent, R22 | **Personnes** selon définition administrative R22 | Comparaison au personnel en emploi sur la même paie | Assimiler le chiffre aux heures entières de travail perdues |
| Personnel présent, R22 | **Personnes**; emploi − absent | Même périmètre et période seulement | Assimiler à ETP clinique réellement présent |
| Temps régulier ou supplémentaire | **Heures** | Heures de même nature, période et profession, avec doubles comptes exclus | Ajouter heures aux personnes ou aux ETP sans conversion |
| ETP clinique de première ligne | **Heures pertinentes / heures de référence** | ETP d'une profession ou groupe comparable sur même territoire, avec règles d'imputation | Déduire d'un simple nombre de professionnels payés ou de consultations facturées |
| Professionnels payés RAMQ | **Professionnels** selon définition St@tRAMQ | Même série avec exclusion des doublons | Présenter comme ETP disponibles ou salariés du R22 |
| Épisodes de soin réellement effectués | **Épisodes définis** | Même besoin clinique, même horizon et niveau de risque | Déduire mécaniquement d'un effectif brut |

## 4. Comptabilité des changements de capacité

Quand un opérateur privé, coopératif, OBNL ou un service public réorganisé accroît son personnel, il faut **examiner simultanément ce qui se passe ailleurs**.

**Identité de cohérence, à périmètre complet identique :**

`ETP nets après − ETP nets avant = (ETP publics après + ETP autres après) − (ETP publics avant + ETP autres avant)`.

Cet outil n'est valable que si les quatre chiffres mesurent des **ETP cliniques présents en première ligne, sans chevauchement, pour les mêmes professions, le même territoire et des périodes comparables**.

### Exemple purement synthétique
- Avant : public **80 ETP**, autres opérateurs **20 ETP**, total **100**.
- Après : public **70 ETP**, autres opérateurs **30 ETP**, total **100**.
- Variation nette **0 ETP** : un déplacement de dix ETP ne constitue pas dix nouveaux ETP dans la région.

Ce calcul est une **identité comptable illustrative**, non une observation québécoise et non une évaluation de la production réelle de soins.

Même si le total augmente de cinq ETP, **cela ne prouve pas cinq fois un volume d'actes**, ni l'efficacité, la continuité, la qualité ou la baisse des dépenses. Il faut des données de besoins servis, de compétences, de productivité sans intensification abusive et de coûts complets.

Le module `assets/g06-capacite-rh-core.mjs` refuse les nombres négatifs/non finis, les unités non comparables, les périmètres distincts et les risques de double compte déclarés non maîtrisés. Le calcul ne délivre **aucune autorisation de pilote ni économie**.

## 5. Contrat minimal de données régionales

**Grain final visé :** `RSS × dates de début et fin × profession × type de travail × secteur de soins × statut de présence × source`.

Pour chaque valeur :
- `rss_id` : RSS 01–18, pas région administrative ni RTS sans table de concordance;
- `period_start`, `period_end` et fréquence de paie ou exercice;
- `population`, `unit`, `profession`, `employment_type`, `clinical_scope`;
- `source_url`, `version`, `sha256` de fichier;
- `numerateur`, `denominateur`, `heures_standard_etp` si conversion;
- `inclusion/exclusion`, `coverage`, `risk_overlap`, `methodologie`;
- `date_verification`, `auditeur_independant`, `limitations`;
- aucun identifiant de personne et aucune donnée de paie individuelle.

Toute valeur non obtenue doit rester **`null`**, jamais zéro; **2024–2025 ne représente pas 2026–2027**.

Le registre `data/registre-rh-regional-g0-6-sante.json` couvre les **18 RSS**, **11 mesures candidates** et **quatre familles de sources**, mais conserve actuellement les valeurs numériques RH et coûts régionaux **nulles**. Les taux d'affiliation régionaux 2025 existent en référence pour les 16 RSS couvertes, mais ne sont pas des indicateurs de main-d'œuvre.

## 6. Travail à accomplir après ce protocole
1. Obtenir le classeur officiel RH 2024–2025 avec date de téléchargement, SHA-256 et licence; comprendre les lignes, regroupements, totaux et exclusions avant extraction.
2. Extraire les données agrégées pertinentes sans réidentifier quiconque. Contrôler les codes RSS, la profession, l'emploi principal et les états temps plein/partiel.
3. Documenter St@tRAMQ avec les mêmes années, les unités, les doubles comptes, les heures de pratique connues ou inconnues et les dimensions non couvertes.
4. Réunir heures cliniques pertinentes, absences et temps supplémentaire, sans confondre personnes présentes et ETP.
5. Obtenir une méthode indépendante des **ETP nets** et des mouvements avant/après, incluant les effets sur les établissements d'origine.
6. Mettre en relation les ressources avec l'accès **réellement obtenu**, la qualité, la continuité, les besoins complexes et les coûts complets, aux mêmes périodes et périmètres.
7. Faire vérifier par des juristes et les partenaires compétents les traitements de données, les contrats, les droits des personnes et les protections du personnel.
8. Évaluer l'incertitude et conserver la possibilité de ne pas lancer le pilote si les conditions ne sont pas satisfaites.

## 7. Contrôle et état de la porte G0

**Complétude RH dans le registre Nova :** aucune série régionale RH inspectée ni certifiée, aucun ETP par RSS chiffré, aucun coût unitaire. Cela mesure la documentation disponible pour le dossier Nova, **pas l'effectif réel de ces régions ni la qualité de leurs travailleurs**.

**G0 demeure NON FRANCHIE.** Aucun transfert de personnel, diminution de masse salariale, licenciement, réduction d'horaires ou changement d'accès aux soins n'a été approuvé. Le projet continue d'imposer une amélioration de la qualité sans réduire la main-d'œuvre existante ni transférer indûment les coûts vers la population.

**Nature du document :** proposition méthodologique publique, distincte des références officielles candidates du Projet Nova et de toute décision clinique ou juridique.
