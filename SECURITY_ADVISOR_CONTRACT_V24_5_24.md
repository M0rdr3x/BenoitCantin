# SINJIRA™ V24.5.24 — Contrat des findings de sécurité

## Principe

**L’humain avant tout.** Un avertissement automatique ne doit jamais être « corrigé » en ouvrant des données privées, en supprimant une protection utile ou en activant un service payant sans décision humaine explicite.

Cette version est un **contrat de validation uniquement**. Elle n’ajoute **aucune migration de production** et le ledger Supabase reste à **155 migrations**, dernière version `20260823040936`.

## RLS Enabled No Policy

Supabase peut signaler `RLS Enabled No Policy` lorsqu’une table a RLS active mais aucune policy. Pour les tables SINJIRA volontairement scellées des schémas `public` et `private`, cet état est accepté **uniquement** lorsque les rôles navigateur `anon` et `authenticated` n’ont aucun privilège direct `SELECT`, `INSERT`, `UPDATE` ou `DELETE`.

Le contrat pgTAP V24.5.24 vérifie dynamiquement cette condition pour toutes les tables SINJIRA concernées. Il est interdit d’ajouter une policy permissive uniquement pour faire disparaître le linter.

Les tables du schéma `storage` sont gérées par Supabase et ne sont pas incluses dans ce contrat applicatif.

Référence : https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy

## SECURITY DEFINER exposé

Aucune fonction `SECURITY DEFINER` du schéma API `public` ne doit être directement exécutable par `anon` ou `authenticated`. Les opérations privilégiées restent derrière des wrappers publics `SECURITY INVOKER` et des schémas internes contrôlés.

Le contrat pgTAP vérifie séparément l’absence d’exposition privilégiée pour `anon` et pour `authenticated`.

## Unused Index

Le finding `unused_index` est une information de performance, pas une instruction automatique de suppression. Un index récent, un index de clé étrangère, un index de sécurité ou un index destiné à un parcours encore peu utilisé peut légitimement avoir zéro lecture observée.

**Aucun index ne doit être supprimé uniquement parce que l’advisor le marque inutilisé.** Toute suppression future exige une analyse de requêtes, des dépendances FK, des contraintes et de la charge réelle.

Référence : https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index

## Leaked Password Protection

L’advisor signale actuellement `Leaked Password Protection Disabled`. La protection intégrée Supabase utilisant HaveIBeenPwned est liée à une capacité de plan payant. La règle du projet reste : **aucun service payant ne doit être activé sans autorisation explicite**.

Le finding est donc documenté comme risque résiduel accepté sous contrainte Free; il ne doit pas déclencher automatiquement un changement de plan. Les protections gratuites existantes, notamment le minimum de 12 caractères et les parcours MFA/AAL2, restent obligatoires.

Référence : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Commerce et services externes

Ce contrat n’active aucun paiement, checkout, transporteur, courriel/SMS payant, IA distante payante, publication App Store/Play Store, passkey ou changement DNS.

Les précommandes du Livre I restent des réservations sans engagement financier automatique; les paramètres de vente, paiement, checkout, transport externe et conversion automatique restent désactivés jusqu’à décision explicite.

## GitHub

La protection serveur de la branche `main` reste un prérequis d’infrastructure externe tant que l’action de branch protection/ruleset n’est pas exposée par les outils disponibles. Le workflow de gouvernance du dépôt reste un garde secondaire, mais ne doit pas être présenté comme équivalent à une branch protection GitHub active.
