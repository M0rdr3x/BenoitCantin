# SINJIRA™ — registre des fournisseurs et transferts

Version V24.4.83 — 2026-08-19. Ce registre doit être revu avant l’ajout d’un fournisseur, d’un nouveau type de renseignement ou d’une nouvelle communication hors Québec.

## Supabase

- **Fonction actuelle** : authentification SINJIRA™, base PostgreSQL, RLS/RPC, stockage/fonctions lorsque la fonction concernée les utilise.
- **Projet production** : `gpvivleexywljowcqkru`.
- **Région du projet vérifiée** : `ca-central-1` — Canada Central.
- **Catégories possibles** : identifiants de compte, profils privés, données de sécurité/âge, contenus et états applicatifs selon les modules activés.
- **Minimisation** : aucune clé de service dans le navigateur; accès par RLS/RPC; données privées séparées des contenus publics.
- **Action de gouvernance** : conserver les conditions applicables, la liste des sous-traitants et l’analyse de transfert à jour. La région du projet ne suffit pas à conclure que tout sous-traitement reste exclusivement au Canada.

## Formspree

- **Fonction actuelle** : backend des formulaires publics de contact du portail et de Projet Nova. Le Registre des Consciences n’utilise pas Formspree comme stockage canonique.
- **Renseignements transmis par le formulaire général** : nom, courriel, projet sélectionné, message, consentement de contact et métadonnées techniques de soumission du fournisseur.
- **Hébergement déclaré par Formspree** : Amazon Web Services aux **États-Unis**.
- **Sécurité déclarée par le fournisseur** : TLS 1.2 minimum, AES-256 au repos, contrôles d’accès, SOC 2 Type II et clauses contractuelles types pour ses traitements pertinents.
- **Transfert hors Québec** : oui, pour les formulaires qui utilisent Formspree. Doit rester déclaré dans la politique publique et couvert par l’EFVP/évaluation hors Québec avant maintien ou élargissement du traitement.
- **Rétention** : dépend du forfait/configuration actif. La documentation Formspree indique 30 jours d’historique de soumissions pour le forfait gratuit. SINJIRA™ ne doit pas promettre cette durée comme durée contractuelle de son propre compte sans vérification du forfait actif.
- **Contrôle gratuit recommandé/obligatoire avant clôture** : activer `Restrict to Domain` avec `benoitcantin.com`; la documentation Formspree indique que cette option est disponible sur tous les forfaits.
- **État de ce contrôle** : à vérifier dans le compte Formspree; aucune connexion Formspree n’est disponible dans l’environnement de maintenance actuel, donc l’activation n’est pas revendiquée.

## GitHub / GitHub Pages

- **Fonction actuelle** : dépôt public du code non secret et hébergement statique du site public.
- **Règle** : aucun secret, clé de service, export privé, donnée de compte ou pièce justificative ne doit être commité dans le dépôt public.
- **Données de visite** : les requêtes vers le site statique peuvent générer des données techniques sous les pratiques du fournisseur d’hébergement; ne pas y ajouter de traqueur comportemental SINJIRA™.

## Facebook / Meta — liens sortants

- **Fonction actuelle** : liens vers les pages officielles SINJIRA™ et Projet Nova.
- **Règle** : lien sortant seulement; ne pas intégrer de pixel Meta ou autre profilage comportemental sans nouvelle EFVP, consentement applicable et activation explicite.

## Fournisseur futur

Avant toute intégration nouvelle, documenter au minimum :
1. finalité et nécessité;
2. catégories de renseignements;
3. personnes concernées, dont mineurs;
4. localisation et transferts;
5. sous-traitants;
6. chiffrement, accès, journalisation et réponse aux incidents;
7. durée de conservation/suppression;
8. clauses contractuelles pertinentes;
9. mécanisme d’exercice des droits;
10. coût et risque de facturation;
11. EFVP et gate juridique applicable.

Un fournisseur non documenté ne doit pas recevoir de nouveaux renseignements personnels de production.
