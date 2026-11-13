# Projet Nova — Sondage citoyen : prévol SQL local V7 sur la confidentialité

**Document de contrôle daté du 9 novembre 2026.** Fondé sur les sources et critères de réception du **8 novembre 2026**. **Aucun bulletin réel émis, aucun vote ouvert, aucune modification de Supabase.**

## État du sondage

Le sondage demeure **6/11 critères de réception réussis (54,5 % de couverture technique)**, avec `published:false`, aucun vote réel documenté et aucune autorisation de mise en service. Le prévol SQL V7 **ne change pas** le statut `POLL_PRIVATE_PREFLIGHT=PENDING`, `POLL_CAPTCHA_ANTIREPLAY=PENDING`, `POLL_LEGAL_REVIEW=PENDING`, `POLL_ACCESSIBILITY=PENDING` ou `POLL_APPROVAL_GO_LIVE=PENDING`. L'avancement politique du Projet Nova demeure 47/100, sans rapport de déduction avec le nombre de tests du sondage.

## Pourquoi tester le schéma réellement exécuté ?

Les contrôles précédents avaient testé la politique de publication à travers une **modélisation SQLite** et une revue du SQL Supabase, mais ne démontraient pas l'exécution du **vrai `public.nova_poll_submit` PostgreSQL** en concurrence avec les règles RLS, ACL et le stockage de lots. La V7 utilise le contenu original de `supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql` **sans aucun changement** dans un service **PostgreSQL 17.6 éphémère** sur l'interface locale de GitHub Actions. Les rôles `anon`, `authenticated` et `service_role` sont fictifs et ne possèdent pas d'identifiants de connexion; `service_role` est autorisé à exécuter le RPC, les deux autres ne le sont pas.

Les fichiers `tests/security/sql/nova_poll_v7_lab_setup.sql`, `nova_poll_v7_security_replay.sql` et `nova_poll_v7_private_batches.sql` vérifient :

| Contrôle | Opération de test et résultat attendu |
| --- | --- |
| Schéma et droit | Huit questions de référence; cinq tables avec RLS; refus d'EXECUTE du RPC et de SELECT direct aux rôles anonymes et authentifiés |
| Anti-rejeu | Dix bulletins **entièrement artificiels** à jetons hexadécimaux factices; une réutilisation du même jeton doit répondre `duplicate` et laisser les comptes inchangés |
| Questionnaire canonique | Réponses incomplètes, question `q99` ou choix `8` doivent échouer avec l'erreur SQL `22023`; aucune ligne ajoutée |
| Premier lot | Dix bulletins fictifs identiques produisent **un seul instantané agrégé** avec huit comptes de dix, sans stockage de texte individuel des réponses |
| Temporisation | Dix nouveaux bulletins arrivant immédiatement ne doivent pas rafraîchir le lot avant six heures; puis simuler un âge de sept heures **dans la base jetable** |
| Différences de publication | Avec un premier lot de dix, un deuxième ajout fictif **9/1** (neuf et un) ne doit pas être publié; après quatre ajouts à la catégorie minoritaire, le lot **9/5** ne doit être publié qu'une fois le seuil atteint |
| Sortie | Message `NOVA-POLL-V7-LAB-ONLY`; aucun accès distant, aucun secret, aucune page publique modifiée |

**Attention aux limites de preuve :** le seuil SQL ne peut pas empêcher toute inférence politique à partir d'une connaissance externe sur un groupe; le mécanisme anti-rejeu par jeton ne garantit pas **une personne unique**. Les tests sont séquentiels et ne démontrent pas encore le comportement de deux soumissions réellement concurrentes, ni les intégrations de Turnstile, les délais réseau, la conservation/purge, l'accessibilité ou les obligations légales.

## Pièces exigées avant la réception des cinq critères ouverts

