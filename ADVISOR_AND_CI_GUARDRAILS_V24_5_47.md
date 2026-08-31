# SINJIRA™ V24.5.47 — Garde-fous advisor et résilience CI

## Principe

Cette version ne modifie pas le schéma de production et n'ajoute aucune migration Supabase. Le ledger reste à **174 migrations**, avec `20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening` comme dernière migration appliquée.

Le but est d'empêcher deux mauvaises corrections : ouvrir des données pour faire disparaître un avertissement informatif, ou supprimer des index utiles uniquement parce qu'ils sont encore peu utilisés.

## RLS activée sans politique

Un avis `RLS Enabled No Policy` est acceptable lorsqu'une table est volontairement scellée et que son contrat prévoit qu'aucun navigateur ne doit y accéder directement.

Règles :

- ne jamais créer une politique permissive uniquement pour faire disparaître le lint ;
- conserver RLS active sur les tables scellées ;
- conserver les privilèges directs `anon` et `authenticated` révoqués lorsque le contrat de la table l'exige ;
- passer par une RPC contrôlée lorsqu'un accès applicatif légitime existe ;
- toute nouvelle politique RLS doit correspondre à un besoin métier explicite et être testée.

## Index indiqués comme inutilisés

`unused_index` est un avis de performance informatif, pas une preuve qu'un index doit être supprimé.

Règles :

- ne pas supprimer automatiquement un index couvrant une clé étrangère ;
- ne pas supprimer un index de sécurité, de rétention, de purge ou de fonctionnalité dormante uniquement parce que son compteur d'utilisation est encore nul ;
- avant toute suppression, exiger une analyse de redondance, un historique d'utilisation représentatif et, lorsque pertinent, un `EXPLAIN` sur les requêtes concernées ;
- les fonctions commerciales encore dormantes peuvent légitimement avoir des index peu utilisés avant l'ouverture réelle du service.

## Protection des mots de passe compromis

Le lint `Leaked Password Protection Disabled` reste une contrainte connue du plan actuellement gratuit lorsque la fonction intégrée nécessite un niveau payant.

SINJIRA™ ne doit pas activer un plan, une option ou un fournisseur payant sans autorisation explicite. En attendant, le contrat gratuit conserve notamment le minimum de **12 caractères** et les barrières MFA/AAL2 déjà en place.

Référence Supabase : https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Résilience des tests Firefox

Un timeout isolé de navigation Firefox a été observé alors que Chromium, WebKit, Lighthouse, le site et les autres contrôles étaient verts. Le smoke test local Firefox autorise désormais **une seule relance bornée** :

- aucun retry supplémentaire ;
- Chromium et WebKit ne reçoivent aucun retry automatique ;
- si Firefox échoue une deuxième fois, le workflow échoue ;
- aucune assertion fonctionnelle n'est supprimée ou assouplie.

Cette règle absorbe un incident ponctuel du moteur ou du runner sans masquer une régression persistante.

## Services externes et commerce

Cette version n'active aucun paiement, checkout, vente, transporteur, courriel/SMS payant, IA distante payante ni autre fournisseur externe facturable.

Les précommandes du Livre I restent des réservations sans engagement financier et les UUID internes restent opaques.
