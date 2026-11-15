# NOVA-SINJ-G0-SAN-002 — Protocole de preuve, dictionnaire d'indicateurs et accès aux données

> **Addendum G0.4, 3 novembre 2026.** Les 16 valeurs d'affiliation régionales sont désormais transcrites du tableau 8.1 du PDF `Panorama des régions du Québec 2026`, et les démarches vers l'urgence du tableau 8.3. Voir `official/working/protocole-portrait-regional-sante-g0-v2.md`. Le classeur XLSX ISQ n'a **pas** été importé. Les présentes règles de dictionnaire GAP et de confidentialité restent nécessaires et inchangées.


**Projet politique :** Projet Nova  
**Version :** 1.0 du 3 novembre 2026  
**Statut :** dossier méthodologique de travail; non adopté, non validé par les institutions citées, sans demande de données expédiée et sans autorisation de traitement de renseignements personnels.  
**Porte :** G0 santé de première ligne **non franchie**.

## 1. Le problème à résoudre sans confondre les résultats
L'affiliation à une équipe n'est pas équivalente à une consultation obtenue. Le premier rappel du Guichet d'accès à la première ligne (GAP) n'est pas une rencontre clinique. L'octroi d'un rendez-vous n'est pas une consultation effectuée. Une donnée de recours aux urgences ne suffit pas à prouver la cause d'une visite. Une rémunération versée par la RAMQ n'est pas le coût complet de production ni un coût social.

Ces distinctions constituent des **contraintes de définition obligatoires** pour toute future comparaison entre gestion publique améliorée, opérateurs privés agréés, coopératives et organismes sans but lucratif.

## 2. Sources gouvernementales vérifiées au 3 novembre 2026

| Source | Ce qui a été confirmé | Ce qui n'a PAS été extrait ni démontré |
| --- | --- | --- |
| **ISQ, EQUSSSS 2025**, faits saillants du 2 novembre 2026 | 82 % des adultes étudiés affiliés, 18 % non affiliés; recours aux urgences d'environ 10 % parmi les affiliés et 19 % parmi les non-affiliés. Enquête du 6 janvier au 11 mai 2025; 9 391 répondants; exclusion des populations institutionnalisées, du Nunavik et des Terres-Cries-de-la-Baie-James | Effets causaux; coûts d'épisodes; coûts par mode d'exploitation |
| **ISQ, page des tableaux EQUSSSS 2025** | Un fichier XLSX pour l'ensemble du Québec, un XLSX ventilé selon les régions sociosanitaires et des documents méthodologiques sont référencés et datés du 2 novembre 2026 | Les valeurs régionales et marges d'erreur **n'ont pas été lues, analysées ni publiées dans ce dossier**. Ne pas inventer de classement des régions |
| **Gouvernement du Québec / Santé Québec, documentation de performance** | Définitions officielles : attitration, demandes GAP, demandes annulées, délai du premier rappel, rappel en 36 h, complétion GAP, orientations. Limites d'interprétation et fréquences de mise à jour | Les valeurs du tableau de bord à une date donnée **n'ont pas été reprises comme une série vérifiée** |
| **RAMQ, données et statistiques** | Données officielles et statistiques fréquemment demandées; la RAMQ propose un chemin de demande pour des données complémentaires. Des statistiques GAMF sont signalées pour 2021–2026 | Aucun tableau nouveau de coûts unitaires, de risques cliniques ou de répartition par propriétaire n'a été obtenu |
| **Québec, accès à l'information** | Les demandes de documents administratifs se font verbalement ou par écrit; identifier l'objet et les coordonnées du demandeur. Le délai général est de 20 jours, possiblement prolongé de 10 jours; le droit de révision est encadré | Une demande ne garantit pas la création d'un tableau inédit ni l'accès à des informations protégées |
| **Québec, LRSSS / recherche** | La collecte et la communication de renseignements de santé sont réglementées. L'accès à des données de recherche nécessite une justification spécifique et des autorisations; le consentement seul ne donne pas un accès libre aux banques sensibles | Aucun accès individuel, pseudonymisé ou autre à des dossiers de patients n'est demandé ni autorisé ici |

