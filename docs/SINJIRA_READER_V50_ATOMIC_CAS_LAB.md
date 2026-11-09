# SINJIRA — V50 : démonstration CAS atomique sur base jetable

**9 novembre 2026 · Livrable expérimental de sécurité et de cohérence, NON une mise en service.**

## Constats déjà établis

- **V47 sur catalogue Supabase réel : NO_GO** (7 PASS, 2 BLOCK, 1 REVIEW). La colonne de position intrapage `scroll_ratio` issue de la migration V32 et sa contrainte de bornes sont absentes dans la base inspectée; aucune migration réelle n'a été exécutée dans cette phase.
- **V48 dans PostgreSQL fictif :** la migration originale V32 s'applique à des données artificielles et la RLS isole les comptes de test. Ce résultat n'est ni une preuve de version prod ni un test multi-appareils réel.
- **V49 dans PostgreSQL fictif :** un ancien UPSERT pour le même compte arrive après une nouvelle position et **l'écrase**. Les tests verts V49 signifient *risque reproduit*, pas risque résolu.

## V50 : ce que le prototype démontre

Le prototype s'ajoute **après** la reproduction V49, et seulement dans le conteneur PostgreSQL jetable de CI. Il ajoute une colonne de test `local_test_revision bigint NOT NULL DEFAULT 0` et une fonction locale **`SECURITY INVOKER`** `public.sinjira_reader_v50_try_save`. La fonction, exécutée avec les droits du lecteur, effectue dans **une seule instruction UPDATE** :

```sql
UPDATE public.sinjira_reader_library
   SET last_page = next_page,
       progress_percent = next_percent,
       scroll_ratio = next_ratio,
       local_test_revision = local_test_revision + 1
 WHERE user_id = (SELECT auth.uid())
   AND novel_id = novel_uuid
   AND local_test_revision = expected_revision;
```

La condition `local_test_revision=expected_revision` et l'incrément sont atomiques dans PostgreSQL : deux mises à jour concurrentes avec la même révision ne peuvent pas toutes deux réussir pour la même ligne. La fonction retourne **`true` uniquement si exactement une ligne** a été modifiée; sinon `false`, sans révéler la position d'un autre compte. La fonction n'a ni `SECURITY DEFINER` ni droit d'exécution anonyme. Les politiques RLS existantes du banc d'essai restent applicables.

| Connexion fictive | Action | Résultat attendu |
| --- | --- | --- |
| Préparation | Remettre la ligne du compte A à la révision 0 dans la base de test | Page 4, ratio `NULL`, révision 0 |
| Appareil B | Écrire page 31 / ratio 0.8123 avec révision attendue **0** | **Accepté**, révision devient 1 |
| Appareil A en retard | Proposer page 12 / ratio 0.2100 avec révision attendue **0** | **Refusé**, B reste à page 31 / ratio 0.8123 |
| Compte distinct | Lire A ou écrire sur un roman absent | Aucun accès transversal, aucun insert implicite |
| A après reprise | Après lecture du nouvel état et choix explicite, proposer page 33 / ratio 0.8500 avec révision attendue **1** | **Accepté**, révision devient 2 |

**Critère d'acceptation du POC :** le test SQL échoue si l'écriture ancienne est acceptée ou si la position récente est modifiée. Le contrat Python refuse les secrets, identités réelles, contournements de RLS, fonctions `SECURITY DEFINER` et usages d'une base distante.

## Ce que V50 NE résout PAS

1. **La liseuse actuelle utilise toujours son `upsert` normal**, sans fournir de révision. Le prototype n'est pas appelé depuis le navigateur. Aucun correctif de production n'est déployé.
2. **V32 n'est pas déployée** dans la base réelle inspectée; les colonnes, contraintes et migrations effectives exigent un processus protégé. La colonne `local_test_revision` est **un artefact de test**; la créer en production demanderait une conception, un nom et une migration nouveaux, revus et approuvés.
3. **L'insertion initiale**, la migration de progressions existantes, les écritures hors ligne, les doubles envois, la révocation des droits, les erreurs de timeout et les courses de deux transactions simultanées doivent recevoir des tests supplémentaires.
4. Un conflit d'écriture doit être expliqué au lecteur. **Ne pas faire disparaître silencieusement le marque-page local** après un rejet; relire l'état distant autorisé et offrir une résolution explicite.
5. **Aucun test réel sur deux appareils**, aucun contrôle du vrai cycle Auth/Storage PDF privé, aucune certification de conformité ou de disponibilité.
6. Le choix d'une révision monotone côté serveur est un **candidat technique**, pas une décision d'architecture validée. L'horodatage fourni par le client ne doit pas être une source de vérité suffisante pour éviter les écrasements.

## Passage obligatoire à la correction réelle

**Ordre recommandé :** revue de conception et menace → branche de correction contrôlée → migration testée/retour arrière → permissions RLS et comportement RPC ou requêtes conditionnelles → gestion du conflit dans la liseuse → tests de transactions simultanées/usage hors ligne → audit des droits privés → préproduction à deux appareils → décision d'autorisation.

La référence normative actuelle de Supabase pour les mises à jour RLS exige un droit de `SELECT` associé et le respect de `USING` et `WITH CHECK`. Voir https://supabase.com/docs/guides/database/postgres/row-level-security. Le prototype V50 est limité au banc d'essai autorisé; **aucune requête sur la production n'est nécessaire** pour sa démonstration.

**Décision inchangée : SINJIRA 66,5 % ±10 points de maturité estimée, 13 portes de lancement ouvertes, `reader_two_devices` et `reader_v32_prod` NO_GO.** Projet Nova politique 47 %, Nova–Sinjira sans taux, boussole 9/12, sondage 6/11 au relevé du 8 novembre.

Suivi : issue [#826](https://github.com/M0rdr3x/BenoitCantin/issues/826) ; PR [#923](https://github.com/M0rdr3x/BenoitCantin/pull/923).
