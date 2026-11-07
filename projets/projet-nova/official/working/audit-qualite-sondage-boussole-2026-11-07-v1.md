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
6. `tests/nova-civic-integrity.test.mjs` contient **35 tests déclarés** dans Node : documents, manipulations hostiles, ordre des chargements, conformité des bundles JSON/JavaScript, neutralité de la pondération, présence de la progression et non-publication du sondage.
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

## Audit d'accès Supabase — vérification en lecture seule

Une vérification supplémentaire de la **base Supabase connectée au site** a été effectuée **sans soumettre de bulletin, ni modifier les politiques ou la structure** :

- Les **cinq tables** `public.nova_poll_questions`, `public.nova_poll_counts`, `public.nova_poll_public_counts`, `public.nova_poll_publication_state` et `public.nova_poll_receipts` ont **RLS activée**.
- Les rôles `anon` et `authenticated` ne disposent **d'aucun droit SQL direct de lecture ou d'insertion** sur ces cinq tables, selon les privilèges contrôlés. Aucun droit direct de mise à jour n'est accordé à `anon`.
- La fonction SQL `public.nova_poll_submit` utilise `SECURITY DEFINER` avec un `search_path` fermé, mais le privilège `EXECUTE` est **réservé à `service_role`**, non accordé à `anon` ou `authenticated`. Le fait qu'elle soit dans le schéma `public` exige de conserver strictement cette restriction.
- Le SQL du RPC vérifie version, questions, valeurs autorisées, jeton anti-rejeu et conflits; les comptes sont agrégés sans enregistrement des choix individuels. Les critères de publication par lots comprennent au moins dix nouveaux bulletins, six heures entre publications et une protection contre les écarts de moins de cinq dans chaque catégorie.
- L'Edge Function publique `nova-civic-poll` contrôle les origines admises et le challenge antirobot avant l'appel privilégié au RPC. **Cette vérification du code ne remplace ni un test de charge, ni un pentest, ni la validation des paramètres secrets réels.**
- La base contient toujours **huit questions, aucun bulletin enregistré et aucun résultat publié** au moment de l'inspection. Les huit formulations correspondent **caractère pour caractère** au corpus GitHub.
- Le chargement du **registre partisan** de la boussole appelle maintenant aussi la validation complète du questionnaire avant toute présentation de fiches, afin d'empêcher des positions documentaires reliées à des axes incohérents.

**Limites et prochain contrôle :** vérifier l'absence d'autres chemins privilégiés vers les tables, le comportement simultané du RPC et les politiques de conservation, avec des tests d'intégration en environnement **isolé**. Ne pas écrire de faux votes en production; la certification « 100 % » reste non acquise.

## Complément du 7 novembre : calcul reproductible et déploiement contrôlé

### Résultat technique supplémentaire

Le module `assets/nova-civic-integrity.js` contient désormais **`scoreCompass(questionnaire, answers)`**, une fonction pure pour les seize axes, contrôlant les réponses (−3 à +3, ou `null` pour « Sans opinion »), les poids d'importance et les projections secondaires. La boussole publique utilise **ce même calcul**, plutôt qu'une copie non testée.

Une comparaison de **260 jeux de réponses de test diversifiés** (valeurs, poids et questions passées) entre le calcul historique et le nouveau moteur a donné **260 résultats identiques**. Des essais supplémentaires montrent que **64 questions passées** produisent **16 scores non calculables** et qu'un seul choix ne crée pas artificiellement un score d'axe. Le nouveau fichier `tests/nova-civic-scoring.test.mjs` contient **25 tests Node déclarés**; `tests/nova-civic-readiness.test.mjs` en contient maintenant **10**, en plus des **35 tests** d'intégrité existants. Leur exécution en GitHub Actions n'est **pas encore attestée** par une preuve de CI.

Les huit **formulations et thèmes** du sondage sont aussi figés dans le contrôleur et comparés aux sources JSON; changer la formulation dans le bundle local seul empêche l'utilisation du questionnaire. Le sondage reste `published:false`.

### Une fonctionnalité citoyenne supplémentaire

La boussole permet désormais, **dans GitHub**, l'action **« Voir mon profil actuel (même incomplet) »**, sans parcourir les 64 étapes. Si une dimension compte moins de deux réponses principales, elle reste affichée **« données insuffisantes »**, sans score, et l'outil ne recommande jamais une formation politique. Les réponses restent localement consultables/corrigeables et `Recommencer` les efface. Le HTML, le JS, le CSS et les versions anti-cache ont été modifiés ensemble.

### Tests navigateur et état de publication

- [Parcours réel Q01 à Q25](https://agent.tinyfish.ai/runs/cd87d505-b0a4-4252-b23e-64309558e4e3) : les 25 premières questions ont accepté « Sans opinion / passer », sans erreur ni score pendant le défilement. **Q26 à Q64 et l'écran final n'ont pas été atteints** dans cette session : ne pas présenter ce test comme terminé.
- [Navigation Q01/Q02 et remise à zéro](https://agent.tinyfish.ai/runs/9ecee317-305e-469f-a6a5-223c2055fba3) : deux réponses de test ont été correctement conservées, puis le bouton `Recommencer` a remis les réponses à zéro. **Le bouton de profil partiel nouvellement enregistré dans GitHub n'était pas encore visible sur le site public** pendant cette inspection. Le déploiement récent ne peut donc **pas être déclaré vérifié**.
- Le dépôt possède un [workflow Netlify staging](https://github.com/M0rdr3x/BenoitCantin/blob/main/.github/workflows/deploy-netlify-staging.yml) à déclenchement **manuel**, protégé par un SHA complet, une branche de release, l'identité exacte du site et une confirmation `STAGING_ONLY`. Il produit des URLs de vérification sans promotion en production. **Aucune promotion ou activation n'est demandée par cet audit.**
- La continuité GitHub → serveur public doit être vérifiée par **SHA de release**, accès au nouvel élément d'interface et tests de fumée navigateur **avant** de certifier la version publique.

### Vérification du serveur du sondage en lecture seule

La version 5 de l'Edge Function `nova-civic-poll` a été consultée : elle refuse l'ouverture sans drapeaux de publication, version approuvée et secrets requis, contrôle une origine explicite, effectue Turnstile côté serveur, hache le jeton avec HMAC et utilise un RPC privilégié avec validation des huit choix. L'étape a **revu le code**, et non certifié l'efficacité des protections face à des tentatives réelles. Les cinq tables protégées par RLS et les droits du RPC ont été vérifiés séparément. La consultation reste **fermée**, sans bulletins de test en production.

### Matrice actualisée

Le registre `data/validation-sondage-boussole-2026-11-07.json` atteste **5 contrôles sur 12** pour la boussole et **6 contrôles sur 11** pour le sondage. Ces rapports de portes franchies **ne sont pas des pourcentages de réussite**. Les contrôles restants exigent notamment des tests d'intégration complets, vérifications multi-navigateurs et accessibilité, revue de confidentialité et décisions de publication.

### Complément : consentement explicite et conformité électorale

Le formulaire de sondage demande désormais **un consentement exprès** à la transmission d'opinions politiques pour leur comptabilisation et la publication conditionnelle de statistiques agrégées, avec un lien vers la politique de confidentialité et l'avertissement qu'une réponse agrégée ne peut être retirée individuellement. L'analyse préalable `official/working/controle-juridique-confidentialite-sondage-2026-11-07-v1.md` documente les références de la Commission d'accès à l'information et d'Élections Québec sur les sondages et les dépenses électorales. **Ce travail ne constitue pas une certification juridique; la porte légale demeure non franchie.**

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
