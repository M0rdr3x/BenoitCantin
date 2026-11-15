# Nova–Sinjira — Passage du registre sectoriel à des preuves vérifiables

**12 novembre 2026 — contrôle documentaire, sans homologation ni budget adopté.**

## Ce que montre le registre du 3 novembre

Source contrôlée : `projets/projet-nova/data/registre-donnees-services-nova-sinjira.json` (`nova-sinjira-registre-donnees-service/v1`).

| Élément | Résultat constaté | Portée |
|---|---:|---|
| Secteurs NV-01 à NV-14 identifiés | **14** | Inventaire, non des services livrés |
| Secteurs avec jeu de données précis identifié dans le champ de preuve | **0** | Les noms d'institutions ou URLs de départ ne prouvent pas la disponibilité des séries requises |
| Secteurs dont la qualité des données est vérifiée | **0** | Indicateur binaire interne, pas audit externe |
| Secteurs avec chiffrage validé | **0** | Des coûts manquants ne sont pas des coûts nuls |
| Secteurs avec affectation du personnel validée | **0** | Aucun gain d'effectifs/temps ne peut être présumé |
| Secteurs avec toutes les entrées documentaires et validations requises | **0** | Ne correspond pas à « 0 % du programme » |
| **Taux de complétude globale des services** | **Non calculable** | Les poids, périmètres, bases de coût et déploiements ne sont pas comparables |
| **Date de livraison totale** | **Inconnue** | Ni jalons validés ni chemin critique chiffré |

Cette situation de preuve ne signifie pas que les services n'existent pas, que les réformes n'ont pas commencé ou qu'aucun chiffre externe n'existe; elle indique uniquement ce que **le registre actuel** ne démontre pas.

## Automatisation introduite

- `scripts/validate_nova_sinjira_sector_evidence_20261112.mjs` analyse les 14 identifiants NV-01..NV-14, les sources précises, périodes, territoires, populations, unités, années de prix et les cinq modes de coûts.
- Un **champ absent** est signalé comme preuve manquante; il ne devient **jamais zéro dollar**.
- Cocher `chiffrage_valide` sans source, coût complet ou contrôle qualité est une **erreur de cohérence** bloquante en CI, plutôt qu'une « avancée » acceptée.
- L'automatisation renvoie les **décomptes de preuves** et la liste des champs manquants, sans formule de « pourcentage global » et sans prétendre certifier des mesures publiques.
- Les huit tests Node protègent les identifiants, les doubles comptes, la distinction entre URLs candidates et preuve réelle, la validation du personnel et l'absence de faux GO.

## Processus de réalisation sectoriel (sans inventer les données)

1. Choisir pour chaque secteur une unité de comparaison, une population, une période et un territoire explicitement déclarés.
2. Identifier le **jeu de données précis**, la version, le producteur, la date de valeur et les conditions d'utilisation, puis valider sa comparabilité.
3. Documenter les coûts publics complets, les frais aux usagers et les coûts de transition; séparer le statut actuel, public réorganisé, privé, coopérative et OBNL sans présumer que tous les modes conviennent à tous les secteurs.
4. Faire contrôler la continuité territoriale, l'accès des personnes vulnérables, les droits, la main-d'œuvre présente et les risques de transfert de coûts.
5. Construire des scénarios financiers **Québec dans le Canada** et **Québec souverain** distincts, avec leurs compétences, coûts d'État et transferts respectifs.
6. Exiger la validation externe, puis seulement discuter d'un pilote limité et de ses garde-fous.

Le registre contient notamment neuf catégories de coût complet requises : `paiementPublic`, `administrationPublique`, `coutAvalPublic`, `ressourcesReelles`, `capitalAnnualise`, `fraisUsagers`, `tempsProches`, `transitionAnnuelle` et `reserveAnnuelle`. Elles ne sont pas remplacées par cinq simples valeurs forfaitaires : le validateur les traite comme **conditions méthodologiques de preuve**, non comme valeurs fabriquées.

## Décision et lien avec le programme politique

**Décision actuelle : NON HOMOLOGUÉ.** Aucun pourcentage total ni date n'est défendable à partir de ces données. Pour Projet Nova, la dimension « finances » obtient **3/16** dans l'audit de référence et reste un chantier préalable au financement d'un programme gouvernemental sur dix ans.

Les autres scores du bilan audité du 8 novembre ne sont pas modifiés par cet outil : **Nova 47 %**, **boussole 75 %**, **sondage 54,5 %**, **SINJIRA 66,5 % ±10 points**. Voir [bilan consolidé sur `main`](https://github.com/M0rdr3x/BenoitCantin/blob/main/docs/AVANCEMENT_QUATRE_PROGRAMMES_2026-11-10.md).

La réception automatisée vise **l'intégrité du registre** et non l'adoption politique, le lancement de services, l'approbation d'un budget ou la certification indépendante.