# SINJIRA™ — EFVP / évaluation des facteurs relatifs à la vie privée

Version V24.4.83 — 2026-08-19. À réviser avant toute nouvelle fonction ou refonte impliquant des renseignements personnels et avant tout nouveau transfert hors Québec.

## 1. Description du projet

Fonction évaluée: portail SINJIRA™, compte universel, Communauté, Registre, jeux, Rencontres 18+ et fonctions narratives préparées.

Responsable opérationnel: Benoit Cantin. Les demandes publiques passent par les canaux du site; aucun courriel administrateur privé n'est publié par ce document.

## 2. Renseignements traités

Catégories possibles selon les fonctions activées:
- compte: courriel, pseudo, identifiants techniques;
- sécurité: date de naissance, statut d'âge, liens parent/tuteur;
- profil privé: langue, région générale, préférences choisies;
- Communauté: publications, commentaires, messages, blocages et signalements;
- Registre: réponses volontairement fournies pour la création d'un personnage;
- Rencontres 18+: préférences relationnelles, compatibilité, conversations et consentements;
- sécurité/modération: preuves textuelles minimales, métadonnées et historique de traitement;
- jeux: progression et données nécessaires au service.

## 3. Finalités et minimisation

Chaque champ doit avoir une finalité documentée. Ne pas collecter d'adresse civique, de pièce d'identité, de biométrie, de géolocalisation précise ou de donnée financière si la fonction ne l'exige pas. Ne pas réutiliser une donnée pour publicité comportementale.

## 4. Confidentialité par défaut

- identité privée séparée des identités communautaire et narrative;
- données jeunesse non publiques par défaut;
- communications adulte/jeunesse séparées côté serveur;
- géolocalisation précise jeunesse non activée;
- profilage publicitaire désactivé;
- partage externe désactivé sauf finalité documentée et contrôle approprié;
- Rencontres 18+ uniquement.

## 5. Mineurs

- inscription libre-service: 13+;
- à 13 ans: autorisation parent/tuteur requise;
- 14–17 ans: compte jeunesse avec protections serveur; les fonctions sociales peuvent rester en attente tant qu'une supervision prévue n'est pas vérifiée;
- adulte ↔ jeunesse: interaction sociale directe interdite;
- Rencontres: 18+ strict;
- prévention du grooming, sollicitation sexuelle/financière et déplacement hors plateforme;
- l'enfant doit être informé lorsqu'un mécanisme de supervision parentale lui est appliqué.

## 6. Risques principaux

| Risque | Gravité | Mesures |
|---|---:|---|
| Accès non autorisé à des données privées | élevée | RLS, RPC contrôlées, séparation des schémas, secrets hors navigateur |
| Contact adulte-mineur | critique | séparation de cohortes serveur |
| Grooming/exploitation | critique | filtres serveur, signalement prioritaire, dossier d'escalade |
| Traite/prostitution/drogues | critique | contenu transactionnel interdit, signalement et blocage |
| Doxxing/contact externe d'un mineur | critique | garde de messagerie jeunesse |
| Surcollecte | élevée | minimisation + activation par fonction |
| Incident de confidentialité | élevée | registre 5 ans + procédure de notification |
| Suppression incompatible avec obligation légale | élevée | demandes structurées + legal holds internes |
| Décision automatisée opaque | moyenne/élevée | IA distante désactivée, décision canonique humaine, compatibilité Rencontres explicable |
| Transfert hors Québec | élevée | EFVP + entente/documentation avant nouveau transfert |

## 7. Fournisseurs et transferts

Pour chaque fournisseur ou hébergeur réellement utilisé, consigner: catégories transmises, localisation, finalité, mesures contractuelles, sous-traitants, durée, mécanisme de suppression et résultat de l'évaluation hors Québec. Ne pas présumer qu'un fournisseur est « conforme » uniquement parce qu'il est connu.

## 8. Conservation

Appliquer `DATA_RETENTION_SCHEDULE.md`. Aucun contenu ne doit être conservé indéfiniment sans finalité, obligation ou choix explicite de l'utilisateur. Les incidents de confidentialité sont conservés au moins cinq ans après leur découverte.

## 9. Droits et transparence

Le compte doit fournir un canal structuré pour accès, portabilité lorsque pertinente, rectification, suppression, retrait du consentement, opposition et plainte. Les refus/limitations doivent être documentés.

## 10. Validation avant mise en production

Une fonction impliquant données sensibles, enfants, nouvelle IA, paiement, géolocalisation, biométrie, nouveau fournisseur externe ou ciblage d'une nouvelle juridiction ne doit pas être activée avant:
1. mise à jour de cette EFVP;
2. analyse de sécurité/menaces;
3. analyse enfant si accessible aux mineurs;
4. documentation des transferts et rétention;
5. tests RLS/RPC et navigateur;
6. validation juridique spécialisée si nécessaire;
7. accord explicite de Benoit Cantin pour toute activation payante.
