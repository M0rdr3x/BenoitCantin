# Réseau personnage — confidentialité du rôle propriétaire V25

## Objectif

Le runtime navigateur du Réseau personnage ne doit jamais déterminer un privilège à partir d’une identité réelle embarquée dans le code public.

**L’HUMAIN AVANT TOUT.** La séparation entre le compte réel et le personnage doit être conservée jusque dans les contrôles techniques.

**Protéger sans surveiller.** Le navigateur demande uniquement au serveur si le compte actuellement authentifié possède le rôle nécessaire; il ne connaît pas l’identité réelle qui sert à administrer ce rôle.

## Décision de rôle côté serveur

`assets/js/sinjira-community-character.js` utilise désormais `public.is_sinjira_owner` avec l’identifiant du compte authentifié. Cette RPC est la frontière existante pour savoir si **le compte courant** possède le rôle propriétaire.

Le contrat serveur vérifie `auth.uid()` : un compte authentifié ordinaire ne peut pas utiliser ce mécanisme pour tester arbitrairement le rôle d’un autre utilisateur.

Le runtime ne compare donc plus une adresse de compte et ne contient **aucune adresse courriel** pour reconnaître le propriétaire.

## Réparation du personnage

La réparation automatique existante `ensure_sinjira_owner_character` est conservée, mais elle n’est tentée qu’après une réponse positive de `is_sinjira_owner`.

La vraie autorisation reste côté serveur : la frontière interne de réparation vérifie le rôle propriétaire associé à `auth.uid()` avant toute mutation. Le navigateur ne devient jamais une source d’autorité.

## Migrations historiques

Cette correction ne réécrit aucune des **migrations historiques** déjà présentes dans le ledger de production. Leur immutabilité reste protégée par le garde V25 de l’historique des migrations.

Le changement porte uniquement sur le runtime navigateur actuel et sur sa preuve CI. Il n’ajoute aucune migration SQL et ne nécessite aucune écriture Supabase.

## CI

Le garde `validate_character_network_owner_privacy_v25.py` exige notamment :

- l’utilisation de `is_sinjira_owner` pour la décision du rôle;
- l’absence de `user.email` et de toute adresse courriel littérale dans le runtime Réseau personnage;
- le maintien de `ensure_sinjira_owner_character` derrière la décision de rôle serveur;
- la revalidation des contrats historiques du rôle propriétaire, de la réparation personnage, des RLS d’identité personnage et des RPC sociales;
- l’absence de secrets suivis.

Le workflow dédié ne reçoit aucun secret de production, ne lance aucune commande de migration et n’effectue **aucune écriture Supabase**.

## Frontière à conserver

Compte réel, profil public et personnage restent trois couches distinctes. Le réseau personnage peut utiliser l’identité de personnage nécessaire au rôle-play, mais il ne doit pas réintroduire une identité réelle comme raccourci d’autorisation dans le navigateur.
