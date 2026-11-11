# SINJIRA™ V59 — autoriser la sauvegarde CAS seulement au détenteur du droit de lecture

**10 novembre 2026 — correctif candidat de sécurité, NON déployé.** Cette version est empilée sur [V51 #947](https://github.com/M0rdr3x/BenoitCantin/pull/947) et répond à l'écart [#955](https://github.com/M0rdr3x/BenoitCantin/issues/955).

## Constat

La RPC `public.sinjira_reader_save_progress_cas` (V51 candidate) est créée en `SECURITY DEFINER` afin d'éviter l'écrasement concurrent de positions. Elle exigeait `auth.uid()` et le roman existant mais ne prouvait pas que **ce compte était autorisé à lire ce roman**. Un client tiers peut appeler directement la RPC sans utiliser le parcours d'accès au PDF. Il ne s'agit pas d'une preuve de fuite de texte ou de données en production : la RPC V51 elle-même **n'est pas déployée**.

Le 10 novembre, une **lecture seule du catalogue PostgreSQL Supabase** a confirmé la présence des colonnes nécessaires :
- `sinjira_novels.id,status,product_id,file_ready`;
- `products.id,active`;
- `user_entitlements.user_id,product_id`;
- les fonctions `is_sinjira_owner(p_user_id uuid)` et `is_sinjira_admin(p_user_id uuid)`.
La colonne `revision` candidate V51 et `scroll_ratio` V32 **ne sont pas présentes dans le schéma de production consulté**. Aucune migration ni mutation n'a été effectuée.

## Politique proposée (alignée sur l'Edge Function `get-novel-file-url`)

Un appel CAS ne peut écrire que si, au moment de la requête :
1. l'utilisateur est authentifié par `auth.uid()`;
2. le roman est **published** et `file_ready=true`;
3. le compte est reconnu propriétaire/administrateur interne via les mêmes helpers, **ou** il détient une ligne `user_entitlements` vers le `product_id` du roman et `products.active=true`.

Tout autre cas — roman inexistant, non publié, non activé, produit inactif, absence de droit, droit retiré — retourne la même réponse opaque `unavailable` **sans exposer une révision ni un marque-page**. L'autorisation est réévaluée à chaque sauvegarde, même pour une ligne déjà existante.

**Restriction retenue :** un fichier `file_ready=false` interdit la sauvegarde de position intégrale, même pour un owner/admin, puisque l'Edge Function ne remet pas le PDF non prêt. Cette décision est explicite et requiert confirmation du responsable produit.

## Modifications techniques limitées

- Le fichier de migration V51 reste dans **`supabase/review-candidates/`** : il n'entre pas dans le lot de migrations de production autorisé. Aucune modification sur le serveur n'est proposée ou exécutée.
- Le contrôle de droits est placé **dans** la fonction privilégiée, avant l'INSERT ou UPDATE, sans client, SQL dynamique, paramètre de compte alternatif ni changement aux GRANT V51.
- La fixture `setup_sinjira_reader_v59_entitlements.sql` ajoute au laboratoire V48 un schéma représentatif avec comptes/romans/produits **fictifs uniquement**.
- Le script `test_sinjira_reader_v59_entitlements.sql` contrôle publication, achat/droit actif, refus au compte étranger, produit désactivé, absence de fichier, roman inconnu, retrait du droit, owner/admin autorisé uniquement au titre publié, JWT authentifié vide, refus de toute écriture de métadonnées et préservation des anciennes révisions.
- La CI V59 dans PostgreSQL 17.6 jetable exécute d'abord les scénarios V48/V51 (y compris sauvegarde concurrente page 51/52), puis les règles d'accès V59.

## Éléments qui restent bloquants avant GO

- Vérification indépendante du propriétaire SQL réel des fonctions `SECURITY DEFINER`, du rôle d'exécution, des GRANT, de RLS, des schémas et du fonctionnement avec un **vrai JWT** en préproduction.
- Contrôle métier de la différence entre droit de télécharger le PDF intégral, droit de mémoriser une progression et consultation de la **démo publique**. Cette RPC est destinée au roman complet et non aux marque-pages locaux de la démo.
- Vérification d'une révocation réelle de droits, d'une annulation, d'un changement de compte, d'un ancien client en cache et de l'effet des colonnes V32/V51 non encore appliquées.
- Tests de concurrence sur deux vrais appareils, migrations de production dans l'ordre approuvé, audits RLS/advisors et approbation humaine.

**Décision : NO_GO production.** Aucun score global ne change : SINJIRA **66,5 % ±10 points** au référentiel du 8 novembre 2026, **13/13 portes ouvertes**. Réussite de laboratoire ≠ revue de sécurité ni autorisation de livraison.
