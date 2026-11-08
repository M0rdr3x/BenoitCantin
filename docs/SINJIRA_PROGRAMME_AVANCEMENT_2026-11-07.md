# SINJIRA™ — état du programme complet et critères de sortie

**Date de référence : 7 novembre 2026.** **Périmètre : SINJIRA** (pas Projet Nova, qui est un projet indépendant).
**Évaluation indicative : 66,5 %, soit environ 67 % (incertitude ±10 points).**

> Le pourcentage est une **estimation de maturité produit**, pas une mesure automatisée de tâches achevées ni une certification de sécurité. Il ne constitue pas une promesse de mise en production, une mesure d'achèvement du roman ou un engagement commercial.
> La définition du « programme complet » et la validation finale des critères appartiennent au responsable du projet.

## Méthode reproductible

Les poids totalisent 100. Le score est la somme de `poids × maturité / 100`. Chaque maturité est une appréciation prudente des fonctions observables, des tests disponibles, de leur état réellement déployé et des validations opérationnelles ou humaines restant à effectuer. Une page visible ou une table SQL n'implique **pas** à elle seule une fonctionnalité opérationnelle.

| Domaine | Poids | Maturité estimée | Contribution |
|---|---:|---:|---:|
| Site public, accès et navigation | 10 % | 95 % | 9,5 |
| Comptes, identité, confidentialité et sécurité | 15 % | 75 % | 11,25 |
| Romans, bibliothèque et liseuse | 15 % | 90 % | 13,5 |
| Registre des Consciences et personnages | 10 % | 75 % | 7,5 |
| Jeux, dont Fracture et Résistance | 15 % | 55 % | 8,25 |
| Communauté, messages et modération | 10 % | 60 % | 6 |
| Monde parallèle et Codex | 10 % | 50 % | 5 |
| Commerce, précommandes, livraisons | 5 % | 25 % | 1,25 |
| Mon IA et services avancés | 5 % | 20 % | 1 |
| Tests, exploitation, lancement et conformité | 5 % | 65 % | 3,25 |
| **TOTAL** | **100 %** | | **66,5 / 100** |

Cette grille doit être revue à chaque jalon significatif; **ne pas modifier les poids ou scores uniquement pour afficher une progression artificielle**. Les métriques de conformité, sécurité et production doivent faire l'objet d'une évaluation indépendante.

## Constatations traçables

