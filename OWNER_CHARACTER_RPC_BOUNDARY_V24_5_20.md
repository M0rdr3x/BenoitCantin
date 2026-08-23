# SINJIRA V24.5.20 — Frontière RPC personnage propriétaire

## Objectif

Réduire la surface privilégiée exposée par `public.ensure_sinjira_owner_character()` sans modifier son contrat fonctionnel ni les séparations d’identité de SINJIRA™.

## Production

Migration appliquée :

`20260823031850 sinjira_v24_5_20_owner_character_rpc_boundary`

Le ledger compte **151 migrations**.

## Frontière d’exécution

- `public.ensure_sinjira_owner_character()` reste la signature appelée par l’interface.
- Le wrapper public est `SECURITY INVOKER`.
- L’implémentation privilégiée est déplacée dans `sinjira_owner_internal`.
- `anon` n’a aucun droit `EXECUTE`.
- `authenticated` et `service_role` conservent le droit nécessaire au contrat existant.
- L’implémentation interne conserve sa vérification `auth.uid()` et le verrou propriétaire/service role.
- Le type de retour `jsonb` reste inchangé.

## Invariants d’identité

Cette migration ne fusionne aucune identité. Elle ne change ni le profil d’affichage, ni l’identité technique privée, ni l’identité narrative du Monde parallèle. Elle ne rend aucune donnée du Registre publique et ne crée aucun nouveau lien public entre identités.

Le rôle de cette RPC reste un mécanisme de réparation/alignement du personnage propriétaire déjà autorisé; elle n’accorde pas un pouvoir de création canonique automatique à une IA.

## Sécurité et coût

Aucun service externe payant, paiement, checkout, transporteur, courriel/SMS externe, IA distante ou modification DNS n’est activé par V24.5.20.

Principe directeur : **L’humain avant tout.**