- **`POLL_PRIVATE_PREFLIGHT`** : revoir en préproduction isolée les politiques de suppression par lots, les instantanés publics sous charges variées, la réidentification par comparaison et les durées de conservation; vérifier les permissions et la purge, avec avis indépendant. Le succès de ce laboratoire est une **preuve partielle seulement**.
- **`POLL_CAPTCHA_ANTIREPLAY`** : démontrer le CAPTCHA avec secrets **de test**, cas de rejeu/soumissions concurrentes, taille et délai, sans utiliser un compte ni un participant réel; conserver les résultats et revue de sécurité distincte.
- **`POLL_ACCESSIBILITY`** : examen humain WCAG 2.2 AA avec lecteurs d'écran sur appareils physiques, claviers, indication d'erreur, labels et consentements.
- **`POLL_LEGAL_REVIEW`** : avis juridique indépendant sur la collecte d'opinions politiques, justification du traitement, information/consentement, conservation, droits d'accès et risques de réidentification; publication des limites de représentativité.
- **`POLL_APPROVAL_GO_LIVE`** : approbation distincte de la version du corpus, du déploiement, des contrôles et de l'ouverture; la décision doit rester humaine, explicite, datée et révocable.

Le document ne valide **aucun des cinq critères**. Si le test local échoue, corriger l'outil ou le mécanisme dans une PR, puis refaire l'exécution. Ne jamais abaisser les seuils de confidentialité pour rendre un test vert.

**Références dans le dépôt :**
- `docs/nova-sondages/reception-sondage-boussole-2026-11-08.json`
- `supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql`
- `supabase/functions/nova-civic-poll/index.ts`
- `scripts/test_nova_poll_delta_privacy.py`
- `.github/workflows/nova-poll-v7-sql-private-lab.yml`

**Décision de lancement : NO-GO, en attente d'autorisation et d'avis indépendants.**

## Extension V8 — Soumissions simultanées du même jeton et de jetons distincts

**Hypothèse testée :** la contrainte unique `(poll_version,token_hash)` et les compteurs agrégés doivent produire le même nombre de bulletins comptabilisés, que les requêtes fictives arrivent en série ou presque simultanément. Ces essais se déroulent **uniquement sur le même PostgreSQL jetable local**, après V7 et une remise à zéro autorisée des seules lignes fictives.

Le script `scripts/test_nova_poll_v8_concurrent_local.sh` refuse toute exécution si l'identité du serveur n'est pas exactement `nova_poll_v7_disposable` sur `127.0.0.1`. Il utilise `psql` et `SET ROLE service_role` **dans des connexions séparées**. Les jetons sont des valeurs hexadécimales artificielles produites par `printf`; aucune identité ni opinion réelle n'est collectée ou persistée. L'essai est volontairement une concurrence **best-effort dans la CI** et ne prétend pas simuler toute une charge nationale ou des latences d'Internet.

| Essai | Garantie vérifiée sur la base jetable |
| --- | --- |
| Même jeton, **deux appels asynchrones** | Exactement **un** `accepted`, un `duplicate`, **un seul reçu**, huit compteurs à 1, **aucun lot public** avant dix participants |
| **16 jetons différents**, seize connexions asynchrones | Les 16 soumissions terminent avec `accepted`, sans interblocage ni échec SQL, huit comptes agrégés valant 16 |
| Instantané publié sous concurrence | Au moins dix bulletins avant publication, au plus seize; huit comptes publiés identiques au compteur `published_ballots` |
| Isolation du banc | Garde serveur/base avant le `TRUNCATE` local, aucune connexion Supabase, aucun changement du schéma SQL original |
| Résultat et autorisation | Le script indique explicitement `NOVA-V8-LAB-ONLY-NO_GO`. Une réussite CI reste une **preuve de laboratoire**, non une autorisation de vote |

Des tests Python de contrat supplémentaires `tests/security/test_nova_poll_v8_concurrency_contract.py` et `bash -n` protègent le scénario, qui est lancé par la validation existante `.github/workflows/validate-nova-civic-poll.yml`.

**Conditions restant à vérifier séparément :** concurrence avec des réponses différentes et simultanées, expiration du CAPTCHA, erreurs réseau, test d'intrusion avec secrets de test, résilience lors d'un crash à mi-transaction, confidentialité de plusieurs publications, purge des reçus, accessibilité mobile et lecteur d'écran et avis juridique sur les données d'opinions politiques. Aucune porte `POLL_PRIVATE_PREFLIGHT`, `POLL_CAPTCHA_ANTIREPLAY` ou `POLL_APPROVAL_GO_LIVE` ne doit changer d'état sans attestation distincte.