**URLs :**
- ISQ, enquête et faits saillants : https://statistique.quebec.ca/fr/document/utilisation-services-sante-et-services-sociaux/publication/utilisation-services-sante-sociaux-premiere-ligne-2025
- ISQ, XLSX provinciaux et régionaux et méthodologie : https://statistique.quebec.ca/fr/document/utilisation-services-sante-et-services-sociaux
- Indicateurs gouvernementaux de performance : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/performance-reseau-sante-services-sociaux
- RAMQ, statistiques et données sur demande : https://www.ramq.gouv.qc.ca/fr/donnees-statistiques
- RAMQ, statistiques fréquemment demandées : https://www.ramq.gouv.qc.ca/fr/donnees-statistiques/statistiques-frequemment-demandees
- Procédure gouvernementale d'accès aux documents : https://www.quebec.ca/acces-information
- Limitation de l'accès aux renseignements de santé : https://www.quebec.ca/sante/vos-informations-de-sante/loi-renseignements-sante-services-sociaux
- Accès de chercheurs aux renseignements de santé : https://www.quebec.ca/sante/professionnels/encadrement-recherche-participants-humains/acces-renseignements-sante-services-sociaux-chercheurs-recherche
- Recherche à partir des dossiers de patients : https://www.quebec.ca/sante/professionnels/encadrement-recherche-participants-humains/encadrement-recherche-dossiers-patients

## 3. Règles de calcul et de comparaison à appliquer au catalogue
Le catalogue machine lisible se trouve dans `data/dictionnaire-indicateurs-g0-sante.json`. Il distingue les indicateurs **avec valeurs vérifiées**, les indicateurs dont **la définition est vérifiée mais non la valeur à date**, et les indicateurs **à concevoir**.

### 3.1 Affiliation/attitration
- Donnée EQUSSSS : enquête autodéclarée auprès des adultes visés. Unité : **personne répondante et estimation pondérée**.
- Donnée FIPA/GRL : fichier administratif d'attitration de personnes assurées. Unité : **personne inscrite/attitrée** selon les règles officielles.
- **Interdit** : une soustraction entre deux pourcentages provenant de méthodes et de populations distinctes pour annoncer une hausse ou baisse.

### 3.2 GAP : demander, rappeler, orienter, compléter, consulter
- Demande reçue : formulaire numérique, pas nécessairement personne unique.
- Annulation sans traitement : inclut notamment doublons, demande annulée ou usager non joint après des tentatives documentées; ne signifie pas systématiquement refus de service.
- Premier rappel : délai jusqu'à une première tentative de traitement par un agent ou une infirmière, calculé en temps calendaire; ce n'est pas l'attente jusqu'à un soin médical.
- Rappel en 36 h : indicateur sur les demandes **numériques**; les autres voies d'accès ne sont pas nécessairement comptées.
- Complétion : traitement du dossier pouvant inclure octroi d'un rendez-vous, pas preuve que le rendez-vous a eu lieu.
- Orientations : une demande peut produire plus d'une orientation; les totaux d'orientations ne doivent pas être présentés comme des nombres de personnes.
- Consultation effectuée : indicateur G0-SAN-ATT-01 **non disponible** dans ce dossier; il faudra relier un événement de demande à la réalisation du service sous les restrictions applicables.

### 3.3 Qualité, personnel et financement
- **Sécurité** : complications et réorientations avec groupe de risque défini; ne pas récompenser l'exclusion des cas complexes.
- **Effectifs** : variation nette d'ETP sur le territoire, y compris départs du réseau public vers un nouvel opérateur.
- **Coût du payeur** : tarifs et dépenses publiques imputables au même épisode, administration, aval et coûts de réserve.
- **Coût réel de ressources** : ressources de production, capital, temps des proches et frais complémentaires **non déjà comptés**.
- **Dimension territoriale** : ne jamais assimiler les résultats du Québec urbain aux régions absentes de l'enquête ou aux territoires peu denses sans preuves spécifiques.

