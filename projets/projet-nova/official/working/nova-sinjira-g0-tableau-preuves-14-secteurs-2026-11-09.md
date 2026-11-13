# Projet Nova–Sinjira — Tableau de recevabilité G0 des quatorze secteurs

**Rapport de travail du 9 novembre 2026.** Données de référence du registre du **3 novembre 2026**, examinées pour le bilan du **8 novembre 2026**. **Aucune réforme adoptée, aucun pilote ni coût certifié.** Ce document n'établit PAS un pourcentage de complétude Nova–Sinjira; le seul indicateur actuel est l'inventaire de pièces à obtenir.

## Décision de réception

- **14 dossiers sectoriels définis** dans `data/registre-donnees-services-nova-sinjira.json`. Il existe une architecture institutionnelle et des intentions de mesure.
- **0/14 dossiers** comportent toutes les séries de base requises avec qualité validée et tous les coûts comparatifs complets; **aucune porte G0 n'a été indépendamment attestée** dans ce registre.
- **5 portes G0–G4 prévues** : diagnostic, comparaison à périmètre égal, légalité/droits/financement, pilote autorisé, évaluation et éventuelle généralisation.
- La santé première ligne possède des **sources descriptives partielles** (dont 16 taux régionaux ISQ et un examen technique de documents RH MSSS) : **ce travail n'est pas nul**, mais il manque les coûts par épisode, le niveau de personnel réellement disponible, les attestations externes et une preuve de résultat.
- **Aucune date de fin défendable.** Les périodes « 90 jours après autorisation », puis « 3 à 9 mois » du plan d'exécution sont des phases proposées **qui n'ont pas démarré par une autorisation attestée** et ne constituent pas une date promise.

Ce projet d'étude de services publics est distinct de **SINJIRA™**, univers créatif et numérique, dont les pourcentages et gates de lancement ne s'appliquent pas aux institutions publiques.

## Ce que la porte G0 doit prouver

À la première collecte, conserver pour chaque secteur la **source primaire précise**, sa version et son auteur, **la date de valeur**, **la période**, **le territoire**, **la population**, **le nombre d'unités** et **l'année de prix** quand un coût est examiné. Le rapport doit documenter la méthode, l'échantillonnage, l'incertitude, les exclusions, le propriétaire de la donnée et les effets possibles sur les droits.

L'outil `assets/nova-sinjira-g0-reception-core.mjs` signale les champs absents et les incohérences flagrantes. Même si tous les champs sont renseignés, son statut est seulement **« candidat à la revue humaine »**, jamais **« G0 franchi »**. La qualité indiquée dans une case du registre ne remplace pas un mandat d'audit ni une décision signée. Aucun taux global n'est calculé à partir du nombre de champs remplis.

## Dossiers prioritaires et mesure proposée

| ID | Secteur | Unité et mesure candidate issues du registre | Pièce G0 déterminante / prudence |
| --- | --- | --- | --- |
| NV-01 | Pouvoir d'achat | Ménage et période ; revenu disponible réel après panier essentiel | Panier par taille, région et période, inflation et frais inclus |
| NV-02 | Fiscalité | Ménage ou entreprise par exercice ; charge nette et prestations | Distinguer assiette, recettes constatées et transferts fédéraux |
| NV-03 | Santé première ligne | Épisode clinique standardisé ; délai p50/p90, sécurité et coûts ajustés | Données sur cas complexes, qualité, ETP cliniques disponibles et comparateur |
| NV-04 | Logement | Logement occupé et année ; logements nets réellement habitables | Coût du terrain, qualité, logement social et effets d'éviction |
| NV-05 | Éducation | Année-élève ; apprentissage, diplôme et ressources | Besoins particuliers, transport, décrochage et accessibilité |
| NV-06 | Administration citoyenne | Dossier terminé ; temps citoyen, recours et coût complet | Accès sans Internet, guichet physique et erreurs |
| NV-07 | Travail et compétences | Personne en emploi et année ; sécurité, revenu et rétention | Aucun « gain » par simple transfert de salariés entre fournisseurs |
| NV-08 | PME et production | Entreprise et année ; productivité, survie, aides limitées | Séparer subvention, prêt, garantie et rendement net |
| NV-09 | Familles, aînés et domicile | Bénéficiaire et année ; autonomie, sécurité, délais | Comptabiliser le temps et la charge non rémunérée des proches aidants |
| NV-10 | Justice et sécurité | Dossier comparable ; délai médian/p90, recours, coût | Protéger l'indépendance judiciaire, le droit au recours et les pouvoirs régaliens |
| NV-11 | Régions et mobilité | Usager et territoire ; accès réel au service | Garantir la continuité en région éloignée et l'accès sans auto |
| NV-12 | Démocratie et contrats publics | Décision/contrat ; transparence, contestation, contrôle | Sources de décisions datées, indépendance des contrôleurs, confidentialité |
| NV-13 | Environnement et réseaux vitaux | Réseau ou actif ; état, fiabilité, coûts de cycle de vie | Ne pas comparer coût annuel de caisse au coût complet d'un actif |
| NV-14 | Langue, intégration et droits | Service ou usager admissible ; accès et respect des droits | Inclusion, non-discrimination, qualité des traductions et recours |

