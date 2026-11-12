# P50L — Fiche de travail : vérification indépendante du canal courriel

**DOCUMENT À REMPLIR UNIQUEMENT HORS GITHUB, PAR UN TITULAIRE DE MANDAT VÉRIFIÉ.**
**CETTE VERSION PUBLIQUE EST VIDE ET NE CONSTATE AUCUN RÉSULTAT RÉEL.**

## Mandats et sécurisation préalables

- [ ] Identifier la personne morale, l'association ou la personne effectivement responsable de Projet Nova; qualifier la loi applicable avec le conseil juridique.
- [ ] Déterminer qui possède juridiquement le compte, qui y accède et qui est habilité à auditer les seules configurations nécessaires.
- [ ] Approuver le périmètre minimal de vérification et les procédures de protection des traces; ne pas exporter un corpus de messages.
- [ ] Établir un espace privé sécurisé pour la preuve, le journal de décision et les plans de correction, avec accès limité et durée de conservation justifiée.
- [ ] Adopter un protocole de consultation des fournisseurs et de gestion d'incident avant tout exercice de contrôle.

## Contrôles M01–M12 : protocole détaillé sans réponse préremplie

| ID | Observation à établir hors dépôt public |
| --- | --- |
| M01 | Existence et identité juridique du porteur; statut et avis d'applicabilité du régime |
| M02 | Titularité de la boîte, administrateurs effectifs, délégations et mandats |
| M03 | MFA, appareils, sessions, récupération, clés ou mécanismes de secours |
| M04 | Applications OAuth, API, redirections, partage et traitement automatique |
| M05 | Fournisseur, sous-traitants, stockage, accès support, sauvegardes et juridictions |
| M06 | Catégories nécessaires, usages effectifs et séparation participation/assistance/vie privée |
| M07 | Procédure de tri, quarantaine et réponse pour les documents sensibles envoyés spontanément |
| M08 | Demandes d'accès, de rectification, de retrait et de suppression; délais selon loi applicable |
| M09 | Rétention, étiquettes, sauvegardes et procédure vérifiable de destruction |
| M10 | Qualification des communications hors Québec et déclencheurs d'EFVP le cas échéant |
| M11 | Détection, confinement, registre d'incidents et avis exigés selon risque et régime |
| M12 | Concordance du site avec les flux réels et contrôle de publication, revue des PR et retour arrière |

## Résultat de la revue : formulaire privé futur

Pour chaque Mxx, l'auditeur documente **hors dépôt public** : preuve accessible, source primaire, période de validité, méthode, rôle habilité, seconde revue, réserves, mesures correctives et échéance. Le responsable de décision examine les éléments qui relèvent de sa compétence **sans confondre** la conformité de la messagerie, la protection des données, le statut électoral et la publication du site.

### Valeurs admissibles dans le système privé futur
`NON_DOCUMENTE`, `A_VERIFIER`, `VERIFIE_HORS_DEPOT`, `REJETE`, `EXPIRE` et `REVOQUE`. Aucun état ne doit être traduit en autorisation électorale ou déploiement sans décision humaine distincte.

## Arrêt, suspension et clôture

Si la preuve est absente ou contradictoire, **NO_GO**. En cas de risque immédiat avéré pour des personnes, le traitement d'incident par les responsables habilités prime; aucune fausse conclusion de conformité n'est possible. Des actions de réduction de risque interne adaptées peuvent être décidées par les titulaires compétents, sans autoriser pour autant un formulaire ou des contributions.

Après revue privée et qualification juridique, une **vraie EFVP** peut être réalisée si obligatoire ou jugée appropriée; elle ne doit pas être baptisée « achevée » sur la base du protocole P50L.

**Ne jamais placer dans la PR :** contenu de messages, identités d'expéditeurs, configurations sensibles, captures d'administration, codes de sécurité, signatures, informations de santé, financières ou politiques individuelles.

État du jalon au 14 octobre 2026 : **0/12 éléments vérifiés par P50L.**
