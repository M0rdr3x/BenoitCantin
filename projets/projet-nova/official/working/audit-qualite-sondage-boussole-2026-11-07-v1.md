# Projet Nova — audit technique du sondage et de la boussole électorale

**Date :** 7 novembre 2026  
**Nature :** contrôle technique de préparation et des interfaces publiques, non homologation indépendante.  
**Objectif :** fiabiliser deux outils civiques neutres sans fabriquer de réponses, de données électorales, de preuves documentaires, de comparaisons partisanes ni de disponibilité.

## Synthèse exécutive

**Boussole :** questionnaire de **64 propositions** et **16 dimensions** présent; quatre questions principales par dimension, deux orientées vers chacun de ses deux pôles. Réponses localement calculées et option de passage. Comparaison avec les partis **désactivée** tant que les exigences de provenance et de couverture ne sont pas satisfaites.

**Sondage :** version **nova-consultation-v1** de **8 questions** à participation volontaire (âge 18+ autodéclaré). Les huit questions du JSON GitHub et des tables `nova_poll_questions` de Supabase **ont été comparées mot à mot** : identifiant, ordre, texte, tous concordants. Le corpus GitHub indique toujours `published:false`. L’Edge Function `nova-civic-poll` existe et est **ACTIVE (version 5)**, sans pour autant ouvrir le vote. Les données constatées le 7 novembre 2026 : **0 bulletin**, **0 ligne de totaux publiés**, **0 reçu anti-rejeu**, **0 bulletin annoncé publié**.

La condition « **100 % opérationnel** » n'est **pas certifiée** pour l'un ou l'autre des deux outils : plusieurs vérifications restent à réaliser. La bonne formulation actuelle est « composants et contrôles vérifiés, essais d'intégration partiels réussis, activation du sondage non autorisée ».

## Corrections et garanties ajoutées directement à GitHub

1. `assets/nova-civic-integrity.js` fournit trois validations sans réseau : **64/16**, orientations symétriques et limites des pondérations; **8 questions/6 choix** du sondage; correspondance textuelle et thématique entre sondage et boussole.
2. `assets/boussole-electorale.js` applique la validation stricte avant le rendu ou le calcul; les anomalies de poids, d'échelle ou de direction provoquent un échec contrôlé.
3. `assets/sondage-citoyen.js` refuse un corpus corrompu avant de rendre le formulaire ou d'autoriser le vote. Le bouton exige toujours les huit réponses (dont « Sans opinion / passer »), les deux confirmations, un jeton Turnstile et le statut d'ouverture; aucune donnée n'est transmise par le validateur.
4. `sondage-citoyen.html` expose un message de progression **accessible par lecteur d'écran**, « Questions répondues : X sur 8 »; `assets/sondage-citoyen.css` rend ce message lisible et `?v=2` invalide les anciennes feuilles de style.
5. `boussole-electorale.html` et `sondage-citoyen.html` chargent le **script d'intégrité après les corpus et avant les scripts d'interaction**, avec nouvelles versions d'URL pour limiter les caches obsolètes.
6. `tests/nova-civic-integrity.test.mjs` contient **33 tests déclarés** dans Node : documents, manipulations hostiles, ordre des chargements, conformité des bundles JSON/JavaScript, neutralité de la pondération, présence de la progression et non-publication du sondage.
7. `.github/workflows/nova-sinjira-finances-tests.yml` déclenche désormais aussi les contrôles en cas de modification des interfaces, scripts et corpus civiques, pour `push` et `pull_request`.

**Contrôles directs réellement exécutés :** **30/30** assertions de cohérence et mutations du validateur réussies dans un exécuteur JavaScript isolé. L'ensemble des **33 tests Node n'a pas encore une exécution CI attestée**, et les contrôles directs ne remplacent pas des tests navigateur exhaustifs.

## Audit navigateur public non destructif

Une session navigateur distante a examiné les deux pages en ligne **sans envoyer de bulletin ni de résultat**. Résultats observés :

| Parcours | Observation |
|---|---|
| Boussole : affichage | Page visible, 64 questions et 16 dimensions annoncées |
| Boussole : démarrage | Bouton fonctionnel, question 1/64 visible |
| Boussole : réponse à Q01 | Réponse de test conservée localement |
| Boussole : question suivante et précédente | Passage à Q02, retour à Q01 et préservation de la sélection |
| Sondage : interface | Huit questions et cases de consentement affichées |
| Sondage : statut | Consultation **en préparation**, pas de vote actif |
| Sondage : résultats | Masqués : aucun lot publiable |
| Soumission serveur | **Non testée** pour ne pas inventer une participation |