Les intitulés et indicateurs sont **des propositions à définir et approuver**, et non des séries de résultats déjà calculées.

## Protocole de métriques : trois critères fondamentaux par étude

**1. Résultat chez les personnes :** pourcentage de personnes admissibles recevant la prestation dans le délai cible, ou résultat concret équivalent. Définir *numérateur*, *dénominateur*, date de l'événement, exclusions, accessibilité et distribution territoriale. **Pas de cible numérique inventée** avant établissement de la distribution historique.

**2. Coût complet comparable :** coût public annuel et coût social total **séparés**, par unité homogène et selon le même niveau de qualité, en incluant les actifs annualisés, la rémunération et formation, l'administration, la cybersécurité, les contrôles, les risques, la transition, le recours et les coûts imposés aux usagers et aux proches. Décrire cinq modes possibles (public actuel, public réorganisé, privé, coopérative, OBNL) sans supposer que tous sont juridiquement admissibles dans chaque secteur. **Un prix facturé n'est pas un coût de société.**

**3. Continuité, droits et personnels :** disponibilité des services essentiels, sécurité, nombre d'effectifs réellement requis (ne pas confondre personnes, heures et ETP), qualité des emplois, accès territorial et voie de plainte. Les critères de qualité et de droits doivent empêcher de « produire une économie » par rejet des dossiers coûteux, sous-paiement ou réduction de la couverture.

## Séparation des portes

| Porte | Preuve requise et décision distincte | Condition actuelle |
| --- | --- | --- |
| **G0 — Diagnostic** | Source primaire complète, données comparables, périmètre, droits et revue documentée | **Aucune attestation indépendante enregistrée** |
| **G1 — Comparaison** | Plusieurs modes à **même unité et même qualité**, coûts publics et sociaux, marges d'erreur | **Aucune comparaison financière complète validée** |
| **G2 — Droit + financement** | Avis compétent, consultations, financement public net, personnel, clauses de continuité | **Aucune autorisation comptabilisée** |
| **G3 — Pilote** | Autorisation explicite, protocole publié, évaluateur externe, arrêt et retour arrière | **Aucun pilote autorisé par ce registre** |
| **G4 — Généralisation** | Évaluation des résultats, dommages et incertitudes, décision politique et recours | **Aucune généralisation autorisée** |

La CI de ce dépôt **ne peut jamais signer ni décerner** ces décisions. Elle se limite à détecter des déclarations contradictoires et à lister les pièces manquantes.

## Priorités d'exécution utiles, sans modifier les services

1. **NV-03 Santé** : capitaliser sur la description RH déjà documentée pour obtenir un plan de source clinique/financière et les avis de sécurité, droits des patients, travailleurs et régions; aucun pilote d'assurance ou délégation avant G2.
2. **NV-02 Fiscalité** : réutiliser l'analyse des finances de Projet Nova tout en séparant budgets provinciaux, municipalités, dépenses sociales et hypothèse souveraine; ne pas promettre d'assiettes fiscales ni de taux avant validation.
3. **NV-06 Administration citoyenne** : définir un parcours administratif mesurable à petit risque, avec accès hors ligne, protection des données, personnel et droit au recours, puis étudier un comparateur à niveau de service identique.
4. Étendre les fiches de même niveau aux 11 autres secteurs, avec consultation des groupes concernés et contraintes régionales; aucune présomption de supériorité du public ou du privé.

## Traçabilité et limites d'automatisation

**Registre d'entrée :** `data/registre-donnees-services-nova-sinjira.json`, source de référence pour l'état des dossiers.  
**Contrôleur :** `assets/nova-sinjira-g0-reception-core.mjs`.  
**Sortie inspectable :** `node projets/projet-nova/scripts/nova-sinjira-audit-g0-readonly.mjs`.  
**Tests :** `tests/nova-sinjira-g0-reception.test.mjs`.  
**Critères de réception de la CI :** 14 secteurs distincts, 17 tests de cohérence et de résistance aux faux changements de statut, aucun score de complétude, aucune acceptation ou dépense nouvelle.

**Conclusion :** ce travail rend la progression future *mesurable*, mais n'attribue **aucun pourcentage nouveau** à Nova–Sinjira. Il ne modifie ni la Constitution candidate, ni les lois, ni la propriété des services, ni le personnel ni les finances publiques.
