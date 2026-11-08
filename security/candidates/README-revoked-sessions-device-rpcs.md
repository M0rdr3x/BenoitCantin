# SINJIRA — garde de session active pour les RPC d'appareils

**État : candidat de revue, jamais une migration directement déployable.**
Fichier : `sinjira_revoked_auth_session_device_rpcs.sql`.

## Constat contrôlé (Supabase actif, lecture seule)

Les RPC privées `sinjira_security_internal` sont `SECURITY DEFINER`.
Elles effectuent déjà des contrôles d'identité `auth.uid()`, d'appareil,
d'autorisation ou MFA. Huit opérations sensibles inspectées ne
reconsultent cependant pas explicitement la session présente dans
`auth.sessions` pour refuser une session supprimée/révoquée.

Les métadonnées de `auth.sessions` confirment l'existence de
`id uuid`, `user_id uuid`, `not_after timestamptz`. Le catalogue
confirme que les rôles PostgreSQL habituels de migration `postgres`
et `supabase_admin` peuvent lire la table. **Aucune ligne de cette
table et aucun jeton utilisateur n'ont été consultés.**

Ce constat ne démontre ni vol de JWT ni exploitation réelle.
Le risque suppose déjà la possession d'un jeton et des paramètres
nécessaires. Les validations existantes ne sont pas supprimées.

Documentation : https://supabase.com/docs/guides/auth/sessions

## Huit opérations couvertes

| RPC privée | Risque à limiter |
|---|---|
| `security_resolve_connection_challenge` | Approbation ou refus d'une demande depuis un appareil supposé fiable |
| `security_resolve_connection_challenge_mfa` | Confirmation d'une nouvelle connexion par MFA |
| `security_set_device_trust` | Attribution d'un niveau de confiance/primaire |
| `security_revoke_device` | Révocation d'appareil |
| `security_report_lost_device` | Déclaration d'appareil perdu et fermeture de ses accès |
| `security_compromise_account` | Mesures d'urgence sur les autres appareils |
| `security_after_password_recovery` | Réinitialisation des appareils après récupération |
| `security_update_settings` | Modification des paramètres de sécurité du compte |

Les huit définitions de fonction sont copiées depuis
`pg_get_functiondef` du projet actif, puis une **seule instruction
`PERFORM private.security_require_current_auth_session(v_user)`**
est ajoutée immédiatement après leur contrôle `AUTH_REQUIRED`.
Un second contrôle compare les **empreintes SHA-256 des huit définitions
d'origine** calculées depuis le catalogue réel, après retrait de cette
unique instruction. La CI rejette donc également toute altération
inattendue de la logique métier copiée : elle ne peut pas se contenter
de conserver quelques marqueurs de sécurité.

## Nouveau garde

La fonction `private.security_require_current_auth_session(uuid)` :

1. Refuse un `p_user` nul ou différent de `auth.uid()`, issu du JWT
   validé côté Supabase.
2. Extrait `session_id` du JWT, refuse la valeur absente ou mal formée.
3. Vérifie dans `auth.sessions` la correspondance exacte des
   `id` et `user_id`, ainsi que
   `not_after IS NULL OR not_after > clock_timestamp()`.
4. Renvoie une erreur générique `AUTH_SESSION_INVALID` (SQLSTATE
   `42501`) sans révéler de session, UUID ou jeton dans le message.
5. Utilise `SECURITY DEFINER`, un `search_path` fixé à
   `pg_catalog`, des noms entièrement qualifiés et
   `REVOKE ALL ... FROM PUBLIC, anon, authenticated`.
   L'invocation se fait par les RPC existantes appartenant à un rôle
   privilégié, pas directement depuis le navigateur.

Les signatures RPC, les contrôles MFA/appareils, les opérations
métier et les droits des huit fonctions existantes sont conservés.

## Essais obligatoires avec comptes **fictifs** en staging

- Session active valide : appareil propriétaire, AAL2 si requis,
  action légitime acceptée comme auparavant.
- JWT valide cryptographiquement mais session **supprimée** :
  chaque RPC refuse avec `42501`, sans changement de données.
- Session de même UUID sous **autre utilisateur** : refus.
- Session dont `not_after` est dépassé : refus.
- `session_id` absent, mal formé ou de valeur nulle : refus.
- Appareil déjà révoqué / changement d'appareil / demande expirée :
  les anciennes règles continuent de refuser sans changement.
- Parcours de récupération de mot de passe et connexion MFA :
  un jeton légitimement renouvelé doit fonctionner.
- Vérifier les enveloppes `public` appelantes, les grants et le
  comportement de la traduction des erreurs HTTP au client.
- Vérifier que les autres RPC de sécurité non traitées ne constituent
  pas un contournement équivalent.

La CI `validate_revoked_session_rpc_candidate.py` refuse des mutations
d'identité, suppression du garde, contrôle tardif, divulgation de
droits et absence de `ROLLBACK`. **Un test statique ne prouve pas la
compatibilité réelle des RPC.**

## Contrôles de déploiement

- Ce fichier débute par `BEGIN;` et se termine obligatoirement par
  `ROLLBACK;` ; **il ne doit pas être exécuté sur la production**, même
  en transaction réversible.
- Aucun chemin GitHub Actions n'appelle `supabase db push` pour ce
  candidat. La CI ne reçoit aucun secret de production.
- Avant de créer une nouvelle migration canonique : résoudre le
  désalignement des migrations #438, comparer les définitions de
  production et les versions GitHub, tester en staging, obtenir une
  approbation et prévoir un retour arrière.
- Une future migration doit respecter les contrôles de publication
  et les contraintes de protection de branche GitHub (#135).
- Suivi prioritaire : #725, #702, #713.

**Aucune migration ni fonction SQL de production n'a été modifiée.**
