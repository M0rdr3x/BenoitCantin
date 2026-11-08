# Projet Nova — contrôle Supabase en lecture seule

**Date :** 8 novembre 2026. **Portée :** sondage citoyen de 8 questions, version `nova-consultation-v1`.  
**Nature de la preuve :** inspection de la configuration publiée, des privilèges PostgreSQL et des compteurs agrégés. Aucun vote, mutation SQL, changement de secret ni activation du sondage.

## Constats vérifiés

| Contrôle | Résultat |
| --- | --- |
| Fonction Edge `nova-civic-poll` | Active, version **6** |
| Code Edge actif vs fichier GitHub `supabase/functions/nova-civic-poll/index.ts` | **Correspondance exacte du contenu UTF-8** |
| Verrou d'ouverture côté serveur | Nécessite simultanément l'approbation de la version, le drapeau d'ouverture et les prérequis serveur; **les valeurs des secrets et drapeaux ne sont pas divulguées ni vérifiées par ce contrôle** |
| Tables `public.nova_poll_*` | **5/5 avec RLS activé** |
| Accès directs `anon` et `authenticated` | Aucun droit SELECT, INSERT, UPDATE ou DELETE sur ces 5 tables |
| RPC `public.nova_poll_submit` | EXECUTE refusé à `anon` et `authenticated`; accordé à `service_role` |
| Tables `nova_poll_counts`, `nova_poll_receipts`, `nova_poll_public_counts` | **0 ligne** dans chacune |
| `nova_poll_publication_state` | **0 bulletin publié** |

Le corpus publié dans le dépôt conserve `published:false`. La fonction Edge publique peut être active sans que l'envoi de réponses soit autorisé. Un nombre nul de bulletins ne prouve **pas**, à lui seul, l'état HTTP réel du serveur ni l'absence de données dans les journaux techniques des fournisseurs.

## Vérifications restantes et portes de sécurité

1. Exécuter les essais isolés de préproduction : origine autorisée et refusée, Turnstile, HMAC anti-rejeu, requêtes concurrentes, corps POST tronqués, délais et limites de débit.
2. Valider le cloisonnement et la publication par lots, y compris les risques de déduction par comparaison de publications successives et le traitement des cellules rares.
3. Faire confirmer les durées de conservation, les journaux des sous-traitants, les transferts de données, le consentement et les obligations québécoises par une personne compétente en droit et vie privée.
4. Revoir l'accessibilité clavier, lecteur d'écran et mobile; obtenir l'approbation éditoriale du corpus.
5. Vérifier explicitement le déploiement public à partir d'une version Git exacte, puis obtenir une autorisation documentée **avant toute ouverture du sondage**.

**Décision : NON HOMOLOGUÉ.** La réception demeure à **6/11 critères**; cet audit renforce la preuve déjà comptabilisée pour `POLL_DB_ACCESS` et `POLL_SERVER_SOURCE_REVIEW`, sans ajouter un nouveau critère réussi. Aucun secret, adresse IP, bulletin individuel ou identifiant de participation n'est inclus dans ce rapport.