**Preuve de contrôle externe :** https://agent.tinyfish.ai/runs/59ec01c2-2ef7-407f-a5bd-20e52b7b64e4

Cette session ne confirme **pas** que tous les nouveaux fichiers GitHub sont déjà déployés sur le site, ni que les 64 questions ont été parcourues jusqu'à l'affichage final du graphique. Le parcours mobile et l'audit des lecteurs d'écran n'ont pas été attestés.

## Portes de qualité nécessaires pour pouvoir annoncer « 100 % »

| Domaine | Critère vérifiable | Situation |
|---|---|---|
| Corpus boussole | 64/64, 16/16, équilibre de direction et poids contrôlés | **Vérifié dans GitHub** |
| Corpus sondage | 8/8 questions concordantes avec l'API et la boussole | **Vérifié** |
| Intégrité des bundles | Fichiers JS publics identiques aux JSON GitHub | **Vérifié** |
| Parcours boussole | Début, Q01, Q02, retour, mémoire de réponse | **Vérifié en navigateur** |
| Résultat final boussole | Q64, saut, pondération, graphique, copie, partage et réinitialisation | **À tester entièrement en navigateur** |
| Parcours sondage | Chargement, fermeture, résultats non publiés | **Vérifié en navigateur** |
| Vote réel | Turnstile, consentement, POST, anti-rejeu, erreurs réseau et limites de débit | **Non testé avec participation réelle; ouverture fermée** |
| Publication agrégée | Seuil de confidentialité, états des lots, différenciation temporelle, absence de réidentification | **À auditer en environnement de test** |
| Accessibilité | Navigation clavier complète, focus, contrastes, lecteurs d'écran, WCAG | **Contrôles sémantiques partiels; revue humaine à faire** |
| Compatibilité et déploiement | Appareils mobiles, Firefox, Chromium, Safari, scripts en production et absence d'erreurs | **Parcours Chromium partiel; autres à vérifier** |
| Comparaison partis | Sources admissibles, deux révisions, couverture homogène, absence d'orientation du vote | **Désactivée volontairement : ne pas activer sans preuve** |
| Mise en service du sondage | Version officiellement approuvée, objectifs publiés, analyse vie privée, CAPTCHA opérationnel, registre de traitement et autorisation d'ouverture | **NON AUTORISÉ** |

## Précautions éthiques et juridiques

- Le sondage est **non probabiliste**, sans vérification d'unicité des personnes et sans garantie statistique de représentativité. Un jeton anti-rejeu de navigateur ne représente **pas** une identité prouvée.
- Les opinions politiques peuvent constituer des données sensibles. La boussole conserve les réponses dans la mémoire de la page, sans serveur de profil. Le sondage agrégera seulement les choix lors de l'ouverture et ne publiera jamais de bulletins individuels; l'infrastructure d'hébergement et l'anti-robots peuvent traiter des métadonnées techniques.
- **Aucun taux d'appui électoral, classement des partis, recommandation de vote ni résultat de scrutin n'est calculé ou déduit de cette consultation.**
- L'activation du sondage nécessite une décision de publication distincte, la validation du corpus, l'état des secrets Turnstile, les limites de stockage et de conservation, puis une vérification réglementaire et de confidentialité. **La simple existence d'une Edge Function active ne suffit pas.**

## Suite logique et professionnelle

**Priorité A — audit du parcours complet :** essais automatisés de Q01 à Q64 avec cas de réponses passées, modifications, pondérations, résultat final et partage volontaire; vérifications sur plusieurs navigateurs et terminaux.

**Priorité B — préproduction sondage :** tests de soumission avec tokens anti-robots réservés au test, revues des politiques RLS et du RPC `nova_poll_submit`, comportement anti-rejeu, concurrence, publication différentielle et confidentialité, **sans publier de faux bulletins en production**.

**Priorité C — préparation décisionnelle :** validation éthique de l'enquête, documentation des limites statistiques, calendrier et responsabilité de publication; maintenir `published:false` tant qu'aucune approbation de mise en service n'est enregistrée.

**Priorité D — registre partisan :** conserver le statut `comparisonEligible:false` sans préférence pour Parti Nova. Compléter, documenter et faire revoir les positions de toutes les formations sous les mêmes règles, sans inventer de positions ni produire de classement électoral.

**Bilan :** infrastructure de base et contrôles renforcés, parcours élémentaire fonctionnel, mais **aucune affirmation « 100 % »** avant validation des portes restantes. Le pourcentage global du programme politique Nova (`47/100`, audit G0.12) est **distinct** de la préparation des deux outils et **n'a pas changé**.