1. **Portail** — page SINJIRA et accès publics structurés autour des romans, jeux, Registre, Communauté et Monde parallèle : <https://www.benoitcantin.com/projets/sinjira/>. Publication GitHub Pages depuis `main` : [README](../README.md).
2. **Livres et lecture** — démo publique de **82 pages** et édition privée de **520 pages**, liseuse Web, styles, vocalisation et progression locale. V32 (PR [#816](https://github.com/M0rdr3x/BenoitCantin/pull/816)) a passé 69 workflows CI et a été fusionnée. **La synchronisation intrapage entre appareils n'est pas encore activée** : le champ `scroll_ratio` manque toujours en base de production au contrôle du 7 novembre. Le code doit continuer à enregistrer la page sous l'ancien schéma.
3. **Registre** — formulaire connecté au Compte SINJIRA et dossier du personnage, sans génération IA automatique : <https://www.benoitcantin.com/projets/sinjira/registre/>.
4. **Jeux** — Fracture du Réseau-Mère possède des règles et une édition de déduction simplifiée; Réseau-Mère : Résistance est présenté comme un projet confirmé, non un jeu entièrement livré : <https://www.benoitcantin.com/projets/sinjira/jeux/>.
5. **Communauté** — espaces, identités séparées, modération et appels sont implémentés ou documentés; les parcours réels multi-comptes et la capacité de modération doivent encore être validés : <https://www.benoitcantin.com/projets/sinjira/communaute/>.
6. **Monde parallèle** — conception et parcours de continuité narrative visibles, mais pas de preuve d'une exploitation complète sur plusieurs cycles avec vrais utilisateurs : <https://www.benoitcantin.com/projets/sinjira/monde-parallele/>.
7. **Commerce** — seules les **réservations sans paiement** sont annoncées, avec prix/date de sortie non publiés; achats payants désactivés : <https://www.benoitcantin.com/compte/mes-achats.html>. Ne pas activer des paiements sans décision explicite et contrôles légaux/commerciaux.
8. **Mon IA** — fondation de réglages et consentements, **sans moteur conversationnel, sans récupération de contenu**, explicitement indiquée sur <https://www.benoitcantin.com/compte/mon-ia.html>. Aucune activation silencieuse ou prestation payante.
9. **Sécurité/exploitation** — inspection Supabase en lecture seule : **134 tables publiques avec RLS**, **177 politiques publiques**, **241 fonctions SQL publiques** et **31 Edge Functions actives**. Ces volumes ne démontrent pas la qualité du service. Le Security Advisor signale notamment que la protection Auth contre les mots de passe compromis n'est pas activée; sa disponibilité peut dépendre du forfait. Aucune fonction de protection ne doit être affirmée active avant vérification. Référence : [runbook](SUPABASE_PRODUCTION_RUNBOOK.md).
10. **Frontière de production** — la migration `supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql` est déclarée au lot revu mais **non appliquée en production** au contrôle du 7 novembre. Respecter la séparation prévol local, prévol distant, application manuelle avec confirmation et éventuelle protection de l'Environment `production`.

## Priorités de livraison avec critères vérifiables

| Priorité | Travaux | Critères de fermeture |
|---|---|---|
| P0 | Synchronisation précise liseuse V32 | Revue/approbation explicite de la migration, prévol protégé, application autorisée, colonne SQL et contrainte vérifiées, RLS inchangé, reprise page + défilement validée avec compte autorisé sur deux appareils |
| P0 | Protection des comptes et droits du roman | Aucun accès intégral sans droit serveur; tests d'expiration et de changement de compte; pas de stockage local du livre privé; contrôle Auth des mots de passe compromis examiné selon le forfait |
| P1 | Vérification fonctionnelle des jeux | Exécution complète des règles et du moteur Fracture par des testeurs; cas négatifs, reprise, fin de partie, observabilité; périmètre et date de Résistance validés |
| P1 | Communauté et Monde parallèle | Parcours multi-comptes, modération/appels, confidentialité, reprise des cycles, règles de canon approuvées et tests de charge adaptés |
| P1 | Registre et identité du personnage | Formulaire, droits, corrections/retraits des données, parcours mineurs avec validation juridique lorsque pertinent et revue éditoriale réelle |
| P2 | Commerce | Prix, conditions et dates annoncés seulement après décision; conformité fiscale/consommation, livraison et remboursements validés avant tout paiement |
| P2 | Mon IA | Décision explicite de périmètre; étude de confidentialité et de coûts; tests de consentement/révocation avant tout moteur externe |
| Transversal | Accessibilité, QA et disponibilité | Tests automatisés + essais utilisateurs, mobile, navigateur, supervision, sauvegardes, procédure d'incident et preuve de mise en ligne |

### Statuts à ne jamais confondre

- **Développé** : le code existe sur GitHub.
- **Testé** : un scénario CI ou manuel précis a réussi; les autres scénarios ne sont pas implicitement validés.
- **Publié** : le code ou le contenu est effectivement visible sur le site.
- **Activé en production** : le backend et son schéma hébergé prennent réellement en charge le parcours.
- **Prêt pour le lancement** : une revue fonctionnelle, sécurité, accessibilité, conformité et exploitation a accepté le jalon.

### Mise à jour

Lors du prochain jalon, consigner les modules modifiés, les preuves de tests (SHA/PR), les limites, les blocages d'approbation et la nouvelle estimation *si et seulement si* les critères se sont réellement améliorés.


## Suivi de référence au 8 novembre 2026 — registre calculable

L'estimation initiale **66,5 % ≈ 67 % (incertitude ±10 points)** est confirmée comme **score pondéré indicatif**, non comme certification du lancement. Le registre JSON de référence [`docs/sinjira/programme-readiness-2026-11-08.json`](sinjira/programme-readiness-2026-11-08.json) reprend les dix domaines ci-dessus **sans ajuster les poids, maturités ou périmètre**. Le calculateur [`scripts/sinjira_programme_progress.py`](../scripts/sinjira_programme_progress.py) contrôle la formule et les critères avec tests de refus des dates ou preuves fictives.

### Jalons effectivement fusionnés depuis l'état initial

- **Fracture V45** : [PR #885](https://github.com/M0rdr3x/BenoitCantin/pull/885) fusionnée, 30 CI réussies. Proposition de quarantaine de dix fonctions SQL, **non appliquée à Supabase**.
- **Suivi éditorial des romans** : [PR #869](https://github.com/M0rdr3x/BenoitCantin/pull/869) fusionnée, 31 CI réussies et 32 tests Node. Registres de contrôle des deux livres **sans certification éditoriale finale ni publication intégrale**.
- **Fracture V46** : [PR #888](https://github.com/M0rdr3x/BenoitCantin/pull/888) fusionnée, 25 CI réussies. Le prévol en lecture seule de la base réelle conclut à **6 PASS, 3 BLOCK, NO_GO** : les permissions mutatrices et deux `WITH CHECK` ne sont pas encore durcis en production.

### Pourquoi aucune date de fin n'est annoncée

Il n'existe pas actuellement de série de mesures suffisante sur **le temps nécessaire à l'achèvement des jalons critiques**, leurs dépendances, les décisions éditoriales et les fenêtres de déploiement protégées. En conséquence, la date de fin est **`null` (indéterminée)** dans le registre. On ne déduit jamais une échéance de `33 %` de travail restant, ni du nombre de PR fusionnées, sans taux de livraison mesuré.

Les **13 critères de sortie** du registre restent ouverts et couvrent : synchronisation de lecture V32 et essai sur deux appareils, droits du livre privé, RLS/RPC Fracture, règles et multijoueur, révocation de sessions/MFA, performances mobiles et CSP privée, communauté et modération, Monde parallèle/Registre, révision éditoriale, commerce, Mon IA, puis recette et décision finale. Le calcul peut afficher **100 % de maturité estimée sans déclarer le lancement autorisé** tant que la validation réelle des critères et l'approbation du responsable ne sont pas consignées.

Les responsables peuvent clôturer un jalon seulement avec une **preuve vérifiable, une date de contrôle et le bon périmètre**. Le workflow n'a aucun accès au serveur ni aux comptes réels et ne doit jamais déclarer de mise en production à partir des seuls tests unitaires. 