## 4. Dictionnaire de métadonnées pour chaque extraction
Une valeur n'est acceptable en vue d'un arbitrage que si la fiche comprend :
1. `source_document` : organisme, titre, lien durable, version, édition.
2. `date_extraction`, `periode_reference` et `date_publication`.
3. `definition` : quoi, unité, numérateur, dénominateur, événements exclus.
4. `population` et `territoire` : inclusions, exclusions, couverture, effectifs.
5. `mesure` et `methode` : estimation pondérée, comptage, moyenne/médiane/p90; révisions de codage.
6. `incertitude` : marge d'erreur, taille de l'échantillon, suppression statistique, biais.
7. `droit_diffusion` : permission de citer ou reproduire les données et des tableaux.
8. `concordance` : les définitions et périodes s'alignent-elles avec les données de coût?
9. `audit` : source reproductible, contrôleur, date et résultat.
10. `statut` : valeur sourcée, valeur non disponible, indicateur candidat, à corriger.

Valeur inconnue = `null`, jamais zéro par défaut. Éviter un classement par région lorsque les intervalles d'incertitude se recouvrent ou lorsqu'il manque des territoires.

## 5. Trois voies d'accès à utiliser dans cet ordre
**Voie A — réutiliser le public déjà publié** : téléchargements ISQ, pages RAMQ et documentations Santé Québec. Identifier les licences, la qualité et la population avant redistribution.

**Voie B — demander un document administratif existant et diffusable** : formuler une demande étroite aux responsables de l'accès de l'organisme approprié; vérifier la publication proactive et les précédentes décisions. Le gouvernement du Québec indique un délai habituel de 20 jours, avec prolongation de 10 jours possible selon les règles applicables; sans garantie de réponse favorable.

**Voie C — demande de tabulation ou de données protégées** : une demande d'accès aux documents n'oblige pas nécessairement à fabriquer des statistiques inédites. Une extraction supplémentaire peut nécessiter un autre mécanisme RAMQ/organisme, une collaboration méthodologique, un comité d'éthique ou un examen juridique. **Ne pas demander de renseignements nominatifs, d'identifiants cliniques ou de dossiers de santé pour ce projet à ce stade.**

## 6. Sécurité, proportionnalité et gouvernance
- Ne recueillir que ce qui est nécessaire; faire valider la base légale de tout échange.
- Obtenir les statistiques **agrégées** sans petit effectif identifiable lorsque possible.
- Aucun profilage commercial des patients; aucun usage politique ciblant une personne malade ou vulnérable.
- Le droit des patients à la confidentialité et les accès/rectifications doivent être respectés.
- Les projets de recherche qui auraient besoin de renseignements individuels sont **hors périmètre** de G0 tel que publié et requièrent des autorisations distinctes.

## 7. Contrôles avant clôture G0
| Exigence | État au 3 novembre 2026 |
| --- | --- |
| Définition d'un épisode clinique partagé et assurabilité | **À établir** |
| Étude EQUSSSS 2025 et portée méthodologique | **Source publiée; premier niveau de lecture effectué** |
| Fichiers XLSX régionaux ISQ | **Référencés; contenu pas encore traité** |
| Tableau de bord Santé Québec — définitions | **Vérifiées; valeurs à date non extraites** |
| Données de coût par épisode ajusté | **Non reçues** |
| Effet des modes sur les équipes/territoires | **Non établi** |
| Comparaison de qualité clinique ajustée | **Non établie** |
| Droits et autorisations de données | **À valider pour chaque méthode** |
| G0 franchi / pilote approuvé | **NON / NON** |

## 8. Livrables techniques de cette phase
- `data/dictionnaire-indicateurs-g0-sante.json` : définition, valeur, période et limites de 15 indicateurs.
- `official/working/modeles-demandes-donnees-g0-sante-v1.md` : trois modèles de correspondance **non expédiés**, sans coordonnées inventées.
- `data/plan-acquisition-donnees-g0-sante.json` : neuf demandes M01–M09 **non transmises**.
- `tests/diagnostic-g0-sante.test.mjs` : vérifications de statut et de traçabilité.

**Les références officielles candidates du Projet Nova restent inchangées. Aucune économie financière ni solution privatisée n'est adoptée.**
