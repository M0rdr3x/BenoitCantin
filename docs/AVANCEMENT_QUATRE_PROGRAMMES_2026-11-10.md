# Avancement des quatre programmes — état de référence du 8 novembre 2026

**Bilan documentaire consolidé le 10 novembre 2026, non certifié par un tiers.** Ce dossier distingue délibérément :
- la maturité d'un **programme politique**, selon audit pondéré;
- la préparation des **14 secteurs de services publics**, qui n'a pas de pourcentage global mesurable;
- les **portes d'homologation** d'une boussole et d'un sondage distincts;
- la maturité de la plateforme **SINJIRA™**, qui est un autre projet et ne contient pas Projet Nova.

Les pourcentages ne sont donc **pas additifs**, et ne représentent ni une probabilité de succès politique ni un lancement autorisé.

## Chiffres sourcés et échéances

| Programme | Indicateur | Calcul / portée | Date de fin |
|---|---:|---|---|
| **Projet Nova — Programme politique** | **47 %** | 47/100 points sur 10 dimensions; audit interne du **5 novembre 2026**, provisoire | **31 décembre 2027** : cible conditionnelle, report possible à 2028 ou au-delà |
| **Projet Nova–Sinjira — Services publics** | **Pas de pourcentage vérifiable** | 14 secteurs NV-01 à NV-14 identifiés; les données et coûts comparables ne sont pas encore validés | **Inconnue** |
| **Projet Nova — Boussole électorale** | **75 %** | 9 critères d'homologation satisfaits / 12, au 8 novembre | **Inconnue**, 3 critères restent en attente |
| **Projet Nova — Sondage citoyen** | **54,5 %** | 6 critères d'homologation satisfaits / 11, au 8 novembre; **collecte non ouverte** | **Inconnue**, 5 critères restent en attente |
| **SINJIRA™ — Plateforme complète** | **66,5 % ±10 points** | Moyenne pondérée par domaine d'un registre de maturité interne du 8 novembre; **13/13 conditions de lancement ouvertes** | **Inconnue**, aucun GO |

### Définitions indispensables

**Nova 47 %.** Score de maturité documentaire, juridique, financière et de préparation. La cible du **31 décembre 2027** appartient au [calendrier de travail conditionnel G0.18 (PR #894)](https://github.com/M0rdr3x/BenoitCantin/pull/894), non à une date de fin prouvée par l'audit. Les finances ont **3 points sur 16** : les scénarios de recettes/dépenses/dette sur dix ans (Québec dans le Canada et Québec souverain), les propositions de deux taxes et la soutenabilité sans hausse d'appauvrissement ne sont pas démontrés. Le bilan n'est pas un budget adopté ni une indépendance prévue pour 2027.

**Services publics.** Le registre `registre-donnees-services-nova-sinjira.json` est un **inventaire de besoins**. Il interdit de présenter 14 secteurs définis comme 14 politiques financées ou comme un pourcentage global calculé sans méthodes, mesures, populations, années de prix et validation externe.

**Boussole/sondage.** Les deux pourcentages sont des **portions de portes d'homologation** : 75 % n'est pas un taux d'adhésion citoyenne, et 54,5 % n'est pas un résultat de votes. La comparaison de partis dans la boussole demeure désactivée. Le sondage ne doit pas être déclaré ouvert.

**SINJIRA.** Les travaux candidats V52–V66 de liseuse ne changent **pas automatiquement** le 66,5 %. **Actualisation technique du 12 novembre 2026, distincte de l'audit du 8 novembre :** [PR unique d'intégration #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), **DRAFT, non fusionnée dans `main` et non déployée**. Elle regroupe les gestes gauche/droite, l'affichage mobile, la continuité de lecture lors des rotations et les protections V66 contre les faux balayages après défilement vertical. [CI V66 #43325893287](https://github.com/M0rdr3x/BenoitCantin/actions/runs/43325893287) : **75/75 tests Node**, **Chromium et WebKit réussis** avec un livre fictif; [V65](https://github.com/M0rdr3x/BenoitCantin/actions/runs/43325893332) couvre les événements tactiles émis par Chromium. La [PR candidate V59 sur les droits de sauvegarde](https://github.com/M0rdr3x/BenoitCantin/pull/986) a passé ses contrôles PostgreSQL **locaux et fictifs**, mais la migration serveur reste non homologuée et l'issue [#955](https://github.com/M0rdr3x/BenoitCantin/issues/955) reste ouverte. Aucune de ces avancées ne constitue une réception sur appareil physique ni un GO de production.

## Suite logique, ordonnée par dépendance

**Projet Nova :** définir la portée légale des mesures fiscales et leurs destinataires, recueillir les données primaires et établir des **budgets complets sur 10 ans**, pour chacun des deux régimes politiques, avec coûts de transition, dette, services publics et analyses de sensibilité. Faire vérifier indépendamment les totaux avant d'annoncer un taux d'impôt, des économies ou un calendrier ferme.

**Nova–Sinjira :** pour chaque NV-01 à NV-14, confirmer le jeu de données précis, l'exercice, la population, l'unité de comparaison, le coût public, les frais des usagers, l'effet sur le personnel, les mesures de transition et l'indicateur de qualité. Exiger une réception de porte G0 avant de passer à G1–G4; ne pas inventer de score global sans preuves.

**Boussole et sondage :** finaliser les examens documentaires indépendants, les vérifications d'accessibilité sur appareils, les essais de confidentialité et de sécurité avec consentement; rendre la comparaison des partis possible seulement avec les sources indépendantes dûment vérifiées. Ne pas ouvrir de vote public sur une simple réussite de tests techniques.

**SINJIRA :** revoir la PR candidate unique de liseuse V64–V66 #1000 et le chantier distinct V51/V59 de sécurité #986; évaluer la liseuse sur de vrais téléphones, puis le contrôle des comptes, les droits sur les romans intégraux, la synchronisation sur deux appareils, les lecteurs d'écran, les fichiers réels et les caches de l'application. Une validation de production exige une approbation humaine explicite.

## Sources de référence versionnées

- [Audit de complétude politique](../projets/projet-nova/data/audit-completude-programme-nova-2026-11-05.json)
- [Registre des services Nova–Sinjira](../projets/projet-nova/data/registre-donnees-services-nova-sinjira.json)
- [Réception de la boussole et du sondage](nova-sondages/reception-sondage-boussole-2026-11-08.json)
- [Maturité et 13 portes SINJIRA](sinjira/programme-readiness-2026-11-08.json)
- [Réception de la liseuse tactile V64 — PR candidate #1000](https://github.com/M0rdr3x/BenoitCantin/blob/review/sinjira-liseuse-mobile-v64-integration-main-20261111/docs/sinjira/SINJIRA_LISEUSE_V64_RECEPTION_2026-11-11.md) (non fusionnée dans `main`)
- [Protection contre les faux glissements V66](https://github.com/M0rdr3x/BenoitCantin/blob/review/sinjira-liseuse-mobile-v64-integration-main-20261111/docs/sinjira/SINJIRA_LISEUSE_V66_TRAJECTOIRE_2026-11-12.md) (testée, non publiée)

Le script `scripts/validate_quatre_programmes_baseline_20261110.mjs` et ses **8 tests Node** recalculent et vérifient directement les valeurs à partir des quatre fichiers JSON originaux. Ce document est un **instantané daté** : toute nouvelle mesure devra être enregistrée et vérifiée par les registres sources avant de remplacer cette référence.
