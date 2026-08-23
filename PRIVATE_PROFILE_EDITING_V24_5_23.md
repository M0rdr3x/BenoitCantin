# SINJIRA™ V24.5.23 — Profil privé modifiable

## Principe

L’humain avant tout : une personne peut compléter ses informations personnelles lorsqu’elles sont absentes et les corriger ou les mettre à jour lorsqu’elles deviennent inexactes.

La page **Profil** n’est donc plus un écran de lecture seule pour le coffre privé. Le membre peut enregistrer et annuler ses modifications directement dans son Compte SINJIRA™.

## Données concernées

Le coffre privé contient uniquement les champs de profil nécessaires à cette fonction :

- date de naissance;
- genre de profil;
- langues;
- ville, province/région et pays de résidence;
- ville, province/région et pays d’origine;
- statut relationnel, date et libellé privé du partenaire.

Ces renseignements ne sont pas publiés automatiquement et ne sont pas copiés automatiquement dans le Registre. Le Registre et l’Histoire de vie conservent leurs frontières et leurs consentements propres.

## Frontière technique

`public.private_profiles` est une table de production avec RLS active. `anon` et `authenticated` n’ont aucun accès direct SELECT/INSERT/UPDATE/DELETE à cette table.

Le navigateur utilise seulement :

- `private_profile_get()`;
- `private_profile_save(...)`.

Les deux fonctions publiques sont `SECURITY INVOKER`. Les opérations privilégiées sont isolées dans `sinjira_profile_internal` et vérifient l’utilisateur courant ainsi que la politique MFA configurée.

## Correction de la date de naissance

Une date déjà utilisée par les règles de sécurité peut être **corrigée**, mais elle n’est pas effacée lorsqu’un profil de sécurité existe.

Une correction de date :

- désactive le profil Rencontres;
- retire la confirmation d’intention sérieuse;
- demande une nouvelle confirmation d’admissibilité;
- si la correction fait franchir la frontière mineur/adulte, ferme les connexions Rencontres actives, annule les rencontres publiques en attente et révoque les consentements de dévoilement photo.

Les règles jeunesse restent appliquées côté serveur : âge minimum, juridiction jeunesse actuellement prise en charge et lien parent/tuteur vérifié pour les moins de 14 ans.

## Version et migrations

La production contient deux migrations liées à ce chantier :

- `20260823035659 sinjira_v24_5_14_private_profile_editing`
- `20260823040936 sinjira_v24_5_23_private_profile_schema_convergence`

Le premier nom interne a été attribué alors que la production avait déjà progressé jusqu’à V24.5.22. Une migration appliquée n’est jamais renommée ni réécrite. **V24.5.23** est donc le jalon canonique de la fonctionnalité et la seconde migration assure la convergence complète des installations.

Le ledger de production contient **155 migrations** après V24.5.23.

## Services externes

Aucun paiement, transporteur, courriel/SMS payant, IA distante payante ou autre fournisseur externe facturé n’est activé par ce chantier.
