# SINJIRA V50 — Risque de sauvegarde périmée entre appareils et protection atomique à étudier

**9 novembre 2026 — note d'ingénierie de sécurité.** Ce document décrit **un risque testable dans le code actuel**, et non une perte réelle observée chez des lecteurs. Les essais utilisent des identités et des marque-pages entièrement fictifs dans une base PostgreSQL jetable.

## Constat dans le code

Le lecteur public `assets/js/sinjira-liseuse-v26.js` envoie des sauvegardes vers `sinjira_reader_library` avec un **`.upsert(payload,{onConflict:'user_id,novel_id'})` non conditionné à la version de ligne**. Un `progressQueue` protège les écritures **du même onglet**, mais pas les écritures provenant de deux appareils. Après une coupure, `retryCloudProgress()` vérifie `updated_at` avant de rappeler `syncProgress()`. Entre le contrôle préalable et l'UPSERT, une autre session peut modifier la position. En mode normal, l'UPSERT ne compare pas non plus la version de la ligne.

**Risque :** l'appareil A conserve la page 13. L'appareil B du même compte enregistre ensuite la page 42. L'ancienne demande A revient et l'UPSERT remplace la page 42 par la page 13, malgré la présence d'une progression serveur plus récente. La sauvegarde de B peut être perdue sans erreur SQL.

La V32 (`scroll_ratio numeric(5,4)` et bornes 0 à 1) et les essais V48/V49 protègent la structure, les anciens marque-pages et la confidentialité RLS. **Ils ne protègent pas à eux seuls contre l'écrasement interappareils d'une écriture obsolète.**

## Preuve reproductible V50 sur PostgreSQL fictif

La suite `.github/workflows/sinjira-reader-v50-cas-lab.yml` utilise la **migration V32 originale** appliquée à la fixture V48 de deux comptes et deux livres fictifs. Après les sauvegardes A/B/A, la requête V50 :

1. Confirme le nom exact `sinjira_reader_v50_lab` et l'activation RLS **avant toute écriture**.
2. Reproduit une sauvegarde courante **page 42 / ratio 0.8250 / horodatage postérieur**, par le compte fictif autorisé A.
3. Rejoue le même `INSERT ... ON CONFLICT DO UPDATE` non conditionnel du produit avec une ancienne **page 13 / ratio 1.0000**. Le marqueur `V50-RISK-REPRODUCED` signifie que **l'écrasement a été reproduit dans la fixture**. C'est **un résultat négatif de sécurité**, même si le test de détection est vert.
4. Ajoute une colonne **`v50_lab_revision bigint` uniquement dans la base temporaire** pour illustrer une stratégie de *compare-and-swap* (CAS). Avec `UPDATE ... WHERE user_id = auth.uid() AND v50_lab_revision = version_attendue`, la sauvegarde de B passe de la révision 0 à 1; l'ancienne sauvegarde A qui attend encore 0 affecte **zéro ligne**; l'écriture suivante à partir de la révision 1 passe normalement à 2.
5. Vérifie que l'autre compte fictif n'a pas changé et que les données personnelles ne sont pas consultées. `V50-CAS-LAB-PASS` signifie seulement que le principe CAS fonctionne sur ce **schéma miniature**.

Le scénario contrôle un **ordre d'interleaving reproductible** et n'est pas une mesure de charge réseau avec deux appareils physiques simultanés. Il ne teste pas le flux Supabase Auth réel, les politiques de production additionnelles, les latences navigateur ni la gestion d'une reprise à révision conflictuelle. Il n'établit aucune violation de la vie privée sur un utilisateur réel.

## Remédiation recommandée — à concevoir puis faire approuver

- Définir une **révision monotone contrôlée par PostgreSQL** ou un autre mécanisme de concurrence atomique par couple `user_id,novel_id`, sans dépendre de l'horloge du téléphone. Préserver les données héritées et proposer une migration **additive nouvelle**, sans réécrire V32 ni une migration déjà appliquée.
- Lire `revision` avec `last_page,scroll_ratio` à l'ouverture; écrire uniquement si la révision attendue correspond. En cas de conflit, **ne pas écraser le serveur** : afficher un message honnête, recharger la progression, puis permettre une reprise humaine ou une nouvelle sauvegarde explicite. Un conflit n'est ni un succès ni une invitation à réessayer aveuglément l'UPSERT.
- Examiner la création de la première ligne, le cas d'une progression de l'ancien schéma, les connexions simultanées, la perte du réseau, la révocation de compte, le changement de livre et l'absence de texte privé dans la télémétrie. Une stratégie `updated_at` seule n'est pas atomique si les clients peuvent fixer les dates.
- Tester dans un Supabase **de préproduction fidèle et approuvé**, avec RLS/GRANT réels et plusieurs sessions de test, les écritures conditionnelles et la lecture d'un autre compte. Soumettre le SQL proposé à la chaîne de migration **par lot explicitement revu** et au runbook de retour arrière. Aucune `supabase db push` globale non revue.
- Exécuter ensuite le prévol V47 sur **la production**, avec examen indépendant, et seulement après faire la recette sur deux appareils physiques ou navigateurs distincts avec le même compte de test autorisé.

**Décision : `NO_GO` pour les deux portes `reader_v32_prod` et `reader_two_devices` tant que la solution réelle n'est ni appliquée ni attestée.** La PR V50 ne corrige pas le code client ni la base de production; elle expose un défaut et un prototype de protection, pour que le correctif ne repose pas sur une hypothèse non testée.

## Avancement du programme

Au **8 novembre 2026**, la maturité du programme SINJIRA est estimée à **66,5 % (±10 points)**, et ses **13 portes de lancement sont ouvertes**. Les portes `reader_v32_prod`, `reader_two_devices` et `security_sessions` ne sont **pas** validées par le laboratoire V50. Aucune date d'achèvement totale ne peut être certifiée.

Ce chantier reste distinct du programme politique **Projet Nova (47 %)**, de la réforme des services publics Nova–Sinjira (sans taux global démontré), et de la boussole électorale (9/12 critères) et du sondage citoyen (6/11 critères, vote fermé).

Suivi de la liseuse : <https://github.com/M0rdr3x/BenoitCantin/issues/826>. Le document ne constitue pas une attestation d'audit de sécurité indépendante.
